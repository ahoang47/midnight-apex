"""CLIMB draft: engine fix-up of the boss r (Barry, 2026-11-19). climb_verify.py showed the grid interpolation misses the pair
on Street (full 80/80 96.47) and Wangan (full 60/60 27.08). Here the boss is set from FULL-build r candidates directly in the
engine (n = 6000): full 60/60 / 80/80, and the same boss at the expected build (65 %), 60 % and 70 % of the round's mod XP.
Variant V0 (live combat). -> climb_boss_fix.json"""
import json, os
from multiprocessing import Pool
import climb_grid as CG
HERE = os.path.dirname(os.path.abspath(__file__))
N = 6000
CAP = (3000.0, 3532.0, 4044.0, 4628.0); DIST = ("street", "wangan", "touge")
CANDS = {"street": (1.048, 1.050), "wangan": (1.034, 1.036), "touge": (1.0589,)}


def pts(i, f):
    return CAP[i] + f * (CAP[i + 1] - CAP[i])


def jobs():
    out = []
    for i, d in enumerate(DIST):
        for rf in CANDS[d]:
            for prof in ("60/60", "80/80"):
                out.append(((d, rf, "full", prof), ("V0", d, "boss", prof, rf, N, 93_000_000)))
            for f in (0.60, 0.65, 0.70):
                r = round(rf * pts(i, f) / CAP[i + 1], 4)
                for prof in (("60/60", "80/80") if f == 0.65 else ("80/80",)):
                    out.append(((d, rf, "%d%%" % round(100 * f), prof), ("V0", d, "boss", prof, r, N, 93_000_000)))
    return out


def run(t):
    tag, a = t; _, w = CG.cell(a); return tag, a[4], w


if __name__ == "__main__":
    with Pool(8) as p:
        res = p.map(run, jobs(), chunksize=1)
    rows = [dict(d=t[0], full_r=t[1], build=t[2], prof=t[3], r=r, n=N, win=w) for t, r, w in res]
    json.dump(dict(n=N, rows=rows), open(os.path.join(HERE, "climb_boss_fix.json"), "w"), indent=1)
    for x in rows: print(x)
