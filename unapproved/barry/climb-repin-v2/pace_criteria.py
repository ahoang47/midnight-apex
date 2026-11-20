"""Criteria table for the AI-pacing re-pins vs the no-pacing ones (targets from equations.MS_TARGETS, band 66-68 per Austin)."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
F = {"lockcap": "repin_final.json", "lockcap+pace": "pace_lc_final.json", "fo0.5": "fo0.5_final.json", "fo0.5+pace": "pace_fo0.5_final.json",
     "fo0.7": "fo0.7_final.json", "fo0.7+pace": "pace_fo0.7_final.json"}
out = {}
for k, f in F.items():
    d = json.load(open(os.path.join(H, f)))["climb"]
    for m in ("street", "wangan", "touge"):
        c = d[m]; s = c["strong_floor"]; w = c["weak_max"]; st = [round(a - b, 2) for a, b in zip(s, s[1:])]
        r = dict(boss_budget=c["budgets"][6], boss_strong_floor=s[6], min_step=min(st), boss_weak_max=w[6], oh2_weak_max=w[5],
                 min_weak_max=min(w), G5=c["boss_strong_max"], gap=round(s[6] - w[6], 2), drop=round(s[0] - s[6], 2),
                 lowest=min(s), boss_weak_floor=c["boss_weak_floor"])
        r["pass"] = dict(G1a=66 <= s[6] <= 68, G3c=min(st) >= 3.0, G2a=min(w) >= 30, G3a=r["drop"] >= 30, G3b=r["gap"] >= 10,
                         G4a=min(s) >= 40, G4b=c["boss_weak_floor"] <= 10, G5=c["boss_strong_max"] <= 95)
        out.setdefault(k, {})[m] = r
json.dump(out, open(os.path.join(H, "pace_criteria.json"), "w"), indent=1)
for k, v in out.items():
    for m, r in v.items():
        print(k, m, {x: y for x, y in r.items() if x != "pass"}, "FAIL:", [x for x, y in r["pass"].items() if not y])
