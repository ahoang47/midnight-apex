"""Can any stat leverage hit all three combat targets at once? Sweep KAPPA_SCALE and TANK_R_EXP on the chosen base
config (N=2000, seed 7, track #1 per district, 10/20/30 turns, balanced boss, even spread). Output: target_fit.json."""
import itertools, json
import numpy as np
import resources_v1 as R
import calibrate as K
BASE = dict(EMPTY_RULE="payoff", TANK_WITH_R=True, TANK_FACTOR=0.5, SHARE_EXPONENT=2.0, SUSP_REC_FACTOR=0.6, EMPTY_MULT=0.4)
out = []
for ks, te in itertools.product([1.0, 1.5, 2.0, 2.5, 3.0, 4.0], [1.0, 3.0]):
    cfg = dict(BASE, KAPPA_SCALE=ks, TANK_R_EXP=te)
    m = {}
    for kind, r in (("perf", 0.8), ("perf", 0.9), ("perf", 1.0), ("avg", 1.0), ("avg", 1.05), ("avg", 1.10)):
        qr = 1.0 if kind == "perf" else 0.6; qt = 1.0 if kind == "perf" else K.avg_q(r)
        v = [R.run_new(K.EVEN, r, d, K.LAPS[d], T, "balanced", qr, qt, K.N, K.SEED, cfg=cfg)[0][0] for d in K.D for T in (10, 20, 30)]
        m[f"{kind}{r}"] = round(100 * float(np.mean(v)), 1)
    out.append(dict(KAPPA_SCALE=ks, TANK_R_EXP=te, **m)); print(out[-1], flush=True)
json.dump(out, open("target_fit.json", "w"), indent=1)
