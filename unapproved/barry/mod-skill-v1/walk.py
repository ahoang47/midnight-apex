"""mod_skill campaign walk R1-R3 (story / mixed / hard), B3 setup base, own-stat share X, pattern kits.

Per race: shop (buy / upgrade kit mods to the round's tier when cash allows, kit order), race, purse (DEBT_SHARE to the
debt while open), then the race's XP goes to ONE owned kit mod: the one that leaves the build closest to the district
tune, ties -> furthest below its ceiling (overflow past the ceiling is lost). Grind = 10-turn wild at kid1 budget,
pays GRIND_PAYOUT_FRACTION x wild purse and a flat GRIND_XP[round] points.
Policies as live progression._walk_round: story never grinds; mixed grinds at the first rung where 60/80 or 80/60 is
< 50 % until both clear, then to "cap" (every kit mod at the round ceiling) before the boss; hard grinds wherever 60/60
< 50 %, then to cap before the boss.
"""
from mod_skill import *

STORY_SHAPE = tuple(tuple(E.STORY_W[j] * E.STORY_XP_MULT[n][j] for j in range(7)) for n in range(3))
PRICES = {"mk1_list": (150.0, 700.0, 1200.0), "mk3_list": (1000.0, 5000.0, 8000.0),
          # spend-matched: today's live mixed walk spends $6,100 / $20,640 / $35,440 on mods per round (live
          # run_with_garage buys); / 4 kit purchases, R2-R3 grossed up for the 20 % wholesale -> list per tier upgrade
          "spend_matched": (1525.0, 6450.0, 11075.0)}


class Car:
    KITS = dict(E.MOD_SLOT_PATTERN)

    def __init__(self, X, spill=False, kits=None):
        self.X = X; self.spill = spill; self.kits = dict(E.MOD_SLOT_PATTERN, **(kits or {})); self.mods = {}            # key (stat letter, k) -> [tier bought 1-3, earned points]
        self.spent = 0.0; self.buys = []

    def kit(self, d):
        seen = {}; out = []
        for c in self.kits[d]:
            seen[c] = seen.get(c, 0) + 1; out.append((c, seen[c]))
        return out

    def equipped(self, d):
        return [(SI[c], self.mods[(c, k)][1] if (c, k) in self.mods else 0.0) for c, k in self.kit(d)]

    def points(self, d):
        return STOCK + sum(p for _, p in self.equipped(d))

    def power(self, d, rnd):
        return min(CAP_POWER[rnd], self.points(d) / 10.0)

    def build(self, d):
        return alloc(BASES["B3_setup"], self.equipped(d), self.X, d)

    def pow_share(self, d):
        st = self.build(d)[0]; return st[0] / sum(st)

    def at_cap(self, d, rnd):
        return all((c, k) in self.mods and self.mods[(c, k)][0] == rnd + 1 and self.mods[(c, k)][1] >= CEIL[rnd] - 1e-9
                   for c, k in self.kit(d))

    def shop(self, wallet, d, rnd, price, wholesale, tag):
        for c, k in self.kit(d):
            m = self.mods.get((c, k))
            if m and m[0] >= rnd + 1:
                continue
            p = price[rnd] * (1 - E.WHOLESALE_DISCOUNT if wholesale else 1.0)
            if p <= wallet + 1e-9:
                wallet -= p; self.spent += p; self.buys.append((tag, f"{c}{k}", rnd + 1, p))
                if m: m[0] = rnd + 1
                else: self.mods[(c, k)] = [rnd + 1, 0.0]
        return wallet

    def assign(self, xp, d):
        """Greedy: owned kit mod with room; min tune distance after, ties -> most room. Returns points lost."""
        cand = []
        for c, k in self.kit(d):
            m = self.mods.get((c, k))
            if not m:
                continue
            room = CEIL[m[0] - 1] - m[1]
            if room <= 1e-9:
                continue
            m[1] += min(room, xp); dist = self.build(d)[1]; m[1] -= min(room, xp)
            cand.append((round(dist, 6), -room, (c, k)))
        if not cand:
            return xp
        _, negroom, key = min(cand); room = -negroom
        self.mods[key][1] += min(room, xp); left = max(0.0, xp - room)
        return self.assign(left, d) if (self.spill and left > 1e-9) else left


def walk(mode, X=0.60, f=(0.5, 0.5, 0.5), grind_xp=(40.0, 60.0, 80.0), price="mk1_list", log=True, story_table=None, upto=None, spill=False, kits=None):
    pr_t = PRICES[price] if isinstance(price, str) else price
    car = Car(X, spill, kits); money, debt = 0.0, E.DEBT_AMOUNT; out = []
    for rnd in range(3):
        d = DIST[rnd]; wholesale = E.wholesale_active(rnd)
        gap = E.MOD_SLOTS * (CEIL[rnd] - (CEIL[rnd - 1] if rnd else 0))
        # catch-up (live xp-carry-v1 fix C, ported): a player entering below the previous round's cap points gets
        # CATCHUP_XP_FRAC x CATCHUP_XP_SHARE[rung] of the shortfall on top of the nominal story XP
        short = max(0.0, 10 * CAP_POWER[rnd - 1] - car.points(d)) if rnd else 0.0
        if story_table is None:
            sxp = [f[rnd] * w / sum(STORY_SHAPE[rnd]) * gap + E.CATCHUP_XP_FRAC * E.CATCHUP_XP_SHARE[j] * short
                   for j, w in enumerate(STORY_SHAPE[rnd])]
        else:
            sxp = [story_table[rnd][j] + E.CATCHUP_XP_FRAC * E.CATCHUP_XP_SHARE[j] * short for j in range(7)]
        rows = []; total = 0; wall_done = False; lost = 0.0; maxdist = 0.0

        def credit(kind, grind):
            nonlocal money, debt
            pay = E.purse(rnd, kind, grind)
            if debt > 0:
                take = min(debt, E.DEBT_SHARE * pay); debt -= take; money += pay - take
            else:
                money += pay

        def shop(tag):
            nonlocal money
            money = car.shop(money, d, rnd, pr_t, wholesale, tag)

        def grind1(tag):
            nonlocal total, lost
            credit("kid", True); shop(tag); lost += car.assign(grind_xp[rnd], d); total += 1; shop(tag)

        def ok(profiles, B, T):
            r = car.power(d, rnd) / B
            for p in profiles:
                pk = P.win_pack(p, r, T, d, car.pow_share(d))
                if pk["district"] < E.CLEAR_THRESHOLD or (T >= 20 and P.hard_win(pk) < E.CLEAR_THRESHOLD):
                    return False
            return True

        def grind_until(profiles, B, T, tag):
            n = 0
            while n < 200 and not car.at_cap(d, rnd) and not ok(profiles, B, T):
                grind1(tag); n += 1
            return n

        for j, name in enumerate(E.LADDER_RUNGS):
            B = E.opponent_budget(rnd, j); T = E.LADDER_TURNS[j]; tag = f"R{rnd + 1} {name}"; here = 0
            shop(tag)
            if name == "boss" and mode in ("mixed", "hard"):
                while not car.at_cap(d, rnd) and here < 400:
                    grind1(tag); here += 1
            elif name != "boss":
                if mode == "mixed" and not wall_done and not ok(("c6080", "c8060"), B, T):
                    here = grind_until(("c6080", "c8060"), B, T, tag); wall_done = True
                elif mode == "hard" and not ok(("c6060",), B, T):
                    here = grind_until(("c6060",), B, T, tag)
            pw = car.power(d, rnd); r = pw / B; ps = car.pow_share(d); maxdist = max(maxdist, car.build(d)[1])
            packs = {p: P.win_pack(p, r, T, d, ps) for p in P.PROFILES}
            rows.append(dict(rung=name, turns=T, grind=here, points=round(car.points(d)), power=round(pw, 2), B=round(B, 2),
                             r=round(r, 4), target_r=E.LADDER_TARGET_R[d][j], pow_share=round(100 * ps, 1),
                             wr={p: P.hard_win(v) for p, v in packs.items()}, wr_district={p: v["district"] for p, v in packs.items()},
                             cash_before=round(money), debt_before=round(debt),
                             tiers="".join(f"{c}{car.mods[(c, k)][0] if (c, k) in car.mods else 0}" for c, k in car.kit(d))))
            credit(E.LADDER_RUNG_KIND[j], False); shop(tag + " won")
            if upto == (rnd, j):
                return out, rows, car
            lost += car.assign(sxp[j], d)
        shop(f"R{rnd + 1} end")
        out.append(dict(rnd=rnd + 1, district=d, rows=rows, total_grind=total, end_points=round(car.points(d)),
                        money=round(money), debt=round(debt), spent=round(car.spent), xp_lost=round(lost, 1),
                        max_tune_dist=round(maxdist, 2), story_xp=[round(x, 1) for x in sxp], at_cap_end=car.at_cap(d, rnd)))
    return out
