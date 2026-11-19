"""Markdown tables from boss.json / touge.json (and rscan.json if present) -> tables.md"""
import json, os
H = os.path.dirname(os.path.abspath(__file__)); out = []
NAME = {"street": "Street", "wangan": "Wangan", "touge": "Touge"}
def opt_table(rows, key, cols, title):
    out.append(f"### {title}\n")
    out.append("| AI option | " + " | ".join(c[0] for c in cols) + " |"); out.append("|---" * (len(cols) + 1) + "|")
    labels = []
    for x in rows:
        lab = x["opt"] if x["heat"] == "boss_rules" else f"Q100 + AI heat {x['heat']}"
        if lab not in labels: labels.append(lab)
    for lab in labels:
        cells = []
        for _, sel in cols:
            m = [x for x in rows if (x["opt"] if x["heat"] == "boss_rules" else f"Q100 + AI heat {x['heat']}") == lab and sel(x)]
            cells.append(f"{m[0]['win']:.1f}" if m else "")
        out.append(f"| {lab} | " + " | ".join(cells) + " |")
    out.append("")
b = json.load(open(os.path.join(H, "boss.json")))
opt_table(b, "opt", [(f"{NAME[d]} {p}", (lambda d, p: lambda x: x["d"] == d and x["prof"] == p)(d, p)) for d in NAME for p in ("60/60", "80/80")],
          "Boss checks (win %, player side; n = 6,000 per cell, SE <= 0.65 pt)")
t = json.load(open(os.path.join(H, "touge.json")))
opt_table(t, "opt", [(f"{a}-tune vs {o}-tune {p}", (lambda a, o, p: lambda x: x["player"] == a and x["opponent"] == o and x["prof"] == p)(a, o, p))
                     for a, o in (("touge", "touge"), ("touge", "wangan"), ("wangan", "touge")) for p in ("60/60", "80/80")],
          "10-turn Touge test race, parity blocks (win %, player side; n = 6,000 per cell, SE <= 0.65 pt)")
if os.path.exists(os.path.join(H, "rscan.json")):
    out.append("### Boss r scan under the recommended option (win %)\n"); out.append("| option | district | r | 60/60 | 80/80 |"); out.append("|---|---|---|---|---|")
    rs = json.load(open(os.path.join(H, "rscan.json"))); seen = []
    for x in rs:
        k = (x["opt"], x["d"], x["r"])
        if k in seen: continue
        seen.append(k); g = {y["prof"]: y["win"] for y in rs if (y["opt"], y["d"], y["r"]) == k}
        out.append(f"| {k[0]} | {NAME[k[1]]} | {k[2]} | {g.get('60/60', ''):.1f} | {g.get('80/80', ''):.1f} |")
open(os.path.join(H, "tables.md"), "w").write("\n".join(out) + "\n"); print("\n".join(out))
