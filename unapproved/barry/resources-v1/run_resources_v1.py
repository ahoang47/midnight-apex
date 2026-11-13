"""resources-v1 runner. Barry, 2026-11-12. DRAFT, NOT APPROVED.

Runs every measurement in RESULTS.md and writes results.json. 9 batches x 1000 runs = 9000 runs per cell,
batch seeds SEED0 + b (b = 0..8). All builds in a cell share the same random numbers (common random numbers).
Usage:  python3 run_resources_v1.py            (about 10 minutes on 8 cores)
"""
from __future__ import annotations
import json, sys, time, itertools
from multiprocessing import Pool
import numpy as np
import resources_v1 as R

E = R.E
SEED0 = 20261112
NB, NPB = 9, 1000
LENGTHS = (10, 20, 30)
GRID = R.tune_grid()
EVEN = np.array([[1 / 3, 1 / 3, 1 / 3]])
TUNES = np.vstack([GRID, EVEN])          # last row = even spread
TR = R.tracks()
TRACK_KEYS = list(TR)
FIRST = [k for k in TRACK_KEYS if k[1][1] == "1"]   # track #1 of each district
KAPPA3 = dict(KAPPA_SCALE=3.0)
VARIANTS = {"base": {}, "hard_block": {}, "downgrade": dict(EMPTY_RULE="downgrade"), "kappa_x3": KAPPA3}


def avg_q(r):
    return E.raw_qte_score(r, profile="average")


def play(kind, r):
    return (1.0, 1.0) if kind == "perfect" else (0.6, avg_q(r))


def cell_new(args):
    """Per-batch win rates (NB, len(TUNES)) for one new-model cell."""
    (d, name), T, style, kind, r, variant, scouted = args
    qr, qt = play(kind, r)
    cfg = VARIANTS[variant]
    out = np.empty((NB, len(TUNES)))
    for b in range(NB):
        out[b] = R.run_new(TUNES, r, d, TR[(d, name)], T, style, qr, qt, NPB, SEED0 + b,
                           hard_block=(variant == "hard_block"), scouted=scouted, cfg=cfg)[0]
    return args, out


def cell_old(args):
    (d, name), T, kind, r = args
    qr, qt = play(kind, r)
    out = np.empty((NB, len(TUNES)))
    for b in range(NB):
        out[b] = R.run_old(TUNES, r, d, TR[(d, name)], T, qr, qt, NPB, SEED0 + b)[0]
    return args, out


def key(a):
    return "|".join(str(x if not isinstance(x, tuple) else "/".join(x)) for x in a)


def main():
    jobs_new, jobs_old = [], []
    # (a)(b) retune at the cap, average play: all 15 tracks x 3 lengths x 3 styles, base model
    for tk, T, st in itertools.product(TRACK_KEYS, LENGTHS, R.STYLES):
        jobs_new.append((tk, T, st, "average", 1.05, "base", True))
    # (c) combat targets: all tracks x lengths x styles at r 0.8/1.0/1.05/1.10, perfect + average (base);
    for tk, T, st, (kind, r) in itertools.product(TRACK_KEYS, LENGTHS, R.STYLES,
                                                  [("perfect", 0.8), ("perfect", 1.0), ("average", 1.10),
                                                   ("perfect", 1.05), ("perfect", 1.10), ("average", 0.8), ("average", 1.0)]):
        jobs_new.append((tk, T, st, kind, r, "base", True))
    # variants (track #1 per district only): hard block, downgrade, kappa x3
    for v in ("hard_block", "downgrade", "kappa_x3"):
        for tk, T, st, (kind, r) in itertools.product(FIRST, LENGTHS, R.STYLES,
                                                      [("perfect", 0.8), ("perfect", 1.0), ("average", 1.05), ("average", 1.10)]):
            jobs_new.append((tk, T, st, kind, r, v, True))
    # scouting value: unscouted player vs hot / conserver (track #1 per district)
    for tk, T, st in itertools.product(FIRST, LENGTHS, ("hot_early", "conserver")):
        jobs_new.append((tk, T, st, "average", 1.05, "base", False))
    # (c)(d) live model, same tracks/lengths (no styles in the live model)
    for tk, T, (kind, r) in itertools.product(TRACK_KEYS, LENGTHS, [("perfect", 0.8), ("perfect", 1.0), ("average", 1.05),
                                                                    ("average", 1.10), ("perfect", 1.05), ("perfect", 1.10),
                                                                    ("average", 0.8), ("average", 1.0)]):
        jobs_old.append((tk, T, kind, r))
    t0 = time.time()
    res = {"meta": dict(seed0=SEED0, batches=NB, runs_per_batch=NPB, runs_per_cell=NB * NPB,
                        tunes=TUNES.tolist(), tune_order="POW,HAN,EN shares; last = even",
                        cfg=R.cfg_of({}), variants=VARIANTS), "new": {}, "old": {}}
    with Pool(8) as p:
        for i, (a, out) in enumerate(p.imap_unordered(cell_new, jobs_new, chunksize=2)):
            res["new"][key(a)] = out.tolist()
            if i % 50 == 0:
                print(f"new {i}/{len(jobs_new)} {time.time()-t0:.0f}s", flush=True)
        for i, (a, out) in enumerate(p.imap_unordered(cell_old, jobs_old, chunksize=2)):
            res["old"][key(a)] = out.tolist()
            if i % 50 == 0:
                print(f"old {i}/{len(jobs_old)} {time.time()-t0:.0f}s", flush=True)
    res["meta"]["elapsed_s"] = round(time.time() - t0)
    json.dump(res, open("results.json", "w"))
    print("done", time.time() - t0)


if __name__ == "__main__":
    main()
