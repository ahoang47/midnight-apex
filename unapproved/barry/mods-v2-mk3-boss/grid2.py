import mk3boss as M, itertools, json, sys
from velocity_shift import equations as E
LIVE = E.STORY_XP_MULT
F2R = dict(R1=range(1, 7), R2=range(15, 23), R3=range(33, 41))
F1L = dict(R1=6, R2=22, R3=40)
out = []
for rid in ("R1", "R2", "R3"):
    i = int(rid[1]) - 1
    for n, where, m2, s, f2 in itertools.product((1, 2), ("oh1", "oh2", "boss"), (0.0, 0.3, 0.6, 1.0), (0.8, 0.9, 1.0), F2R[rid]):
        mult = [list(r) for r in LIVE]; mult[i] = [round(s * LIVE[i][k], 3) for k in range(7)]; mult[i][5] = round(s * m2, 3)
        fills = {(rid, "MK2"): f2, (rid, "MK1"): min(F1L[rid], f2 - 2)}
        prices = {("R1", "MK3"): 600, ("R2", "MK3"): 1500, ("R3", "MK3"): 3000}
        with M.patched(M.make_sets(fills, prices), tuple(tuple(r) for r in mult)):
            res, o = M.summary(n, where)
        s_ = o["story"]; rows = res["story"][0][i]["rows"]
        mk3_pre = sum(1 for r in rows[:-1] for m in r["equipped"] if m.endswith("MK3") and m.startswith(rid))
        out.append(dict(rid=rid, n=n, where=where, m2=m2, s=s, f2=f2, bossL=s_["boss"][i][0], w=s_["boss"][i][1], no=s_["boss"][i][2],
                        mk3=s_["boss"][i][3], min80=s_["min80"][i], mk3_pre=mk3_pre, rows=[(r["rung"], r["arrive_L"], r["wr"]["c8080"]) for r in rows],
                        mixed=o["mixed"]["split"][i], hard=o["hard"]["split"][i], hcap=o["hard"]["boss"][i][1], mcap=o["mixed"]["boss"][i][1]))
json.dump(out, open("../unapproved/barry/mods-v2-mk3-boss/grid2.json", "w"))
for rid in ("R1", "R2", "R3"):
    for n in (1, 2):
        ok = [x for x in out if x["rid"] == rid and x["n"] == n and x["min80"] >= 50 and x["w"] >= 50 and x["no"] <= 45]
        ok.sort(key=lambda x: (x["mk3_pre"], -(x["w"] - x["no"]), -x["s"]))
        print(rid, n, len(ok))
        for x in ok[:6]: print("  ", {k: x[k] for k in ("where", "m2", "s", "f2", "bossL", "w", "no", "mk3", "min80", "mk3_pre", "mixed", "hard", "hcap", "mcap")})
