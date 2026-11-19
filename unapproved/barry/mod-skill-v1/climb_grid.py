"""CLIMB draft engine grid (Barry, 2026-11-19, Austin direct). NOT live: levers are patched in-process only.
Live SimulationRunner, each district's hard track (BOSS_HARD_TRACK), 3 boss styles, ties half, player on the district tune,
opponent 300 units (Street boss shape at the 30-turn boss), encounter_type "boss" (same protocol as the v2 tables).
Variants (lever settings):
  V0   live: kappa x1, AI QTE mean 0.80 at every rung
  K50  kappa x0.50 on story races (stats matter half as much)
  K70  kappa x0.70
  Q    AI QTE mean rising up the ladder: kid 0.70, mat 0.76, oh 0.82, boss 0.86 (sd 0.08, clamp 0.60-1.00), kappa x1
  K70Q kappa x0.70 + the rising AI QTE
Grid: r 0.92-1.12 step 0.04, profiles 60/60 and 80/80, levels kid (10 t) / mat (20) / oh (20) / boss (30).
Usage: N=600 python3 climb_grid.py  -> climb_grid.json"""
import json, os, sys, time
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "sim"))
from velocity_shift import combat as C, equations as E
from velocity_shift.models import CombatantStats, MatchConfig
from velocity_shift.simulation import SimulationRunner

N = int(os.environ.get("N", "600"))
R = [round(0.92 + 0.04 * i, 2) for i in range(6)]
LEVELS = {"kid": 10, "mat": 20, "oh": 20, "boss": 30}
QRISE = {"kid": 0.70, "mat": 0.76, "oh": 0.82, "boss": 0.86}
VARIANTS = {"V0": (1.0, False), "K50": (0.5, False), "K70": (0.7, False), "Q": (1.0, True), "K70Q": (0.7, True)}
KAPPA0 = dict(E.KAPPA_BY_LENGTH)


def cell(a):
    var, d, lv, prof, r, n, seed0 = a
    ks, qr = VARIANTS[var]
    E.KAPPA_BY_LENGTH.clear(); E.KAPPA_BY_LENGTH.update({k: v * ks for k, v in KAPPA0.items()})
    q = 0.6 if prof == "60/60" else 0.8; T = LEVELS[lv]
    sp, sh, se = E.DISTRICT_TUNE[d]
    bp, bh, be = E.BOSS_STAT_SHARES[d] if lv == "boss" else (1 / 3, 1 / 3, 1 / 3)
    ratio = (QRISE[lv] / E.OPPONENT_QTE) if qr else None
    tot = 300.0 * r; w = 0.0; m_ = 0
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(n // 3):
            cfg = MatchConfig(player_stats=CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50),
                              opponent_stats=CombatantStats(name="Opponent", pow=300 * bp, en=300 * be, han=300 * bh, level=50),
                              max_turns=T, seed=seed0 + si * 100_000 + k, district=d,
                              corners=list(C.official_tracks()[d][E.BOSS_HARD_TRACK[d]]), player_read=q, player_timing=q,
                              player_pacing=q, boss_style=st, encounter_type="boss", opponent_qte_ratio=ratio)
            mm = SimulationRunner(cfg).run().match; x, y = mm.player_total_progress, mm.opponent_total_progress
            w += 1.0 if x > y else 0.5 if x == y else 0.0; m_ += 1
    return a, round(100 * w / m_, 2)


def jobs(n=N, variants=VARIANTS, rs=R, seed0=91_000_000):
    out = []
    for var in variants:
        lvs = ("kid", "mat", "oh", "boss") if VARIANTS[var][1] else ("kid", "mat", "boss")   # mat == oh without the QTE rise
        for d in ("street", "wangan", "touge"):
            for lv in lvs:
                for prof in ("60/60", "80/80"):
                    for r in rs:
                        out.append((var, d, lv, prof, r, n, seed0))
    return out


if __name__ == "__main__":
    t0 = time.time(); J = jobs(); res = []
    with Pool(8) as p:
        for i, (a, v) in enumerate(p.imap_unordered(cell, sorted(J, key=lambda a: -LEVELS[a[2]]), chunksize=2)):
            res.append(dict(var=a[0], d=a[1], lv=a[2], prof=a[3], r=a[4], n=a[5], win=v))
            if i % 100 == 0: print(f"{time.time() - t0:5.0f}s {i}/{len(J)}", flush=True)
    json.dump(dict(n=N, r=R, qrise=QRISE, variants={k: dict(kappa_scale=v[0], qte_rise=v[1]) for k, v in VARIANTS.items()},
                   kappa_live=KAPPA0, cells=res, seconds=round(time.time() - t0)), open(os.path.join(HERE, "climb_grid.json"), "w"), indent=1)
    print("done", round(time.time() - t0), "s", len(res))
