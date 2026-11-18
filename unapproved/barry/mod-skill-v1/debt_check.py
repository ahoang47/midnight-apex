"""How much of the R1 cash gate is the Sabine debt: recommended config at 1-4x Mk1 prices with the debt on vs off
(DEBT_AMOUNT patched in memory only; equations.py is not edited)."""
import json, os
from walk import walk, PRICES
from velocity_shift import equations as E
cal = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "calib_mk1_list_spill_tougephee.json")))
out = {}
for debt in (16000.0, 0.0):
    E.DEBT_AMOUNT = debt
    for k in (1, 2, 3, 4):
        pt = tuple(k * p for p in PRICES["mk1_list"])
        s = walk("story", 0.6, grind_xp=tuple(cal["grind_xp"]), story_table=cal["story_table"], price=pt, spill=True, kits={"touge": "PHEE"})
        m = walk("mixed", 0.6, grind_xp=tuple(cal["grind_xp"]), story_table=cal["story_table"], price=pt, spill=True, kits={"touge": "PHEE"})
        out[f"debt{int(debt)}_x{k}"] = dict(story_R1_low=min(x["wr"]["c8080"] for x in s[0]["rows"]), story_R1_boss=s[0]["rows"][-1]["wr"]["c8080"],
                                            mixed_R1_grind=m[0]["total_grind"], story_R2_boss=s[1]["rows"][-1]["wr"]["c8080"])
E.DEBT_AMOUNT = 16000.0
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "debt_check.json"), "w"), indent=1)
for k, v in out.items(): print(k, v)
