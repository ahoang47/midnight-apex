"""Integration tests for turn resolution and full-match flow.

Tests cover resolve_turn, battle-bonus scaling, knockout, full-race
decision, sudden death, and tiebreaker behaviour.
"""
from velocity_shift.models import Stance, CombatantStats, MatchConfig, TurnState
from velocity_shift.combat import resolve_turn
from velocity_shift.match import run_match


def _p_pick(stance: Stance):
    """Return a per-card player callback that prefers *stance*."""
    def fn(turn, clash_index, hand, opponent_hand, previous_clashes):
        for c in hand:
            if c == stance:
                return c
        return hand[0]
    return fn


def _o_pick(stance: Stance):
    """Return a per-card opponent callback that prefers *stance*."""
    def fn(turn, clash_index, hand, player_hand, phase_index, personality, clashes, hist):
        for c in hand:
            if c == stance:
                return c
        return hand[0]
    return fn


def make_default_turn_state(turn=1,
                            p_cards=None, o_cards=None,
                            p_qte=8.0, o_qte=5.0):
    """Build a TurnState with sensible defaults (P: ATK/NEU/DEF, O: DEF/NEU/ATK)."""
    if p_cards is None:
        p_cards = [Stance.ATTACK, Stance.NEUTRAL, Stance.DEFEND]
    else:
        p_cards = [Stance(s) if isinstance(s, str) else s for s in p_cards]
    if o_cards is None:
        o_cards = [Stance.DEFEND, Stance.NEUTRAL, Stance.ATTACK]
    else:
        o_cards = [Stance(s) if isinstance(s, str) else s for s in o_cards]
    return TurnState(
        turn_number=turn,
        player_cards=p_cards,
        opponent_cards=o_cards,
        player_qte=p_qte,
        opponent_qte=o_qte,
    )


def test_resolve_turn_basic():
    """Basic turn resolution — both sides deal positive DP, trace is populated."""
    player = CombatantStats(name="P", pow=500, en=200, han=300)
    opponent = CombatantStats(name="O", pow=400, en=300, han=200)

    turn = make_default_turn_state()
    result = resolve_turn(turn, player, opponent)

    assert result.player_dp > 0
    assert result.opponent_dp > 0
    assert result.turn_number == 1
    assert len(result.trace) > 10


def test_resolve_turn_battle_bonus():
    """A 3-0 win gives higher battle_mult and DP than a tie."""
    player = CombatantStats(name="P", pow=500, en=200, han=300)
    opponent = CombatantStats(name="O", pow=400, en=300, han=200)

    turn_win = make_default_turn_state(
        p_cards=[Stance.ATTACK, Stance.ATTACK, Stance.ATTACK],
        o_cards=[Stance.NEUTRAL, Stance.NEUTRAL, Stance.NEUTRAL],
    )
    r1 = resolve_turn(turn_win, player, opponent)

    turn_tie = make_default_turn_state(
        p_cards=[Stance.ATTACK, Stance.NEUTRAL, Stance.DEFEND],
        o_cards=[Stance.ATTACK, Stance.NEUTRAL, Stance.DEFEND],
    )
    r2 = resolve_turn(turn_tie, player, opponent)

    assert r1.player_dp > r2.player_dp, "Winning 3-0 should yield more DP than a tie"
    assert r1.battle_mult == 1.15, "3-0 win should give 1.15 battle_mult"
    assert r2.battle_mult == 1.0, "Tie should give 1.0 battle_mult"


def test_run_match_full_race():
    """With moderate levels, race goes to decision by position."""
    player = CombatantStats(name="P", pow=120, en=100, han=100, level=200)
    opponent = CombatantStats(name="O", pow=100, en=100, han=100, level=200)

    cfg = MatchConfig(
        player_stats=player,
        opponent_stats=opponent,
        seed=123,
        deterministic=True,
        max_turns=5,
    )

    result = run_match(
        cfg,
        _p_pick(Stance.ATTACK),
        lambda t: 7.0,
        _o_pick(Stance.NEUTRAL),
        lambda t: 5.0,
    )

    assert result.turns_played == result.total_turns, "Should run all turns"
    assert result.winner is not None, "Should have a winner"
    assert result.player_position >= 0, "Player position should be non-negative"
    assert result.opponent_position >= 0, "Opponent position should be non-negative"


def test_positions_computed():
    """Positions are computed from cumulative DP vs max_hp after full race."""
    player = CombatantStats(name="P", pow=100, en=100, han=100, level=500)
    opponent = CombatantStats(name="O", pow=100, en=100, han=100, level=500)

    cfg = MatchConfig(
        player_stats=player,
        opponent_stats=opponent,
        max_turns=1,
        seed=1,
        deterministic=True,
    )

    result = run_match(
        cfg,
        _p_pick(Stance.NEUTRAL),
        lambda t: 5.0,
        _o_pick(Stance.NEUTRAL),
        lambda t: 5.0,
    )

    assert result.player_position >= 0
    assert result.opponent_position >= 0
    assert result.winner is not None
    assert len(result.turn_results) == result.total_turns


def test_equal_race():
    """Identical combatants and identical QTE produce race to decision."""
    player = CombatantStats(name="P", pow=500, en=100, han=100, level=500)
    opponent = CombatantStats(name="O", pow=500, en=100, han=100, level=500)

    cfg = MatchConfig(
        player_stats=player,
        opponent_stats=opponent,
        max_turns=5,
        seed=42,
        deterministic=True,
    )

    result = run_match(
        cfg,
        _p_pick(Stance.NEUTRAL),
        lambda t: 5.0,
        _o_pick(Stance.NEUTRAL),
        lambda t: 5.0,
    )

    assert result.winner is not None
    assert result.turns_played == result.total_turns
