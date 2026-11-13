from __future__ import annotations
"""Turn resolution orchestration.

The playable engine scores each clash with the Phi/tau model (kappa,
opponent QTE unscaled, stat weight on the stance played, heat payoff
multipliers from heat.py) and picks opponent lines from LINE_SET_C.
There is no card draw (removed 2026-11-13 for the heat/load gauges).
The older HP/DP + rubber-band turn maths is kept as `resolve_turn_legacy`
for frozen checks; it is not the default and has no match loop.
"""

from collections.abc import Sequence
from pathlib import Path
from random import Random

from .models import Stance, StanceOutcome, CombatantStats, TurnState, TurnResult
from .equations import (
    qte_factor, clash_mult, compute_damage, resolve_stance, damage_mitigation, BATTLE_BONUS,
    LINE_SET_C, LINE_ADHERENCE, LINE_ALT_WEIGHTS,
    clash_progress, kappa_for_length,
    mean_phase_qte, phase_raw_qte,
)
from .trace import TraceLogger


def _stance(c: object) -> Stance:
    """Accept a Stance or its name ("POW" / "EN" / "HAN")."""
    if isinstance(c, Stance):
        return c
    if isinstance(c, str):
        return Stance(c)
    raise TypeError(f"Expected Stance, got {type(c).__name__}")


def resolve_battle(
    player_stances: list[Stance],
    opponent_stances: list[Stance],
) -> list[StanceOutcome]:
    """Resolve three individual stance clashes between player and opponent.

    Returns outcomes from the player's perspective.
    """
    outcomes: list[StanceOutcome] = []
    for p, o in zip(player_stances, opponent_stances):
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
    race_length: int = 10,
    boss_total: float | None = None,
) -> TurnResult:
    """Resolve one turn with the Phi/tau progress model and heat multipliers.

    `turn_state.player_qte` / `opponent_qte` are raw timing scores in
    [0, 1], not 1–10 scores. If `player_qte_phases` is a length-3 list
    (Entry, Apex, Exit), it is averaged into that single `player_qte`
    (None / unplayed = 0; Austin, 2026-11-11); clash math is unchanged.
    No HAN timing modifier and no knot_window factor: the player's raw
    score already reflects the visible zone at the race's fixed r. The
    opponent uses OPPONENT_QTE. Each clash pays
    clash_progress(outcome, stance played, ...) x that side's heat
    multiplier (`player_heat_mults` / `opponent_heat_mults`, default 1.0).
    `race_length` selects kappa. `boss_total` defaults to the opponent's
    stat sum, so the opponent's V is 1 and the player's V is r**kappa.
    """
    t = TurnResult(turn_number=turn_state.turn_number)
    t.player_stances = [_stance(c) for c in turn_state.player_stances]
    t.opponent_stances = [_stance(c) for c in turn_state.opponent_stances]
    if turn_state.player_qte_phases:
        t.player_qte_phases = [phase_raw_qte(v) for v in turn_state.player_qte_phases]
        t.player_qte = mean_phase_qte(turn_state.player_qte_phases)
    else:
        t.player_qte = turn_state.player_qte
    t.opponent_qte = turn_state.opponent_qte
    player_qte = t.player_qte

    local_trace = TraceLogger() if trace is None else trace
    lt = local_trace

    p_stances = t.player_stances
    o_stances = t.opponent_stances
    p_mults = list(turn_state.player_heat_mults) or [1.0, 1.0, 1.0]
    o_mults = list(turn_state.opponent_heat_mults) or [1.0, 1.0, 1.0]
    t.player_heat_mults = p_mults
    t.opponent_heat_mults = o_mults

    lt.log("turn", "Turn", turn_state.turn_number)
    lt.log("input", "Player Stances", [s.value for s in p_stances])
    lt.log("input", "Opponent Stances", [s.value for s in o_stances])
    lt.log("heat", "Player heat mults", [round(m, 4) for m in p_mults])
    lt.log("heat", "Opponent heat mults", [round(m, 4) for m in o_mults])

    p_outcomes = resolve_battle(p_stances, o_stances)
    t.battle_outcomes = p_outcomes
    outcome_sum = sum(o.value for o in p_outcomes)
    t.battle_winner = battle_winner(p_outcomes)
    t.battle_mult = 1.0  # unused by Phi/tau; kept so older readers don't break

    lt.log("battle", "Battle Outcomes", [o.name for o in p_outcomes])
    lt.log("battle", "Outcome Sum", outcome_sum)
    lt.log("battle", "Battle Winner", t.battle_winner)

    if boss_total is None:
        boss_total = opponent.pow + opponent.en + opponent.han
    kappa = kappa_for_length(race_length)
    p_tot = player.pow + player.en + player.han
    r = p_tot / boss_total if boss_total else 1.0

    lt.log("progress", "r", round(r, 6))
    lt.log("progress", "kappa", kappa)
    lt.log("progress", "player q_time", round(player_qte, 4))
    lt.log("progress", "opponent q_time", round(turn_state.opponent_qte, 4))

    p_prog = 0.0
    o_prog = 0.0
    p_parts: list[float] = []
    o_parts: list[float] = []
    for i, p_outcome in enumerate(p_outcomes):
        o_outcome = StanceOutcome(-p_outcome.value)
        pg = clash_progress(
            p_outcome, p_stances[i], player_qte,
            player.pow, player.en, player.han,
            boss_total, kappa, p_mults[i],
        )
        og = clash_progress(
            o_outcome, o_stances[i], turn_state.opponent_qte,
            opponent.pow, opponent.en, opponent.han,
            boss_total, kappa, o_mults[i],
        )
        p_prog += pg
        o_prog += og
        p_parts.append(pg)
        o_parts.append(og)
        lt.log("progress", f"Clash {i+1} player", round(pg, 6))
        lt.log("progress", f"Clash {i+1} opponent", round(og, 6))

    t.player_progress = p_prog
    t.opponent_progress = o_prog
    t.player_clash_progress = p_parts
    t.opponent_clash_progress = o_parts
    # Compatibility: same numbers under the old field names so exporters don't crash.
    t.player_dp = p_prog
    t.opponent_dp = o_prog

    lt.log("progress", "Player turn progress", round(p_prog, 6))
    lt.log("progress", "Opponent turn progress", round(o_prog, 6))

    t.trace = local_trace.all()
    return t


def resolve_turn_legacy(
    turn_state: TurnState,
    player: CombatantStats,
    opponent: CombatantStats,
    trace: TraceLogger | None = None,
    player_gap: float = 0.0,
    rubber_band_threshold: float = 0.0,
) -> TurnResult:
    """Legacy HP/DP turn resolution (clashes → damage → mitigation). Not the playable engine.


    The QTE factor is split proportionally to the DP gap.
    When ahead, your QTE fuels your offense while your defense erodes
    as the lead grows.  When behind, your QTE bolsters your defense
    while your offense fades.

    Args:
        turn_state: Stances and QTE scores for both sides
        player: Player's stats (used for POW/EN in damage/mitigation)
        opponent: Opponent's stats
        trace: Optional execution trace logger
        player_gap: Cumulative DP gap (player - opponent) before this turn
        rubber_band_threshold: DP gap where full rubber-band applies

    Returns:
        TurnResult with per-side damage, outcomes, battle info, and trace
    """
    t = TurnResult(turn_number=turn_state.turn_number)
    t.player_stances = [_stance(c) for c in turn_state.player_stances]
    t.opponent_stances = [_stance(c) for c in turn_state.opponent_stances]
    t.player_qte = turn_state.player_qte
    t.opponent_qte = turn_state.opponent_qte

    local_trace = TraceLogger() if trace is None else trace
    lt = local_trace

    p_stances = t.player_stances
    o_stances = t.opponent_stances

    lt.log("turn", "Turn", turn_state.turn_number)
    lt.log("input", "Player Stances", [s.value for s in p_stances])
    lt.log("input", "Opponent Stances", [s.value for s in o_stances])

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
    for i, (p_outcome, o_outcome) in enumerate(zip(p_outcomes, o_outcomes)):
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


# ── District line tables (LINE_SET_C) ─────────────────────────────────
# Opponent line pick used by lines-v1 and the winrate_n4000.json rebuild
# (equations_v4.generate_clashes). A whole 3-stance line is drawn once
# per corner (once per turn), not per clash and not once per lap.

# LINE_SET_C letters -> stances, one letter per stat (design/02 §6.0).
LETTER_TO_STANCE = {
    "P": Stance.POW,
    "E": Stance.EN,
    "H": Stance.HAN,
}

_TRACKS_CACHE: dict[str, dict[str, list[str]]] | None = None


def line_probs(
    adherence: float | None = None,
    alt_weights: dict[str, float] | None = None,
) -> tuple[float, float, float]:
    """Probabilities of [main, alt1, alt2].

    P(main) = a, P(alt1) = (1-a)*w_alt1, P(alt2) = (1-a)*w_alt2.
    Same formula as lines-v1 / equations_v4.line_probs.
    """
    a = LINE_ADHERENCE if adherence is None else adherence
    w = LINE_ALT_WEIGHTS if alt_weights is None else alt_weights
    return (a, (1.0 - a) * w["alt1"], (1.0 - a) * w["alt2"])


def normalize_district(district: str) -> str:
    """Accept 'Street' or 'street'; LINE_SET_C keys are lowercase."""
    return district.strip().lower()


def line_triples(district: str, corner: str) -> list[str]:
    """Return [main, alt1, alt2] letter triples for a district and corner type."""
    table = LINE_SET_C[normalize_district(district)]
    if corner not in table:
        raise KeyError(f"Unknown corner type {corner!r} for district {district!r}")
    return list(table[corner])


def parse_line(triple: str) -> list[Stance]:
    """Convert an 'EntryApexExit' letter string (P/E/H) to three Stances."""
    if len(triple) != 3 or any(ch not in LETTER_TO_STANCE for ch in triple):
        raise ValueError(f"Invalid line triple {triple!r}")
    return [LETTER_TO_STANCE[ch] for ch in triple]


def pick_line(
    district: str,
    corner: str,
    rng: Random,
    adherence: float | None = None,
    alt_weights: dict[str, float] | None = None,
    weights: Sequence[float] | None = None,
) -> list[Stance]:
    """Pick the opponent's whole line for one corner, from the match RNG.

    `weights` (over [main, alt1, alt2]) overrides line_probs(), e.g. a boss style
    from heat.boss_line_weights.

    One categorical draw among [main, alt1, alt2] with weights line_probs().
    This is the rule lines-v1 used (`numpy.Generator.choice(3, p=pr)`).
    It is probabilistically the same as 'main with probability LINE_ADHERENCE,
    otherwise alt1/alt2 at LINE_ALT_WEIGHTS', but it is a single draw, not
    an adherence roll followed by a separate alt roll.
    """
    triples = line_triples(district, corner)
    w = line_probs(adherence, alt_weights) if weights is None else weights
    chosen = rng.choices(triples, weights=w, k=1)[0]
    return parse_line(chosen)


def corner_at_turn(corners: Sequence[str], turn_number: int) -> str:
    """Map a 1-indexed turn onto a (possibly repeating) lap of corner codes."""
    if not corners:
        raise ValueError("corners must be a non-empty lap or race sequence")
    return corners[(turn_number - 1) % len(corners)]



def official_tracks() -> dict[str, dict[str, list[str]]]:
    """Stand-in 10-corner laps used by lines-v1 / winrate_n4000.json."""
    global _TRACKS_CACHE
    if _TRACKS_CACHE is None:
        path = Path(__file__).resolve().parents[1] / "config" / "tracks_v1.json"
        import json
        data = json.loads(path.read_text())
        _TRACKS_CACHE = {
            d: {name: list(seq) for name, seq in tracks.items()}
            for d, tracks in data["tracks"].items()
        }
    return _TRACKS_CACHE


def track_corners(district: str, track_index: int = 0) -> list[str]:
    """Return one official 10-corner lap for a district (0..4, in file order)."""
    tracks = official_tracks()[normalize_district(district)]
    names = list(tracks)
    return list(tracks[names[track_index % len(names)]])
