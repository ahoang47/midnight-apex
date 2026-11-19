"""ai-heat-qte-v1 (Barry DRAFT 2026-11-19, unapproved). Austin via Gordon: AI heat parity + AI QTE cap.

Read-only use of the live sim (sim/velocity_shift). Nothing live is edited: the opponent QTE and the
opponent heat rules are swapped in-process by patching the names match.py / simulation.py imported.

  python3 ai_heat_qte.py boss   [N]   # live boss checks (30 turns, hardest track, 3 boss styles), N per style
  python3 ai_heat_qte.py touge  [N]   # 10-turn Touge test race, parity blocks, 5 Touge tracks x 3 styles, N per track/style
  python3 ai_heat_qte.py rscan  [N]   # boss r scan under the recommended option (retune knock-on)
Outputs: <mode>.json next to this file.
"""
import json, math, os, sys
from multiprocessing import Pool
from random import Random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "sim"))
from velocity_shift import combat as C, equations as E, match as M, simulation as S, heat as H
from velocity_shift.models import CombatantStats, MatchConfig
from velocity_shift.simulation import SimulationRunner

HARD = {"street": "S1_Shibuya_Grid", "wangan": "W3_C1_Outer", "touge": "T3_Usui_Esses"}
BOSS_R = {"street": 1.044, "wangan": 1.0548, "touge": 1.0702}
BLOCKS = json.load(open(os.path.join(HERE, "..", "touge-race-parity", "blocks.json")))["cars"]

# AI QTE options: ("fixed", v) or ("normal", mean, sd, lo, hi) drawn once per turn from a seeded RNG separate from the
# match RNG, rounded with E.round_qte_score like every live QTE score.
QTE_OPTS = {
    "Q100": ("fixed", 1.0),            # live baseline (OPPONENT_QTE = 1.0)
    "F95": ("fixed", 0.95),
    "F90": ("fixed", 0.90),
    "F85": ("fixed", 0.85),
    "F80": ("fixed", 0.80),
    "D90": ("normal", 0.90, 0.07, 0.70, 1.00),
    "D85": ("normal", 0.85, 0.08, 0.65, 0.98),
    "F70": ("fixed", 0.70),
    "F60": ("fixed", 0.60),
    # ("skill", q): the AI times like a simulated player of timing skill q on its OWN visible zone,
    # E[s] = raw_qte_score(r_opp, q_time=q) with r_opp = AI total / player total (same model as the player).
    "SK90": ("skill", 0.9),
    "SK80": ("skill", 0.8),
}
HEAT_OPTS = ("boss_rules", "player_rules", "player_rules_r1")

_state = {"rng": None, "opt": None, "r_opp": 1.0, "heat": "boss_rules"}
_orig_resolve = M.resolve_turn
_orig_for_boss = H.HeatGauges.for_boss.__func__


def _ai_qte():
    o = _state["opt"]
    if o[0] == "fixed":
        return o[1]
    if o[0] == "skill":
        return E.raw_qte_score(_state["r_opp"], q_time=o[1])
    _, mu, sd, lo, hi = o
    return E.round_qte_score(min(hi, max(lo, _state["rng"].gauss(mu, sd))))


def _resolve(ts, *a, **k):
    ts.opponent_qte = _ai_qte()
    return _orig_resolve(ts, *a, **k)


def _for_boss(cls, pw, en, hn, wear):
    h = _state["heat"]
    if h == "boss_rules":
        return _orig_for_boss(cls, pw, en, hn, wear)
    r = _state["r_opp"] if h == "player_rules" else 1.0
    return cls(H.build_shares(pw, en, hn), r, wear)       # player rules: HEAT_CAP_TURNS/RECOVERY/RELEASE 0.3, lock on passive


M.resolve_turn = _resolve
H.HeatGauges.for_boss = classmethod(_for_boss)


def run_one(cfg, opt, heat):
    _state["rng"] = Random(cfg.seed * 31 + 424_242)
    _state["heat"] = heat
    p, o = cfg.player_stats, cfg.opponent_stats
    _state["r_opp"] = (o.pow + o.en + o.han) / (p.pow + p.en + p.han)
    _state["opt"] = QTE_OPTS[opt]
    S.OPPONENT_QTE = _ai_qte() if QTE_OPTS[opt][0] == "skill" else QTE_OPTS[opt][1]   # player's expectation (mean)
    m = SimulationRunner(cfg).run().match
    a, b = m.player_total_progress, m.opponent_total_progress
    return 1.0 if a > b else 0.5 if a == b else 0.0


def stats(w, n):
    p = w / n
    return dict(n=n, win=round(100 * p, 2), se=round(100 * math.sqrt(p * (1 - p) / n), 2))


def boss_cell(a):
    d, r, prof, opt, heat, N = a
    q = 0.6 if prof == "60/60" else 0.8
    sp, sh, se = E.DISTRICT_TUNE[d]; tot = 300.0 * r; w = 0.0; n = 0
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(N):
            cfg = MatchConfig(player_stats=CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50),
                              opponent_stats=CombatantStats(name="Opponent", pow=100.0, en=100.0, han=100.0, level=50),
                              max_turns=30, seed=77_000_000 + si * 100_000 + k, district=d,
                              corners=list(C.official_tracks()[d][HARD[d]]), player_read=q, player_timing=q,
                              player_pacing=q, boss_style=st, encounter_type="boss")
            w += run_one(cfg, opt, heat); n += 1
    return dict(d=d, r=r, prof=prof, opt=opt, heat=heat, **stats(w, n))


def touge_cell(a):
    pcar, ocar, prof, opt, heat, N = a
    q = 0.6 if prof == "60/60" else 0.8
    P, O = BLOCKS[pcar], BLOCKS[ocar]; w = 0.0; n = 0
    tracks = C.official_tracks()["touge"]
    for ti, tname in enumerate(sorted(tracks)):
        for si, st in enumerate(E.BOSS_STYLES):
            for k in range(N):
                cfg = MatchConfig(player_stats=CombatantStats(name="Player", pow=P["pow"] / 10, en=P["en"] / 10, han=P["han"] / 10, level=50),
                                  opponent_stats=CombatantStats(name="Opponent", pow=O["pow"] / 10, en=O["en"] / 10, han=O["han"] / 10, level=50),
                                  max_turns=10, seed=88_000_000 + ti * 1_000_000 + si * 100_000 + k, district="touge",
                                  corners=list(tracks[tname]), player_read=q, player_timing=q, player_pacing=q, boss_style=st)
                w += run_one(cfg, opt, heat); n += 1
    return dict(player=P["tune"], opponent=O["tune"], prof=prof, opt=opt, heat=heat, **stats(w, n))


if __name__ == "__main__":
    mode = sys.argv[1]
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 800
    opts = sys.argv[3].split(",") if len(sys.argv) > 3 else list(QTE_OPTS)
    if mode == "boss":
        jobs = [(d, BOSS_R[d], p, o, "boss_rules", N) for o in opts for d in BOSS_R for p in ("60/60", "80/80")]
        jobs += [(d, BOSS_R[d], p, "Q100", h, N) for h in HEAT_OPTS[1:] for d in BOSS_R for p in ("60/60", "80/80")]
        fn = boss_cell
    elif mode == "touge":
        pairs = [("brz", "mx5"), ("brz", "gr_corolla"), ("gr_corolla", "brz")]   # touge-vs-touge mirror, touge vs wangan, wangan vs touge
        jobs = [(a, b, p, o, "boss_rules", N) for o in opts for a, b in pairs for p in ("60/60", "80/80")]
        jobs += [(a, b, p, "Q100", h, N) for h in HEAT_OPTS[1:] for a, b in pairs for p in ("60/60", "80/80")]
        fn = touge_cell
    elif mode == "rscan":
        rs = json.loads(sys.argv[4])                       # {"street":[...], ...}
        jobs = [(d, r, p, o, "boss_rules", N) for o in opts for d in rs for r in rs[d] for p in ("60/60", "80/80")]
        fn = boss_cell
    if len(sys.argv) > 3 and mode != "rscan":                # extra options only: no heat rows, append to the file
        jobs = [j for j in jobs if j[4] == "boss_rules"]
    with Pool(8) as pool:
        rows = pool.map(fn, jobs, chunksize=1)
    path = os.path.join(HERE, f"{mode}.json")
    if len(sys.argv) > 3 and mode != "rscan" and os.path.exists(path):
        old = json.load(open(path)); keys = {(x["opt"], x["heat"]) for x in rows}
        rows = [x for x in old if (x["opt"], x["heat"]) not in keys] + rows
    json.dump(rows, open(path, "w"), indent=1)
    for x in rows:
        print(x)
