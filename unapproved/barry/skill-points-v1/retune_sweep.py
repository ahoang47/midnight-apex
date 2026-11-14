"""Off-tune win-rate sweep for the retune study (draft, Barry 2026-11-14). Every split the retune walk can reach has
HAN = 25 % (all three district tunes do), so splits are POW = p, HAN = 0.25, EN = 0.75 - p, p in 0.25..0.50.
Live engine, live stand-in tracks, 3 boss styles. Common random numbers: the same seeds for every p, so
delta(p) = win(p) - win(p_tune) has much less noise than either value."""
import os, sys, json, time
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "econ-v1-live-tracks"))
import livesim as LS
N = int(os.environ.get("N", "150"))
TAG = os.environ.get("TAG", "rt1")
PS = (0.25, 0.30, 0.35, 0.40, 0.45, 0.50)
RS = tuple(float(x) for x in os.environ.get("RS", "0.97,1.00,1.02,1.04,1.06,1.08,1.12,1.18").split(","))
PROFS = tuple(os.environ.get("PROFS", "c6060,c6080,c8060,c8080").split(","))
ONLY = os.environ.get("ONLY")   # optional "track1,track2" subset
LENS = tuple(int(x) for x in os.environ.get("LENS", "10,20,30").split(","))

def job(a):
    d, t, L, st, pr, r, p = a
    return a, LS.batch(d, t, L, st, pr, r, (p, 0.25, 0.75 - p), N, LS.seed_of(TAG, d, t, L, st, pr, r))

if __name__ == "__main__":
    TR = LS.tracks()
    jobs = [(d, t, L, st, pr, r, p) for d in TR for t in TR[d] if not ONLY or t in ONLY.split(",")
            for L in LENS for st in LS.STYLES for pr in PROFS for r in RS for p in PS]
    t0 = time.time(); res = {}
    with Pool(int(os.environ.get("PROCS", "8"))) as pool:
        for i, ((d, t, L, st, pr, r, p), v) in enumerate(pool.imap_unordered(job, jobs, chunksize=16)):
            res.setdefault(pr, {}).setdefault(str(L), {}).setdefault(t, {}).setdefault(f"{r:.3f}", {}).setdefault(f"{p:.3f}", []).append(v)
            if i % 2000 == 0:
                print(i, len(jobs), round(time.time() - t0), flush=True)
    out = {pr: {L: {t: {r: {p: sum(v) / len(v) for p, v in bp.items()} for r, bp in br.items()} for t, br in bt.items()}
                for L, bt in bl.items()} for pr, bl in res.items()}
    json.dump(dict(n_per_style=N, styles=list(LS.STYLES), ps=PS, rs=RS, tag=TAG, seconds=round(time.time() - t0),
                   tracks=[[d, t] for d in TR for t in TR[d]], win=out),
              open(os.path.join(HERE, f"retune_sweep_{TAG}.json"), "w"))
    print("done", round(time.time() - t0), "s", flush=True)
