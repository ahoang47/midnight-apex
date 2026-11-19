"""Regenerate the off-tune delta table under the live AI QTE model (Austin 2026-11-19) -> sim/config/winrate_offtune_v2.json.
Same method as the tool that built winrate_offtune_v1.json (skill-points-v1 retune_sweep.py, tag rt1, commit c877a19):
splits POW = p, HAN = 0.25, EN = 0.75 - p, p 0.25..0.50; r 0.97..1.18; N=150 per style; 3 boss styles; even opponent;
common random numbers (same seeds for every p). progression.track_win uses only the delta win(p) - win(p_tune).
Usage: python3 offtune_v2.py  (8 processes; ~20 min)"""
import os, sys, json, time
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sweep_v2 as SV
from velocity_shift import combat as C, equations as E
N = int(os.environ.get("N", "150")); TAG = "rt1v2"
PS = (0.25, 0.30, 0.35, 0.40, 0.45, 0.50)
RS = (0.97, 1.00, 1.02, 1.04, 1.06, 1.08, 1.12, 1.18)
PROFS = ("c6060", "c6080", "c8060", "c8080")
ORIG = dict(E.DISTRICT_TUNE)


def job(a):
    d, t, L, st, pr, r, p = a
    E.DISTRICT_TUNE[d] = (p, 0.25, 0.75 - p)       # in-process only: SV.batch reads the player split from DISTRICT_TUNE
    try:
        v = SV.batch(d, t, L, st, pr, r, SV.EVEN, N, SV.seed_of(TAG, d, t, L, st, pr, r))
    finally:
        E.DISTRICT_TUNE[d] = ORIG[d]
    return a, v


if __name__ == "__main__":
    TR = C.official_tracks()
    jobs = [(d, t, L, st, pr, r, p) for d in TR for t in TR[d] for L in (10, 20, 30) for st in E.BOSS_STYLES
            for pr in PROFS for r in RS for p in PS]
    t0 = time.time(); res = {}
    with Pool(8) as pool:
        for i, ((d, t, L, st, pr, r, p), v) in enumerate(pool.imap_unordered(job, jobs, chunksize=16)):
            res.setdefault(pr, {}).setdefault(str(L), {}).setdefault(t, {}).setdefault(f"{r:.3f}", {}).setdefault(f"{p:.3f}", []).append(v)
            if i % 4000 == 0:
                print(i, len(jobs), round(time.time() - t0), flush=True)
    out = {pr: {L: {t: {r: {p: sum(v) / len(v) for p, v in bp.items()} for r, bp in br.items()} for t, br in bt.items()}
                for L, bt in bl.items()} for pr, bl in res.items()}
    path = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "sim", "config", "winrate_offtune_v2.json"))
    json.dump(dict(_comment="Off-tune deltas, live engine with the 0.80 random AI QTE (Austin 2026-11-19); built by "
                            "unapproved/barry/ai-heat-qte-v1/table_v2/offtune_v2.py (same method as winrate_offtune_v1.json).",
                   n_per_style=N, styles=list(E.BOSS_STYLES), ps=PS, rs=RS, tag=TAG, seconds=round(time.time() - t0),
                   tracks=[[d, t] for d in TR for t in TR[d]], win=out), open(path, "w"))
    print("done", path, round(time.time() - t0), "s", flush=True)
