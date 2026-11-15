"""No-respec check: the Touge tune (45/25/30) and the Street tune (50/25/25) / Wangan tune (25/25/50) carried into the
other districts (the 'even' and cap50 rows of builds.json cover the rest). Draft."""
import json
from multiprocessing import Pool
import builds as B
LS = B.LS
def job(x):
    d, tu, t, L, st, pr = x
    return x, LS.batch(d, t, L, st, pr, B.R[d], B.TUNE[tu], B.N, LS.seed_of("sp1", d, t, L, st, pr))
if __name__ == "__main__":
    TR = LS.tracks()
    jobs = [(d, "touge", t, L, st, pr) for d in ("street", "wangan") for t in TR[d] for L in LS.LENGTHS for st in LS.STYLES for pr in ("c8080", "c6060")]
    res = {}
    with Pool(8) as p:
        for (d, tu, t, L, st, pr), v in p.imap_unordered(job, jobs, chunksize=8):
            res.setdefault(d, {}).setdefault(pr, {}).setdefault(t, {}).setdefault(L, []).append(v)
    out = {}
    for d, byp in res.items():
        for pr, bt in byp.items():
            out.setdefault(f"touge tune on {d}", {})[pr] = dict(mean={L: round(sum(sum(bt[t][L]) / 3 for t in bt) / len(bt), 1) for L in (10, 20, 30)},
                                                               hard30=round(sum(bt[B.HARD[d]][30]) / 3, 1))
    json.dump(out, open("builds_fixed.json", "w"), indent=1)
    for k, v in out.items(): print(k, v)
