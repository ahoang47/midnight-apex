"""Criterion 10 on the live stand-in tracks (aero must not be a no-brainer). Draft, Barry 2026-11-13.
Same method as econ-v1 run_aero_sweep.py, re-done on the live engine/tracks:
  0-aero = district-fixed tune (run_sweep.TUNES).
  1-aero = live rule AERO_MAX_EQUIPPED=1, AERO_FREE_POOL_MAX_FRACTION=0.10 of one part: one slot = 0.27/6 of P,
           10% free -> 0.0045 P = 0.0042 of the 1.07P combat split moved (L1 mass) toward that track's best split.
  full-retune (reference upper bound, NOT legal): the track's best split itself.
Stage 1 (STAGE=1): per-track best split, 60/60 r=1.07, 23 splits, 10/20/30 turns, N per style.
Stage 2 (STAGE=2): paired-seed WR for the three tunes at the proposed boss r, 4 profiles, 10 & 30 turns."""
import json, os, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livesim as LS
from run_sweep import TUNES
from run_tune_screen import SPLITS
HERE = LS.HERE
MASS = 0.27 / 6 * 0.10 / 1.07
STAGE = int(os.environ.get("STAGE", "1"))
N = int(os.environ.get("N", "150"))


def j1(a):
    d, t, L, st, tu = a
    return a, LS.batch(d, t, L, st, "c6060", 1.07, tu, N, LS.seed_of("aero1", d, t, L, st))


def aero_tune(fixed, best):
    delta = [b - f for f, b in zip(fixed, best)]
    half = sum(abs(x) for x in delta) / 2
    if half < 1e-9:
        return tuple(fixed)
    m = min(MASS, half)
    return tuple(f + m * x / half for f, x in zip(fixed, delta))


def j2(a):
    d, t, L, st, pr, r, kind, tu = a
    return a, LS.batch(d, t, L, st, pr, r, tu, N, LS.seed_of("aero2", d, t, L, st, pr, r))   # paired across tunes


if __name__ == "__main__":
    TR = LS.tracks(); t0 = time.time()
    if STAGE == 1:
        jobs = [(d, t, L, st, tu) for d in TR for t in TR[d] for L in LS.LENGTHS for st in LS.STYLES for tu in SPLITS]
        acc = {}
        with Pool(8) as p:
            for (d, t, L, st, tu), v in p.imap_unordered(j1, jobs, chunksize=4):
                acc.setdefault((d, t, tu), []).append(v)
        best = {}
        for (d, t, tu), v in acc.items():
            m = sum(v) / len(v)
            if t not in best or m > best[t]["mean"]:
                best[t] = dict(district=d, tune=list(tu), mean=round(m, 2))
        for t in best:
            d = best[t]["district"]
            best[t]["fixed_mean"] = round(sum(acc[(d, t, tuple(TUNES[d]))]) / len(acc[(d, t, tuple(TUNES[d]))]), 2) \
                if (d, t, tuple(TUNES[d])) in acc else None
        json.dump(dict(n=N, r=1.07, profile="c6060", seconds=round(time.time() - t0), best=best),
                  open(os.path.join(HERE, "aero_best_splits_live.json"), "w"), indent=1)
        print(json.dumps(best, indent=1))
    else:
        best = json.load(open(os.path.join(HERE, "aero_best_splits_live.json")))["best"]
        R = json.loads(os.environ["BOSS_R"])
        jobs = []
        for d in TR:
            for t in TR[d]:
                fx = tuple(TUNES[d]); bs = tuple(best[t]["tune"])
                for kind, tu in (("fixed", fx), ("aero", aero_tune(fx, bs)), ("full", bs)):
                    for L in (10, 30):
                        for st in LS.STYLES:
                            for pr in LS.PROFILES:
                                jobs.append((d, t, L, st, pr, R[d], kind, tu))
        acc = {}
        with Pool(8) as p:
            for (d, t, L, st, pr, r, kind, tu), v in p.imap_unordered(j2, jobs, chunksize=2):
                acc.setdefault(f"{d}|{t}|{L}|{pr}|{kind}", []).append(v)
        win = {k: round(sum(v) / len(v), 2) for k, v in sorted(acc.items())}
        json.dump(dict(n_per_style=N, boss_r=R, mass=MASS, seconds=round(time.time() - t0), win=win),
                  open(os.path.join(HERE, "aero_live.json"), "w"), indent=1)
        print("done", round(time.time() - t0))
