"""True fair-odds betting re-run. Draft only, no live sim/ edits.

Austin pick 2026-11-13: BET_ODDS = fair, net payout (1-p)/p, NO 0.95 clamp.
Grid: unlock R2 or R3 (R3 = promoter beat, wholesale already ended) x
      any race, no bet-count cap x
      likely-win (WR >= 65%) and always-max x
      fair (edge 0) and house5 (payout 0.95*(1-p)/p).
T4 regular = $8,000 (representative; package $54,000). 4000 MC trials.
Ruin = a lost bet left cash at $0. Post-shop leftover of $0 is not ruin.
"""
from __future__ import annotations
import json, math, os, sys, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_betting_levers as L
from evaluate import PROFILES

N_MC = 4000
SEED = 20261113
T4 = 8000.0
UNLOCKS = ("R2",)  # Austin locked end_R2; R3-unlock dropped
POLICIES = ("likely", "always")
ODDS = ("fair", "house5")


def odds_net(cfg, p_win):
    p = float(p_win)
    # Numerical endpoints only. This is not a 0.95 clamp.
    if p <= 0.0 or p >= 1.0:
        return 0.0
    net = (1.0 - p) / p
    if cfg.get("odds") == "house5":
        net *= 0.95
    return net


def want_bet(cfg, s, p_win, is_grind, unlocked):
    if not unlocked or cfg.get("policy") == "none":
        return False
    # p=0 has undefined fair odds; p=1 pays net 0. Refuse both.
    if p_win <= 0.0 or p_win >= 1.0:
        return False
    policy = cfg.get("policy")
    if policy == "likely" and p_win < L.LIKELY:
        return False
    cap = cfg.get("cap")
    if cap is not None and s.bets >= cap:
        return False
    elig = cfg.get("elig", "any")
    if elig == "story" and is_grind:
        return False
    if elig == "wild" and not is_grind:
        return False
    return True


def credit(s, amount):
    if s.debt > 0:
        take = min(s.debt, L.DEBT_SHARE * amount)
        s.debt -= take
        s.money += amount - take
    else:
        s.money += amount
    L.shop(s)
    if s.money < s.min_money:
        s.min_money = s.money
    if s.money <= 1e-9:
        s.shop_zeroed = True


def mark_min(s):
    if s.money < s.min_money:
        s.min_money = s.money


def resolve(rng, s, p_win, purse, cfg, is_grind, xp_amt, cap_L, unlocked):
    stake = L.stake_for(cfg, s, p_win, is_grind, unlocked)
    if stake > 0:
        s.bets += 1
        s.money -= stake
    s.races += 1
    if is_grind:
        s.grind_races += 1
    if rng is None:
        win = True
    else:
        win = rng.random() < p_win
    if win:
        if is_grind:
            s.grind_wins += 1
        if stake > 0:
            net = stake * odds_net(cfg, p_win)
            s.money += stake + net
            s.bet_profit += net
        credit(s, purse)
        if xp_amt and s.L < cap_L:
            s.L, s.bag = L.apply_xp(s.L, xp_amt, s.bag, L.XP, cap_L)
            L.shop(s)
            mark_min(s)
        return True
    else:
        if stake > 0:
            s.bet_profit -= stake
            if s.money <= 1e-9:
                s.bet_ruin = True
        mark_min(s)
        return False


L.odds_net = odds_net
L.want_bet = want_bet
L.credit = credit
L.mark_min = mark_min
L.resolve = resolve


def run_one(pr, entry, cfg, rng):
    s = L.clone(entry)
    s.t4_price = T4
    s.min_money = s.money
    s.zeroed = False
    s.shop_zeroed = False
    s.bet_ruin = False
    L.walk_R3(s, pr, L.MODE[pr], cfg, rng)
    end_R3_money = s.money
    flog = L.walk_finale(s, pr, cfg, rng)
    return dict(
        money_end=s.money,
        min_money=s.min_money,
        shop_zeroed=bool(getattr(s, "shop_zeroed", False)),
        bet_ruin=bool(getattr(s, "bet_ruin", False)),
        bet_profit=s.bet_profit,
        bets=s.bets,
        L=s.L,
        stuck=s.stuck,
        end_R3_money=end_R3_money,
        t4_done=s.t4_done,
        steps_won=sum(1 for x in flog if x["won"]),
        F_wr=[x["wr"] for x in flog],
        F_money=[x["money"] for x in flog],
    )


def main():
    t0 = time.time()
    print("pre-R3 entries...", flush=True)
    entries = {}
    for pr in PROFILES:
        entries[pr] = L.walk_pre_R3(pr, L.MODE[pr], T4)
        e = entries[pr]
        print(f"  {pr} L={e.L} ${e.money:.0f} T2={e.n_t2} T3={e.n_t3_reg}+a{e.n_aero3}",
              flush=True)

    none_cfg = dict(unlock="R2", elig="any", cap=None, odds="fair", policy="none")
    no_bet = {}
    for pr, entry in entries.items():
        no_bet[pr] = run_one(pr, entry, none_cfg, None)
        print(f"  no-bet {pr} end ${no_bet[pr]['money_end']:.0f} "
              f"R3 ${no_bet[pr]['end_R3_money']:.0f} t4={no_bet[pr]['t4_done']} "
              f"steps={no_bet[pr]['steps_won']}", flush=True)

    cells = []
    for unlock in UNLOCKS:
        for policy in POLICIES:
            for odds in ODDS:
                cfg = dict(unlock=unlock, elig="any", cap=None, odds=odds, policy=policy)
                print(f"MC {unlock} {policy} {odds}...", flush=True)
                per = {}
                for pr, entry in entries.items():
                    key = f"{pr}|{unlock}|{policy}|{odds}"
                    rng = random.Random(SEED + int.from_bytes(key.encode(), "little") % 1_000_000_007)
                    rows = [run_one(pr, entry, cfg, rng) for _ in range(N_MC)]
                    per[pr] = dict(
                        n=N_MC,
                        profit=L.stats([r["bet_profit"] for r in rows]),
                        money_end=L.stats([r["money_end"] for r in rows]),
                        money_R3=L.stats([r["end_R3_money"] for r in rows]),
                        min_money=L.stats([r["min_money"] for r in rows]),
                        bets=L.stats([r["bets"] for r in rows], 2),
                        ruin_pct=L.pct([r["bet_ruin"] for r in rows]),
                        shop_zeroed_pct=L.pct([r["shop_zeroed"] for r in rows]),
                        stuck_pct=L.pct([r["stuck"] for r in rows]),
                        clear4_pct=L.pct([r["steps_won"] >= 4 for r in rows]),
                        t4_done_pct=L.pct([r["t4_done"] for r in rows]),
                        wr=dict(
                            (f"F{i+1}", L.stats([r["F_wr"][i] for r in rows if len(r["F_wr"]) > i]))
                            for i in range(4)
                        ),
                    )
                    p = per[pr]
                    print(
                        f"    {pr} profit mean={p['profit']['mean']} p50={p['profit']['p50']} "
                        f"p10={p['profit']['p10']} cash p50={p['money_end']['p50']} "
                        f"p10={p['money_end']['p10']} ruin={p['ruin_pct']}% "
                        f"bets={p['bets']['mean']}",
                        flush=True,
                    )
                max_mean = max(per[pr]["profit"]["mean"] for pr in PROFILES)
                wr_jump = False
                # compare mean F-step WR vs no-bet official WR when present
                cells.append(dict(
                    unlock=unlock, policy=policy, odds=odds, elig="any", cap=None,
                    t4_reg=T4, profiles=per, max_mean_profit=max_mean,
                ))

    # C6: printer test on mean profit; WR jump vs no-bet
    for cell in cells:
        jumps = []
        for pr in PROFILES:
            for i in range(4):
                key = f"F{i+1}"
                bet_wr = cell["profiles"][pr]["wr"].get(key)
                nb_wr = no_bet[pr]["F_wr"][i] if len(no_bet[pr]["F_wr"]) > i else None
                if bet_wr and nb_wr is not None:
                    d = bet_wr["mean"] - nb_wr
                    jumps.append(d)
        max_jump = max(jumps) if jumps else 0.0
        mp = cell["max_mean_profit"]
        if mp >= 40000 or max_jump >= 8.0:
            c6 = "FAIL"
        elif mp >= 16000:
            c6 = "LEAK"
        else:
            c6 = "PASS"
        cell["c6"] = c6
        cell["max_wr_jump_pp"] = round(max_jump, 2)
        print(f"C6 {cell['unlock']} {cell['policy']} {cell['odds']}: {c6} "
              f"max_mean=${mp:.0f} max_wr_jump={max_jump:.2f}pp", flush=True)

    out = dict(
        n_mc=N_MC, seed=SEED, t4_reg=T4, t4_pkg=6.75 * T4,
        fair="net (1-p)/p, no 0.95 clamp; refuse bets at p<=0 or p>=1",
        house5="net 0.95*(1-p)/p",
        ruin="lost bet left cash at $0; shop leftover of $0 is not ruin",
        entries={pr: L.snapshot_entry(entries[pr]) for pr in PROFILES},
        no_bet={pr: dict(money_end=round(no_bet[pr]["money_end"], 1),
                         money_R3=round(no_bet[pr]["end_R3_money"], 1),
                         t4_done=no_bet[pr]["t4_done"],
                         steps_won=no_bet[pr]["steps_won"],
                         wr=no_bet[pr]["F_wr"],
                         F_money=no_bet[pr]["F_money"])
                for pr in PROFILES},
        cells=cells,
        elapsed_s=round(time.time() - t0, 1),
    )
    path = os.path.join(HERE, "betting_fair.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {path} in {out['elapsed_s']}s", flush=True)


if __name__ == "__main__":
    main()
