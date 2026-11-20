"""PLAYER JOURNEY engine grid (Barry, 2026-11-19), Round 1 Street. Same protocol as climb_grid.py (hard track, 3 boss styles,
ties half, district tune, opponent 300 units, encounter_type "boss") but with a continuous skill q = read = timing = pacing.
Levels: "r10" 10-turn even opponent (kids, wild encounters, non-mandatory races), "r20" 20-turn even (mat/oh),
"boss" 30-turn Street boss shape 25/25/50 with kappa x0.5 (recommended Street-boss lever). -> journey_grid.json"""
import json, os, time
from multiprocessing import Pool
import climb_grid as CG
from climb_grid import E, C, CombatantStats, MatchConfig, SimulationRunner
HERE = os.path.dirname(os.path.abspath(__file__))
N = int(os.environ.get("N", "1500")); D = "street"
Q = [round(0.50 + 0.05 * i, 2) for i in range(7)]
RG = {"r10": [round(0.96 + 0.02 * i, 2) for i in range(14)], "r20": [round(0.94 + 0.02 * i, 2) for i in range(12)],
      "boss": [round(0.94 + 0.02 * i, 2) for i in range(8)]}
SPEC = {"r10": (10, 1.0, False), "r20": (20, 1.0, False), "boss": (30, 0.5, True)}


def cell(a):
    lv, q, r = a; T, ks, boss = SPEC[lv]
    E.KAPPA_BY_LENGTH.clear(); E.KAPPA_BY_LENGTH.update({k: v * ks for k, v in CG.KAPPA0.items()})
    sp, sh, se = E.DISTRICT_TUNE[D]; bp, bh, be = E.BOSS_STAT_SHARES[D] if boss else (1 / 3, 1 / 3, 1 / 3)
    tot = 300.0 * r; w = 0.0; m = 0
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(N // 3):
            cfg = MatchConfig(player_stats=CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50),
                              opponent_stats=CombatantStats(name="Opponent", pow=300 * bp, en=300 * be, han=300 * bh, level=50),
                              max_turns=T, seed=97_000_000 + si * 100_000 + k, district=D,
                              corners=list(C.official_tracks()[D][E.BOSS_HARD_TRACK[D]]), player_read=q, player_timing=q,
                              player_pacing=q, boss_style=st, encounter_type="boss")
            mm = SimulationRunner(cfg).run().match; x, y = mm.player_total_progress, mm.opponent_total_progress
            w += 1.0 if x > y else 0.5 if x == y else 0.0; m += 1
    return a, round(100 * w / m, 2)


if __name__ == "__main__":
    J = [(lv, q, r) for lv in RG for q in Q for r in RG[lv]]; t0 = time.time()
    with Pool(8) as p:
        res = p.map(cell, J, chunksize=1)
    json.dump(dict(n=N, q=Q, r=RG, cells=[[lv, q, r, w] for (lv, q, r), w in res]), open(os.path.join(HERE, "journey_grid.json"), "w"))
    print(len(J), "cells", round(time.time() - t0), "s")
