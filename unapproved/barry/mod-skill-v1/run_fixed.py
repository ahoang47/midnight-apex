"""Fixed layout POW/HAN/EN/FLEX: XP recalibration (calibrate.py method) + story/mixed/hard walks, spirit OFF (live tables).
Flex configs: 'PEE' = flex own stat P in Street, E in Wangan, E in Touge (one slot, re-typed per round, points carry);
'free' = flex with no own-stat floor. Also re-walks with the OLD recommended calibration (story table + grind XP 13/15/14).
-> fixed_layout.json"""
import json, os
import fixed_layout as FL, calibrate as CA, walk as W

HERE = os.path.dirname(os.path.abspath(__file__))
FLEX = {"PEE": {"street": "P", "wangan": "E", "touge": "E"}, "free": {"street": "free", "wangan": "free", "touge": "free"}}
OLD = json.load(open(os.path.join(HERE, "calib_mk1_list_spill_tougephee.json")))


def summary(ws):   # copied from run_all.py
    out = []
    for w in ws:
        rows = w["rows"]
        out.append(dict(rnd=w["rnd"], grind=w["total_grind"], low8080=min(x["wr"]["c8080"] for x in rows),
                        boss8080=rows[-1]["wr"]["c8080"], boss6060=rows[-1]["wr"]["c6060"], boss_r=rows[-1]["r"],
                        boss_pow_share=rows[-1]["pow_share"], end_points=w["end_points"], xp_lost=w["xp_lost"],
                        max_tune_dist=w["max_tune_dist"], at_cap_end=w["at_cap_end"]))
    return out


CA.SPILL, CA.KITS = True, None
res = dict(ceil=FL.MS.CEIL, cap_points=[3000 + 4 * c for c in FL.MS.CEIL], configs={})
for name, fx in FLEX.items():
    FL.use(fx)
    CA.SHORT.clear(); tab = CA.story_table(0.60, "mk1_list"); g = CA.grind_cal(0.60, tab, "mk1_list")
    cfg = dict(story_table=tab, grind_xp=g, story_shortfall=dict(CA.SHORT), walks={}, walks_old_calib={})
    for m in ("story", "mixed", "hard"):
        cfg["walks"][m] = summary(W.walk(m, 0.60, grind_xp=tuple(g), story_table=tab, price="mk1_list", spill=True))
        cfg["walks_old_calib"][m] = summary(W.walk(m, 0.60, grind_xp=tuple(OLD["grind_xp"]), story_table=OLD["story_table"],
                                                   price="mk1_list", spill=True))
    res["configs"][name] = cfg
    print(name, "grind XP", g, "shortfall>0", {k: v for k, v in CA.SHORT.items() if v > 0})
    for m in ("story", "mixed", "hard"):
        print(" ", m, [(s["grind"], s["low8080"], s["boss6060"], s["boss8080"], s["boss_r"], s["end_points"], s["xp_lost"], s["max_tune_dist"]) for s in cfg["walks"][m]])
        print("  old-cal", m, [(s["grind"], s["low8080"], s["boss6060"], s["boss8080"], s["end_points"], s["xp_lost"]) for s in cfg["walks_old_calib"][m]])
    print("  story table", tab)
json.dump(res, open(os.path.join(HERE, "fixed_layout.json"), "w"), indent=1)
