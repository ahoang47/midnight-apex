from __future__ import annotations
"""Story XP / level / skill-point progression model (grind v8c, Barry 2026-11-09).

STALE vs canon since 2026-11-13: the campaign is now one district per round (R1 Street, R2 Wangan,
R3 Touge; one crew each, no rematches). This model still walks the old 9-crew free-order ladder
until Barry's refit; see the note above DEFAULT_CREW_ORDER in equations.py.

Walks Prologue → R1–R3 (a play order: any permutation of DISTRICTS per round, default
DEFAULT_CREW_ORDER; 9 crews × 7 rungs) → Finale and
reports, per rung, the level cap, the level a player who skips grinding would have,
the grind races needed to reach the cap, and average/good win rates at the cap
("target") and with the grind skipped.

Rules (all constants in equations.py):
  * Levels: GEO curve, SP(L) = 240 · 1.1^(L/12); XP to next level x(L) rises faster than s(L).
  * Level cap = SP cap (SP_CAP_FRACTION of the reference). XP past the cap is lost.
  * Budgets follow the level curve: a crew boss's cap is the level whose SP is nearest
    SP_CAP_FRACTION × its Option A budget; Option A steps by round POSITION.
  * Cap raises per win: CAP_ALLOC_CREW / CAP_ALLOC_ROUND_OPEN (largest remainder).
  * Story XP per win: STORY_XP_* (boss pays the levels it unlocks, immediately).
  * Grind race XP: T2 taper, f(L, j) · x(L).
  * Forced player: grinds to the cap only at a rung that is not clear.
  * Mod tier level floor (slots-v2 b3): the tier first fitted at mature #2 (MOD_TIER_FLOOR_RUNG) needs level
    >= MOD_TIER_LEVEL_FLOOR[(round, position)]; below it the skip state races with the previous rung's mods. The tier
    is fitted once the player reaches the floor on story XP, or after grinding to the cap.
  * Finale exempt: caps lifted, FINALE_GRIND_SHARE of each finale stat rise comes from levels.

STALE (2026-11-13): combat is now the heat/load system (resources-v4b G2) with a 1.07 mod cap. This model still
uses the card-draw oracle below and the frozen PROGRESSION_MOD_CAP_FRACTION (1.05) until the ladder is refit.

Win rates come from `config/winrate_n4000.json`: real output of the N=4000 race-balance
sweep (seeds SIM_SEEDS × RACE_LENGTHS, KNOT_WINDOW_105, KAPPA_BY_LENGTH, OPPONENT_QTE,
LINE_SET_C), pooled and per district. Exact r values the v8c run uses are stored; other
r are linearly interpolated on a 0.0025 grid.
"""

import json
import math
import os
from bisect import bisect_left

from . import equations as E

LEVEL_LIMIT = 400
_TABLE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "winrate_n4000.json")
_TABLE = None


def _table():
    global _TABLE
    if _TABLE is None:
        with open(_TABLE_PATH) as fh:
            _TABLE = json.load(fh)["q"]
    return _TABLE


def win_rate(r: float, q: float, district: str = "pooled") -> tuple[float, float]:
    """(min, max) % win rate over seeds × lengths at budget ratio r, play level q (0.6 or 0.8)."""
    t = _table()[str(q)][district.lower()]
    rs = t["r"]; key = round(r, 4)
    i = bisect_left(rs, key)
    if i < len(rs) and abs(rs[i] - key) < 1e-9:
        return (t["min"][i], t["max"][i])
    if i == 0:
        return (t["min"][0], t["max"][0])
    if i >= len(rs):
        return (t["min"][-1], t["max"][-1])
    w = (key - rs[i - 1]) / (rs[i] - rs[i - 1])
    lerp = lambda a: round(a[i - 1] + w * (a[i] - a[i - 1]), 1)
    return (lerp(t["min"]), lerp(t["max"]))


def mid(t):
    return (t[0] + t[1]) / 2


# ── Curves ────────────────────────────────────────────────────────────
_CURVES = None


def curves():
    """SP[L] (total SP at level L), XC[L] (cumulative XP to reach L), X[L] (XP to fill level L)."""
    global _CURVES
    if _CURVES is None:
        SP = [E.SP_START]; XC = [0.0]; X = [0.0]
        for L in range(1, LEVEL_LIMIT + 1):
            x = E.xp_to_next(L, SP[-1]); SP.append(SP[-1] + E.sp_per_level(L)); X.append(x); XC.append(XC[-1] + x)
        _CURVES = (SP, XC, X)
    return _CURVES


def nearest_level(SP, target):
    return min(range(len(SP)), key=lambda L: abs(SP[L] - target))


def alloc_levels(n, weights):
    """Split n levels across the 7 rungs by weight (largest remainder)."""
    raw = [n * w / sum(weights) for w in weights]; a = [int(math.floor(v)) for v in raw]
    for i in sorted(range(7), key=lambda i: -(raw[i] - a[i]))[: n - sum(a)]:
        a[i] += 1
    return a


# ── Ladder ────────────────────────────────────────────────────────────
def check_order(order):
    """A play order must give each round a permutation of DISTRICTS (free choice, locked per crew, rounds gated)."""
    for rnd in (1, 2, 3):
        if sorted(order[rnd]) != sorted(E.DISTRICTS):
            raise ValueError(f"round {rnd} order {order[rnd]} is not a permutation of {E.DISTRICTS}")
    return order


def all_orders():
    """Every legal play order (6 per round, 216 in all)."""
    import itertools
    P = list(itertools.permutations(E.DISTRICTS))
    for o1, o2, o3 in itertools.product(P, P, P):
        yield {1: o1, 2: o2, 3: o3}


def unlocks_after(rnd: int, pos: int):
    """Unlock markers triggered by beating the boss of the crew played at 0-based position `pos` of round `rnd`."""
    done = (rnd, pos + 1); out = []
    if done == E.DEBT_CLEAR_AFTER: out.append("debt clears, aero unlocks")
    if done == E.BETTING_UNLOCK_AFTER: out.append("betting unlocks")
    if done == E.FINALE_UNLOCK_AFTER: out.append("finale + big finale mods unlock")
    return out


def ladder(order=None):
    """Story races with budgets, mods and level caps. Returns (rungs, finale_caps, finale_story_level, budgets)."""
    order = check_order(order or E.DEFAULT_CREW_ORDER)
    SP, XC, X = curves(); R = []; Bp = E.SABINE_BUDGET; Lp = 0; budgets = []
    for k in (2, 3):
        R.append(dict(k=k, crew="Prologue", district="", rung=f"scripted {k}", j=-1, B=E.SCRIPTED_BUDGETS[k], mods=0.0, L=0, kind="scripted", ro=False))
    k = 4
    for rnd in (1, 2, 3):
        for pos, d in enumerate(order[rnd]):
            ro = pos == 0 and rnd > 1                       # round-opening crew: first crew of R2 / R3
            BcA = Bp * (E.OPTION_A_ROUND_STEP if ro else E.OPTION_A_CREW_STEP)
            Lc = nearest_level(SP, E.SP_CAP_FRACTION * BcA)
            a = alloc_levels(Lc - Lp, E.CAP_ALLOC_ROUND_OPEN if ro else E.CAP_ALLOC_CREW)
            Bc = SP[Lc] / E.SP_CAP_FRACTION; budgets.append((f"R{rnd} {d}", round(BcA, 1), round(Bc, 1)))
            L = Lp
            for j in range(7):
                L += a[j]; ref = SP[L] / E.SP_CAP_FRACTION
                B = Bc if j == 6 else E.PROGRESSION_MOD_CAP_FRACTION * ref / E.LADDER_R[j]
                R.append(dict(k=k, crew=f"R{rnd} {d}", district=d, rung=E.LADDER_RUNGS[j], j=j, B=B, mods=E.MOD_SHARE_OF_REF * ref, L=L,
                              kind="boss" if j == 6 else "lt", ro=ro, rnd=rnd, pos=pos,
                              unlocks=unlocks_after(rnd, pos) if j == 6 else [])); k += 1
            Lp = Lc; Bp = BcA
    Lstep = Lp + alloc_levels(12, E.CAP_ALLOC_CREW)[0]       # finale story step, paid by the last crew boss
    Lf = []; spt = SP[Lstep]; Bq = Bp
    for nm, d, B in E.FINALE:
        spt += E.FINALE_GRIND_SHARE * E.PROGRESSION_MOD_CAP_FRACTION * (B - Bq); Lf.append(nearest_level(SP, spt)); Bq = B
    return R, Lf, Lstep, budgets, Bp


def _story_xp_after(R, i, x, XC, X, Lf, Lstep):
    """Story XP a win at rung i adds (before the next-cap clamp) and the next rung's cap."""
    nxt = R[i + 1]["L"] if i + 1 < len(R) else Lf[0]
    unl = XC[Lstep if i + 1 == len(R) else nxt] - XC[x["L"]]
    if x["k"] == 2:
        add = 0.0
    elif x["kind"] == "boss" or x["k"] == 3:
        add = E.STORY_XP_BOSS * unl
    else:
        lam = E.STORY_XP_LT_ROUND_OPEN if x["ro"] else E.STORY_XP_LT
        add = max(lam * unl, E.STORY_XP_LT_FLOOR * X[max(1, nxt)])
    return add, nxt


def derive_mod_tier_floors(order=None):
    """Crew-local level floor of each crew's mature #2 mod tier, keyed (round, 0-based position) (slots-v2 fix b3).
    Floor = level at the MOD_TIER_FLOOR_RUNG rung of a player who entered the crew at the previous crew boss's level cap
    (no grind), then won on story XP only, + MOD_TIER_FLOOR_MARGIN; never above that rung's cap. Source of
    E.MOD_TIER_LEVEL_FLOOR (same derivation as unapproved/barry/slots-v2/fixes.py LOCAL_L + 1)."""
    SP, XC, X = curves(); R, Lf, Lstep, budgets, B_last = ladder(order)
    xp = 0.0; prev_boss_cap = None; out = {}
    for i, x in enumerate(R):
        cap = x["L"]
        if x["kind"] != "scripted" and x["j"] == 0 and prev_boss_cap is not None:
            xp = max(xp, XC[prev_boss_cap])
        if x["kind"] == "boss":
            prev_boss_cap = cap
        xp = min(xp, XC[cap])
        if x["kind"] != "scripted" and x["j"] == E.MOD_TIER_FLOOR_RUNG:
            out[(x["rnd"], x["pos"])] = min(cap, _level(XC, xp, cap) + E.MOD_TIER_FLOOR_MARGIN)
        add, nxt = _story_xp_after(R, i, x, XC, X, Lf, Lstep)
        xp = min(xp + add, XC[nxt])
    return out


def mod_tier_floor(rnd: int, pos: int, j: int):
    """Level floor of the mod tier first fitted at rung j of the crew at (round, 0-based position); None if not floored."""
    return E.MOD_TIER_LEVEL_FLOOR[(rnd, pos)] if j == E.MOD_TIER_FLOOR_RUNG else None


def mod_tier_available(rnd: int, pos: int, j: int, level: int) -> bool:
    """True when the mod tier unlocked for rung j can be fitted at this level ("requires level N" lock otherwise)."""
    f = mod_tier_floor(rnd, pos, j)
    return f is None or level >= f


def _level(XC, xp, cap):
    L = 0
    while L + 1 <= cap and XC[L + 1] <= xp + 1e-9:
        L += 1
    return L


def _levels_in(XC, a, b):
    def lv(v):
        L = 0
        while XC[L + 1] <= v + 1e-9:
            L += 1
        return L + (v - XC[L]) / (XC[L + 1] - XC[L])
    return lv(b) - lv(a)


def _rates(r_target, r_skip, district):
    return dict(avg_target=win_rate(r_target, E.AVERAGE_PLAY_Q, district), avg_skip=win_rate(r_skip, E.AVERAGE_PLAY_Q, district),
                good_target=win_rate(r_target, E.GOOD_PLAY_Q, district), good_skip=win_rate(r_skip, E.GOOD_PLAY_Q, district))


def run(policy: str = "forced", order=None):
    """Play the season. policy 'forced' grinds to the cap only at rungs that aren't clear; 'never' never grinds."""
    SP, XC, X = curves(); R, Lf, Lstep, budgets, B_last = ladder(order)
    xp = 0.0; rows = []; story = grind = lost = 0.0
    prev_mods = 0.0; gated = 0.0; gate_floor = 0          # mod tier held back by its level floor (MOD_TIER_LEVEL_FLOOR)

    def grind_to(v, cap, j):
        n = 0
        while XC[cap] - v > 1e-9 and n <= 200:
            Ln = _level(XC, v, cap) + 1
            v = min(v + E.grind_payout_fraction(Ln, j) * X[Ln], XC[cap]); n += 1
        return n, v

    for i, x in enumerate(R):
        cap = x["L"]
        if xp > XC[cap] + 1e-9:
            lost += xp - XC[cap]; xp = XC[cap]
        L = _level(XC, xp, cap)
        floor = None
        if x["kind"] != "scripted":
            if gated and L >= gate_floor:                  # floor reached later on story XP: the locked tier is fitted
                gated = 0.0
            floor = mod_tier_floor(x["rnd"], x["pos"], x["j"])
            if floor is not None and L < floor:            # tier for this rung shows "requires level N": not fitted
                gated = x["mods"] - prev_mods; gate_floor = floor
        mods_skip = x["mods"] - gated
        r_skip = (SP[L] + mods_skip) / x["B"]; r_tgt = (SP[cap] + x["mods"]) / x["B"]
        pooled = _rates(r_tgt, r_skip, "pooled")
        clear = x["kind"] == "scripted" or mid(pooled["avg_skip"]) >= E.CLEAR_THRESHOLD
        n, v2 = grind_to(xp, cap, max(0, x["j"]))
        g = n if (policy == "forced" and not clear) else 0
        if g:
            grind += v2 - xp; xp = v2
            gated = 0.0                                    # ground to the cap (>= every floor): tier fitted
        row = dict(k=x["k"], crew=x["crew"], district=x["district"], rung=x["rung"], j=x["j"], round_open=x["ro"], pos=x.get("pos"),
                   unlocks=x.get("unlocks", []), B=round(x["B"], 1),
                   level_cap=cap, story_level=L, races_to_cap=n, grind_races=g, clear=clear,
                   mods=round(x["mods"], 2), mods_skip=round(mods_skip, 2), tier_floor=floor,
                   tier_locked=floor is not None and L < floor, **pooled)
        prev_mods = x["mods"]
        if x["district"]:
            row["district_rates"] = _rates(r_tgt, r_skip, x["district"])
        nxt = R[i + 1]["L"] if i + 1 < len(R) else Lf[0]
        unl = XC[Lstep if i + 1 == len(R) else nxt] - XC[cap]
        if x["k"] == 2:
            add = 0.0
        elif x["kind"] == "boss" or x["k"] == 3:
            add = E.STORY_XP_BOSS * unl
        else:
            lam = E.STORY_XP_LT_ROUND_OPEN if x["ro"] else E.STORY_XP_LT
            add = max(lam * unl, E.STORY_XP_LT_FLOOR * X[max(1, nxt)])
        before = xp; xp = min(xp + add, XC[nxt]); lost += before + add - xp; story += xp - before
        row["win_levels"] = round(_levels_in(XC, before, xp), 2)
        rows.append(row)
    base = E.MOD_SHARE_OF_REF * B_last
    for idx, ((nm, d, B), Lc) in enumerate(zip(E.FINALE, Lf)):
        if xp > XC[Lc]:
            lost += xp - XC[Lc]; xp = XC[Lc]
        L = _level(XC, xp, Lc); n, v2 = grind_to(xp, Lc, E.TAPER_FINALE_RUNG)
        mods = E.PROGRESSION_MOD_CAP_FRACTION * B - SP[Lc] - base
        r_skip = (SP[L] + base + mods) / B; r_tgt = (SP[Lc] + base + mods) / B
        g = n if policy == "forced" else 0
        if g:
            grind += v2 - xp; xp = v2
        rows.append(dict(k=rows[-1]["k"] + 1, crew="Finale", district=d, rung=nm, j=E.TAPER_FINALE_RUNG, round_open=False, B=B, level_cap=Lc,
                         story_level=L, races_to_cap=n, grind_races=g, clear=None, finale_mods=round(mods, 1),
                         **_rates(r_tgt, r_skip, "pooled"), district_rates=_rates(r_tgt, r_skip, d)))
    totals = dict(levels=Lf[-1], grind_races=sum(r["grind_races"] for r in rows), story_xp=round(story), grind_xp=round(grind),
                  lost_xp=round(lost), finale_story_level=Lstep, finale_caps=Lf, budgets=budgets)
    return rows, totals


def walls(rows):
    """[(crew, mature #2 races, boss races)] in game order + finale races."""
    out = []; m = None
    for r in rows:
        if r["crew"] in ("Prologue", "Finale"):
            continue
        if r["j"] == 3:
            m = r["grind_races"]
        if r["j"] == 6:
            out.append((r["crew"], m, r["grind_races"]))
    return out, [r["grind_races"] for r in rows if r["crew"] == "Finale"]


def pattern(rows):
    ab = {"kid": "k", "mature": "m", "old head": "o", "crew boss": "B"}
    s = []; cur = None
    for r in rows:
        if r["crew"] == "Prologue":
            continue
        if r["crew"] != cur:
            s.append(" " + (r["crew"][1] + r["crew"][3] if r["crew"] != "Finale" else "Fin") + ":"); cur = r["crew"]
        c = ab.get(r["rung"], "M" if r["rung"].startswith("Myth") else "S")
        s.append(c.upper() + str(r["grind_races"]) if r["grind_races"] else c)
    return "".join(s).strip()
