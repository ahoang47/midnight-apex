"""Screen the hard-block variant (a stance you cannot pay for is not allowed) for a setting that gets closer to all
three combat targets. N=2000, seed 7, track #1 per district, 10/20/30 turns, 3 boss styles, even spread.
Output: hb_fit.json. Screening only; the chosen setting is then rerun at full size by run_hardblock.py."""
import itertools, json
import numpy as np
import resources_v1 as R
import calibrate as K
out = []
for ks, tf in itertools.product([1.0, 1.25, 1.5, 2.0], [0.5, 0.4, 0.3]):
    cfg = dict(KAPPA_SCALE=ks, TANK_FACTOR=tf)
    m = {}
    for kind, r in (("perf", 0.8), ("perf", 1.0), ("avg", 1.05), ("avg", 1.10)):
        qr = 1.0 if kind == "perf" else 0.6; qt = 1.0 if kind == "perf" else K.avg_q(r)
        v = [R.run_new(K.EVEN, r, d, K.LAPS[d], T, st, qr, qt, K.N, K.SEED, hard_block=True, cfg=cfg)[0][0]
             for d in K.D for T in (10, 20, 30) for st in R.STYLES]
        m[f"{kind}{r}"] = round(100 * float(np.mean(v)), 1)
    out.append(dict(KAPPA_SCALE=ks, TANK_FACTOR=tf, **m)); print(out[-1], flush=True)
json.dump(out, open("hb_fit.json", "w"), indent=1)
