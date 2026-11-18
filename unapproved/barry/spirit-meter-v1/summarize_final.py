"""Tables for RESULTS.md from final.json (+ the mod-skill-v1 table values for the criteria). -> final_tables.md"""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(H, "final.json"))); SPN = list(D["spirits"])
TAB = {"c6060": [31.6, 39.5, 30.3], "c8080": [94.9, 90.6, 92.9]}   # mod-skill-v1 RESULTS.md table 2 (recommended, at cap)
rows = D["rows"]; by = {}
for r in rows: by[(r["mode"], r["rnd"], r["j"], r["prof"])] = r
L = []
P = lambda *a: L.append(" ".join(str(x) for x in a))
DN = {1: "Street", 2: "Wangan", 3: "Touge"}; RN = ["kid1", "kid2", "mat1", "mat2", "oh1", "oh2", "boss"]
P("### Bosses at the mod_skill cap (hardest track, 30 turns, N = %d per cell, paired seeds)" % by[("cap", 1, 6, "c6060")]["n"])
P("| Setting | " + " | ".join(f"{DN[i]} 60/60" for i in (1, 2, 3)) + " | " + " | ".join(f"{DN[i]} 80/80" for i in (1, 2, 3)) + " | criteria (table + delta) |")
P("|---" * 8 + "|")
cells = lambda nm: [(by[("cap", i, 6, p)], p, i) for p in ("c6060", "c8080") for i in (1, 2, 3)]
P("| no spirit (measured) | " + " | ".join("%.1f ±%.1f" % (r["base"], r["se_base"]) for r, _, _ in cells(None)) + " | table: 31.6/39.5/30.3, 94.9/90.6/92.9 |")
for nm in SPN:
    s = []; ok = True; brk = []
    for r, p, i in cells(nm):
        x = r["sp"][nm]; s.append("%+.1f ±%.1f" % (x["delta"], x["se_delta"]))
        v = TAB[p][i - 1] + x["delta"]
        if p == "c6060" and v < 30: ok = False; brk.append(f"{DN[i]} 60/60 {v:.1f}")
        if p == "c8080" and not (90 <= v <= 95): ok = False; brk.append(f"{DN[i]} 80/80 {v:.1f}")
    P(f"| {nm} | " + " | ".join(s) + " | " + ("pass" if ok else "breaks: " + ", ".join(brk)) + " |")
for mode, title in (("story", "Story-only walk (no grinds)"), ("mixed", "Mixed walk (grinds to the targets)")):
    P(f"\n### {title}: 21 races, mean change and lows (pp)")
    P("| Setting | mean Δ 60/60 | mean Δ 80/80 | mean Δ curve | 80/80 low (race) | curve low (race) | boss gap 80/80−60/60 Δ | activations 10/20/30-turn (80/80) |")
    P("|---" * 8 + "|")
    ks = sorted({(k[1], k[2]) for k in by if k[0] == mode})
    def low(p, nm):
        v = [(by[(mode, a, j, p)]["base"] + (by[(mode, a, j, p)]["sp"][nm]["delta"] if nm else 0), a, j) for a, j in ks]
        m = min(v); return "%.1f (%s %s)" % (m[0], DN[m[1]], RN[m[2]])
    gap0 = sum(by[(mode, a, 6, "c8080")]["base"] - by[(mode, a, 6, "c6060")]["base"] for a in (1, 2, 3)) / 3
    P(f"| no spirit | – | – | – | {low('c8080', None)} | {low('curve', None)} | gap {gap0:.1f} | – |")
    for nm in SPN:
        md = {p: sum(by[(mode, a, j, p)]["sp"][nm]["delta"] for a, j in ks) / len(ks) for p in ("c6060", "c8080", "curve")}
        g = sum(by[(mode, a, 6, "c8080")]["sp"][nm]["delta"] - by[(mode, a, 6, "c6060")]["sp"][nm]["delta"] for a in (1, 2, 3)) / 3
        ac = {}
        for a, j in ks: r = by[(mode, a, j, "c8080")]; ac.setdefault(r["T"], []).append(r["sp"][nm]["acts"])
        acs = "/".join("%.2f" % (sum(v) / len(v)) for _, v in sorted(ac.items()))
        P(f"| {nm} | {md['c6060']:+.1f} | {md['c8080']:+.1f} | {md['curve']:+.1f} | {low('c8080', nm)} | {low('curve', nm)} | {g:+.1f} | {acs} |")
# value per activation: delta / activations on the bosses at cap and the story walk
P("\n### Win points per activation (Δ / mean activations)")
P("| Setting | cap bosses 60/60 | cap bosses 80/80 | story 60/60 | story 80/80 | story curve |")
P("|---" * 6 + "|")
for nm in SPN:
    out = []
    for mode, prof in (("cap", "c6060"), ("cap", "c8080"), ("story", "c6060"), ("story", "c8080"), ("story", "curve")):
        rs = [r for k, r in by.items() if k[0] == mode and k[3] == prof]
        d = sum(r["sp"][nm]["delta"] for r in rs); a = sum(r["sp"][nm]["acts"] for r in rs)
        out.append("%.1f" % (d / a) if a else "–")
    P(f"| {nm} | " + " | ".join(out) + " |")
open(os.path.join(H, "final_tables.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
