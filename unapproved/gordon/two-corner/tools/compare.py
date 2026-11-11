"""Compare an engine's race output to the sim's, per clash. Usage: compare.py sim.json engine.json [--tol 1e-12]
Both files may be a single race object or a {"races": [...]} batch."""
import json, sys
TOL = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 1e-12

def races(p):
    d = json.load(open(p)); return d["races"] if "races" in d else [d]

S, G = races(sys.argv[1]), races(sys.argv[2])
assert len(S) == len(G), (len(S), len(G))
worst = 0.0; nclash = 0; fails = []; rows = []
for s, g in zip(S, G):
    assert s["seed"] == g["seed"]
    for i, (cs, cg) in enumerate(zip(s["corners"], g["corners"])):
        for k in ("line", "hand", "picks", "outcomes", "timing", "rng_draws_after"):
            if cs[k] != cg[k]: fails.append(f"seed {s['seed']} corner {i} {k}: sim={cs[k]} engine={cg[k]}")
        for side in ("player_clash", "opponent_clash"):
            for j, (a, b) in enumerate(zip(cs[side], cg[side])):
                d = abs(a - b); worst = max(worst, d); nclash += 1
                if d > TOL: fails.append(f"seed {s['seed']} corner {i} {side}[{j}] sim={a!r} engine={b!r} diff={d:.3e}")
                if len(S) == 1: rows.append((i + 1, cs["district"], cs["corner"], side.split("_")[0], j + 1, a, b, d))
    if s["winner"] != g["winner"]: fails.append(f"seed {s['seed']} winner sim={s['winner']} engine={g['winner']}")
    for k in ("player_total", "opponent_total"):
        worst = max(worst, abs(s[k] - g[k]))
if rows:
    print(f"{'crn':>3} {'district':8} {'code':4} {'side':8} {'clash':>5} {'sim g':>20} {'engine g':>20} {'|diff|':>9}")
    for r in rows: print(f"{r[0]:>3} {r[1]:8} {r[2]:4} {r[3]:8} {r[4]:>5} {r[5]:>20.16f} {r[6]:>20.16f} {r[7]:>9.1e}")
print(f"races={len(S)} clash_values={nclash} max_abs_diff={worst:.3e} tol={TOL:g} -> {'PASS' if not fails else 'FAIL'}")
for f in fails[:20]: print("  ", f)
sys.exit(1 if fails else 0)
