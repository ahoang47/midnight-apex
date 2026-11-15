"""Campaign walk R1-R3 with the staged catalog and a just-in-time buyer (draft; mirrors live progression._walk_round
and run() with garage power in place of combat_power). Usage: python3 catalog_walk.py [slots]"""
import sys, json, copy
import catalog as C
from catalog import E, P

def walk_round(rnd, L, bag, money, debt, mode, build, G, done, log):
    d = E.ROUND_DISTRICTS[rnd].lower(); cap = E.CAP_LEVEL[rnd]; ps = build.pow_share
    wholesale = E.WHOLESALE_STARTS_AFTER <= rnd < E.WHOLESALE_ENDS_AFTER
    done.add(("open", rnd)); rows = []; st = dict(L=L, bag=bag, money=money, debt=debt, total=0, wall=0, post=0, wall_name=None, wall_done=False)
    def credit(kind, grind):
        pay = E.purse(rnd, kind, grind)
        if st["debt"] > 0:
            take = min(st["debt"], E.DEBT_SHARE * pay); st["debt"] -= take; st["money"] += pay - take
        else: st["money"] += pay
    def shop(tag):
        st["money"] = G.shop(st["money"], st["L"], rnd, d, done, wholesale, tag)
    def grind1(tag):
        st["L"], st["bag"] = P.apply_xp(st["L"], E.grind_xp(st["L"], cap), st["bag"], cap); credit("kid", True); st["total"] += 1; shop(tag)
    def ok(profiles, B, T):
        r = G.power(st["L"], rnd, d) / B
        for pr in profiles:
            pk = P.win_pack(pr, r, T, d, ps(st["L"]))
            if pk["district"] < E.CLEAR_THRESHOLD or (T >= 20 and P.hard_win(pk) < E.CLEAR_THRESHOLD): return False
        return True
    def grind_until(profiles, B, T, tag):
        n = 0
        while n < 80 and st["L"] < cap and not ok(profiles, B, T):
            grind1(tag); n += 1
        return n
    for j, name in enumerate(E.LADDER_RUNGS):
        B = E.opponent_budget(rnd, j); T = E.LADDER_TURNS[j]; pre_boss = here = 0; tag = f"R{rnd+1} {name}"
        cash_pre = st["money"]; shop(tag)
        if name == "boss" and mode in ("mixed", "hard") and st["L"] < cap:
            before = st["total"]
            while st["L"] < cap: grind1(tag)
            pre_boss = st["total"] - before
            if st["wall_done"] or mode == "hard": st["post"] += pre_boss
        if name != "boss" and st["L"] < cap:
            if mode == "mixed" and not st["wall_done"] and not ok(("c6080", "c8060"), B, T):
                here = grind_until(("c6080", "c8060"), B, T, tag); st["wall"] = here; st["wall_name"] = name; st["wall_done"] = True
            elif mode == "hard" and not ok(("c6060",), B, T):
                here = grind_until(("c6060",), B, T, tag)
                if st["wall_name"] is None: st["wall_name"] = name; st["wall"] += here
                else: st["post"] += here
        aL = st["L"]; pw = G.power(aL, rnd, d); r = pw / B
        packs = {pr: P.win_pack(pr, r, T, d, ps(aL)) for pr in P.PROFILES}
        r_grind = pw / E.opponent_budget(rnd, 0)
        row = dict(rnd=rnd + 1, rung=name, turns=T, arrive_L=aL, arrive_r=round(r, 4), fill=round(100 * G.fill(aL, rnd, d), 1),
                   live_r=round(P.combat_power(aL, rnd) / B, 4), wr=packs, grind_here=here, pre_boss_grind=pre_boss,
                   grind10={pr: round(P.win_rate(pr, r_grind, E.GRIND_TURNS, d, pow_share=ps(aL)), 1) for pr in P.PROFILES},
                   equipped=[m["id"] if m else "stock" for m in G.equipped(d)], owned=len(G.owned),
                   money_before=round(st["money"], 0), cash_pre=round(cash_pre, 0))
        if name == "boss":
            row["boss_check"] = P.boss_check(round(r, 4), d, ps(aL))
        credit(E.LADDER_RUNG_KIND[j], False); done.add((rnd, name))
        st["L"], st["bag"] = P.apply_xp(st["L"], E.story_xp(rnd, j, L, cap), st["bag"], cap)
        row.update(money_after=round(st["money"], 0), debt=round(max(st["debt"], 0), 0), L_after=st["L"])
        rows.append(row)
    shop(f"R{rnd+1} end")
    return dict(rows=rows, L=st["L"], bag=st["bag"], money=st["money"], debt=max(st["debt"], 0.0), total_grind=st["total"],
                wall_grind=st["wall"], wall=st["wall_name"], post_wall_to_cap=st["post"], cap=cap, build=build.at(st["L"]))

def run(mode, slots, cat=None):
    cat = cat or C.build(slots); G = C.Garage(slots, cat); done = set(); log = []
    L, bag, money, debt = 0, 0.0, 0.0, E.DEBT_AMOUNT; out = []; alloc = P.start_build()
    for rnd in range(3):
        d = E.ROUND_DISTRICTS[rnd].lower()
        if rnd > 0:
            alloc = P.retune(alloc, d); end_L, L, bag = L, E.CAP_LEVEL[rnd - 1], 0.0
            alloc = P.add_points(alloc, E.skill_points(L) - E.skill_points(end_L), d)
        w = walk_round(rnd, L, bag, money, debt, mode, P.Build(d, alloc, L), G, done, log); out.append(w)
        L, bag, money, debt = w["L"], w["bag"], w["money"], w["debt"]; alloc = w["build"]
    return out, G, done

if __name__ == "__main__":
    slots = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    for mode in ("story", "mixed", "hard"):
        out, G, _ = run(mode, slots)
        print(f"== {mode} {slots} slots: spent {G.spent:.0f}, owned {len(G.owned)}, grinds {[w['total_grind'] for w in out]}, end money {out[-1]['money']:.0f}")
        for w in out:
            for r in w["rows"]:
                print(f" R{r['rnd']} {r['rung']:5} L{r['arrive_L']:>2} fill {r['fill']:5.1f} r {r['arrive_r']:.4f}/{r['live_r']:.4f} "
                      f"8080 {r['wr']['c8080']['district']:5.1f}/{P.hard_win(r['wr']['c8080']):5.1f} 6060 {r['wr']['c6060']['district']:5.1f} "
                      f"g{r['grind_here']}+{r['pre_boss_grind']} ${r['money_before']:.0f}->{r['money_after']:.0f} own {r['owned']} {' '.join(r['equipped'])}")
