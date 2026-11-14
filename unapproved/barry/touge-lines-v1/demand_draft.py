"""Demand / wear on the draft 10-variant set (no races). Writes demand_draft.json."""
from __future__ import annotations
import json, os
import numpy as np
import model as M

HERE = os.path.dirname(os.path.abspath(__file__))
RES = ("POW", "HAN", "EN")


def r3(x):
    return [round(float(v), 3) for v in x]


def r4(x):
    return [round(float(v), 4) for v in x]


def mix(x):
    x = np.asarray(x, float)
    return r3(x / x.sum())


def demand_table(use_gravity):
    M.apply(use_gravity=use_gravity)
    c = M.R.cfg_of(M.g2_cfg())
    rows = {}
    for (d, name), lap in M.track_list():
        raw = M.V2.raw_demand(d, lap, c["AGG_STEP"], c["TANK_REF_Q"])
        w = M.R.wear_of(d, lap, c)
        final = raw * w
        rows[name] = dict(
            district=d, lap=list(lap),
            raw_POW_HAN_EN=r4(raw), raw_mix=mix(raw),
            wear_POW_HAN_EN=r4(w),
            after_wear_POW_HAN_EN=r4(final), after_wear_mix=mix(final),
            after_wear_total=round(float(final.sum()), 3),
        )
    by_d = {}
    for d in ("touge", "wangan", "street"):
        fins = [v["after_wear_POW_HAN_EN"] for v in rows.values() if v["district"] == d]
        raws = [v["raw_POW_HAN_EN"] for v in rows.values() if v["district"] == d]
        by_d[d] = dict(
            raw_mix=mix(np.mean(raws, 0)),
            after_wear_mix=mix(np.mean(fins, 0)),
            after_wear_POW_HAN_EN=r4(np.mean(fins, 0)),
        )
    avg = M.R.avg_demand_v(c)
    return dict(
        use_gravity=use_gravity,
        n_laps=len(rows),
        avg_demand_POW_HAN_EN=r4(avg),
        avg_mix=mix(avg),
        avg_total=round(float(np.sum(avg)), 3),
        by_district=by_d,
        by_track=rows,
    )


out = {
    "gravity_on": demand_table(True),
    "gravity_off": demand_table(False),
    "assumptions": M.DRAFT["assumptions"],
    "sources": M.DRAFT["sources"],
}
json.dump(out, open(os.path.join(HERE, "demand_draft.json"), "w"), indent=1)
print("avg demand gravity on ", out["gravity_on"]["avg_demand_POW_HAN_EN"], "mix", out["gravity_on"]["avg_mix"], "n", out["gravity_on"]["n_laps"])
print("avg demand gravity off", out["gravity_off"]["avg_demand_POW_HAN_EN"], "mix", out["gravity_off"]["avg_mix"])
print("after-wear by district ON ", out["gravity_on"]["by_district"])
print("after-wear by district OFF", out["gravity_off"]["by_district"])
for g in ("gravity_on", "gravity_off"):
    print("===", g, "===")
    for name, v in out[g]["by_track"].items():
        if v["district"] == "touge" or name.endswith("_CW") or name.endswith("Uphill") or name.endswith("Downhill"):
            print(f"  {name:28} raw={v['raw_mix']} after={v['after_wear_mix']} tot={v['after_wear_total']}")
