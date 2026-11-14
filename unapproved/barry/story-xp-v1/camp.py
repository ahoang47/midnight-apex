"""story-xp-v1 (draft, Barry): campaign walk on live progression (6d3641f) with story-XP multipliers.
mult[rnd][rung] scales E.story_xp for that rung. In-memory patch only; sim/ is not edited."""
import os, sys, json
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "sim"))
from velocity_shift import equations as E, progression as P
_orig = E.story_xp
PR = P.PROFILES

def run_all(mult):
    def sx(rnd, rung, enter, cap):
        return mult[rnd][rung] * _orig(rnd, rung, enter, cap)
    E.story_xp = sx
    try:
        return {m: P.run(m) for m in ("story", "mixed", "hard")}
    finally:
        E.story_xp = _orig

def summary(res):
    out = {}
    for m, rnds in res.items():
        rr = []
        for w in rnds:
            rows = w["rows"]
            b = rows[-1]
            rr.append(dict(wall=w["wall"], wall_grind=w["wall_grind"], post=w["post_wall_to_cap"], total=w["total_grind"],
                           L_end=w["L"], cap=w["reached_cap"], money=round(w["money"], 2), debt=round(w["debt"], 2),
                           boss_L=b["arrive_L"], boss_r=b["arrive_r"],
                           boss={pr: P.hard_win(b["wr"][pr]) for pr in PR},
                           levels=[x["arrive_L"] for x in rows],
                           min8080=min((P.hard_win(x["wr"]["c8080"]), x["rung"]) for x in rows),
                           rung8080=[P.hard_win(x["wr"]["c8080"]) for x in rows],
                           grind10={pr: rows[0]["grind10"][pr] for pr in PR}))
        out[m] = rr
    return out

def uniform(m):
    return [[m[i]] * 7 for i in range(3)]

if __name__ == "__main__":
    s = summary(run_all(uniform((1, 1, 1))))
    for m, rr in s.items():
        for i, x in enumerate(rr): print(m, i + 1, json.dumps(x))
