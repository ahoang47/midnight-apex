import itertools, mk3boss as M, verify_live as V, json
from configs import CONFIGS
LIVEP = {("R2", "MK1"): 700, ("R2", "MK2"): 1500, ("R3", "MK1"): 1200, ("R3", "MK2"): 2500}
out = []
for n, c in CONFIGS.items():
    for f, p2, p3 in itertools.product((1.0, 0.8, 0.6), (2000, 2500, 3000, 3500, 4000), (3000, 4000, 5000, 6000)):
        pr = {("R1", "MK3"): 1000, ("R2", "MK3"): p2, ("R3", "MK3"): p3}
        pr.update({k: round(v * f / 100) * 100 for k, v in LIVEP.items()})
        with M.patched(M.make_sets(c["fills"], pr), c["xp"]):
            res = {m: M.run(m, c["forced"], c["where"]) for m in ("story", "mixed", "hard")}
            a = V.arc_walk(res)
        st = res["story"][0]
        x = dict(cfg=n, f=f, p2=p2, p3=p3, mk12={k[0] + k[1]: v for k, v in pr.items() if k[1] != "MK3"},
                 boss=[w["rows"][-1]["wr"]["c8080"] for w in st], min80=[min(r["wr"]["c8080"] for r in w["rows"]) for w in st],
                 cash=[round(w["money"]) for w in st], fin=[a[p]["finale"] for p in ("c8080", "c6080", "c8060", "c6060")],
                 arcmin80=a["c8080"]["min_story"], grinds={p: a[p]["grind"] for p in a})
        out.append(x)
json.dump(out, open("../unapproved/barry/mods-v2-mk3-boss/arc_price2.json", "w"))
LIVEFIN = [81.7, 82.7, 79.3, 81.7]
for x in out:
    if x["fin"][0] == LIVEFIN and min(min(x["min80"]), *x["boss"]) >= 50:
        print({k: x[k] for k in ("cfg", "f", "p2", "p3", "boss", "min80", "cash", "arcmin80")}, x["mk12"])
