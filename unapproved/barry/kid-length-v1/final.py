"""kid-length-v1 final: 20/20 kid races + fix K (smallest kid opponent-r lift), with grinds held at the live kid1 budget
(GRIND budget decoupled = C_ROUND / live kid1 r). Run like kidlen.py."""
import json
import carry as C, kidlen as KL
from velocity_shift import equations as E, progression as P
LIVE_R = E.LADDER_TARGET_R
FIXK = dict(street=(1.205, 1.159), wangan=(1.185, 1.165), touge=(1.207, 1.188))
ALT_T = dict(street=(1.205, 1.159), wangan=(1.185, 1.165), touge=(1.192, 1.173))
def grind10_live_budget(patch):
    """min grind10 per profile with grinds at the LIVE kid1 budget (walk row power / live grind budget)."""
    with C.patched(**patch):
        o = C.summary(True)
    res = {}
    for m in o:
        mins = {pr: 101 for pr in P.PROFILES}
        for rnd, w in enumerate(o[m]["out"]):
            d = E.ROUND_DISTRICTS[rnd].lower(); Bg = E.C_ROUND[rnd] / LIVE_R[d][0]
            for r in w["rows"]:
                pw = r["arrive_r"] * r["B"]
                for pr in P.PROFILES:
                    mins[pr] = min(mins[pr], round(P.win_rate(pr, pw / Bg, E.GRIND_TURNS, d, pow_share=r["pow_share"] / 100), 1))
        res[m] = mins
    return res
V = {"base (fix C, kid 10/10)": dict(KL.FIXC),
     "kid 20/20, no fix": dict(KL.FIXC, LADDER_TURNS=KL.turns(20, 20)),
     "kid 20/20 + fix K": dict(KL.FIXC, LADDER_TURNS=KL.turns(20, 20), LADDER_TARGET_R=KL.tr(**FIXK)),
     "kid 20/20 + fix K-lite (Touge +0.010)": dict(KL.FIXC, LADDER_TURNS=KL.turns(20, 20), LADDER_TARGET_R=KL.tr(**ALT_T))}
if __name__ == "__main__":
  out = {}
  for n, p in V.items():
      r = KL.evaluate(p); r["grind10_live_budget"] = grind10_live_budget(p); out[n] = r
  json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=1, default=str)
  for n, r in out.items():
      print("=====", n)
      print(" story", r["story"]); print(" story_min", r["story_min"])
      for i, w in enumerate(r["story_rows"]): print("  R%d" % (i + 1), [(x["rung"], x["T"], x["L"], x["c8080"]) for x in w[:2]])
      for m in ("mixed", "hard"): print(" ", m, r[m]["grinds"], r[m]["wall"], r[m]["wall_at"], r[m]["boss80"], r[m]["boss6060"], r[m]["cash"])
      print("  at cap", r["at_cap"]); print("  grind10 live budget", r["grind10_live_budget"])
      for p_, a in r["arc"].items(): print("  arc", p_, a)
