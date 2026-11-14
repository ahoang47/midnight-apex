"""Exact-r 30-turn confirmations for the hardest-track pick (Austin 2026-11-13). Draft."""
import json, os, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livesim as LS
from run_sweep import TUNES
N = int(os.environ.get("N", 3000))
POINTS = json.loads(os.environ["POINTS"])   # [[district, track, r], ...]
OUT = os.environ["OUT"]
JOBS = [(d, t, r, st, pr) for d, t, r in POINTS for st in LS.STYLES for pr in LS.PROFILES]

def job(a):
    d, t, r, st, pr = a
    return a, LS.batch(d, t, 30, st, pr, r, TUNES[d], N, LS.seed_of("pc2", d, t, r, st, pr))

if __name__ == "__main__":
    t0 = time.time(); acc = {}
    with Pool(8) as p:
        for (d, t, r, st, pr), v in p.imap_unordered(job, JOBS):
            acc.setdefault(f"{d}|{t}|{r}|{pr}", []).append(v)
    out = dict(n_per_style=N, T=30, seconds=round(time.time() - t0),
               win={k: round(sum(v) / len(v), 2) for k, v in sorted(acc.items())})
    json.dump(out, open(os.path.join(LS.HERE, OUT), "w"), indent=1)
    print("done", out["seconds"])
