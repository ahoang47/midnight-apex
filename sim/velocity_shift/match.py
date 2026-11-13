from __future__ import annotations
"""Multi-turn match loop — pick stances under heat, resolve, repeat.

Heat/load resource system (resources-v4b G2, Austin approved 2026-11-13);
the card draw is gone. Each turn is one corner of the lap:

  1. The opponent's whole line (Entry/Apex/Exit) is drawn from LINE_SET_C
     once per corner from the match RNG (boss style weights optional).
  2. For each of the 3 clashes, the opponent plays its line stance under the
     boss heat rule (heat.boss_stance), and the player picks any stance whose
     gauge is not locked (callback). With all three gauges locked the side
     limps on its least-loaded gauge at LIMP_MULT. Each played stance adds
     load; overrun pays less (overrun_mult); a full gauge locks.
  3. End of turn: passive corner load, recovery, release (heat.HeatGauges).
  4. Phi/tau progress per clash x stat weight x heat multiplier; the higher
     total after max_turns wins (ties allowed).
"""

import copy
from random import Random
from typing import Callable, Optional

from .models import Stance, StanceOutcome, MatchConfig, MatchResult, TurnResult, TurnState, ClashResult, ClashContext
from .combat import resolve_turn, pick_line, corner_at_turn, official_tracks, normalize_district
from .equations import resolve_stance, OPPONENT_QTE, raw_qte_score, mean_phase_qte, phase_raw_qte, DISTRICTS
from .heat import HeatGauges, track_wear, boss_stance, boss_line_weights
from .trace import TraceLogger
from .ai import get_phase, get_total_phases

DEFAULT_DISTRICT = DISTRICTS[0]


def race_setup(cfg: MatchConfig) -> tuple[str, list[str]]:
    """(district, lap) for a match; falls back to DEFAULT_DISTRICT's first official track."""
    if cfg.district and cfg.corners:
        return cfg.district, list(cfg.corners)
    d = cfg.district or DEFAULT_DISTRICT
    tr = official_tracks()[normalize_district(d)]
    return d, list(tr[next(iter(tr))])


def run_match(
    cfg: MatchConfig,
    get_player_stance: Callable[[int, int, ClashContext], Stance],
    get_player_qte: Callable[[int], float | list | tuple | None],
    trace: TraceLogger | None = None,
    on_turn_start: Optional[Callable[[int, str, HeatGauges, HeatGauges], None]] = None,
    on_clash_resolved: Optional[Callable[[int, int, Stance, Stance, StanceOutcome], None]] = None,
    on_turn_complete: Optional[Callable[[int, TurnResult, float, float], None]] = None,
    on_lap_complete: Optional[Callable[[int, int], None]] = None,
    on_clashes_complete: Optional[Callable[[int, list[ClashResult]], None]] = None,
    on_line_picked: Optional[Callable[[int, str, list[Stance]], None]] = None,
) -> MatchResult:
    """Run a full match between two combatants.

    Callbacks:
        get_player_stance(turn, clash_index, ctx) -> Stance; must be selectable
            (not called when all three gauges are locked: the engine limps).
        get_player_qte(turn) -> raw score, or (Entry, Apex, Exit) scores; ignored
            when cfg sets a QTE profile / player_timing / player_quality.
        on_turn_start(turn, corner, player_gauges, opponent_gauges)
        on_line_picked(turn, corner_type, line) — the opponent's drawn line (hidden from the player)
        on_clash_resolved(turn, clash_index, player_stance, opponent_stance, outcome)
        on_turn_complete(turn, turn_result, cum_player_progress, cum_opponent_progress)
        on_lap_complete(phase_index, total_phases)
    """
    player = copy.copy(cfg.player_stats)
    opponent = copy.copy(cfg.opponent_stats)
    district, lap = race_setup(cfg)

    result = MatchResult(
        player_name=player.name,
        opponent_name=opponent.name,
        total_turns=cfg.max_turns,
    )
    main_trace = trace or TraceLogger()
    rng = Random(cfg.seed) if cfg.seed is not None else Random()

    p_tot = player.pow + player.en + player.han
    o_tot = opponent.pow + opponent.en + opponent.han
    r = p_tot / o_tot if o_tot else 1.0
    wear = track_wear(district, lap)
    p_heat = HeatGauges.for_player(player.pow, player.en, player.han, r, wear)
    o_heat = HeatGauges.for_boss(opponent.pow, opponent.en, opponent.han, wear)

    prev_phase: int = -1
    for turn_num in range(1, cfg.max_turns + 1):
        phase_index = get_phase(turn_num, cfg.encounter_type)
        total_phases = get_total_phases(cfg.encounter_type)
        if phase_index != prev_phase:
            if on_lap_complete:
                on_lap_complete(phase_index, total_phases)
            prev_phase = phase_index

        corner = corner_at_turn(lap, turn_num)
        weights = None
        if cfg.boss_style != "balanced":
            weights = boss_line_weights(district, corner, turn_num - 1, cfg.max_turns, cfg.boss_style)
        planned_line = pick_line(district, corner, rng, weights=weights)
        if on_line_picked:
            on_line_picked(turn_num, corner, planned_line)

        p_heat.begin_turn()
        o_heat.begin_turn()
        if on_turn_start:
            on_turn_start(turn_num, corner, p_heat, o_heat)

        p_stances: list[Stance] = []
        o_stances: list[Stance] = []
        p_mults: list[float] = []
        o_mults: list[float] = []
        p_limp: list[bool] = []
        o_limp: list[bool] = []
        clash_history: list[ClashResult] = []

        for ci in range(3):
            o_s = boss_stance(o_heat, planned_line[ci])
            om, _, ol = o_heat.play(o_s, corner)

            if p_heat.all_locked():
                p_s = p_heat.least_loaded(only_unlocked=False)
            else:
                ctx = ClashContext(turn_num, ci, cfg.max_turns, district, corner, lap, r, p_heat, list(clash_history))
                p_s = get_player_stance(turn_num, ci, ctx)
            pm, _, pl = p_heat.play(p_s, corner)

            outcome = resolve_stance(p_s, o_s)
            cr = ClashResult(ci, p_s, o_s, outcome)
            clash_history.append(cr)
            p_stances.append(p_s); o_stances.append(o_s)
            p_mults.append(pm); o_mults.append(om)
            p_limp.append(pl); o_limp.append(ol)
            if on_clash_resolved:
                on_clash_resolved(turn_num, ci, p_s, o_s, outcome)

        if on_clashes_complete:
            on_clashes_complete(turn_num, clash_history)

        p_heat.end_turn(corner)
        o_heat.end_turn(corner)

        # Raw q_time in [0, 1]. If a skill profile or player_timing is configured,
        # the score is E[s] at the race's fixed r (and qte_window_mod); otherwise the
        # callback value is already a raw score. A 3-tuple of Entry/Apex/Exit scores is
        # averaged (unplayed / None = 0; Austin, 2026-11-11). Opponent timing is OPPONENT_QTE.
        p_phases: list[float] = []
        if cfg.player_qte_profile or cfg.player_timing is not None or cfg.player_quality is not None:
            q_time = cfg.player_timing if cfg.player_timing is not None else cfg.player_quality
            p_qte = raw_qte_score(
                r,
                profile=cfg.player_qte_profile,
                q_time=None if cfg.player_qte_profile else q_time,
                window_mod=cfg.qte_window_mod,
            )
        else:
            cb = get_player_qte(turn_num)
            if isinstance(cb, (list, tuple)) and len(cb) == 3 and not isinstance(cb, (str, bytes)):
                p_phases = [phase_raw_qte(v) for v in cb]
                p_qte = mean_phase_qte(cb)
            else:
                p_qte = cb

        turn_state = TurnState(
            turn_number=turn_num,
            player_stances=p_stances,
            opponent_stances=o_stances,
            player_qte=p_qte,
            opponent_qte=OPPONENT_QTE,
            player_heat_mults=p_mults,
            opponent_heat_mults=o_mults,
            player_qte_phases=p_phases,
        )
        turn_result = resolve_turn(turn_state, player, opponent, main_trace, race_length=cfg.max_turns)
        turn_result.corner_type = corner
        turn_result.opponent_line = list(planned_line)
        turn_result.player_heat_fill = p_heat.fill()
        turn_result.opponent_heat_fill = o_heat.fill()
        turn_result.player_locked = list(p_heat.locked)
        turn_result.opponent_locked = list(o_heat.locked)
        turn_result.player_limp = p_limp
        turn_result.opponent_limp = o_limp

        result.player_total_progress += turn_result.player_progress
        result.opponent_total_progress += turn_result.opponent_progress
        result.player_total_dp = result.player_total_progress
        result.opponent_total_dp = result.opponent_total_progress
        result.turn_results.append(turn_result)
        if on_turn_complete:
            on_turn_complete(turn_num, turn_result, result.player_total_progress, result.opponent_total_progress)
        result.turns_played = turn_num

    gp = result.player_total_progress
    go = result.opponent_total_progress
    total = gp + go
    result.player_position = gp / total if total else 0.5
    result.opponent_position = go / total if total else 0.5
    if gp > go:
        result.winner = result.player_name
    elif go > gp:
        result.winner = result.opponent_name
    else:
        result.winner = "Tie"
    return result
