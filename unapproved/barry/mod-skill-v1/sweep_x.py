"""Sweep the own-stat share X x base option: tune reachability, kit choice and the 80/80 / 60/60 boss cost of a wrong kit."""
import json, os
from mod_skill import *

XS = (0.34, 0.40, 0.50, 0.60, 0.70, 0.80, 1.00)


def kit_mods(kit, earned):
    return [(SI[k], earned) for k in kit]


def boss_wr(district, rnd, pshare):
    r = CAP_POWER[rnd] / E.opponent_budget(rnd, 6)
    return P.boss_check(r, district, max(0.25, min(0.5, pshare)))


def entry_dist(base, X, rnd):
    """Entering round rnd (1, 2) with the previous round's pattern kit at its ceiling, plus the new district's
    pattern: mods the old kit lacks start at 0 (no new XP yet)."""
    old = E.MOD_SLOT_PATTERN[DIST[rnd - 1]]; new = E.MOD_SLOT_PATTERN[DIST[rnd]]
    pool = list(old); mods = []
    for k in new:
        if k in pool:
            pool.remove(k); mods.append((SI[k], CEIL[rnd - 1]))
        else:
            mods.append((SI[k], 0))
    return alloc(BASES[base], mods, X, DIST[rnd])[1]


rows = []
for base in BASES:
    for X in XS:
        row = dict(base=base, X=X, d={})
        for rnd, d in enumerate(DIST):
            res = {k: alloc(BASES[base], kit_mods(k, CEIL[rnd]), X, d) for k in KITS}
            pat = "".join(sorted(E.MOD_SLOT_PATTERN[d], key="PHE".index))
            best = min(res, key=lambda k: res[k][1]); worst = max(res, key=lambda k: res[k][1])
            n_ok = sum(1 for k in res if res[k][1] < 0.5 and res[k][2])
            sh = lambda k: res[k][0][0] / sum(res[k][0])
            # early-round state: the round's kit at half its tier fill above the previous ceiling (mid-round)
            prev = CEIL[rnd - 1] if rnd else 0
            mid = alloc(BASES[base], kit_mods(pat, (prev + CEIL[rnd]) / 2), X, d)[1]
            row["d"][d] = dict(pattern=pat, pattern_dist=round(res[pat][1], 2), pattern_band=res[pat][2],
                               best=best, best_dist=round(res[best][1], 2), worst=worst, worst_dist=round(res[worst][1], 2),
                               kits_on_tune=n_ok, kits=len(KITS), mid_round_dist=round(mid, 2),
                               boss_pattern=boss_wr(d, rnd, sh(pat)), boss_worst=boss_wr(d, rnd, sh(worst)),
                               entry_dist=round(entry_dist(base, X, rnd), 2) if rnd else None)
        rows.append(row)

json.dump(dict(ceil=CEIL, cap_power=CAP_POWER, rows=rows), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sweep_x.json"), "w"), indent=1)
print("ceilings", CEIL, "cap power", CAP_POWER)
for r in rows:
    print(r["base"], r["X"], " | ".join(
        f"{d[:2]} pat {v['pattern_dist']:.1f}{'' if v['pattern_band'] else '!'} mid {v['mid_round_dist']:.1f} ent {v['entry_dist']} worst {v['worst']} {v['worst_dist']:.1f} ok {v['kits_on_tune']}/15 "
        f"b80 {v['boss_pattern']['c8080']}/{v['boss_worst']['c8080']} b60 {v['boss_pattern']['c6060']}/{v['boss_worst']['c6060']}"
        for d, v in r["d"].items()))
