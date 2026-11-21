"""Full-size rerun of the best hard-block setting from hb_fit.json ("hb_b": hard block, KAPPA_SCALE 1.25,
TANK_FACTOR 0.4; everything else = base). Same seeds/batches as run_resources_v1.py. Writes results_hb.json."""
import json, time, itertools
from multiprocessing import Pool
import numpy as np
import run_resources_v1 as M
import resources_v1 as R

HB = dict(KAPPA_SCALE=1.25, TANK_FACTOR=0.4)


def cell(args):
    tk, T, st, kind, r = args
    qr, qt = M.play(kind, r)
    out = np.empty((M.NB, len(M.TUNES)))
    for b in range(M.NB):
        out[b] = R.run_new(M.TUNES, r, tk[0], M.TR[tk], T, st, qr, qt, M.NPB, M.SEED0 + b, hard_block=True, cfg=HB)[0]
    return args, out


if __name__ == "__main__":
    jobs = [(tk, T, st, "average", 1.05) for tk, T, st in itertools.product(M.TRACK_KEYS, M.LENGTHS, R.STYLES)]
    jobs += [(tk, T, st, k, r) for tk, T, st, (k, r) in itertools.product(M.TRACK_KEYS, M.LENGTHS, R.STYLES,
             [("perfect", 0.8), ("perfect", 1.0), ("average", 1.10), ("average", 1.0)])]
    t0 = time.time(); res = {"meta": dict(variant="hb_b", hard_block=True, cfg=R.cfg_of(HB), seed0=M.SEED0, batches=M.NB,
                                          runs_per_batch=M.NPB, tunes=M.TUNES.tolist()), "new": {}}
    with Pool(8) as p:
        for i, (a, out) in enumerate(p.imap_unordered(cell, jobs, chunksize=2)):
            res["new"][M.key((a[0], a[1], a[2], a[3], a[4], "hb_b", True))] = out.tolist()
            if i % 100 == 0:
                print(i, len(jobs), round(time.time() - t0), flush=True)
    res["meta"]["elapsed_s"] = round(time.time() - t0)
    json.dump(res, open("results_hb.json", "w")); print("done", time.time() - t0)
