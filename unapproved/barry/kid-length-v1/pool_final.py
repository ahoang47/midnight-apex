"""Pokémon-style finite pool: candidate checks (run like kidlen.py)."""
import json, itertools
import pool as Q
from velocity_shift import equations as E
CANDS = {"A: 6/round (1 at open + 1 after kid1..oh1), XP x2.5, purse x2": ((1, 1, 1, 1, 1, 1, 0), 2.5, 2.0),
         "A5: 5/round, XP x2.5, purse x2": ((1, 1, 1, 1, 1, 0, 0), 2.5, 2.0),
         "B: 6/round front (2 open + 1 after kid1..mat2), XP x2.25, purse x2": ((2, 1, 1, 1, 1, 0, 0), 2.25, 2.0)}
out = []
for (n, (lay, px, pay)), fbx, fbp, fl in itertools.product(CANDS.items(), (0.25, 0.5), (0.25, 0.5), (0.2, 0.05)):
    Q.MODE[0] = "clear"; Q.PX[0] = px; Q.PAYX[0] = pay
    r = Q.evaluate(lay, fbx, fbp, floor=fl)
    E.GRIND_TAPER_FLOOR, f0 = fl, E.GRIND_TAPER_FLOOR
    xp_lv = {d: round(px * E.grind_xp(29 - d, 29) / E.xp_to_next(29 - d), 3) for d in (8, 4, 2, 1, 0)}
    E.GRIND_TAPER_FLOOR = f0
    x = dict(cand=n, fb_xp=fbx, fb_pay=fbp, floor=fl, pool_xp_levels_by_d=xp_lv, **{k: r[k] for k in ("c6080", "c8060", "mixed", "c6060", "story8080")})
    out.append(x)
    print(n, "fb", fbx, fbp, "floor", fl, "| 6080", x["c6080"]["total"], "bossL", x["c6080"]["boss_L"], "boss", x["c6080"]["boss_own"], "min", x["c6080"]["min_own"],
          "| 8060", x["c8060"]["total"], x["c8060"]["boss_L"], x["c8060"]["boss_own"], x["c8060"]["min_own"], "| mixed", x["mixed"]["total"], x["mixed"]["min_own"],
          "| 6060", x["c6060"]["total"], "fb", x["c6060"]["fb"], x["c6060"]["boss_own"], x["c6060"]["cap_reached"], "cash", x["c6060"]["cash"], "| story", x["story8080"]["min"], "| xp", xp_lv)
json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=0)
