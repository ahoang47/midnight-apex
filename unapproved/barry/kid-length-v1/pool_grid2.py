"""Grid for the finite-pool design: pool XP x PX, purse x PAYX, pool size/layout, taper floor; fallback 0.25 XP / 0.25 purse."""
import itertools, json
import pool as Q
LAYOUTS = {}
for n in (4, 5, 6, 7):
    ev = [0] * 7
    for i in range(n): ev[i % 6] += 1           # spread over open..oh2 (before kid1 .. before oh2)
    LAYOUTS[f"{n} even"] = tuple(ev)
    fr = [0] * 7; fr[0] = 2
    for i in range(n - 2): fr[1 + i % 5] += 1   # 2 at open, then 1 per rung
    LAYOUTS[f"{n} front"] = tuple(fr)
out = []
for (ln, lay), px, pay, fl in itertools.product(LAYOUTS.items(), (1.75, 2.0, 2.25, 2.5), (1.0, 2.0), (0.2, 0.05)):
    Q.MODE[0] = "clear"; Q.PX[0] = px; Q.PAYX[0] = pay
    r = Q.evaluate(lay, 0.25, 0.25, floor=fl)
    x = dict(layout=ln, pool=lay, px=px, pay=pay, floor=fl, **{k: r[k] for k in ("c6080", "c8060", "mixed", "c6060", "story8080")})
    out.append(x)
json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=0)
def good(x):
    return all(3 <= t <= 6 for k in ("c6080", "c8060") for t in x[k]["total"]) and all(b >= 50 for k in ("c6080", "c8060") for b in x[k]["min_own"]) \
        and all(x["c6060"]["cap_reached"]) and all(b >= 30 for b in x["c6060"]["boss_own"])
G = [x for x in out if good(x)]
print(len(out), "good", len(G))
for x in sorted(G, key=lambda x: (x["px"], x["pay"], sum(x["pool"])))[:30]:
    print(x["layout"], x["px"], x["pay"], x["floor"], "6080", x["c6080"]["total"], x["c6080"]["fb"], x["c6080"]["boss_own"], "8060", x["c8060"]["total"], x["c8060"]["fb"], x["c8060"]["boss_own"],
          "6060", x["c6060"]["total"], x["c6060"]["fb"], x["c6060"]["boss_own"], "cash6060", x["c6060"]["cash"])
