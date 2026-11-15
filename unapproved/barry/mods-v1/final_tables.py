"""Final pick (Austin 2026-11-14): 4 slots, canon staging (Mk2 after mat1), aspire Mk3 prices. Prints the per-rung money/gear
tables and the unlock/price table from catalog_results.json (run catalog_report.py first)."""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "catalog_results.json")))["final_4"]
C = json.load(open(os.path.join(HERE, "catalog.json")))["final_4"]
WHEN = {"open": "opens"}
def when(u):
    a, b = u
    if a == "open": return f"R{b+1} open" + (" (Prologue race 3 win)" if b == 0 else "")
    if a == "arc": return f"arc: {b} win"
    return f"after R{a+1} {b}"
print("## Unlock and price table (4 slots)\n\n| Unlocks | Mod IDs | Points | List price | Fills gap through |\n|---|---|---|---|---|")
seen = {}
for m in C:
    seen.setdefault((when(m["unlock"]), m["tier"], m["mk"]), []).append(m)
for (w, t, mk), ms in seen.items():
    print(f"| {w} | {', '.join('`'+m['id']+'`' for m in ms)} | {ms[0]['pts']} | ${ms[0]['price']:,.0f} | L{ms[0]['fills_to_L']} |")
for mode, k, lab in (("story", "wr8080_hard", "80/80"), ("mixed", "wr8080_hard", "80/80"), ("hard", "wr6060", "60/60")):
    c = R["campaign"][mode]
    print(f"\n## {mode} walk ({lab} win %, hard cell where it applies)\n\n| Rung | L | Grinds | Fill % | Win % | Cash in | After shop | After race | Debt | Owned | Equipped |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for r in c["rows"]:
        print(f"| R{r['rnd']} {r['rung']} | {r['arrive_L']} | {r['grind_here']}+{r['pre_boss_grind']} | {r['fill']} | {r[k]} | ${r['cash_pre']:,.0f} | ${r['money_before']:,.0f} | ${r['money_after']:,.0f} | ${r['debt']:,.0f} | {r['owned']} | {' '.join(x.replace('MOD_','') for x in r['equipped'])} |")
for pr in ("c8080", "c6060"):
    a = R["arc"][pr]
    print(f"\n## arc {pr} (cash before each race, after shopping)\n\n| Race | L | Fill % | Cash | Owned | Equipped |\n|---|---|---|---|---|---|")
    for r in a["log"]:
        print(f"| {r['id']} | {r['L']} | {r['fill']} | ${r['money_before']:,.0f} | {r['owned']} | {' '.join(x.replace('MOD_','') for x in r['equipped'])} |")
