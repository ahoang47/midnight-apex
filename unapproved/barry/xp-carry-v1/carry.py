"""xp-carry-v1 (draft, Barry 2026-11-14): leftover XP carries over between rounds. A player enters R2/R3 at the level
and XP bag they actually ended the previous round with (live mods-v1 bumps them to the previous cap with an empty bag).
In memory only; live sim/ is not changed."""
import contextlib
from velocity_shift import equations as E, progression as P

def run_carry(mode, carry=True):
    L, bag, money, debt = 0, 0.0, 0.0, E.DEBT_AMOUNT; out = []
    alloc = P.start_build(); G = P.Garage(); done = set()
    for rnd in range(3):
        d = E.ROUND_DISTRICTS[rnd].lower()
        if rnd > 0:
            alloc = P.retune(alloc, d)
            if not carry:
                end_L, L, bag = L, E.CAP_LEVEL[rnd - 1], 0.0
                alloc = P.add_points(alloc, E.skill_points(L) - E.skill_points(end_L), d)
        w = P._walk_round(rnd, L, bag, money, debt, mode, P.Build(d, alloc, L), G, done); out.append(w)
        L, bag, money, debt = w["L"], w["bag"], w["money"], w["debt"]; alloc = w["build"]
    return out, G, done

@contextlib.contextmanager
def patched(**kw):
    """Temporarily set equations / progression attributes (e.g. STORY_XP_MULT, story_xp, opponent_budget)."""
    saved = {}
    try:
        for k, v in kw.items():
            mod = E if hasattr(E, k) else P
            saved[k] = (mod, getattr(mod, k)); setattr(mod, k, v)
        yield
    finally:
        for k, (mod, v) in saved.items(): setattr(mod, k, v)

def summary(carry=True):
    o = {}
    for m in ("story", "mixed", "hard"):
        out, G, done = run_carry(m, carry)
        o[m] = dict(out=out, G=G, done=done,
                    enter=[w["rows"][0]["arrive_L"] for w in out], endL=[w["L"] for w in out], bag=[round(w["bag"]) for w in out],
                    grinds=[w["total_grind"] for w in out], wall=[w["wall_grind"] for w in out],
                    rows=[[(r["rung"], r["arrive_L"], r["wr"]["c8080"]["district"], P.hard_win(r["wr"]["c8080"])) for r in w["rows"]] for w in out],
                    min80=[min(min(r["wr"]["c8080"]["district"], P.hard_win(r["wr"]["c8080"])) for r in w["rows"]) for w in out],
                    boss80=[P.hard_win(w["rows"][-1]["wr"]["c8080"]) for w in out], boss6060=[P.hard_win(w["rows"][-1]["wr"]["c6060"]) for w in out],
                    cash=[round(w["money"]) for w in out], spent=round(G.spent))
    return o
