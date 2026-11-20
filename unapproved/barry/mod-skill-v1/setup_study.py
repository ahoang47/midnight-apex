"""SETUP STUDY engine runs (Barry, 2026-11-19, Austin direct). Live SimulationRunner via climb_grid.cell (hard track, 3 boss
styles, ties half, district tune, opponent 300 units, encounter "boss"); n = 2000 per non-boss cell, 6000 per boss cell.
Crews stat-locked at the climb budgets (climb_floor.budgets: V0 rungs; bosses Street 332.58 with kappa x0.5 on that race,
Wangan 390.35, Touge 437.06). Race XP is FIXED per race (stat-locked crews, fixed rewards): story 29x5+32 / 58x5+73 /
60x5+77 (boss win pays cash, no XP), wild encounter and non-mandatory win 13 / 12 / 14.
Setups (structure S1, one crew per round): M = mandatory per round 7 / 10 / 13 / 20 = 7 story + 0 / 3 / 6 / 13 required wild
encounters, placed in the gaps before kid2, mat1, mat2, oh1, oh2, boss: 0 | 0,1,0,1,0,1 | 1 each | 2,2,2,2,2,3.
Non-mandatory cap c = XP-paying non-mandatory wins per round: none (round ceiling only), 8, 12, 15.
S2 (every crew every round) is checked separately with stat-locked crews (s2_cells). -> setup_study.json"""
import json, os
from multiprocessing import Pool
import climb_grid as CG, climb_floor as F
HERE = os.path.dirname(os.path.abspath(__file__))
D = F.D; RUNGS = F.RUNGS; CAP = F.CAP; WE_XP = F.WE_XP
GAPS = {7: (0, 0, 0, 0, 0, 0), 10: (0, 1, 0, 1, 0, 1), 13: (1, 1, 1, 1, 1, 1), 20: (2, 2, 2, 2, 2, 3)}
CAPS = {"none": 10 ** 6, "8": 8, "12": 12, "15": 15}
BUD = [F.budgets(i) for i in range(3)]


def mand_xp(M, i):
    """cumulative mandatory XP on arrival at each rung of round i"""
    x = [0]
    for j in range(6):
        x.append(x[-1] + F.STORY_XP[i][j] + GAPS[M][j] * WE_XP[i])
    return x


def builds(M, c):
    """floor (mandatory) and max (capped) points per round/rung"""
    fl, mx = [], []; ef = em = CAP[0]
    for i in range(3):
        x = mand_xp(M, i)
        f = [min(CAP[i + 1], ef + v) for v in x]
        m = [min(CAP[i + 1], em + v + CAPS[c] * WE_XP[i]) for v in x]
        fl.append(f); mx.append(m); ef, em = f[-1], m[-1]
    return fl, mx


def key(i, j, prof, pts):
    return (i, j, prof, int(round(pts)))


def run(k):
    i, j, prof, pts = k; n = 6000 if j == 6 else 2000
    var = F.BOSS_VAR[i] if j == 6 else "V0"
    _, w = CG.cell((var, D[i], F.LV[RUNGS[j]], prof, round(pts / 10 / BUD[i][j], 4), n, 96_000_000)); return k, w


# S2 = every crew each round, 7 story races per round, mapping by tier (stated in SETUP-STUDY.md):
# R1: kid1+kid2 of Street, Wangan, Touge + Street mat1; R2: Wangan mat1, Touge mat1, mat2 x3, Street oh1, Wangan oh1;
# R3: Touge oh1, oh2 x3, boss x3. Stat-locked crews keep their S1 stats; player build = S1 M20 floor at the same round slot.
S2 = [[(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2)],
      [(1, 2), (2, 2), (0, 3), (1, 3), (2, 3), (0, 4), (1, 4)],
      [(2, 4), (0, 5), (1, 5), (2, 5), (0, 6), (1, 6), (2, 6)]]


def s2_cells():
    fl, _ = builds(20, "none"); out = []
    for rr in range(3):
        for slot, (i, j) in enumerate(S2[rr]):
            out.append(((rr, slot, i, j), fl[rr][slot]))
    return out


def run_s2(t):
    (rr, slot, i, j), pts = t; var = F.BOSS_VAR[i] if j == 6 else "V0"
    r = round(pts / 10 / BUD[i][j], 4); _, w = CG.cell((var, D[i], F.LV[RUNGS[j]], "80/80", r, 2000, 96_500_000))
    return dict(round=rr + 1, slot=slot + 1, crew=D[i], rung=RUNGS[j], pts=pts, r=r, w8080=w)


if __name__ == "__main__":
    ks = set()
    for M in GAPS:
        for c in CAPS:
            fl, mx = builds(M, c)
            for i in range(3):
                for j in range(7):
                    ks.add(key(i, j, "60/60", fl[i][j])); ks.add(key(i, j, "80/80", fl[i][j]))
                    ks.add(key(i, j, "60/60", mx[i][j]))
                ks.add(key(i, 6, "80/80", mx[i][6]))
    ks = sorted(ks, key=lambda k: -k[1])
    print(len(ks), "cells", flush=True)
    with Pool(8) as p:
        res = p.map(run, ks, chunksize=1)
        s2 = p.map(run_s2, s2_cells(), chunksize=1)
    json.dump(dict(cells=[[*k, w] for k, w in res], s2=s2), open(os.path.join(HERE, "setup_study.json"), "w"), indent=1)
    print("done")
