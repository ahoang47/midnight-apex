"""Verify the live mods-v1 go-live (sim/ progression Garage + buyer) against the draft: campaign walks, at-cap bosses,
and the pre-finale arc + finale through the draft econ-v1 walker hooked to the live Garage. Run from sim/:
PYTHONPATH=.:../unapproved/barry/skill-points-v1:../unapproved/barry/mods-v1 python3 ../unapproved/barry/mods-v1/verify_live.py"""
import copy, json, os, io, contextlib
import retune as R
P, E, camp, arc, A, core = R.P, R.E, R.camp, R.arc, R.A, R.core
HERE = os.path.dirname(os.path.abspath(__file__))
DIST = ("touge", "wangan", "street", "touge")
MODE_OF = {"c8080": "story", "c6080": "mixed", "c8060": "mixed", "c6060": "hard"}

def campaign():
    out = {m: P.run_with_garage(m) for m in ("story", "mixed", "hard")}
    s = {}
    for m, (rounds, G, _) in out.items():
        s[m] = dict(grinds=[w["total_grind"] for w in rounds], split=[(w["wall_grind"], w["post_wall_to_cap"]) for w in rounds],
                    min8080=[min(min(r["wr"]["c8080"]["district"], P.hard_win(r["wr"]["c8080"])) for r in w["rows"]) for w in rounds],
                    boss8080=[P.hard_win(w["rows"][-1]["wr"]["c8080"]) for w in rounds],
                    boss_check=[P.boss_check(round(w["rows"][-1]["arrive_r"], 4), E.ROUND_DISTRICTS[i].lower(), w["rows"][-1]["pow_share"] / 100)
                                for i, w in enumerate(rounds)],
                    grind10_min={pr: min(r["grind10"][pr] for w in rounds for r in w["rows"]) for pr in P.PROFILES},
                    spent=G.spent, end_money=round(rounds[-1]["money"], 2))
    return out, s

def arc_walk(out):
    with contextlib.redirect_stdout(io.StringIO()):
        res = camp.run_all(camp.uniform((1, 1, 1)))
    ent = arc.entries_for(camp.summary(res))
    races = core.arc_races(core.LIVE_ARC, arc.M, fill=core.LIVE.ARC_STORY_FILL); ids = [rc["id"] for rc in races]
    orig = (A.combat_vs, A.shop_arc, A.credit_arc, A.wr_pack); CUR = {}
    step_of = lambda C: min(range(4), key=lambda i: abs(A.FINALE_C[i] - C))
    def shop(s_, u):
        st = CUR["step"]; s_.money = s_.G.shop(s_.money, int(s_.L), 3 + st, DIST[st], s_.done, False, "arc")
    def cvs(s_, C):
        CUR["step"] = step_of(C); shop(s_, None); return s_.G.power(int(s_.L), 3 + CUR["step"], DIST[CUR["step"]])
    def credit(s_, amount, u):
        if abs(amount - A.GRIND_PAY) > 1e-6:
            s_.done.add(P.arc_unlock_token(ids[CUR["i"]])); CUR["i"] += 1
        if s_.debt > 0:
            take = min(s_.debt, E.DEBT_SHARE * amount); s_.debt -= take; s_.money += amount - take
        else:
            s_.money += amount
        shop(s_, u)
    A.combat_vs, A.shop_arc, A.credit_arc = cvs, shop, credit
    A.wr_pack = lambda pr, r, T, district: A.wr_cell(pr, r, T, district, True)
    walks = []
    try:
        for pr in P.PROFILES:
            rounds, G, done = out[MODE_OF[pr]]; last = rounds[-1]; e = ent[pr]
            e.L, e.bag, e.money, e.debt = last["L"], last["bag"], last["money"], last["debt"]
            e.G, e.done = copy.deepcopy(G), set(done); CUR.update(step=0, i=0)
            walks.append(A.walk_profile(pr, e, races, MODE_OF[pr]))
    finally:
        A.combat_vs, A.shop_arc, A.credit_arc, A.wr_pack = orig
    return {w["pr"]: dict(grind=[w["grind"][i]["total"] for i in range(4)], finale=[x["wr_hard"] for x in w["log"] if x["billed"]],
                          min_story=min(x["wr_hard"] for x in w["log"] if not x["billed"]), end_money=w["end_money"]) for w in walks}

if __name__ == "__main__":
    out, s = campaign(); a = arc_walk(out)
    caps = P.boss_check_at_cap()
    res = dict(campaign=s, arc=a, at_cap=[(c["c6060"], c["c8080"]) for c in caps])
    draft = json.load(open(os.path.join(HERE, "catalog_results.json")))["final_4"]
    same = dict(grinds={m: s[m]["grinds"] == draft["campaign"][m]["grinds"] for m in s},
                min8080={m: s[m]["min8080"] == draft["campaign"][m]["min_8080"] for m in s},
                spent={m: s[m]["spent"] == draft["campaign"][m]["spent"] for m in s},
                arc={pr: a[pr]["finale"] == draft["arc"][pr]["finale_hard"] and a[pr]["grind"] == draft["arc"][pr]["grind"] for pr in a})
    res["matches_draft"] = same
    json.dump(res, open(os.path.join(HERE, "verify_live.json"), "w"), indent=1, default=str)
    for m, x in s.items():
        print(m, "grinds", x["grinds"], x["split"], "min80", x["min8080"], "boss80", x["boss8080"], "boss_check", [(b["c6060"], b["c8080"]) for b in x["boss_check"]],
              "grind10 min", x["grind10_min"]["c6060"], x["grind10_min"]["c8080"], "spent", x["spent"], "end", x["end_money"])
    print("at cap (boss_check_at_cap)", res["at_cap"])
    for pr, x in a.items():
        print("arc", pr, x)
    print("matches draft", same)
