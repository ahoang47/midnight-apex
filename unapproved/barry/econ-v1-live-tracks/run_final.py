"""Proposed live-track constant set: fitted ladder + finale r* + re-fitted arc walls; full report. Draft."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core, fit_arc as F, run_drift as R

FIN = tuple(json.loads(os.environ.get("FINALE", "[1.071, 1.041, 1.043, 1.071]")))
LADF = os.environ.get("LADDER", "fit_ladder_v2.json")
TAG = os.environ.get("TAG", "proposed")
lad = {x["district"]: x["ladder"] for x in json.load(open(os.path.join(core.HERE, LADF)))["fits"]}
M, mods = core.setup(lad, FIN)
ent, _, _ = core.run_arc(mods, core.arc_races(core.LIVE_ARC, M))
rd, races, walks, ev = F.fit(M, mods, ent)
spec = [dict(id=r["id"], place=r["place"], dist=r["dist"], T=r["T"], r_design=r["r_design"], xp_share=r["xp_share"],
             purse=r["purse"], B=r["B"]) for r in races if not r["billed"]]
o = R.report(lad, FIN, None, spec, tag=TAG)
o["arc_walls_r_design"] = rd
o["arc_spec"] = spec
o["finale_r"] = list(FIN)
o["billed_cells"] = F.billed_cells(walks)
json.dump(o, open(os.path.join(core.HERE, f"{TAG}.json"), "w"), indent=1, default=str)
R.show(o)
print("walls", rd)
for s in spec: print(s)
