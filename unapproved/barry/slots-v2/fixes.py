"""slots-v2 part B (NOT approved): three fixes for V1/V2 (strong player clears R1 Wangan / R2 Touge mature #2 with only the newly
unlocked tier), run on the LIVE constants after 5e5d902 (KNOT_WINDOW_105 r=1.00 knot 0.67, aero pool <= 10%).

Same progression loop as prog.run (official forced player: at each story rung, clear = pooled mid >= 50 at the skip state with the
best allowed loadout; otherwise grind to the level cap, then race). Same oracle (share grid, N=4000, seeds 20261113-15 x 10/20/30
turns, 9 paired banks). Only the equipped mod lines change per fix:
  base  official schedule (slots-v1 scheme C): the tier unlocked by win k-1 is equipped at rung k.
  a     P2 grind-matched prices: purchases cost money; wallet +1 race-unit per race (story win or grind race), starts at 0 at mod
        unlock (race 4). Price per purchase = per crew min(weak, avg) forced income / purchases, from the base run (default order).
        Pending tiers are bought in schedule order whenever affordable (on arrival and after grinding).
  a0    as a, but the R1 opening 6-mod set is pre-funded (wallet starts at its cost) - isolates the first-crew effect.
  b     level floor: every crew's mature #2 tier (bought on arrival at j=3) needs level >= that rung's level cap; at the skip state it
        is not fitted unless the player is already at the cap. It is fitted after grinding to the cap, or at the first later rung
        where the player's level reaches that floor (story XP).
  b2    minimal level floor: the mature #2 tier needs level >= (level a never-grinding player has at that rung) + 1, i.e. it can
        only be fitted with some grinding behind you; same release rule as b.
  b3    crew-local level floor: level >= (level at that rung of a player who reached the previous crew boss's level cap and has
        not ground in this crew) + 1, i.e. the tier needs some grinding inside the current crew; same release rule as b.
  c     delayed unlock: the mature #2 tier unlocks after the mature #2 win (fitted from old head #1, j=4) instead of after mature #1.
Policies: balanced (2/2/2, 100/0/0), window (+75%, 1.15 w0 cap, any slot, max one), aero10 (pool 10%, + window allowed).
'decisive' = rung cleared at the skip state whose clear depends on the newest fitted purchase (mid with >= 50 > mid with the
previous rung's fitted lines, same SP/B). Writes results_fixes.json."""
import json, sys
import numpy as np
from multiprocessing import Pool
import model as M, prog, cells as R

E, P = M.E, M.P
SPLIT = "100/0/0"
FIXES = ("base", "a", "a0", "b", "b2", "b3", "c")
POLICIES = ("balanced", "window", "aero10")


def sched_list():
    return [s for s in M.S1.schedule("C") if s["crew"] != "Finale"]


def items(buy, before):
    """Individual purchases of one schedule entry: list of (line, new value)."""
    if buy is None:
        return []
    if isinstance(buy, tuple) and buy[0] == "initial":
        return [(i, buy[2]) for i in range(buy[1])]
    return [(i, new) for i, _old, new in buy]


def p2_prices(base_grind):
    """Per-crew P2 price from base forced grind (default order): min(weak, avg) (story wins + grind) / purchases."""
    sch = sched_list(); price = {}
    for crew in dict.fromkeys(s["crew"] for s in sch):
        ss = [s for s in sch if s["crew"] == crew]
        n = sum(len(items(s["buy"], None)) for s in ss)
        inc = min(len(ss) + base_grind["weak"][crew], len(ss) + base_grind["average"][crew])
        price[crew] = inc / n
    return price


def never_levels(crew_local=False):
    """Level at each story rung (skip state) of a player who never grinds (story XP only), keyed by (crew, rung, j).
    crew_local: at each crew's first rung the player starts from the previous crew boss's level cap (no grind in this crew)."""
    SP, XC, X = P.curves(); Rl, Lf, Lstep, budgets, B_last = P.ladder(); xp = 0.0; out = {}; prev_boss_cap = None
    for i, x in enumerate(Rl):
        cap = x["L"]
        if crew_local and x["j"] == 0 and prev_boss_cap is not None:
            xp = max(xp, XC[prev_boss_cap])
        if x["kind"] == "boss":
            prev_boss_cap = cap
        xp = min(xp, XC[cap]); out[(x["crew"], x["rung"], x["j"])] = P._level(XC, xp, cap)
        nxt = Rl[i + 1]["L"] if i + 1 < len(Rl) else Lf[0]
        unl = XC[Lstep if i + 1 == len(Rl) else nxt] - XC[cap]
        if x["k"] == 2:
            add = 0.0
        elif x["kind"] == "boss" or x["k"] == 3:
            add = E.STORY_XP_BOSS * unl
        else:
            lam = E.STORY_XP_LT_ROUND_OPEN if x["ro"] else E.STORY_XP_LT
            add = max(lam * unl, E.STORY_XP_LT_FLOOR * X[max(1, nxt)])
        xp = min(xp + add, XC[nxt])
    return out


NEVER_L = never_levels()
LOCAL_L = never_levels(crew_local=True)


def run(fix, policy, profile, price=None):
    SP, XC, X = P.curves(); Rl, Lf, Lstep, budgets, B_last = P.ladder()
    key = {(s["crew"], s["rung"], s["j"]): s for s in M.S1.schedule("C")}
    xp = 0.0; rows = []; lost = 0.0
    lines = np.zeros(6); queue = []; wallet = 0.0; prev_lines = None; spent = 0.0; gated = []; floor = 0; gate = False

    def grind_to(v, cap, j):
        n = 0
        while XC[cap] - v > 1e-9 and n <= 200:
            Ln = P._level(XC, v, cap) + 1
            v = min(v + E.grind_payout_fraction(Ln, j) * X[Ln], XC[cap]); n += 1
        return n, v

    def buy_affordable():
        nonlocal wallet, spent
        while queue and (price is None or wallet + 1e-9 >= queue[0][2]):
            i, val, cost, _crew = queue.pop(0)
            lines[i] = val
            if price is not None:
                wallet -= cost; spent += cost

    def mid_of(lv, L, x):
        return prog.best_mid(SP[L], lv, x["B"], SPLIT, policy, R.aero_ok(x["crew"]), profile)

    for i, x in enumerate(Rl):
        cap = x["L"]
        if xp > XC[cap] + 1e-9:
            lost += xp - XC[cap]; xp = XC[cap]
        L = P._level(XC, xp, cap)
        row = dict(crew=x["crew"], rung=x["rung"], j=x["j"])
        if x["kind"] == "scripted":
            clear = True
        else:
            s = key[(x["crew"], x["rung"], x["j"])]
            if x["crew"] != "Prologue":
                new = [(a, b, (price[x["crew"]] if price else 0.0), x["crew"]) for a, b in items(s["buy"], None)]
                if fix == "a0" and isinstance(s["buy"], tuple) and s["buy"][0] == "initial":
                    wallet += sum(c for _, _, c, _ in new)          # pre-fund the R1 opening set
                if fix == "c" and x["j"] == 3:
                    held = new; new = []                             # mature #2 tier waits for the mature #2 win
                elif fix == "c" and x["j"] == 4:
                    new = held + new
                if fix in ("b", "b2", "b3") and gated and L >= floor:    # floor met later (story XP): release the gated tier
                    queue.extend(gated); gated = []
                gate = fix in ("b", "b2", "b3") and x["j"] == 3
                if gate:
                    gated = new; new = []
                    floor = cap if fix == "b" else min(cap, (NEVER_L if fix == "b2" else LOCAL_L)[(x["crew"], x["rung"], x["j"])] + 1)
                    row["floor"] = floor; row["level_skip"] = L; row["xp_skip"] = xp
                queue.extend(new); buy_affordable()
                lv = lines.copy()
                if gate and L >= floor:                              # already at the floor level
                    queue.extend(gated); gated = []; buy_affordable(); lv = lines.copy(); gate = False
            else:
                lv = np.full(6, x["mods"] / 6)
            m, pick = mid_of(lv, L, x); clear = m >= E.CLEAR_THRESHOLD
            row.update(mid_skip=round(m, 2), pick=pick, total_mods=round(float(lv.sum()), 2), sched_mods=round(s["mods"], 2) if x["crew"] != "Prologue" else None)
            if prev_lines is not None and x["j"] in (3, 6) and clear and not np.allclose(prev_lines, lv):
                mp, _ = mid_of(prev_lines, L, x); row["mid_prev_lines"] = round(mp, 2); row["decisive"] = bool(mp < E.CLEAR_THRESHOLD)
        n, v2 = grind_to(xp, cap, max(0, x["j"]))
        g = 0 if clear else n
        if g:
            xp = v2
            if price is not None:
                wallet += g
            if x["kind"] != "scripted" and x["crew"] != "Prologue":
                if fix in ("b", "b2", "b3") and x["j"] == 3 and gate:
                    queue.extend(gated); gated = []; gate = False
                buy_affordable()
                lt = lines.copy(); mt, _ = mid_of(lt, cap, x)
                row.update(mid_at_cap=round(mt, 2), total_mods_at_cap=round(float(lt.sum()), 2))
        if x["kind"] != "scripted" and x["crew"] != "Prologue":
            prev_lines = lines.copy()
            if price is not None:
                wallet += 1.0                                         # story race purse
        row.update(grind=g, wallet=round(wallet, 2), queued=len(queue)); rows.append(row)
        nxt = Rl[i + 1]["L"] if i + 1 < len(Rl) else Lf[0]
        unl = XC[Lstep if i + 1 == len(Rl) else nxt] - XC[cap]
        if x["k"] == 2:
            add = 0.0
        elif x["kind"] == "boss" or x["k"] == 3:
            add = E.STORY_XP_BOSS * unl
        else:
            lam = E.STORY_XP_LT_ROUND_OPEN if x["ro"] else E.STORY_XP_LT
            add = max(lam * unl, E.STORY_XP_LT_FLOOR * X[max(1, nxt)])
        before = xp; xp = min(xp + add, XC[nxt]); lost += before + add - xp
    for (nm, d, B), Lc in zip(E.FINALE, Lf):
        if xp > XC[Lc]:
            lost += xp - XC[Lc]; xp = XC[Lc]
        n, v2 = grind_to(xp, Lc, E.TAPER_FINALE_RUNG); xp = v2
        rows.append(dict(crew="Finale", rung=nm, j=E.TAPER_FINALE_RUNG, grind=n))
    dead = sum(1 for s in sched_list() if s["buy"] is None) + (9 if fix == "c" else 0)
    tot = dict(grind_races=sum(r["grind"] for r in rows), levels=Lf[-1], lost_xp=round(lost), dead_wins=dead,
               unbought_at_end=len(queue), money_spent=round(spent, 2), wallet_end=round(wallet, 2))
    return rows, tot


def job(a):
    fix, pol, prof, price = a
    rows, t = run(fix, pol, prof, price if fix in ("a", "a0") else None)
    print(fix, pol, prof, t, flush=True)
    return f"{fix}|{pol}|{prof}", dict(total=t, rows=rows)


if __name__ == "__main__":
    # base per-crew forced grind (balanced) -> P2 prices
    bg = {}
    for prof in ("weak", "average"):
        rows, _ = run("base", "balanced", prof)
        g = {}
        for r in rows:
            if r["crew"] not in ("Prologue", "Finale"):
                g[r["crew"]] = g.get(r["crew"], 0) + r["grind"]
        bg[prof] = g
    price = p2_prices(bg)
    print("P2 prices", {k: round(v, 2) for k, v in price.items()}, flush=True)
    jobs = [(f, pol, prof, price) for pol in POLICIES for f in FIXES for prof in M.PROFILES]
    res = {}
    with Pool(8) as pool:
        for k, v in pool.imap_unordered(job, jobs, chunksize=1):
            res[k] = v                                             # save as results arrive (long aero10 jobs)
            json.dump(dict(p2_price=price, base_grind_by_crew=bg, runs=res), open("results_fixes.json", "w"), separators=(",", ":"), default=float)
