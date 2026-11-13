"""v4 kappa-per-length / cap screen. For one base config (argv[1] = JSON) and each race length T separately (KAPPA_T only
touches T-turn races), scans the kappa multiplier and the cap. All 15 stand-in laps x 3 boss styles, N 300, seed 11
(screen only; full runs re-measure). Each player on its own best tune per cell.
Writes kfit_<tag>.json (argv[2] = tag)."""
import sys, json, numpy as np
from multiprocessing import Pool
import resources_v4 as R
E = R.E
TUNES = np.vstack([R.tune_grid(), [[1 / 3] * 3]])
TR = sorted(R.tracks().items())
N, SEED = 300, 11
BASE = json.loads(sys.argv[1]); TAG = sys.argv[2]
import os
KS = [float(x) for x in os.environ.get("KF_KS", "0.75,1.0,1.25,1.5,1.75,2.0,2.5").split(",")]
CAPS = [float(x) for x in os.environ.get("KF_CAPS", "1.05,1.10").split(",")]
LENS = [int(x) for x in os.environ.get("KF_LENS", "10,20,30").split(",")]


def meas(cap):
    avg = E.raw_qte_score(cap, profile="average")
    return {"perf08": (0.8, 1.0, 1.0, "reserve", 1.0), "perf10": (1.0, 1.0, 1.0, "reserve", 1.0),
            "avg": (cap, 0.6, avg, "mix", 0.6), "c8080": (cap, 0.8, 0.8, "mix", 0.8)}


def job(a):
    T, k, cap, m, ti, st = a
    r, q, qt, pac, pq = meas(cap)[m]
    cfg = dict(BASE, **{f"KAPPA_{T}": k}, PACE_Q=pq)
    (d, _), lap = TR[ti]
    o = R.run_new(TUNES, r, d, lap, T, st, q, qt, N, SEED, cfg=cfg, pacing=pac)
    w = o["win"].mean(1)
    return a, float(w[:21].max()), float(w[21])


if __name__ == "__main__":
    jobs = [(T, k, cap, m, ti, st) for T in LENS for k in KS for cap in CAPS for m in meas(cap)
            if not (m.startswith("perf") and cap != CAPS[0]) for ti in range(len(TR)) for st in R.STYLES]
    res = {}
    with Pool(8) as p:
        for a, w, e in p.imap_unordered(job, jobs, chunksize=8):
            res[a] = (w, e)
    out = []
    for T in LENS:
        for k in KS:
            for cap in CAPS:
                row = dict(T=T, kappa=k, cap=cap)
                for m in meas(cap):
                    if m.startswith("perf") and cap != CAPS[0]:
                        continue
                    v = np.array([res[(T, k, cap, m, ti, st)] for ti in range(len(TR)) for st in R.STYLES])
                    row[m] = round(100 * v[:, 0].mean(), 1); row[m + "_even"] = round(100 * v[:, 1].mean(), 1)
                out.append(row); print(json.dumps(row), flush=True)
    json.dump(dict(base=BASE, rows=out), open(f"kfit_{TAG}.json", "w"), indent=1)
