"""DRAFT runner (Barry, UNAPPROVED): experience gauntlet (sim/scripts/experience_gauntlet.py, unchanged) on the Touge passing v1
variant. Live 0.5 unlock, live crew stats, same seeds, n per cell (default 6000).
  python3 run_touge_passing.py --variant live|pp|w035 [--rung-scale s1,..,s7] [--w W] [--boss-scale S] [--n 6000] [--json out.json]
--boss-scale S multiplies the Touge boss crew budget (lever: crew re-pin), everything else live."""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, os.path.join(ROOT, "sim")); sys.path.insert(0, os.path.join(ROOT, "sim", "scripts")); sys.path.insert(0, HERE)
import experience_gauntlet as G
import touge_passing as TP
from velocity_shift import mod_skill as M

ap = argparse.ArgumentParser()
ap.add_argument("--variant", default="w035"); ap.add_argument("--w", type=float, default=None)
ap.add_argument("--boss-scale", type=float, default=1.0); ap.add_argument("--rung-scale", default=None,
                help="comma list of 7 Touge budget multipliers kid1..boss")
ap.add_argument("--touge-budget", default=None, help="comma list of 7 exact Touge crew stats kid1..boss (overrides scales)")
ap.add_argument("--seed", type=int, default=None, help="base seed (default experience_gauntlet.SEED 96,000,000)")
ap.add_argument("--n", type=int, default=6000); ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
ap.add_argument("--json", default=None); ap.add_argument("--district", action="append", default=None)
a = ap.parse_args()
if a.variant != "live":
    TP.install(("touge",), a.w if a.w is not None else (1.0 if a.variant == "pp" else 0.35))
scale = [1.0] * 6 + [a.boss_scale]
if a.rung_scale: scale = [float(x) for x in a.rung_scale.split(",")]
if a.seed is not None: G.SEED = a.seed
if a.touge_budget:
    tb = [float(x) for x in a.touge_budget.split(",")]
    _cb0 = M.crew_budget
    def crew_budget(rnd, j, _cb=_cb0):
        return tb[M.rung_index(j)] if M.DISTRICTS[rnd] == "touge" else _cb(rnd, j)
    M.crew_budget = crew_budget
elif scale != [1.0] * 7:
    _cb = M.crew_budget
    def crew_budget(rnd, j, _cb=_cb):
        b = _cb(rnd, j)
        return b * scale[M.rung_index(j)] if M.DISTRICTS[rnd] == "touge" else b
    M.crew_budget = crew_budget
res, fails = G.evaluate(G.run(a.n, a.workers, a.district or ["touge"]))
G.report(res, fails, a.n - a.n % 3)
if a.json:
    json.dump(dict(seed=G.SEED, touge_budget=a.touge_budget, variant=a.variant, w=TP.SETTINGS["w"] if a.variant != "live" else None, scale=scale, n=a.n,
                   results=res, fails=fails), open(a.json, "w"), indent=1)
