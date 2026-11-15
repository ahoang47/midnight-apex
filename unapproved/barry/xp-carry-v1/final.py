"""Before / after for xp-carry-v1 on live mods-v1: campaign rows, at-cap bosses, arc + finale (econ-v1 walker hooked to the
live Garage via mods-v1/verify_live.arc_walk). Run from sim/:
PYTHONPATH=.:../unapproved/barry/xp-carry-v1:../unapproved/barry/mods-v1:../unapproved/barry/skill-points-v1 python3 ../unapproved/barry/xp-carry-v1/final.py"""
import json, os, contextlib
import carry as C, catchup as K, verify_live as V
from velocity_shift import equations as E, progression as P
HERE = os.path.dirname(os.path.abspath(__file__))
def mult_b2(b2):
    m = [list(r) for r in E.STORY_XP_MULT]; m[1][6] = b2; return tuple(tuple(r) for r in m)
def tr(dm2, do1):
    t = {k: list(v) for k, v in E.LADDER_TARGET_R.items()}; t["wangan"][3] += dm2; t["wangan"][4] += do1
    return {k: tuple(round(x, 4) for x in v) for k, v in t.items()}
VARIANTS = {
    "live (reset to prev cap)": (False, {}),
    "carry, no fix": (True, {}),
    "fix C: catch-up XP 0.75 + R2 boss XP 1.5": (True, dict(story_xp=K.make(0.75), STORY_XP_MULT=mult_b2(1.5))),
    "fix B: R2 boss XP 1.5 + R2 mat2/oh1 r +0.005": (True, dict(STORY_XP_MULT=mult_b2(1.5), LADDER_TARGET_R=tr(.005, .005))),
}
res = {}
for name, (carry, patch) in VARIANTS.items():
    with C.patched(**patch):
        o = C.summary(carry)
        out = {m: (o[m]["out"], o[m]["G"], o[m]["done"]) for m in o}
        arc = V.arc_walk(out)
        caps = P.boss_check_at_cap()
    res[name] = dict(campaign={m: {k: v for k, v in x.items() if k not in ("out", "G", "done")} for m, x in o.items()},
                     g10=min(r["grind10"]["c8080"] for w in o["story"]["out"] for r in w["rows"]),
                     g10_6060=min(r["grind10"]["c6060"] for w in o["hard"]["out"] for r in w["rows"]),
                     arc=arc, at_cap=[(c["c6060"], c["c8080"]) for c in caps])
json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str)
for n, r in res.items():
    s = r["campaign"]["story"]
    print("=====", n)
    print(" story enter", s["enter"], "end", s["endL"], "min80", s["min80"], "boss80", s["boss80"], "cash", s["cash"], "spent", s["spent"])
    for i, w in enumerate(s["rows"]): print("   R%d" % (i + 1), [(x[0], x[1], x[3]) for x in w])
    for m in ("mixed", "hard"):
        x = r["campaign"][m]; print(" ", m, "grinds", x["grinds"], "wall", x["wall"], "min80", x["min80"], "boss80", x["boss80"], "6060", x["boss6060"], "cash", x["cash"])
    print("  at cap", r["at_cap"], "grind10 min 80/80", r["g10"], "60/60", r["g10_6060"])
    for p, a in r["arc"].items(): print("  arc", p, a)
