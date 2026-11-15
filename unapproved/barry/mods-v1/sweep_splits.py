"""Engine runs at the car splits the mod schemes reach (draft, Barry 2026-11-14). Same seeds as the skill-points-v1 rt1
sweep (seed_of('rt1', ...), independent of the split), so delta = win(split) - win_rt1(tune) is paired (CRN).
SPLITS env: JSON list of [district, pow, han, en, tracks ('all' | 'hard'), lens]."""
import os, sys, json, time
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "econ-v1-live-tracks"))
import livesim as LS
N = int(os.environ.get("N", "150")); TAG = "rt1"
RS = (0.97, 1.00, 1.02, 1.04, 1.06, 1.08, 1.12, 1.18)
PROFS = ("c6060", "c6080", "c8060", "c8080")
HARD = {"street": "S1_Shibuya_Grid", "wangan": "W3_C1_Outer", "touge": "T3_Usui_Esses"}

def job(a):
    key, d, t, L, st, pr, r, sh = a
    return a, LS.batch(d, t, L, st, pr, r, sh, N, LS.seed_of(TAG, d, t, L, st, pr, r))

if __name__ == "__main__":
    SPL = json.loads(os.environ["SPLITS"]); out_name = os.environ.get("OUT", "splits.json")
    TR = LS.tracks(); jobs = []
    for d, p, h, e, which, lens in SPL:
        key = f"{d}:{p:.3f}/{h:.3f}/{e:.3f}"
        ts = TR[d] if which == "all" else [HARD[d]]
        jobs += [(key, d, t, L, st, pr, r, (p, h, e)) for t in ts for L in lens for st in LS.STYLES for pr in PROFS for r in RS]
    t0 = time.time(); res = {}
    with Pool(int(os.environ.get("PROCS", "8"))) as pool:
        for i, ((key, d, t, L, st, pr, r, sh), v) in enumerate(pool.imap_unordered(job, jobs, chunksize=8)):
            res.setdefault(key, {}).setdefault(pr, {}).setdefault(str(L), {}).setdefault(t, {}).setdefault(f"{r:.3f}", []).append(v)
            if i % 1000 == 0: print(i, len(jobs), round(time.time() - t0), flush=True)
    out = {k: {pr: {L: {t: {r: sum(v) / len(v) for r, v in br.items()} for t, br in bt.items()} for L, bt in bl.items()} for pr, bl in bp.items()} for k, bp in res.items()}
    old = json.load(open(os.path.join(HERE, out_name))) if os.path.exists(os.path.join(HERE, out_name)) else {}
    old.update(out)
    json.dump(old, open(os.path.join(HERE, out_name), "w"))
    print("done", round(time.time() - t0), "s", flush=True)
