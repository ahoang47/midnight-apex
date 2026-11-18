"""Spirit meter (Yakuza "heat"-style) hook on a COPY of the live match path. Barry draft 2026-11-18, touge-race @ bbdda07.

sim/velocity_shift is imported read-only. `spirit_run_match` is velocity_shift.match.run_match copied line for line,
plus four marked SPIRIT hooks; `SpiritRunner` is SimulationRunner with run() pointed at the copy. With spirit=None
the copy reproduces the live engine bit for bit (checked by check_identity()).

Meter (all PLACEHOLDER):
  fill per executed clash (not limping) = base x outcome factor x match multiplier
     outcome factor: win 1.0, tie `tie_frac`, loss `loss_frac`
     match multiplier mm = 1 + match_k x (3 x share of the played stance's stat in the car build - 1)
       (same form as equations.STAT_M_W; on a 25-50 % band build mm runs 1 - 0.25k .. 1 + 0.5k)
  no fill while a buff runs. When the meter reaches `size` and activations < `max_acts`, the sim player activates
  at the start of the next turn; the meter empties and the buff runs `dur` turns (that turn included).
Buffs:
  "pay"  : the player's clash payoff x (1 + amount) on buff turns (multiplies the heat payoff multiplier)
  "qte"  : QTE zone width x (1 + amount) on buff turns (adds `amount` to MatchConfig.qte_window_mod)
  "heat" : free heat: on activation every player gauge empties and unlocks; for `dur` turns played stances add no
           load (passive corner load and recovery still run)
"""
from __future__ import annotations
import copy, os, sys
from dataclasses import dataclass
from random import Random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "sim"))
from velocity_shift.models import MatchConfig, MatchResult, TurnState, ClashResult, ClashContext, StanceOutcome  # noqa
from velocity_shift.combat import resolve_turn, pick_line, corner_at_turn  # noqa
from velocity_shift.equations import resolve_stance, OPPONENT_QTE, raw_qte_score, mean_phase_qte, phase_raw_qte, \
    STAT_M_W, kappa_for_length, _STANCE_INDEX  # noqa
from velocity_shift.heat import HeatGauges, track_wear, boss_stance, boss_line_weights, build_shares  # noqa
from velocity_shift.trace import TraceLogger  # noqa
from velocity_shift.ai import get_phase, get_total_phases  # noqa
from velocity_shift.match import race_setup  # noqa
from velocity_shift import simulation as S  # noqa


@dataclass
class Spirit:
    base: float = 10.0        # fill per won clash at mm = 1 (meter units)
    size: float = 100.0       # meter size
    match_k: float = 1.0      # match multiplier strength
    loss_frac: float = 0.2    # fill on a lost (executed) clash, as a fraction of a win
    tie_frac: float = 0.5     # fill on a tie
    buff: str = "pay"         # pay | qte | heat
    amount: float = 0.25      # pay: +25 % payoff; qte: +25 % zone width; heat: unused
    dur: int = 3              # turns
    max_acts: int = 99        # activations per race


class Meter:
    def __init__(self, sp: Spirit, shares):
        self.sp, self.shares = sp, shares
        self.v, self.left, self.acts, self.buff_turns, self.pending = 0.0, 0, 0, 0, False
        self.turn, self.first = 0, None

    def start_turn(self) -> bool:
        """True when a buff is active this turn (activates here if the meter filled last turn)."""
        new = False
        self.turn += 1
        if self.left == 0 and self.pending:
            self.pending, self.v, self.left, new = False, 0.0, self.sp.dur, True
            self.acts += 1
            if self.first is None:
                self.first = self.turn
        self.active = self.left > 0
        self.new = new
        return self.active

    def end_turn(self):
        if self.left > 0:
            self.left -= 1; self.buff_turns += 1

    def clash(self, stance, outcome, limp):
        if limp or self.active:
            return
        sp = self.sp
        f = 1.0 if outcome == StanceOutcome.WIN else sp.tie_frac if outcome == StanceOutcome.DRAW else sp.loss_frac
        mm = 1.0 + sp.match_k * (3.0 * self.shares[_STANCE_INDEX[stance]] - 1.0)
        self.v = min(sp.size, self.v + sp.base * f * mm)
        if self.v >= sp.size - 1e-9 and self.acts < sp.max_acts:
            self.pending = True


def spirit_run_match(cfg, get_player_stance, get_player_qte, trace=None, on_turn_start=None, on_clash_resolved=None,
                     on_turn_complete=None, on_lap_complete=None, on_clashes_complete=None, on_line_picked=None,
                     spirit: Spirit | None = None, meter_out: list | None = None) -> MatchResult:
    player = copy.copy(cfg.player_stats)
    opponent = copy.copy(cfg.opponent_stats)
    district, lap = race_setup(cfg)
    result = MatchResult(player_name=player.name, opponent_name=opponent.name, total_turns=cfg.max_turns)
    main_trace = trace or TraceLogger()
    rng = Random(cfg.seed) if cfg.seed is not None else Random()
    p_tot = player.pow + player.en + player.han
    o_tot = opponent.pow + opponent.en + opponent.han
    r = p_tot / o_tot if o_tot else 1.0
    wear = track_wear(district, lap)
    p_heat = HeatGauges.for_player(player.pow, player.en, player.han, r, wear)
    o_heat = HeatGauges.for_boss(opponent.pow, opponent.en, opponent.han, wear)
    meter = Meter(spirit, build_shares(player.pow, player.en, player.han)) if spirit else None  # SPIRIT
    prev_phase = -1
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
        # SPIRIT hook 1: activation at turn start
        buff = meter.start_turn() if meter else False
        if buff and spirit.buff == "heat" and meter.new:
            p_heat.load = [0.0, 0.0, 0.0]; p_heat.locked = [False, False, False]
        if on_turn_start:
            on_turn_start(turn_num, corner, p_heat, o_heat)
        p_stances, o_stances, p_mults, o_mults, p_limp, o_limp, clash_history = [], [], [], [], [], [], []
        for ci in range(3):
            o_s = boss_stance(o_heat, planned_line[ci])
            om, _, ol = o_heat.play(o_s, corner)
            if p_heat.all_locked():
                p_s = p_heat.least_loaded(only_unlocked=False)
            else:
                ctx = ClashContext(turn_num, ci, cfg.max_turns, district, corner, lap, r, p_heat, list(clash_history))
                p_s = get_player_stance(turn_num, ci, ctx)
            if buff and spirit.buff == "heat":  # SPIRIT hook 2: played stances add no load
                keep = (list(p_heat.load), list(p_heat.locked))
                pm, _, pl = p_heat.play(p_s, corner)
                p_heat.load, p_heat.locked = keep
            else:
                pm, _, pl = p_heat.play(p_s, corner)
            if buff and spirit.buff == "pay":
                pm *= 1.0 + spirit.amount
            outcome = resolve_stance(p_s, o_s)
            if meter:  # SPIRIT hook 3: fill
                meter.clash(p_s, outcome, pl)
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
        p_phases = []
        if cfg.player_qte_profile or cfg.player_timing is not None or cfg.player_quality is not None:
            q_time = cfg.player_timing if cfg.player_timing is not None else cfg.player_quality
            wm = cfg.qte_window_mod + (spirit.amount if buff and spirit.buff == "qte" else 0.0)  # SPIRIT hook 4
            p_qte = raw_qte_score(r, profile=cfg.player_qte_profile,
                                  q_time=None if cfg.player_qte_profile else q_time, window_mod=wm)
        else:
            cb = get_player_qte(turn_num)
            if isinstance(cb, (list, tuple)) and len(cb) == 3 and not isinstance(cb, (str, bytes)):
                p_phases = [phase_raw_qte(v) for v in cb]
                p_qte = mean_phase_qte(cb)
            else:
                p_qte = cb
        if meter:
            meter.end_turn()
        turn_state = TurnState(turn_number=turn_num, player_stances=p_stances, opponent_stances=o_stances,
                               player_qte=p_qte, opponent_qte=OPPONENT_QTE, player_heat_mults=p_mults,
                               opponent_heat_mults=o_mults, player_qte_phases=p_phases)
        turn_result = resolve_turn(turn_state, player, opponent, main_trace, race_length=cfg.max_turns)
        turn_result.corner_type = corner
        turn_result.opponent_line = list(planned_line)
        result.player_total_progress += turn_result.player_progress
        result.opponent_total_progress += turn_result.opponent_progress
        result.turn_results.append(turn_result)
        if on_turn_complete:
            on_turn_complete(turn_num, turn_result, result.player_total_progress, result.opponent_total_progress)
        result.turns_played = turn_num
    if meter_out is not None and meter:
        meter_out.append((meter.acts, meter.buff_turns, meter.first))
    return result


class SpiritRunner(S.SimulationRunner):
    """SimulationRunner (same simulated player) on the spirit copy of the match path."""

    def __init__(self, cfg, spirit: Spirit | None = None, meter_out=None):
        super().__init__(cfg)
        self.spirit, self.meter_out = spirit, meter_out

    def run(self):
        c = self.cfg
        self._district, self._lap = race_setup(c)
        T = c.max_turns
        p, o = c.player_stats, c.opponent_stats
        r = (p.pow + p.en + p.han) / (o.pow + o.en + o.han)
        pq = self._play_quality(); self._pq = pq
        if pq is not None:
            q_read, q_time = pq
            qt = raw_qte_score(r, profile=c.player_qte_profile, q_time=None if c.player_qte_profile else q_time,
                               window_mod=c.qte_window_mod)
            self._q_read = q_read
            self._pace_q = c.player_pacing if c.player_pacing is not None else q_read
            V = r ** kappa_for_length(T)
            php, pho = S._phi(qt), S._phi(OPPONENT_QTE)
            self._V, self._php, self._pho = V, php, pho
            self._d_lock = V * (php[2] - php[1]) + (pho[1] - pho[0])
            sh = build_shares(p.pow, p.en, p.han)
            self._mf = [1.0 + STAT_M_W * (x - 1 / 3) for x in sh]
            self._plan_race(T)
        m = spirit_run_match(c, self._pick_stance, lambda t: self._rng.uniform(0.1, 1.0),
                             on_line_picked=self._on_line_picked, spirit=self.spirit, meter_out=self.meter_out)
        return m
