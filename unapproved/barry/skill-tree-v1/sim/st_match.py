"""Skill-tree thought-experiment engine (Barry draft 2026-11-18, touge-race @ 7e0febe).
A copy of spirit-meter-v1's match path (itself a copy of velocity_shift.match.run_match; sim/ untouched) with:
  * spirit buff "pay" (payoff x (1 + amount), the prototype) or "stakes" (additive clash_stakes form from design/05 §1:
    clash_mult = 1 + b x outcome, i.e. win x (1 + b), tie x 1, loss x (1 - b), on buff turns);
  * driver-tree effects [PH]: QTE window_mod (Steady hands / In the zone), HEAT_RELEASE offset on the player's gauges
    (Cool down), meter fill / buff turns / loss fill / activations via the Spirit fields (Fired up, Hold it, Kindling, Second wind);
  * optional carried state for back-to-back races (heat fill fractions, locks, meter value) and an end-state return;
  * progress accounting by outcome on buff turns (to calibrate b).
No potions (cut 2026-11-18)."""
from __future__ import annotations
import copy, os, sys
from dataclasses import dataclass, replace
from random import Random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "spirit-meter-v1"))
import spirit_match as SM  # noqa: E402
from spirit_match import Spirit, Meter, S  # noqa: E402
from velocity_shift.models import MatchResult, TurnState, ClashResult, ClashContext, StanceOutcome  # noqa: E402
from velocity_shift.combat import resolve_turn, pick_line, corner_at_turn  # noqa: E402
from velocity_shift.equations import resolve_stance, OPPONENT_QTE, raw_qte_score, STAT_M_W, kappa_for_length  # noqa: E402
from velocity_shift.heat import HeatGauges, track_wear, boss_stance, boss_line_weights, build_shares  # noqa: E402
from velocity_shift.trace import TraceLogger  # noqa: E402
from velocity_shift.match import race_setup  # noqa: E402

SPIRIT_A = Spirit(base=6, size=100, match_k=1.0, loss_frac=0.25, tie_frac=0.5, buff="pay", amount=0.25, dur=3, max_acts=1)


@dataclass
class Driver:
    window: float = 0.0     # added to qte_window_mod
    release: float = 0.0    # added to the player's HEAT_RELEASE
    fill: float = 0.0       # added to spirit base fill
    dur: int = 0            # added buff turns
    loss_fill: float | None = None
    acts_long: int = 0      # extra activations in 20-30-turn races


def apply_driver(sp: Spirit | None, drv: Driver, T: int) -> Spirit | None:
    if sp is None:
        return None
    return replace(sp, base=sp.base + drv.fill, dur=sp.dur + drv.dur,
                   loss_frac=sp.loss_frac if drv.loss_fill is None else drv.loss_fill,
                   max_acts=sp.max_acts + (drv.acts_long if T >= 20 else 0))


def run(cfg, pick, on_line_picked, spirit, drv: Driver, carry: dict | None = None, out: dict | None = None):
    player = copy.copy(cfg.player_stats); opponent = copy.copy(cfg.opponent_stats)
    district, lap = race_setup(cfg); T = cfg.max_turns
    res = MatchResult(player_name=player.name, opponent_name=opponent.name, total_turns=T)
    tr = TraceLogger(); rng = Random(cfg.seed)
    r = (player.pow + player.en + player.han) / (opponent.pow + opponent.en + opponent.han)
    wear = track_wear(district, lap)
    ph = HeatGauges.for_player(player.pow, player.en, player.han, r, wear)
    ph.release += drv.release
    oh = HeatGauges.for_boss(opponent.pow, opponent.en, opponent.han, wear)
    meter = Meter(spirit, build_shares(player.pow, player.en, player.han)) if spirit else None
    if carry:
        ph.load = [f * c for f, c in zip(carry["fill"], ph.cap)]; ph.locked = list(carry["locked"])
        if meter is not None:
            meter.v = carry.get("meter", 0.0)
    acc = [0.0, 0.0, 0.0]   # player progress on buff turns by outcome (loss, tie, win)
    for tn in range(1, T + 1):
        corner = corner_at_turn(lap, tn)
        w = boss_line_weights(district, corner, tn - 1, T, cfg.boss_style) if cfg.boss_style != "balanced" else None
        line = pick_line(district, corner, rng, weights=w)
        on_line_picked(tn, corner, line)
        ph.begin_turn(); oh.begin_turn()
        buff = meter.start_turn() if meter else False
        ps, os_, pms, oms, hist, outs = [], [], [], [], [], []
        for ci in range(3):
            o_s = boss_stance(oh, line[ci]); om, _, _ = oh.play(o_s, corner)
            if ph.all_locked():
                p_s = ph.least_loaded(only_unlocked=False)
            else:
                p_s = pick(tn, ci, ClashContext(tn, ci, T, district, corner, lap, r, ph, list(hist)))
            pm, _, pl = ph.play(p_s, corner)
            outcome = resolve_stance(p_s, o_s)
            if buff:
                pm *= (1.0 + spirit.amount) if spirit.buff == "pay" else (1.0 + spirit.amount * outcome.value)
            if meter:
                meter.clash(p_s, outcome, pl)
            hist.append(ClashResult(ci, p_s, o_s, outcome)); outs.append(outcome)
            ps.append(p_s); os_.append(o_s); pms.append(pm); oms.append(om)
        ph.end_turn(corner); oh.end_turn(corner)
        q = cfg.player_timing if cfg.player_timing is not None else cfg.player_quality
        pq = raw_qte_score(r, q_time=q, window_mod=cfg.qte_window_mod)
        if meter:
            meter.end_turn()
        t = resolve_turn(TurnState(turn_number=tn, player_stances=ps, opponent_stances=os_, player_qte=pq, opponent_qte=OPPONENT_QTE,
                                   player_heat_mults=pms, opponent_heat_mults=oms), player, opponent, tr, race_length=T)
        if buff:   # un-buffed progress by outcome (for calibration)
            for o, g, m in zip(outs, t.player_clash_progress, pms):
                base_m = m / ((1.0 + spirit.amount) if spirit.buff == "pay" else (1.0 + spirit.amount * o.value)) if m else 0.0
                acc[o.value + 1] += g * (base_m / m if m else 0.0)
        res.player_total_progress += t.player_progress; res.opponent_total_progress += t.opponent_progress
    if out is not None:
        out.update(acc=acc, acts=meter.acts if meter else 0,
                   end=dict(fill=ph.fill(), locked=list(ph.locked), meter=meter.v if meter else 0.0))
    return res


class Runner(S.SimulationRunner):
    def __init__(self, cfg, spirit=SPIRIT_A, drv: Driver = Driver(), carry=None, out=None):
        cfg = copy.copy(cfg); cfg.qte_window_mod = cfg.qte_window_mod + drv.window
        super().__init__(cfg)
        self.spirit = apply_driver(spirit, drv, cfg.max_turns); self.drv, self.carry, self.out = drv, carry, out

    def run(self):
        c = self.cfg; self._district, self._lap = race_setup(c); T = c.max_turns
        p, o = c.player_stats, c.opponent_stats; r = (p.pow + p.en + p.han) / (o.pow + o.en + o.han)
        q_read, q_time = self._play_quality(); self._pq = (q_read, q_time)
        qt = raw_qte_score(r, q_time=q_time, window_mod=c.qte_window_mod)
        self._q_read = q_read; self._pace_q = c.player_pacing if c.player_pacing is not None else q_read
        V = r ** kappa_for_length(T); php, pho = S._phi(qt), S._phi(OPPONENT_QTE)
        self._V, self._php, self._pho = V, php, pho
        self._d_lock = V * (php[2] - php[1]) + (pho[1] - pho[0])
        self._mf = [1.0 + STAT_M_W * (x - 1 / 3) for x in build_shares(p.pow, p.en, p.han)]
        self._plan_race(T)
        return run(c, self._pick_stance, self._on_line_picked, self.spirit, self.drv, self.carry, self.out)


# Driver builds by round [PH]. Points(L) = floor(3 + 2 sqrt(L)) [PH, front-loaded]: L0 3, L12 9, L29 13, L46 16, L64 19.
BUILDS = {
    1: ("L0, 3 pts: Steady hands, Cool down, Fired up", Driver(window=0.05, release=0.05, fill=1)),
    2: ("L12, 9 pts: + Hold it, Kindling, Ride the edge (not simulated)", Driver(window=0.05, release=0.05, fill=1, dur=1, loss_fill=0.4)),
    3: ("L29, 13 pts: + In the zone, Scout (UI only)", Driver(window=0.10, release=0.05, fill=1, dur=1, loss_fill=0.4)),
    4: ("L64, 19 pts: + Feather (not simulated), Second wind", Driver(window=0.10, release=0.05, fill=1, dur=1, loss_fill=0.4, acts_long=1)),
}


def check_identity(n=30):
    """Driver() + SPIRIT_A == spirit_match.SpiritRunner(SPIRIT_A)."""
    sys.path.insert(0, os.path.join(HERE, "..", "..", "spirit-meter-v1"))
    import importlib.util as iu
    sp = iu.spec_from_file_location("sc", os.path.join(HERE, "..", "..", "spirit-meter-v1", "core.py")); SC = iu.module_from_spec(sp); sp.loader.exec_module(SC)
    from velocity_shift import combat as C, equations as E
    bad = 0
    for d in SC.TUNE:
        trk = next(iter(C.official_tracks()[d]))
        for k in range(n):
            c = SC.cfg_of(d, trk, 30, E.BOSS_STYLES[k % 3], 0.7, 0.7, 0.7, 1.05, SC.TUNE[d], 4242 + k)
            a = SM.SpiritRunner(c, SPIRIT_A).run(); b = Runner(c).run()
            bad += abs(a.player_total_progress - b.player_total_progress) > 1e-9 or abs(a.opponent_total_progress - b.opponent_total_progress) > 1e-9
    return bad, 3 * n
