"""CLIMB draft: Street boss follow-up (Barry, 2026-11-19), n = 6000 per cell. V0 at full r 1.052 (just under 80/80 = 95), and
K50 (kappa x0.5 on story races) at full r 1.062 / 1.070, to see whether lower stat weight lets an under-built strong reader win
more against the EN-heavy Street boss. -> climb_street_check.json"""
import json, os
from multiprocessing import Pool
import climb_grid as CG
HERE = os.path.dirname(os.path.abspath(__file__))
N = 6000; CAP0, CAP1 = 3000.0, 3532.0
CASES = [("V0", 1.052), ("K50", 1.062), ("K50", 1.070)]


def jobs():
    out = []
    for var, rf in CASES:
        for prof in ("60/60", "80/80"):
            out.append(((var, rf, "full", prof), (var, "street", "boss", prof, rf, N, 93_000_000)))
        for f in (0.60, 0.65, 0.70):
            out.append(((var, rf, "%d%%" % round(100 * f), "80/80"), (var, "street", "boss", "80/80", round(rf * (CAP0 + f * (CAP1 - CAP0)) / CAP1, 4), N, 93_000_000)))
    return out


def run(t):
    tag, a = t; _, w = CG.cell(a); return tag, a[4], w


if __name__ == "__main__":
    with Pool(8) as p:
        res = p.map(run, jobs(), chunksize=1)
    rows = [dict(var=t[0], full_r=t[1], build=t[2], prof=t[3], r=r, n=N, win=w) for t, r, w in res]
    json.dump(dict(n=N, rows=rows), open(os.path.join(HERE, "climb_street_check.json"), "w"), indent=1)
    for x in rows: print(x)
