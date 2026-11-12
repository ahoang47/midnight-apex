"""b3 feel cost: at every mature #2 (j=3) rung, grind races a player needs from the skip state to reach the b3 level floor (official
grind payout, same as prog.grind_to), and whether the full scheduled loadout at that level clears (pooled mid >= 50). Balanced 2/2/2.
Writes results_floor_cost.json.
Moved from unapproved/barry/slots-v2 when b3 was approved (2026-11-12); study modules are still imported from there."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "unapproved", "barry", "slots-v2"))
import numpy as np
import fixes as F, model as M, prog
M.GRID_DIR = os.environ.get("SLOTS_V2_COUNTS", "/workspace/barry-drafts/slots-v2/counts")

E, P = M.E, M.P
SP, XC, X = P.curves(); Rl = P.ladder()[0]
key = {(s["crew"], s["rung"], s["j"]): s for s in M.S1.schedule("C")}
out = []
for prof in M.PROFILES:
    rows, _ = F.run("b3", "balanced", prof)
    for x, r in zip(Rl, rows):
        if r.get("floor") is None:
            continue
        v, n, cap = r["xp_skip"], 0, x["L"]
        while P._level(XC, v, cap) < r["floor"] and n <= 200:
            Ln = P._level(XC, v, cap) + 1; v = min(v + E.grind_payout_fraction(Ln, x["j"]) * X[Ln], XC[cap]); n += 1
        Lf = P._level(XC, v, cap); lines = np.array(key[(x["crew"], x["rung"], x["j"])]["lines"])
        m, _ = prog.best_mid(SP[Lf], lines, x["B"], "100/0/0", "balanced", False, prof)
        out.append(dict(profile=prof, crew=x["crew"], level_skip=r["level_skip"], floor=r["floor"], races_to_floor=0 if r["level_skip"] >= r["floor"] else n,
                        mid_at_floor_full_mods=round(m, 2), clears_at_floor=bool(m >= E.CLEAR_THRESHOLD), grind_to_cap=r["grind"]))
        print(out[-1], flush=True)
json.dump(out, open("results_floor_cost.json", "w"), indent=0)
