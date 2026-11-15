"""kid-length-v1 (draft, Barry 2026-11-14): kid story races (kid1/kid2, R1-R3) 10 -> 20 turns; grinds stay 10.
Base = live mods-v1 + xp-carry-v1 fix C (carry, catch-up XP 0.75, R2 boss XP x1.5). In memory only. Run from sim/:
PYTHONPATH=.:../unapproved/barry/kid-length-v1:../unapproved/barry/xp-carry-v1:../unapproved/barry/mods-v1:../unapproved/barry/skill-points-v1 python3 ../unapproved/barry/kid-length-v1/kidlen.py"""
import json, os, sys
import carry as C, catchup as K, verify_live as V
from velocity_shift import equations as E, progression as P
HERE = os.path.dirname(os.path.abspath(__file__))
def mult_b2(b2):
    m = [list(r) for r in E.STORY_XP_MULT]; m[1][6] = b2; return tuple(tuple(r) for r in m)
FIXC = dict(story_xp=K.make(0.75), STORY_XP_MULT=mult_b2(1.5))
def turns(t1, t2): return (t1, t2) + E.LADDER_TURNS[2:]
def tr(**d):  # d: {"street":(kid1,kid2)...} absolute target r overrides
    t = {k: list(v) for k, v in E.LADDER_TARGET_R.items()}
    for k, (a, b) in d.items(): t[k][0], t[k][1] = a, b
    return {k: tuple(v) for k, v in t.items()}
def evaluate(patch, arc=True):
    with C.patched(**patch):
        o = C.summary(True)
        caps = P.boss_check_at_cap()
        res = dict(at_cap=[(c["c6060"], c["c8080"]) for c in caps])
        res["kid_at_cap"] = {f"R{x['rnd']} {x['rung']}": {pr: P.hard_win(x["wr"][pr]) for pr in P.PROFILES}
                             for x in P.at_cap_table() if x["rung"] in ("kid1", "kid2")}
        if arc:
            res["arc"] = V.arc_walk({m: (o[m]["out"], o[m]["G"], o[m]["done"]) for m in o})
    s = o["story"]
    res["story_rows"] = [[dict(rung=r["rung"], T=r["turns"], L=r["arrive_L"],
                              **{pr: min(r["wr"][pr]["district"], P.hard_win(r["wr"][pr])) for pr in P.PROFILES}) for r in w["rows"]] for w in s["out"]]
    res["story_min"] = {pr: [min(x[pr] for x in w) for w in res["story_rows"]] for pr in P.PROFILES}
    res["story"] = {k: s[k] for k in ("enter", "endL", "min80", "boss80", "cash", "spent")}
    for m in ("mixed", "hard"):
        x = o[m]; res[m] = dict(grinds=x["grinds"], wall=x["wall"], wall_at=[w["wall"] for w in x["out"]], boss80=x["boss80"], boss6060=x["boss6060"], cash=x["cash"],
            kid_rows=[[ (r["rung"], r["arrive_L"], r["grind_here"], {pr: min(r["wr"][pr]["district"], P.hard_win(r["wr"][pr])) for pr in P.PROFILES}) for r in w["rows"][:2]] for w in x["out"]])
    res["g10_min_story8080"] = min(r["grind10"]["c8080"] for w in s["out"] for r in w["rows"])
    return res
if __name__ == "__main__":
    V_ = {"base: fix C, kid 10/10": dict(FIXC),
          "kid 20/20": dict(FIXC, LADDER_TURNS=turns(20, 20)),
          "kid 20/30": dict(FIXC, LADDER_TURNS=turns(20, 30)),
          "kid 30/30": dict(FIXC, LADDER_TURNS=turns(30, 30))}
    out = {n: evaluate(p) for n, p in V_.items()}
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str)
    for n, r in out.items():
        print("=====", n)
        print(" story", r["story"]); print(" story_min", r["story_min"])
        for i, w in enumerate(r["story_rows"]): print("  R%d" % (i + 1), [(x["rung"], x["T"], x["L"], x["c8080"], x["c6060"]) for x in w])
        for m in ("mixed", "hard"): print(" ", m, {k: v for k, v in r[m].items()})
        print("  at cap", r["at_cap"]); print("  kid at cap", r["kid_at_cap"]); print("  g10 story", r["g10_min_story8080"])
        for p, a in r["arc"].items(): print("  arc", p, a)
