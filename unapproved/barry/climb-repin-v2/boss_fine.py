"""Boss fine-tune check (n = 6,000 per cell): Wangan 395.80, Touge 450.07."""
import json, os
os.environ.setdefault("SIM", "/tmp/pp/sim")
from multiprocessing import Pool
import repin as R
J = [(m, rnd, 6, B, q, w, 6000) for m, rnd, B in (("wangan", 1, 395.80), ("touge", 2, 450.07), ("touge_pp", 2, 450.07))
     for q, w in ((0.8, "floor"), (0.6, "max"), (0.8, "max"), (0.6, "floor"))]
if __name__ == "__main__":
    with Pool(8) as p: res = p.map(R.verify_job, J, chunksize=1)
    out = {}
    for (m, rnd, j, B, q, w, n), v in res: out.setdefault(m, {"boss_budget": B})[("strong_" if q == 0.8 else "weak_") + w] = v
    json.dump(out, open(os.path.join(R.HERE, "boss_fine.json"), "w"), indent=1); print(out)
