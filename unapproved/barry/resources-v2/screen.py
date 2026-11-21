"""Screening harness for v2 (N=1000 per cell, seed 7, track #1 of each district x 10/20/30 turns x 3 boss styles =
27 cells, full 21-tune grid + even). Screening numbers choose settings; final numbers come from run_v2.py."""
from __future__ import annotations
import itertools, json, sys
from multiprocessing import Pool
import numpy as np
import resources_v2 as R

E = R.E
N, SEED = 1000, 7
GRID = R.tune_grid(); TUNES = np.vstack([GRID, [[1 / 3, 1 / 3, 1 / 3]]]); NT = len(GRID); EV = NT
D = ("touge", "wangan", "street"); LAPS = {d: R.C.track_corners(d, 0) for d in D}
CELLS = [(d, T, st) for d in D for T in (10, 20, 30) for st in R.STYLES]


def avg_q(r):
    return E.raw_qte_score(r, profile="average")


def run_cells(cfg, kind, r, cells=CELLS, mode="read", **kw):
    qr, qt = (1.0, 1.0) if kind == "perfect" else (0.6, avg_q(r))
    out = {}
    for d, T, st in cells:
        o = R.run_new(TUNES, r, d, LAPS[d], T, st, qr, qt, N, SEED, cfg=cfg, mode=mode, **kw)
        out[(d, T, st)] = dict(win=o["win"].mean(1), blk=o["blocked_race"].mean(1), blkr=o["blocked_read_race"].mean(1),
                               rb=o["read_blocked"].sum(1) / np.maximum(o["read_turns"].sum(1), 1))
    return out


def metrics(cfg):
    cap = cfg.get("_cap", 1.05)
    c = {k: v for k, v in cfg.items() if not k.startswith("_")}
    m = {}
    A = run_cells(c, "average", cap)
    tw, ew, ge, gw, tb, trb, wb, eb, tbr = [], [], [], [], [], [], [], [], []
    by_d = {d: [] for d in D}
    mw, mb, mrb, mge, mgw = [], [], [], [], []
    for (d, T, st), x in A.items():
        b = int(np.argmax(x["win"][:NT]))
        oth = np.mean([A[(d2, T, st)]["win"][:NT] for d2 in D if d2 != d], axis=0); j = int(np.argmax(oth))
        tw.append(x["win"][b]); ew.append(x["win"][EV]); ge.append(x["win"][b] - x["win"][EV]); gw.append(x["win"][b] - x["win"][j])
        mi = R.matched_tune(d, LAPS[d], R.cfg_of(c), GRID)
        mj = R.matched_tune(D[(D.index(d) + 1) % 3], LAPS[D[(D.index(d) + 1) % 3]], R.cfg_of(c), GRID)
        mw.append(x["win"][mi]); mb.append(x["blk"][mi]); mrb.append(x["rb"][mi]); mge.append(x["win"][mi] - x["win"][EV])
        mgw.append(x["win"][mi] - np.mean([x["win"][R.matched_tune(d2, LAPS[d2], R.cfg_of(c), GRID)] for d2 in D if d2 != d]))
        tb.append(x["blk"][b]); tbr.append(x["blkr"][b]); trb.append(x["rb"][b]); wb.append(x["blk"][j]); eb.append(x["blk"][EV]); by_d[d].append(x["win"][b])
    m.update(avg_cap_tuned=np.mean(tw), avg_cap_even=np.mean(ew), gap_even=np.mean(ge), gap_even_min=np.min(ge), gap_wrong=np.mean(gw),
             gap_wrong_max=np.max(gw), gap_wrong_min=np.min(gw), blk_tuned=np.mean(tb), blkread_tuned=np.mean(tbr), rb_tuned=np.mean(trb), blk_wrong=np.mean(wb), blk_even=np.mean(eb),
             match_win=np.mean(mw), match_blk=np.mean(mb), match_rb=np.mean(mrb), match_gap_even=np.mean(mge), match_gap_wrong=np.mean(mgw),
             **{f"tuned_{d}": np.mean(v) for d, v in by_d.items()})
    def lowdry(x):
        ok = np.where(x["blk"][:NT] <= 0.15)[0]
        return int(ok[np.argmax(x["win"][ok])]) if len(ok) else int(np.argmin(x["blk"][:NT]))
    m["avg_cap_lowdry"] = np.mean([x["win"][lowdry(x)] for x in A.values()])
    m["lowdry_gap_even"] = np.mean([x["win"][lowdry(x)] - x["win"][EV] for x in A.values()])
    for kind, r in (("perfect", 0.8), ("perfect", 1.0)):
        P = run_cells(c, kind, r)
        m[f"{kind}{r}_tuned"] = np.mean([x["win"][:NT].max() for x in P.values()])
        m[f"{kind}{r}_lowdry"] = np.mean([x["win"][lowdry(x)] for x in P.values()])
        m[f"{kind}{r}_even"] = np.mean([x["win"][EV] for x in P.values()])
        if r == 1.0:
            bs = [int(np.argmax(x["win"][:NT])) for x in P.values()]
            m["perf1.0_blk_tuned"] = np.mean([x["blk"][b] for x, b in zip(P.values(), bs)])
            m["perf1.0_rb_tuned"] = np.mean([x["rb"][b] for x, b in zip(P.values(), bs)])
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
    grid = dict(TANK_MODE=["lap"], REFILL=[0.5, 0.75], TANK_FACTOR=[1.3, 1.6, 2.0], SHARE_EXPONENT=[1.0, 1.5],
                SUSP_TANK_TURNS=[5.0], SUSP_REC_FACTOR=[1.1])
    cfgs = [dict(zip(grid, v)) for v in itertools.product(*grid.values())]
    cfgs += [dict(TANK_MODE="race", TANK_FACTOR=tf, SHARE_EXPONENT=se, SUSP_TANK_TURNS=5.0, SUSP_REC_FACTOR=1.1)
             for tf in (1.1, 1.3, 1.6) for se in (1.0, 1.5)]
    sweep(cfgs, "screen_A.json")
