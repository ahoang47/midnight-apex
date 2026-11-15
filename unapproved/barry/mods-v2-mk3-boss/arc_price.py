import itertools, mk3boss as M, verify_live as V, json
from configs import CONFIGS
out = []
for n, c in CONFIGS.items():
    for p2, p3 in itertools.product((2000, 2500, 3000, 3500, 4000), (3000, 4000, 5000, 6000)):
        pr = {("R1", "MK3"): 1000, ("R2", "MK3"): p2, ("R3", "MK3"): p3}
        with M.patched(M.make_sets(c["fills"], pr), c["xp"]):
            res = {m: M.run(m, c["forced"], c["where"]) for m in ("story", "mixed", "hard")}
            a = V.arc_walk(res)
        st = res["story"][0]
        x = dict(cfg=n, p2=p2, p3=p3, boss=[w["rows"][-1]["wr"]["c8080"] for w in st], min80=[min(r["wr"]["c8080"] for r in w["rows"]) for w in st],
                 cash=[round(w["money"]) for w in st], fin80=a["c8080"]["finale"], arcmin80=a["c8080"]["min_story"], arc_end=a["c8080"]["end_money"],
                 fin6060=a["c6060"]["finale"], grind6060=a["c6060"]["grind"])
        out.append(x); print(x)
json.dump(out, open("../unapproved/barry/mods-v2-mk3-boss/arc_price.json", "w"))
