#!/usr/bin/env python3
"""Bit-identity: Godot py_random.gauss + AI QTE draw vs CPython random.Random / match.py (live sim).

Usage: python3 tools/touge_race/ai_qte_check.py
Needs /workspace/tools/godot. SIM_PATH / SIM_PIN select the live sim when this worktree's sim/ is behind.
"""
import json, math, os, random, statistics, struct, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

def sim_path():
    for c in (os.environ.get("SIM_PATH"), str(REPO / ".out" / "sim-live"), str(REPO / "sim")):
        if not c:
            continue
        p = Path(c).resolve()
        if (p / "velocity_shift").is_dir():
            return p
        if (p / "sim" / "velocity_shift").is_dir():
            return p / "sim"
    return REPO / "sim"

SIM = sim_path()
sys.path.insert(0, str(SIM))
from velocity_shift import equations as E  # noqa: E402
from velocity_shift.models import MatchConfig  # noqa: E402
from velocity_shift.match import opponent_qte_mean, opponent_qte_spread  # noqa: E402

hexf = lambda x: "0x%016x" % (struct.unpack("<Q", struct.pack("<d", float(x)))[0])
GODOT = os.environ.get("GODOT", "/workspace/tools/godot")
OUT = REPO / ".out"
OUT.mkdir(exist_ok=True)


def godot(flag, inp, outp):
    subprocess.run(
        [GODOT, "--headless", "--path", str(REPO), "--script", "res://scripts/headless_run.gd", "--",
         "x", flag, str(inp), "--out", str(outp)],
        check=True, capture_output=True, text=True,
    )


def check_gauss():
    seeds = [0, 1, 42, 20261119, 20261119 + E.OPPONENT_QTE_SEED_OFFSET, 10**9, 2**31 - 1]
    cases = [{"seed": s, "mu": 0.80, "sd": 0.08, "n": 40} for s in seeds]
    cases += [{"seed": s, "mu": 0.0, "sd": 1.0, "n": 20} for s in (7, 99, 104729)]
    inp = OUT / "gauss_in.json"
    outp = OUT / "gauss_godot.json"
    inp.write_text(json.dumps({"cases": cases}))
    godot("--gauss-test", inp, outp)
    got = {c["seed"]: c for c in json.loads(outp.read_text())["cases"]}
    bad = 0
    n = 0
    for c in cases:
        r = random.Random(c["seed"])
        exp = [hexf(r.gauss(c["mu"], c["sd"])) for _ in range(c["n"])]
        g = got[c["seed"]]["draws"]
        n += len(exp)
        if exp != g:
            bad += sum(a != b for a, b in zip(exp, g))
            for i, (a, b) in enumerate(zip(exp, g)):
                if a != b and bad <= 5:
                    print("GAUSS MISMATCH seed", c["seed"], "i", i, "py", a, "godot", b)
    print("GAUSS bit-identity %s: %d/%d draws match (CPython Random.gauss vs py_random.gd)" % (
        "PASS" if bad == 0 else "FAIL", n - bad, n))
    return bad == 0, n, bad


def check_ai_qte():
    seeds = [1, 42, 20261119, 7777777, 123456789]
    cases = [{"seed": s, "ratio": 1.0, "n": 10} for s in seeds]
    cases += [{"seed": 20261119, "ratio": 0.9, "n": 10}, {"seed": 7, "ratio": 1.0, "sd": 0.0, "n": 5}]
    inp = OUT / "ai_qte_in.json"
    outp = OUT / "ai_qte_godot.json"
    inp.write_text(json.dumps({"cases": cases}))
    godot("--ai-qte-test", inp, outp)
    got = json.loads(outp.read_text())["cases"]
    bad = 0
    n = 0
    for c, g in zip(cases, got):
        cfg = MatchConfig(
            None, None, seed=c["seed"],
            opponent_qte_ratio=c.get("ratio"),
            opponent_qte_sd=c.get("sd"),
        )
        mean = opponent_qte_mean(cfg)
        sd, lo, hi = opponent_qte_spread(cfg)
        if "sd" in c and c["sd"] == 0.0:
            sd = 0.0
        if sd > 0.0:
            rng = random.Random(c["seed"] + E.OPPONENT_QTE_SEED_OFFSET)
            exp = [hexf(E.round_qte_score(min(hi, max(lo, rng.gauss(mean, sd))))) for _ in range(c["n"])]
        else:
            exp = [hexf(mean)] * c["n"]
        n += len(exp)
        if exp != g["qte"]:
            bad += sum(a != b for a, b in zip(exp, g["qte"]))
            if bad <= 5:
                print("AI QTE MISMATCH seed", c["seed"], "ratio", c.get("ratio"), "sd", c.get("sd"))
                print(" py   ", exp)
                print(" godot", g["qte"])
    print("AI QTE sequence %s: %d/%d scores bit-identical (match.py formula vs Godot)" % (
        "PASS" if bad == 0 else "FAIL", n - bad, n))
    return bad == 0, n, bad


def stats_report():
    """If bit-identity failed, still report mean/sd/clamp over many draws (statistical parity)."""
    n = 20000
    seed = 20261119
    mu, sd, lo, hi = E.OPPONENT_QTE, E.OPPONENT_QTE_SD, E.OPPONENT_QTE_MIN, E.OPPONENT_QTE_MAX
    r = random.Random(seed + E.OPPONENT_QTE_SEED_OFFSET)
    py = [min(hi, max(lo, r.gauss(mu, sd))) for _ in range(n)]  # pre-round, for distro shape
    # Godot: request n raw gauss draws at mu,sd then we'll clamp in python... better get raw from --gauss-test
    inp = OUT / "gauss_stat_in.json"
    outp = OUT / "gauss_stat_godot.json"
    inp.write_text(json.dumps({"cases": [{"seed": seed + E.OPPONENT_QTE_SEED_OFFSET, "mu": mu, "sd": sd, "n": n}]}))
    godot("--gauss-test", inp, outp)
    unhex = lambda h: struct.unpack("<d", struct.pack("<Q", int(h, 16)))[0]
    gd = [unhex(x) for x in json.loads(outp.read_text())["cases"][0]["draws"]]
    # Compare the unclamped gauss stream first (bit identity of gauss itself)
    r2 = random.Random(seed + E.OPPONENT_QTE_SEED_OFFSET)
    py_raw = [r2.gauss(mu, sd) for _ in range(n)]
    bit = sum(hexf(a) == hexf(b) for a, b in zip(py_raw, gd))
    py_c = [E.round_qte_score(min(hi, max(lo, x))) for x in py_raw]
    gd_c = [E.round_qte_score(min(hi, max(lo, x))) for x in gd]
    def sumry(xs):
        return dict(mean=statistics.fmean(xs), sd=statistics.pstdev(xs),
                    floor=sum(x <= lo + 1e-15 for x in xs) / len(xs),
                    ceil=sum(x >= hi - 1e-15 for x in xs) / len(xs))
    sp, sg = sumry(py_c), sumry(gd_c)
    print("STAT n=%d seed+offset %d: gauss bit-identical %d/%d" % (n, seed + E.OPPONENT_QTE_SEED_OFFSET, bit, n))
    print("  py    mean=%.6f sd=%.6f floor=%.4f ceil=%.4f" % (sp["mean"], sp["sd"], sp["floor"], sp["ceil"]))
    print("  godot mean=%.6f sd=%.6f floor=%.4f ceil=%.4f" % (sg["mean"], sg["sd"], sg["floor"], sg["ceil"]))
    print("  |dmean|=%.3e |dsd|=%.3e" % (abs(sp["mean"] - sg["mean"]), abs(sp["sd"] - sg["sd"])))
    return bit == n


def main():
    print("sim", SIM, "OPPONENT_QTE", E.OPPONENT_QTE, "SD", E.OPPONENT_QTE_SD, "offset", E.OPPONENT_QTE_SEED_OFFSET)
    ok_g, _, _ = check_gauss()
    ok_q, _, _ = check_ai_qte()
    if not (ok_g and ok_q):
        stats_report()
    sys.exit(0 if ok_g and ok_q else 1)


if __name__ == "__main__":
    main()
