"""Second calibration pass after normalising the share curve (tank multipliers sum to 3). Same cells as calibrate.py."""
import itertools, json, time
import calibrate as K
grid = dict(EMPTY_RULE=["payoff", "downgrade"], TANK_WITH_R=[True], TANK_FACTOR=[0.5, 0.6, 0.7],
            SHARE_EXPONENT=[1.0, 2.0], SUSP_REC_FACTOR=[0.85, 0.6], EMPTY_MULT=[0.4])
out = []
for vals in itertools.product(*grid.values()):
    cfg = dict(zip(grid, vals)); t0 = time.time()
    m = K.metrics(cfg); out.append(dict(cfg=cfg, **m))
    print(json.dumps(cfg), {k: v for k, v in m.items() if not k.endswith("range")}, f"{time.time()-t0:.0f}s", flush=True)
    json.dump(out, open("calibrate2.json", "w"), indent=1)
