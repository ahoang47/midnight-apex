"""Write sim/config/heat_g2_tuned.json: the G2 tuned split (POW, HAN, EN) per track x length x boss style and measure,
plus G2's full-run win rate at that split (9 x 1000 races). Tune = argmax of the 9-batch mean (analyze_v4b.tuned_idx).
Read by sim/scripts/balance_gauntlet.py."""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, "results_v4b_meta.json")))
Z = np.load(os.path.join(HERE, "results_v4b_G2_slant_m10.npz"))
T = M["tunes"]
out = {"source": "unapproved/barry/resources-v4/retune results_v4b_G2_slant_m10.npz (9 x 1000 races per cell)",
       "order": "POW, HAN, EN", "lengths": M["lengths"], "styles": M["styles"], "cells": []}
for meas in ("avg_cap", "perf_0.8", "perf_1.0", "c8080"):
    A = Z[meas][..., 0, :].mean(0)
    for ti, (d, name) in enumerate(M["tracks"]):
        for k, L in enumerate(M["lengths"]):
            for s, st in enumerate(M["styles"]):
                i = int(A[ti, k, s, :21].argmax())
                out["cells"].append(dict(measure=meas, district=d, track=name, length=L, style=st,
                                         tune=[round(x, 4) for x in T[i]], g2_win=round(100 * float(A[ti, k, s, i]), 2),
                                         g2_even=round(100 * float(A[ti, k, s, 21]), 2)))
json.dump(out, open(os.path.join(HERE, "..", "..", "..", "..", "sim", "config", "heat_g2_tuned.json"), "w"), indent=0)
print(len(out["cells"]))
