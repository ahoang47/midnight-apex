"""STRICT CLIMB (Barry, 2026-11-19, Austin 6:31 PM PT: "Do whatever it takes to make it such that it gets harder the higher up
the ladder it goes."). Rule G3c: strong 80/80 at the floor falls strictly kid1 > kid2 > mat1 > mat2 > oh1 > oh2 > boss, every
step >= 3.0 points, every rung measured at n = 6000. Start: climb70 floors/budgets. Boss and oh2 fixed (66-68 / 70-72).
Top-down repair: for j = oh1 .. kid1, if w[j] < w[j+1] + 3.0, raise rung j's r (lower its stats) by bisection until
w[j] in [w[j+1] + 3.5, w[j+1] + 5.0]; Wangan oh1 to 74-75 (Austin). -> climb_strict.json"""
import json, os
from multiprocessing import Pool
import climb_grid as CG, climb70 as C7
HERE = os.path.dirname(os.path.abspath(__file__))
D = C7.D; RUNGS = C7.RUNGS; N = 6000; SEED = 96_000_000


def w(i, j, r):
    var = C7.F.BOSS_VAR[i] if j == 6 else "V0"
    return CG.cell((var, D[i], C7.F.LV[RUNGS[j]], "80/80", round(r, 4), N, SEED))[1]


def district(i):
    r = [C7.FL[i][j] / 10 / C7.BUD[i][j] for j in range(7)]
    win = [w(i, j, r[j]) for j in range(7)]; start = list(win); log = []
    for j in range(4, -1, -1):
        lo_t, hi_t = (74.0, 75.0) if (D[i] == "wangan" and j == 4) else (win[j + 1] + 3.5, win[j + 1] + 5.0)
        if win[j] >= win[j + 1] + 3.0 and not (D[i] == "wangan" and j == 4 and not lo_t <= win[j] <= hi_t):
            continue
        lo, hi = (r[j], r[j] + 0.08) if win[j] < lo_t else (r[j] - 0.08, r[j]); tr = []
        for _ in range(10):
            mid = (lo + hi) / 2; v = w(i, j, mid); tr.append((round(mid, 4), v))
            if lo_t <= v <= hi_t: break
            lo, hi = (mid, hi) if v < lo_t else (lo, mid)
        log.append(dict(rung=RUNGS[j], r_old=round(r[j], 4), r_new=round(mid, 4), win_old=win[j], win_new=v, target=[round(lo_t, 2), round(hi_t, 2)], trace=tr))
        r[j] = round(mid, 4); win[j] = v
    bud_new = [round(C7.FL[i][j] / 10 / r[j], 2) for j in range(7)]
    steps = [round(win[j] - win[j + 1], 2) for j in range(6)]
    return dict(d=D[i], start=start, win=win, r=[round(x, 4) for x in r], budget_old=C7.BUD[i], budget_new=bud_new, steps=steps,
                ok=all(s >= 3.0 for s in steps), changes=log)


if __name__ == "__main__":
    with Pool(3) as p:
        res = p.map(district, range(3))
    json.dump(res, open(os.path.join(HERE, "climb_strict.json"), "w"), indent=1)
    for x in res: print(json.dumps({k: v for k, v in x.items() if k != "changes"})); [print("   ", c) for c in x["changes"]]
