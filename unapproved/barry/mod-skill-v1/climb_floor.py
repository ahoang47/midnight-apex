"""CLIMB + STAT-LOCK FLOORS draft (Barry, 2026-11-19), engine n = 6000 per cell (same protocol as climb_grid.py).
Austin: every story crew character is stat-locked (fixed stats); the lock is a FLOOR on the player's earned car points
(base 3000 + all mod XP earned, assigned or not) to challenge them. No underdog bonus; no softening for 60/60.
Floor F = the mandatory-path earned total on arrival at the rung (integer story XP schedule below), so the floor never blocks
the mandatory path and blocks skipping the required wild encounters. Rung budgets = climb_eval.json V0 (non-boss); bosses set
by full-build r (Street 1.062 with kappa x0.5 on that race only, Wangan 1.036, Touge 1.0589; climb_boss_fix / street_check).
Outputs: per-rung win % at the floor build (60/60, 80/80); boss at 60/65/70 % and full; 60/60 grind cost to reach 30 % at
mat1..boss (optional wild-encounter wins on top of the mandatory path, capped at the round cap) and its cash. -> climb_floor.json"""
import json, math, os
from multiprocessing import Pool
import climb_grid as CG
HERE = os.path.dirname(os.path.abspath(__file__))
N = 6000; SEED = 95_000_000
D = ("street", "wangan", "touge"); RUNGS = ("kid1", "kid2", "mat1", "mat2", "oh1", "oh2", "boss")
LV = dict(kid1="kid", kid2="kid", mat1="mat", mat2="mat", oh1="oh", oh2="oh", boss="boss")
CAP = (3000, 3532, 4044, 4628)
WE_XP = (13, 12, 14); WE_CASH = (550.0, 632.5, 742.5)
# integer mandatory-path XP schedule (pre-boss story XP 177 / 363 / 377; boss win pays cash, its XP is the next round's entry)
STORY_XP = ((29, 29, 29, 29, 29, 32), (58, 58, 58, 58, 58, 73), (60, 60, 60, 60, 60, 77))
WE_BEFORE = (2, 2, 2, 2, 2, 3)            # required wild-encounter wins between rung j and rung j+1 (13 per round)
BOSS_FULL_R = (1.062, 1.036, 1.0589); BOSS_VAR = ("K50", "V0", "V0")
EV = json.load(open(os.path.join(HERE, "climb_eval.json")))


def floors(i):
    p = [floors(i - 1)[-1] if i else CAP[0]]          # round entry = previous boss floor (no optionals, boss pays no XP)
    for j in range(6):
        p.append(p[-1] + STORY_XP[i][j] + WE_BEFORE[j] * WE_XP[i])
    return p


def budgets(i):
    rows = EV["variants"]["V0"][i]["rows"]
    b = [x["budget"] for x in rows[:6]]
    b.append(round(CAP[i + 1] / 10 / BOSS_FULL_R[i], 2))
    return b


def var(i, j): return BOSS_VAR[i] if j == 6 else "V0"


def win(i, j, prof, pts):
    _, w = CG.cell((var(i, j), D[i], LV[RUNGS[j]], prof, round(pts / 10 / budgets(i)[j], 4), N, SEED)); return w


def table_job(t):
    i, j, prof, tag, pts = t; return t, win(i, j, prof, pts)


def grind_job(t):
    """Smallest k optional wins (each +WE_XP, points capped at the round cap) so that 60/60 >= 30 at rung j."""
    i, j = t; F = floors(i)[j]; xp = WE_XP[i]; kmax = math.ceil((CAP[i + 1] - F) / xp)
    pts = lambda k: min(CAP[i + 1], F + k * xp); seen = {}
    def w(k):
        if k not in seen: seen[k] = win(i, j, "60/60", pts(k))
        return seen[k]
    if w(kmax) < 30: return t, dict(k=None, at_cap=w(kmax), kmax=kmax, seen=seen)
    lo, hi = -1, kmax                                   # w(hi) >= 30
    if w(0) >= 30: hi = 0
    while hi - lo > 1:
        m = (lo + hi) // 2
        if w(m) >= 30: hi = m
        else: lo = m
    return t, dict(k=hi, pts=pts(hi), win=w(hi), win_prev=(w(hi - 1) if hi > 0 else None), cash=hi * WE_CASH[i], seen=seen)


if __name__ == "__main__":
    tj = []
    for i in range(3):
        F = floors(i)
        for j in range(7):
            for prof in ("60/60", "80/80"):
                tj.append((i, j, prof, "floor", F[j]))
        for f in (0.60, 0.70):
            tj.append((i, 6, "80/80", "%d%%" % round(100 * f), CAP[i] + f * (CAP[i + 1] - CAP[i])))
        for prof in ("60/60", "80/80"):
            tj.append((i, 6, prof, "full", CAP[i + 1]))
    gj = [(i, j) for i in range(3) for j in range(2, 7)]
    with Pool(8) as p:
        tr = p.map(table_job, tj, chunksize=1)
        gr = p.map(grind_job, gj, chunksize=1)
    out = dict(n=N, floors={D[i]: dict(zip(RUNGS, floors(i))) for i in range(3)},
               budgets={D[i]: dict(zip(RUNGS, budgets(i))) for i in range(3)},
               table=[dict(d=D[t[0]], rung=RUNGS[t[1]], prof=t[2], build=t[3], pts=t[4], r=round(t[4] / 10 / budgets(t[0])[t[1]], 4),
                           var=var(t[0], t[1]), win=w) for t, w in tr],
               grind=[dict(d=D[t[0]], rung=RUNGS[t[1]], **{k: v for k, v in g.items() if k != "seen"},
                           trace={str(k): v for k, v in sorted(g["seen"].items())}) for t, g in gr])
    json.dump(out, open(os.path.join(HERE, "climb_floor.json"), "w"), indent=1)
    print(json.dumps(out["floors"])); print(json.dumps(out["budgets"]))
    for x in out["table"]: print(x)
    for x in out["grind"]: print(x)
