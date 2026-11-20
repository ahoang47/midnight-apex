"""AI-pacing boss fix (n = 6,000, strong 80/80 at floor): scan bosses that the search left outside 66-68.
Usage: AI_PACE=1 FALLOFF_T=t python3 pace_boss_fix.py street:0:330,333,336 touge:2:443,445"""
import json, os, sys
os.environ.setdefault("SIM", "/tmp/pp/sim")
from multiprocessing import Pool
import repin as R
J = []
for a in sys.argv[1:]:
    m, rnd, bs = a.split(":")
    J += [(m, int(rnd), 6, float(B), 0.8, "floor", 6000) for B in bs.split(",")]
if __name__ == "__main__":
    with Pool(8) as p: res = p.map(R.verify_job, J, chunksize=1)
    out = [(m, B, v) for (m, rnd, j, B, q, w, n), v in res]
    print(out)
    f = os.path.join(R.HERE, "pace_boss_fix.json"); d = json.load(open(f)) if os.path.exists(f) else {}
    d.setdefault(os.environ.get("FALLOFF_T", "lockcap"), []).extend(out); json.dump(d, open(f, "w"), indent=1)
