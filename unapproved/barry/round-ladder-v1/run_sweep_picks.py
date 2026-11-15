"""G2 r-sweep for Austin's offset picks + no-grind arrivals. 9×1000, draft tracks, district-fixed tunes.

Does not edit sim/ or live constants.
"""
from __future__ import annotations
import json, os, sys, time
from multiprocessing import Pool
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TL = os.path.abspath(os.path.join(HERE, "..", "touge-lines-v1"))
sys.path.insert(0, TL)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "resources-v4", "retune")))

import model as M
import resources_v4b as R

N = int(os.environ.get("V4_N", "1000"))
N_SEEDS = int(os.environ.get("V4_SEEDS", "9"))
SEEDS = [20261112 + b for b in range(N_SEEDS)]
LENGTHS = (10, 20, 30)
KEYS = ("win", "lock", "rlock", "limp")
GRID_PATH = os.environ.get("PICKS_R_PATH", os.path.join(HERE, "picks_r_grid.json"))
R_GRID = tuple(json.load(open(GRID_PATH)))
OUT_NAME = os.environ.get("PICKS_OUT", "results_picks.npz")

TUNES = {
    "street": np.array([[0.50, 0.25, 0.25]]),
    "wangan": np.array([[0.25, 0.30, 0.45]]),
    "touge":  np.array([[0.40, 0.30, 0.30]]),
}
MEASURES = ("avg", "c8080")


def _cfg(pace_q):
    c = {k: v for k, v in M.g2_cfg().items()}
    c["PACE_Q"] = pace_q
    return c


def _q(mname, r):
    if mname == "avg":
        return 0.6, R.E.raw_qte_score(r, profile="average"), 0.6
    return 0.8, 0.8, 0.8


def _init():
    M.apply(line_edits=None, use_gravity=True)


def job(a):
    ti, k, s, b = a
    _init()
    TR = M.track_list()
    (d, name), lap = TR[ti]
    T = LENGTHS[k]
    st = R.STYLES[s]
    seed = SEEDS[b]
    tune = TUNES[d]
    out = np.zeros((len(MEASURES), len(R_GRID), len(KEYS)))
    for mi, mname in enumerate(MEASURES):
        for ri, r in enumerate(R_GRID):
            q, qt, pq = _q(mname, r)
            o = R.run_new(tune, r, d, lap, T, st, q, qt, N, seed, cfg=_cfg(pq), pacing="mix")
            rc = max(float(o["read_clash"].sum()), 1.0)
            out[mi, ri] = (
                float(o["win"].mean()),
                float(o["lock_turns"].mean()) / T,
                float(o["read_lock"].sum()) / rc,
                float(o["limp"].mean()) / (3 * T),
            )
    return a, out


def main():
    t0 = time.time()
    _init()
    TR = M.track_list()
    print(f"r count {len(R_GRID)} n={N} seeds={N_SEEDS}", flush=True)
    jobs = [(ti, k, s, b)
            for ti in range(len(TR))
            for k in range(len(LENGTHS))
            for s in range(len(R.STYLES))
            for b in range(N_SEEDS)]
    arr = np.zeros((len(MEASURES), len(R_GRID), N_SEEDS, len(TR), len(LENGTHS), len(R.STYLES), len(KEYS)))
    njob = len(jobs); done = 0
    with Pool(8, initializer=_init) as p:
        for (ti, k, s, b), v in p.imap_unordered(job, jobs, chunksize=1):
            arr[:, :, b, ti, k, s, :] = v
            done += 1
            if done % 40 == 0 or done == njob:
                print(f"{time.time()-t0:7.0f}s {done}/{njob}", flush=True)
    fn = os.path.join(HERE, OUT_NAME)
    meta = dict(
        seeds=SEEDS, n=N, r_grid=list(R_GRID), measures=list(MEASURES), keys=list(KEYS),
        lengths=list(LENGTHS), styles=list(R.STYLES),
        tracks=[list(k) for k, _ in TR],
        tunes={d: t.reshape(-1).tolist() for d, t in TUNES.items()},
        use_gravity=True, line_edits=None, cap_constant=M.g2_cap(),
        note="Picks sweep: exact target/arrival r for offset ladder + no-grind walks.",
    )
    np.savez_compressed(fn, arr=arr, r_grid=np.array(R_GRID))
    json.dump(meta, open(os.path.join(HERE, OUT_NAME.replace(".npz", "_meta.json")), "w"), indent=1, default=str)
    print("wrote", fn, "in", round(time.time()-t0, 1), "s")


if __name__ == "__main__":
    main()
