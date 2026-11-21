from __future__ import annotations
"""DRAFT (Barry, 2026-11-20, UNAPPROVED): Touge passing v1 = per-phase resolution in Touge, opt-in, sim/ untouched.

Austin (relayed by Gordon, 2026-11-20 5:01 PM PT): "Yes, have Barry spec Touge passing now on that plan." Plan: the Touge race
starts from the PA, no cat-and-mouse roles, no turn-5 swap, passing resolves per phase like Wangan/Street (design/01, acf9b25).

run_match_pp is a copy of sim/velocity_shift/match.py run_match (touge-race 6b53d74) with ONE change: in a district listed in
SETTINGS["districts"], each clash (Entry, Apex, Exit) is scored with its own phase QTE instead of the turn's single score:
  player (sim): one press per phase from the live press model, s = max(0, 1 - |e|/a), e ~ N(0, sigma) (E[s] unchanged);
                real play: the callback's (Entry, Apex, Exit) scores;
  AI:           one N(OPPONENT_QTE, OPPONENT_QTE_SD) draw per phase (Entry = the live per-turn draw);
  smoothing:    option 2 (per-phase-combat-v1): phase score = w*press + (1-w)*mean(earlier presses this turn), Entry = press;
                w = 1.0 is "own phase QTE" (Austin 6:14 AM decision for Wangan/Street).
Car order after each phase = running progress totals (display; passing). Heat, picks, line draws, the match RNG and the winner
rule (higher total progress) are the live code. Roles / the turn-5 swap never existed in the sim (Godot race_core.gd says
"purely presentational"), so removing them changes no number.

install() points velocity_shift.simulation.run_match at run_match_pp, so SimulationRunner / mod_skill.crew_config /
experience_gauntlet use it unchanged.
"""

import copy
from random import Random
from typing import Callable, Optional

from velocity_shift import equations as E
from velocity_shift.models import Stance, StanceOutcome, MatchConfig, MatchResult, TurnResult, TurnState, ClashResult, ClashContext
from velocity_shift.combat import resolve_turn, pick_line, corner_at_turn, normalize_district
from velocity_shift.equations import (resolve_stance, OPPONENT_QTE_SEED_OFFSET, raw_qte_score, mean_phase_qte, phase_raw_qte,
                                      round_qte_score, kappa_for_length, clash_progress)
from velocity_shift.heat import HeatGauges, track_wear, boss_stance, boss_line_weights
from velocity_shift.trace import TraceLogger
from velocity_shift.ai import get_phase, get_total_phases
from velocity_shift.match import opponent_qte_mean, opponent_qte_spread, race_setup

SETTINGS = {"districts": ("touge",), "w": 0.35}
PLAYER_PRESS_SEED_OFFSET = 15_485_863          # same offset as per-phase-combat-v1


def sample_press_score(rng, sigma_over_a0: float, width_over_w0: float) -> float:
    """One timing press: s = max(0, 1 - |e| / a), e ~ N(0, sigma) (a0 units); E[s] = E.expected_hit_quality."""
    if width_over_w0 <= 0.0:
        return 0.0
    if sigma_over_a0 <= 0.0:
        return 1.0
    return round_qte_score(max(0.0, 1.0 - abs(rng.gauss(0.0, sigma_over_a0)) / width_over_w0))


def smooth(v, w):
    """Option 2: [Entry, w*Apex + (1-w)*Entry, w*Exit + (1-w)*mean(Entry, Apex)] on the raw presses; w = 1 = own press."""
    if v is None or w is None or w >= 1.0:
        return v
    return [v[0]] + [round_qte_score(w * v[i] + (1 - w) * sum(v[:i]) / i) for i in (1, 2)]


def resolve_turn_pp(turn_state, player, opponent, trace, cfg, pq, oq) -> TurnResult:
    """Live resolve_turn (stances, outcomes, trace), then each clash re-paid with its own phase score (pq / oq; None = live)."""
    t = resolve_turn(turn_state, player, opponent, trace, race_length=cfg.max_turns, kappa_mult=cfg.kappa_mult)
    if pq is None and oq is None:
        return t
    boss_total = opponent.pow + opponent.en + opponent.han
    kappa = kappa_for_length(cfg.max_turns) * cfg.kappa_mult
    pp, op, order = [], [], []
    cp = co = 0.0
    for i, p_out in enumerate(t.battle_outcomes):
        o_out = StanceOutcome(-p_out.value)
        pg = clash_progress(p_out, t.player_stances[i], t.player_qte if pq is None else pq[i], player.pow, player.en, player.han,
                            boss_total, kappa, t.player_heat_mults[i])
        og = clash_progress(o_out, t.opponent_stances[i], t.opponent_qte if oq is None else oq[i], opponent.pow, opponent.en,
                            opponent.han, boss_total, kappa, t.opponent_heat_mults[i])
        pp.append(pg); op.append(og)
    t.player_clash_progress, t.opponent_clash_progress = pp, op
    t.player_progress = t.player_dp = sum(pp)
    t.opponent_progress = t.opponent_dp = sum(op)
    t.phase_qte = (pq, oq)
    return t


def install(districts=("touge",), w=0.35):
    """Opt in: per-phase in `districts` with smoothing w (None or 1.0 = own press). Patches simulation.run_match."""
    import velocity_shift.simulation as S
    SETTINGS["districts"] = tuple(districts); SETTINGS["w"] = w
    S.run_match = run_match_pp


def run_match_pp(
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
    o_qte_mean = opponent_qte_mean(cfg)
    o_qte_sd, o_qte_lo, o_qte_hi = opponent_qte_spread(cfg)
    o_qte_rng = None
    if o_qte_sd > 0.0:
        o_qte_rng = Random(cfg.seed + OPPONENT_QTE_SEED_OFFSET) if cfg.seed is not None else Random()

    per_phase = normalize_district(district) in SETTINGS["districts"]
    press_rng = Random((cfg.seed or 0) + PLAYER_PRESS_SEED_OFFSET) if per_phase else None
    q_time = cfg.player_timing if cfg.player_timing is not None else cfg.player_quality

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
        # averaged (unplayed / None = 0; Austin, 2026-11-11). Opponent timing: opponent_qte_mean(cfg) / spread.
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

        if o_qte_rng is None:
            o_qte = o_qte_mean
        else:
            o_qte = round_qte_score(min(o_qte_hi, max(o_qte_lo, o_qte_rng.gauss(o_qte_mean, o_qte_sd))))

        turn_state = TurnState(
            turn_number=turn_num,
            player_stances=p_stances,
            opponent_stances=o_stances,
            player_qte=p_qte,
            opponent_qte=o_qte,
            player_heat_mults=p_mults,
            opponent_heat_mults=o_mults,
            player_qte_phases=p_phases,
        )
        if not per_phase:
            turn_result = resolve_turn(turn_state, player, opponent, main_trace, race_length=cfg.max_turns,
                                       kappa_mult=cfg.kappa_mult)
        else:
            pq = oq = None
            if p_phases:                                   # real play: one press per phase from the callback
                pq = list(p_phases)
            elif cfg.player_timing is not None or cfg.player_quality is not None:
                sig = E.qte_sigma_over_a0(None, q_time); zw = E.qte_zone_width(r, cfg.qte_window_mod)
                pq = [sample_press_score(press_rng, sig, zw) for _ in range(3)]
            if o_qte_rng is not None:                      # AI: Entry = the live per-turn draw, Apex/Exit = 2 more draws
                oq = [o_qte] + [round_qte_score(min(o_qte_hi, max(o_qte_lo, o_qte_rng.gauss(o_qte_mean, o_qte_sd))))
                                for _ in range(2)]
            pq = smooth(pq, SETTINGS["w"]); oq = smooth(oq, SETTINGS["w"])
            turn_result = resolve_turn_pp(turn_state, player, opponent, main_trace, cfg, pq, oq)
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
