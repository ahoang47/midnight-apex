from __future__ import annotations
"""Turn resolution orchestration — clash, battle, damage, mitigation.

This module wires together the pure functions from equations.py into
a complete turn resolution pipeline. The QTE-split logic implements
a rubber-band mechanic: the leading combatant gets their full QTE for
damage but none for mitigation, while the trailing combatant gets the
reverse — keeping close races competitive.
"""

from .models import Stance, StanceOutcome, CombatantStats, TurnState, TurnResult, Card
from .equations import qte_factor, clash_mult, compute_damage, resolve_stance, damage_mitigation, BATTLE_BONUS
from .trace import TraceLogger


def _stance(c: object) -> Stance:
    """Unwrap a Card or Stance to a bare Stance enum."""
    if isinstance(c, Card):
        return c.stance
    if isinstance(c, Stance):
        return c
    raise TypeError(f"Expected Card or Stance, got {type(c).__name__}")


def resolve_battle(
    player_cards: list[Stance],
    opponent_cards: list[Stance],
) -> list[StanceOutcome]:
    """Resolve three individual card clashes between player and opponent.

    Returns outcomes from the player's perspective.
    """
    outcomes: list[StanceOutcome] = []
    for p, o in zip(player_cards, opponent_cards):
        outcomes.append(resolve_stance(_stance(p), _stance(o)))
    return outcomes


def battle_winner(outcomes: list[StanceOutcome]) -> str:
    """Determine battle winner from clash outcome sum.

    Returns 'Player', 'Opponent', or 'Tie'.
    """
    score = sum(o.value for o in outcomes)
    if score > 0:
        return "Player"
    elif score < 0:
        return "Opponent"
    else:
        return "Tie"


def resolve_turn(
    turn_state: TurnState,
    player: CombatantStats,
    opponent: CombatantStats,
    trace: TraceLogger | None = None,
    player_gap: float = 0.0,
    rubber_band_threshold: float = 0.0,
) -> TurnResult:
    """Resolve one complete turn: clashes → damage → mitigation.

    The QTE factor is split proportionally to the DP gap.
    When ahead, your QTE fuels your offense while your defense erodes
    as the lead grows.  When behind, your QTE bolsters your defense
    while your offense fades.

    Args:
        turn_state: Cards and QTE scores for both sides
        player: Player's stats (used for POW/EN in damage/mitigation)
        opponent: Opponent's stats
        trace: Optional execution trace logger
        player_gap: Cumulative DP gap (player - opponent) before this turn
        rubber_band_threshold: DP gap where full rubber-band applies

    Returns:
        TurnResult with per-side damage, outcomes, battle info, and trace
    """
    t = TurnResult(turn_number=turn_state.turn_number)
    t.player_cards = list(turn_state.player_cards)
    t.opponent_cards = list(turn_state.opponent_cards)
    t.player_qte = turn_state.player_qte
    t.opponent_qte = turn_state.opponent_qte

    local_trace = TraceLogger() if trace is None else trace
    lt = local_trace

    p_cards_raw = list(turn_state.player_cards)
    o_cards_raw = list(turn_state.opponent_cards)
    p_stances = [_stance(c) for c in p_cards_raw]
    o_stances = [_stance(c) for c in o_cards_raw]

    lt.log("turn", "Turn", turn_state.turn_number)
    lt.log("input", "Player Cards", [s.value for s in p_stances])
    lt.log("input", "Opponent Cards", [s.value for s in o_stances])

    p_outcomes = resolve_battle(p_stances, o_stances)
    o_outcomes = [StanceOutcome(-o.value) for o in p_outcomes]
    t.battle_outcomes = p_outcomes
    outcome_sum = sum(o.value for o in p_outcomes)
    t.battle_winner = battle_winner(p_outcomes)
    t.battle_mult = 1 + BATTLE_BONUS * abs(outcome_sum)

    lt.log("battle", "Battle Outcomes", [o.name for o in p_outcomes])
    lt.log("battle", "Outcome Sum", outcome_sum)
    lt.log("battle", "Battle Winner", t.battle_winner)
    lt.log("battle", "Battle Mult", round(t.battle_mult, 4))

    p_qte_fac = qte_factor(turn_state.player_qte)
    o_qte_fac = qte_factor(turn_state.opponent_qte)
    p_qte_fac = max(0.0, min(1.0, p_qte_fac))
    o_qte_fac = max(0.0, min(1.0, o_qte_fac))

    lt.log("qte", "Player QTE_factor", round(p_qte_fac, 4))
    lt.log("qte", "Opponent QTE_factor", round(o_qte_fac, 4))

    if rubber_band_threshold > 0:
        blend = min(1.0, abs(player_gap) / rubber_band_threshold)
    else:
        blend = 1.0 if player_gap != 0 else 0.0

    lt.log("qte", "Rubber-band blend", round(blend, 4))

    if player_gap > 0:
        p_damage_qte = p_qte_fac
        p_mitigation_qte = p_qte_fac + (1.0 - p_qte_fac) * blend
        o_damage_qte = o_qte_fac + (1.0 - o_qte_fac) * blend
        o_mitigation_qte = o_qte_fac
    elif player_gap < 0:
        p_damage_qte = p_qte_fac + (1.0 - p_qte_fac) * blend
        p_mitigation_qte = p_qte_fac
        o_damage_qte = o_qte_fac
        o_mitigation_qte = o_qte_fac + (1.0 - o_qte_fac) * blend
    else:
        p_damage_qte = p_qte_fac
        p_mitigation_qte = p_qte_fac
        o_damage_qte = o_qte_fac
        o_mitigation_qte = o_qte_fac

    lt.log("qte", "Player damage QTE", round(p_damage_qte, 4))
    lt.log("qte", "Player mitigation QTE", round(p_mitigation_qte, 4))
    lt.log("qte", "Opponent damage QTE", round(o_damage_qte, 4))
    lt.log("qte", "Opponent mitigation QTE", round(o_mitigation_qte, 4))

    p_total_dp = 0.0
    o_total_dp = 0.0
    for i, (p_card, o_card, p_outcome, o_outcome) in enumerate(
        zip(p_cards_raw, o_cards_raw, p_outcomes, o_outcomes)
    ):
        p_cm = clash_mult(p_outcome)
        o_cm = clash_mult(o_outcome)

        lt.log("clash", f"Clash {i+1} Player clash_mult", round(p_cm, 4))
        lt.log("clash", f"Clash {i+1} Opponent clash_mult", round(o_cm, 4))

        p_dp = compute_damage(player.pow, p_damage_qte, p_cm, t.battle_mult)
        o_dp = compute_damage(opponent.pow, o_damage_qte, o_cm, t.battle_mult)

        p_total_dp += p_dp
        o_total_dp += o_dp

        lt.log("clash", f"Clash {i+1} Player DP contrib", round(p_dp, 4))
        lt.log("clash", f"Clash {i+1} Opponent DP contrib", round(o_dp, 4))

    num_clashes = len(p_outcomes)
    t.player_dp = p_total_dp / num_clashes
    t.opponent_dp = o_total_dp / num_clashes

    p_mit = damage_mitigation(player.en, p_mitigation_qte)
    o_mit = damage_mitigation(opponent.en, o_mitigation_qte)

    t.player_dp = t.player_dp * o_mit
    t.opponent_dp = t.opponent_dp * p_mit

    lt.log("mitigation", "Player mitigation_mult", round(p_mit, 4))
    lt.log("mitigation", "Opponent mitigation_mult", round(o_mit, 4))
    lt.log("damage", "Player Turn DP (avg, mitigated)", round(t.player_dp, 4))
    lt.log("damage", "Opponent Turn DP (avg, mitigated)", round(t.opponent_dp, 4))

    t.trace = local_trace.all()
    return t
