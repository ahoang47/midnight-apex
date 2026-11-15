"""mods-v2-mk3-boss (draft, Barry 2026-11-14): make Mk3 required at the boss for story-only players who play N mandatory
grind races per round. In memory only: patches equations' mod catalog (MOD_SETS) and STORY_XP_MULT while a config runs,
and walks a copy of live progression._walk_round with a mandatory-grind gate. Live sim/ is not changed."""
import os, sys, json, copy, math, contextlib, io
HERE = os.path.dirname(os.path.abspath(__file__))
from velocity_shift import equations as E, progression as P

LIVE_SETS = E.MOD_SETS
LIVE_XP = E.STORY_XP_MULT

@contextlib.contextmanager
def patched(sets=None, xp_mult=None):
    saved = (E.MOD_SETS, E.MOD_CATALOG, E.MOD_UNLOCK, E.MOD_PRICE, E.STORY_XP_MULT)
    try:
        if sets is not None:
            E.MOD_SETS = tuple(sets)
            E.MOD_CATALOG = {f"MOD_{g}_{st}_{mk}": dict(group=g, mk=mk, stat=st, points=pts, price=price, unlock=u, fills_to=fl)
                             for g, mk, pts, price, u, fl in E.MOD_SETS for st in E.MOD_STATS}
            E.MOD_UNLOCK = {m: v["unlock"] for m, v in E.MOD_CATALOG.items()}
            E.MOD_PRICE = {m: v["price"] for m, v in E.MOD_CATALOG.items()}
        if xp_mult is not None:
            E.STORY_XP_MULT = xp_mult
        yield
    finally:
        E.MOD_SETS, E.MOD_CATALOG, E.MOD_UNLOCK, E.MOD_PRICE, E.STORY_XP_MULT = saved

def mk_points(fill_L, stage):
    return int(math.ceil(P.mod_gap(fill_L, stage) / E.MOD_SLOTS - 1e-9))

def make_sets(fills, prices):
    """fills / prices: {(group, mk): value}; ARC sets stay live. Points = ceil(gap(fill level) / slots)."""
    out = []
    for g, mk, pts, price, u, fl in LIVE_SETS:
        if g != "ARC":
            fl = fills.get((g, mk), fl); stage = int(g[1]) - 1; pts = mk_points(fl, stage); price = prices.get((g, mk), price)
        out.append((g, mk, pts, price, u, fl))
    return out

def walk_round(rnd, enter_level, enter_bag, money, debt, mode, build, G, done, forced=0, where="boss"):
    """Copy of live P._walk_round plus the mandatory-grind gate: before rung `where`, a player with fewer than `forced`
    grind wins this round grinds the rest (story-only included). Rows add the no-Mk3 boss check."""
    d = E.ROUND_DISTRICTS[rnd].lower(); cap = E.CAP_LEVEL[rnd]; wholesale = E.wholesale_active(rnd)
    L, bag = enter_level, enter_bag; ps = build.pow_share; done.add(("open", rnd))
    rows = []; st = dict(total=0, wall=0, post=0, wall_name=None, wall_done=False, forced_here=0)
    S = dict(L=L, bag=bag, money=money, debt=debt)
    def credit(kind, grind):
        pay = E.purse(rnd, kind, grind)
        if S["debt"] > 0:
            take = min(S["debt"], E.DEBT_SHARE * pay); S["debt"] -= take; S["money"] += pay - take
        else:
            S["money"] += pay
    def shop(tag): S["money"] = G.shop(S["money"], S["L"], rnd, d, done, wholesale, tag)
    def grind1(tag):
        S["L"], S["bag"] = P.apply_xp(S["L"], E.grind_xp(S["L"], cap), S["bag"], cap); credit("kid", True); st["total"] += 1; shop(tag)
    def ok(profiles, B, T):
        r = G.power(S["L"], rnd, d) / B
        for pr in profiles:
            pk = P.win_pack(pr, r, T, d, ps(S["L"]))
            if pk["district"] < E.CLEAR_THRESHOLD or (T >= 20 and P.hard_win(pk) < E.CLEAR_THRESHOLD): return False
        return True
    def grind_until(profiles, B, T, tag):
        n = 0
        while n < 80 and S["L"] < cap and not ok(profiles, B, T):
            grind1(tag); n += 1
        return n
    g = E.ROUND_DISTRICTS[rnd][0]
    rid = ("R1", "R2", "R3")[rnd]
    mk2 = E.MOD_CATALOG[f"MOD_{rid}_POW_MK2"]["points"]
    for j, name in enumerate(E.LADDER_RUNGS):
        B = E.opponent_budget(rnd, j); T = E.LADDER_TURNS[j]; pre_boss = here = forced_n = 0; tag = f"R{rnd+1} {name}"
        cash_pre = S["money"]; shop(tag)
        if name == where and st["total"] < forced and S["L"] < cap:
            while st["total"] < forced and S["L"] < cap:
                grind1(tag); forced_n += 1
        if name == "boss" and mode in ("mixed", "hard") and S["L"] < cap:
            before = st["total"]
            while S["L"] < cap: grind1(tag)
            pre_boss = st["total"] - before
            if st["wall_done"] or mode == "hard": st["post"] += pre_boss
        if name != "boss" and S["L"] < cap:
            if mode == "mixed" and not st["wall_done"] and not ok(("c6080", "c8060"), B, T):
                here = grind_until(("c6080", "c8060"), B, T, tag); st["wall"] = here; st["wall_name"] = name; st["wall_done"] = True
            elif mode == "hard" and not ok(("c6060",), B, T):
                here = grind_until(("c6060",), B, T, tag)
                if st["wall_name"] is None: st["wall_name"] = name; st["wall"] += here
                else: st["post"] += here
        aL = S["L"]; pw = G.power(aL, rnd, d); r = pw / B
        packs = {pr: P.win_pack(pr, r, T, d, ps(aL)) for pr in P.PROFILES}
        row = dict(rnd=rnd + 1, rung=name, arrive_L=aL, r=round(r, 4), fill=round(100 * G.fill(aL, rnd, d), 1),
                   wr={pr: P.hard_win(packs[pr]) for pr in P.PROFILES},
                   grind10={pr: round(P.win_rate(pr, pw / E.opponent_budget(rnd, 0), E.GRIND_TURNS, d, pow_share=ps(aL)), 1) for pr in P.PROFILES},
                   equipped=[m.removeprefix("MOD_") if m else "stock" for m in G.equipped(d)], owned=len(G.owned),
                   cash_pre=round(cash_pre), money_before=round(S["money"]), grind_here=here, forced=forced_n, pre_boss=pre_boss)
        if True:   # Mk2-capped car: every slot at this round's Mk2 (best car without Mk3), every rung
            sp = E.skill_points(aL)
            pw2 = min(10 * P.stage_ceiling(rnd), 10 * E.MOD_CAP_FRACTION * E.stats_at_level(aL), sp + E.MOD_SLOTS * mk2) / 10
            row["no_mk3"] = {pr: P.hard_win(P.win_pack(pr, pw2 / B, T, d, ps(aL))) for pr in P.PROFILES}
            row["r_no_mk3"] = round(pw2 / B, 4)
            row["mk3_owned"] = sum(1 for m in G.owned if m.startswith(f"MOD_{rid}_") and m.endswith("_MK3"))
        credit(E.LADDER_RUNG_KIND[j], False); done.add((rnd, name))
        S["L"], S["bag"] = P.apply_xp(S["L"], E.story_xp(rnd, j, enter_level, cap), S["bag"], cap)
        row.update(money_after=round(S["money"]), debt=round(max(S["debt"], 0)))
        rows.append(row)
    shop(f"R{rnd+1} end")
    return dict(rows=rows, L=S["L"], bag=S["bag"], money=S["money"], debt=max(S["debt"], 0.0), total_grind=st["total"],
                wall_grind=st["wall"], post=st["post"], build=build.at(S["L"]), spent=G.spent)

def run(mode, forced=0, where="boss"):
    L, bag, money, debt = 0, 0.0, 0.0, E.DEBT_AMOUNT; out = []; alloc = P.start_build(); G = P.Garage(); done = set()
    for rnd in range(3):
        d = E.ROUND_DISTRICTS[rnd].lower()
        if rnd > 0:
            alloc = P.retune(alloc, d); end_L, L, bag = L, E.CAP_LEVEL[rnd - 1], 0.0
            alloc = P.add_points(alloc, E.skill_points(L) - E.skill_points(end_L), d)
        w = walk_round(rnd, L, bag, money, debt, mode, P.Build(d, alloc, L), G, done, forced, where); out.append(w)
        L, bag, money, debt = w["L"], w["bag"], w["money"], w["debt"]; alloc = w["build"]
    return out, G, done

def summary(forced=0, where="boss"):
    res = {m: run(m, forced, where) for m in ("story", "mixed", "hard")}
    o = {}
    for m, (out, G, _) in res.items():
        o[m] = dict(grinds=[w["total_grind"] for w in out], split=[(w["wall_grind"], w["post"]) for w in out],
                    boss=[(b["arrive_L"], b["wr"]["c8080"] if m != "hard" else b["wr"]["c6060"], b["no_mk3"]["c8080"] if m != "hard" else b["no_mk3"]["c6060"], b["mk3_owned"], b["fill"])
                          for b in (w["rows"][-1] for w in out)],
                    boss_all=[(w["rows"][-1]["wr"], w["rows"][-1]["no_mk3"]) for w in out],
                    min80=[min(r["wr"]["c8080"] for r in w["rows"]) for w in out],
                    min_fill=[min(r["fill"] for r in w["rows"][2:]) for w in out],
                    grind10_min=min(r["grind10"]["c6060" if m == "hard" else "c8080"] for w in out for r in w["rows"]),
                    cash=[round(w["money"]) for w in out], spent=round(G.spent), endL=[w["L"] for w in out])
    return res, o
