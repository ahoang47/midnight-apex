"""Coarse calibration sweep over the resource placeholders (N=2000 per cell, seed 7, track #1 of each district,
balanced boss). Purpose: find a region where the retune gap appears AND the combat targets are near. Output:
calibrate.json. These are screening numbers; the final numbers come from run_resources_v1.py."""
import itertools, json, sys, time
import numpy as np
import resources_v1 as R
E = R.E
N, SEED = 2000, 7
G = R.tune_grid(); EVEN = np.array([[1/3, 1/3, 1/3]])
D = ("touge", "wangan", "street")
LAPS = {d: R.C.track_corners(d, 0) for d in D}

def avg_q(r): return E.raw_qte_score(r, profile="average")

def metrics(cfg):
    m = {}
    for kind, r in (("perf", 0.8), ("perf", 1.0), ("avg", 1.05), ("avg", 1.10)):
        qr = 1.0 if kind == "perf" else 0.6; qt = 1.0 if kind == "perf" else avg_q(r)
        v = [R.run_new(EVEN, r, d, LAPS[d], T, "balanced", qr, qt, N, SEED, cfg=cfg)[0][0] for d in D for T in (10, 20, 30)]
        m[f"{kind}{r}"] = round(100 * float(np.mean(v)), 1)
        m[f"{kind}{r}_range"] = (round(100 * min(v), 1), round(100 * max(v), 1))
    W = {}
    for d in D:
        for T in (10, 20, 30):
            W[(d, T)] = R.run_new(np.vstack([G, EVEN]), 1.05, d, LAPS[d], T, "balanced", 0.6, avg_q(1.05), N, SEED, cfg=cfg)[0]
    gaps_even, gaps_else = [], []
    for (d, T), w in W.items():
        best = w[:-1].max(); even = w[-1]
        other = np.mean([W[(d2, T)][:-1] for d2 in D if d2 != d], axis=0)
        j = int(np.argmax(other))
        gaps_even.append(best - even); gaps_else.append(best - w[j])
    m["gap_vs_even_mean"] = round(100 * float(np.mean(gaps_even)), 1)
    m["gap_vs_else_mean"] = round(100 * float(np.mean(gaps_else)), 1)
    m["gap_vs_else_max"] = round(100 * float(np.max(gaps_else)), 1)
    m["best_tunes"] = {f"{d}{T}": [round(x, 2) for x in G[int(np.argmax(w[:-1]))]] for (d, T), w in W.items()}
    return m

if __name__ == "__main__":
    grid = dict(EMPTY_RULE=["payoff", "downgrade"], TANK_WITH_R=[False, True], TANK_FACTOR=[0.6, 0.8, 1.0],
                SHARE_EXPONENT=[1.0, 2.0], EMPTY_MULT=[0.4, 0.0])
    out = []
    keys = list(grid)
    for vals in itertools.product(*grid.values()):
        cfg = dict(zip(keys, vals)); t0 = time.time()
        m = metrics(cfg); out.append(dict(cfg=cfg, **m))
        print(json.dumps(cfg), {k: v for k, v in m.items() if k != "best_tunes" and not k.endswith("range")}, f"{time.time()-t0:.0f}s", flush=True)
        json.dump(out, open("calibrate.json", "w"), indent=1)
