"""resources-v3 full runs. 9 batches x 1000 races (seeds 20261112..20261120), all 15 stand-in laps x 10/20/30 turns x
3 boss styles, 21-tune grid + exact even spread (common random numbers across tunes).
Usage: python3 run_v3.py CAND [CAND ...]   (candidates defined in CANDS; settings chosen from screen_*.json)
Writes results_v3_<CAND>.npz and results_v3_meta.json."""
from __future__ import annotations
import json, sys, time
from multiprocessing import Pool
import numpy as np
import resources_v3 as R

E = R.E
import os
N = int(os.environ.get("V3_N", 1000))
SEEDS = [20261112 + b for b in range(9)]
GRID = R.tune_grid(); TUNES = np.vstack([GRID, [[1 / 3, 1 / 3, 1 / 3]]])
TR = sorted(R.tracks().items())
LENGTHS = (10, 20, 30)
CANDS = json.load(open("candidates.json"))          # name -> cfg (+ "_cap")
KEYS = ("win", "ov", "ovc", "lock", "pen", "rlock", "rov", "rovplay", "rswitch", "streak", "limp")


def measures(cap):
    avg = E.raw_qte_score(cap, profile="average")
    return {"avg_cap": (cap, 0.6, avg, {}, {}),
            "perf_0.8": (0.8, 1.0, 1.0, {}, {}),
            "perf_1.0": (1.0, 1.0, 1.0, {}, {}),
            "greedy_cap": (cap, 0.6, avg, {"ration": False}, {}),
            "ration2_cap": (cap, 0.6, avg, {}, {"RATION_LAMBDA": 2.0, "RATION_H": 4}),
            "read1_cap": (cap, 1.0, avg, {}, {}),
            "random_cap": (cap, 0.0, avg, {"mode": "random"}, {})}


def job(a):
    cand, mname, b, ti, T, st = a
    cfg = CANDS[cand]; cap = cfg["_cap"]
    r, q, qt, kw, over = measures(cap)[mname]
    c = {k: v for k, v in cfg.items() if not k.startswith("_")}; c.update(over)
    (d, name), lap = TR[ti]
    o = R.run_new(TUNES, r, d, lap, T, st, q, qt, N, SEEDS[b], cfg=c, **kw)
    rc = np.maximum(o["read_clash"].sum(1), 1)
    v = np.stack([o["win"].mean(1), o["ov_turns"].mean(1) / T, o["ov_clash"].mean(1) / (3 * T), o["lock_turns"].mean(1) / T, o["pen_loss"].mean(1) / (3 * T),
                  o["read_lock"].sum(1) / rc, o["read_ov"].sum(1) / rc, o["read_ov_play"].sum(1) / rc, o["read_switch"].sum(1) / rc,
                  o["lock_streak"].mean(1), o["limp"].mean(1) / (3 * T)])
    extra = None
    if mname == "avg_cap":
        lt = np.zeros((len(TUNES), 30)); lt[:, :T] = o["lock_t"]
        ot = np.zeros((len(TUNES), 30)); ot[:, :T] = o["ov_t"]
        hist = np.zeros((len(TUNES), 31)); hist[:, :T + 1] = o["lock_hist"]
        extra = dict(lock_t=lt, ov_t=ot, hist=hist, n_locks=o["n_locks"], dur=o["lock_dur_sum"], lock_res=o["lock_res"],
                     streak_max=o["lock_streak"].max(1), streak_p90=np.percentile(o["lock_streak"], 90, axis=1))
    return a, v, extra


if __name__ == "__main__":
    t0 = time.time()
    for cand in sys.argv[1:]:
        out = {}
        with Pool(8) as p:
            for mname in measures(CANDS[cand]["_cap"]):
                arr = np.zeros((9, len(TR), 3, 3, len(KEYS), len(TUNES)))
                ex = {}
                jobs = [(cand, mname, b, ti, T, st) for b in range(9) for ti in range(len(TR)) for T in LENGTHS for st in R.STYLES]
                for (c_, m_, b, ti, T, st), v, extra in p.imap_unordered(job, jobs, chunksize=4):
                    k = LENGTHS.index(T); s = R.STYLES.index(st)
                    arr[b, ti, k, s] = v
                    if extra:
                        for kk, vv in extra.items():
                            if kk not in ex:
                                ex[kk] = np.zeros((9, len(TR), 3, 3) + np.shape(vv))
                            ex[kk][b, ti, k, s] = vv
                out[mname] = arr
                for kk, vv in ex.items():
                    out[f"{mname}|{kk}"] = vv
                np.savez_compressed(f"results_v3_{cand}.npz", **out)
                print(f"{time.time()-t0:7.0f}s {cand} {mname} avg win {100*arr[:, :, :, :, 0].mean():.1f}", flush=True)
    meta = dict(seeds=SEEDS, n=N, tracks=[list(k) for k, _ in TR], laps=[lap for _, lap in TR], lengths=LENGTHS, styles=list(R.STYLES),
                keys=KEYS, tunes=TUNES.tolist(), candidates=CANDS,
                measures={c: {k: [v[0], v[1], v[2], v[3], v[4]] for k, v in measures(CANDS[c]["_cap"]).items()} for c in CANDS})
    json.dump(meta, open("results_v3_meta.json", "w"), indent=1, default=str)
    print("done", time.time() - t0)
