"""Boss trade-off scan: boss stat total x {0.985, 0.995, 1.0, 1.005, 1.015} of the search value; strong/weak at floor and max,
n = 6,000 each. Shows whether the boss band (66-68), G2a (weak at max >= 30) and G5 (strong at max <= 95) can hold together."""
import json, os, sys
from multiprocessing import Pool
os.environ.setdefault("SIM", "/tmp/pp/sim")
import repin as R

F = (0.985, 0.995, 1.0, 1.005, 1.015)


def job(t):
    m, rnd, B, q, which = t
    return t, R.verify_job((m, rnd, 6, B, q, which, 6000))[1]


if __name__ == "__main__":
    bud = json.load(open(os.path.join(R.HERE, "search.json")))["budgets"]
    J = [(m, rnd, round(bud[m][6] * f, 2), q, w) for m, rnd in (("street", 0), ("wangan", 1), ("touge", 2)) for f in F
         for q, w in ((0.8, "floor"), (0.6, "max"), (0.8, "max"), (0.6, "floor"))]
    with Pool(8) as p: res = p.map(job, J, chunksize=1)
    out = {}
    for (m, rnd, B, q, w), v in res:
        out.setdefault(m, {}).setdefault(str(B), {})[("strong_" if q == 0.8 else "weak_") + w] = v
    json.dump(out, open(os.path.join(R.HERE, "boss_scan.json"), "w"), indent=1)
    for m in out:
        for B in sorted(out[m], key=float): print(m, B, out[m][B])
