"""resources-v2 full runs. 9 batches x 1000 races (seeds 20261112..20261120), all 15 stand-in laps x 10/20/30 turns x 3 boss
styles, 21-tune grid + exact even spread. Misread rule = live (tie with prob q_read, else lose), chosen after screen_H.
Writes results_v2.npz (per batch, per cell, per tune means) + results_v2_meta.json."""
from __future__ import annotations
import json, sys, time
from multiprocessing import Pool
import numpy as np
import resources_v2 as R

E = R.E
N = 1000
SEEDS = [20261112 + b for b in range(9)]
GRID = R.tune_grid(); TUNES = np.vstack([GRID, [[1 / 3, 1 / 3, 1 / 3]]])
TR = sorted(R.tracks().items())                       # 15 x ((district, name), lap)
LENGTHS = (10, 20, 30)
BASE = dict(SUSP_TANK_TURNS=5.0, SUSP_REC_FACTOR=1.1, TANK_REF_Q=0.6, MISREAD="live")
CANDS = {
    "A_scarce": dict(BASE, TANK_MODE="lap", REFILL=0.75, TANK_FACTOR=1.3, SHARE_EXPONENT=1.5, DEMAND_SLANT=1.0, KAPPA_SCALE=1.0, TANK_R_EXP=3.0, _cap=1.05),
    "A_mid": dict(BASE, TANK_MODE="lap", REFILL=0.75, TANK_FACTOR=1.6, SHARE_EXPONENT=1.5, DEMAND_SLANT=1.0, KAPPA_SCALE=1.25, TANK_R_EXP=3.0, _cap=1.05),
    "A_mid_norefill": dict(BASE, TANK_MODE="race", TANK_FACTOR=1.6, SHARE_EXPONENT=1.5, DEMAND_SLANT=1.0, KAPPA_SCALE=1.25, TANK_R_EXP=3.0, _cap=1.05),
    "A_mid_refill50": dict(BASE, TANK_MODE="lap", REFILL=0.5, TANK_FACTOR=1.6, SHARE_EXPONENT=1.5, DEMAND_SLANT=1.0, KAPPA_SCALE=1.25, TANK_R_EXP=3.0, _cap=1.05),
    "B_generous": dict(BASE, TANK_MODE="race", TANK_FACTOR=1.6, SHARE_EXPONENT=1.0, DEMAND_SLANT=0.5, KAPPA_SCALE=1.5, TANK_R_EXP=3.0, _cap=1.05),
}
# measures: name -> (r, q_read, timing, kwargs, cfg overrides)
def measures(cand, cap):
    avg = E.raw_qte_score(cap, profile="average")
    m = {"avg_cap": (cap, 0.6, avg, {}, {}),
         "perf_0.8": (0.8, 1.0, 1.0, {}, {}),
         "perf_1.0": (1.0, 1.0, 1.0, {}, {})}
    if not cand.endswith(("norefill", "refill50")):
        m.update({"read1_cap": (cap, 1.0, avg, {}, {}),
                  "random_cap": (cap, 0.0, avg, {"mode": "random"}, {}),
                  "noration_cap": (cap, 0.6, avg, {"ration": False}, {}),
                  "unscouted_cap": (cap, 0.6, avg, {"scouted": False}, {}),
                  "b1_scouted_cap": (cap, 0.6, avg, {}, {"STYLE_BETA": 1.0}),
                  "b1_unscouted_cap": (cap, 0.6, avg, {"scouted": False}, {"STYLE_BETA": 1.0})})
    return m

KEYS = ("win", "blk", "blkr", "rb", "limp")


def job(a):
    cand, mname, b, ti, T, st = a
    cfg = CANDS[cand]; cap = cfg["_cap"]
    r, q, qt, kw, over = measures(cand, cap)[mname]
    c = {k: v for k, v in cfg.items() if not k.startswith("_")}; c.update(over)
    (d, name), lap = TR[ti]
    o = R.run_new(TUNES, r, d, lap, T, st, q, qt, N, SEEDS[b], cfg=c, **kw)
    rb = o["read_blocked"].sum(1) / np.maximum(o["read_turns"].sum(1), 1)
    return a, np.stack([o["win"].mean(1), o["blocked_race"].mean(1), o["blocked_read_race"].mean(1), rb, o["limp"].mean(1) / T])


def live_job(a):
    kind, b, ti, T = a
    (d, name), lap = TR[ti]
    qt = E.raw_qte_score(1.05, profile="average")
    if kind == "live_read1":
        w, _ = R.run_old(TUNES, 1.05, d, lap, T, 1.0, qt, N, SEEDS[b])
    elif kind == "live_avg":
        w, _ = R.run_old(TUNES, 1.05, d, lap, T, 0.6, qt, N, SEEDS[b])
    else:
        w, _ = R.run_old(TUNES, 1.05, d, lap, T, 0.0, qt, N, SEEDS[b], random_read=True)
    return a, w


if __name__ == "__main__":
    t0 = time.time()
    out = {}
    with Pool(8) as p:
        for cand in CANDS:
            ms = list(measures(cand, CANDS[cand]["_cap"]))
            for mname in ms:
                arr = np.zeros((9, len(TR), 3, 3, len(KEYS), len(TUNES)))
                jobs = [(cand, mname, b, ti, T, st) for b in range(9) for ti in range(len(TR)) for T in LENGTHS for st in R.STYLES]
                for (c_, m_, b, ti, T, st), v in p.imap_unordered(job, jobs, chunksize=4):
                    arr[b, ti, LENGTHS.index(T), R.STYLES.index(st)] = v
                out[f"{cand}|{mname}"] = arr
                np.savez_compressed("results_v2.npz", **out)
                print(f"{time.time()-t0:7.0f}s {cand} {mname} avg win {100*arr[:, :, :, :, 0].mean():.1f}", flush=True)
        for kind in ("live_read1", "live_avg", "live_random"):
            arr = np.zeros((9, len(TR), 3, len(TUNES)))
            jobs = [(kind, b, ti, T) for b in range(9) for ti in range(len(TR)) for T in LENGTHS]
            for (k_, b, ti, T), w in p.imap_unordered(live_job, jobs, chunksize=4):
                arr[b, ti, LENGTHS.index(T)] = w
            out[kind] = arr
            np.savez_compressed("results_v2.npz", **out)
            print(f"{time.time()-t0:7.0f}s {kind} {100*arr.mean():.1f}", flush=True)
    meta = dict(seeds=SEEDS, n=N, tracks=[list(k) for k, _ in TR], lengths=LENGTHS, styles=list(R.STYLES), keys=KEYS,
                tunes=TUNES.tolist(), candidates=CANDS, measures={c: {k: [v[0], v[1], v[2], v[3], v[4]] for k, v in measures(c, CANDS[c]["_cap"]).items()} for c in CANDS})
    json.dump(meta, open("results_v2_meta.json", "w"), indent=1, default=str)
    print("done", time.time() - t0)
