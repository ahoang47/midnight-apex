"""Summarise results_fixes.json -> results_fixes_summary.json (no new sim). Per fix x policy x profile: grind total, per-wall
skip-state mids (mature #2 j=3, crew boss j=6), min margin to 50 among walls that force grind, walls cleared with no grind,
'decisive' clears (newest fitted purchase lifts the wall over 50: the V1/V2 rule), mid at the cap where the loadout is below the
schedule, dead wins, unbought tiers, money."""
import json
d = json.load(open("results_fixes.json")); out = {}
for k, v in sorted(d["runs"].items()):
    fix, pol, prof = k.split("|"); rows = [r for r in v["rows"] if r["crew"] not in ("Prologue", "Finale")]
    walls = [r for r in rows if r["j"] in (3, 6)]
    forced = [r for r in walls if r["grind"]]
    s = dict(total=v["total"],
             walls={f"{r['crew']} {'mature #2' if r['j'] == 3 else 'boss'}": dict(mid_skip=r.get("mid_skip"), grind=r["grind"], mid_at_cap=r.get("mid_at_cap"),
                    mods=r.get("total_mods"), sched_mods=r.get("sched_mods"), decisive=r.get("decisive")) for r in walls},
             forced_walls=len(forced),
             min_margin_forced=round(min(50 - r["mid_skip"] for r in forced), 2) if forced else None,
             max_mid_forced=max(r["mid_skip"] for r in forced) if forced else None,
             cleared_no_grind=[f"{r['crew']} j{r['j']} {r['mid_skip']}" for r in walls if not r["grind"]],
             decisive=[f"{r['crew']} j{r['j']} {r['mid_prev_lines']}->{r['mid_skip']}" for r in walls if r.get("decisive")],
             below_sched_at_cap=[f"{r['crew']} j{r['j']} cap-mid {r['mid_at_cap']} mods {r['total_mods_at_cap']}/{r['sched_mods']}"
                                 for r in walls if r.get("mid_at_cap") is not None and r["total_mods_at_cap"] < r["sched_mods"] - 1e-6],
             nonwall_rungs_lacking_mods=sum(1 for r in rows if r.get("total_mods") is not None and r["total_mods"] < r["sched_mods"] - 1e-6))
    out[k] = s
json.dump(out, open("results_fixes_summary.json", "w"), indent=1)
for k, s in out.items():
    print(k, s["total"]["grind_races"], "dead", s["total"]["dead_wins"], "minmargin", s["min_margin_forced"], "decisive", s["decisive"],
          "lacking", s["nonwall_rungs_lacking_mods"], "capshort", len(s["below_sched_at_cap"]), "wallet", s["total"].get("wallet_end"), "unbought", s["total"]["unbought_at_end"])
