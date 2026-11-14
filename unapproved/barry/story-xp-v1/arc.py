"""Arc/finale walk for story-xp-v1: econ-v1 draft arc walker (via econ-v1-live-tracks/core.py, live 6d3641f constants,
fixed live arc budgets) with (a) 80/80 arc entry level/bag and mixed/hard entry cash taken from the patched live
campaign walk, (b) arc story fill = ARC_STORY_FILL x arc multiplier (optionally per step). Draft only."""
import os, sys, copy
os.environ.setdefault("HARD_WANGAN", "W3_C1_Outer"); os.environ.setdefault("HARD_TOUGE", "T3_Usui_Esses")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "econ-v1-live-tracks"))
sys.path.insert(1, os.path.join(HERE, "..", "econ-v1"))
import core
import camp
import oracle
oracle.track_wr = lambda pr, r, T, name: camp.P._track_win(pr, r, T, name)   # live table (6d3641f)
M, MODS = core.setup()
A = MODS["run_finale_arc"]
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    BASE_ENT = A.entry_states()
BASE_CAMP = camp.summary(camp.run_all(camp.uniform((1, 1, 1))))
MODE = {"c8080": "story", "c6080": "mixed", "c8060": "mixed", "c6060": "hard"}

def entries_for(camp_sum):
    ent = {}
    for pr, e in BASE_ENT.items():
        s = copy.deepcopy(e); m = MODE[pr]
        r3n, r3b = camp_sum[m][2], BASE_CAMP[m][2]
        if m == "story":
            s.L = r3n["L_end"]
        s.money += r3n["money"] - r3b["money"]   # extra grind purses (live walk banks, draft shops; delta only)
        ent[pr] = s
    return ent

def run(camp_sum, arc_mult=1.0):
    # arc_mult: scalar, 4 per-step values, or {race id: multiplier}
    races = core.arc_races(core.LIVE_ARC, M, fill=core.LIVE.ARC_STORY_FILL)
    for rc in races:
        if isinstance(arc_mult, dict):
            rc["fill"] = rc["fill"] * arc_mult.get(rc["id"], 1.0)
        else:
            am = arc_mult if isinstance(arc_mult, (list, tuple)) else [arc_mult] * 4
            rc["fill"] = rc["fill"] * am[rc["step"]]
    ent = entries_for(camp_sum)
    _, walks, ev = core.run_arc(MODS, races, ent)
    return walks, ev

def brief(walks):
    out = {}
    for w in walks:
        out[w["pr"]] = dict(end_L=w["end_L"], end_money=w["end_money"], t4_done=w["t4_done"],
                            grind=[w["grind"][i]["total"] for i in range(4)],
                            billed=[x["wr_hard"] for x in w["log"] if x["billed"]],
                            billed_L=[x["L"] for x in w["log"] if x["billed"]],
                            min_story=min((x["wr_hard"], x["id"]) for x in w["log"] if not x["billed"]),
                            log=[(x["id"], x["L"], x["wr_hard"]) for x in w["log"]])
    return out

if __name__ == "__main__":
    print({pr: (e.L, round(e.money, 1)) for pr, e in BASE_ENT.items()})
    w, ev = run(BASE_CAMP)
    for pr, b in brief(w).items(): print(pr, b)
    print(ev.get("issues"))
