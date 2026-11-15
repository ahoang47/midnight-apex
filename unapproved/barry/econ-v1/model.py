"""Draft 3-crew XP / money / grind / cap model for econ-v1.

Replaces stale sim/velocity_shift/progression.py logic in this folder only.
Uses G2 win-rate tables (not the card-draw oracle). Live G2 combat, live
AERO_MAX_EQUIPPED=1 (one aero, any of 6 slots, blocks that slot's regular
mod). No live-sim edits.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field, asdict
from typing import Optional

# ---------------------------------------------------------------------------
# Ladder geometry (fixed from Austin + round-ladder-v1 primary walk)
# ---------------------------------------------------------------------------
ANCHOR_B = 330.0
K_STEP = 1.07
K_CAP = 1.07
LADDER_RUNGS = (
    ("kid1", 10, "kid"),
    ("kid2", 10, "kid"),
    ("mat1", 20, "mature"),
    ("mat2", 20, "mature"),
    ("oh1",  20, "old_head"),
    ("oh2",  20, "old_head"),
    ("boss", 30, "boss"),
)
DISTRICTS = ("street", "wangan", "touge")
ROUNDS = (1, 2, 3)
# Previous (frozen) target-r ladder, kept as relative spacing only
OLD_LADDER_R = (1.13, 1.11, 1.10, 1.09, 1.08, 1.06, 1.07)

# Boss target-r (Variant A — criterion 9: 80/80 ~85% at cap).
# Relative intent kept: R1 S1 eased vs the other Street tracks (boss-only);
# R3 Touge a touch harder than R2 (uphill is the hard cell).
# Variant B (60/60-survivable bosses) is a reported alternative, not default.
BOSS_R_A = {"street": 1.040, "wangan": 1.025, "touge": 1.053}
# Full per-rung target r (Variant A). Kids are set so a player who enters
# the round at the previous ceiling (or R1 at L=0, k=1.00) arrives near
# r≈1.02-1.03 on 10-turn wilds — enough for mixed players to be >=50%
# without a kid1 wall. The 1.07^2 cap jump would otherwise drop arrival r
# to ~0.95 on kids budgeted like the old +0.06 offset, which is a 15-20
# grind-race wall (see eval iter 0). Boss r is locked to the 80/80 ~85% band.
LADDER_R_A = {
    "street": (1.20, 1.16, 1.10, 1.07, 1.055, 1.048, 1.040),
    "wangan": (1.18, 1.16, 1.12, 1.08, 1.05, 1.035, 1.025),
    "touge":  (1.18, 1.14, 1.10, 1.08, 1.065, 1.058, 1.053),
}
# Variant B: 60/60-survivable bosses (~40%+ at cap). 80/80 will sit in the
# high 90s — it cannot also be 85% on the same r (see RESULTS).
BOSS_R_B = {"street": 1.08, "wangan": 1.07, "touge": 1.10}
LADDER_R_B = {
    "street": (1.20, 1.16, 1.14, 1.12, 1.10, 1.09, 1.08),
    "wangan": (1.20, 1.16, 1.13, 1.11, 1.09, 1.08, 1.07),
    "touge":  (1.22, 1.18, 1.16, 1.14, 1.12, 1.11, 1.10),
}
LT_DR = (0.060, 0.040, 0.030, 0.020, 0.010, 0.005, 0.000)  # documented only


# Variant C (Austin 2026-11-13 middle ground): 80/80 at cap about 90%
# (band 88-92) AND 60/60 at least 30% on every boss variant (S1 CW/CCW,
# Touge uphill). Wangan and Touge have an r that hits both. Street S1
# does not — see RESULTS. Closest r that meets the 60/60 S1 30% floor is
# 1.053 (exact grid 1.05313730): 60/60 S1 30.9/31.2, 80/80 S1 93.9/95.4
# (2-3 pp over 92). Relative intent: Touge a bit harder (uphill 89.6 at
# r=1.0656), S1 eased to reach the 30% floor (which overshoots 80/80).
BOSS_R_C = {"street": 1.053, "wangan": 1.040, "touge": 1.066}
LADDER_R_C = {
    "street": (1.20, 1.16, 1.10, 1.07, 1.065, 1.058, 1.053),
    "wangan": (1.18, 1.16, 1.11, 1.08, 1.06, 1.048, 1.040),
    "touge":  (1.18, 1.16, 1.12, 1.085, 1.075, 1.070, 1.066),
}

LADDERS = {"A": LADDER_R_A, "B": LADDER_R_B, "C": LADDER_R_C}


def target_r(district: str, j: int, variant: str = "C") -> float:
    return float(LADDERS[variant][district][j])


def ceilings():
    """C_n = 1.07 * P_n, P_1 = ANCHOR_B, P_{n+1} = 1.07 * C_n, C_n = 1.07 * P_n
    so C_{n+1} = 1.07^2 * C_n? No:
    boss_n budget B_n so that at cap r_boss, B_n = C_n / r_boss.
    Ceiling C_n = K_CAP * P_n, P_1 = ANCHOR_B, P_{n+1} = K_STEP * C_n.
    C1 = 1.07 * 330 = 353.1
    P2 = 1.07 * 353.1 = 377.817?  Wait earlier we used 1.07 * C1? Let's be exact.
    From RESULTS: P1=330, C1=353.1, P2=377.817? 353.1*1.07=377.817, C2=404.264?
    Previous notes said 377.71 / 404.145. That used boss B = C/1.07 so P2 = 1.07*C1
    wait P2 = previous ceiling * k_step = C1 * 1.07 = 353.1*1.07=377.817.
    Earlier 377.71 came from B_boss_R1 = 353.1/1.07?  330*1.07=353.1, 353.1/1.07=330.
    The PRIMARY WALK without the +0.01 S1 offset: R1 boss B=330, C1=353.1.
    Austin then applied +0.01 target-r on the R1 boss (r=1.08) which CUT the
    boss budget, but the ceiling stayed 1.07 x the UNADJUSTED? or 1.07 x boss?

    Fixed input this task: "R1 Street anchor B=330, ceiling = 1.07 x boss,
    next boss = 1.07 x prev ceiling" WITH the picks (R3 +0.03, R1 +0.01).

    Conflict: if ceiling = 1.07 x boss and R1 boss r is 1.08, B_boss is no
    longer 330 if 330 is the *anchor*. The fixed input says "anchor B=330".
    I'll keep the POWER ceilings on the un-offset 1.07 chain (C1=353.1,
    C2=404.145?, let's compute consistently):

    Official primary walk (from RESULTS.md before picks):
      P1=330, C1=353.10, P2=377.82, C2=404.26, P3=432.56, C3=462.84
      or they used 353.1 * 1.07 = 377.817.

    I'll lock:
      P = [330.0, 330*1.07**2, 330*1.07**4]   # because C=1.07 P, next P=1.07 C
      C = [330*1.07, 330*1.07**3, 330*1.07**5]
    Opponent budgets are then B = C_round / target_r, which applies the
    new (retuned) target-r without moving the player's ceiling.
    """
    P, C = [], []
    p = ANCHOR_B
    for _ in ROUNDS:
        P.append(p)
        c = K_CAP * p
        C.append(c)
        p = K_STEP * c
    return P, C


P_ROUND, C_ROUND = ceilings()  # index 0 = R1

# Finale opponent budgets are a fixed input
FINALE_B = (494.8, 566.3, 648.2, 741.9)
FINALE_DIST = ("touge", "wangan", "street", "touge")  # Myth 1-3 + Summit; taste/story flag
# Variant A: give the player a finale ceiling so 80/80 can sit at the same
# boss-r targets. This forces a large post-R3 cap climb (flagged).
FINALE_R_A = (1.050, 1.025, 1.040, 1.050)
# Variant C: same 90%/30% boss r as the campaign (Touge 1.066, Wangan 1.040,
# Street 1.053 with the S1 trade-off, Summit Touge 1.066).
FINALE_R_C = (1.066, 1.040, 1.053, 1.066)


def finale_ceilings(rs=None, variant: str = "C"):
    if rs is None:
        rs = FINALE_R_C if variant == "C" else FINALE_R_A
    return tuple(b * r for b, r in zip(FINALE_B, rs))


# ---------------------------------------------------------------------------
# Level curve: geometric SP, 12 / 17 / 17 levels per campaign round
# so C_n = 1.07 * SP(L_n) / 0.8, L = 12, 29, 46.
# ---------------------------------------------------------------------------
SP0 = 240.0          # SP at L=0 (start). 0.8*330=264 = SP at L=12.
SP_GROWTH_PER_12 = 1.10  # SP(L+12)/SP(L) = 1.10, matches C2/C1 = 1.07^2


def sp_at(L: float) -> float:
    return SP0 * (SP_GROWTH_PER_12 ** (L / 12.0))


def level_for_sp(sp: float) -> float:
    return 12.0 * math.log(sp / SP0) / math.log(SP_GROWTH_PER_12)


def power_at_level(L: float) -> float:
    """Player stats P = SP / 0.8. Ceiling is 1.07 * P only when mods fill the cap."""
    return sp_at(L) / 0.8


def ceiling_at_level(L: float) -> float:
    return K_CAP * power_at_level(L)


# Cap levels (exact to the 1.07 chain)
def cap_levels():
    out = []
    for C in C_ROUND:
        # C = 1.07 * SP/0.8  => SP = C * 0.8 / 1.07
        out.append(round(level_for_sp(C * 0.8 / K_CAP)))
    return tuple(out)


CAP_L = cap_levels()  # (12, 29, 46)
FINALE_C = finale_ceilings(variant="C")
FINALE_L = tuple(int(round(level_for_sp(c * 0.8 / K_CAP))) for c in FINALE_C)
FINALE_C_A = finale_ceilings(variant="A")
FINALE_L_A = tuple(int(round(level_for_sp(c * 0.8 / K_CAP))) for c in FINALE_C_A)


# ---------------------------------------------------------------------------
# XP curve
# xp_to_next(L) grows so later levels cost more; story + grind spend this.
# ---------------------------------------------------------------------------
@dataclass
class EconParams:
    # XP
    xp0: float = 100.0            # xp_to_next(0)
    xp_growth: float = 1.08       # per level
    # Story XP as a fraction of (xp needed to go from enter-level to cap)
    # distributed across the 7 rungs. The 7 weights sum to story_fill.
    # story_fill < 1 so a story-only run does not reach cap.
    story_fill: tuple = (0.62, 0.75, 0.80)  # R1, R2, R3 — more fill in R3 so 80/80 hits boss r
    # relative weights kid1..boss (normalized per round)
    story_w: tuple = (0.12, 0.12, 0.14, 0.14, 0.14, 0.14, 0.20)
    # Grind: a 10-turn win yields grind_frac * xp_to_next(L) * taper
    grind_frac: float = 0.70      # early-round fraction of a level per grind win
    grind_taper_tau: float = 3.6  # levels-from-cap at which grind XP halves
    grind_taper_floor: float = 0.20
    # Money (cash units; 10 = one R1 wild purse)
    payout_wild: float = 10.0
    payout_crew: float = 25.0
    payout_boss: float = 80.0
    round_mult: tuple = (1.00, 1.15, 1.35)
    grind_payout_frac: float = 0.55
    debt_amount: float = 160.0    # retargeted; 60/60 modest R1 should clear
    debt_share: float = 0.65
    wholesale: float = 0.20
    # Mods: 6 slots, 3 tiers. Prices are per slot (upgrade cost to that tier).
    # T2/T3 prices are the incremental upgrade, not the full replacement.
    price_t1: float = 16.0
    price_t2: float = 28.0
    price_t3: float = 40.0
    aero_price_mult: float = 1.75   # one aero, vs the regular mod it replaces
    aero_pool_frac: float = 0.10    # live 10% of that one part's total
    aero_unlock_after: str = "R1"   # end of R1
    # Floors (level). Must be <= that round's cap.
    floor_t1: int = 0
    floor_t2: int = 13              # start of R2
    floor_t3: int = 30              # start of R3
    # Betting (unlock end R2)
    bet_min: float = 5.0
    bet_max: float = 20.0           # bound so even a lucky finale streak can't break caps
    bet_payout_odds: float = 1.0    # net profit = stake * odds on a win
    # Target-r variant
    r_variant: str = "C"


def xp_to_next(L: int, p: EconParams) -> float:
    return p.xp0 * (p.xp_growth ** max(0, L))


def story_xp_for_rung(rnd: int, j: int, enter_L: int, cap_L: int, p: EconParams) -> float:
    """XP awarded after winning story rung j of this round."""
    # Total XP to climb enter_L -> cap_L
    total = sum(xp_to_next(L, p) for L in range(enter_L, cap_L))
    w = p.story_w[j] / sum(p.story_w)
    return p.story_fill[rnd] * w * total


def grind_xp(L: int, cap_L: int, p: EconParams) -> float:
    dist = max(0, cap_L - L)
    taper = p.grind_taper_floor + (1 - p.grind_taper_floor) * (
        1 - math.exp(-dist / p.grind_taper_tau)
    )
    return p.grind_frac * xp_to_next(L, p) * taper


def apply_xp(L: int, xp: float, bag: float, p: EconParams, cap_L: int):
    """Add xp, return (new_L, new_bag). Does not pass cap_L."""
    bag = bag + xp
    while L < cap_L:
        need = xp_to_next(L, p)
        if bag + 1e-9 < need:
            break
        bag -= need
        L += 1
    if L >= cap_L:
        L = cap_L
        bag = 0.0
    return L, bag


def purse(rnd: int, kind: str, grind: bool, p: EconParams) -> float:
    base = {"kid": p.payout_wild, "mature": p.payout_crew, "old_head": p.payout_crew, "boss": p.payout_boss}[kind]
    pay = base * p.round_mult[rnd]
    if grind:
        pay *= p.grind_payout_frac
    return pay


def opponent_budget(rnd: int, j: int, district: str, variant: str) -> float:
    return C_ROUND[rnd] / target_r(district, j, variant)


def arrival_r(player_P: float, B: float) -> float:
    return player_P / B


# Player power at a level: if the shop has funded the 1.07 cap, player combat
# power used in r is the ceiling, i.e. 1.07 * P_stats, BUT r is defined as
# opponent/player or player/opponent?
# In the existing work, r = player_power / opponent_budget, and at cap
# player_power = C = 1.07 * P, r_at_cap = C / B.
# We set B = C / target_r so r_at_cap = target_r.
# Mid-round, if the player is at level L and has bought mods up to the
# current cap (or as high as money allows), power = min(C_round, 1.07 * P(L))
# if they can afford the cap; else  P(L) + purchased_mod_budget.
#
# Criterion 1 requires the shop CAN fund the full cap. For walk tables we
# assume a player who has the money equips to min(C_round, 1.07*P(L)).
# A cash-poor walk uses stats-only 1.00*P plus whatever they bought.

def combat_power(L: float, rnd: int, mods_filled: bool = True) -> float:
    """Combat power used in r = player / opponent.

    L=0 R1 opener: stock car, no cap mods (k=1.00). After the first level
    (or once T1 can be bought mid-R1) the 1.07 cap applies, clipped to the
    current round ceiling.
    """
    P = power_at_level(L)
    if not mods_filled or (rnd == 0 and L <= 0):
        return P
    return min(C_ROUND[rnd], K_CAP * P)


# ---------------------------------------------------------------------------
# Season walk
# ---------------------------------------------------------------------------
@dataclass
class RungResult:
    rnd: int
    district: str
    j: int
    name: str
    T: int
    kind: str
    B: float
    target_r: float
    arrive_L: int
    arrive_P: float
    arrive_C: float
    arrive_r: float
    wr: dict          # profile -> {win, limp, exact, r_used}
    grind_to_50: dict  # profile -> (n_grind, L_after, r_after, wr_after)
    grind_to_cap: int
    L_after_story: int
    money_after: float
    debt_left: float


def _wr_pack(profile, r, T, district, allow_interp=True):
    from wr import wr as wr_fn
    # Touge: also report uphill/downhill. Street boss: S1 CW/CCW.
    out = {}
    win, r_used, exact, src = wr_fn(profile, r, T, district=district, allow_interp=allow_interp)
    out["district"] = dict(win=round(win, 1), r_used=r_used, exact=exact, src=src)
    if district == "touge":
        for trk, label in (("T_Uphill", "uphill"), ("T_Downhill", "downhill")):
            w, ru, ex, src = wr_fn(profile, r, T, track=trk, allow_interp=allow_interp)
            out[label] = dict(win=round(w, 1), r_used=ru, exact=ex, src=src)
    return out


def grind_count_to_r(L, bag, cap_L, B, rnd, r_goal, p, max_n=80):
    """How many 10-turn grind wins to reach arrival r >= r_goal (or cap)."""
    n = 0
    while n < max_n:
        P = combat_power(L, rnd, True)
        if P / B + 1e-9 >= r_goal or L >= cap_L:
            return n, L, bag, P / B
        L, bag = apply_xp(L, grind_xp(L, cap_L, p), bag, p, cap_L)
        n += 1
    return n, L, bag, combat_power(L, rnd, True) / B


def grind_count_to_cap(L, bag, cap_L, p, max_n=200):
    n = 0
    while L < cap_L and n < max_n:
        L, bag = apply_xp(L, grind_xp(L, cap_L, p), bag, p, cap_L)
        n += 1
    return n, L, bag


def walk_round(rnd, enter_L, enter_bag, enter_money, enter_debt, p: EconParams,
               profiles=("c6060", "c6080", "c8060", "c8080"),
               grind_policy="mixed_wall"):
    """Walk one round.

    grind_policy:
      'story'      — no grind (used for 80/80 criterion 3 and no-grind walks)
      'mixed_wall' — grind at the first rung where mixed (worse of 60/80,80/60)
                     district WR < 50%, enough to restore >=50%, then after
                     that wall grind toward cap before the boss (recorded,
                     not auto-applied mid-lieutenant unless policy says so)
      'always_cap' — grind to cap at every rung (60/60 hard path upper bound)
    Returns list[RungResult], final (L, bag, money, debt).
    """
    district = DISTRICTS[rnd]
    cap_L = CAP_L[rnd]
    L, bag, money, debt = enter_L, enter_bag, enter_money, enter_debt
    rows = []
    for j, (name, T, kind) in enumerate(LADDER_RUNGS):
        B = opponent_budget(rnd, j, district, p.r_variant)
        tr = target_r(district, j, p.r_variant)
        arrive_L = L
        arrive_P = combat_power(L, rnd, True)
        arrive_r = arrive_P / B
        wr_map = {}
        for pr in profiles:
            try:
                wr_map[pr] = _wr_pack(pr, arrive_r, T, district, allow_interp=True)
            except Exception as e:
                wr_map[pr] = {"error": str(e)}

        # grind-to-50 for each profile (10-turn grind at this cap)
        g50 = {}
        for pr in profiles:
            # find r where this profile, this T (20/30) or 10-turn? "grind races"
            # are 10-turn, but the *rung* is T. We grind 10-turn then re-fight the rung.
            # We search n such that WR(profile, new_r, T) >= 50.
            n, Ln, bagn, rn = 0, L, bag, arrive_r
            wr_now = wr_map[pr].get("district", {}).get("win", 0) if "district" in wr_map[pr] else 0
            # For Touge 80/80 criterion we also care about uphill; for mixed wall, district mean.
            target_cell = "uphill" if (district == "touge" and T == 30 and pr == "c8080") else "district"
            wr_now = wr_map[pr].get(target_cell, wr_map[pr].get("district", {})).get("win", 0)
            if wr_now >= 50 or L >= cap_L:
                g50[pr] = dict(n=0, L=L, r=round(arrive_r, 4), wr=wr_now)
            else:
                # binary-ish increment
                Ln, bagn = L, bag
                found = None
                for ntry in range(1, 81):
                    Ln, bagn = apply_xp(Ln, grind_xp(Ln, cap_L, p), bagn, p, cap_L)
                    rn = combat_power(Ln, rnd, True) / B
                    try:
                        pack = _wr_pack(pr, rn, T, district, allow_interp=True)
                    except Exception:
                        pack = wr_map[pr]
                    w = pack.get(target_cell, pack.get("district", {})).get("win", 0)
                    if w >= 50 or Ln >= cap_L:
                        found = dict(n=ntry, L=Ln, r=round(rn, 4), wr=w)
                        break
                if found is None:
                    found = dict(n=80, L=Ln, r=round(rn, 4), wr=None, note="not_reached")
                g50[pr] = found

        n_cap, _, _ = grind_count_to_cap(L, bag, cap_L, p)

        # Apply policy for the continuing walker (used as the 'canonical' money/XP walk:
        # 60/60 modest / mixed-wall: grind at first <50% mixed rung only, then
        # the rest of the round stays story-only until we record grind-to-cap
        # at the boss. Money from mixed-wall grinds is credited.
        applied = 0
        if grind_policy == "always_cap":
            applied, L, bag = grind_count_to_cap(L, bag, cap_L, p)[0], *apply_until_cap(L, bag, cap_L, p)
        elif grind_policy == "mixed_wall":
            # worse mixed WR
            mixed_w = []
            for pr in ("c6080", "c8060"):
                cell = wr_map.get(pr, {}).get("district", {})
                if cell:
                    mixed_w.append(cell.get("win", 100))
            if mixed_w and min(mixed_w) < 50 and L < cap_L:
                # grind the worse mixed up to 50
                worse = "c6080" if wr_map["c6080"]["district"]["win"] <= wr_map["c8060"]["district"]["win"] else "c8060"
                applied = g50[worse]["n"]
                # actually apply
                for _ in range(applied):
                    L, bag = apply_xp(L, grind_xp(L, cap_L, p), bag, p, cap_L)
                    money += purse(rnd, "kid", True, p)
        # story purse + XP after the (possible) grind, then the story race
        # Money: one story purse of this kind, 65% to debt while debt remains
        pay = purse(rnd, kind, False, p)
        if debt > 0:
            take = min(debt, p.debt_share * pay)
            debt -= take
            money += pay - take
        else:
            money += pay
        L, bag = apply_xp(L, story_xp_for_rung(rnd, j, enter_L if j == 0 else enter_L, cap_L, p), bag, p, cap_L)
        # The enter_L used in story_xp should be the round-enter level, not mid-round.
        # (already passed; we re-pass enter_L always — good, total is computed from enter->cap)

        rows.append(RungResult(
            rnd=rnd + 1, district=district, j=j, name=name, T=T, kind=kind,
            B=round(B, 2), target_r=tr,
            arrive_L=arrive_L, arrive_P=round(arrive_P, 2),
            arrive_C=round(arrive_P, 2), arrive_r=round(arrive_r, 4),
            wr=wr_map, grind_to_50=g50, grind_to_cap=n_cap,
            L_after_story=L, money_after=round(money, 2), debt_left=round(debt, 2),
        ))
    return rows, L, bag, money, debt


def apply_until_cap(L, bag, cap_L, p):
    n, L, bag = grind_count_to_cap(L, bag, cap_L, p)
    return L, bag


# Fix story_xp: must use the ROUND enter level consistently — already the case
# if the caller passes enter_L. In walk_round I used enter_L even after grind
# in the loop; good.
