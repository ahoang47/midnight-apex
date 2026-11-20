"""Feel at kid1 / oh1 / boss for the strong 80/80 (floor) and weak 60/60 (max build) player, all three districts:
turns starting locked, limp %, mean lock length, races with all three gauges locked, win %. Live sim; 3 boss styles x 200 seeds
(96,000,000 + style x 100,000 + k). Usage: RELEASE=0.3|0.5 python3 feel.py <budgets.json|live> <tag>"""
import json, os, sys
from multiprocessing import Pool
import repin as R
sys.path.insert(0, os.path.join(R.HERE, "..", "experience-rootcause-v1"))
from exp import feel, agg
E, M = R.E, R.M
BUD = None if sys.argv[1] == "live" else json.load(open(os.path.join(R.HERE, sys.argv[1])))
BUD = BUD.get("budgets", BUD) if BUD else None


def job(t):
    rnd, j, q, which, si, n = t; d = M.DISTRICTS[rnd]
    if BUD: E.MS_CREW_BUDGET[d] = tuple(BUD[d])
    pts = E.MS_FLOOR_POINTS[d][j] if which == "floor" else R.max_build()[d][j]; rows = []
    for k in range(n):
        m = R.SimulationRunner(M.crew_config(rnd, j, pts, seed=R.SEED + si * 100_000 + k, player_read=q, player_timing=q,
                                             player_pacing=q, boss_style=E.BOSS_STYLES[si])).run().match
        f = feel(m); x, y = m.player_total_progress, m.opponent_total_progress; f["win"] = 1.0 if x > y else 0.5 if x == y else 0.0; rows.append(f)
    return (rnd, j, q, which), rows


if __name__ == "__main__":
    J = [(rnd, j, q, w, si, 200) for rnd in range(3) for j in (0, 4, 6) for q, w in ((0.8, "floor"), (0.6, "max")) for si in range(3)]
    with Pool(8) as p: res = p.map(job, J, chunksize=1)
    acc = {}
    for k, rows in res: acc.setdefault(k, []).extend(rows)
    out = {}
    for (rnd, j, q, w), rows in sorted(acc.items()):
        s = agg(rows); s["win"] = round(100 * sum(r["win"] for r in rows) / len(rows), 2)
        out.setdefault(M.DISTRICTS[rnd], {})[f"{M.RUNGS[j]} {'strong floor' if q == 0.8 else 'weak max'}"] = s
    json.dump(dict(release=R.RELEASE, budgets=sys.argv[1], n_per_cell=600, out=out), open(os.path.join(R.HERE, f"feel_{sys.argv[2]}.json"), "w"), indent=1)
    for d, c in out.items():
        for k, s in c.items(): print(d, k, s["win"], s["turns_starting_locked_pct"], s["limp_pct"], s["mean_lock_turns"], s["races_with_all_locked_pct"])
