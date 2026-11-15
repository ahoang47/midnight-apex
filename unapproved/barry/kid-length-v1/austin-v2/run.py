"""kid-length-v1 / austin-v2 (draft, Barry 2026-11-14). Austin: kid races 20 turns WITHOUT fix K; no finite pool;
grinds unlimited and XP-limited only: a grind keeps paying good XP right up to the stage cap, nothing past it.
Base = live mods-v1 + xp-carry fix C. Grinds stay on their own opponent at today's kid1 strength (no fix K, so the
kid1 budget is unchanged). Grind falloff: taper floor GRIND_TAPER_FLOOR 0.20 -> F (1.0 = flat 0.70 level per grind).
Arc grinds (econ-v1 walker) get the same floor through its EconParams. In memory only. Run from sim/:
PYTHONPATH=.:../unapproved/barry/kid-length-v1:../unapproved/barry/xp-carry-v1:../unapproved/barry/mods-v1:../unapproved/barry/skill-points-v1 python3 ../unapproved/barry/kid-length-v1/austin-v2/run.py"""
import json, os, contextlib
import carry as C, kidlen as KL, verify_live as V
from velocity_shift import equations as E, progression as P
HERE = os.path.dirname(os.path.abspath(__file__))
A = V.A

@contextlib.contextmanager
def arc_floor(f):
    p = A.XP; old = p.grind_taper_floor
    try:
        if f is not None: p.grind_taper_floor = f
        yield
    finally: p.grind_taper_floor = old

def lv(f, d):
    return round(E.GRIND_FRAC * (f + (1 - f) * (1 - __import__("math").exp(-d / E.GRIND_TAPER_TAU))), 3)

def run(name, patch, floor):
    p = dict(patch)
    if floor is not None: p["GRIND_TAPER_FLOOR"] = floor
    with C.patched(**p), arc_floor(floor):
        o = C.summary(True)
        caps = P.boss_check_at_cap()
        arc = V.arc_walk({m: (o[m]["out"], o[m]["G"], o[m]["done"]) for m in o})
    res = dict(name=name, floor=floor, at_cap=[(c["c6060"], c["c8080"]) for c in caps], arc=arc)
    for m in ("story", "mixed", "hard"):
        out = o[m]["out"]
        res[m] = dict(
            grinds=[w["total_grind"] for w in out], wall=[w["wall_grind"] for w in out], wall_at=[w["wall"] for w in out],
            post=[w["post_wall_to_cap"] for w in out], reached_cap=[w["reached_cap"] for w in out],
            boss_L=[w["rows"][-1]["arrive_L"] for w in out], enter=[w["rows"][0]["arrive_L"] for w in out],
            per_rung=[[(r["rung"], r["grind_here"] + r["pre_boss_grind"]) for r in w["rows"] if r["grind_here"] + r["pre_boss_grind"]] for w in out],
            kid_grinds=[sum(r["grind_here"] for r in w["rows"][:2]) for w in out],
            kid=[[(r["rung"], r["arrive_L"], {pr: min(r["wr"][pr]["district"], P.hard_win(r["wr"][pr])) for pr in P.PROFILES}) for r in w["rows"][:2]] for w in out],
            low=[min(min(r["wr"][pr]["district"], P.hard_win(r["wr"][pr])) for r in w["rows"]) for w in out for pr in (("c8080",) if m == "story" else ("c6080", "c8060") if m == "mixed" else ("c6060",))],
            boss={pr: [P.hard_win(w["rows"][-1]["wr"][pr]) for w in out] for pr in P.PROFILES},
            cash=[round(w["money"]) for w in out], spent=round(o[m]["G"].spent),
            boss_equipped=[w["rows"][-1]["equipped"] for w in out], boss_fill=[w["rows"][-1]["fill"] for w in out])
    res["story_rows"] = [[(r["rung"], r["turns"], r["arrive_L"], min(r["wr"]["c8080"]["district"], P.hard_win(r["wr"]["c8080"]))) for r in w["rows"]] for w in o["story"]["out"]]
    return res

if __name__ == "__main__":
    K20 = dict(KL.FIXC, LADDER_TURNS=KL.turns(20, 20))
    VARS = [("today: fix C, kid 10/10, floor 0.20", dict(KL.FIXC), None),
            ("kid 20/20, floor 0.20 (no fix K)", K20, None),
            ("austin-v2: kid 20/20, flat grind XP (floor 1.0)", K20, 1.0),
            ("soft: kid 20/20, floor 0.60", K20, 0.6)]
    out = [run(*v) for v in VARS]
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str)
    for f in (0.2, 0.6, 1.0): print("levels per grind, floor", f, {d: lv(f, d) for d in (10, 6, 3, 2, 1)})
    for r in out:
        print("=====", r["name"]); print("  at cap 60/60, 80/80", r["at_cap"])
        for m in ("story", "mixed", "hard"):
            x = r[m]; print(" ", m, {k: x[k] for k in ("grinds", "wall", "wall_at", "post", "kid_grinds", "per_rung", "reached_cap", "enter", "boss_L", "low", "cash", "spent", "boss_fill")})
            print("    boss", x["boss"]); print("    kid", x["kid"])
        print("  story rows", r["story_rows"]); print("  story boss equipped", r["story"]["boss_equipped"])
        for p_, a in r["arc"].items(): print("  arc", p_, a)
