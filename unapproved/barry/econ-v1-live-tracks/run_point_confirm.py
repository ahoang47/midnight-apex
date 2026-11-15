"""Exact-r confirmation cells (30-turn, N per style) at the proposed boss / finale r. Draft."""
import json, os, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livesim as LS
from run_sweep import TUNES
N = int(os.environ.get("N", 1500))
TR = LS.tracks()
POINTS = [("touge", t, 1.070) for t in TR["touge"]] + [("touge", t, 1.062) for t in TR["touge"]] + \
         [("street", "S1_Shibuya_Grid", r) for r in (1.037, 1.043)] + [("wangan", t, 1.041) for t in TR["wangan"]]
JOBS = [(d, t, r, st, pr) for d, t, r in POINTS for st in LS.STYLES for pr in LS.PROFILES]

def job(a):
    d, t, r, st, pr = a
    return a, LS.batch(d, t, 30, st, pr, r, TUNES[d], N, LS.seed_of("pt", d, t, r, st, pr))

if __name__ == "__main__":
    t0 = time.time(); acc = {}
    with Pool(8) as p:
        for (d, t, r, st, pr), v in p.imap_unordered(job, JOBS):
            acc.setdefault(f"{d}|{t}|{r}|{pr}", []).append(v)
    out = dict(n_per_style=N, T=30, seconds=round(time.time() - t0),
               win={k: round(sum(v) / len(v), 2) for k, v in sorted(acc.items())})
    json.dump(out, open(os.path.join(LS.HERE, "point_confirm.json"), "w"), indent=1)
    print("done", out["seconds"])
