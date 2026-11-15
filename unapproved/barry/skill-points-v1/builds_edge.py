"""Where does the all-in exploit start? POW-heavy on Street, EN-heavy on Wangan, at 80 / 90 / 95 % (rest split evenly). Draft."""
import os, sys, json
from multiprocessing import Pool
import builds as B
LS = B.LS
CASES = [("street", "POW"), ("wangan", "EN"), ("touge", "POW")]
def tune(stat, a):
    b = (1 - a) / 2
    return {"POW": (a, b, b), "HAN": (b, a, b), "EN": (b, b, a)}[stat]
def job(x):
    d, stat, a, t, L, st, pr = x
    return x, LS.batch(d, t, L, st, pr, B.R[d], tune(stat, a), B.N, LS.seed_of("sp1", d, t, L, st, pr))
if __name__ == "__main__":
    TR = LS.tracks()
    jobs = [(d, s, a, t, L, st, pr) for d, s in CASES for a in (0.80, 0.90, 0.95) for t in TR[d] for L in LS.LENGTHS
            for st in LS.STYLES for pr in ("c8080", "c6060")]
    res = {}
    with Pool(8) as p:
        for (d, s, a, t, L, st, pr), v in p.imap_unordered(job, jobs, chunksize=8):
            res.setdefault(f"{d} {s} {a}", {}).setdefault(pr, {}).setdefault(t, {}).setdefault(L, []).append(v)
    out = {}
    for k, byp in res.items():
        d = k.split()[0]
        for pr, bt in byp.items():
            mean = {L: round(sum(sum(bt[t][L]) / 3 for t in bt) / len(bt), 1) for L in (10, 20, 30)}
            out.setdefault(k, {})[pr] = dict(mean=mean, hard30=round(sum(bt[B.HARD[d]][30]) / 3, 1))
    json.dump(out, open("builds_edge.json", "w"), indent=1)
    for k, v in out.items(): print(k, v)
