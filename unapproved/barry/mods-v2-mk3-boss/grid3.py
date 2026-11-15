"""Lever search per round: mandatory grinds n and where, story XP (oh1 mult m1, oh2 mult m2, round scale s), Mk2/Mk1 fills."""
import mk3boss as M, itertools, json
from velocity_shift import equations as E
LIVE = E.STORY_XP_MULT
F2R = dict(R1=range(1, 6), R2=range(15, 23), R3=range(32, 40))
out = []
for rid in ("R1", "R2", "R3"):
    i = int(rid[1]) - 1
    for n, where, m1, m2, s, f2, k in itertools.product((1, 2), ("mat2", "oh1", "oh2", "boss"), (0.4, 0.7, 1.0), (0.0, 0.3, 0.6, 1.0), (0.9, 1.0), F2R[rid], (2, 4)):
        base = [0.9] * 7 if i == 0 else [1.0] * 7
        mult = [list(r) for r in LIVE]; row = [s * b for b in base]; row[4] = s * m1 * base[4]; row[5] = s * m2 * base[5]
        mult[i] = [round(v, 3) for v in row]
        fills = {(rid, "MK2"): f2, (rid, "MK1"): max(0, f2 - k) if i == 0 else max(dict(R2=12, R3=29)[rid], f2 - k)}
        prices = {("R1", "MK3"): 600, ("R2", "MK3"): 1500, ("R3", "MK3"): 3000}
        with M.patched(M.make_sets(fills, prices), tuple(tuple(r) for r in mult)):
            res, o = M.summary(n, where)
        rows = res["story"][0][i]["rows"]; b = rows[-1]
        out.append(dict(rid=rid, n=n, where=where, m1=m1, m2=m2, s=s, f2=f2, f1=fills[(rid, "MK1")], bossL=b["arrive_L"], w=b["wr"]["c8080"], no=b["no_mk3"]["c8080"],
                        min80=min(r["wr"]["c8080"] for r in rows), pre_no_min=min(r["no_mk3"]["c8080"] for r in rows[:-1]),
                        rows=[(r["rung"], r["arrive_L"], r["wr"]["c8080"], r["no_mk3"]["c8080"]) for r in rows],
                        mixed=o["mixed"]["split"][i], mixed_tot=o["mixed"]["grinds"][i], hard=o["hard"]["split"][i], hcap=o["hard"]["boss"][i][1], mcap=o["mixed"]["boss"][i][1],
                        g10=min(r["grind10"]["c8080"] for r in rows)))
json.dump(out, open("../unapproved/barry/mods-v2-mk3-boss/grid3.json", "w"))
