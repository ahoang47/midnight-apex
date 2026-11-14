"""All-in / skewed build test on the live engine (G2 heat, live QTE, live stand-in tracks), draft.
Each build is (POW, HAN, EN) shares of the same stat total, at the district's boss r, every track, 10/20/30 turns,
3 boss styles, profiles 80/80 and 60/60. Exact zero in a stat is not runnable (heat.py overrun_if divides by the
stat's heat capacity), so "all-in" is 98/1/1."""
import os, sys, json, time
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "econ-v1-live-tracks"))
import livesim as LS
N = int(os.environ.get("N", "200"))
R = {"street": 1.044, "wangan": 1.055, "touge": 1.071}
TUNE = {"street": (0.50, 0.25, 0.25), "wangan": (0.25, 0.25, 0.50), "touge": (0.45, 0.25, 0.30)}
def perms(a, b):
    return [(a, b, b), (b, a, b), (b, b, a)]
BUILDS = {"even": (1/3, 1/3, 1/3)}
for name, (a, b) in {"allin98": (0.98, 0.01), "skew70": (0.70, 0.15), "skew60": (0.60, 0.20), "cap50": (0.50, 0.25)}.items():
    for lab, t in zip(("POW", "HAN", "EN"), perms(a, b)):
        BUILDS[f"{name}_{lab}"] = t
HARD = {"street": "S1_Shibuya_Grid", "wangan": "W3_C1_Outer", "touge": "T3_Usui_Esses"}

def job(a):
    d, t, L, st, pr, bn = a
    tu = TUNE[d] if bn == "tune" else BUILDS[bn]
    return a, LS.batch(d, t, L, st, pr, R[d], tu, N, LS.seed_of("sp1", d, t, L, st, pr))   # same seeds across builds

if __name__ == "__main__":
    TR = LS.tracks()
    jobs = [(d, t, L, st, pr, bn) for d in TR for t in TR[d] for L in LS.LENGTHS for st in LS.STYLES
            for pr in ("c8080", "c6060") for bn in ["tune"] + list(BUILDS)]
    t0 = time.time(); res = {}
    with Pool(int(os.environ.get("PROCS", "8"))) as p:
        for (d, t, L, st, pr, bn), v in p.imap_unordered(job, jobs, chunksize=8):
            res.setdefault(bn, {}).setdefault(pr, {}).setdefault(d, {}).setdefault(t, {}).setdefault(str(L), []).append(v)
    out = {}
    for bn, a in res.items():
        for pr, b in a.items():
            for d, c in b.items():
                mean = {L: sum(sum(c[t][L]) / len(c[t][L]) for t in c) / len(c) for L in ("10", "20", "30")}
                hard = {L: sum(c[HARD[d]][L]) / len(c[HARD[d]][L]) for L in ("10", "20", "30")}
                out.setdefault(bn, {}).setdefault(pr, {})[d] = dict(mean={k: round(v, 1) for k, v in mean.items()},
                                                                   hard={k: round(v, 1) for k, v in hard.items()})
    json.dump(dict(n=N, r=R, tunes=TUNE, builds={k: list(v) for k, v in BUILDS.items()}, seconds=round(time.time() - t0),
                   win=out), open(os.path.join(HERE, "builds.json"), "w"), indent=1)
    print("done", round(time.time() - t0), "s")
