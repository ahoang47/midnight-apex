"""G2 comparison: best 0-aero (district-fixed split) vs best 1-aero
(district-fixed + 10% of one slot retuned toward that track's per-race best).

Live rule: AERO_MAX_EQUIPPED=1, aero occupies any one of 6 slots and blocks
that slot's regular mod. The aero part still contributes its regular stats;
only AERO_POOL_FRACTION (live 0.10) of that one part is freely assignable.
No stacking is possible; this script does not touch stacking rules.

Shift of total combat power = (0.27 * P / 6) * 0.10 / (1.07 * P) = 0.004206
of the 1.07 ceiling, i.e. 0.42 percentage points of the split.
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
# Cap r = 1.07 (parity reference) plus Variant A boss targets
R_GRID = (1.025, 1.040, 1.050, 1.070)
TUNES_FIXED = {
    "street": np.array([0.50, 0.25, 0.25], float),
    "wangan": np.array([0.25, 0.30, 0.45], float),
    "touge":  np.array([0.40, 0.30, 0.30], float),
}
# Per-race best splits from touge-lines-v1 (same source as district_fixed).
# Filled at runtime from analysis if present; fallback below.
AERO_SHIFT = 0.27 / 6.0 * 0.10  # fraction of P_stats; combat frac = this/1.07

# 80/80 and 60/60 only — aero is a build question, not a skill-profile one
MEASURES = ("avg_cap", "c8080")


def _best_splits():
    path = os.path.join(TL, "analysis.json")
    # resources-v4 / touge-lines stores best tune per track per length
    # We read model.tune_grid and analysis; if missing, use district fixed
    # (delta will be 0). Optional file aero_best_splits.json can override.
    p2 = os.path.join(HERE, "aero_best_splits.json")
    if os.path.exists(p2):
        raw = json.load(open(p2))
        return {k: {int(T): np.array(v, float) for T, v in d.items()} for k, d in raw.items()}
    return {}


def aero_tune(fixed, best):
    """Move AERO_SHIFT of the split from fixed toward best. Renormalize to 1."""
    fixed = np.array(fixed, float)
    best = np.array(best, float)
    delta = best - fixed
    n = np.linalg.norm(delta, 1)  # total mass moved in a full retune
    if n < 1e-9:
        return fixed.copy()
    # Move L1 mass equal to AERO_SHIFT (as a fraction of the 1.00 split,
    # which equals AERO_SHIFT of P when the split is of P; our tunes are
    # fractions of the car, so shift the fraction vector by AERO_SHIFT).
    step = (AERO_SHIFT) * delta / (n / 2.0)  # n/2 is mass taken from donors
    # Simpler: take AERO_SHIFT from the most-over-allocated stats, add to under.
    out = fixed.copy()
    # Project: move min(AERO_SHIFT, half the L1 gap) along the direction.
    mass = min(AERO_SHIFT, n / 2.0)
    out = fixed + mass * (delta / (n / 2.0))
    out = np.clip(out, 0, 1)
    out = out / out.sum()
    return out


def _cfg(pq):
    c = {k: v for k, v in M.g2_cfg().items()}
    c["PACE_Q"] = pq
    return c


def _q(mname, r):
    if mname == "avg_cap":
        return 0.6, R.E.raw_qte_score(r, profile="average"), 0.6
    return 0.8, 0.8, 0.8


def _init():
    M.apply(line_edits=None, use_gravity=True)


BEST = None


def job(a):
    ti, k, s, b = a
    _init()
    TR = M.track_list()
    (d, name), lap = TR[ti]
    T = LENGTHS[k]
    st = R.STYLES[s]
    seed = SEEDS[b]
    fixed = TUNES_FIXED[d]
    best = BEST.get(name, {}).get(T, fixed)
    aero = aero_tune(fixed, best)
    builds = (fixed, aero)
    out = np.zeros((2, len(MEASURES), len(R_GRID), len(KEYS)))
    for bi, tune in enumerate(builds):
        t = tune.reshape(1, 3)
        for mi, mname in enumerate(MEASURES):
            for ri, r in enumerate(R_GRID):
                q, qt, pq = _q(mname, r)
                o = R.run_new(t, r, d, lap, T, st, q, qt, N, seed, cfg=_cfg(pq), pacing="mix")
                rc = max(float(o["read_clash"].sum()), 1.0)
                out[bi, mi, ri] = (
                    float(o["win"].mean()),
                    float(o["lock_turns"].mean()) / T,
                    float(o["read_lock"].sum()) / rc,
                    float(o["limp"].mean()) / (3 * T),
                )
    return a, out, aero.tolist()


def main():
    global BEST
    t0 = time.time()
    _init()
    BEST = _best_splits()
    TR = M.track_list()
    print(f"aero sweep r={R_GRID} shift={AERO_SHIFT:.4f} n={N}", flush=True)
    jobs = [(ti, k, s, b)
            for ti in range(len(TR))
            for k in range(len(LENGTHS))
            for s in range(len(R.STYLES))
            for b in range(N_SEEDS)]
    arr = np.zeros((2, len(MEASURES), len(R_GRID), N_SEEDS, len(TR), len(LENGTHS), len(R.STYLES), len(KEYS)))
    aeros = {}
    njob = len(jobs); done = 0
    with Pool(8, initializer=_init) as p:
        for (ti, k, s, b), v, at in p.imap_unordered(job, jobs, chunksize=1):
            arr[:, :, :, b, ti, k, s, :] = v
            (d, name), _ = TR[ti]
            aeros[f"{name}:{LENGTHS[k]}"] = at
            done += 1
            if done % 40 == 0 or done == njob:
                print(f"{time.time()-t0:7.0f}s {done}/{njob}", flush=True)
    fn = os.path.join(HERE, "results_aero.npz")
    np.savez_compressed(fn, arr=arr, r_grid=np.array(R_GRID))
    meta = dict(
        seeds=SEEDS, n=N, r_grid=list(R_GRID), measures=list(MEASURES),
        keys=list(KEYS), lengths=list(LENGTHS), styles=list(R.STYLES),
        tracks=[list(k) for k, _ in TR],
        aero_shift=AERO_SHIFT, aero_tunes=aeros,
        note="build0=0-aero district-fixed; build1=1-aero 10% of one slot toward per-race best",
    )
    json.dump(meta, open(os.path.join(HERE, "results_aero_meta.json"), "w"), indent=1, default=str)
    print("wrote", fn, "in", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
