import mk3boss as M, itertools
# explore Mk2 fills-through per round with Mk3 prices loose (cheap) to see the power side only
for forced in (1, 2):
    for rid, opts in (("R1", range(3, 9)), ("R2", range(18, 26)), ("R3", range(36, 44))):
        for f2 in opts:
            fills = {(rid, "MK2"): f2, (rid, "MK1"): min(dict(R1=6, R2=22, R3=40)[rid], f2 - 2)}
            prices = {("R1", "MK3"): 600, ("R2", "MK3"): 1500, ("R3", "MK3"): 3000}
            with M.patched(M.make_sets(fills, prices)):
                res, o = M.summary(forced, "boss")
            i = int(rid[1]) - 1; s = o["story"]
            print(forced, rid, "F2", f2, "boss L/with/no", s["boss"][i][:3], "mk3", s["boss"][i][3], "min80", s["min80"][i], "minfill", s["min_fill"][i],
                  "mixed", o["mixed"]["split"][i], "hard", o["hard"]["split"][i], "hard cap/no", o["hard"]["boss"][i][1:3], "mixed80", o["mixed"]["boss"][i][1:3])
