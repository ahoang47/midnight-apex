"""v2.json -> tables_v2.md (every v2 cell, grouped)."""
import json, os
H = os.path.dirname(os.path.abspath(__file__)); rows = json.load(open(os.path.join(H, "v2.json")))
NAME = {"street": "Street", "wangan": "Wangan", "touge": "Touge"}
out = ["# ai-heat-qte-v1 v2 cells (player win %, ties half; n = 6,000 each)", "",
       "| group | race | r | AI QTE (mean / sd / clamp) | lever | 60/60 | 80/80 |", "|---|---|---|---|---|---|---|"]
seen = []
for x in rows:
    lever = (f"kappa x{x['kappa_mult']}" if "kappa_mult" in x else "") + (f"boss tune POW/HAN/EN {x['boss_shape']}" if "boss_shape" in x else "")
    k = (x["tag"], x["mode"], x["d"], x["r"], x["mean"], x["sd"], lever)
    if k in seen: continue
    seen.append(k)
    g = {y["prof"]: y["win"] for y in rows if (y["tag"], y["mode"], y["d"], y["r"], y["mean"], y["sd"],
         (f"kappa x{y['kappa_mult']}" if "kappa_mult" in y else "") + (f"boss tune POW/HAN/EN {y['boss_shape']}" if "boss_shape" in y else "")) == k}
    race = f"{NAME[x['d']]} boss, 30 turns" if x["mode"] == "boss" else "Touge test race mirror, 10 turns"
    out.append(f"| {x['tag']} | {race} | {x['r']} | {x['mean']:.2f} / {x['sd']:.2f} / {x['lo']:.2f}-{x['hi']:.2f} | {lever or '-'} | {g['60/60']:.1f} | {g['80/80']:.1f} |")
open(os.path.join(H, "tables_v2.md"), "w").write("\n".join(out) + "\n"); print("\n".join(out))
