"""planner-v2: Python reference for the Page engine (engine.ts), plus a scripted playthrough (script.json) and an
error-path plan (script_errors.json). Rules are the LIVE mod_skill rules (sim/velocity_shift/mod_skill.py): 4 slots, the slot
step on a buy (current round's Mk1 over an older group, else the next Mk; Mk2 after the mat1 win, Mk3 after the mat2 win),
Garage.assign (XP to the slot with the most room first, spilling; the rest is lost but still counts in the ledger),
floors on the ledger, required wild encounters before each rung, non-mandatory wins pay XP for the first NM_CAP per round.
Every planned race is a win. Win % = the Monte Carlo table (build_tables.py) at the standard reading curve s and the car's
points, bilinear in (s, points), rounded to 0.1. All constants: constants.json (gen_constants.py, from the live sim).
Run: python3 py_reference.py -> py_reference.json"""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
K = json.load(open(os.path.join(HERE, "constants.json"))); C, WT = K["C"], K["WT"]


def r1(x): return math.floor(x * 10 + 0.5 + 1e-9) / 10


def span(xs, x):
    n = len(xs)
    if x <= xs[0]: return 0, 0, 0.0
    if x >= xs[-1]: return n - 1, n - 1, 0.0
    i = 1
    while xs[i] < x and abs(xs[i] - x) >= 1e-12: i += 1
    if abs(xs[i] - x) < 1e-12: return i, i, 0.0
    return i - 1, i, (x - xs[i - 1]) / (xs[i] - xs[i - 1])


def win_at(d, j, s, pts):
    t = WT["WIN"][d][j]; q0, q1, fq = span(WT["Q"], s); p0, p1, fp = span(WT["PTS"][d], pts)
    lo = t[q0][p0] * (1 - fp) + t[q0][p1] * fp; hi = t[q1][p0] * (1 - fp) + t[q1][p1] * fp
    return r1(lo * (1 - fq) + hi * fq)


def usd(x): return "$" + f"{round(x):,}"


def simulate(plan):
    cash, debt, ledger = 0.0, C["DEBT"], float(C["STOCK"])
    slots = [None] * C["SLOTS"]; rows = []
    pts = lambda: C["STOCK"] + sum(s[2] for s in slots if s)

    def credit(pay):
        nonlocal cash, debt
        t = min(debt, C["DEBT_SHARE"] * pay) if debt > 0 else 0.0
        debt -= t; cash += pay - t

    def assign(xp):
        nonlocal ledger
        ledger += xp
        for s in sorted((s for s in slots if s), key=lambda s: s[2] - C["TIER"][s[0]][s[1] - 1]):
            room = C["TIER"][s[0]][s[1] - 1] - s[2]
            if room > 0 and xp > 0:
                t = min(room, xp); s[2] += t; xp -= t
        return xp

    for rnd, d in enumerate(C["ROUNDS"]):
        nmw = 0; ws = C["WHOLESALE_ON"][rnd]
        ex = []
        for j in range(7):
            rid = f"R{rnd + 1} {C['RUNGS'][j]}"
            w = max(0, int(plan["wilds"].get(rid, 0))); n = max(0, int(plan["nm"].get(rid, 0)))
            ex.append((min(w, C["REQ_WILDS"][j]), n + max(0, w - C["REQ_WILDS"][j])))
        N = 6 + sum(a + b for a, b in ex); ran = 0
        for j, rung in enumerate(C["RUNGS"]):
            rid = f"R{rnd + 1} {rung}"; err = []; req, nm = ex[j]

            def buy(phase):
                nonlocal cash
                top = (C["MK_PRE"] if phase == "pre" else C["MK_POST"])[j]
                for b in plan["buys"]:
                    if b["at"] != rid or b["phase"] != phase: continue
                    i = int(b["slot"]); s = slots[i]
                    g, mk = (rnd, 1) if (s is None or s[0] < rnd) else (s[0], s[1] + 1)
                    if mk > 3:
                        err.append(f"buy slot {i + 1}: already Mk3"); continue
                    if mk > top:
                        err.append(f"buy slot {i + 1}: Mk{mk} not on sale yet"); continue
                    price = C["PRICE_WS" if ws else "PRICE"][g][mk - 1]
                    if price > cash + 1e-9:
                        err.append(f"buy slot {i + 1}: needs {usd(price)}, have {usd(cash)}"); continue
                    cash -= price
                    slots[i] = [g, mk, s[2] if s else 0.0]

            buy("pre")
            lostX = 0.0
            for _ in range(req):
                credit(C["WILD_PURSE"][rnd]); lostX += assign(C["WILD_XP"][rnd])
            for _ in range(nm):
                credit(C["WILD_PURSE"][rnd]); lostX += assign(C["WILD_XP"][rnd] if nmw < C["NM_CAP"] else 0); nmw += 1
            ran += req + nm
            skill = C["SKILL"][0] + (C["SKILL"][1] - C["SKILL"][0]) * ran / N
            p = pts(); fl = C["FLOOR"][d][j]
            if req < C["REQ_WILDS"][j]:
                err.append(f"needs {C['REQ_WILDS'][j]} required wild win(s) first, has {req}")
            if ledger < fl - 1e-9:
                err.append(f"locked: earned {ledger:.1f} < floor {fl}")
            ok = req >= C["REQ_WILDS"][j] and ledger >= fl - 1e-9
            win = win_at(d, j, skill, p) if ok else None; lr = ledger
            credit(C["PURSE"][rnd][C["KIND"][j]])
            buy("post")
            lostW = assign(C["STORY_XP"][rnd][j])
            ran += 1
            rows.append(dict(id=rid, skill=round(skill, 6), points=round(p, 4), ledger=round(lr, 4), win=win, cash=round(cash, 2),
                             debt=round(debt, 2), lostX=round(lostX, 4), lostW=round(lostW, 4), nmw=nmw,
                             slots=[None if s is None else [s[0], s[1], round(s[2], 4)] for s in slots], errors=err))
    return rows


def script():
    """A full legal playthrough: required wilds everywhere, some non-mandatory wins, buys as cash and unlocks allow."""
    wilds = {f"R{r + 1} {x}": C["REQ_WILDS"][j] for r in range(3) for j, x in enumerate(C["RUNGS"])}
    nm = {"R1 kid2": 2, "R1 mat2": 3, "R1 boss": 6, "R2 kid1": 4, "R2 oh1": 5, "R2 boss": 6, "R3 kid2": 6, "R3 oh2": 6, "R3 boss": 3}
    buys = [dict(at="R1 kid1", phase="pre", slot=0)]                          # unaffordable ($0 on arrival)
    buys += [dict(at="R1 kid1", phase="post", slot=i) for i in range(4)]
    buys += [dict(at="R1 kid2", phase="post", slot=0),                         # Mk2 not on sale before the mat1 win
             dict(at="R1 mat1", phase="post", slot=0), dict(at="R1 mat1", phase="post", slot=1),
             dict(at="R1 mat2", phase="post", slot=0), dict(at="R1 mat2", phase="post", slot=2), dict(at="R1 mat2", phase="post", slot=3),
             dict(at="R1 oh1", phase="post", slot=0)]                          # already Mk3
    for r in (2, 3):
        buys += [dict(at=f"R{r} kid1", phase="pre", slot=i) for i in range(4)]
        buys += [dict(at=f"R{r} mat1", phase="post", slot=i) for i in range(4)]
        buys += [dict(at=f"R{r} mat2", phase="post", slot=i) for i in range(4)]
    return dict(wilds=wilds, nm=nm, buys=buys)


def error_script():
    """Validation paths: R1 mat1 without its required wild and without the R1 kid2 extra wins (missing wild + floor lock),
    extra wilds at R2 mat2 (the excess counts as non-mandatory), R3 oh1 without its wild, and no R2 buys (R1 slots carry)."""
    p = script()
    p["wilds"] = dict(p["wilds"], **{"R1 mat1": 0, "R2 mat2": 3, "R3 oh1": 0}); p["nm"] = dict(p["nm"], **{"R1 kid2": 0})
    p["buys"] = [b for b in p["buys"] if not b["at"].startswith("R2")]
    return p


if __name__ == "__main__":
    plan = script(); json.dump(plan, open(os.path.join(HERE, "script.json"), "w"), indent=1)
    rows = simulate(plan); eplan = error_script(); erows = simulate(eplan)
    json.dump(eplan, open(os.path.join(HERE, "script_errors.json"), "w"), indent=1)
    json.dump(dict(main=rows, errors=erows), open(os.path.join(HERE, "py_reference.json"), "w"), indent=1)
    print("error plan:", sorted({e for x in erows for e in x["errors"]}))
    for x in rows:
        print(x["id"], round(x["skill"], 3), x["points"], x["ledger"], x["win"], x["cash"], x["debt"], x["lostX"], x["lostW"], x["errors"])
