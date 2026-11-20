"""mod_skill crew climb table (LIVE, go-live 2026-11-19): live engine through mod_skill.crew_config (district tune, hardest
live track, 3 boss styles x n/3 seeds, ties half, AI QTE 0.80 random). Cells per crew member: strong 80/80 and weak 60/60 at
the floor (E.MS_FLOOR_POINTS), weak 60/60 at the max build (non-mandatory cap MS_NM_XP_CAP, capped by the round), and the
boss 80/80 at the max build. Writes config/mod_skill_climb_v1.json; checked by tests/test_mod_skill.py against E.MS_TARGETS.
Usage: python scripts/mod_skill_climb.py [n=6000] [workers=8]"""
import json, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from velocity_shift import equations as E, mod_skill as M
from velocity_shift.simulation import SimulationRunner

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "mod_skill_climb_v1.json")
SEED = 96_000_000


def win(rnd, rung, pts, q, n, seed=SEED):
    w = m = 0.0
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(n // 3):
            cfg = M.crew_config(rnd, rung, pts, seed=seed + si * 100_000 + k, player_read=q, player_timing=q, player_pacing=q, boss_style=st)
            mm = SimulationRunner(cfg).run().match; x, y = mm.player_total_progress, mm.opponent_total_progress
            w += 1.0 if x > y else 0.5 if x == y else 0.0; m += 1
    return round(100 * w / m, 2)


def max_build():
    out, e = {}, E.MS_STOCK_POINTS
    for rnd, d in enumerate(M.DISTRICTS):
        fl = E.MS_FLOOR_POINTS[d]
        row = tuple(min(E.MS_ROUND_CAP_POINTS[rnd], e + (f - fl[0]) + E.MS_NM_XP_CAP * E.MS_WILD_XP[rnd]) for f in fl)
        out[d] = row; e = row[-1]
    return out


def _job(t):
    rnd, j, q, build, pts, n = t
    return t, win(rnd, j, pts, q, n)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6000; workers = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    MX = max_build(); J = []
    for rnd, d in enumerate(M.DISTRICTS):
        for j in range(7):
            fl = E.MS_FLOOR_POINTS[d][j]
            J += [(rnd, j, 0.8, "floor", fl, n), (rnd, j, 0.6, "floor", fl, n), (rnd, j, 0.6, "max", MX[d][j], n)]
        J.append((rnd, 6, 0.8, "max", MX[d][6], n))
    with Pool(workers) as p:
        res = p.map(_job, sorted(J, key=lambda t: -t[1]), chunksize=1)
    tab = {d: {r: {} for r in M.RUNGS} for d in M.DISTRICTS}
    for (rnd, j, q, build, pts, _), w in res:
        tab[M.DISTRICTS[rnd]][M.RUNGS[j]]["%s_%s" % ("strong" if q == 0.8 else "weak", build)] = w
    json.dump(dict(n=n, seed=SEED, note="live engine via mod_skill.crew_config; strong = 80/80, weak = 60/60; % wins, ties half",
                   floor=E.MS_FLOOR_POINTS, max_build=MX, table=tab), open(OUT, "w"), indent=1)
    for d in M.DISTRICTS:
        print(d, [tab[d][r]["strong_floor"] for r in M.RUNGS], "boss weak floor/max", tab[d]["boss"]["weak_floor"], tab[d]["boss"]["weak_max"], "strong max", tab[d]["boss"]["strong_max"])
