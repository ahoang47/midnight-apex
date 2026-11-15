"""Pokémon-style grind study (draft, Barry 2026-11-14). Base: live mods-v1 + xp-carry fix C + kid 20/20 + fix K.
Finite grind pool per round: POOL[j] one-time grind races open before rung j (j=0 at round open; j>0 after the rung j-1
win), all closed after the boss. Each pays the live grind XP (falloff toward the cap) and the live grind purse.
Fallback: a repeatable low-XP race (FB_XP x the grind XP, FB_PAY x the grind purse), unlimited.
Policies ("natural"): story = no grinds. mixed (c6080 / c8060 each walked alone, plus the live joint 6080+8060 check):
clears every open pool race before each rung, then uses fallback only if its own win on the next race < 50 %
(hard cell at 20/30 turns, same test as the live walk). hard (c6060): pool, then fallback until >= 50 % on non-boss
rungs and to the cap before the boss (the 60/60 boss floor is defined at the cap). In memory only."""
import json, itertools, sys
import carry as C, kidlen as KL, final as F
from velocity_shift import equations as E, progression as P
BASE = dict(KL.FIXC, LADDER_TURNS=KL.turns(20, 20), LADDER_TARGET_R=KL.tr(**F.FIXK))

PAYX = [1.0]   # pool-race purse multiplier
PX = [1.0]   # pool-race XP multiplier on grind_xp
MODE = ['clear']   # 'clear' = clear the open pool before each rung; 'need' = pool/fallback only while < 50 %
def walk_round(rnd, L, bag, money, debt, profiles, to_cap, build, G, done, pool, fb_xp, fb_pay):
    d = E.ROUND_DISTRICTS[rnd].lower(); cap = E.CAP_LEVEL[rnd]; enter = L
    wholesale = E.wholesale_active(rnd); ps = build.pow_share; done.add(("open", rnd))
    n_pool = n_fb = 0; avail = 0; lost = 0.0; rows = []
    def credit(pay):
        nonlocal money, debt
        if debt > 0:
            t = min(debt, E.DEBT_SHARE * pay); debt -= t; money += pay - t
        else: money += pay
    def shop(tag):
        nonlocal money; money = G.shop(money, L, rnd, d, done, wholesale, tag)
    def g(kind):
        nonlocal L, bag, n_pool, n_fb, lost
        xp = E.grind_xp(L, cap) * (PX[0] if kind == "pool" else fb_xp)
        L0 = L; L, bag = P.apply_xp(L, xp, bag, cap)
        credit(E.purse(rnd, "kid", True) * (PAYX[0] if kind == "pool" else fb_pay))
        if kind == "pool": n_pool += 1
        else: n_fb += 1
        shop("g")
    def ok(B, T):
        r = G.power(L, rnd, d) / B
        for pr in profiles:
            pk = P.win_pack(pr, r, T, d, ps(L))
            if pk["district"] < E.CLEAR_THRESHOLD or (T >= 20 and P.hard_win(pk) < E.CLEAR_THRESHOLD): return False
        return True
    for j, name in enumerate(E.LADDER_RUNGS):
        B = E.opponent_budget(rnd, j); T = E.LADDER_TURNS[j]; shop(name)
        avail += pool[j]
        if profiles:
            if MODE[0] == 'clear':
                while avail > 0:            # natural: clear the open one-time races (XP past the cap is lost; purse still pays)
                    avail -= 1; g("pool")
            k = 0
            while MODE[0] == 'need' and avail > 0 and L < cap and not ok(B, T): avail -= 1; g("pool")
            if name == "boss" and to_cap:
                while L < cap and k < 400: g("fb"); k += 1
            while not ok(B, T) and L < cap and k < 400: g("fb"); k += 1
        pw = G.power(L, rnd, d); r = pw / B
        rows.append(dict(rung=name, L=L, wr={pr: min(P.win_pack(pr, r, T, d, ps(L))["district"], P.hard_win(P.win_pack(pr, r, T, d, ps(L)))) for pr in P.PROFILES}))
        credit(E.purse(rnd, E.LADDER_RUNG_KIND[j], False)); done.add((rnd, name))
        L, bag = P.apply_xp(L, E.story_xp(rnd, j, enter, cap), bag, cap)
    shop("end")
    return dict(rows=rows, L=L, bag=bag, money=money, debt=debt, pool=n_pool, fb=n_fb, unused=avail, build=build.at(L))

def campaign(profiles, to_cap, pool, fb_xp, fb_pay):
    L, bag, money, debt = 0, 0.0, 0.0, E.DEBT_AMOUNT; alloc = P.start_build(); G = P.Garage(); done = set(); out = []
    for rnd in range(3):
        d = E.ROUND_DISTRICTS[rnd].lower()
        if rnd > 0: alloc = P.retune(alloc, d)
        w = walk_round(rnd, L, bag, money, debt, profiles, to_cap, P.Build(d, alloc, L), G, done, pool, fb_xp, fb_pay); out.append(w)
        L, bag, money, debt, alloc = w["L"], w["bag"], w["money"], w["debt"], w["build"]
    return out

WALKERS = {"c6080": (("c6080",), False), "c8060": (("c8060",), False), "mixed": (("c6080", "c8060"), False), "c6060": (("c6060",), True)}
def evaluate(pool, fb_xp=0.25, fb_pay=0.25, floor=None, patch=None):
    p = dict(BASE, **(patch or {}))
    if floor is not None: p["GRIND_TAPER_FLOOR"] = floor
    res = {}
    with C.patched(**p):
        for k, (prof, tc) in WALKERS.items():
            o = campaign(prof, tc, pool, fb_xp, fb_pay); own = prof[0] if k != "mixed" else None
            res[k] = dict(pool=[w["pool"] for w in o], fb=[w["fb"] for w in o], total=[w["pool"] + w["fb"] for w in o],
                          boss_L=[w["rows"][-1]["L"] for w in o], cap_reached=[w["rows"][-1]["L"] >= E.CAP_LEVEL[i] for i, w in enumerate(o)],
                          boss_own=[w["rows"][-1]["wr"][own] if own else min(w["rows"][-1]["wr"]["c6080"], w["rows"][-1]["wr"]["c8060"]) for w in o],
                          min_own=[min(r["wr"][own] if own else min(r["wr"]["c6080"], r["wr"]["c8060"]) for r in w["rows"]) for w in o],
                          enter=[w["rows"][0]["L"] for w in o], cash=[round(w["money"]) for w in o])
        s = campaign((), False, pool, fb_xp, fb_pay)
        res["story8080"] = dict(min=[min(r["wr"]["c8080"] for r in w["rows"]) for w in s])
    return res

if __name__ == "__main__":
    out = []
    pools = {}
    for n0, nr in itertools.product((0, 1, 2, 3, 4), (0, 1)):
        pools[f"open{n0}+{nr}/rung"] = (n0,) + (nr,) * 6
    pools["live-like unlimited"] = None
    for name, pool in pools.items():
        if pool is None: continue
        for fbx in (0.25, 0.5):
            r = evaluate(pool, fbx, 0.25); r.update(pool=name, fb_xp=fbx); out.append(r)
            print(name, "fb", fbx, "| 6080", r["c6080"]["total"], r["c6080"]["fb"], r["c6080"]["boss_own"], "| 8060", r["c8060"]["total"], r["c8060"]["fb"], r["c8060"]["boss_own"],
                  "| mixed", r["mixed"]["total"], r["mixed"]["boss_own"], "| 6060", r["c6060"]["total"], r["c6060"]["fb"], r["c6060"]["boss_own"], "| story", r["story8080"]["min"])
    json.dump(out, open(__file__.replace(".py", "_grid.json"), "w"), indent=0)
