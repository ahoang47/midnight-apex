"""USD betting audit, Variant C. Honest shop (no T1+T2 stack), T2/T3 floors, 1.07 cap.

Betting unlocks after R2: R3 grind, R3 ladder, and finale. Even odds unless policy says otherwise.
"""
from __future__ import annotations
import json, math, os, sys, random
from dataclasses import dataclass
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from model import (
    EconParams, CAP_L, C_ROUND, P_ROUND, FINALE_C, FINALE_L, FINALE_B, FINALE_DIST, FINALE_R_C,
    LADDER_RUNGS, DISTRICTS, opponent_budget, power_at_level,
    story_xp_for_rung, grind_xp, apply_xp,
)
from evaluate import wr_cell, hard_win, PROFILES

WILD, CREW, BOSS = 1000.0, 2500.0, 8000.0
ROUND_MULT = (1.00, 1.15, 1.35)
GRIND_FRAC_PAY = 0.55
DEBT_AMOUNT = 16000.0
DEBT_SHARE = 0.65
PRICE_T1, PRICE_T2, PRICE_T3 = 1600.0, 2800.0, 4000.0
AERO_MULT = 1.75
PRICE_AERO_T3 = PRICE_T3 * AERO_MULT  # 7000
BET_MIN, BET_MAX = 500.0, 2000.0
T3_BEST = 5 * PRICE_T3 + PRICE_AERO_T3  # 27000
T1_ALL, T2_ALL = 6 * PRICE_T1, 6 * PRICE_T2
BUILD_TOTAL = T1_ALL + T2_ALL + T3_BEST  # 53400
FLOOR_T2, FLOOR_T3 = 13, 30
FINALE_PURSE = BOSS * ROUND_MULT[2]  # 10800 (assumption: not in canon)
FINALE_GRIND_PAY = WILD * ROUND_MULT[2] * GRIND_FRAC_PAY  # 742.50
SLOT_T1 = 0.27 * P_ROUND[0] / 6.0
SLOT_T2 = 0.27 * P_ROUND[1] / 6.0
SLOT_T3 = 0.27 * P_ROUND[2] / 6.0

XP = EconParams(story_fill=(0.62, 0.75, 0.80), grind_frac=0.70,
                grind_taper_tau=3.6, grind_taper_floor=0.20, r_variant="C",
                payout_wild=WILD, payout_crew=CREW, payout_boss=BOSS,
                debt_amount=DEBT_AMOUNT, price_t1=PRICE_T1, price_t2=PRICE_T2,
                price_t3=PRICE_T3, bet_min=BET_MIN, bet_max=BET_MAX)
VARIANT = "C"
N_R3 = 4000
N_FARM = 4000
N_FINALE = 1500
SEED = 20261113

_WR = {}
def wr_for(pr, r, T, district, hard=False):
    key = (pr, round(r, 6), T, district, hard)
    if key not in _WR:
        pack = wr_cell(pr, r, T, district, True)
        p = (hard_win(pack) if hard else pack["district"]["win"]) / 100.0
        _WR[key] = max(0.0, min(1.0, p))
    return _WR[key]


def pay_story(kind, rnd):
    return {"kid": WILD, "mature": CREW, "old_head": CREW, "boss": BOSS}[kind] * ROUND_MULT[rnd]


def pay_grind(rnd):
    return WILD * ROUND_MULT[rnd] * GRIND_FRAC_PAY


def combat(L, n_t1, n_t2, n_t3_reg, n_aero, content_C):
    """Slot is T3 or T2 or T1, never stacked. Aero is 1.75x T3 on one slot."""
    P = power_at_level(L)
    n_t3_slots = n_t3_reg + n_aero
    n_t2_only = max(0, n_t2 - n_t3_slots)
    n_t1_only = max(0, n_t1 - n_t2)
    have = (n_t1_only * SLOT_T1 + n_t2_only * SLOT_T2
            + n_t3_reg * SLOT_T3 + n_aero * SLOT_T3 * AERO_MULT)
    if n_t1 + n_t2 + n_t3_reg + n_aero == 0 and L <= 0:
        raw = P
    else:
        raw = 0.80 * P + have
    return min(raw, 1.07 * P, content_C)


@dataclass
class State:
    L: int = 0
    bag: float = 0.0
    money: float = 0.0
    debt: float = DEBT_AMOUNT
    n_t1: int = 0
    n_t2: int = 0
    n_t3_reg: int = 0
    n_aero: int = 0
    races: int = 0
    grind_races: int = 0
    grind_wins: int = 0
    bets: int = 0
    bets_this_round: int = 0
    bet_wagered: float = 0.0
    bet_profit: float = 0.0
    min_money: float = 0.0
    wiped: bool = False  # money resolved below BET_MIN
    zeroed: bool = False
    t3_funded_races: int | None = None
    t3_funded_grind_wins: int | None = None
    t3_funded_L: int | None = None
    t3_before_boss: bool = False
    stuck: bool = False

    @property
    def t3_done(self):
        return self.n_t3_reg >= 5 and self.n_aero == 1


def shop(s: State):
    while s.n_t1 < 6 and s.money + 1e-9 >= PRICE_T1:
        s.money -= PRICE_T1
        s.n_t1 += 1
    if s.L >= FLOOR_T2:
        while s.n_t2 < s.n_t1 and s.n_t2 < 6 and s.money + 1e-9 >= PRICE_T2:
            s.money -= PRICE_T2
            s.n_t2 += 1
    if s.L >= FLOOR_T3:
        while s.n_t3_reg < 5 and s.n_t2 > s.n_t3_reg + s.n_aero and s.money + 1e-9 >= PRICE_T3:
            s.money -= PRICE_T3
            s.n_t3_reg += 1
        if s.n_aero == 0 and (s.n_t2 > s.n_t3_reg + s.n_aero) and s.money + 1e-9 >= PRICE_AERO_T3:
            s.money -= PRICE_AERO_T3
            s.n_aero = 1
    if s.t3_funded_races is None and s.t3_done:
        s.t3_funded_races = s.races
        s.t3_funded_grind_wins = s.grind_wins
        s.t3_funded_L = s.L


def credit(s: State, amount: float):
    if s.debt > 0:
        take = min(s.debt, DEBT_SHARE * amount)
        s.debt -= take
        s.money += amount - take
    else:
        s.money += amount
    shop(s)
    _mark_min(s)


def _mark_min(s: State):
    if s.money < s.min_money:
        s.min_money = s.money
    if s.money < BET_MIN - 1e-9:
        s.wiped = True
    if s.money <= 1e-9:
        s.zeroed = True


def bet_cap(policy, purse):
    if policy == "max500":
        return 500.0
    if policy == "cap_purse":
        return min(BET_MAX, purse)
    return BET_MAX


def want_bet(policy, p_win, is_grind, s: State, limit=3):
    if policy == "none":
        return False
    if policy == "story_only" and is_grind:
        return False
    if policy == "likely65" and p_win < 0.65:
        return False
    if policy == "likely50" and p_win < 0.50:
        return False
    if policy == "limit3" and s.bets_this_round >= limit:
        return False
    return True


def stake_for(policy, p_win, money, purse, is_grind, s: State):
    if not want_bet(policy, p_win, is_grind, s):
        return 0.0
    cap = bet_cap(policy, purse)
    if money + 1e-9 >= cap and cap + 1e-9 >= BET_MIN:
        return cap
    if money + 1e-9 >= BET_MIN:
        # bet whatever we have, floored to $50
        got = math.floor(money / 50.0) * 50.0
        return got if got + 1e-9 >= BET_MIN else 0.0
    return 0.0


def odds_net(policy, p_win):
    if policy == "fair_odds":
        p = min(max(p_win, 0.05), 0.95)
        return (1.0 - p) / p
    return 1.0


def resolve_race(rng, s, p_win, purse, policy, is_grind, xp_amt, cap_L):
    stake = stake_for(policy, p_win, s.money, purse, is_grind, s)
    if stake > 0:
        s.bets += 1
        s.bets_this_round += 1
        s.bet_wagered += stake
        s.money -= stake
    s.races += 1
    if is_grind:
        s.grind_races += 1
    win = rng.random() < p_win
    if win:
        if is_grind:
            s.grind_wins += 1
        if stake > 0:
            net = stake * odds_net(policy, p_win)
            s.money += stake + net
            s.bet_profit += net
        credit(s, purse)
        if xp_amt and s.L < cap_L:
            s.L, s.bag = apply_xp(s.L, xp_amt, s.bag, XP, cap_L)
            shop(s)
            _mark_min(s)
        return True
    else:
        if stake > 0:
            s.bet_profit -= stake
        _mark_min(s)
        return False


def try_until_win(rng, s, p_win, purse, policy, is_grind, xp_amt, cap_L, max_tries=60):
    # Hopeless fight: don't spin 60 times unless the policy is actually betting.
    if p_win <= 0.002:
        # greedy always-max still throws money at it until wiped or cap
        n = 0
        while n < min(max_tries, 20):
            n += 1
            if resolve_race(rng, s, p_win, purse, policy, is_grind, xp_amt, cap_L):
                return n, True
            if s.money < BET_MIN and not want_bet(policy, p_win, is_grind, s):
                break
            if not want_bet(policy, p_win, is_grind, s) and policy != "always":
                # no-bet / likely* skip: one attempt is enough to know we're stuck
                if n >= 3:
                    break
        s.stuck = True
        return n, False
    for n in range(1, max_tries + 1):
        if resolve_race(rng, s, p_win, purse, policy, is_grind, xp_amt, cap_L):
            return n, True
    s.stuck = True
    return max_tries, False


def arrival(s, B, content):
    c = combat(s.L, s.n_t1, s.n_t2, s.n_t3_reg, s.n_aero, content)
    return c / B, c


def clone(s: State) -> State:
    t = State()
    for k, v in s.__dict__.items():
        setattr(t, k, v)
    return t


def walk_pre_R3(pr, grind_mode):
    s = State(debt=DEBT_AMOUNT, min_money=0.0)
    shop(s)
    for rnd in range(2):
        district = DISTRICTS[rnd]
        cap_L = CAP_L[rnd]
        enter_round_L = s.L
        mixed_wall_done = False
        for j, (name, T, kind) in enumerate(LADDER_RUNGS):
            B = opponent_budget(rnd, j, district, VARIANT)
            if name == "boss" and grind_mode in ("mixed", "hard") and s.L < cap_L:
                while s.L < cap_L:
                    s.races += 1
                    s.grind_races += 1
                    s.grind_wins += 1
                    credit(s, pay_grind(rnd))
                    s.L, s.bag = apply_xp(s.L, grind_xp(s.L, cap_L, XP), s.bag, XP, cap_L)
                    shop(s)
            if name != "boss" and s.L < cap_L:
                rr, _ = arrival(s, B, C_ROUND[rnd])
                need = False
                if grind_mode == "mixed" and not mixed_wall_done:
                    stuck = False
                    for pr2 in ("c6080", "c8060"):
                        if wr_for(pr2, rr, T, district, False) < 0.50:
                            stuck = True
                        if T >= 20 and wr_for(pr2, rr, T, district, True) < 0.50:
                            stuck = True
                    if stuck:
                        need = True
                        mixed_wall_done = True
                elif grind_mode == "hard":
                    if wr_for("c6060", rr, T, district, T >= 20) < 0.50:
                        need = True
                if need:
                    guard = 0
                    while s.L < cap_L and guard < 80:
                        rr2, _ = arrival(s, B, C_ROUND[rnd])
                        ok = True
                        if grind_mode == "mixed":
                            for pr2 in ("c6080", "c8060"):
                                if wr_for(pr2, rr2, T, district, False) < 0.50:
                                    ok = False
                                if T >= 20 and wr_for(pr2, rr2, T, district, True) < 0.50:
                                    ok = False
                        else:
                            if wr_for("c6060", rr2, T, district, T >= 20) < 0.50:
                                ok = False
                        if ok:
                            break
                        s.races += 1
                        s.grind_races += 1
                        s.grind_wins += 1
                        credit(s, pay_grind(rnd))
                        s.L, s.bag = apply_xp(s.L, grind_xp(s.L, cap_L, XP), s.bag, XP, cap_L)
                        shop(s)
                        guard += 1
            s.races += 1
            credit(s, pay_story(kind, rnd))
            s.L, s.bag = apply_xp(s.L, story_xp_for_rung(rnd, j, enter_round_L, cap_L, XP), s.bag, XP, cap_L)
            shop(s)
        if grind_mode in ("mixed", "hard") and s.L < cap_L:
            while s.L < cap_L:
                s.races += 1
                s.grind_races += 1
                s.grind_wins += 1
                credit(s, pay_grind(rnd))
                s.L, s.bag = apply_xp(s.L, grind_xp(s.L, cap_L, XP), s.bag, XP, cap_L)
                shop(s)
        if grind_mode in ("mixed", "hard"):
            s.L, s.bag = cap_L, 0.0
            shop(s)
    return s


def mixed_stuck(rr, T, district):
    for pr2 in ("c6080", "c8060"):
        if wr_for(pr2, rr, T, district, False) < 0.50:
            return True
        if T >= 20 and wr_for(pr2, rr, T, district, True) < 0.50:
            return True
    return False


def walk_R3(s, pr, grind_mode, policy, rng):
    rnd = 2
    district = "touge"
    cap_L = CAP_L[2]
    enter_L = s.L
    s.bets_this_round = 0
    mixed_wall_done = False
    rungs = []
    for j, (name, T, kind) in enumerate(LADDER_RUNGS):
        B = opponent_budget(rnd, j, district, VARIANT)
        if name == "boss" and grind_mode in ("mixed", "hard") and s.L < cap_L:
            guard = 0
            while s.L < cap_L and guard < 80:
                Bw = opponent_budget(rnd, 0, district, VARIANT)
                rr, _ = arrival(s, Bw, C_ROUND[2])
                p = wr_for(pr, rr, 10, district, False)
                try_until_win(rng, s, p, pay_grind(rnd), policy, True,
                              grind_xp(s.L, cap_L, XP), cap_L)
                guard += 1
        if name != "boss" and s.L < cap_L:
            rr, _ = arrival(s, B, C_ROUND[2])
            need = False
            if grind_mode == "mixed" and not mixed_wall_done and mixed_stuck(rr, T, district):
                need = True
                mixed_wall_done = True
            elif grind_mode == "hard" and wr_for("c6060", rr, T, district, T >= 20) < 0.50:
                need = True
            if need:
                guard = 0
                while s.L < cap_L and guard < 80:
                    rr2, _ = arrival(s, B, C_ROUND[2])
                    ok = True
                    if grind_mode == "mixed":
                        if mixed_stuck(rr2, T, district):
                            ok = False
                    else:
                        if wr_for("c6060", rr2, T, district, T >= 20) < 0.50:
                            ok = False
                    if ok:
                        break
                    Bw = opponent_budget(rnd, 0, district, VARIANT)
                    rrw, _ = arrival(s, Bw, C_ROUND[2])
                    p = wr_for(pr, rrw, 10, district, False)
                    try_until_win(rng, s, p, pay_grind(rnd), policy, True,
                                  grind_xp(s.L, cap_L, XP), cap_L)
                    guard += 1
        # flag T3 before this official race (especially the boss)
        if name == "boss" and s.t3_done:
            s.t3_before_boss = True
        rr, cbt = arrival(s, B, C_ROUND[2])
        p = wr_for(pr, rr, T, district, T >= 20 or name == "boss")
        had_t3 = s.t3_done
        tries, won = try_until_win(rng, s, p, pay_story(kind, rnd), policy, False,
                                   story_xp_for_rung(rnd, j, enter_L, cap_L, XP), cap_L)
        rungs.append(dict(
            name=name, L=s.L, arrive_r=round(rr, 4), wr=round(p * 100, 1),
            combat=round(cbt, 2), fill=round(cbt / C_ROUND[2], 4),
            tries=tries, won=won, t3_on_arrive=had_t3,
            money=round(s.money, 1),
        ))
        if not won:
            break
    return rungs


def walk_finale(s, pr, policy, rng, scaled=True):
    logs = []
    for i, (Bfin, dist, rstar, Cfin, Lf) in enumerate(
        zip(FINALE_B, FINALE_DIST, FINALE_R_C, FINALE_C, FINALE_L)
    ):
        s.bets_this_round = 0  # per-step limit for limit3
        guard = 0
        while s.L < Lf and guard < 200:
            Bw = (Cfin / 1.18) if scaled else opponent_budget(2, 0, "touge", VARIANT)
            rr, _ = arrival(s, Bw, Cfin)
            p = wr_for(pr, rr, 10, dist, False)
            won_g = try_until_win(rng, s, p, FINALE_GRIND_PAY, policy, True,
                                  grind_xp(s.L, Lf, XP), Lf)[1]
            if not won_g:
                # if a grind is hopeless, stop leveling
                break
            guard += 1
        rr, cbt = arrival(s, Bfin, Cfin)
        p = wr_for(pr, rr, 30, dist, True)
        tries, won = try_until_win(rng, s, p, FINALE_PURSE, policy, False, 0.0, Lf)
        logs.append(dict(
            step=i + 1, dist=dist, rstar=rstar, L=s.L, money=round(s.money, 1),
            arrive_r=round(rr, 4), wr=round(p * 100, 1), combat=round(cbt, 2),
            cap=round(Cfin, 2), fill=round(cbt / Cfin, 4), tries=tries, won=won,
            t3=int(s.t3_done), wiped=s.wiped, zeroed=s.zeroed,
            bet_profit=round(s.bet_profit, 1), bets=s.bets,
        ))
        if not won:
            break
    return logs


def farm_t3(s, pr, policy, rng, max_races=200):
    """Wild-only farm from this state until T3 is bought (L30 floor binds)."""
    cap_L = CAP_L[2]
    district = "touge"
    Bw = opponent_budget(2, 0, district, VARIANT)
    start_races, start_gw, start_gr = s.races, s.grind_wins, s.grind_races
    while (not s.t3_done) and (s.grind_races - start_gr) < max_races:
        rr, _ = arrival(s, Bw, C_ROUND[2])
        p = wr_for(pr, rr, 10, district, False)
        try_until_win(rng, s, p, pay_grind(2), policy, True,
                      grind_xp(s.L, cap_L, XP), cap_L)
        if s.zeroed and s.money < BET_MIN and p < 0.45 and policy == "always":
            # ruined mid-farm
            break
    return dict(
        funded=s.t3_done,
        grind_attempts=s.grind_races - start_gr,
        grind_wins=s.grind_wins - start_gw,
        races=s.races - start_races,
        L=s.L,
        money=round(s.money, 1),
        wiped=s.wiped,
        zeroed=s.zeroed,
        bet_profit=round(s.bet_profit, 1),
        stuck_unfunded=not s.t3_done,
    )


def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    i = min(len(xs) - 1, max(0, int(round(p * (len(xs) - 1)))))
    return xs[i]


def stats(xs, nd=2):
    xs = [v for v in xs if v is not None and v == v]
    if not xs:
        return None
    return dict(mean=round(sum(xs) / len(xs), nd),
                p10=round(q(xs, 0.10), nd), p50=round(q(xs, 0.50), nd),
                p90=round(q(xs, 0.90), nd), min=round(min(xs), nd), max=round(max(xs), nd))


def pct(xs):
    return round(100.0 * sum(1 for v in xs if v) / len(xs), 2) if xs else None


MODE = {"c8080": "story", "c6080": "mixed", "c8060": "mixed", "c6060": "hard"}
BASE = ("none", "likely65", "likely50", "always")
FIXES = ("story_only", "cap_purse", "fair_odds", "max500", "limit3")


def snap_entry(s):
    return dict(L=s.L, money=round(s.money, 1), debt=round(s.debt, 1),
                t1=s.n_t1, t2=s.n_t2, t3=s.n_t3_reg, aero=s.n_aero,
                remaining_T3=round(max(0, T3_BEST - s.money), 1),
                races=s.races, grind_wins=s.grind_wins)


def main():
    print("pre-R3 entries...", flush=True)
    entries = {}
    for pr in PROFILES:
        entries[pr] = walk_pre_R3(pr, MODE[pr])
        e = entries[pr]
        print(f"  {pr} {MODE[pr]} L={e.L} ${e.money:.0f} debt=${e.debt:.0f} "
              f"T1={e.n_t1} T2={e.n_t2} T3={e.n_t3_reg}+a{e.n_aero}", flush=True)

    entry_report = {}
    Bkid = opponent_budget(2, 0, "touge", VARIANT)
    Bboss = opponent_budget(2, 6, "touge", VARIANT)
    for pr, s in entries.items():
        r_k, c = arrival(s, Bkid, C_ROUND[2])
        rec = dict(**snap_entry(s),
                   combat=round(c, 2), fill_vs_C3=round(c / C_ROUND[2], 4),
                   r_kid=round(r_k, 4), wr10=round(wr_for(pr, r_k, 10, "touge", False) * 100, 1),
                   cap_binds_at_entry=abs(c - min(1.07 * power_at_level(s.L), C_ROUND[2])) < 0.05)
        entry_report[pr] = rec
        print(f"  entry wr {pr}: {rec}", flush=True)

    results = {
        "costs": dict(T1_ALL=T1_ALL, T2_ALL=T2_ALL, T3_BEST=T3_BEST, BUILD_TOTAL=BUILD_TOTAL,
                      PRICE_AERO_T3=PRICE_AERO_T3, FINALE_PURSE=FINALE_PURSE,
                      FINALE_GRIND_PAY=FINALE_GRIND_PAY,
                      assumption_finale_purse="R3 boss purse $10,800 (not specified in canon)"),
        "entry": entry_report,
        "farm": {},
        "r3": {},
        "finale": {},
    }

    # ---- wild-only T3 farm ----
    for pr in PROFILES:
        results["farm"][pr] = {}
        for pol in BASE + FIXES:
            rows = []
            for i in range(N_FARM):
                rng = random.Random(SEED + 1000 + i * 31 + (hash(pr + pol) % 99991))
                s = clone(entries[pr])
                s.min_money = s.money
                s.wiped = s.zeroed = False
                rows.append(farm_t3(s, pr, pol, rng))
            results["farm"][pr][pol] = dict(
                n=N_FARM,
                funded_pct=pct([r["funded"] for r in rows]),
                wiped_pct=pct([r["wiped"] for r in rows]),
                zeroed_pct=pct([r["zeroed"] for r in rows]),
                grind_attempts=stats([r["grind_attempts"] for r in rows if r["funded"]], 1),
                grind_wins=stats([r["grind_wins"] for r in rows if r["funded"]], 1),
                L_at_fund=stats([r["L"] for r in rows if r["funded"]], 1),
                money_left=stats([r["money"] for r in rows if r["funded"]], 1),
                bet_profit=stats([r["bet_profit"] for r in rows], 1),
            )
            sm = results["farm"][pr][pol]
            print(f"farm {pr} {pol}: funded={sm['funded_pct']}% wiped={sm['wiped_pct']}% "
                  f"wins={sm['grind_wins']} attempts={sm['grind_attempts']}", flush=True)

    # ---- R3 walk MC ----
    # stash one end-R3 clone per (pr, pol) mid trial 0 for finale start variety;
    # finale uses fresh MC from the precomputed entry through R3 again.
    for pr in PROFILES:
        results["r3"][pr] = {}
        for pol in BASE + FIXES:
            rows = []
            for i in range(N_R3):
                rng = random.Random(SEED + 5000 + i * 17 + (hash("r3" + pr + pol) % 99991))
                s = clone(entries[pr])
                s.min_money = s.money
                s.wiped = s.zeroed = False
                rungs = walk_R3(s, pr, MODE[pr], pol, rng)
                boss = next((r for r in rungs if r["name"] == "boss"), None)
                rows.append(dict(
                    t3_done=s.t3_done,
                    t3_before_boss=s.t3_before_boss,
                    t3_races=(None if s.t3_funded_races is None else s.t3_funded_races - entries[pr].races),
                    t3_grind_wins=(None if s.t3_funded_grind_wins is None else s.t3_funded_grind_wins - entries[pr].grind_wins),
                    t3_L=s.t3_funded_L,
                    money=s.money,
                    min_money=s.min_money,
                    wiped=s.wiped,
                    zeroed=s.zeroed,
                    stuck=s.stuck,
                    bet_profit=s.bet_profit,
                    bets=s.bets,
                    grind_wins=s.grind_wins - entries[pr].grind_wins,
                    grind_races=s.grind_races - entries[pr].grind_races,
                    L=s.L,
                    boss=boss,
                    rungs=rungs,
                ))
            bosses = [r["boss"] for r in rows if r["boss"]]
            results["r3"][pr][pol] = dict(
                n=N_R3,
                t3_funded_pct=pct([r["t3_done"] for r in rows]),
                t3_before_boss_pct=pct([r["t3_before_boss"] for r in rows]),
                stuck_pct=pct([r["stuck"] for r in rows]),
                wiped_pct=pct([r["wiped"] for r in rows]),
                zeroed_pct=pct([r["zeroed"] for r in rows]),
                money_end=stats([r["money"] for r in rows], 1),
                min_money=stats([r["min_money"] for r in rows], 1),
                bet_profit=stats([r["bet_profit"] for r in rows], 1),
                bets=stats([r["bets"] for r in rows], 1),
                t3_grind_wins=stats([r["t3_grind_wins"] for r in rows if r["t3_done"]], 1),
                t3_races=stats([r["t3_races"] for r in rows if r["t3_done"]], 1),
                t3_L=stats([r["t3_L"] for r in rows if r["t3_done"]], 1),
                R3_grind_wins=stats([r["grind_wins"] for r in rows], 1),
                boss_reached_pct=pct([r["boss"] is not None for r in rows]),
                boss_wr=stats([b["wr"] for b in bosses], 1),
                boss_r=stats([b["arrive_r"] for b in bosses], 4),
                boss_fill=stats([b["fill"] for b in bosses], 4),
                boss_tries=stats([b["tries"] for b in bosses], 2),
                boss_t3_on_arrive_pct=pct([b["t3_on_arrive"] for b in bosses]),
                # per-rung T3-on-arrive and WR (means)
                rungs={name: dict(
                    n=sum(1 for r in rows if any(x["name"] == name for x in r["rungs"])),
                    wr=stats([next(x["wr"] for x in r["rungs"] if x["name"] == name)
                              for r in rows if any(x["name"] == name for x in r["rungs"])], 1),
                    r=stats([next(x["arrive_r"] for x in r["rungs"] if x["name"] == name)
                             for r in rows if any(x["name"] == name for x in r["rungs"])], 4),
                    t3_pct=pct([next(x["t3_on_arrive"] for x in r["rungs"] if x["name"] == name)
                                for r in rows if any(x["name"] == name for x in r["rungs"])]),
                    tries=stats([next(x["tries"] for x in r["rungs"] if x["name"] == name)
                                 for r in rows if any(x["name"] == name for x in r["rungs"])], 2),
                ) for name, _, _ in LADDER_RUNGS},
            )
            sm = results["r3"][pr][pol]
            print(f"R3 {pr} {pol}: t3={sm['t3_funded_pct']}% before_boss={sm['t3_before_boss_pct']}% "
                  f"wiped={sm['wiped_pct']}% boss_wr={sm['boss_wr']} fill={sm['boss_fill']} "
                  f"money={sm['money_end']}", flush=True)

    # ---- Finale MC (none / always / recommended fixes) for all profiles ----
    finale_pols = ("none", "likely65", "always", "story_only", "fair_odds", "max500")
    for pr in PROFILES:
        results["finale"][pr] = {}
        for pol in finale_pols:
            rows = []
            for i in range(N_FINALE):
                rng = random.Random(SEED + 9000 + i * 13 + (hash("f" + pr + pol) % 99991))
                s = clone(entries[pr])
                s.min_money = s.money
                s.wiped = s.zeroed = False
                walk_R3(s, pr, MODE[pr], pol, rng)
                # reset wiped? no — keep through finale. But min_money continues.
                flog = walk_finale(s, pr, pol, rng, scaled=True)
                rows.append(dict(
                    money=s.money, min_money=s.min_money, wiped=s.wiped, zeroed=s.zeroed,
                    bet_profit=s.bet_profit, bets=s.bets, L=s.L, stuck=s.stuck,
                    steps_won=sum(1 for x in flog if x["won"]),
                    flog=flog,
                ))
            out = dict(
                n=N_FINALE,
                wiped_pct=pct([r["wiped"] for r in rows]),
                zeroed_pct=pct([r["zeroed"] for r in rows]),
                money_end=stats([r["money"] for r in rows], 1),
                min_money=stats([r["min_money"] for r in rows], 1),
                bet_profit=stats([r["bet_profit"] for r in rows], 1),
                steps_won=stats([r["steps_won"] for r in rows], 2),
                clear_all4_pct=pct([r["steps_won"] >= 4 for r in rows]),
            )
            for i in range(4):
                xs = [r["flog"][i] for r in rows if len(r["flog"]) > i]
                if not xs:
                    out[f"F{i+1}"] = None
                    continue
                out[f"F{i+1}"] = dict(
                    reached_pct=pct([len(r["flog"]) > i for r in rows]),
                    won_pct=pct([len(r["flog"]) > i and r["flog"][i]["won"] for r in rows]),
                    wr=stats([x["wr"] for x in xs], 1),
                    r=stats([x["arrive_r"] for x in xs], 4),
                    fill=stats([x["fill"] for x in xs], 4),
                    tries=stats([x["tries"] for x in xs], 2),
                    money=stats([x["money"] for x in xs], 1),
                    L=stats([x["L"] for x in xs], 1),
                )
            results["finale"][pr][pol] = out
            print(f"FIN {pr} {pol}: wipe={out['wiped_pct']}% clear4={out['clear_all4_pct']}% "
                  f"steps={out['steps_won']} money={out['money_end']}", flush=True)

    fn = os.path.join(HERE, "betting_results.json")
    json.dump(results, open(fn, "w"), indent=1)
    print("wrote", fn, "wr_cache", len(_WR), flush=True)


if __name__ == "__main__":
    main()
