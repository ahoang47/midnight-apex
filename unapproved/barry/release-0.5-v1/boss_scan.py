"""Boss scan (n = 6,000 per cell): strong at floor, weak at max, strong at max for candidate boss totals.
Usage: RELEASE=0.5 python3 boss_scan.py street:0:337,338 wangan:1:396 ... -> appends to boss_scan.json"""
import json, os, sys
from multiprocessing import Pool
import repin as R
J = []
for a in sys.argv[1:]:
    m, rnd, bs = a.split(":")
    J += [(m, int(rnd), 6, float(B), q, w, 6000) for B in bs.split(",") for q, w in ((0.8, "floor"), (0.6, "max"), (0.8, "max"), (0.6, "floor"))]
if __name__ == "__main__":
    with Pool(8) as p: res = p.map(R.verify_job, J, chunksize=1)
    f = os.path.join(R.HERE, "boss_scan.json"); d = json.load(open(f)) if os.path.exists(f) else {}
    for (m, rnd, j, B, q, w, n), v in res:
        d.setdefault(f"{R.RELEASE} {m} {B}", {})[("strong_" if q == 0.8 else "weak_") + w] = v
    json.dump(d, open(f, "w"), indent=1)
    for k, v in sorted(d.items()): print(k, v)
