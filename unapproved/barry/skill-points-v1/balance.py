"""Run the live progression walk (story / mixed / hard), the at-cap boss check, and the draft arc/finale walker with
SP(L) replaced by each whole-number scheme's table (integer levels only). Draft, in memory, sim/ untouched."""
import sys, os, json, copy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "story-xp-v1"))
import schemes as SC
import arc, camp, core           # story-xp-v1 harness: live table, live constants, draft arc walker
E, P = camp.E, camp.P
M = arc.M
ORIG_E, ORIG_M = E.sp_at_level, M.sp_at

def install(tab):
    def f(L, _o=ORIG_E):
        return tab[int(L)] if tab is not None and float(L).is_integer() and 0 <= L <= SC.LMAX else _o(L)
    def g(L, _o=ORIG_M):
        return tab[int(L)] if tab is not None and float(L).is_integer() and 0 <= L <= SC.LMAX else _o(L)
    E.sp_at_level = f; M.sp_at = g

def evaluate(tab):
    install(tab)
    try:
        s = camp.summary(camp.run_all(camp.uniform((1, 1, 1))))
        caps = []
        for rnd, d in enumerate(E.ROUND_DISTRICTS):
            r = P.combat_power(E.CAP_LEVEL[rnd], rnd) / E.opponent_budget(rnd, 6)
            caps.append(P.boss_check(round(r, 4), d))
        st = s["story"][2]
        ent = arc.entries_for(s)
        raw = P.run("story")[2]; ent["c8080"].L = raw["L"]; ent["c8080"].bag = raw["bag"]   # live end L and bag
        races = core.arc_races(core.LIVE_ARC, M, fill=core.LIVE.ARC_STORY_FILL)
        _, walks, ev = core.run_arc(arc.MODS, races, ent)
        b = arc.brief(walks)
        return dict(campaign=s, at_cap=caps, arc=b, arc_issues=ev.get("issues"))
    finally:
        install(None)

if __name__ == "__main__":
    out = {"live": evaluate(None)}
    for k, s in SC.SCHEMES.items():
        out[k] = evaluate(s["table"])
    out["S2alt_steps(rejected)"] = evaluate(SC.rejected()["table"])
    json.dump(out, open(os.path.join(HERE, "balance.json"), "w"), indent=1, default=str)
    for k, o in out.items():
        c = o["campaign"]
        print("==", k)
        print("  story boss (L, hard80):", [(x["boss_L"], x["boss"]["c8080"]) for x in c["story"]], "min80", [x["min8080"][0] for x in c["story"]], "end", [x["L_end"] for x in c["story"]])
        print("  mixed grind:", [(x["wall_grind"], x["post"]) for x in c["mixed"]], " hard grind:", [x["total"] for x in c["hard"]], "caps", all(x["cap"] for x in c["mixed"] + c["hard"]))
        print("  at-cap boss 60/60 / 80/80 hard:", [(x["c6060"], x["c8080"], x["ok"]) for x in o["at_cap"]])
        for pr, a in o["arc"].items():
            print("  arc", pr, "grind", a["grind"], "billed", a["billed"], "L", a["billed_L"], "min", a["min_story"], "end", a["end_L"], a["end_money"])
        print("  issues", o["arc_issues"])
