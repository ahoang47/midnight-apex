"""Emit the markdown tables used in RESULTS.md from results.json / sweep_x.json / sweep_fine.json (tables.md)."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(H, "results.json"))); S = json.load(open(os.path.join(H, "sweep_x.json"))); F = json.load(open(os.path.join(H, "sweep_fine.json")))
L = []; w = L.append
rec = R["configs"]["recommended"]
for mode in ("story", "mixed", "hard"):
    w(f"\n#### {mode} ({'80/80 criterion, never grinds' if mode == 'story' else 'grinds when 60/80 or 80/60 < 50 %, then to cap before the boss' if mode == 'mixed' else 'grinds when 60/60 < 50 %, then to cap before the boss'})\n")
    w("| Round | Rung | Grinds before | Car points | r | 60/60 | 60/80 | 80/60 | 80/80 | Cash before | Debt before | Tiers (kit) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for rd in rec["runs"][mode]:
        for x in rd["rows"]:
            wr = x["wr"]
            w(f"| R{rd['rnd']} {rd['district']} | {x['rung']} | {x['grind']} | {x['points']} | {x['r']:.3f} | {wr['c6060']} | {wr['c6080']} | {wr['c8060']} | {wr['c8080']} | ${x['cash_before']:,} | ${x['debt_before']:,} | {x['tiers']} |")
    w("")
    w("| Round | Grinds | End points | End cash | Debt left | Spent on mods | XP lost past ceilings |")
    w("|---|---|---|---|---|---|---|")
    for rd in rec["runs"][mode]:
        w(f"| R{rd['rnd']} | {rd['total_grind']} | {rd['end_points']} | ${rd['money']:,} | ${rd['debt']:,} | ${rd['spent']:,} | {rd['xp_lost']} |")
# side by side
w("\n#### Side by side with live\n")
w("| Metric | Live (rerun today) | mod_skill recommended | strict (1 mod, pattern kits) |")
w("|---|---|---|---|")
lv = R["live"]; rs = rec["summary"]; st = R["configs"]["strict"]["summary"]; cap = R["live_boss_at_cap"]
f3 = lambda xs: " / ".join(str(x) for x in xs)
w(f"| Story-only 80/80 low | {f3([r['low8080'] for r in lv['story']])} | {f3([r['low8080'] for r in rs['story']])} | {f3([r['low8080'] for r in st['story']])} |")
w(f"| Story-only boss 80/80 | {f3([r['boss8080'] for r in lv['story']])} | {f3([r['boss8080'] for r in rs['story']])} | {f3([r['boss8080'] for r in st['story']])} |")
w(f"| 60/60 boss at cap | {f3([c['c6060'] for c in cap])} | {f3([r['boss6060'] for r in rs['mixed']])} | {f3([r['boss6060'] for r in st['mixed']])} |")
w(f"| 80/80 boss at cap | {f3([c['c8080'] for c in cap])} | {f3([r['boss8080'] for r in rs['mixed']])} | {f3([r['boss8080'] for r in st['mixed']])} |")
w(f"| Mixed grinds | {f3([r['grind'] for r in lv['mixed']])} | {f3([r['grind'] for r in rs['mixed']])} | {f3([r['grind'] for r in st['mixed']])} |")
w(f"| Hard grinds | {f3([r['grind'] for r in lv['hard']])} | {f3([r['grind'] for r in rs['hard']])} | {f3([r['grind'] for r in st['hard']])} |")
w(f"| Story-only cash at round end | {f3(['$%s' % format(r['cash'], ',') for r in lv['story']])} | {f3(['$%s' % format(r['cash'], ',') for r in rs['story']])} | {f3(['$%s' % format(r['cash'], ',') for r in st['story']])} |")
w(f"| Story-only debt at round end | {f3(['$%s' % format(int(r['debt']), ',') for r in lv['story']])} | {f3(['$%s' % format(r['debt'], ',') for r in rs['story']])} | {f3(['$%s' % format(r['debt'], ',') for r in st['story']])} |")
w("\n#### Variant configs (story low / story boss 80/80; mixed and hard grinds)\n")
w("| Config | Story 80/80 low | Story boss 80/80 | Mixed grinds | Hard grinds | Mixed XP lost |")
w("|---|---|---|---|---|---|")
for k, v in R["configs"].items():
    s = v["summary"]
    w(f"| {k} | {f3([r['low8080'] for r in s['story']])} | {f3([r['boss8080'] for r in s['story']])} | {f3([r['grind'] for r in s['mixed']])} | {f3([r['grind'] for r in s['hard']])} | {f3([r['xp_lost'] for r in s['mixed']])} |")
w("\n#### X sweep (at each round's cap, all 4 mods at the tier ceiling)\n")
w("| Base | X | Street pattern off-tune (pts) | Wangan pattern off-tune | Touge pattern off-tune | Kits on tune S/W/T (of 15) | Round-entry off-tune R2/R3 | Wangan boss 60/60 / 80/80, pattern vs PPPP |")
w("|---|---|---|---|---|---|---|---|")
for r in S["rows"]:
    d = r["d"]
    w(f"| {r['base']} | {r['X']:.2f} | {d['street']['pattern_dist']} | {d['wangan']['pattern_dist']}{'' if d['wangan']['pattern_band'] else ' (outside 25-50 band)'} | {d['touge']['pattern_dist']} | "
      f"{d['street']['kits_on_tune']}/{d['wangan']['kits_on_tune']}/{d['touge']['kits_on_tune']} | {d['wangan']['entry_dist']} / {d['touge']['entry_dist']} | "
      f"{d['wangan']['boss_pattern']['c6060']} / {d['wangan']['boss_pattern']['c8080']} vs {d['wangan']['boss_worst']['c6060']} / {d['wangan']['boss_worst']['c8080']} |")
w("\n#### Fine sweep, B3 setup base\n")
w("| X | Kits on tune Street | Wangan | Touge | Kits on tune in BOTH Street and Wangan |")
w("|---|---|---|---|---|")
for r in F["rows"]:
    w(f"| {r['X']:.2f} | {r['street']} | {r['wangan']} | {r['touge']} | {r['shared_sw']} |")
w("\n#### Price sweep (recommended config, XP fixed; story-only 80/80 low/boss and rungs raced on a lagging tier)\n")
w("| Prices R1/R2/R3 per tier | Story R1 low/boss | Story R2 low/boss | Story R3 low/boss | Story rungs on old tier R1/R2/R3 | Mixed grinds | Hard grinds |")
w("|---|---|---|---|---|---|---|")
for k, v in R["price_sweep"].items():
    s = v["summary"]; p = v["prices"]
    w(f"| {k} (${p[0]:,.0f} / ${p[1]:,.0f} / ${p[2]:,.0f}) | " + " | ".join(f"{r['low8080']} / {r['boss8080']}" for r in s["story"]) +
      f" | {f3([len(r['tier_lag_rungs']) for r in s['story']])} | {f3([r['grind'] for r in s['mixed']])} | {f3([r['grind'] for r in s['hard']])} |")
open(os.path.join(H, "tables.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
