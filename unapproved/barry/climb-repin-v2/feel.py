"""Feel metrics, lock cap vs heat falloff (each with its own re-pinned crew stats), oh1 / oh2 / boss, strong 80/80 at floor
and weak 60/60 at max, n = 999 per cell (seeds 95,000,000+). Degraded = the stance countering the AI's planned Entry stance
is locked or would pay m < 0.7 at turn start. Avg mult = mean player clash output multiplier (overrun / falloff / limp).
Usage: SIM=/tmp/pp/sim python3 feel.py lockcap=repin_final.json fo0.5=fo0.5_final.json fo0.7=fo0.7_final.json"""
import json, os, sys
from multiprocessing import Pool
SIM = os.environ.get("SIM", "/tmp/pp/sim"); sys.path.insert(0, SIM); sys.path.insert(0, os.path.join(SIM, "scripts"))
from velocity_shift import equations as E, mod_skill as M
from velocity_shift.simulation import SimulationRunner
from mod_skill_climb import max_build
HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = dict(a.split("=") for a in sys.argv[1:])
BUD = {k: json.load(open(os.path.join(HERE, v)))["budgets"] for k, v in SPEC.items()}


def heat(model):
    return dict(lock_cap=2, lock_cap_keep_load=True) if model == "lockcap" else dict(falloff_t=float(model[2:]))


def job(t):
    model, rnd, j, q, which = t; d = M.DISTRICTS[rnd]; E.MS_CREW_BUDGET[d] = tuple(BUD[model][d])
    pp = dict(per_phase=True, phase_smooth_w=0.35) if d != "touge" else dict(per_phase=False)
    pts = E.MS_FLOOR_POINTS[d][j] if which == "floor" else max_build()[d][j]
    deg = tot = 0; ms = nc = 0.0; longest = []; win = 0.0; n = 999
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(n // 3):
            r = SimulationRunner(M.crew_config(rnd, j, pts, seed=95_000_000 + si * 100_000 + k, player_read=q, player_timing=q,
                                               player_pacing=q, boss_style=st, **pp, **heat(model))).run().match
            pd = r.pref_degraded; deg += sum(pd); tot += len(pd); run = best = 0
            for x in pd:
                run = run + 1 if x else 0; best = max(best, run)
            longest.append(best)
            for tr in r.turn_results: ms += sum(tr.player_heat_mults); nc += len(tr.player_heat_mults)
            win += 1.0 if r.player_total_progress > r.opponent_total_progress else 0.5 if r.player_total_progress == r.opponent_total_progress else 0.0
    return t, dict(win=round(100 * win / n, 1), degraded_pct=round(100 * deg / tot, 1), avg_mult=round(ms / nc, 3),
                   longest_mean=round(sum(longest) / n, 2), longest_max=max(longest))


if __name__ == "__main__":
    J = [(m, rnd, j, q, w) for m in BUD for rnd in range(3) for j in (4, 5, 6) for q, w in ((0.8, "floor"), (0.6, "max"))]
    with Pool(8) as p: R = p.map(job, sorted(J, key=lambda t: -t[2]), chunksize=1)
    out = {}
    for (m, rnd, j, q, w), v in R:
        out.setdefault(m, {}).setdefault(M.DISTRICTS[rnd], {})["%s %s" % (M.RUNGS[j], "strong" if q == 0.8 else "weak")] = v
    json.dump(out, open(os.path.join(HERE, "feel.json"), "w"), indent=1)
    for m in out:
        for d in out[m]:
            for c, v in sorted(out[m][d].items()): print(m, d, c, v)
