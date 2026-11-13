"""v4 screen 2: heat-stakes knobs x pacing policies. N 400, seed 7, track #1 per district, 20 and 30 turns, all 3
boss styles (18 cells), 21-tune grid; each policy on its own best tune per cell. Screen numbers choose settings only."""
import sys, itertools, json, numpy as np
from multiprocessing import Pool
import resources_v4 as R
TUNES = np.vstack([R.tune_grid(), [[1 / 3] * 3]])
N, SEED = 400, 7
CELLS = [(d, T, st) for d in ("touge", "wangan", "street") for T in (20, 30) for st in R.STYLES]
POL = [("greedy", {}), ("ration", {}), ("ration", dict(RATION_LAMBDA=2.0, RATION_H=4)),
       ("reserve", dict(RES_T=0.7, RES_K=1.0)), ("reserve", dict(RES_T=0.9, RES_K=2.0)),
       ("reserve", dict(RES_T=0.8, RES_K=1.5, RES_LOOK=0.5, PLAN_H=3)), ("plan", dict(PLAN_LAMBDA=0.5, PLAN_H=3))]
PN = ["greedy", "ration", "ration2", "resA", "resB", "resLook", "plan"]
BASE = dict(CAP_TURNS=3.0, REC_R_EXP=1.0, CAP_R_EXP=1.0, KAPPA_SCALE=1.5, PEN_FLOOR=0.4)
def job(a):
    ci, pi, q, cell = a
    cfg = dict(BASE, **CFGS[ci], **POL[pi][1])
    d, T, st = cell
    o = R.run_new(TUNES, 1.05, d, R.C.track_corners(d, 0), T, st, q, 0.6, N, SEED, cfg=cfg, pacing=POL[pi][0])
    w = o["win"].mean(1)[:21]; b = int(w.argmax())
    return a, w[b], o["lock_turns"].mean(1)[b] / T, (o["read_lock"].sum(1) / np.maximum(o["read_clash"].sum(1), 1))[b]
grid = dict(REC_FACTOR=[0.8, 0.65], RELEASE=[0.5, 0.3], AGG_STEP=[0.5, 0.75], PEN_FLOOR=[0.4, 0.1])
CFGS = []
for rf, rel, ag, fl in itertools.product(*grid.values()):
    CFGS.append(dict(REC_FACTOR=rf, RELEASE=rel, AGG_STEP=ag, PEN_FLOOR=fl, PEN_SHAPE="quadratic", PEN_SLOPE=4.0))
if __name__ == "__main__":
    jobs = [(ci, pi, q, cell) for ci in range(len(CFGS)) for pi in range(len(POL)) for q in (0.6, 1.0) for cell in CELLS]
    res = {}
    with Pool(8) as p:
        for a, w, lk, rl in p.imap_unordered(job, jobs, chunksize=2):
            res[a] = (w, lk, rl)
    out = []
    for ci, cfg in enumerate(CFGS):
        row = dict(cfg=cfg)
        for pi, (pn, pk) in enumerate(POL):
            for q in (0.6, 1.0):
                v = np.array([res[(ci, pi, q, cell)] for cell in CELLS])
                row[f"{PN[pi]}_q{q}"] = [round(100 * float(x), 1) for x in v.mean(0)]
        out.append(row); print(json.dumps(row))
    json.dump(out, open("screen_stakes2.json", "w"), indent=1)
