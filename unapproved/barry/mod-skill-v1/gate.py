"""GATE draft (Barry, 2026-11-19, Austin direct): Pokemon-style required grinding for mod_skill. NOT live.
Gate = the round boss is locked until every kit mod is at the round ceiling (car points 3532 / 4044 / 4628).
Runs the fixed layout (POW/HAN/EN + flex, PEE), the APPROVED calibration in fixed_layout.json (story table, grind XP
13/12/14), on the LIVE sim (0.80 random AI QTE, boss r 1.046/1.040/1.050, Street boss 25/25/50, v2 tables) with the
walk_boss_flag.patch fix applied to walk.py. Modes: story / mixed / hard (today) and gate. -> gate.json"""
import json, os
import fixed_layout as FL, walk as W, calibrate as CA
from velocity_shift import equations as E

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "fixed_layout.json")))["configs"]["PEE"]
FL.use({"street": "P", "wangan": "E", "touge": "E"}); CA.SPILL, CA.KITS = True, None
assert (E.OPPONENT_QTE, E.BOSS_TARGET_R["street"], E.BOSS_STAT_SHARES["street"]) == (0.80, 1.046, (0.25, 0.25, 0.50)), "not the live sim"


def summ(w):
    rows = w["rows"]; boss = rows[-1]; out = dict(
        rnd=w["rnd"], grind=w["total_grind"], boss6060=boss["wr"]["c6060"], boss8080=boss["wr"]["c8080"], boss_r=boss["r"],
        boss_points=boss["points"], low8080_nonboss=min(x["wr"]["c8080"] for x in rows[:-1]),
        low6060_nonboss=min(x["wr"]["c6060"] for x in rows[:-1]), end_points=w["end_points"], money=w["money"],
        debt=w["debt"], spent=w["spent"], xp_lost=w["xp_lost"], max_tune_dist=w["max_tune_dist"],
        boss_attempts_6060=round(100 / max(boss["wr"]["c6060"], 1e-9), 1), boss_attempts_8080=round(100 / max(boss["wr"]["c8080"], 1e-9), 2))
    for p in ("c6060", "c8080"):   # expected races / turns per round if a loss means retry (story rungs and grinds alike)
        ra = [100 / max(x["wr"][p], 0.05) for x in rows]; ga = [100 / max(g[p], 0.05) for g in w["grind_wr"]]
        out["exp_races_" + p] = round(sum(ra) + sum(ga), 1)
        out["exp_turns_" + p] = round(sum(a * x["turns"] for a, x in zip(ra, rows)) + 10 * sum(ga))
    out["rungs"] = [dict(rung=x["rung"], grind=x["grind"], points=x["points"], r=x["r"], wr6060=x["wr"]["c6060"], wr8080=x["wr"]["c8080"]) for x in rows]
    t = w.get("gate_trace")
    if t:
        out["gate_grinds"] = len(t) - 1
        out["gate_grind_attempts"] = {p: round(sum(100 / t[i]["grind"][p] for i in range(len(t) - 1)), 1) for p in ("c6060", "c8080")}
        out["points_short_at_boss"] = round(t[-1]["points"] - t[0]["points"], 1)
        out["boss_ungated"] = t[0]["boss"]
        ok = [x for x in t if x["boss"]["c6060"] >= 30 and x["boss"]["c8080"] <= 95]
        out["min_gate"] = dict(n=ok[0]["n"], points=ok[0]["points"], boss=ok[0]["boss"]) if ok else None
        out["trace"] = t
    return out


res = dict(ceil=list(FL.MS.CEIL), cap_points=[3000 + 4 * c for c in FL.MS.CEIL], grind_xp=cfg["grind_xp"], walks={})
run = lambda m, **k: W.walk(m, 0.60, grind_xp=tuple(cfg["grind_xp"]), story_table=cfg["story_table"], price="mk1_list", spill=True, **k)
for m in ("story", "mixed", "hard", "gate"):
    res["walks"][m] = [summ(w) for w in run(m)]
# option B: + a mid-round gate at the mixed walk's wall rung, threshold = the mixed player's car points there (derived, not picked)
GA = {}
for w in run("mixed"):
    j, x = next((j, x) for j, x in enumerate(w["rows"][:-1]) if x["grind"] > 0); GA[(w["rnd"] - 1, j)] = x["points"] - 0.5   # rows hold rounded points; -0.5 = "displays as >= that number"
res["gate_b_mid"] = {f"R{k[0] + 1} {W.E.LADDER_RUNGS[k[1]]}": v + 0.5 for k, v in GA.items()}
res["walks"]["gate_b"] = [summ(w) for w in run("gate", gate_pts=GA)]
print("gate B mid thresholds", res["gate_b_mid"])
json.dump(res, open(os.path.join(HERE, "gate.json"), "w"), indent=1)
for m, ws in res["walks"].items():
    print(m)
    for s in ws:
        print("  R%d grind %d boss %.1f/%.1f r %.4f pts %d low8080 %.1f low6060 %.1f end %d $%d debt %d spent %d" % (
            s["rnd"], s["grind"], s["boss6060"], s["boss8080"], s["boss_r"], s["boss_points"], s["low8080_nonboss"], s["low6060_nonboss"],
            s["end_points"], s["money"], s["debt"], s["spent"]), "exp races 60/80:", s["exp_races_c6060"], s["exp_races_c8080"], "turns", s["exp_turns_c6060"], s["exp_turns_c8080"], {k: s[k] for k in ("gate_grind_attempts", "boss_ungated", "min_gate", "points_short_at_boss") if k in s})
