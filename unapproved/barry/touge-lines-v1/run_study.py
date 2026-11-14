"""Full / screen runs on the draft 10-variant track set, G2 heat rules, resources_v4b.

Usage:
  python3 run_study.py baseline
  V4_N=400 V4_SEEDS=1 V4_MEASURES=avg_cap,c8080,perf_0.8,perf_1.0,best_cap,greedy_cap,read1_best,rand_best python3 run_study.py baseline

Writes results_<tag>.npz and updates results_meta.json.
"""
from __future__ import annotations
import json, os, sys, time
from multiprocessing import Pool
import numpy as np

import model as M
import resources_v4b as R

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = ("win", "ov", "ovc", "lock", "pen", "rlock", "rov", "rovplay", "rswitch", "streak", "limp", "lockdur")
LENGTHS = (10, 20, 30)
# tag -> (line_edits or None, use_gravity)
CANDS = {
    "baseline": (None, True),            # draft tracks, current LINE_SET_C, Arthur gravity
    "baseline_nogravity": (None, False), # same tracks, no gravity (IR/DR flip only)
}

N = int(os.environ.get("V4_N", 1000))
N_SEEDS = int(os.environ.get("V4_SEEDS", 9))
SEEDS = [20261112 + b for b in range(N_SEEDS)]
ONLY = os.environ.get("V4_MEASURES")
GRID = R.tune_grid()
TUNES = np.vstack([GRID, [[1 / 3, 1 / 3, 1 / 3]]])


def measures(cap):
    avg = R.E.raw_qte_score(cap, profile="average")
    return {"avg_cap": (cap, 0.6, avg, {"pacing": "mix"}, {"PACE_Q": 0.6}),
            "perf_0.8": (0.8, 1.0, 1.0, {"pacing": "reserve"}, {}),
            "perf_1.0": (1.0, 1.0, 1.0, {"pacing": "reserve"}, {}),
            "c8080": (cap, 0.8, 0.8, {"pacing": "mix"}, {"PACE_Q": 0.8}),
            "best_cap": (cap, 0.6, avg, {"pacing": "reserve"}, {}),
            "greedy_cap": (cap, 0.6, avg, {"pacing": "greedy"}, {}),
            "read1_best": (cap, 1.0, avg, {"pacing": "reserve"}, {}),
            "read1_greedy": (cap, 1.0, avg, {"pacing": "greedy"}, {}),
            "rand_best": (cap, 1.0, avg, {"pacing": "reserve", "mode": "randguess"}, {}),
            "rand_greedy": (cap, 1.0, avg, {"pacing": "greedy", "mode": "randguess"}, {})}


def _init_worker(tag):
    edits, grav = CANDS[tag]
    M.apply(line_edits=edits, use_gravity=grav)


def job(a):
    tag, mname, b, ti, T, st = a
    edits, grav = CANDS[tag]
    M.apply(line_edits=edits, use_gravity=grav)
    TR = M.track_list()
    cap = M.g2_cap()
    r, q, qt, kw, over = measures(cap)[mname]
    c = {k: v for k, v in M.g2_cfg().items()}; c.update(over)
    (d, name), lap = TR[ti]
    o = R.run_new(TUNES, r, d, lap, T, st, q, qt, N, SEEDS[b], cfg=c, **kw)
    rc = np.maximum(o["read_clash"].sum(1), 1)
    v = np.stack([o["win"].mean(1), o["ov_turns"].mean(1) / T, o["ov_clash"].mean(1) / (3 * T),
                  o["lock_turns"].mean(1) / T, o["pen_loss"].mean(1) / (3 * T),
                  o["read_lock"].sum(1) / rc, o["read_ov"].sum(1) / rc, o["read_ov_play"].sum(1) / rc,
                  o["read_switch"].sum(1) / rc, o["lock_streak"].mean(1),
                  o["limp"].mean(1) / (3 * T), o["lock_dur_sum"] / np.maximum(o["n_locks"], 1)])
    extra = None
    if mname in ("avg_cap", "best_cap", "greedy_cap"):
        lt = np.zeros((len(TUNES), 30)); lt[:, :T] = o["lock_t"]
        hist = np.zeros((len(TUNES), 31)); hist[:, :T + 1] = o["lock_hist"]
        extra = dict(lock_t=lt, hist=hist, n_locks=o["n_locks"], dur=o["lock_dur_sum"], lock_res=o["lock_res"])
    return a, v, extra


def main():
    tags = sys.argv[1:] or ["baseline"]
    t0 = time.time()
    for tag in tags:
        if tag not in CANDS:
            raise SystemExit(f"unknown tag {tag}, have {list(CANDS)}")
        edits, grav = CANDS[tag]
        M.apply(line_edits=edits, use_gravity=grav)
        TR = M.track_list()
        fn = os.path.join(HERE, f"results_{tag}.npz")
        meta_path = os.path.join(HERE, "results_meta.json")
        try:
            meta = json.load(open(meta_path))
        except FileNotFoundError:
            meta = {}
        meta[tag] = dict(
            seeds=SEEDS, n=N, tracks=[list(k) for k, _ in TR], laps=[lap for _, lap in TR],
            lengths=list(LENGTHS), styles=list(R.STYLES), keys=list(KEYS),
            tunes=TUNES.tolist(), line_edits=edits, use_gravity=grav,
            cap=M.g2_cap(), g2=M.G2,
            gravity=dict(GRADE_UP=M.GRADE_UP, GRADE_DOWN=M.GRADE_DOWN),
        )
        json.dump(meta, open(meta_path, "w"), indent=1, default=str)
        out = dict(np.load(fn)) if os.path.exists(fn) else {}
        meas = list(measures(M.g2_cap()))
        if ONLY:
            meas = [m for m in meas if m in ONLY.split(",")]
        with Pool(8, initializer=_init_worker, initargs=(tag,)) as p:
            for mname in meas:
                if mname in out:
                    print(f"skip existing {tag} {mname}", flush=True)
                    continue
                arr = np.zeros((N_SEEDS, len(TR), 3, 3, len(KEYS), len(TUNES)))
                ex = {}
                jobs = [(tag, mname, b, ti, T, st)
                        for b in range(N_SEEDS) for ti in range(len(TR))
                        for T in LENGTHS for st in R.STYLES]
                njob = len(jobs); done = 0
                for (c_, m_, b, ti, T, st), v, extra in p.imap_unordered(job, jobs, chunksize=2):
                    k = LENGTHS.index(T); s = R.STYLES.index(st)
                    arr[b, ti, k, s] = v
                    if extra:
                        for kk, vv in extra.items():
                            if kk not in ex:
                                ex[kk] = np.zeros((N_SEEDS, len(TR), 3, 3) + np.shape(vv))
                            ex[kk][b, ti, k, s] = vv
                    done += 1
                    if done % 50 == 0 or done == njob:
                        print(f"{time.time()-t0:7.0f}s {tag} {mname} {done}/{njob}", flush=True)
                out[mname] = arr
                for kk, vv in ex.items():
                    out[f"{mname}|{kk}"] = vv
                np.savez_compressed(fn, **out)
                print(f"{time.time()-t0:7.0f}s {tag} {mname} mean over tunes {100*arr[:, :, :, :, 0].mean():.1f}", flush=True)
        print("done", tag, time.time() - t0)


if __name__ == "__main__":
    main()
