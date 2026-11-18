"""Retune the XP (points paid into mods).
Story: a per-rung XP table built so the story-only player arrives at every rung at today's live story-only r
(baseline_live.json, which reproduces the live run): XP after rung j = points needed for rung j+1's live r (R3 boss:
today's story-only end-of-R3 power, combat_power(L43, R3)), minus the ported catch-up. Grind: a flat XP per grind win
per round, set so the mixed walk grinds as often as today's live mixed walk (13/13/12)."""
import json, os, sys
from walk import walk, CAP_POWER
from velocity_shift import progression as P, equations as E

HERE = os.path.dirname(os.path.abspath(__file__))
base = json.load(open(os.path.join(HERE, "baseline_live.json")))
MIX_G = [w["total_grind"] for w in base["mixed"]]
story_r = [[x["r"] for x in w["rows"]] for w in base["story"]]
END_L = base["story"][2]["end_L"]


def target_points(rnd, j):
    if j < 7:
        return 10 * story_r[rnd][j] * E.opponent_budget(rnd, j)
    return 10 * P.combat_power(END_L, 2)


SPILL = False
KITS = None


def _pts(X, tab, price, nxt):
    if nxt == (2, 7):
        return walk("story", X, story_table=tab, price=price, spill=SPILL, kits=KITS)[2]["end_points"]
    _, rows, car = walk_until(X, tab, price, nxt)
    return car.points(E.ROUND_DISTRICTS[nxt[0]].lower())


SHORT = {}


def story_table(X, price):
    """If one race's XP cannot reach the live target (the ONE-mod rule caps a race at the picked mod's room, or the tier
    ceiling is in the way), the table pays only what that mod can absorb and the shortfall is recorded in SHORT."""
    tab = [[0.0] * 7 for _ in range(3)]
    for rnd in range(3):
        for j in range(7):
            nxt = (rnd, j + 1) if j < 6 else ((rnd + 1, 0) if rnd < 2 else (2, 7))
            tab[rnd][j] = 5000.0; most = _pts(X, tab, price, nxt); tgt = target_points(*nxt)
            SHORT[f"R{rnd + 1} {E.LADDER_RUNGS[j]}"] = round(max(0.0, tgt - most), 1)
            tgt = min(tgt, most - 0.05)
            lo, hi = 0.0, 5000.0
            for _ in range(45):
                tab[rnd][j] = (lo + hi) / 2
                lo, hi = (tab[rnd][j], hi) if _pts(X, tab, price, nxt) < tgt else (lo, tab[rnd][j])
            tab[rnd][j] = round(hi, 1)
    return tab


def walk_until(X, tab, price, at):
    """Story walk stopped right before rung `at` is raced (after its shop): returns (None, rows, car)."""
    rnd, j = at
    # stop after the previous race's purse; points on arrival = after the previous race's XP, i.e. stop at `at` itself
    return walk("story", X, story_table=tab, price=price, upto=at, spill=SPILL, kits=KITS)


def grind_cal(X, tab, price):
    g = [17.0, 17.0, 17.0]
    for n in range(3):
        best = None
        for gx in range(5, 300):
            g[n] = float(gx); t = walk("mixed", X, grind_xp=tuple(g), story_table=tab, price=price, spill=SPILL, kits=KITS)[n]["total_grind"]
            key = (abs(t - MIX_G[n]), -gx)
            if best is None or key < best[0]:
                best = (key, gx)
        g[n] = float(best[1])
    return g


if __name__ == "__main__":
    price = sys.argv[1] if len(sys.argv) > 1 else "mk1_list"; X = 0.60
    SPILL = "spill" in sys.argv[2:]
    if "touge_phee" in sys.argv[2:]:
        KITS = {"touge": "PHEE"}      # free kit pick: keep the Wangan kit for Touge (on tune at X = 0.60)
    tab = story_table(X, price); g = grind_cal(X, tab, price)
    print("story XP table", tab, "\ngrind XP", g, "\nshortfall vs live story curve", SHORT)
    json.dump(dict(story_table=tab, grind_xp=g, price=price, X=X, spill=SPILL, kits=KITS, story_shortfall=SHORT), open(os.path.join(HERE, f"calib_{price}{'_spill' if SPILL else ''}{'_tougephee' if KITS else ''}.json"), "w"), indent=1)
