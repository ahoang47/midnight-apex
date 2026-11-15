"""Factorial betting-lever audit + T4 sink. Draft only, no live sim/ edits.

Levers:
  1. unlock: after R2 or after R3 (R3 also has the promoter beat; wholesale already
     ends at the Mentor Confrontation / end of R3 in both cases)
  2. eligible: any, story (ladder/story/billed finale), wild (grind/wild only)
  3. bet-count cap: none, 4, 8, 16 (total bets after unlock)
  4. T4 regular-upgrade price, swept; aero is 1.75x; package = 6.75 * regular
  optional. odds: even (net +1) vs fair (net (1-p)/p)

Likely-win = bet max when WR >= 65% and the levers allow it.
Wholesale 0.20 applies from end of R1 through end of R3 (not to T4, not in R1).
T4 unlocks after R3 at L47, sized to fill 1.07*P at L114 (0.27*P(114) across 6 slots).
"""
from __future__ import annotations
import json, math, os, sys, random, itertools, time
from dataclasses import dataclass, field

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
DEBT_AMOUNT, DEBT_SHARE = 16000.0, 0.65
PRICE_T1, PRICE_T2, PRICE_T3 = 1600.0, 2800.0, 4000.0
AERO_MULT = 1.75
WHOLESALE = 0.20  # off list, end R1 through end R3
BET_MIN, BET_MAX = 500.0, 2000.0
FLOOR_T2, FLOOR_T3, FLOOR_T4 = 13, 30, 47
FINALE_PURSE = BOSS * ROUND_MULT[2]
FINALE_GRIND_PAY = WILD * ROUND_MULT[2] * GRIND_FRAC_PAY
SLOT_T1 = 0.27 * P_ROUND[0] / 6.0
SLOT_T2 = 0.27 * P_ROUND[1] / 6.0
SLOT_T3 = 0.27 * P_ROUND[2] / 6.0
SLOT_T4 = 0.27 * power_at_level(FINALE_L[-1]) / 6.0  # fills 1.07*P at L114
XP = EconParams(story_fill=(0.62, 0.75, 0.80), grind_frac=0.70,
                grind_taper_tau=3.6, grind_taper_floor=0.20, r_variant="C")
VARIANT = "C"
MODE = {"c8080": "story", "c6080": "mixed", "c8060": "mixed", "c6060": "hard"}
N_MC = 400
SEED = 20261113
LIKELY = 0.65

T4_REG_PRICES = (5000.0, 8000.0, 12000.0, 18000.0)
UNLOCKS = ("R2", "R3")
ELIGS = ("any", "story", "wild")
CAPS = (None, 4, 8, 16)
ODDS = ("even", "fair")  # fair only layered on a subset if we need to cut

_WR = {}
def wr_for(pr, r, T, district, hard=False):
    key = (pr, round(float(r), 6), T, district, hard)
    if key not in _WR:
        pack = wr_cell(pr, r, T, district, True)
        p = (hard_win(pack) if hard else pack["district"]["win"]) / 100.0
        _WR[key] = max(0.0, min(1.0, p))
    return _WR[key]

def pay_story(kind, rnd):
    return {"kid": WILD, "mature": CREW, "old_head": CREW, "boss": BOSS}[kind] * ROUND_MULT[rnd]

def pay_grind(rnd):
    return WILD * ROUND_MULT[rnd] * GRIND_FRAC_PAY

def disc(wholesale):
    return (1.0 - WHOLESALE) if wholesale else 1.0

def combat(s, content_C):
    P = power_at_level(s.L)
    n_t4_slots = s.n_t4_reg + s.n_aero4
    n_t3_slots = s.n_t3_reg + s.n_aero3
    # a slot is its highest tier
    n_t3_only = max(0, n_t3_slots - n_t4_slots)
    n_t2_only = max(0, s.n_t2 - max(n_t3_slots, n_t4_slots))
    n_t1_only = max(0, s.n_t1 - s.n_t2)
    # split t3/t4 regular vs aero for the 1.75x aero slot
    # equipped aero is whichever aero tier is highest
    if s.n_aero4:
        aero_have = SLOT_T4 * AERO_MULT
        t4_reg = s.n_t4_reg
        t3_reg = max(0, s.n_t3_reg - t4_reg)  # leftover regular T3 not upgraded; aero was T3 now T4
        # n_t3_reg counts regular only; n_aero3 should be 0 if aero upgraded
        have = (n_t1_only * SLOT_T1 + n_t2_only * SLOT_T2
                + t3_reg * SLOT_T3 + t4_reg * SLOT_T4 + aero_have)
    elif s.n_aero3:
        aero_have = SLOT_T3 * AERO_MULT
        t3_reg = s.n_t3_reg
        t4_reg = s.n_t4_reg
        have = (n_t1_only * SLOT_T1 + n_t2_only * SLOT_T2
                + t3_reg * SLOT_T3 + t4_reg * SLOT_T4 + aero_have)
    else:
        have = (n_t1_only * SLOT_T1 + n_t2_only * SLOT_T2
                + s.n_t3_reg * SLOT_T3 + s.n_t4_reg * SLOT_T4)
    if s.n_t1 + s.n_t2 + s.n_t3_reg + s.n_aero3 + s.n_t4_reg + s.n_aero4 == 0 and s.L <= 0:
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
    n_aero3: int = 0
    n_t4_reg: int = 0
    n_aero4: int = 0
    races: int = 0
    grind_races: int = 0
    grind_wins: int = 0
    bets: int = 0
    bet_profit: float = 0.0
    min_money: float = 0.0
    zeroed: bool = False
    wholesale: bool = False
    post_R3: bool = False
    t4_price: float = 8000.0
    t4_done_races: int | None = None
    t4_done_L: int | None = None
    stuck: bool = False

    @property
    def t3_done(self):
        return self.n_t3_reg >= 5 and (self.n_aero3 + self.n_aero4) >= 1

    @property
    def t4_done(self):
        return self.n_t4_reg >= 5 and self.n_aero4 >= 1

def shop(s: State):
    d = disc(s.wholesale)
    p1, p2, p3, pa3 = PRICE_T1 * d, PRICE_T2 * d, PRICE_T3 * d, PRICE_T3 * AERO_MULT * d
    while s.n_t1 < 6 and s.money + 1e-9 >= p1:
        s.money -= p1
        s.n_t1 += 1
    if s.L >= FLOOR_T2:
        while s.n_t2 < s.n_t1 and s.n_t2 < 6 and s.money + 1e-9 >= p2:
            s.money -= p2
            s.n_t2 += 1
    if s.L >= FLOOR_T3:
        while s.n_t3_reg < 5 and s.n_t2 > s.n_t3_reg + s.n_aero3 + s.n_aero4 and s.money + 1e-9 >= p3:
            s.money -= p3
            s.n_t3_reg += 1
        if s.n_aero3 == 0 and s.n_aero4 == 0 and (s.n_t2 > s.n_t3_reg) and s.money + 1e-9 >= pa3:
            s.money -= pa3
            s.n_aero3 = 1
    if s.post_R3 and s.L >= FLOOR_T4:
        p4 = s.t4_price  # full price, no wholesale
        pa4 = s.t4_price * AERO_MULT
        # need a T3 regular to upgrade
        while s.n_t4_reg < 5 and s.n_t3_reg > s.n_t4_reg and s.money + 1e-9 >= p4:
            s.money -= p4
            s.n_t4_reg += 1
        if s.n_aero4 == 0 and (s.n_aero3 or (s.n_t3_reg > s.n_t4_reg)) and s.money + 1e-9 >= pa4:
            s.money -= pa4
            s.n_aero4 = 1
            s.n_aero3 = 0
    if s.t4_done_races is None and s.t4_done:
        s.t4_done_races = s.races
        s.t4_done_L = s.L

def credit(s, amount):
    if s.debt > 0:
        take = min(s.debt, DEBT_SHARE * amount)
        s.debt -= take
        s.money += amount - take
    else:
        s.money += amount
    shop(s)
    if s.money < s.min_money:
        s.min_money = s.money
    if s.money <= 1e-9:
        s.zeroed = True

def mark_min(s):
    if s.money < s.min_money:
        s.min_money = s.money
    if s.money <= 1e-9:
        s.zeroed = True

def clone(s: State) -> State:
    t = State()
    for k, v in s.__dict__.items():
        setattr(t, k, v)
    return t

def arrival(s, B, content):
    c = combat(s, content)
    return c / B, c

def mixed_stuck(rr, T, district):
    for pr2 in ("c6080", "c8060"):
        if wr_for(pr2, rr, T, district, False) < 0.50:
            return True
        if T >= 20 and wr_for(pr2, rr, T, district, True) < 0.50:
            return True
    return False

def want_bet(cfg, s, p_win, is_grind, unlocked):
    if not unlocked or cfg.get("policy") == "none":
        return False
    if p_win < LIKELY:
        return False
    cap = cfg.get("cap")
    if cap is not None and s.bets >= cap:
        return False
    elig = cfg["elig"]
    if elig == "story" and is_grind:
        return False
    if elig == "wild" and not is_grind:
        return False
    return True

def stake_for(cfg, s, p_win, is_grind, unlocked):
    if not want_bet(cfg, s, p_win, is_grind, unlocked):
        return 0.0
    if s.money + 1e-9 >= BET_MAX:
        return BET_MAX
    if s.money + 1e-9 >= BET_MIN:
        got = math.floor(s.money / 50.0) * 50.0
        return got if got + 1e-9 >= BET_MIN else 0.0
    return 0.0

def odds_net(cfg, p_win):
    if cfg.get("odds") == "fair":
        p = min(max(p_win, 0.05), 0.95)
        return (1.0 - p) / p
    return 1.0

def resolve(rng, s, p_win, purse, cfg, is_grind, xp_amt, cap_L, unlocked):
    stake = stake_for(cfg, s, p_win, is_grind, unlocked)
    if stake > 0:
        s.bets += 1
        s.money -= stake
    s.races += 1
    if is_grind:
        s.grind_races += 1
    win = (rng is None) or (rng.random() < p_win)  # rng is None => official win (no-bet path)
    if rng is None:
        win = True
    if win:
        if is_grind:
            s.grind_wins += 1
        if stake > 0:
            net = stake * odds_net(cfg, p_win)
            s.money += stake + net
            s.bet_profit += net
        credit(s, purse)
        if xp_amt and s.L < cap_L:
            s.L, s.bag = apply_xp(s.L, xp_amt, s.bag, XP, cap_L)
            shop(s)
            mark_min(s)
        return True
    else:
        if stake > 0:
            s.bet_profit -= stake
        mark_min(s)
        return False

def try_win(rng, s, p_win, purse, cfg, is_grind, xp_amt, cap_L, unlocked, max_tries=60):
    if rng is None:
        # official winning path
        resolve(None, s, p_win, purse, cfg, is_grind, xp_amt, cap_L, unlocked)
        return 1, True
    if p_win <= 0.002:
        # likely-win will not bet; a few attempts then stuck
        n = 0
        while n < 3:
            n += 1
            if resolve(rng, s, p_win, purse, cfg, is_grind, xp_amt, cap_L, unlocked):
                return n, True
        s.stuck = True
        return n, False
    for n in range(1, max_tries + 1):
        if resolve(rng, s, p_win, purse, cfg, is_grind, xp_amt, cap_L, unlocked):
            return n, True
    s.stuck = True
    return max_tries, False

def walk_pre_R3(pr, grind_mode, t4_price):
    """Deterministic official-win R1-R2. Wholesale starts at end of R1."""
    s = State(debt=DEBT_AMOUNT, min_money=0.0, wholesale=False, t4_price=t4_price)
    shop(s)
    for rnd in range(2):
        district = DISTRICTS[rnd]
        cap_L = CAP_L[rnd]
        enter_L = s.L
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
                if grind_mode == "mixed" and not mixed_wall_done and mixed_stuck(rr, T, district):
                    need = True
                    mixed_wall_done = True
                elif grind_mode == "hard" and wr_for("c6060", rr, T, district, T >= 20) < 0.50:
                    need = True
                if need:
                    guard = 0
                    while s.L < cap_L and guard < 80:
                        rr2, _ = arrival(s, B, C_ROUND[rnd])
                        ok = True
                        if grind_mode == "mixed":
                            if mixed_stuck(rr2, T, district):
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
            s.L, s.bag = apply_xp(s.L, story_xp_for_rung(rnd, j, enter_L, cap_L, XP), s.bag, XP, cap_L)
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
        if rnd == 0:
            s.wholesale = True  # Reiko's wholesale at end of R1
            shop(s)
    return s

def unlocked_at(cfg, phase):
    """phase: 'R3' or 'finale'."""
    u = cfg["unlock"]
    if cfg.get("policy") == "none":
        return False
    if u == "R2":
        return phase in ("R3", "finale")
    return phase == "finale"  # R3 unlock

def walk_R3(s, pr, grind_mode, cfg, rng):
    rnd = 2
    district = "touge"
    cap_L = CAP_L[2]
    enter_L = s.L
    unl = unlocked_at(cfg, "R3")
    mixed_wall_done = False
    for j, (name, T, kind) in enumerate(LADDER_RUNGS):
        B = opponent_budget(rnd, j, district, VARIANT)
        if name == "boss" and grind_mode in ("mixed", "hard") and s.L < cap_L:
            guard = 0
            while s.L < cap_L and guard < 80:
                Bw = opponent_budget(rnd, 0, district, VARIANT)
                rr, _ = arrival(s, Bw, C_ROUND[2])
                p = wr_for(pr, rr, 10, district, False)
                try_win(rng, s, p, pay_grind(rnd), cfg, True, grind_xp(s.L, cap_L, XP), cap_L, unl)
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
                    try_win(rng, s, p, pay_grind(rnd), cfg, True, grind_xp(s.L, cap_L, XP), cap_L, unl)
                    guard += 1
        rr, cbt = arrival(s, B, C_ROUND[2])
        p = wr_for(pr, rr, T, district, T >= 20 or name == "boss")
        won = try_win(rng, s, p, pay_story(kind, rnd), cfg, False,
                      story_xp_for_rung(rnd, j, enter_L, cap_L, XP), cap_L, unl)[1]
        if not won:
            break
    # end of R3: wholesale ends, T4 becomes legal (Mentor Confrontation)
    s.wholesale = False
    s.post_R3 = True
    shop(s)
    return s

def walk_finale(s, pr, cfg, rng):
    unl = unlocked_at(cfg, "finale")
    logs = []
    gw0 = s.grind_wins
    for i, (Bfin, dist, rstar, Cfin, Lf) in enumerate(
        zip(FINALE_B, FINALE_DIST, FINALE_R_C, FINALE_C, FINALE_L)
    ):
        gw_step0 = s.grind_wins
        guard = 0
        while s.L < Lf and guard < 200:
            Bw = Cfin / 1.18
            rr, _ = arrival(s, Bw, Cfin)
            p = wr_for(pr, rr, 10, dist, False)
            won_g = try_win(rng, s, p, FINALE_GRIND_PAY, cfg, True,
                            grind_xp(s.L, Lf, XP), Lf, unl)[1]
            if not won_g:
                break
            guard += 1
        rr, cbt = arrival(s, Bfin, Cfin)
        p = wr_for(pr, rr, 30, dist, True)
        tries, won = try_win(rng, s, p, FINALE_PURSE, cfg, False, 0.0, Lf, unl)
        logs.append(dict(
            step=i + 1, dist=dist, L=s.L, money=round(s.money, 1),
            arrive_r=round(rr, 4), wr=round(p * 100, 1), combat=round(cbt, 2),
            cap=round(Cfin, 2), fill=round(cbt / Cfin, 4), tries=tries, won=won,
            t4=int(s.t4_done), t4_reg=s.n_t4_reg, aero4=s.n_aero4,
            grind_wins_step=s.grind_wins - gw_step0,
            bet_profit=round(s.bet_profit, 1), bets=s.bets,
        ))
        if not won:
            break
    return logs

def snapshot_entry(s):
    return dict(L=s.L, money=round(s.money, 1), debt=round(s.debt, 1),
                t1=s.n_t1, t2=s.n_t2, t3=s.n_t3_reg, aero3=s.n_aero3,
                t4=s.n_t4_reg, aero4=s.n_aero4)

def stats(xs, nd=1):
    xs = [v for v in xs if v is not None and v == v]
    if not xs:
        return None
    xs = sorted(xs)
    def q(p):
        i = min(len(xs) - 1, max(0, int(round(p * (len(xs) - 1)))))
        return xs[i]
    return dict(mean=round(sum(xs) / len(xs), nd),
                p10=round(q(0.10), nd), p50=round(q(0.50), nd),
                p90=round(q(0.90), nd), min=round(xs[0], nd), max=round(xs[-1], nd))

def pct(xs):
    return round(100.0 * sum(1 for v in xs if v) / len(xs), 2) if xs else None

def run_one(pr, entry, cfg, t4_price, rng, do_mc):
    s = clone(entry)
    s.t4_price = t4_price
    s.min_money = s.money
    s.zeroed = False
    walk_R3(s, pr, MODE[pr], cfg, rng)
    end_R3_money = s.money
    end_R3_t3 = s.t3_done
    flog = walk_finale(s, pr, cfg, rng)
    return dict(
        money_end=s.money, min_money=s.min_money, zeroed=s.zeroed,
        bet_profit=s.bet_profit, bets=s.bets, L=s.L, stuck=s.stuck,
        end_R3_money=end_R3_money, end_R3_t3=end_R3_t3,
        t4_done=s.t4_done, t4_L=s.t4_done_L,
        steps_won=sum(1 for x in flog if x["won"]),
        flog=flog,
    )

def summarize(rows):
    out = dict(
        n=len(rows),
        zeroed_pct=pct([r["zeroed"] for r in rows]),
        t4_done_pct=pct([r["t4_done"] for r in rows]),
        clear4_pct=pct([r["steps_won"] >= 4 for r in rows]),
        money_end=stats([r["money_end"] for r in rows]),
        money_R3=stats([r["end_R3_money"] for r in rows]),
        bet_profit=stats([r["bet_profit"] for r in rows]),
        bets=stats([r["bets"] for r in rows], 2),
        steps_won=stats([r["steps_won"] for r in rows], 2),
        t4_L=stats([r["t4_L"] for r in rows if r["t4_L"] is not None], 1),
        min_money=stats([r["min_money"] for r in rows]),
    )
    for i in range(4):
        xs = [r["flog"][i] for r in rows if len(r["flog"]) > i]
        if not xs:
            out[f"F{i+1}"] = None
            continue
        out[f"F{i+1}"] = dict(
            reached_pct=pct([len(r["flog"]) > i for r in rows]),
            won_pct=pct([len(r["flog"]) > i and r["flog"][i]["won"] for r in rows]),
            wr=stats([x["wr"] for x in xs]),
            r=stats([x["arrive_r"] for x in xs], 4),
            fill=stats([x["fill"] for x in xs], 4),
            money=stats([x["money"] for x in xs]),
            t4_pct=pct([x["t4"] for x in xs]),
            grind_wins=stats([x["grind_wins_step"] for x in xs], 1),
            tries=stats([x["tries"] for x in xs], 2),
        )
    return out

def cfg_key(cfg):
    cap = "none" if cfg.get("cap") is None else str(cfg["cap"])
    return f"{cfg['unlock']}|{cfg['elig']}|cap={cap}|{cfg.get('odds','even')}"

def main():
    t0 = time.time()
    print("T4 slot", round(SLOT_T4, 3), "P114", round(power_at_level(114), 2), flush=True)
    # entries depend on wholesale, not on T4 price (T4 illegal pre-R3)
    print("pre-R3 with wholesale after R1...", flush=True)
    entries = {}
    for pr in PROFILES:
        entries[pr] = walk_pre_R3(pr, MODE[pr], T4_REG_PRICES[1])
        e = entries[pr]
        print(f"  {pr} {MODE[pr]} L={e.L} ${e.money:.0f} debt={e.debt:.0f} "
              f"T1={e.n_t1} T2={e.n_t2} T3={e.n_t3_reg}+a{e.n_aero3} wholesale={e.wholesale}",
              flush=True)

    results = dict(
        design=dict(
            SLOT_T4=SLOT_T4, FLOOR_T4=FLOOR_T4,
            P114=power_at_level(FINALE_L[-1]),
            T4_fills="0.27*P(114) across 6 slots; 1.07 cap clips earlier finale steps",
            aero_mult=AERO_MULT,
            wholesale="0.20 off list from end R1 through end R3; T4 is always full price",
            finale_purse=FINALE_PURSE, finale_grind=FINALE_GRIND_PAY,
            grind_wins_from_L46={"F1": 31, "F2": 25, "F3": 34, "F4": 34, "total": 106},
            grind_wins_80_80_from_L43={"to_L46": 9, "F1": 35, "then_same": "25/34/34"},
            T4_reg_prices=list(T4_REG_PRICES),
            T4_packages=[round(6.75 * p, 1) for p in T4_REG_PRICES],
            likely_threshold=LIKELY,
            n_mc=N_MC,
        ),
        entry={pr: snapshot_entry(entries[pr]) for pr in PROFILES},
        no_bet={},
        combos=[],
    )

    none_cfg = dict(unlock="R2", elig="any", cap=None, odds="even", policy="none")

    # no-bet per T4 price (deterministic official wins)
    for p4 in T4_REG_PRICES:
        pkg = 6.75 * p4
        results["no_bet"][str(int(p4))] = {}
        for pr in PROFILES:
            row = run_one(pr, entries[pr], none_cfg, p4, None, False)
            sm = summarize([row])
            results["no_bet"][str(int(p4))][pr] = sm
            fnotes = []
            for i in range(1, 5):
                f = sm.get(f"F{i}")
                if f:
                    fnotes.append(f"F{i} mon=${f['money']['mean']:.0f} t4={f['t4_pct']}% wr={f['wr']['mean']} won={f['won_pct']}")
            print(f"no-bet T4={int(p4)} pkg=${pkg:.0f} {pr}: endR3=${sm['money_R3']['mean']:.0f} "
                  f"end=${sm['money_end']['mean']:.0f} t4={sm['t4_done_pct']}% clear4={sm['clear4_pct']}% "
                  + " | ".join(fnotes), flush=True)

    # factorial: even money, all unlock/elig/cap/T4; then fair odds for cap=none (all T4, all unlock/elig)
    even_cfgs = [dict(unlock=u, elig=e, cap=c, odds="even", policy="likely")
                 for u, e, c in itertools.product(UNLOCKS, ELIGS, CAPS)]
    fair_cfgs = [dict(unlock=u, elig=e, cap=None, odds="fair", policy="likely")
                 for u, e in itertools.product(UNLOCKS, ELIGS)]
    all_cfgs = even_cfgs + fair_cfgs
    print(f"MC {len(all_cfgs)} betting cfgs x {len(T4_REG_PRICES)} T4 x {len(PROFILES)} profiles x {N_MC}...",
          flush=True)

    for ci, cfg in enumerate(all_cfgs):
        for p4 in T4_REG_PRICES:
            cell = dict(unlock=cfg["unlock"], elig=cfg["elig"], cap=cfg["cap"],
                        odds=cfg["odds"], t4_reg=p4, t4_pkg=round(6.75 * p4, 1),
                        profiles={})
            for pr in PROFILES:
                rows = []
                for i in range(N_MC):
                    rng = random.Random(SEED + i * 19 + (hash(cfg_key(cfg) + pr + str(p4)) % 99991))
                    rows.append(run_one(pr, entries[pr], cfg, p4, rng, True))
                sm = summarize(rows)
                nb = results["no_bet"][str(int(p4))][pr]
                # profit vs no-bet at end and at each finale step (mean money difference)
                sm["d_money_end"] = round(sm["money_end"]["mean"] - nb["money_end"]["mean"], 1)
                sm["d_profit"] = round(sm["bet_profit"]["mean"], 1)
                sm["d_money_R3"] = round(sm["money_R3"]["mean"] - nb["money_R3"]["mean"], 1)
                for i in range(1, 5):
                    f, nbf = sm.get(f"F{i}"), nb.get(f"F{i}")
                    if f and nbf:
                        f["d_money"] = round(f["money"]["mean"] - nbf["money"]["mean"], 1)
                        f["d_wr"] = round(f["wr"]["mean"] - nbf["wr"]["mean"], 1)
                        f["d_t4_pp"] = round(f["t4_pct"] - nbf["t4_pct"], 1)
                cell["profiles"][pr] = sm
            results["combos"].append(cell)
        print(f"  done {cfg_key(cfg)}  elapsed {time.time()-t0:.1f}s  wr={len(_WR)}", flush=True)

    fn = os.path.join(HERE, "betting_levers.json")
    json.dump(results, open(fn, "w"), indent=1)
    print("wrote", fn, "in", round(time.time() - t0, 1), "s", flush=True)

if __name__ == "__main__":
    main()
