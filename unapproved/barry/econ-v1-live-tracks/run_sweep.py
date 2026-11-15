"""Live-engine r sweep on the LIVE stand-in tracks: 4 profiles x 15 tracks x 10/20/30 turns x 3 boss styles x R_GRID.

District-fixed tunes from run_tune_screen.py (tune_screen.json, 60/60 at r=1.07, mean over lengths).
Output: sweep_<tag>.json  {r: [...], win[profile][length][r_index][track_index] = % (mean over styles)}.
Env: N (races per track x style x r), R_GRID (json list), TAG.
"""
from __future__ import annotations
import json, os, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livesim as LS

TUNES = {"street": (0.50, 0.25, 0.25), "wangan": (0.25, 0.25, 0.50), "touge": (0.45, 0.25, 0.30)}   # POW, HAN, EN
N = int(os.environ.get("N", "300"))
R_GRID = json.loads(os.environ.get("R_GRID", json.dumps([round(0.94 + 0.01 * i, 2) for i in range(31)])))
LEN = json.loads(os.environ.get("LENGTHS", "[10, 20, 30]"))
PROFS = json.loads(os.environ.get("PROFS", json.dumps(list(LS.PROFILES))))
TAG = os.environ.get("TAG", "main")


def job(a):
    d, t, L, st, pr = a
    return a, [LS.batch(d, t, L, st, pr, r, TUNES[d], N, LS.seed_of(TAG, d, t, L, st, pr, r)) for r in R_GRID]


def main():
    TR = LS.tracks(); names = [(d, t) for d in sorted(TR) for t in sorted(TR[d])]
    jobs = [(d, t, L, st, pr) for (d, t) in names for L in LEN for st in LS.STYLES for pr in PROFS]
    jobs.sort(key=lambda a: -a[2])   # long races first
    t0 = time.time(); acc = {}; done = 0
    with Pool(8) as p:
        for (d, t, L, st, pr), v in p.imap_unordered(job, jobs):
            acc.setdefault((pr, L, d, t), []).append(v); done += 1
            if done % 50 == 0:
                print(f"{time.time() - t0:6.0f}s {done}/{len(jobs)}", flush=True)
    win = {pr: {str(L): [[round(sum(acc[(pr, L, d, t)][s][ri] for s in range(len(LS.STYLES))) / len(LS.STYLES), 3)
                          for (d, t) in names] for ri in range(len(R_GRID))] for L in LEN} for pr in PROFS}
    out = dict(_comment="Live engine, live stand-in tracks (sim/config/tracks_v1.json), G2 heat, live QTE mapping. Win % "
                        "(ties half), mean over 3 boss styles; n races per track x style x r.",
               n=N, r=R_GRID, tracks=[list(x) for x in names], tunes=TUNES, lengths=LEN,
               profiles={k: LS.PROFILES[k] for k in PROFS}, seconds=round(time.time() - t0), win=win)
    json.dump(out, open(os.path.join(LS.HERE, f"sweep_{TAG}.json"), "w"))
    print("wrote", TAG, round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
