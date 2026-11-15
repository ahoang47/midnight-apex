"""Shift, don't cut: per step, the story race just before the billed fight (P4, M12, M22, M32) pays less XP so 80/80
story-only arrives at the billed fight at a target level, and the first race after it (M11, M21, M31) pays more so
80/80 is back at its live level by the next wall race. Sequential fit, middle of each plateau. Draft."""
import json, sys, camp, arc, cands
CN = sys.argv[1] if len(sys.argv) > 1 else "B_mixed"
CAMP = camp.summary(camp.run_all(cands.m_of(cands.CANDS[CN])))
TARGETS = {"t55": (58, 72, 88, 109), "t62": (59, 73, 89, 110)}
LAST = ("P4", "M12", "M22", "M32"); FIRST = (None, "M11", "M21", "M31"); NEXTWALL = (None, "M12", "M22", "M32")
base = arc.brief(arc.run(CAMP, 1.0)[0])["c8080"]
baseL = {i: L for i, L, _ in base["log"]}
def lv(b, rid): return next(L for i, L, _ in b["c8080"]["log"] if i == rid)
cut_grid = [round(1.0 - 0.01 * i, 2) for i in range(101)]
boost_grid = [round(1.0 + 0.02 * i, 2) for i in range(151)]
res = {}
for tag, tl in TARGETS.items():
    am = {}
    for k in range(4):
        if k > 0:   # boost first race of step k so 80/80 reaches the next wall race at its live level
            hits = []
            for m in boost_grid:
                t = dict(am); t[FIRST[k]] = m
                if lv(arc.brief(arc.run(CAMP, t)[0]), NEXTWALL[k]) == baseL[NEXTWALL[k]]: hits.append(m)
            am[FIRST[k]] = hits[len(hits) // 2] if hits else None
            print(tag, FIRST[k], "plateau", (hits[0], hits[-1]) if hits else None, "pick", am[FIRST[k]], flush=True)
        hits = []
        for m in cut_grid:
            t = dict(am); t[LAST[k]] = m
            if arc.brief(arc.run(CAMP, t)[0])["c8080"]["billed_L"][k] == tl[k]: hits.append(m)
        am[LAST[k]] = hits[len(hits) // 2] if hits else None
        print(tag, LAST[k], "plateau", (hits[-1], hits[0]) if hits else None, "pick", am[LAST[k]], flush=True)
    w, ev = arc.run(CAMP, am)
    res[tag] = dict(arc_mult=am, brief=arc.brief(w), issues=ev.get("issues"))
w, ev = arc.run(CAMP, 1.0); res["arc_unchanged"] = dict(arc_mult={}, brief=arc.brief(w), issues=ev.get("issues"))
json.dump(res, open(f"arc_fit2_{CN}.json", "w"), indent=1)
for tag, r in res.items():
    print("==", tag, r["arc_mult"], r["issues"])
    for pr, x in r["brief"].items():
        print(" ", pr, {k: x[k] for k in ("end_L", "end_money", "t4_done", "grind", "billed", "billed_L", "min_story")})
        if pr == "c8080": print("   log", x["log"])
