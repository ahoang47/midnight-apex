#!/usr/bin/env python3
"""Touge race parity: sim match.run_match (truth) vs Godot RaceCore (headless_run.gd). Gordon [godot], touge-race.

For N seeds: random wanted stances + random Entry/Apex/Exit scores (some unplayed) drive the SIM; the stances the sim
actually played (locked gauges -> least-loaded fallback in this harness, limp forced by the engine) and the exact phase
scores (IEEE-754 hex) go to Godot, which must reproduce every turn's progress and both totals bit for bit.
Stats: the TODO(barry) even, equal placeholder (POW = HAN = EN = 1 both sides), same as globals.gd.
Touge passing (sim 5c79dea): Touge is per-phase (each clash its own smoothed phase QTE, 3 AI draws per turn); every turn's
per-clash QTEs (both sides) and the order after each phase (TurnResult.phase_order) must match too. --per-turn forces
MatchConfig.per_phase False on both sides (the Street / Wangan per-turn path, which must stay bit-identical).
Usage: python3 tools/touge_race/parity_touge.py [N] [--per-turn]   (needs /workspace/tools/godot; run from anywhere)
"""
import json, os, random, struct, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]; GD = REPO
# Prefer a live sim checkout when the worktree's sim/ is behind origin (do not pull this worktree).
def _sim_path():
    cands = [os.environ.get("SIM_PATH"), str(REPO / ".out" / "sim-live"), str(REPO / "sim")]
    for c in cands:
        if not c: continue
        p = Path(c).resolve()
        if (p / "velocity_shift").is_dir(): return p
        if (p / "sim" / "velocity_shift").is_dir(): return p / "sim"
    return REPO / "sim"
SIM = _sim_path()
sys.path.insert(0, str(SIM))
from velocity_shift.models import CombatantStats, MatchConfig, Stance  # noqa
from velocity_shift.match import run_match  # noqa
_pin_file = REPO / ".out" / "sim-live.pin"
SIM_PIN = os.environ.get("SIM_PIN") or (_pin_file.read_text().strip() if _pin_file.is_file() else subprocess.check_output(
    ["git", "-C", str(REPO), "log", "-1", "--format=%h", "--", "sim/"], text=True).strip())

CFG = json.loads((GD / "spec" / "race_config.json").read_text())
LET = {Stance.POW: "P", Stance.HAN: "H", Stance.EN: "E"}; STA = {v: k for k, v in LET.items()}
hexf = lambda x: "0x%016x" % (struct.unpack("<Q", struct.pack("<d", x))[0])

import argparse
BLOCKS = "unapproved/barry/touge-race-parity/blocks.json"
BLOCKS_PIN = "fd59332"
unhex = lambda h: None if h is None else (struct.unpack("<d", struct.pack("<Q", int(h, 16)))[0] if isinstance(h, str) else float(h))
def stats_for(car, use_draft):
    if not use_draft: return (1.0, 1.0, 1.0)
    pin = BLOCKS_PIN   # Austin: read the blocks at fd59332 (same pin as tools/touge_race/gen_globals.py -> globals.gd CAR_BLOCKS_PIN)
    b = json.loads(subprocess.check_output(["git", "-C", str(REPO), "show", "%s:%s" % (pin, BLOCKS)], text=True))["cars"][car]
    return (float(b["pow"]), float(b["en"]), float(b["han"]))
PS = OS_ = None
PER_TURN = "--per-turn" in sys.argv
def _pp(): return {"per_phase": False} if PER_TURN else {}

def sim_race(seed, rnd):
    want = [[rnd.choice("PHE") for _ in range(3)] for _ in range(CFG["max_turns"])]
    qte = [[None if rnd.random() < 0.15 else rnd.random() for _ in range(3)] for _ in range(CFG["max_turns"])]
    def stance(turn, ci, ctx):
        w = STA[want[turn - 1][ci]]
        return w if ctx.gauges.selectable(w) else ctx.gauges.least_loaded(True)
    cfg = MatchConfig(CombatantStats("Player", *PS), CombatantStats("Opponent", *OS_), max_turns=CFG["max_turns"], seed=seed,
                      district=CFG["district"], corners=[c["corner"] for c in CFG["corners"]], qte_window_mod=CFG["qte_window_mod"],
                      opponent_qte_ratio=CFG.get("opponent_qte_ratio"),
                      opponent_qte_sd=CFG.get("opponent_qte_sd"), opponent_qte_min=CFG.get("opponent_qte_min"),
                      opponent_qte_max=CFG.get("opponent_qte_max"), **_pp())
    res = run_match(cfg, stance, lambda t: tuple(qte[t - 1]))
    corners = [{"pick": "".join(LET[s] for s in tr.player_stances), "qte": [None if v is None else hexf(v) for v in qte[i]]}
               for i, tr in enumerate(res.turn_results)]
    truth = {"turns": [[hexf(tr.player_progress), hexf(tr.opponent_progress)] for tr in res.turn_results],
             "player_total": hexf(res.player_total_progress), "opponent_total": hexf(res.opponent_total_progress), "winner": res.winner,
             "limp": sum(any(tr.player_limp) for tr in res.turn_results),
             "phase": [{"p_qte": [hexf(v) for v in tr.player_clash_qte], "o_qte": [hexf(v) for v in tr.opponent_clash_qte],
                        "order": list(tr.phase_order)} for tr in res.turn_results],
             "passes": sum(1 for tr in res.turn_results for a, b in zip(["opponent"] + tr.phase_order, tr.phase_order) if a != b and "even" not in (a, b))}
    return {"seed": seed, "corners": corners}, truth

def game_check(path):
    """--game-result <touge_result.json>: the windowed game's own race (main.gd _run_touge_script) replayed in the sim with the
    stances the game played and the same phase scores; every turn and both totals must match bit for bit."""
    global PS, OS_
    g = json.loads(Path(path).read_text())
    PS = stats_for(g["player_car"], g["use_draft_blocks"]); OS_ = stats_for(g["opp_car"], g["use_draft_blocks"])
    want = [c["pick"] for c in g["corners"]]
    qte = [[None if v is None else unhex(v) if isinstance(v, str) else float(v) for v in c["qte"]] for c in g["corners"]]
    def stance(turn, ci, ctx):
        w = STA[want[turn - 1][ci]]
        return w if ctx.gauges.selectable(w) else ctx.gauges.least_loaded(True)
    cfg = MatchConfig(CombatantStats("Player", *PS), CombatantStats("Opponent", *OS_), max_turns=CFG["max_turns"], seed=g["seed"],
                      district=CFG["district"], corners=[c["corner"] for c in CFG["corners"]], qte_window_mod=CFG["qte_window_mod"],
                      opponent_qte_ratio=CFG.get("opponent_qte_ratio"),
                      opponent_qte_sd=CFG.get("opponent_qte_sd"), opponent_qte_min=CFG.get("opponent_qte_min"),
                      opponent_qte_max=CFG.get("opponent_qte_max"))
    res = run_match(cfg, stance, lambda t: tuple(qte[t - 1]))
    turns_ok = all(hexf(tr.player_progress) == c["p"] and hexf(tr.opponent_progress) == c["o"] and "".join(LET[s] for s in tr.player_stances) == c["pick"]
                   and "".join(LET[s] for s in tr.opponent_stances) == c["rival"] for tr, c in zip(res.turn_results, g["corners"]))
    # Touge passing: the order the game drew after each phase must be the sim's phase_order
    turns_ok = turns_ok and all(c.get("phase_order", []) == list(tr.phase_order) for tr, c in zip(res.turn_results, g["corners"]))
    tot_ok = hexf(res.player_total_progress) == g["player_total"] and hexf(res.opponent_total_progress) == g["opponent_total"]
    win_ok = res.winner == g["winner"]
    # Austin t119u: the gauges the game drew after each turn must be the sim's TurnResult.player_heat_fill (bit for bit, and the
    # drawn bar = clamp(fill, 0, 1))
    heat_ok = all(c.get("heat_fill") == [hexf(v) for v in tr.player_heat_fill] for tr, c in zip(res.turn_results, g["corners"]))
    drawn_ok = all(abs(float(c["heat_drawn"][k]) - min(1.0, max(0.0, tr.player_heat_fill[i]))) < 1e-6
                   for tr, c in zip(res.turn_results, g["corners"]) if c.get("heat_drawn") for k, i in (("P", 0), ("H", 1), ("E", 2)))
    print("GAUGES vs SIM %s: post-turn fill %s, drawn bars %s" % ("PASS" if heat_ok and drawn_ok else "FAIL", "ok" if heat_ok else "MISMATCH", "ok" if drawn_ok else "MISMATCH"))
    win_ok = win_ok and heat_ok and drawn_ok
    print("GAME vs SIM %s: seed %d %s vs %s; turns + phase order %s, totals %s, winner %s (sim %s, game %s)" % (
        "PASS" if turns_ok and tot_ok and win_ok else "FAIL", g["seed"], g["player_car"], g["opp_car"],
        "ok" if turns_ok else "MISMATCH", "ok" if tot_ok else "MISMATCH", "ok" if win_ok else "MISMATCH", res.winner, g["winner"]))
    sys.exit(0 if turns_ok and tot_ok and win_ok else 1)

def main():
    global PS, OS_
    if "--game-result" in sys.argv: game_check(sys.argv[sys.argv.index("--game-result") + 1]); return
    ap = argparse.ArgumentParser(); ap.add_argument("n", nargs="?", type=int, default=300)
    ap.add_argument("--no-draft-blocks", action="store_true"); ap.add_argument("--per-turn", action="store_true"); ap.add_argument("--player-car"); ap.add_argument("--opp-car")
    a = ap.parse_args(); n = a.n
    use = CFG.get("use_draft_blocks", False) and not a.no_draft_blocks
    pc = a.player_car or CFG["player"]["car"]; oc = a.opp_car or CFG["opponent"]["car"]
    PS = stats_for(pc, use); OS_ = stats_for(oc, use)
    extra = (["--no-draft-blocks"] if a.no_draft_blocks else []) + (["--per-turn"] if PER_TURN else []) + ["--player-car", pc, "--opp-car", oc]
    rnd = random.Random(20261119)
    races, truths = [], []
    for i in range(n):
        r, t = sim_race(1 + rnd.randrange(10**9), rnd); races.append(r); truths.append(t)
    inp = Path("/tmp/touge_parity_in.json"); out = Path("/tmp/touge_parity_out.json")
    inp.write_text(json.dumps({"races": races}))
    subprocess.run(["/workspace/tools/godot", "--headless", "--path", str(GD), "--script", "res://scripts/headless_run.gd", "--",
                    str(inp), "--out", str(out)] + extra, check=True, capture_output=True)
    got = json.loads(out.read_text())["races"]
    bad = 0
    for t, g in zip(truths, got):
        ok = t["turns"] == g["turns"] and t["phase"] == g["phase"] and t["player_total"] == g["player_total"] and t["opponent_total"] == g["opponent_total"] and \
             {"Player": "P", "Tie": "Tie"}.get(t["winner"], "O") == {"Player": "P", "Tie": "Tie"}.get(g["winner"], "O")
        bad += not ok
        if not ok and bad <= 3: print("MISMATCH seed", g["seed"], "\n sim ", t, "\n godot", g)
    wins = sum(t["winner"] == "Player" for t in truths); limps = sum(t["limp"] for t in truths)
    passes = sum(t["passes"] for t in truths)
    print("TOUGE PARITY %s [%s vs %s, %s, %s]: %d/%d races bit-identical incl. per-clash QTE + phase order (sim %s at %s); player wins %d, turns with limp %d, phase lead changes %d" % (
        "PASS" if bad == 0 else "FAIL", pc, oc, "blocks.json" if use else "placeholder", "per-turn forced" if PER_TURN else "per-phase by district",
        n - bad, n, SIM_PIN[:7], SIM, wins, limps, passes))
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
