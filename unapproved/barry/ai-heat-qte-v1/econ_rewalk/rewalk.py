"""Econ re-walk after the 2026-11-19 go-live (Barry DRAFT). Runs the mod_skill fixed-layout walks (unapproved/barry/mod-skill-v1,
read-only, imported from a copy) with the APPROVED calibration (story table + grind XP 13/12/14 from fixed_layout.json PEE)
on the NEW live sim/tables, plus the recalibrated values run_fixed.py would pick now. The walk's boss row reads the boss-shape
cells (win_pack boss=True, the one-line fix the copy applies to walk.py). -> rewalk.json
Usage: MODSKILL=/path/to/copy/of/mod-skill-v1 python3 rewalk.py   (the copy must sit at <repo>/unapproved/barry/ so it imports <repo>/sim)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.environ["MODSKILL"]; sys.path.insert(0, MS)
import fixed_layout as FL, walk as W, calibrate as CA
APP = json.load(open(os.path.join(HERE, "..", "..", "mod-skill-v1", "fixed_layout.json")))   # approved/committed calibration
cfg = APP["configs"]["PEE"]
FL.use({"street": "P", "wangan": "E", "touge": "E"}); CA.SPILL, CA.KITS = True, None
def summ(ws):
    return [dict(rnd=w["rnd"], grind=w["total_grind"], low8080=min(x["wr"]["c8080"] for x in w["rows"]),
                 boss6060=w["rows"][-1]["wr"]["c6060"], boss8080=w["rows"][-1]["wr"]["c8080"], boss_r=w["rows"][-1]["r"],
                 end_points=w["end_points"]) for w in ws]
out = dict(ceil=FL.MS.CEIL, cap_points=[3000 + 4 * c for c in FL.MS.CEIL], approved_grind_xp=cfg["grind_xp"], walks={})
for m in ("story", "mixed", "hard"):
    out["walks"][m] = summ(W.walk(m, 0.60, grind_xp=tuple(cfg["grind_xp"]), story_table=cfg["story_table"], price="mk1_list", spill=True))
CA.SHORT.clear(); tab = CA.story_table(0.60, "mk1_list"); g = CA.grind_cal(0.60, tab, "mk1_list")
out["recalibrated"] = dict(grind_xp=g, story_table=tab, shortfall={k: v for k, v in CA.SHORT.items() if v > 0})
json.dump(out, open(os.path.join(HERE, "rewalk.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
