"""Fit per-step arc story-XP multipliers (x ARC_STORY_FILL 0.80) so 80/80 story-only arrives at each billed fight at a
target level. Sequential by step; picks the middle of the multiplier plateau that lands the target. Draft."""
import json, sys, camp, arc, cands
CAMP = camp.summary(camp.run_all(cands.m_of(cands.CANDS[sys.argv[1] if len(sys.argv) > 1 else "B_mixed"])))
TARGETS = {"t55": (58, 72, 88, 109), "t62": (59, 73, 89, 110)}
grid = [round(1.0 - 0.01 * i, 2) for i in range(0, 91)]
res = {}
for tag, tl in TARGETS.items():
    am = [1.0] * 4
    for k in range(4):
        hits = []
        for m in grid:
            t = list(am); t[k] = m
            w, ev = arc.run(CAMP, t); b = arc.brief(w)
            if b["c8080"]["billed_L"][k] == tl[k]:
                hits.append(m)
        am[k] = hits[len(hits) // 2] if hits else None
        print(tag, "step", k, "plateau", (hits[-1], hits[0]) if hits else None, "pick", am[k], flush=True)
        if am[k] is None: break
    w, ev = arc.run(CAMP, am); b = arc.brief(w)
    res[tag] = dict(arc_mult=am, brief=b, issues=ev.get("issues"))
base_w, base_ev = arc.run(CAMP, 1.0)
res["arc_unchanged"] = dict(arc_mult=[1.0] * 4, brief=arc.brief(base_w), issues=base_ev.get("issues"))
json.dump(res, open(f"arc_fit_{sys.argv[1] if len(sys.argv) > 1 else 'B_mixed'}.json", "w"), indent=1)
for tag, r in res.items():
    print("==", tag, r["arc_mult"], r["issues"])
    for pr, x in r["brief"].items():
        print(" ", pr, {k: x[k] for k in ("end_L", "end_money", "t4_done", "grind", "billed", "billed_L", "min_story")})
