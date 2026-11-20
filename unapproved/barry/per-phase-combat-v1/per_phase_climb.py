"""Per-phase combat prototype climb (Barry DRAFT, unapproved). Runs the live mod_skill climb cells on a branch copy of sim/
with per_phase.patch applied (default /tmp/pp/sim). Variants: PP = per-phase, each clash its own phase QTE (player one press
per phase from the press model, AI one draw per phase); CTRL = same presses but turn average (isolates press noise);
SP = PP + spirit sweep bonus 0.20 (win all 3 clashes -> x1.20 clash progress next turn, both sides).
Cells: strong 80/80 at floor kid1..boss (2000; boss 6000), boss weak 60/60 at floor / at max, boss strong at max (6000).
Usage: python3 per_phase_climb.py [sim_copy=/tmp/pp/sim] [workers=8]"""
import json, os, sys
from multiprocessing import Pool
SIM = sys.argv[1] if len(sys.argv) > 1 else "/tmp/pp/sim"; sys.path.insert(0, SIM)
from velocity_shift import equations as E, mod_skill as M
from velocity_shift.simulation import SimulationRunner
sys.path.insert(0, os.path.join(SIM, "scripts"))
from mod_skill_climb import max_build

SEED = 96_000_000
VAR = {"PP": dict(per_phase=True), "CTRL": dict(per_phase=True, phase_avg_control=True), "SP": dict(per_phase=True, sweep_bonus=0.20)}


def job(t):
    v, rnd, j, q, pts, n, key = t; w = sw = 0.0; m = 0
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(n // 3):
            r = SimulationRunner(M.crew_config(rnd, j, pts, seed=SEED + si * 100_000 + k, player_read=q, player_timing=q,
                                               player_pacing=q, boss_style=st, **VAR[v])).run().match
            x, y = r.player_total_progress, r.opponent_total_progress
            w += 1.0 if x > y else 0.5 if x == y else 0.0; m += 1
            sw += sum(1 for tr in r.turn_results if all(o.value > 0 for o in tr.battle_outcomes)) / max(1, len(r.turn_results))
    return t, round(100 * w / m, 2), round(100 * sw / m, 1)


if __name__ == "__main__":
    MX = max_build(); J = []
    for v in VAR:
        for rnd, d in enumerate(M.DISTRICTS):
            fl = E.MS_FLOOR_POINTS[d]
            for j in range(7):
                J.append((v, rnd, j, 0.8, fl[j], 6000 if j == 6 else 2000, "strong_floor"))
            J += [(v, rnd, 6, 0.6, fl[6], 6000, "weak_floor"), (v, rnd, 6, 0.6, MX[d][6], 6000, "weak_max"), (v, rnd, 6, 0.8, MX[d][6], 6000, "strong_max")]
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 8) as p:
        res = p.map(job, sorted(J, key=lambda t: -t[5]), chunksize=1)
    out = {v: {d: {} for d in M.DISTRICTS} for v in VAR}
    for (v, rnd, j, q, pts, n, key), w, sw in res:
        d = out[v][M.DISTRICTS[rnd]]
        if key == "strong_floor":
            d.setdefault("strong_floor", [None] * 7)[j] = w; d.setdefault("sweep_pct_turns", [None] * 7)[j] = sw
        else:
            d[key] = w; d["sweep_" + key] = sw
    json.dump(dict(seed=SEED, variants=VAR, out=out), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "per_phase_climb.json"), "w"), indent=1)
    for v in VAR:
        for d in M.DISTRICTS:
            o = out[v][d]; print(v, d, o["strong_floor"], "wf", o["weak_floor"], "wm", o["weak_max"], "sm", o["strong_max"], "sweep%", o["sweep_pct_turns"][6], o["sweep_weak_max"])
