"""Integration tests for turn resolution and full-match flow.

Tests cover resolve_turn, battle-bonus scaling, knockout, full-race
decision, sudden death, and tiebreaker behaviour.
"""
from velocity_shift.models import Stance, CombatantStats, MatchConfig, TurnState
from velocity_shift.combat import resolve_turn
from velocity_shift.match import run_match


def _p_pick(stance: Stance):
    """Player callback that plays *stance* while its gauge is open, else the first selectable one."""
    def fn(turn, clash_index, ctx):
        if ctx.gauges.selectable(stance):
            return stance
        return ctx.gauges.selectable_stances()[0]
    return fn


def make_default_turn_state(turn=1,
                            p_cards=None, o_cards=None,
                            p_qte=0.8, o_qte=0.5):
    """Build a TurnState with sensible defaults (P: POW/HAN/EN, O: EN/HAN/POW)."""
    if p_cards is None:
        p_cards = [Stance.POW, Stance.HAN, Stance.EN]
    else:
        p_cards = [Stance(s) if isinstance(s, str) else s for s in p_cards]
    if o_cards is None:
        o_cards = [Stance.EN, Stance.HAN, Stance.POW]
    else:
        o_cards = [Stance(s) if isinstance(s, str) else s for s in o_cards]
    return TurnState(
        turn_number=turn,
        player_stances=p_cards,
        opponent_stances=o_cards,
        player_qte=p_qte,
        opponent_qte=o_qte,
    )


def test_resolve_turn_basic():
    """Basic turn resolution — both sides deal positive DP, trace is populated."""
    player = CombatantStats(name="P", pow=500, en=200, han=300)
    opponent = CombatantStats(name="O", pow=400, en=300, han=200)

    turn = make_default_turn_state()
    result = resolve_turn(turn, player, opponent)

    assert result.player_progress > 0
    assert result.opponent_progress > 0
    assert result.turn_number == 1
    assert len(result.trace) > 10


def test_resolve_turn_battle_bonus():
    """A 3-0 clash win gives more Phi progress than a three-clash tie."""
    player = CombatantStats(name="P", pow=500, en=200, han=300)
    opponent = CombatantStats(name="O", pow=400, en=300, han=200)

    turn_win = make_default_turn_state(
        p_cards=[Stance.POW, Stance.POW, Stance.POW],
        o_cards=[Stance.HAN, Stance.HAN, Stance.HAN],
    )
    r1 = resolve_turn(turn_win, player, opponent)

    turn_tie = make_default_turn_state(
        p_cards=[Stance.POW, Stance.HAN, Stance.EN],
        o_cards=[Stance.POW, Stance.HAN, Stance.EN],
    )
    r2 = resolve_turn(turn_tie, player, opponent)

    assert r1.player_progress > r2.player_progress, "Winning 3-0 should yield more progress than a tie"


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
        _p_pick(Stance.POW),
        lambda t: 0.7,
    )

    assert result.turns_played == result.total_turns, "Should run all turns"
    assert result.winner is not None, "Should have a winner"
    assert result.player_position >= 0, "Player position should be non-negative"
    assert result.opponent_position >= 0, "Opponent position should be non-negative"


def test_positions_computed():
    """Positions are the share of combined Phi progress after a full race."""
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
        _p_pick(Stance.HAN),
        lambda t: 0.5,
    )

    assert result.player_position >= 0
    assert result.opponent_position >= 0
    assert result.winner is not None
    assert len(result.turn_results) == result.total_turns


def test_r105_same_stances_player_leads_on_v():
    """At r=1.05 with identical (even-share) stances and perfect timing, V = r**kappa
    gives the player more progress than the opponent (whose V is 1)."""
    from velocity_shift.equations import kappa_for_length, T_MAX
    player = CombatantStats(name="P", pow=105, en=105, han=105, level=50)
    opponent = CombatantStats(name="O", pow=100, en=100, han=100, level=50)
    turn = make_default_turn_state(
        p_cards=[Stance.HAN, Stance.HAN, Stance.HAN],
        o_cards=[Stance.HAN, Stance.HAN, Stance.HAN],
        p_qte=1.0, o_qte=1.0,
    )
    result = resolve_turn(turn, player, opponent, race_length=10)
    V = 1.05 ** kappa_for_length(10)
    assert abs(result.player_progress - 3 * V * T_MAX) < 1e-12
    assert abs(result.opponent_progress - 3 * T_MAX) < 1e-12
    assert result.player_progress > result.opponent_progress

def test_resolve_turn_phase_mean_matches_scalar():
    """Three phase scores average into the existing single raw_qte; clash math is unchanged."""
    player = CombatantStats(name="P", pow=500, en=200, han=300)
    opponent = CombatantStats(name="O", pow=400, en=300, han=200)
    mean = (1.0 + 0.0 + 0.5) / 3.0
    via_phases_state = make_default_turn_state(p_qte=0.0)
    via_phases_state.player_qte_phases = [1.0, None, 0.5]
    via_phases = resolve_turn(via_phases_state, player, opponent)
    via_scalar = resolve_turn(make_default_turn_state(p_qte=mean), player, opponent)
    assert via_phases.player_qte == mean
    assert via_phases.player_qte_phases == [1.0, 0.0, 0.5]
    assert via_phases.player_progress == via_scalar.player_progress
    assert via_phases.opponent_progress == via_scalar.opponent_progress
    assert via_phases.player_clash_progress == via_scalar.player_clash_progress
    assert via_phases.opponent_clash_progress == via_scalar.opponent_clash_progress


def test_heat_mults_scale_clash_progress():
    """A heat multiplier scales that clash's progress and nothing else."""
    player = CombatantStats(name="P", pow=100, en=100, han=100)
    opponent = CombatantStats(name="O", pow=100, en=100, han=100)
    base = resolve_turn(make_default_turn_state(), player, opponent)
    st = make_default_turn_state()
    st.player_heat_mults = [1.0, 0.4, 1.0]
    hot = resolve_turn(st, player, opponent)
    assert abs(hot.player_clash_progress[1] - 0.4 * base.player_clash_progress[1]) < 1e-12
    assert hot.player_clash_progress[0] == base.player_clash_progress[0]
    assert hot.opponent_progress == base.opponent_progress


def test_repeating_one_stance_overheats_and_locks():
    """Spamming POW fills the engine gauge; the engine then refuses POW until it cools (callback sees it locked)."""
    player = CombatantStats(name="P", pow=100, en=100, han=100, level=50)
    opponent = CombatantStats(name="O", pow=100, en=100, han=100, level=50)
    cfg = MatchConfig(player_stats=player, opponent_stats=opponent, seed=3, max_turns=10,
                      district="wangan", corners=["SW"] * 10)
    seen_locked = []

    def pick(turn, ci, ctx):
        seen_locked.append(not ctx.gauges.selectable(Stance.POW))
        return Stance.POW if ctx.gauges.selectable(Stance.POW) else ctx.gauges.selectable_stances()[0]

    res = run_match(cfg, pick, lambda t: 1.0)
    assert any(seen_locked)
    assert any(m < 1.0 for t in res.turn_results for m in t.player_heat_mults)   # overrun before the lock
