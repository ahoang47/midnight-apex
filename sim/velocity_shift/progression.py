from __future__ import annotations
"""Story XP / level / money progression on the 3-round ladder (econ-v1, Barry; Austin go-ahead 2026-11-13).

Port of unapproved/barry/econ-v1/model.py + evaluate.py (walk_round) onto the live constants in equations.py.
One district per round (R1 Street, R2 Wangan, R3 Touge), one crew each, 7 rungs (kid1 kid2 mat1 mat2 oh1 oh2 boss,
10/10/20/20/20/20/30 turns), no rematches. Then the pre-finale arc (P1-P4, M11-M32) and the finale F1-F4.

Rules (all constants in equations.py):
  * Levels: SP(L) = 240 x 1.1^(L/12); stats P = SP / 0.8. Combat power = min(C_ROUND, 1.07 x P) once mods are on
    (R1 at L0 is the stock car, 1.00 x P). Opponent budget B = C_ROUND / target r, so r at the cap = target r.
  * XP: xp_to_next(L) = 100 x 1.08^L. Story wins pay STORY_FILL x STORY_W share of the round's entry-to-cap XP;
    grind wins (10-turn wilds) pay GRIND_FRAC x xp_to_next x taper. XP past the cap is lost.
  * Money (USD): purse by rung kind x ROUND_PAYOUT_MULT; grind races pay GRIND_PAYOUT_FRACTION of a wild purse;
    DEBT_SHARE of every purse pays the DEBT_AMOUNT debt while it is open. The walk banks cash and buys nothing
    (as evaluate.py does); the shop / betting / T4 Monte Carlo stays in unapproved/barry/econ-v1 (run_betting_levers.py,
    run_finale_arc.py).
  * Walk policies: "story" never grinds (80/80 criterion); "mixed" grinds once at the first rung where 60/80 or 80/60
    is < 50 % (hard cell for 20/30-turn races) until both clear, then grinds to the cap before the boss; "hard"
    (60/60) grinds at every rung where 60/60 is < 50 %, then to the cap before the boss.

Win rates come from config/winrate_g2_econ_v1.json: real G2 sweep output (9 seeds x 1000 races, 3 boss styles), on the
touge-lines-v1 DRAFT track set (Street/Wangan CW+CCW, Touge uphill/downhill). The nearest sweep r is used, as in
econ-v1 evaluate.py (its wr() call never interpolates when allow_interp is set; it takes the nearest point).
"""

import json
import math
import os
from bisect import bisect_left

from . import equations as E

PROFILES = ("c6060", "c6080", "c8060", "c8080")
_TABLE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "winrate_g2_econ_v1.json")
_TABLE = None
HARD_TRACKS = {"touge": ("T_Uphill",), "street": ("S1_Shibuya_Grid_CW", "S1_Shibuya_Grid_CCW")}


def _table():
    global _TABLE
    if _TABLE is None:
        with open(_TABLE_PATH) as fh:
            _TABLE = json.load(fh)
    return _TABLE


def _cols(district=None, track=None):
    tr = _table()["tracks"]
    if track:
        return [i for i, (_, n) in enumerate(tr) if n == track]
    return [i for i, (d, _) in enumerate(tr) if d == district.lower()]


def win_rate(profile: str, r: float, turns: int, district: str | None = None, track: str | None = None) -> float:
    """Win rate (%) for a profile (c6060 / c6080 / c8060 / c8080) at stat ratio r, race length 10/20/30, averaged
    over a district's draft tracks (or one track). Uses the nearest sweep point, as econ-v1 wr.py / evaluate.py do
    (no interpolation; the sweep grids include every designed and walk r, so offsets are small)."""
    t = _table()["q"][profile]
    rs = t["r"]; rows = t["win"][str(int(turns))]; cols = _cols(district, track)
    i = bisect_left(rs, r)
    if i >= len(rs) or (i > 0 and abs(rs[i - 1] - r) <= abs(rs[i] - r)):
        i -= 1
    return sum(rows[i][c] for c in cols) / len(cols)


def nearest_r(profile: str, r: float) -> float:
    """The sweep r that win_rate uses for r."""
    rs = _table()["q"][profile]["r"]
    return min(rs, key=lambda x: abs(x - r))


def win_pack(profile: str, r: float, turns: int, district: str) -> dict:
    """{"district": %, plus "uphill"/"downhill" on Touge, "S1_CW"/"S1_CCW" on 30-turn Street}, each rounded to 0.1."""
    d = district.lower()
    out = {"district": round(win_rate(profile, r, turns, d), 1)}
    if d == "touge":
        out["uphill"] = round(win_rate(profile, r, turns, track="T_Uphill"), 1)
        out["downhill"] = round(win_rate(profile, r, turns, track="T_Downhill"), 1)
    if d == "street" and turns == 30:
        out["S1_CW"] = round(win_rate(profile, r, turns, track="S1_Shibuya_Grid_CW"), 1)
        out["S1_CCW"] = round(win_rate(profile, r, turns, track="S1_Shibuya_Grid_CCW"), 1)
    return out


def hard_win(pack: dict) -> float:
    """The hard cell of a pack: Touge uphill, worse Shibuya S1 direction, else the district mean."""
    if "uphill" in pack:
        return pack["uphill"]
    if "S1_CW" in pack:
        return min(pack["S1_CW"], pack["S1_CCW"])
    return pack["district"]


# ── Level / power helpers ─────────────────────────────────────────────
def combat_power(level: int, rnd: int, mods: bool = True) -> float:
    """Player combat power: min(C_ROUND, 1.07 x P(L)) with mods; stock car (1.00 x P) at R1 L0 or without mods."""
    P = E.stats_at_level(level)
    if not mods or (rnd == 0 and level <= 0):
        return P
    return min(E.C_ROUND[rnd], E.MOD_CAP_FRACTION * P)


def apply_xp(level: int, xp: float, bag: float, cap: int):
    """Add xp to (level, bag) without passing `cap`; XP past the cap is lost. Returns (level, bag)."""
    bag += xp
    while level < cap:
        need = E.xp_to_next(level)
        if bag + 1e-9 < need:
            break
        bag -= need; level += 1
    if level >= cap:
        level, bag = cap, 0.0
    return level, bag


def grind_to_cap(level: int, bag: float, cap: int, max_n: int = 200) -> int:
    """Grind wins from (level, bag) to the cap."""
    n = 0
    while level < cap and n < max_n:
        level, bag = apply_xp(level, E.grind_xp(level, cap), bag, cap); n += 1
    return n


# ── Ladder ────────────────────────────────────────────────────────────
def check_order(order):
    """The only legal play order is DEFAULT_CREW_ORDER: one crew per round, R1 Street, R2 Wangan, R3 Touge."""
    for rnd in (1, 2, 3):
        if tuple(order.get(rnd, ())) != E.DEFAULT_CREW_ORDER[rnd]:
            raise ValueError(f"round {rnd} order {order.get(rnd)} is not {E.DEFAULT_CREW_ORDER[rnd]} (one district per round)")
    return order


def unlocks_after(rnd: int):
    """Unlock markers triggered by beating round `rnd`'s crew boss (1-based)."""
    out = []
    if rnd == E.DEBT_CLEAR_AFTER:
        out.append("debt due, aero + wholesale unlock")
    if rnd == E.BETTING_UNLOCK_AFTER:
        out.append("betting unlocks")
    if rnd == E.FINALE_UNLOCK_AFTER:
        out.append("wholesale ends; pre-finale arc + finale open (T4 at P1)")
    return out


def ladder():
    """Story rungs with budgets, target r and level caps, R1-R3."""
    rows = []
    for rnd, d in enumerate(E.ROUND_DISTRICTS):
        for j, name in enumerate(E.LADDER_RUNGS):
            rows.append(dict(rnd=rnd + 1, district=d, rung=name, j=j, kind=E.LADDER_RUNG_KIND[j], turns=E.LADDER_TURNS[j],
                             B=E.opponent_budget(rnd, j), target_r=E.LADDER_TARGET_R[d.lower()][j], cap=E.CAP_LEVEL[rnd],
                             unlocks=unlocks_after(rnd + 1) if j == 6 else []))
    return rows


def mod_tier_floor(tier: str) -> int:
    return E.MOD_TIER_LEVEL_FLOOR[tier]


def mod_tier_available(tier: str, level: int, rounds_done: int = 0, t4_unlocked: bool = False) -> bool:
    """True when `tier` can be fitted: level >= its floor ("requires level N" otherwise); T4 also needs the P1 win."""
    if level < E.MOD_TIER_LEVEL_FLOOR[tier]:
        return False
    if tier == "T4":
        return t4_unlocked and rounds_done >= E.FINALE_UNLOCK_AFTER
    return True


def t4_package_price() -> float:
    """Full T4 build (5 regular + 1 aero), full price."""
    return E.T4_PACKAGE["regular"] * E.mod_price("T4") + E.T4_PACKAGE["aero"] * E.mod_price("T4", aero=True)


def _walk_round(rnd, enter_level, enter_bag, money, debt, mode):
    d = E.ROUND_DISTRICTS[rnd].lower(); cap = E.CAP_LEVEL[rnd]
    L, bag = enter_level, enter_bag
    rows = []; wall_done = False; total = wall = post = 0; wall_name = None

    def credit(kind, grind):
        nonlocal money, debt
        pay = E.purse(rnd, kind, grind)
        if debt > 0:
            take = min(debt, E.DEBT_SHARE * pay); debt -= take; money += pay - take
        else:
            money += pay

    def do_grind(n):
        nonlocal L, bag, total
        for _ in range(n):
            if L >= cap:
                break
            L, bag = apply_xp(L, E.grind_xp(L, cap), bag, cap); credit("kid", True); total += 1

    def ok(profiles, r, T):
        for pr in profiles:
            pk = win_pack(pr, r, T, d)
            if pk["district"] < E.CLEAR_THRESHOLD or (T >= 20 and hard_win(pk) < E.CLEAR_THRESHOLD):
                return False
        return True

    def grind_until(profiles, B, T):
        Lt, bt = L, bag; n = 0
        while n < 80:
            Lt, bt = apply_xp(Lt, E.grind_xp(Lt, cap), bt, cap); n += 1
            if ok(profiles, combat_power(Lt, rnd) / B, T) or Lt >= cap:
                break
        return n

    for j, name in enumerate(E.LADDER_RUNGS):
        B = E.opponent_budget(rnd, j); T = E.LADDER_TURNS[j]; pre_boss = 0; here = 0
        if name == "boss" and mode in ("mixed", "hard") and L < cap:
            before = total; do_grind(grind_to_cap(L, bag, cap)); pre_boss = total - before
            if wall_done or mode == "hard":
                post += pre_boss
        r = combat_power(L, rnd) / B
        if name != "boss" and L < cap:
            if mode == "mixed" and not wall_done and not ok(("c6080", "c8060"), r, T):
                here = grind_until(("c6080", "c8060"), B, T); do_grind(here)
                wall = here; wall_name = name; wall_done = True
            elif mode == "hard" and not ok(("c6060",), r, T):
                here = grind_until(("c6060",), B, T); do_grind(here)
                if wall_name is None:
                    wall_name = name; wall += here
                else:
                    post += here
            r = combat_power(L, rnd) / B
        arrive_L = L
        packs = {pr: win_pack(pr, r, T, d) for pr in PROFILES}
        credit(E.LADDER_RUNG_KIND[j], False)
        L, bag = apply_xp(L, E.story_xp(rnd, j, enter_level, cap), bag, cap)
        r_grind = combat_power(arrive_L, rnd) / E.opponent_budget(rnd, 0)
        rows.append(dict(rnd=rnd + 1, district=E.ROUND_DISTRICTS[rnd], rung=name, turns=T, B=round(B, 2),
                         target_r=E.LADDER_TARGET_R[d][j], arrive_L=arrive_L, arrive_r=round(r, 4), wr=packs,
                         grind_here=here, pre_boss_grind=pre_boss,
                         grind10={pr: round(win_rate(pr, r_grind, E.GRIND_TURNS, d), 1) for pr in PROFILES},
                         L_after=L, money=round(money, 2), debt=round(max(debt, 0.0), 2),
                         unlocks=unlocks_after(rnd + 1) if j == 6 else []))
    return dict(rows=rows, L=L, bag=bag, money=money, debt=max(debt, 0.0), total_grind=total, wall_grind=wall,
                wall=wall_name, post_wall_to_cap=post, cap=cap, reached_cap=L >= cap)


def run(mode: str = "mixed", order=None):
    """Walk R1-R3 for a policy ("story", "mixed", "hard"). Each round is entered at the previous round's cap (R1 at L0)
    with cash and debt carried. Returns a list of 3 round dicts (rows + totals)."""
    if mode not in ("story", "mixed", "hard"):
        raise ValueError(mode)
    check_order(order or E.DEFAULT_CREW_ORDER)
    L, bag, money, debt = 0, 0.0, 0.0, E.DEBT_AMOUNT; out = []
    for rnd in range(3):
        if rnd > 0:
            L, bag = E.CAP_LEVEL[rnd - 1], 0.0
        w = _walk_round(rnd, L, bag, money, debt, mode); out.append(w)
        L, bag, money, debt = w["L"], w["bag"], w["money"], w["debt"]
    return out


def at_cap_table():
    """Every ladder rung and finale race at its level cap (r = target r), all four profiles."""
    rows = []
    for x in ladder():
        rows.append(dict(rnd=x["rnd"], district=x["district"], rung=x["rung"], turns=x["turns"], r=x["target_r"],
                         wr={pr: win_pack(pr, x["target_r"], x["turns"], x["district"]) for pr in PROFILES}))
    for (nm, d, B), r, opp in zip(E.FINALE, E.FINALE_TARGET_R, E.FINALE_OPPONENT):
        rows.append(dict(rnd="F", district=d, rung=f"{nm} vs {opp}", turns=E.FINALE_TURNS, r=r, B=B,
                         wr={pr: win_pack(pr, r, E.FINALE_TURNS, d) for pr in PROFILES}))
    return rows


# ── Finale and pre-finale arc ─────────────────────────────────────────
def finale_caps():
    """(ceiling C = B x r, level cap) for F1-F4."""
    out = []
    for (_, _, B), r in zip(E.FINALE, E.FINALE_TARGET_R):
        C = B * r
        out.append((C, int(round(E.level_for_sp(C * E.SP_CAP_FRACTION / E.MOD_CAP_FRACTION)))))
    return out


def finale_arc():
    """Pre-finale arc and finale in play order with budgets, design r, purses and story XP."""
    caps = (E.CAP_LEVEL[-1],) + E.FINALE_CAP_LEVEL
    steps = ("pre_F1", "F1_F2", "F2_F3", "F3_F4")
    gap = {s: sum(E.xp_to_next(L) for L in range(caps[i], caps[i + 1])) for i, s in enumerate(steps)}
    out = []
    for i, s in enumerate(steps):
        for (rid, place, d, T, r, share, purse, B) in E.FINALE_ARC:
            if place == s:
                out.append(dict(id=rid, place=place, district=d, turns=T, r_design=r, B=B, purse=purse, billed=False,
                                xp=E.ARC_STORY_FILL * share * gap[s], unlock_t4=rid == E.T4_UNLOCK_RACE))
        nm, d, B = E.FINALE[i]
        out.append(dict(id=f"F{i + 1}", place=f"F{i + 1}", district=d.lower(), turns=E.FINALE_TURNS, r_design=E.FINALE_TARGET_R[i],
                        B=B, purse=E.FINALE_PURSE, billed=True, xp=0.0, unlock_t4=False,
                        name=nm, opponent=E.FINALE_OPPONENT[i], cap=E.FINALE_CAP_LEVEL[i]))
    return out
