"""Screening harness for v3 (N=1000 per cell, seed 7, track #1 of each district x 10/20/30 turns x 3 boss styles =
27 cells, 21-tune grid + even). Screen numbers only choose settings; quoted results come from run_v3.py."""
from __future__ import annotations
import itertools, json, sys
from multiprocessing import Pool
import numpy as np
import resources_v3 as R

E = R.E
N, SEED = 1000, 7
GRID = R.tune_grid(); TUNES = np.vstack([GRID, [[1 / 3, 1 / 3, 1 / 3]]]); NT = len(GRID); EV = NT
D = ("touge", "wangan", "street"); LAPS = {d: R.C.track_corners(d, 0) for d in D}
CELLS = [(d, T, st) for d in D for T in (10, 20, 30) for st in R.STYLES]


def run_cells(cfg, kind, r, **kw):
    qr, qt = (1.0, 1.0) if kind == "perfect" else (0.6, E.raw_qte_score(r, profile="average"))
    out = {}
    for d, T, st in CELLS:
        o = R.run_new(TUNES, r, d, LAPS[d], T, st, qr, qt, N, SEED, cfg=cfg, **kw)
        out[(d, T, st)] = dict(win=o["win"].mean(1), ov=o["ov_turns"].mean(1) / T, lk=o["lock_turns"].mean(1) / T,
                               rl=o["read_lock"].sum(1) / np.maximum(o["read_clash"].sum(1), 1), stk=o["lock_streak"].mean(1),
                               dur=o["lock_dur_sum"] / np.maximum(o["n_locks"], 1))
    return out


def metrics(cfg):
    cap = cfg.get("_cap", 1.05)
    c = {k: v for k, v in cfg.items() if not k.startswith("_")}
    A = run_cells(c, "average", cap)
    m = {}
    tw, ew, ge, gw, tov, tlk, trl, tst, tdu, elk = [], [], [], [], [], [], [], [], [], []
    by_d = {d: [] for d in D}; gw_d = {d: [] for d in D}
    for (d, T, st), x in A.items():
        b = int(np.argmax(x["win"][:NT]))
        oth = np.mean([A[(d2, T, st)]["win"][:NT] for d2 in D if d2 != d], axis=0); j = int(np.argmax(oth))
        tw.append(x["win"][b]); ew.append(x["win"][EV]); ge.append(x["win"][b] - x["win"][EV]); gw.append(x["win"][b] - x["win"][j])
        tov.append(x["ov"][b]); tlk.append(x["lk"][b]); trl.append(x["rl"][b]); tst.append(x["stk"][b]); tdu.append(x["dur"][b]); elk.append(x["lk"][EV])
        by_d[d].append(x["win"][b]); gw_d[d].append(x["win"][b] - x["win"][j])
    m.update(avg_tuned=np.mean(tw), avg_even=np.mean(ew), gap_even=np.mean(ge), gap_wrong=np.mean(gw), gap_wrong_max=np.max(gw),
             ov_corners=np.mean(tov), lock_corners=np.mean(tlk), read_locked=np.mean(trl), lock_streak=np.mean(tst) / 100,
             lock_dur=np.mean(tdu) / 100, even_lock_corners=np.mean(elk),
             **{f"tuned_{d}": np.mean(v) for d, v in by_d.items()}, **{f"gapw_{d}": np.mean(v) for d, v in gw_d.items()})
    if cfg.get("_pacing"):
        G_ = run_cells(c, "average", cap, ration=False)
        m["pacing_gap"] = np.mean([A[k]["win"][int(np.argmax(A[k]["win"][:NT]))] - G_[k]["win"][int(np.argmax(G_[k]["win"][:NT]))] for k in A])
    for r in (0.8, 1.0):
        P = run_cells(c, "perfect", r)
        m[f"perf{r}_tuned"] = np.mean([x["win"][:NT].max() for x in P.values()])
        m[f"perf{r}_even"] = np.mean([x["win"][EV] for x in P.values()])
    return {k: round(100 * float(v), 1) for k, v in m.items()}


def _job(cfg):
    return cfg, metrics(cfg)


def sweep(cfgs, out_path):
    res = []
    with Pool(8) as p:
        for cfg, m in p.imap_unordered(_job, cfgs):
            res.append(dict(cfg=cfg, **m)); print(json.dumps(cfg), m, flush=True)
            json.dump(res, open(out_path, "w"), indent=1)
    return res


if __name__ == "__main__":
    grid = dict(CAP_TURNS=[2.0, 3.0, 4.5], REC_FACTOR=[0.9, 1.0, 1.15], RX=[0.0, 1.0, 2.0], KAPPA_SCALE=[1.0, 1.25, 1.5])
    cfgs = []
    for ct, rf, rx, ks in itertools.product(*grid.values()):
        cfgs.append(dict(CAP_TURNS=ct, REC_FACTOR=rf, CAP_R_EXP=rx, REC_R_EXP=rx, KAPPA_SCALE=ks, RELEASE=0.7, _cap=1.05))
    sweep(cfgs, "screen_A.json")
