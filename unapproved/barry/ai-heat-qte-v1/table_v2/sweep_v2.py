"""Regenerate the progression win-rate table under the live AI QTE model (Austin 2026-11-19) -> sweep_v2.json.

Same method as the tool that built winrate_g2_live_tracks_v1.json (econ-v1-live-tracks run_sweep.py / livesim.py /
export_live_table.py, commit 6d3641f): live engine, 15 live stand-in tracks, 4 profiles, 10/20/30 turns, 3 boss styles,
r 0.94-1.24 step 0.01, N=300 races per track x style x r, ties half, mean over styles; player on the district tune,
opponent 300 units. New: the AI QTE model is whatever the live sim runs (seeded 0.80 / 0.08 / 0.60-1.00 since 2026-11-19),
and Street gets a second 30-turn set against the Street boss shape (equations.BOSS_STAT_SHARES, POW/HAN/EN 25/25/50).
Exact-r point checks (N=2000 per style) on each boss's hardest track at the new boss r, all 4 profiles.
Usage: python3 sweep_v2.py   (8 processes; ~30 min)
"""
from __future__ import annotations
import json, os, sys, time
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "sim")))
from velocity_shift import combat as C, simulation as S, equations as E
from velocity_shift.models import CombatantStats, MatchConfig

PROFILES = {"c6060": (0.6, 0.6, 0.6), "c6080": (0.6, 0.8, 0.8), "c8060": (0.8, 0.6, 0.6), "c8080": (0.8, 0.8, 0.8)}
LENGTHS = (10, 20, 30)
R_GRID = [round(0.94 + 0.01 * i, 2) for i in range(31)]
N = int(os.environ.get("N", "300")); NP = int(os.environ.get("NP", "2000"))
EVEN = (1 / 3, 1 / 3, 1 / 3)


def seed_of(*parts):
    h = 20261119
    for p in parts:
        for ch in str(p):
            h = (h * 131 + ord(ch)) % 1_000_000_007
    return h * 10


def batch(d, track, L, style, prof, r, opp_shape, n, seed):
    q, qt, pace = PROFILES[prof]
    tot = 300.0 * r; sp, sh, se = E.DISTRICT_TUNE[d]; bp, bh, be = opp_shape
    player = CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50)
    opponent = CombatantStats(name="Opponent", pow=300.0 * bp, en=300.0 * be, han=300.0 * bh, level=50)
    corners = list(C.official_tracks()[d][track]); w = 0.0
    for k in range(n):
        cfg = MatchConfig(player_stats=player, opponent_stats=opponent, max_turns=L, seed=seed + k, district=d, corners=corners,
                          player_read=q, player_timing=qt, player_pacing=pace, boss_style=style, encounter_type="boss")
        m = S.SimulationRunner(cfg).run().match
        a, b = m.player_total_progress, m.opponent_total_progress
        w += 1.0 if a > b else 0.5 if a == b else 0.0
    return 100.0 * w / n


def job(a):
    kind, d, t, L, st, pr, shape, rs, n = a
    return a, [batch(d, t, L, st, pr, r, shape, n, seed_of("v2", kind, d, t, L, st, pr, r)) for r in rs]


def main():
    TR = C.official_tracks(); names = [(d, t) for d in sorted(TR) for t in sorted(TR[d])]
    boss_shape = tuple(E.BOSS_STAT_SHARES["street"])
    jobs = [("q", d, t, L, st, pr, EVEN, R_GRID, N) for (d, t) in names for L in LENGTHS for st in E.BOSS_STYLES for pr in PROFILES]
    jobs += [("q_boss", d, t, 30, st, pr, boss_shape, R_GRID, N) for (d, t) in names if d == "street" for st in E.BOSS_STYLES for pr in PROFILES]
    for d in ("street", "wangan", "touge"):
        kind = "q_boss" if any(abs(x - 1 / 3) > 1e-9 for x in E.BOSS_STAT_SHARES[d]) else "q"
        jobs += [("pt_" + kind, d, E.BOSS_HARD_TRACK[d], 30, st, pr, tuple(E.BOSS_STAT_SHARES[d]), [E.BOSS_TARGET_R[d]], NP)
                 for st in E.BOSS_STYLES for pr in PROFILES]
    jobs.sort(key=lambda a: -(a[3] * len(a[7]) * a[8]))
    t0 = time.time(); acc = {}; done = 0
    with Pool(8) as p:
        for a, v in p.imap_unordered(job, jobs):
            kind, d, t, L, st, pr, shape, rs, n = a
            acc.setdefault((kind, pr, L, t), {}).setdefault(st, dict(zip(rs, v))); done += 1
            if done % 60 == 0:
                print(f"{time.time() - t0:6.0f}s {done}/{len(jobs)}", flush=True)
    out = {"n": N, "np": NP, "r": R_GRID, "tracks": [list(x) for x in names], "boss_shape_street": list(boss_shape),
           "seconds": round(time.time() - t0), "cells": []}
    for (kind, pr, L, t), bys in sorted(acc.items()):
        rs = sorted(next(iter(bys.values())))
        out["cells"].append(dict(kind=kind, profile=pr, turns=L, track=t,
                                 pts=[[r, round(sum(bys[s][r] for s in bys) / len(bys), 3)] for r in rs]))
    json.dump(out, open(os.path.join(HERE, "sweep_v2.json"), "w"))
    print("wrote sweep_v2.json", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
