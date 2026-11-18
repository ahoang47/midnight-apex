import json, os, sys
D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stage2.json")))
rows = D["rows"]; SPN = list(D["spirits"])
def key(r): return (r["mode"], r["rnd"], r["j"])
by = {}
for r in rows: by.setdefault(r["prof"], {})[key(r)] = r
# sanity: measured base vs the walk's table value
dif = [abs(r["base"] - r["walk_wr"][r["prof"]]) for r in rows if r["prof"] != "curve"]
print("base vs walk table: mean |diff| %.2f, max %.2f pp (n=%d)" % (sum(dif) / len(dif), max(dif), len(dif)))
for mode in ("story", "mixed"):
    print("\n==", mode)
    print("%-16s" % "spirit" + "".join("%11s" % h for h in ["d8080", "d6060", "dcurve", "acts10/20/30(c80)", "", "low8080", "lowCurve", "bossGap+"]))
    ks = sorted(k for k in by["c8080"] if k[0] == mode)
    def lo(prof, nm):
        v = [(by[prof][k]["base"] + (by[prof][k]["sp"][nm]["delta"] if nm else 0), k) for k in ks]; return min(v)
    b80, bc = lo("c8080", None), lo("curve", None)
    print("%-16s" % "no spirit" + " " * 33 + " " * 22 + "%7.1f %-3s %7.1f %-3s" % (b80[0], "R%d%s" % (b80[1][1], b80[1][2]), bc[0], "R%d%s" % (bc[1][1], bc[1][2])))
    for nm in SPN:
        m = {p: sum(by[p][k]["sp"][nm]["delta"] for k in ks) / len(ks) for p in ("c8080", "c6060", "curve")}
        acts = {}
        for k in ks:
            r = by["c8080"][k]; acts.setdefault(r["T"], []).append(r["sp"][nm]["acts"])
        a = "/".join("%.2f" % (sum(v) / len(v)) for T, v in sorted(acts.items()))
        bosses = [k for k in ks if k[2] == 6]
        gap = sum(by["c8080"][k]["sp"][nm]["delta"] - by["c6060"][k]["sp"][nm]["delta"] for k in bosses) / 3
        l80, lc = lo("c8080", nm), lo("curve", nm)
        print("%-16s%9.1f %9.1f %9.1f   %-20s %7.1f %-3s %7.1f %-3s %+6.1f" % (nm, m["c8080"], m["c6060"], m["curve"], a, l80[0], "R%d%s" % (l80[1][1], l80[1][2]), lc[0], "R%d%s" % (lc[1][1], lc[1][2]), gap))
