"""Probe (Barry 2026-11-19): Touge boss 80/80 near r 1.022 (boss_lever trace is steppy) and kid1 r for 80/80 = 97.5 at the new
floors (Wangan 3392, Touge 3904) so G3a's kid1 -> boss drop stays >= 30. Engine, climb_grid protocol. -> boss65_probe.json"""
import json, os
from multiprocessing import Pool
import climb_grid as CG, boss_lever as BL
HERE = os.path.dirname(os.path.abspath(__file__))


def tb(r): return ("touge_boss", r, BL.cell(2, 0.8, r))


def k1(t):
    d, lo, hi = t; tr = []
    for _ in range(7):
        mid = (lo + hi) / 2; _, w = CG.cell(("V0", d, "kid", "80/80", round(mid, 4), 3000, 99_000_000)); tr.append((round(mid, 4), w))
        if abs(w - 97.5) <= 0.4: break
        lo, hi = (mid, hi) if w < 97.5 else (lo, mid)
    return ("kid1", d, mid, w, tr)


def job(t): return tb(t[1]) if t[0] == "tb" else k1(t[1])


if __name__ == "__main__":
    J = [("tb", r) for r in (1.0219, 1.0220, 1.0221, 1.0223, 1.0225)] + [("k1", ("wangan", 1.046, 1.12)), ("k1", ("touge", 1.0636, 1.14))]
    with Pool(7) as p:
        res = p.map(job, J, chunksize=1)
    json.dump(res, open(os.path.join(HERE, "boss65_probe.json"), "w"), indent=1)
    for x in res: print(x)
