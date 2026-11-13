"""v4 fix screen (after kfit_M1-M3 showed average 60/60 at the cap far below target at 20/30 turns).
Tries lower stakes (player recovery 0.95-1.0 instead of 0.9), a gentler overrun slope, and capacity/recovery scaling
with r^2, at kappa multipliers 0.75-1.5 for 20 and 30 turns and caps 1.05 / 1.10. N 400, seed 7, track #1 per district
x 3 boss styles (9 cells per length). Each player on its own best tune per cell; the random-guess player uses the perfect
reader's tune. Writes fix_screen.json incrementally. Screen numbers choose settings only."""
import json, numpy as np
from multiprocessing import Pool
import resources_v4 as R
E = R.E
TUNES = np.vstack([R.tune_grid(), [[1 / 3] * 3]])
N, SEED = 400, 7
CELLS = [(d, st) for d in ("touge", "wangan", "street") for st in R.STYLES]
B = dict(BOSS_REC_FACTOR=1.0, BOSS_RELEASE=0.8, BOSS_CAP_TURNS=3.0, CAP_TURNS=3.0, KAPPA_SCALE=1.5, PEN_FLOOR=0.4,
         RES_T=0.7, RES_K=2.0, RES_LOOK=0.5, PLAN_H=3, RELEASE=0.3, AGG_STEP=1.0)
CFGS = {"F1": dict(REC_FACTOR=1.0, PEN_SHAPE="linear", PEN_SLOPE=4.0),
        "F2": dict(REC_FACTOR=1.0, PEN_SHAPE="linear", PEN_SLOPE=2.0),
        "F3": dict(REC_FACTOR=0.95, PEN_SHAPE="linear", PEN_SLOPE=4.0),
        "F4": dict(REC_FACTOR=0.95, PEN_SHAPE="linear", PEN_SLOPE=2.0),
        "F5": dict(REC_FACTOR=0.9, PEN_SHAPE="linear", PEN_SLOPE=4.0, CAP_R_EXP=2.0, REC_R_EXP=2.0),
        "F6": dict(REC_FACTOR=0.95, PEN_SHAPE="linear", PEN_SLOPE=4.0, CAP_R_EXP=2.0, REC_R_EXP=2.0),
        "F7": dict(REC_FACTOR=1.0, PEN_SHAPE="linear", PEN_SLOPE=4.0, CAP_R_EXP=2.0, REC_R_EXP=2.0),
        "F8": dict(REC_FACTOR=1.0, PEN_SHAPE="linear", PEN_SLOPE=2.0, RELEASE=0.5, AGG_STEP=0.75)}
KS = (0.75, 1.0, 1.25, 1.5)


def runs():
    out = []
    for name in CFGS:
        for T in (20, 30):
            for k in KS:
                out.append((name, T, k, "perf08", 0.8))
                for cap in (1.05, 1.10):
                    out.append((name, T, k, "avg", cap))
            for cap in (1.05, 1.10):
                for m in ("greedy", "best", "q1g", "q1b", "randb"):
                    out.append((name, T, 1.0, m, cap))
    return out


def spec(m, r):
    avg = E.raw_qte_score(r, profile="average")
    return {"perf08": (1.0, 1.0, "reserve", "read", {}), "avg": (0.6, avg, "mix", "read", {"PACE_Q": 0.6}),
            "greedy": (0.6, avg, "greedy", "read", {}), "best": (0.6, avg, "reserve", "read", {}),
            "q1g": (1.0, avg, "greedy", "read", {}), "q1b": (1.0, avg, "reserve", "read", {}),
            "randb": (1.0, avg, "reserve", "randguess", {})}[m]


def job(a):
    (name, T, k, m, r), cell = a
    q, qt, pac, mode, over = spec(m, r)
    cfg = dict(B, **CFGS[name], **{f"KAPPA_{T}": k}, **over)
    d, st = cell
    o = R.run_new(TUNES, r, d, R.C.track_corners(d, 0), T, st, q, qt, N, SEED, cfg=cfg, pacing=pac, mode=mode)
    return a, o["win"].mean(1), o["lock_turns"].mean(1) / T


if __name__ == "__main__":
    jobs = [(rn, c) for rn in runs() for c in CELLS]
    res = {}
    with Pool(8) as p:
        for a, w, lk in p.imap_unordered(job, jobs, chunksize=2):
            res[a] = (w, lk)
    out = {}
    for rn in runs():
        name, T, k, m, r = rn
        vals = []
        for c in CELLS:
            w, lk = res[(rn, c)]
            if m == "randb":
                b = int(res[((name, T, k, "q1b", r), c)][0][:21].argmax())
            else:
                b = int(w[:21].argmax())
            vals.append((w[b], lk[b]))
        out[f"{name}|{T}|{k}|{m}|{r}"] = [round(100 * float(x), 1) for x in np.mean(vals, 0)]
    json.dump(out, open("fix_screen.json", "w"), indent=1)
    print("done")
