"""Criteria per district: live (sim/config/mod_skill_climb_v1.json, n 6,000) vs release 0.5 re-pin (r0.5_final.json)."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
live = json.load(open(os.path.join(H, "..", "..", "..", "sim", "config", "mod_skill_climb_v1.json")))["table"]
new = json.load(open(os.path.join(H, "r0.5_final.json")))["climb"]
R = ["kid1", "kid2", "mat1", "mat2", "oh1", "oh2", "boss"]


def crit(s, w, bwf, bsm):
    st = [round(a - b, 2) for a, b in zip(s, s[1:])]
    v = dict(boss=s[6], min_step=min(st), G2a_boss=w[6], G2a_min=min(w), G3a=round(s[0] - s[6], 2), G3b=round(s[6] - w[6], 2),
             G4a=min(s), G4b=bwf, G5=bsm)
    v["pass"] = dict(G1a=66 <= s[6] <= 68, G3c=min(st) >= 3.0, G2a=min(w) >= 30, G3a=v["G3a"] >= 30, G3b=v["G3b"] >= 10,
                     G4a=min(s) >= 40, G4b=bwf <= 10, G5=bsm <= 95)
    return v


out = {}
for d in ("street", "wangan", "touge"):
    L = live[d]; out[d] = dict(live=crit([L[r]["strong_floor"] for r in R], [L[r]["weak_max"] for r in R], L["boss"]["weak_floor"], L["boss"]["strong_max"]),
                               release05=crit(new[d]["strong_floor"], new[d]["weak_max"], new[d]["boss_weak_floor"], new[d]["boss_strong_max"]))
json.dump(out, open(os.path.join(H, "criteria.json"), "w"), indent=1)
for d, v in out.items():
    for k, c in v.items(): print(d, k, {x: y for x, y in c.items() if x != "pass"}, "FAIL", [x for x, y in c["pass"].items() if not y])
