"""v4 screen 3: heat-stakes knobs (REC, RELEASE, AGG_STEP, overrun curve) x reserve-rule settings, at cap 1.05, kappa x1.5.
N 400, seed 7, track #1 per district, 20 and 30 turns, 3 boss styles (18 cells); each player on its own best tune per cell,
except the random-guess player, which uses the perfect reader's best tune (same as v3 read gap). Screen numbers only
choose settings."""
import sys, itertools, json, numpy as np
from multiprocessing import Pool
import resources_v4 as R
TUNES = np.vstack([R.tune_grid(), [[1 / 3] * 3]])
N, SEED = 400, 7
CELLS = [(d, T, st) for d in ("touge", "wangan", "street") for T in (20, 30) for st in R.STYLES]
RES = [dict(RES_T=0.8, RES_K=1.5, RES_LOOK=0.5, PLAN_H=3), dict(RES_T=0.7, RES_K=2.0, RES_LOOK=0.5, PLAN_H=3),
       dict(RES_T=0.9, RES_K=2.0, RES_LOOK=1.0, PLAN_H=5), dict(RES_T=0.8, RES_K=3.0, RES_LOOK=1.0, PLAN_H=3)]
# (name, pacing, res index, q, mode)
PL = [("greedy_q0.6", "greedy", None, 0.6, "read"), ("greedy_q1", "greedy", None, 1.0, "read")]
for i in range(len(RES)):
    PL += [(f"res{i}_q0.6", "reserve", i, 0.6, "read"), (f"res{i}_q1", "reserve", i, 1.0, "read"),
           (f"res{i}_mix0.6_q0.6", "mix", i, 0.6, "read"), (f"res{i}_rand", "reserve", i, 1.0, "randguess")]
BASE = dict(CAP_TURNS=3.0, REC_R_EXP=1.0, CAP_R_EXP=1.0, KAPPA_SCALE=1.5, PEN_FLOOR=0.4)
grid = dict(REC_FACTOR=[0.8, 0.9], RELEASE=[0.3, 0.2], AGG_STEP=[0.75, 1.0],
            PEN=[("quadratic", 4.0), ("linear", 2.0), ("quadratic", 8.0), ("linear", 4.0)])
CFGS = [dict(REC_FACTOR=a, RELEASE=b, AGG_STEP=g, PEN_SHAPE=ps, PEN_SLOPE=sl) for a, b, g, (ps, sl) in itertools.product(*grid.values())]


def job(a):
    ci, pi, cell = a
    name, pac, ri, q, mode = PL[pi]
    cfg = dict(BASE, **CFGS[ci], **(RES[ri] if ri is not None else {}))
    if pac == "mix":
        cfg["PACE_Q"] = 0.6
    d, T, st = cell
    o = R.run_new(TUNES, 1.05, d, R.C.track_corners(d, 0), T, st, q, 0.6, N, SEED, cfg=cfg, pacing=pac, mode=mode)
    return a, o["win"].mean(1), o["lock_turns"].mean(1) / T, o["read_lock"].sum(1) / np.maximum(o["read_clash"].sum(1), 1)


if __name__ == "__main__":
    jobs = [(ci, pi, cell) for ci in range(len(CFGS)) for pi in range(len(PL)) for cell in CELLS]
    res = {}
    with Pool(8) as p:
        for a, w, lk, rl in p.imap_unordered(job, jobs, chunksize=4):
            res[a] = (w, lk, rl)
    out = []
    for ci, cfg in enumerate(CFGS):
        row = dict(cfg=cfg)
        for pi, pl in enumerate(PL):
            vals = []
            for cell in CELLS:
                w, lk, rl = res[(ci, pi, cell)]
                if pl[4] == "randguess":
                    b = int(res[(ci, PL.index(next(x for x in PL if x[0] == pl[0].replace("_rand", "_q1"))), cell)][0][:21].argmax())
                else:
                    b = int(w[:21].argmax())
                vals.append((w[b], lk[b], rl[b]))
            row[pl[0]] = [round(100 * float(x), 1) for x in np.mean(vals, 0)]
        out.append(row); print(json.dumps(row), flush=True)
    json.dump(out, open("screen3.json", "w"), indent=1)
