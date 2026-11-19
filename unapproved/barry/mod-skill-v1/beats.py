"""STORY-BEAT GATE draft (Barry, 2026-11-19, Austin direct): N required wild-encounter wins per round placed as story beats
(spread over the slots before kid2..boss), extra wild encounters optional, NO build check at the boss. NOT live.
Live sim (0.80 random AI QTE, boss r 1.046/1.040/1.050, Street boss 25/25/50, v2 tables), fixed layout PEE, approved
calibration (fixed_layout.json: ceilings 133/261/407, wild-encounter XP 13/12/14 = code grind_xp), walk_boss_flag fix.
Part 1: sweep N = 2..8. Part 2: boss r retune per round for N in 3..5 (min-path player: 60/60 >= 30, 80/80 <= 95) and
what a fully built player gets there. Part 3: ceiling mitigation. -> beats.json"""
import json, math, os
import fixed_layout as FL, walk as W, calibrate as CA
from velocity_shift import progression as P, equations as E

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "fixed_layout.json")))["configs"]["PEE"]
FL.use({"street": "P", "wangan": "E", "touge": "E"}); CA.SPILL, CA.KITS = True, None
assert (E.OPPONENT_QTE, E.BOSS_TARGET_R["street"], E.BOSS_STAT_SHARES["street"]) == (0.80, 1.046, (0.25, 0.25, 0.50))
CEIL0, CAP0 = tuple(W.CEIL), tuple(W.CAP_POWER)
CAPPTS = [3000 + 4 * c for c in CEIL0]
DIST = ("street", "wangan", "touge")
run = lambda m, **k: W.walk(m, 0.60, grind_xp=tuple(cfg["grind_xp"]), story_table=cfg["story_table"], price="mk1_list", spill=True, **k)


def summ(w):
    rows = w["rows"]; b = rows[-1]; o = dict(rnd=w["rnd"], wild_wins=w["total_grind"], boss_points=b["points"], boss_power=b["power"],
        boss_pow_share=b["pow_share"], boss_r=b["r"], boss6060=b["wr"]["c6060"], boss8080=b["wr"]["c8080"],
        low6060_nonboss=min(x["wr"]["c6060"] for x in rows[:-1]), low8080_nonboss=min(x["wr"]["c8080"] for x in rows[:-1]),
        money=w["money"], debt=w["debt"], spent=w["spent"], end_points=w["end_points"])
    for p in ("c6060", "c8080"):
        o["exp_races_" + p] = round(sum(100 / max(x["wr"][p], 0.05) for x in rows) + sum(100 / max(g[p], 0.05) for g in w["grind_wr"]), 1)
    return o


def boss_wr(r, d, ps):
    return {p: P.hard_win(P.win_pack(p, r, 30, d, ps, boss=True)) for p in ("c6060", "c8080")}


def r_window(d, ps):
    """Smallest r with 60/60 >= 30 and largest r with 80/80 <= 95 on the boss table (step 0.0005)."""
    grid = [round(0.950 + 0.0005 * i, 4) for i in range(401)]
    lo = next(r for r in grid if boss_wr(r, d, ps)["c6060"] >= 30.0)
    hi = max(r for r in grid if boss_wr(r, d, ps)["c8080"] <= 95.0)
    return lo, hi


res = dict(cap_points=CAPPTS, grind_xp=cfg["grind_xp"], sweep={}, today_story=[summ(w) for w in run("story")],
           today_mixed=[summ(w) for w in run("mixed")])
for N in range(2, 9):
    res["sweep"][N] = [summ(w) for w in run("beats", beats=N)]

# Part 2: retune. Min-path player = exactly N required wins; full build = every mod at the ceiling (mixed walk's boss row).
full = res["today_mixed"]
res["retune"] = {}
for N in (3, 4, 5):
    out = []
    for i, d in enumerate(DIST):
        m = res["sweep"][N][i]; lo, hi = r_window(d, m["boss_pow_share"] / 100)
        r_new = math.ceil(lo * 1000) / 1000                     # boss r for the min-path player, rounded up to 0.001
        B_new = m["boss_power"] / r_new                          # new boss budget (stat units)
        r_full = full[i]["boss_power"] / B_new
        out.append(dict(rnd=i + 1, min_points=m["boss_points"], min_power=m["boss_power"], r_window_min_path=[lo, hi],
                        boss_r_new=r_new, boss_budget_new=round(B_new, 2), boss_budget_live=round(m["boss_power"] / m["boss_r"], 2),
                        min_path=boss_wr(r_new, d, m["boss_pow_share"] / 100), full_points=full[i]["boss_points"],
                        full_r=round(r_full, 4), full_build=boss_wr(r_full, d, full[i]["boss_pow_share"] / 100)))
    res["retune"][N] = out

# Part 3: mitigation = lower each round's ceiling so a full build stays at 80/80 <= 95 against a boss retuned for the
# min-path player. Round by round (R2's min path depends on R1's ceiling through catch-up), iterated to a fixed point.
# Cap power follows the ceiling so the clamp and catch-up stay consistent. Boss budgets do not feed back into the walk.
def mitigate(N):
    ce = list(CEIL0)
    for i, d in enumerate(DIST):
        for _ in range(6):
            W.CEIL = tuple(ce); W.CAP_POWER = tuple((3000 + 4 * c) / 10 for c in ce)
            m = summ(run("beats", beats=N)[i]); lo, _ = r_window(d, m["boss_pow_share"] / 100)
            r_new = math.ceil(lo * 1000) / 1000; B = m["boss_power"] / r_new
            f = summ(run("mixed")[i]); _, hi_full = r_window(d, f["boss_pow_share"] / 100)
            c_new = min(CEIL0[i], math.floor((hi_full * B * 10 - 3000) / 4))
            if c_new == ce[i]:
                break
            ce[i] = c_new
    W.CEIL = tuple(ce); W.CAP_POWER = tuple((3000 + 4 * c) / 10 for c in ce)
    mp = [summ(w) for w in run("beats", beats=N)]; fb = [summ(w) for w in run("mixed")]
    W.CEIL, W.CAP_POWER = CEIL0, CAP0
    out = []
    for i, d in enumerate(DIST):
        lo, hi = r_window(d, mp[i]["boss_pow_share"] / 100); r_new = math.ceil(lo * 1000) / 1000; B = mp[i]["boss_power"] / r_new
        out.append(dict(rnd=i + 1, ceiling=ce[i], cap_points=3000 + 4 * ce[i], boss_r_new=r_new, boss_budget_new=round(B, 2),
                        min_path_points=mp[i]["boss_points"], min_path=boss_wr(r_new, d, mp[i]["boss_pow_share"] / 100),
                        full_points=fb[i]["boss_points"], full_r=round(fb[i]["boss_power"] / B, 4),
                        full=boss_wr(fb[i]["boss_power"] / B, d, fb[i]["boss_pow_share"] / 100),
                        headroom_points=fb[i]["boss_points"] - mp[i]["boss_points"], full_wild_wins=fb[i]["wild_wins"],
                        min_path_cash=mp[i]["money"], full_cash=fb[i]["money"], min_low6060=mp[i]["low6060_nonboss"],
                        min_exp=[mp[i]["exp_races_c6060"], mp[i]["exp_races_c8080"]]))
    return out


res["mitigation"] = {N: mitigate(N) for N in (3, 4, 5)}
# Part 4: alternative mitigation = optional wild encounters pay XP only for the first K extra wins per round (cash always).
# A player taking all K is a "K-extra" player (walk mode beats with N + K wins); boss budgets stay the Part 2 retune for N.
res["optional_xp_cap"] = {}
for N in (3, 4, 5):
    rt = res["retune"][N]; rows = []
    for K in range(0, 11):
        ws = [summ(w) for w in run("beats", beats=N + K)]
        rows.append(dict(K=K, rounds=[dict(rnd=i + 1, points=ws[i]["boss_points"], r=round(ws[i]["boss_power"] / rt[i]["boss_budget_new"], 4),
                                          wr=boss_wr(ws[i]["boss_power"] / rt[i]["boss_budget_new"], d, ws[i]["boss_pow_share"] / 100))
                                     for i, d in enumerate(DIST)]))
    kmax = [max(r["K"] for r in rows if r["rounds"][i]["wr"]["c8080"] <= 95.0) for i in range(3)]
    res["optional_xp_cap"][N] = dict(rows=rows, K_max_8080_le_95=kmax)

json.dump(res, open(os.path.join(HERE, "beats.json"), "w"), indent=1)

f = lambda s: "%d/%d pts r%.4f boss %.1f/%.1f low6060 %.1f exp %.1f/%.1f $%d debt %d" % (s["boss_points"], CAPPTS[s["rnd"] - 1], s["boss_r"], s["boss6060"], s["boss8080"], s["low6060_nonboss"], s["exp_races_c6060"], s["exp_races_c8080"], s["money"], s["debt"])
print("story ", " | ".join(f(s) for s in res["today_story"]))
print("mixed ", " | ".join(f(s) for s in res["today_mixed"]))
for N, ws in res["sweep"].items():
    print("N=%d  " % N, " | ".join(f(s) for s in ws))
for N, rt in res["retune"].items():
    print("retune N=%d" % N, [(x["boss_r_new"], x["r_window_min_path"], x["min_path"], x["full_r"], x["full_build"]) for x in rt])
for N, m in res["mitigation"].items():
    print("mitig N=%d" % N, [(x["ceiling"], x["cap_points"], x["boss_r_new"], x["boss_budget_new"], x["min_path_points"], x["min_path"], x["full_r"], x["full"], x["full_wild_wins"], x["min_exp"]) for x in m])
for N, o in res["optional_xp_cap"].items():
    print("xpcap N=%d Kmax" % N, o["K_max_8080_le_95"], [(r["K"], [(x["points"], x["r"], x["wr"]["c6060"], x["wr"]["c8080"]) for x in r["rounds"]]) for r in o["rows"][:7]])
