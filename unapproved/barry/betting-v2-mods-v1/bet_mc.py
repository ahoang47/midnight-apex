"""betting-v2-mods-v1 (draft, Barry 2026-11-14): betting re-run on the live mods-v1 economy and the 15 live stand-in tracks.
Rules (live constants): fair odds, net = stake x (1-p)/p, unlock after R2 (so R3, pre-finale arc and finale), any race
(story, grind, arc, billed finale), BET_MIN $500 .. BET_MAX $2,000, no count cap.
Monte Carlo: R1-R2 are the live deterministic walk (no betting yet). From R3 on every race attempt is rolled: a lost story
race is re-run, a lost grind pays nothing. p = the player's real win probability on that race (hardest track for 20-30-turn
races, district mean for 10-turn races, as the walk's own clear check), so the odds are priced on the same p that rolls.
The live just-in-time buyer (P.Garage.shop) spends after every credit, exactly as in the live walks.
Policies: none, likely (bet BET_MAX when p >= 0.65), always (bet BET_MAX on every race), grind-only (always, grinds only).
Ruin = a lost bet leaves cash below BET_MIN. Run from sim/:
PYTHONPATH=.:../unapproved/barry/mods-v1:../unapproved/barry/skill-points-v1:../unapproved/barry/betting-v2-mods-v1 python3 ../unapproved/barry/betting-v2-mods-v1/bet_mc.py"""
import copy, json, os, random, statistics as st, sys, time
import verify_live as V
from velocity_shift import equations as E, progression as P
A, core, arc = V.A, V.core, V.arc
HERE = os.path.dirname(os.path.abspath(__file__))
DIST = ("touge", "wangan", "street", "touge")
MODE = {"c8080": "story", "c6080": "mixed", "c8060": "mixed", "c6060": "hard"}
RACES = core.arc_races(core.LIVE_ARC, arc.M, fill=core.LIVE.ARC_STORY_FILL)
_C1, _C2 = {}, {}
def camp_p(pr, r, T, d, ps):
    k = (pr, round(r, 5), T, d, round(ps, 4))
    if k not in _C1:
        pk = P.win_pack(pr, r, T, d, ps); _C1[k] = (pk["district"] if T < 20 else P.hard_win(pk)) / 100
    return _C1[k]
def camp_grind_p(pr, r, d, ps):
    k = (pr, round(r, 5), d, round(ps, 4))
    if k not in _C1: _C1[k] = P.win_rate(pr, r, E.GRIND_TURNS, d, pow_share=ps) / 100
    return _C1[k]
def arc_p(pr, r, T, d):
    k = (pr, round(r, 5), T, d)
    if k not in _C2:
        pk = A.wr_cell(pr, r, T, d, True); _C2[k] = (pk["district"]["win"] if T < 20 else A.hard_win(pk)) / 100
    return _C2[k]

class S:  # bettor state
    def __init__(s, **kw): s.__dict__.update(kw)

def bet_roll(s, rng, p, grind, policy):
    """Place (or not) a bet, roll the race, settle the bet. Returns win."""
    stake = 0.0
    if policy != "none" and 0 < p < 1 and s.money >= E.BET_MIN and not (policy == "likely" and p < 0.65) and not (policy == "grind" and not grind):
        stake = min(E.BET_MAX, s.money)
    win = (rng.random() < p) if rng else True
    s.races += 1
    if stake:
        s.bets += 1; s.gbets += grind
        if win:
            net = stake * (1 - p) / p; s.money += net; s.profit += net; s.gprofit += net if grind else 0
        else:
            s.money -= stake; s.profit -= stake; s.gprofit -= stake if grind else 0
            if s.money < E.BET_MIN: s.ruin = True
        s.min_money = min(s.min_money, s.money)
    return win

def credit(s, pay):
    if s.debt > 0:
        take = min(s.debt, E.DEBT_SHARE * pay); s.debt -= take; s.money += pay - take
    else:
        s.money += pay

def walk_R3(s, pr, rng, policy):
    rnd = 2; d = "touge"; cap = E.CAP_LEVEL[rnd]; mode = MODE[pr]; G = s.G; done = s.done
    enter = s.L; ps = s.build.pow_share; done.add(("open", rnd))
    shop = lambda: setattr(s, "money", G.shop(s.money, s.L, rnd, d, done, True, "R3"))
    def grind1():
        r = G.power(s.L, rnd, d) / E.opponent_budget(rnd, 0); p = camp_grind_p(pr, r, d, ps(s.L)); s.grinds += 1
        if bet_roll(s, rng, p, True, policy):
            s.L, s.bag = P.apply_xp(s.L, E.grind_xp(s.L, cap), s.bag, cap); credit(s, E.purse(rnd, "kid", True)); s.gwins += 1
        shop()
    def ok(profiles, B, T):
        r = G.power(s.L, rnd, d) / B
        for q in profiles:
            pk = P.win_pack(q, r, T, d, ps(s.L))
            if pk["district"] < E.CLEAR_THRESHOLD or (T >= 20 and P.hard_win(pk) < E.CLEAR_THRESHOLD): return False
        return True
    wall_done = False
    for j, name in enumerate(E.LADDER_RUNGS):
        B = E.opponent_budget(rnd, j); T = E.LADDER_TURNS[j]; shop()
        if name == "boss" and mode in ("mixed", "hard"):
            g = 0
            while s.L < cap and g < 200: grind1(); g += 1
        if name != "boss" and s.L < cap:
            n = 0
            if mode == "mixed" and not wall_done and not ok(("c6080", "c8060"), B, T):
                while n < 80 and s.L < cap and not ok(("c6080", "c8060"), B, T): grind1(); n += 1
                wall_done = True
            elif mode == "hard":
                while n < 80 and s.L < cap and not ok(("c6060",), B, T): grind1(); n += 1
        tries = 0
        while True:
            p = camp_p(pr, G.power(s.L, rnd, d) / B, T, d, ps(s.L)); tries += 1
            if bet_roll(s, rng, p, False, policy): break
            shop()
            if tries > 400: s.stuck = True; break
        if name == "boss": s.boss_tries = tries; s.boss_p = p
        credit(s, E.purse(rnd, E.LADDER_RUNG_KIND[j], False)); done.add((rnd, name))
        s.L, s.bag = P.apply_xp(s.L, E.story_xp(rnd, j, enter, cap), s.bag, cap)
    shop()

def walk_arc(s, pr, rng, policy):
    mode = MODE[pr]; G = s.G; done = s.done
    def shop(st): s.money = G.shop(s.money, int(s.L), 3 + st, DIST[st], done, False, "arc")
    def power(st): shop(st); return G.power(int(s.L), 3 + st, DIST[st])
    def grind(st, cap_L, dist, stop=None):
        n = 0
        while s.L < cap_L and n < 400:
            if stop and stop(): break
            c = power(st); p = arc_p(pr, A.GRIND_R, 10, dist); s.grinds += 1; s.arc_grinds[st] += 1; n += 1
            if bet_roll(s, rng, p, True, policy):
                credit(s, A.GRIND_PAY); s.L, s.bag = A.apply_xp(s.L, A.grind_xp(s.L, cap_L, A.XP), s.bag, A.XP, cap_L); s.gwins += 1
            shop(st)
    for rc in RACES:
        st = rc["step"]; cap_L = A.CAPS[st + 1]
        hard = lambda: arc_p(pr, power(st) / rc["B"], rc["T"], rc["dist"])
        if mode in ("mixed", "hard") and not rc["billed"] and s.L < cap_L and hard() < 0.5:
            grind(st, cap_L, rc["dist"], stop=lambda: hard() >= 0.5)
        if rc["billed"] and mode in ("mixed", "hard") and s.L < cap_L:
            grind(st, cap_L, rc["dist"])
        tries = 0
        while True:
            p = arc_p(pr, power(st) / rc["B"], rc["T"], rc["dist"]); tries += 1
            if bet_roll(s, rng, p, False, policy): break
            if tries > 400: s.stuck = True; break
        if rc["billed"]: s.fin_p.append(round(100 * p, 1)); s.fin_tries.append(tries)
        done.add(P.arc_unlock_token(rc["id"]))          # every arc win (story and billed) is an unlock token (Myth2 after F1 ...)
        credit(s, rc["purse"]); shop(st)
        if not rc["billed"]:
            s.L, s.bag = A.apply_xp(s.L, rc["fill"] * rc["xp_share"] * A.GAP_XP[st], s.bag, A.XP, cap_L); shop(st)

def entry(pr):
    """Live deterministic R1-R2, then the R3 entry (retune, previous cap)."""
    mode = MODE[pr]; L, bag, money, debt = 0, 0.0, 0.0, E.DEBT_AMOUNT; alloc = P.start_build(); G = P.Garage(); done = set()
    for rnd in range(2):
        d = E.ROUND_DISTRICTS[rnd].lower()
        if rnd > 0:
            alloc = P.retune(alloc, d); end_L, L, bag = L, E.CAP_LEVEL[rnd - 1], 0.0
            alloc = P.add_points(alloc, E.skill_points(L) - E.skill_points(end_L), d)
        w = P._walk_round(rnd, L, bag, money, debt, mode, P.Build(d, alloc, L), G, done)
        L, bag, money, debt = w["L"], w["bag"], w["money"], w["debt"]; alloc = w["build"]
    alloc = P.retune(alloc, "touge"); end_L, L = L, E.CAP_LEVEL[1]
    alloc = P.add_points(alloc, E.skill_points(L) - E.skill_points(end_L), "touge")
    return dict(L=L, bag=0.0, money=money, debt=debt, G=G, done=done, build=P.Build("touge", alloc, L))

def run_one(pr, ent, policy, rng):
    s = S(L=ent["L"], bag=ent["bag"], money=ent["money"], debt=ent["debt"], G=copy.deepcopy(ent["G"]), done=set(ent["done"]), build=ent["build"],
          races=0, bets=0, gbets=0, profit=0.0, gprofit=0.0, ruin=False, stuck=False, grinds=0, gwins=0, min_money=ent["money"],
          fin_p=[], fin_tries=[], arc_grinds=[0, 0, 0, 0])
    walk_R3(s, pr, rng, policy); r3 = dict(money=s.money, profit=s.profit, grinds=s.grinds, boss_tries=s.boss_tries, boss_p=s.boss_p, L=s.L)
    walk_arc(s, pr, rng, policy)
    return dict(r3=r3, end=s.money, profit=s.profit, gprofit=s.gprofit, bets=s.bets, gbets=s.gbets, ruin=s.ruin, stuck=s.stuck,
                min_money=s.min_money, grinds=s.grinds, fin_p=s.fin_p, fin_tries=s.fin_tries, arc_grinds=s.arc_grinds, spent=s.G.spent)

def q(xs, f):
    xs = sorted(xs); return round(xs[min(len(xs) - 1, int(f * len(xs)))], 0)

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000; t0 = time.time()
    ents = {pr: entry(pr) for pr in P.PROFILES}
    res = {}
    for pr in P.PROFILES:
        det = run_one(pr, ents[pr], "none", None)          # all races won once: the live deterministic walk
        res[pr] = dict(entry_money=round(ents[pr]["money"]), det=dict(r3=round(det["r3"]["money"]), end=round(det["end"]), fin_p=det["fin_p"], arc_grinds=det["arc_grinds"]))
        for pol in ("none", "likely", "always", "grind"):
            rng = random.Random(20261114 + hash((pr, pol)) % 10_000_019)
            rows = [run_one(pr, ents[pr], pol, rng) for _ in range(N)]
            nb = sum(r["bets"] for r in rows); ng = sum(r["gbets"] for r in rows)
            res[pr][pol] = dict(
                n=N, bets_mean=round(nb / N, 1), grind_bets_mean=round(ng / N, 1),
                profit_mean=round(st.mean(r["profit"] for r in rows)), profit_p10=q([r["profit"] for r in rows], .1), profit_p90=q([r["profit"] for r in rows], .9),
                profit_per_bet=round(sum(r["profit"] for r in rows) / nb, 1) if nb else 0.0,
                grind_profit_per_bet=round(sum(r["gprofit"] for r in rows) / ng, 1) if ng else 0.0,
                ruin_pct=round(100 * sum(r["ruin"] for r in rows) / N, 1), stuck_pct=round(100 * sum(r["stuck"] for r in rows) / N, 1),
                r3_mean=round(st.mean(r["r3"]["money"] for r in rows)), r3_p10=q([r["r3"]["money"] for r in rows], .1), r3_p50=q([r["r3"]["money"] for r in rows], .5),
                end_mean=round(st.mean(r["end"] for r in rows)), end_p10=q([r["end"] for r in rows], .1), end_p50=q([r["end"] for r in rows], .5), end_p90=q([r["end"] for r in rows], .9),
                min_money_p10=q([r["min_money"] for r in rows], .1),
                r3_boss_p=round(100 * st.mean(r["r3"]["boss_p"] for r in rows), 1), r3_boss_tries=round(st.mean(r["r3"]["boss_tries"] for r in rows), 2),
                r3_grinds=round(st.mean(r["r3"]["grinds"] for r in rows), 1),
                fin_p=[round(st.mean(r["fin_p"][i] for r in rows), 1) for i in range(4)], fin_p_min=[min(r["fin_p"][i] for r in rows) for i in range(4)],
                fin_tries=[round(st.mean(r["fin_tries"][i] for r in rows), 2) for i in range(4)],
                arc_grinds=[round(st.mean(r["arc_grinds"][i] for r in rows), 1) for i in range(4)],
                spent=round(st.mean(r["spent"] for r in rows)))
            print(pr, pol, res[pr][pol], flush=True)
    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    print("elapsed", round(time.time() - t0), "s")
