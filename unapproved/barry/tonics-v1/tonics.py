"""tonics-v1 (Barry DRAFT, unapproved). Tonic (my placeholder definition, no spec exists in the repo): a consumable; at the
start of a turn, if any player gauge is locked, one tonic cools the hottest locked gauge to 0 and unlocks it (max 1 per
turn, N per race). Heat models: "live" = live locks with live crew stats (per-turn engine, all districts); "lockcap" = the
climb-repin-v2 proposal (player lock cap 2, load kept; Street/Wangan per-phase smoothed w 0.35, Touge per-turn) with its
re-pinned crew stats. Cells: kid1, oh2, boss; strong 80/80 at floor, weak 60/60 at max; tonics 0-3; common seeds
(paired). n = 1,500 (kid1/oh2), 3,000 (boss). Usage: SIM=/tmp/pp/sim python3 tonics.py"""
import json, os, sys
from multiprocessing import Pool
SIM = os.environ.get("SIM", "/tmp/pp/sim"); sys.path.insert(0, SIM); sys.path.insert(0, os.path.join(SIM, "scripts"))
from velocity_shift import equations as E, mod_skill as M
from velocity_shift.simulation import SimulationRunner
from mod_skill_climb import max_build

HERE = os.path.dirname(os.path.abspath(__file__)); SEED = 97_000_000
REPIN = json.load(open(os.path.join(HERE, "..", "climb-repin-v2", "repin_final.json")))["budgets"]
CAP = dict(lock_cap=2, lock_cap_keep_load=True)
MODELS = {"live": {d: dict(per_phase=False) for d in M.DISTRICTS},
          "lockcap": {"street": dict(per_phase=True, phase_smooth_w=0.35, **CAP), "wangan": dict(per_phase=True, phase_smooth_w=0.35, **CAP),
                      "touge": dict(per_phase=False, **CAP)}}
RUNGS = (0, 5, 6)
FO = {t: json.load(open(os.path.join(HERE, "..", "climb-repin-v2", "fo%s_final.json" % t)))["budgets"] for t in ("0.5", "0.7")}
for t in FO:   # heat falloff (Austin 7:04-7:08 AM): no locks; tonic cools the hottest gauge to 0 at turn start
    MODELS["fo" + t] = {"street": dict(per_phase=True, phase_smooth_w=0.35, falloff_t=float(t)), "wangan": dict(per_phase=True, phase_smooth_w=0.35, falloff_t=float(t)),
                        "touge": dict(per_phase=False, falloff_t=float(t))}
ONLY = os.environ.get("ONLY")
LIVE = {d: tuple(E.MS_CREW_BUDGET[d]) for d in M.DISTRICTS}


def job(t):
    model, rnd, j, q, which, nt, n = t; d = M.DISTRICTS[rnd]
    E.MS_CREW_BUDGET[d] = tuple(REPIN[d]) if model == "lockcap" else tuple(FO[model[2:]][d]) if model.startswith("fo") else LIVE[d]   # set every job (pool workers are reused)
    pts = E.MS_FLOOR_POINTS[d][j] if which == "floor" else max_build()[d][j]
    w = used = 0.0; m = 0
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(n // 3):
            r = SimulationRunner(M.crew_config(rnd, j, pts, seed=SEED + si * 100_000 + k, player_read=q, player_timing=q, player_pacing=q,
                                               boss_style=st, tonics=nt, **MODELS[model][d])).run().match
            x, y = r.player_total_progress, r.opponent_total_progress
            w += 1.0 if x > y else 0.5 if x == y else 0.0; m += 1; used += r.tonics_used
    return t, round(100 * w / m, 2), round(used / m, 2)


if __name__ == "__main__":
    J = [(mo, rnd, j, q, wh, nt, 3000 if j == 6 else 1500) for mo in MODELS if not ONLY or mo in ONLY.split(',') for rnd in range(3) for j in RUNGS
         for q, wh in ((0.8, "floor"), (0.6, "max")) for nt in range(4)]
    with Pool(8) as p: R = p.map(job, sorted(J, key=lambda t: -t[2]), chunksize=1)
    out = {}
    for (mo, rnd, j, q, wh, nt, n), w, u in R:
        c = out.setdefault(mo, {}).setdefault(M.DISTRICTS[rnd], {}).setdefault(M.RUNGS[j], {}).setdefault("strong_floor" if q == 0.8 else "weak_max", {})
        c[nt] = dict(win=w, used=u)
    json.dump(out, open(os.path.join(HERE, os.environ.get("OUT", "tonics.json")), "w"), indent=1)
    for mo in out:
        for d in out[mo]:
            for rg in out[mo][d]:
                for pl, c in out[mo][d][rg].items():
                    print(mo, d, rg, pl, [c[k]["win"] for k in sorted(c)], "used", [c[k]["used"] for k in sorted(c)])
