"""Per-round sweep of story-XP multipliers: uniform (all rungs) and targeted (oh2 only, oh1+oh2). Draft."""
import json, camp
out = []
for rnd in range(3):
    for kind, rungs in (("uniform", range(7)), ("oh2", (5,)), ("oh1+oh2", (4, 5))):
        for k in range(0, 41):
            m = round(1.0 - 0.025 * k, 3)
            if kind == "uniform" and m < 0.5: continue
            mult = [[1.0] * 7 for _ in range(3)]
            for j in rungs: mult[rnd][j] = m
            s = camp.summary(camp.run_all(mult))
            st, mx, hd = s["story"][rnd], s["mixed"][rnd], s["hard"][rnd]
            out.append(dict(rnd=rnd + 1, kind=kind, m=m, boss_L=st["boss_L"], boss80=st["boss"]["c8080"], min80=st["min8080"],
                            levels=st["levels"], L_end=st["L_end"], money_story=st["money"],
                            mixed=(mx["wall"], mx["wall_grind"], mx["post"], mx["total"], mx["cap"]),
                            hard=(hd["wall_grind"], hd["post"], hd["total"], hd["cap"], hd["boss"]["c6060"])))
json.dump(out, open("sweep.json", "w"), indent=0)
prev = None
for x in out:
    key = (x["rnd"], x["kind"], x["levels"], x["mixed"], x["hard"])
    if key != prev:
        print(x["rnd"], x["kind"], x["m"], "bossL", x["boss_L"], x["boss80"], "min", x["min80"], x["levels"], "mixed", x["mixed"], "hard", x["hard"])
    prev = key
