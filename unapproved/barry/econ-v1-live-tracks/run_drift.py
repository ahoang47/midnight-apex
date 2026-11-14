"""Drift: current LIVE econ-v1 constants (Variant C r, finale r*, FINALE_ARC) on the live-track oracle. Draft."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core, oracle


def report(ladder=None, finale_r=None, finale_B=None, arc_spec=None, tag="drift"):
    M, mods = core.setup(ladder, finale_r, finale_B)
    res = core.campaign(M, mods)
    crit = {k: v["pass_"] for k, v in res["criteria"].items()}
    bosses = []
    for rnd, d in enumerate(("street", "wangan", "touge")):
        r = M.target_r(d, 6)
        bosses.append(dict(rnd=rnd + 1, district=d, r=r, cells=core.boss_cells(r, d)))
    fin = []
    for i, d in enumerate(M.FINALE_DIST):
        fin.append(dict(F=i + 1, district=d, r=M.FINALE_R_C[i], B=M.FINALE_B[i], C=round(M.FINALE_C[i], 1),
                        L=M.FINALE_L[i], cells=core.boss_cells(M.FINALE_R_C[i], d)))
    races = core.arc_races(arc_spec or core.LIVE_ARC, M)
    entries, walks, ev = core.run_arc(mods, races)
    arc = {w["pr"]: dict(end_L=w["end_L"], end_money=w["end_money"], t4=w["t4"], aero4=w["aero4"],
                         grind={i: w["grind"][i] for i in range(4)},
                         log=[{k: x[k] for k in ("id", "L", "r", "wr_dist", "wr_hard", "wall_grinds", "to_cap_grinds", "t4")}
                              for x in w["log"]]) for w in walks}
    c3fail = [x for x in res["criteria"][3]["rows"] if x.get("fail")]
    out = dict(tag=tag, oracle_files=oracle.load()["files"], criteria=crit, grind=core.grind_summary(res),
               crit2=res["criteria"][2], crit3_fail=c3fail, crit4=res["criteria"][4]["rows"],
               crit7=res["criteria"][7], crit8=res["criteria"][8]["finale_L"], crit9=res["criteria"][9]["bosses"],
               bosses=bosses, finale=fin, arc=arc, arc_ev=ev,
               ladder={d: list(M.LADDER_R_C[d]) for d in ("street", "wangan", "touge")},
               story_rows={m: [[dict(name=r["name"], L=r["arrive_L"], r=round(r["arrive_r"], 4),
                                     wr={pr: (r["wr"][pr]["district"]["win"], core_hard(r["wr"][pr])) for pr in r["wr"]},
                                     g=r.get("grind_before", None))
                                for r in w["rows"]] for w in rnds] for m, rnds in res["results_summary"].items()})
    return out


def core_hard(pack):
    import evaluate
    return evaluate.hard_win(pack)


def show(o):
    print("criteria", o["criteria"])
    for m, g in o["grind"].items():
        print(m, [(x["wall"], x["wall_grind"], x["post"], x["total"], x["L"], x["money_usd"], x["debt_usd"]) for x in g])
    print("crit3 fails", [(x["rnd"], x["name"], x["L"], x["r"], x["wr"], x["wr_hard"]) for x in o["crit3_fail"]])
    print("crit4", [(x["rnd"], x["pr"], x["r"], x["wr10"]) for x in o["crit4"] if "pr" in x])
    print("crit7 dead", o["crit7"]["dead"])
    for b in o["bosses"] + o["finale"]:
        print(b.get("rnd", "F%d" % b.get("F", 0)), b["district"], b["r"],
              {pr: (c["district"], c["hard"], c["worst"], c["worst_track"][:6]) for pr, c in b["cells"].items()})
    print("arc issues", o["arc_ev"]["issues"], o["arc_ev"]["wall_notes"])
    for pr, a in o["arc"].items():
        print(pr, "L", a["end_L"], "$", a["end_money"], "t4", a["t4"], a["aero4"],
              [(a["grind"][i]["wall"], a["grind"][i]["to_cap"]) for i in range(4)])
        print("   ", [(x["id"], x["L"], x["r"], x["wr_hard"]) for x in a["log"]])


if __name__ == "__main__":
    o = report()
    json.dump(o, open(os.path.join(core.HERE, "drift.json"), "w"), indent=1, default=str)
    show(o)
