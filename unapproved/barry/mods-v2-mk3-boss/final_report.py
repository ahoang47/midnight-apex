"""Full validation of the candidates (campaign + arc + finale) vs live. Run from sim/:
PYTHONPATH=.:../unapproved/barry/mods-v1:../unapproved/barry/skill-points-v1:../unapproved/barry/mods-v2-mk3-boss python3 ../unapproved/barry/mods-v2-mk3-boss/final_report.py"""
import json, os, sys
import mk3boss as M
import verify_live as V
from configs import CONFIGS
from velocity_shift import equations as E, progression as P
MK12 = {("R2", "MK1"): 400, ("R2", "MK2"): 900, ("R3", "MK1"): 700, ("R3", "MK2"): 1500}   # 0.6x mods-v1 (they now fill fewer levels)
PRICES = {"G1": {("R1", "MK3"): 1000, ("R2", "MK3"): 2000, ("R3", "MK3"): 4000, **MK12},
          "G2": {("R1", "MK3"): 1000, ("R2", "MK3"): 3000, ("R3", "MK3"): 4000, **MK12}}
def one(sets, xp, forced, where):
    with M.patched(sets, xp):
        out = {m: M.run(m, forced, where) for m in ("story", "mixed", "hard")}
        arc = V.arc_walk(out)
        cat = {k: dict(points=v["points"], price=v["price"], unlock=str(v["unlock"]), fills_to=v["fills_to"]) for k, v in E.MOD_CATALOG.items()
               if k.endswith("_POW_MK1") or k.endswith("_POW_MK2") or k.endswith("_POW_MK3")}
    camp = {}
    for m, (rounds, G, _) in out.items():
        camp[m] = dict(grinds=[w["total_grind"] for w in rounds], wall=[w["wall_grind"] for w in rounds],
                       rows=[[dict(rung=r["rung"], L=r["arrive_L"], wr=r["wr"], no=r["no_mk3"], forced=r["forced"], cash_pre=r["cash_pre"], equipped=r["equipped"], g10=r["grind10"]) for r in w["rows"]] for w in rounds],
                       end_cash=[round(w["money"]) for w in rounds], debt=[round(w["debt"]) for w in rounds], spent=round(G.spent))
    return dict(campaign=camp, arc=arc, catalog=cat)
res = {"live": one(None, None, 0, "boss")}
for n, c in CONFIGS.items():
    res[n] = one(M.make_sets(c["fills"], PRICES[n]), c["xp"], c["forced"], c["where"])
json.dump(res, open(os.path.join(M.HERE, "results.json"), "w"), indent=1, default=str)
for n, r in res.items():
    print("=====", n)
    for m, x in r["campaign"].items():
        pr = {"story": ["c8080"], "mixed": ["c6080", "c8060", "c8080"], "hard": ["c6060"]}[m]
        print(m, "grinds", x["grinds"], "wall", x["wall"], "end cash", x["end_cash"], "debt", x["debt"], "spent", x["spent"])
        for i, w in enumerate(x["rows"]):
            b = w[-1]
            print("   R%d boss L%d" % (i + 1, b["L"]), {p: (b["wr"][p], b["no"][p]) for p in pr},
                  "min80" if m != "hard" else "min6060", min(rr["wr"]["c8080" if m != "hard" else "c6060"] for rr in w),
                  "pre-boss noMk3 min", min(rr["no"]["c8080" if m != "hard" else "c6060"] for rr in w[:-1]), "g10 min", min(rr["g10"]["c8080" if m != "hard" else "c6060"] for rr in w))
    for p, a in r["arc"].items(): print("arc", p, a)
    print("cat", {k.removeprefix("MOD_"): (v["points"], v["price"], v["fills_to"], v["unlock"]) for k, v in r["catalog"].items()})
