"""Pick one fixed tune per district on the live stand-in tracks: 60/60 at r=1.07 (cap), mean over 10/20/30 turns,
5 tracks, 3 boss styles. 21-split grid (each share 0.25-0.50 in 0.05 steps) + even."""
from __future__ import annotations
import json, os, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livesim as LS

N = int(os.environ.get("N", "150"))
SPLITS = sorted({(round(p, 2), round(h, 2), round(1 - p - h, 2)) for p in [0.25 + 0.05 * i for i in range(6)]
                 for h in [0.25 + 0.05 * i for i in range(6)] if 0.25 - 1e-9 <= 1 - p - h <= 0.50 + 1e-9}) + [(1/3, 1/3, 1/3)]


def job(a):
    d, t, L, st, tune = a
    return a, LS.batch(d, t, L, st, "c6060", 1.07, tune, N, LS.seed_of("tune", d, t, L, st))


def main():
    TR = LS.tracks(); jobs = [(d, t, L, st, tu) for d in TR for t in TR[d] for L in LS.LENGTHS for st in LS.STYLES for tu in SPLITS]
    t0 = time.time(); res = {}
    with Pool(8) as p:
        for (d, t, L, st, tu), v in p.imap_unordered(job, jobs, chunksize=4):
            res.setdefault(d, {}).setdefault(str(tu), {}).setdefault(str(L), []).append(v)
    out = {}
    for d in res:
        rows = []
        for tu, byL in res[d].items():
            m = {L: sum(v) / len(v) for L, v in byL.items()}
            rows.append(dict(tune=tu, mean=round(sum(m.values()) / 3, 2), **{f"L{L}": round(x, 2) for L, x in m.items()}))
        rows.sort(key=lambda x: -x["mean"]); out[d] = rows[:8]
    json.dump(dict(n=N, r=1.07, profile="c6060", seconds=round(time.time() - t0), top=out), open(os.path.join(LS.HERE, "tune_screen.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
