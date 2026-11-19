"""Bit-exact check: Godot combat.gd erf / expected_hit_quality / qte_zone_width / raw_qte_score vs the pinned sim.
Usage: python3 tools/qte_fn_test.py   (uses $GODOT or /workspace/tools/godot; prints PASS/FAIL and the max |diff|)

raw_qte_score must match bit-for-bit (it is rounded at QTE_SCORE_DECIMALS=3).
erf, expected_hit_quality and qte_zone_width stay unrounded and may differ by a couple of ULPs across
libm (glibc 2.41 on the box vs 2.43 on GitHub's Ubuntu 26.04 runner). A 2-ULP tolerance is allowed on
those three groups only. CI on 328a817 (strict qte-v1) reported 327 bit mismatches, 269 within 1 ULP,
58 at 2 ULP, max_abs_diff=2.220e-16, raw_qte_score exact.
"""
import json, math, os, random, struct, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_pin" / "sim"))
from velocity_shift import equations as E  # noqa: E402
def h(x): return "0x%016x" % struct.unpack("<Q", struct.pack("<d", x))[0]
def d(s): return struct.unpack("<d", struct.pack("<Q", int(s, 16)))[0]
def ulp_distance(a, b, cap=8):
    """Finite-value ULP steps from a to b, or None if farther than cap / non-finite."""
    if h(a) == h(b):
        return 0
    if not (math.isfinite(a) and math.isfinite(b)):
        return None
    n = 0
    t = a
    while t != b and n < cap:
        t = math.nextafter(t, b)
        n += 1
    return n if t == b else None
R = random.Random(11)
erf_x = [R.uniform(-7, 7) * R.choice([1, 1, 0.3, 0.01, 1e-5, 1e-9]) for _ in range(4000)] + [0.0, 0.5, 0.84375, 1.25, 2.857, 6.0, 30.0]
ehq = [(R.uniform(0.01, 2.0), R.uniform(0.0, 3.0)) for _ in range(1500)] + [(s, 1.0) for s in E.QTE_SKILL_SIGMA_OVER_A0.values()]
zone = [(R.uniform(0.6, 1.2), R.choice([0.0, 0.0, 0.1, 0.25, R.uniform(0, 0.5)])) for _ in range(150)] + [(r, 0.0) for r, _ in E.KNOT_WINDOW_105] + [(1.05, 0.0)]
raw = [(R.uniform(0.7, 1.15), R.choice(["weak", "average", "strong", None]), None, R.choice([0.0, 0.1])) for _ in range(60)]
raw += [(R.uniform(0.7, 1.15), None, R.choice([0.4, 0.6, 0.8, R.uniform(0.05, 0.95)]), 0.0) for _ in range(30)]
grid = {"erf": [h(x) for x in erf_x], "ehq": [[h(a), h(b)] for a, b in ehq], "zone": [[h(a), h(b)] for a, b in zone],
        "raw": [[h(r), p, None if q is None else h(q), h(m)] for r, p, q, m in raw]}
(ROOT / "out").mkdir(exist_ok=True)
gp = ROOT / "out" / "qte_fn_grid.json"; op = ROOT / "out" / "qte_fn_godot.json"
gp.write_text(json.dumps(grid))
godot = os.environ.get("GODOT", "/workspace/tools/godot")
subprocess.run([godot, "--headless", "--path", str(ROOT / "godot"), "--script", "res://scripts/headless_run.gd", "--",
                "x", "--qte-fn-test", str(gp), "--out", str(op)], capture_output=True, check=True)
g = json.loads(op.read_text())
sim = {"erf": [math.erf(x) for x in erf_x], "ehq": [E.expected_hit_quality(a, b) for a, b in ehq],
       "zone": [E.qte_zone_width(a, b) for a, b in zone], "raw": [E.raw_qte_score(r, profile=p, q_time=q, window_mod=m) for r, p, q, m in raw]}
# 2-ULP allowed only on unrounded intermediates. raw_qte_score must be bit-exact.
TOL_ULP = {"erf", "ehq", "zone"}
TOL_N = 2
worst = 0.0; bit_mis = 0; fail = 0; n = 0; ulp_ok = 0; worst_ulp = 0
by = {k: {"n": 0, "mis": 0, "ulp_ok": 0, "fail": 0, "worst": 0.0, "worst_ulp": 0} for k in sim}
for k in sim:
    for a, b in zip(sim[k], g[k]):
        n += 1; by[k]["n"] += 1; bv = d(b)
        if h(a) == b:
            continue
        bit_mis += 1; by[k]["mis"] += 1
        worst = max(worst, abs(a - bv)); by[k]["worst"] = max(by[k]["worst"], abs(a - bv))
        steps = ulp_distance(a, bv)
        if steps is not None:
            worst_ulp = max(worst_ulp, steps); by[k]["worst_ulp"] = max(by[k]["worst_ulp"], steps)
        if k in TOL_ULP and steps is not None and steps <= TOL_N:
            ulp_ok += 1; by[k]["ulp_ok"] += 1
        else:
            fail += 1; by[k]["fail"] += 1
ok = fail == 0
print(f"qte-v1 functions Godot vs sim: {n} values (erf {len(erf_x)}, expected_hit_quality {len(ehq)}, qte_zone_width {len(zone)}, raw_qte_score {len(raw)}), "
      f"bit mismatches={bit_mis} (of which {ulp_ok} within {TOL_N} ULP on erf/expected_hit_quality/qte_zone_width; raw_qte_score is exact) "
      f"max_abs_diff={worst:.3e} max_ulp={worst_ulp} fails={fail} -> {'PASS' if ok else 'FAIL'}")
if bit_mis or fail:
    for k in sim:
        s = by[k]
        print(f"  {k}: n={s['n']} mismatches={s['mis']} within_{TOL_N}ulp={s['ulp_ok']} fails={s['fail']} max_abs={s['worst']:.3e} max_ulp={s['worst_ulp']}")
sys.exit(0 if ok else 1)
