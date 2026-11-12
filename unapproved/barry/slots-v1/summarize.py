"""Print the compact tables used in RESULTS.md from the json outputs (no new runs)."""
import json, collections
d = json.load(open("results.json")); z = json.load(open("results_sizes.json")); g = json.load(open("results_grind.json")); c = json.load(open("results_cap.json"))
AB = {"dominant": "D", "dominated": "X", "even": "=", "lean+": "+", "lean-": "-"}
SEL = [("kid #1 at target", lambda t: t["crew"] != "Finale" and t["j"] == 0 and t["kind"] == "target"),
       ("mature #2 skipped", lambda t: t["crew"] != "Finale" and t["j"] == 3 and t["kind"] == "skip"),
       ("boss skipped", lambda t: t["crew"] != "Finale" and t["j"] == 6 and t["kind"] == "skip"),
       ("boss at target", lambda t: t["crew"] != "Finale" and t["j"] == 6 and t["kind"] == "target"),
       ("Myth #2 skipped", lambda t: t["rung"] == "Myth #2" and t["kind"] == "skip"),
       ("Summit skipped", lambda t: t["rung"] == "Summit" and t["kind"] == "skip")]
print("## sizes: mean paired delta range across crews + verdict counts (one window mod)")
for sc in "ABC":
    for nm, f in SEL:
        for p in ("weak", "average", "strong"):
            line = f"{sc} | {nm} | {p}"
            for w in z["sizes"]:
                xs = [t for t in z["trades"][sc] if f(t) and t["profile"] == p and t["size"] == w]
                cc = collections.Counter(AB[t["verdict"]] for t in xs)
                line += f" | {min(t['delta_mean'] for t in xs):+.1f}..{max(t['delta_mean'] for t in xs):+.1f} {''.join(k + str(v) for k, v in sorted(cc.items()))}"
            print(line)
print("## base mids (all-stat) and one-slot dr")
for sc in "ABC":
    for nm, f in SEL:
        for p in ("weak", "average", "strong"):
            xs = [t for t in z["trades"][sc] if f(t) and t["profile"] == p and t["size"] == 0.1]
            print(sc, nm, p, f"{min(t['base_mid'] for t in xs):.1f}-{max(t['base_mid'] for t in xs):.1f}", "dr", min(t["dr"] for t in xs), max(t["dr"] for t in xs))
print("## break-even w*")
for sc in "ABC":
    for cell in ("mature #2 skipped", "boss skipped", "boss at target", "Myth #2 skipped", "Summit skipped"):
        xs = [b for b in d["break_even"][sc] if b["cell"] == cell]
        out = {}
        for p in ("weak", "average", "strong"):
            v = [b["w_star"][p] for b in xs]; num = [x for x in v if not isinstance(x, str)]
            out[p] = (f"{min(num):.2f}-{max(num):.2f}" if num else "") + (" (some >3.00)" if len(num) < len(v) else "")
        print(sc, cell, out)
print("## grind"); [print(k, v) for k, v in g.items()]
print("## feel")
for sc in "ABC":
    f = d["feel"][sc]; print(sc, {k: v for k, v in f.items() if k not in ("no_tier_wins",)})
print("## C +75% cap vs nocap")
for lab in ("nocap", "cap1.15"):
    print(lab, c[lab]["grind"])
    for nm, f in SEL:
        for p in ("weak", "average", "strong"):
            xs = [t for t in c[lab]["trades"] if f(t) and t["profile"] == p]
            cc = collections.Counter(AB[t["verdict"]] for t in xs)
            print(f"  {nm} | {p} | base {min(t['base_mid'] for t in xs):.1f}-{max(t['base_mid'] for t in xs):.1f} | win {min(t['mid'] for t in xs):.1f}-{max(t['mid'] for t in xs):.1f} | {min(t['delta_mean'] for t in xs):+.1f}..{max(t['delta_mean'] for t in xs):+.1f} {''.join(k + str(v) for k, v in sorted(cc.items()))}")
    allc = collections.Counter((t["profile"], t["verdict"]) for t in c[lab]["trades"] if t["crew"] != "Finale")
    print("  campaign rungs (63 x target/skip):", dict(sorted(allc.items())))
