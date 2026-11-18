"""Run every mod_skill walk used in RESULTS.md and write results.json.
Configs (each with its own XP calibration, calibrate.py, on Mk1 list prices):
  strict      = Austin's rule as written: all of a race's XP into ONE mod (overflow lost), MOD_SLOT_PATTERN kits
  spill       = overflow past the picked mod's ceiling spills to the next greedy pick
  touge_phee  = free kit pick: Touge runs the Wangan kit PHEE (on tune at X = 0.60) instead of PPHE
  recommended = spill + touge_phee
Price sweep on the recommended config with its XP tables held fixed (cash is the only thing that changes)."""
import json, os
from walk import walk, CEIL, CAP_POWER, STOCK, PRICES
from velocity_shift import progression as P, equations as E

HERE = os.path.dirname(os.path.abspath(__file__))
live = json.load(open(os.path.join(HERE, "baseline_live.json")))
CONFIGS = {"strict": ("calib_mk1_list.json", False, None), "spill": ("calib_mk1_list_spill.json", True, None),
           "touge_phee": ("calib_mk1_list_tougephee.json", False, {"touge": "PHEE"}),
           "recommended": ("calib_mk1_list_spill_tougephee.json", True, {"touge": "PHEE"})}
MK1 = PRICES["mk1_list"]
PRICE_SWEEP = {f"mk1_x{k}": tuple(k * p for p in MK1) for k in (1, 2, 3, 4, 6, 8)}
PRICE_SWEEP.update(mk3_list=PRICES["mk3_list"], spend_matched=PRICES["spend_matched"])


def summary(ws):
    out = []
    for w in ws:
        rows = w["rows"]
        lag = [x["rung"] for x in rows if any(int(t) < w["rnd"] for t in x["tiers"][1::2])]
        out.append(dict(rnd=w["rnd"], grind=w["total_grind"], low8080=min(x["wr"]["c8080"] for x in rows),
                        boss8080=rows[-1]["wr"]["c8080"], boss6060=rows[-1]["wr"]["c6060"], boss_r=rows[-1]["r"],
                        end_points=w["end_points"], cash=w["money"], debt=w["debt"], spent=w["spent"], xp_lost=w["xp_lost"],
                        max_tune_dist=w["max_tune_dist"], tier_lag_rungs=lag))
    return out


res = dict(X=0.60, ceil=CEIL, cap_power=CAP_POWER, stock=STOCK, configs={}, price_sweep={}, live={})
for name, (cf, spill, kits) in CONFIGS.items():
    cal = json.load(open(os.path.join(HERE, cf)))
    runs = {m: walk(m, cal["X"], grind_xp=tuple(cal["grind_xp"]), story_table=cal["story_table"], price="mk1_list",
                    spill=spill, kits=kits) for m in ("story", "mixed", "hard")}
    res["configs"][name] = dict(calibration=cal, runs=runs, summary={m: summary(v) for m, v in runs.items()})
    if name == "recommended":
        for pn, pt in PRICE_SWEEP.items():
            res["price_sweep"][pn] = dict(prices=pt, summary={m: summary(walk(m, cal["X"], grind_xp=tuple(cal["grind_xp"]),
                                          story_table=cal["story_table"], price=pt, spill=spill, kits=kits))
                                          for m in ("story", "mixed", "hard")})
for m in ("story", "mixed", "hard"):
    res["live"][m] = [dict(rnd=i + 1, grind=w["total_grind"], low8080=min(x["c8080"] for x in w["rows"]),
                           boss8080=w["rows"][-1]["c8080"], boss6060=w["rows"][-1]["c6060"], cash=w["money"], debt=w["debt"])
                      for i, w in enumerate(live[m])]
res["live_boss_at_cap"] = live["boss_at_cap"]
res["finale_ceil"] = [dict(step=f"F{i + 1}", C=round(C, 2), cap=L, ceil_per_mod=round((10 * C - STOCK) / 4, 1),
                           stock_share=round(STOCK / (10 * C), 3)) for i, (C, L) in enumerate(P.finale_caps())]
json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1)
for k, v in res["configs"].items():
    for m, rs in v["summary"].items():
        print(k, m, [(r["grind"], r["low8080"], r["boss8080"], r["boss6060"], r["cash"], r["xp_lost"], r["max_tune_dist"]) for r in rs])
for k, v in res["price_sweep"].items():
    s = v["summary"]; print(k, v["prices"], "story", [(r["low8080"], r["boss8080"], r["tier_lag_rungs"][-1:] and len(r["tier_lag_rungs"])) for r in s["story"]],
          "mixed g", [r["grind"] for r in s["mixed"]], "hard g", [r["grind"] for r in s["hard"]], "mixed low", [r["low8080"] for r in s["mixed"]],
          "cash end", [r["cash"] for r in s["story"]])
