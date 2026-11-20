"""planner-v2: win-chance tables by Monte Carlo through the LIVE sim (mod_skill.crew_config, live HEAT_RELEASE, live crew
stats, the district's hardest live track, player on the district tune). Grid: district x rung x player car points x reading.
Reading q drives player_read = player_timing = player_pacing (as experience_gauntlet.py). Ties count half.
Points knots per district: the 7 rung floors (E.MS_FLOOR_POINTS), the midpoint boss floor -> round cap, the round cap
(E.MS_ROUND_CAP_POINTS), so every 'at the floor' cell is a knot (no interpolation there).
Seeds: SEED + style x 100,000 + k over the 3 boss styles (E.BOSS_STYLES), n/3 each; reproducible.
Run from this folder: python3 build_tables.py [--n 2400] [--workers 8]  -> win_tables.json"""
import argparse, json, os, subprocess, sys
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "sim"))
from velocity_shift import equations as E, mod_skill as M
from velocity_shift.simulation import SimulationRunner

SEED = 96_000_000                # experience_gauntlet.py's seeds: each cell is a subset of the gauntlet's races
Q_LEVELS = (0.6, 0.65, 0.7, 0.75, 0.8)
PTS_KNOTS = 9                    # the 7 rung floors, the midpoint boss floor -> round cap, the round cap


def knots(rnd):
    fl, cap = list(E.MS_FLOOR_POINTS[M.DISTRICTS[rnd]]), E.MS_ROUND_CAP_POINTS[rnd]
    return fl + [round((fl[-1] + cap) / 2), cap]


def job(t):
    rnd, j, qi, pi, si, k0, k1 = t; q = Q_LEVELS[qi]; pts = knots(rnd)[pi]; w = 0.0
    for k in range(k0, k1):
        m = SimulationRunner(M.crew_config(rnd, j, pts, seed=SEED + si * 100_000 + k, player_read=q, player_timing=q,
                                           player_pacing=q, boss_style=E.BOSS_STYLES[si])).run().match
        x, y = m.player_total_progress, m.opponent_total_progress
        w += 1.0 if x > y else 0.5 if x == y else 0.0
    return (rnd, j, qi, pi), w, k1 - k0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=2400); ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args(); per = a.n // len(E.BOSS_STYLES); chunk = 400
    J = [(rnd, j, qi, pi, si, k0, min(per, k0 + chunk)) for rnd in range(3) for j in range(7) for qi in range(len(Q_LEVELS))
         for pi in range(PTS_KNOTS) for si in range(len(E.BOSS_STYLES)) for k0 in range(0, per, chunk)]
    J.sort(key=lambda t: -E.LADDER_TURNS[t[1]])
    with Pool(a.workers) as p: R = p.map(job, J, chunksize=1)
    acc = {}
    for key, w, n in R: s = acc.setdefault(key, [0.0, 0]); s[0] += w; s[1] += n
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE, capture_output=True, text=True).stdout.strip()
    out = dict(commit=commit, heat_release=E.HEAT_RELEASE, n=a.n, seed=SEED, q=list(Q_LEVELS), track={d: E.BOSS_HARD_TRACK[d] for d in M.DISTRICTS},
               pts={d: knots(r) for r, d in enumerate(M.DISTRICTS)},
               win={d: [[[round(100 * acc[(r, j, qi, pi)][0] / acc[(r, j, qi, pi)][1], 2) for pi in range(PTS_KNOTS)]
                         for qi in range(len(Q_LEVELS))] for j in range(7)] for r, d in enumerate(M.DISTRICTS)})
    json.dump(out, open(os.path.join(HERE, "win_tables.json"), "w"), indent=1)
    print("win_tables.json", commit, "HEAT_RELEASE", E.HEAT_RELEASE, "n", a.n)
