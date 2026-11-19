"""CLIMB draft engine verification (Barry, 2026-11-19): the recommended variant from climb_eval.json at n = 6000 per cell
(2000 per boss style), same protocol as climb_grid.py. Cells: every rung at its expected-build r (60/60 and 80/80), plus the
boss at full build (60/60, 80/80) and at 60 % / 70 % of the round's mod XP (80/80). -> climb_verify.json"""
import json, os, sys
from multiprocessing import Pool
import climb_grid as CG
HERE = os.path.dirname(os.path.abspath(__file__))
VAR = os.environ.get("VAR", "V0"); N = int(os.environ.get("N", "6000"))
EV = json.load(open(os.path.join(HERE, "climb_eval.json")))
# optional: boss set from a FULL-build r per district (engine-picked), e.g. BOSS_FULL='{"street": 1.062}'
BOSS_FULL = json.loads(os.environ.get("BOSS_FULL", "{}"))
OUT = os.environ.get("OUT", "climb_verify.json")
LV = {"kid1": "kid", "kid2": "kid", "mat1": "mat", "mat2": "mat", "oh1": "oh", "oh2": "oh", "boss": "boss"}
CAP = (3000.0, 3532.0, 4044.0, 4628.0)


def jobs():
    out = []
    for o in EV["variants"][VAR]:
        d = o["district"]; i = o["rnd"] - 1
        b = dict(o["rows"][-1]); pb = b["points"]
        if d in BOSS_FULL:
            b["full_r"] = BOSS_FULL[d]; b["r"] = round(BOSS_FULL[d] * pb / CAP[i + 1], 4)
        for x in o["rows"][:-1] + [b]:
            for prof in ("60/60", "80/80"):
                out.append(((x["rung"], "expected"), (VAR, d, LV[x["rung"]], prof, x["r"], N, 93_000_000)))
        for prof in ("60/60", "80/80"):
            out.append((("boss", "full"), (VAR, d, "boss", prof, b["full_r"], N, 93_000_000)))
        for f in (0.60, 0.70):
            r = round(b["r"] * (CAP[i] + f * (CAP[i + 1] - CAP[i])) / pb, 4)
            out.append((("boss", "%d%%" % round(100 * f)), (VAR, d, "boss", "80/80", r, N, 93_000_000)))
    return out


def run(t):
    tag, a = t; a2, w = CG.cell(a); return tag, a2, w


if __name__ == "__main__":
    J = jobs()
    with Pool(8) as p:
        res = p.map(run, sorted(J, key=lambda t: -CG.LEVELS[t[1][2]]), chunksize=1)
    rows = [dict(rung=t[0], build=t[1], d=a[1], prof=a[3], r=a[4], n=a[5], win=w) for t, a, w in res]
    json.dump(dict(variant=VAR, n=N, boss_full=BOSS_FULL, rows=rows), open(os.path.join(HERE, OUT), "w"), indent=1)
    for d in ("street", "wangan", "touge"):
        print(d, [(x["rung"], x["build"], x["prof"], x["r"], x["win"]) for x in rows if x["d"] == d])
