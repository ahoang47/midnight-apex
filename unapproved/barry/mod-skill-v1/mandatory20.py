"""MANDATORY-20 draft (Barry, 2026-11-19, Austin direct: "I want a mandatory 20 races per round"). NOT live.
Mandatory races per round = 7 story races (E.LADDER_RUNGS) + N required wild-encounter wins (story beats), N = 20 - 7 = 13.
"20 races" = 20 required WINS (race slots); a loss is a retry, not counted. Same setup as beats.py (live sim, fixed layout PEE,
approved calibration, walk_boss_flag fix). Also: min N per round that reaches the cap, and the R3 XP that lands the cap on the
13th win. Engine numbers at the resulting boss r are in gate_engine_check.json (identical inputs). -> mandatory20.json"""
import json, os
import beats as B, walk as W
from velocity_shift import equations as E

HERE = os.path.dirname(os.path.abspath(__file__))
STORY = len(E.LADDER_RUNGS); N = 20 - STORY
run = lambda beats, gx=None: W.walk("beats", 0.60, grind_xp=tuple(gx or B.cfg["grind_xp"]), story_table=B.cfg["story_table"],
                                     price="mk1_list", spill=True, beats=beats)
ws = run(N)
out = dict(story_races_per_round=STORY, rungs=list(E.LADDER_RUNGS), turns=list(E.LADDER_TURNS), N=N, cap_points=B.CAPPTS,
           rounds=[dict(B.summ(w), at_cap_at_boss=w["rows"][-1]["points"] >= B.CAPPTS[i], xp_lost=w["xp_lost"],
                        rungs=[dict(rung=x["rung"], beats_before=x["grind"], points=x["points"], wr6060=x["wr"]["c6060"], wr8080=x["wr"]["c8080"]) for x in w["rows"]])
                   for i, w in enumerate(ws)])
mins = []
for i in range(3):
    for n in range(1, N + 1):
        Ns = [N] * 3; Ns[i] = n
        if run(tuple(Ns))[i]["rows"][-1]["points"] >= B.CAPPTS[i]:
            mins.append(n); break
out["min_N_to_cap"] = mins; out["cash_only_wins"] = [N - m for m in mins]
r3 = next(x / 10 for x in range(80, 141) if run(N, (13, 12, x / 10))[2]["rows"][-1]["points"] >= B.CAPPTS[2])
out["r3_xp_cap_on_13th"] = r3
w10 = run((10, N, N))[0]["rows"][-1]
out["alt_prologue_counted_R1_N10"] = dict(points=w10["points"], wr6060=w10["wr"]["c6060"], wr8080=w10["wr"]["c8080"])
json.dump(out, open(os.path.join(HERE, "mandatory20.json"), "w"), indent=1)
for s in out["rounds"]:
    print(s["rnd"], s["boss_points"], s["boss_r"], s["boss6060"], s["boss8080"], s["low6060_nonboss"], s["exp_races_c6060"], s["exp_races_c8080"], s["money"], s["debt"], s["at_cap_at_boss"])
print("min N to cap", mins, "cash-only", out["cash_only_wins"], "R3 xp for cap on 13th", r3, "prologue-alt", out["alt_prologue_counted_R1_N10"])
