"""oh2 at ~70 % (Barry, 2026-11-19, Austin: "Make the old head a bit easier, about 70%, and keep the boss at 66-68%").
Bisection on oh2 r at the climb65 floors (Street 3275, Wangan 3802, Touge 4344) for 80/80 = 71 (band 70-72), engine n = 6000,
climb_grid protocol, same seed as climb65. Touge first checked at its current r 1.018. -> oh2_70.json"""
import json, os
from multiprocessing import Pool
import climb_grid as CG
HERE = os.path.dirname(os.path.abspath(__file__))
D = ("street", "wangan", "touge"); R0 = (3275 / 10 / 332.93, 3802 / 10 / 384.44, 1.018)


def w(d, r, prof="80/80"): return CG.cell(("V0", d, "oh", prof, round(r, 4), 6000, 96_000_000))[1]


def job(i):
    d = D[i]; r0 = R0[i]; v0 = w(d, r0); tr = [(round(r0, 4), v0)]
    if 70 <= v0 <= 72: return dict(d=d, r=round(r0, 4), w8080=v0, moved=False, trace=tr)
    lo, hi = (r0, r0 + 0.06) if v0 < 70 else (r0 - 0.06, r0)
    for _ in range(9):
        mid = round((lo + hi) / 2, 4); v = w(d, mid); tr.append((mid, v))
        if 70 <= v <= 72: return dict(d=d, r=mid, w8080=v, moved=True, trace=tr)
        lo, hi = (mid, hi) if v < 71 else (lo, mid)
    return dict(d=d, r=mid, w8080=v, moved=True, trace=tr, unconverged=True)


if __name__ == "__main__":
    with Pool(3) as p:
        res = p.map(job, range(3))
    json.dump(res, open(os.path.join(HERE, "oh2_70.json"), "w"), indent=1)
    for x in res: print(x)
