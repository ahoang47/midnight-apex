"""STRICT CLIMB SCORECARD (G3c, Austin 2026-11-19 6:31 PM PT): budgets from climb_strict.json, EVERY cell n = 6000. Base: OH2 ~70 % + BOSS 66-68 % VARIANT (climb65 + Austin 2026-11-19 6:26 PM: "Make the old head a bit easier, about 70%, and keep the boss at 66-68%"): Street oh2 r 0.9865, Wangan oh2 r 0.9927 (oh2_70.py), Touge oh2 unchanged; oh2 and boss cells n = 6000. Base: full 9-criterion scorecard (Barry, 2026-11-19, Austin: "Think we can get a strong story player to
65-70%?"). Setup S1 M13r cap 15 with lever (b): the boss floor is raised (story XP in the oh2 -> boss gap) to Street 3392,
Wangan 3904, Touge 4467; boss budgets and max build unchanged. Next round's entry rises with it; R2/R3 kid1..oh2 budgets are
rescaled to keep each rung's old r (same win rates). G3a repairs (the boss drop breaks it otherwise): Wangan kid1 r 1.0645,
Touge kid1 r 1.1018 (80/80 97.5+), Touge oh2 r 1.018 (boss <= oh2 + 1). Engine n = 2000 non-boss, 6000 boss.
-> climb65.json"""
import json, os
from multiprocessing import Pool
import climb_grid as CG, climb_floor as F
HERE = os.path.dirname(os.path.abspath(__file__))
D = F.D; RUNGS = F.RUNGS; CAP = F.CAP; WE = F.WE_XP
OLD_FL = [F.floors(i) for i in range(3)]; OLD_B = [F.budgets(i) for i in range(3)]
BOSS_FL = (3392, 3904, 4467)
GAP = (55, 82, 88)               # M13r floor step kid1 -> oh2 per round (story + 1 wild encounter)
FIX_R = {(1, 0): 1.0645, (2, 0): 1.1018, (2, 5): 1.018, (0, 5): 0.9865, (1, 5): 0.9927}


def floors():
    out = []; e = CAP[0]
    for i in range(3):
        f = [e + GAP[i] * j for j in range(6)] + [BOSS_FL[i]]; out.append(f); e = f[-1]
    return out


FL = floors()


def budgets(i):
    b = []
    for j in range(6):
        r = FIX_R.get((i, j), OLD_FL[i][j] / 10 / OLD_B[i][j]); b.append(round(FL[i][j] / 10 / r, 2))
    return b + [OLD_B[i][6]]


BUD = [x["budget_new"] for x in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "climb_strict.json")))]


def maxb():
    out = []; e = CAP[0]
    for i in range(3):
        m = [min(CAP[i + 1], e + (FL[i][j] - FL[i][0]) + 15 * WE[i]) for j in range(7)]; out.append(m); e = m[-1]
    return out


MX = maxb()


def run(t):
    i, j, prof, tag, pts = t; n = 6000; var = F.BOSS_VAR[i] if j == 6 else "V0"
    r = round(pts / 10 / BUD[i][j], 4); _, w = CG.cell((var, D[i], F.LV[RUNGS[j]], prof, r, n, 96_000_000))
    return dict(d=D[i], rung=RUNGS[j], prof=prof, build=tag, pts=pts, r=r, win=w)


if __name__ == "__main__":
    J = []
    for i in range(3):
        for j in range(7):
            J += [(i, j, "80/80", "floor", FL[i][j]), (i, j, "60/60", "floor", FL[i][j]), (i, j, "60/60", "max", MX[i][j])]
        J.append((i, 6, "80/80", "max", MX[i][6]))
    J.sort(key=lambda t: -t[1])
    with Pool(8) as p:
        rows = p.map(run, J, chunksize=1)
    W = lambda d, rung, prof, b: next(x["win"] for x in rows if x["d"] == d and x["rung"] == rung and x["prof"] == prof and x["build"] == b)
    cur = {d: [W(d, r, "80/80", "floor") for r in RUNGS] for d in D}
    sc = dict(
        G1a=[W(d, "boss", "80/80", "floor") for d in D],
        G1b=[round(sum(100 / max(w, 0.01) - 1 for w in cur[d]), 2) for d in D],
        G2a=min((W(d, r, "60/60", "max"), d + " " + r) for d in D for r in RUNGS),
        G3a=[(all(cur[d][k + 1] <= cur[d][k] + 1.0 for k in range(6)), round(cur[d][0] - cur[d][6], 2)) for d in D],
        G3b=[round(W(d, "boss", "80/80", "floor") - W(d, "boss", "60/60", "max"), 2) for d in D],
        G4a=min(min(c) for c in cur.values()),
        G4b=[W(d, "boss", "60/60", "floor") for d in D],
        G5=[W(d, "boss", "80/80", "max") for d in D],
        G3c=[[round(cur[d][k] - cur[d][k + 1], 2) for k in range(6)] for d in D],
        boss_6060_max=[W(d, "boss", "60/60", "max") for d in D])
    P = dict(G1a=all(65 <= x <= 70 for x in sc["G1a"]), G1b=all(1.5 <= x <= 4 for x in sc["G1b"]), G2a=sc["G2a"][0] >= 30,
             G3a=all(m and dr >= 30 for m, dr in sc["G3a"]), G3b=min(sc["G3b"]) >= 10, G4a=sc["G4a"] >= 40,
             G4b=max(sc["G4b"]) <= 10, G5=max(sc["G5"]) <= 95, G3c=all(s >= 3.0 for st in sc["G3c"] for s in st))
    out = dict(floors=FL, budgets=BUD, max=MX, rows=rows, curves=cur, score=sc, P=P)
    json.dump(out, open(os.path.join(HERE, "climb_g3c.json"), "w"), indent=1)
    print("floors", FL); print("budgets", BUD); print("max", MX)
    for d in D: print(d, cur[d])
    print(json.dumps(sc)); print(P)
