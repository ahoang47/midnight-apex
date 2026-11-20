"""Non-crew-stat fix check (NOT applied): move a round's max-build cap (E.MS_ROUND_CAP_POINTS) and measure the boss cells at
the release-0.5 boss totals (n = 6,000). Usage: RELEASE=0.5 python3 cap_fix.py wangan:1:395.2:4084,4124 street:0:336.5:3502,3472"""
import json, os, sys
from multiprocessing import Pool
import repin as R
J = []
for a in sys.argv[1:]:
    m, rnd, B, ps = a.split(":")
    J += [(m, int(rnd), float(B), float(p), q) for p in ps.split(",") for q in (0.6, 0.8)]


def job(t):
    m, rnd, B, pts, q = t
    return t, round(R.win(m, rnd, 6, B, q, pts, 6000), 2)


if __name__ == "__main__":
    with Pool(8) as p: res = p.map(job, J, chunksize=1)
    f = os.path.join(R.HERE, "cap_fix.json"); d = json.load(open(f)) if os.path.exists(f) else {}
    for (m, rnd, B, pts, q), v in res: d.setdefault(f"{m} boss {B} max {pts}", {})["weak_max" if q == 0.6 else "strong_max"] = v
    json.dump(d, open(f, "w"), indent=1)
    for k, v in sorted(d.items()): print(k, v)
