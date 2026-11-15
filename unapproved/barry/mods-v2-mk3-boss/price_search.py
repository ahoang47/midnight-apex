import mk3boss as M, itertools, json
from configs import CONFIGS
res_all = {}
for name, c in CONFIGS.items():
    rows = []
    for p1, p2, p3 in itertools.product((600, 800, 1000), (2000, 2500, 3000, 3500, 4000, 5000), (3000, 4000, 5000, 6000, 8000)):
        prices = {("R1", "MK3"): p1, ("R2", "MK3"): p2, ("R3", "MK3"): p3}
        with M.patched(M.make_sets(c["fills"], prices), c["xp"]):
            res, o = M.summary(c["forced"], c["where"])
        s = o["story"]
        rows.append(dict(p=(p1, p2, p3), boss=[b[1] for b in s["boss"]], no=[b[2] for b in s["boss"]], mk3=[b[3] for b in s["boss"]], min80=s["min80"],
                         cash=s["cash"], hcap=[b[1] for b in o["hard"]["boss"]], mcap=[b[1] for b in o["mixed"]["boss"]]))
    res_all[name] = rows
    best = {}
    for r in rows:
        print(name, r)
json.dump(res_all, open("../unapproved/barry/mods-v2-mk3-boss/price_search.json", "w"))
