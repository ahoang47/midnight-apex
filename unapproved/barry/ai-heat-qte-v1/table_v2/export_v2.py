"""sweep_v2.json -> sim/config/winrate_g2_live_tracks_v2.json (same layout as v1, plus "q_boss" for the Street boss shape).
Exact-r point checks (pt_q / pt_q_boss) add or override that r in the grid, as v1's point checks did."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
import sys; sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "sim")))
from velocity_shift import equations as E
S = json.load(open(os.path.join(HERE, "sweep_v2.json")))
q, qb = {}, {}
for c in S["cells"]:
    kind = c["kind"].replace("pt_", "")
    tgt = (q if kind == "q" else qb).setdefault(c["profile"], {}).setdefault(str(c["turns"]), {}).setdefault(c["track"], {})
    for r, v in c["pts"]:
        if c["kind"].startswith("pt_") or round(r, 6) not in tgt:
            tgt[round(r, 6)] = v
fix = lambda D: {pr: {T: {t: [[r, v] for r, v in sorted(pts.items())] for t, pts in byT.items()} for T, byT in byL.items()} for pr, byL in D.items()}
out = dict(_comment=("Live engine (G2 heat, live QTE mapping, AI QTE seeded per turn N(0.80, 0.08) clamped 0.60-1.00, "
                     "Austin 2026-11-19), live stand-in tracks config/tracks_v1.json. Win % (ties half), mean of 3 boss styles. "
                     "Built by unapproved/barry/ai-heat-qte-v1/table_v2/sweep_v2.py + export_v2.py (same method as v1): "
                     f"N={S['n']}/track/style r 0.94-1.24 step 0.01 (10/20/30 turns), opponent even split; q_boss = Street "
                     f"30-turn cells vs the Street boss shape POW/HAN/EN {S['boss_shape_street']}; exact-r point checks "
                     f"N={S['np']}/style at each boss r on its hardest track. Linear interpolation in r, flat outside."),
           tracks=S["tracks"], tunes={d: list(v) for d, v in E.DISTRICT_TUNE.items()},
           profiles={"c6060": [0.6, 0.6, 0.6], "c6080": [0.6, 0.8, 0.8], "c8060": [0.8, 0.6, 0.6], "c8080": [0.8, 0.8, 0.8]},
           boss_shares={d: list(v) for d, v in E.BOSS_STAT_SHARES.items()}, q=fix(q), q_boss=fix(qb))
path = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "sim", "config", "winrate_g2_live_tracks_v2.json"))
json.dump(out, open(path, "w"), separators=(",", ":"))
print(path, os.path.getsize(path))
