"""Climb re-pin v2 (Barry DRAFT, unapproved): crew stat totals only (floors, XP, cap unchanged), model = Street/Wangan
per-phase smoothed QTE w 0.35 + player lock cap 2 (load kept); Touge per-turn + lock cap (canon), Touge per-phase what-if.
Engine: patched sim copy (per_phase.patch), mod_skill.crew_config, seeds 96,000,000 + style x 100,000 + k (live climb).
  python3 repin.py search   -> bisection per rung on strong 80/80 at floor to TARGET (common seeds, n=1200) -> search.json
  python3 repin.py verify [budgets.json] -> all cells (rungs 2,000, bosses 6,000) -> verify.json
"""
import json, os, sys
from multiprocessing import Pool
SIM = os.environ.get("SIM", "/tmp/pp/sim"); sys.path.insert(0, SIM); sys.path.insert(0, os.path.join(SIM, "scripts"))
from velocity_shift import equations as E, mod_skill as M
from velocity_shift.simulation import SimulationRunner
from mod_skill_climb import max_build

SEED = 96_000_000
CAP = dict(lock_cap=2, lock_cap_keep_load=True)
MODEL = {"street": dict(per_phase=True, phase_smooth_w=0.35, **CAP), "wangan": dict(per_phase=True, phase_smooth_w=0.35, **CAP),
         "touge": dict(per_phase=False, **CAP), "touge_pp": dict(per_phase=True, phase_smooth_w=0.35, **CAP)}
TARGET = tuple(float(x) for x in os.environ.get("TARGET", "95,89,84,79,75,71,67").split(","))
SEARCH_N = int(os.environ.get("SEARCH_N", "1200"))
FIXED_BOSS = json.loads(os.environ.get("FIXED_BOSS", "null"))   # {"street": B, ...}: boss not searched
HERE = os.path.dirname(os.path.abspath(__file__))


def win(model, rnd, j, B, q, pts, n):
    d = M.DISTRICTS[rnd]; b = list(E.MS_CREW_BUDGET[d]); b[j] = B; E.MS_CREW_BUDGET[d] = tuple(b)
    w = 0.0; m = 0
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(n // 3):
            r = SimulationRunner(M.crew_config(rnd, j, pts, seed=SEED + si * 100_000 + k, player_read=q, player_timing=q,
                                               player_pacing=q, boss_style=st, **MODEL[model])).run().match
            x, y = r.player_total_progress, r.opponent_total_progress
            w += 1.0 if x > y else 0.5 if x == y else 0.0; m += 1
    return 100 * w / m


def search_job(t):
    model, rnd, j = t; d = M.DISTRICTS[rnd]
    if FIXED_BOSS and j == 6: return model, rnd, j, FIXED_BOSS[model]
    B0 = E.MS_CREW_BUDGET[d][j]; fl = E.MS_FLOOR_POINTS[d][j]
    lo, hi = 0.85 * B0, 1.25 * B0
    for _ in range(9):
        mid = 0.5 * (lo + hi)
        if win(model, rnd, j, mid, 0.8, fl, SEARCH_N) > TARGET[j]: lo = mid
        else: hi = mid
    return model, rnd, j, round(0.5 * (lo + hi), 2)


def verify_job(t):
    model, rnd, j, B, q, which, n = t; d = M.DISTRICTS[rnd]
    pts = E.MS_FLOOR_POINTS[d][j] if which == "floor" else max_build()[d][j]
    return t, round(win(model, rnd, j, B, q, pts, n), 2)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "search":
        J = [(m, r, j) for m, r in (("street", 0), ("wangan", 1), ("touge", 2)) for j in range(7)]
        with Pool(8) as p: R = p.map(search_job, sorted(J, key=lambda t: -t[2]), chunksize=1)
        out = {m: [None] * 7 for m in ("street", "wangan", "touge")}
        for m, r, j, B in R: out[m][j] = B
        json.dump(dict(target=TARGET, budgets=out), open(os.path.join(HERE, os.environ.get("OUT", "search.json")), "w"), indent=1); print(out)
    else:
        bud = json.load(open(os.path.join(HERE, sys.argv[2] if len(sys.argv) > 2 else "search.json")))["budgets"]
        bud["touge_pp"] = bud["touge"]; J = []
        for m, rnd in (("street", 0), ("wangan", 1), ("touge", 2), ("touge_pp", 2)):
            for j in range(7):
                n = 6000 if j == 6 else 2000
                J += [(m, rnd, j, bud[m][j], 0.8, "floor", n), (m, rnd, j, bud[m][j], 0.6, "max", n)]
            J += [(m, rnd, 6, bud[m][6], 0.6, "floor", 6000), (m, rnd, 6, bud[m][6], 0.8, "max", 6000)]
        with Pool(8) as p: R = p.map(verify_job, sorted(J, key=lambda t: -t[6]), chunksize=1)
        out = {}
        for (m, rnd, j, B, q, which, n), w in R:
            o = out.setdefault(m, {"budgets": bud[m], "strong_floor": [None] * 7, "weak_max": [None] * 7})
            key = ("strong_" if q == 0.8 else "weak_") + which
            if key in ("strong_floor", "weak_max"): o[key][j] = w
            else: o["boss_" + key] = w
        tag = sys.argv[3] if len(sys.argv) > 3 else "verify"
        json.dump(out, open(os.path.join(HERE, tag + ".json"), "w"), indent=1)
        for m, o in out.items(): print(m, o)
