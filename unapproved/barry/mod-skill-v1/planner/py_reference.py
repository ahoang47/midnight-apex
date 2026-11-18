"""mod_skill planner: Python reference for the Page engine, plus one scripted playthrough (script.json).
Same rules as ../walk.py (recommended config) but every choice comes from the plan: base setup per district, mod splits
per district, grinds per race, buys (before grinds / after the win), and the mod each race's grind XP and win XP go to.
Win % = the live progression.win_rate per profile (unrounded), blended by the standard reading curve, rounded to 0.1.
Run: python3 py_reference.py  -> py_reference.json"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "sim"))
from velocity_shift import equations as E, progression as P

C = json.load(open(os.path.join(HERE, "constants.json")))
SI = {"P": 0, "H": 1, "E": 2}


def skill_weights(s):
    a = min(1.0, max(0.0, (s - 0.6) / 0.2))
    return [("c6060", (1 - a) * (1 - a)), ("c6080", (1 - a) * a), ("c8060", a * (1 - a)), ("c8080", a * a)]


def pack(s, r, T, d, ps):
    w = skill_weights(s); dm = sum(k * P.win_rate(pr, r, T, d, pow_share=ps) for pr, k in w)
    h = None
    if T in C["HARD_TURNS"][d]:
        h = round(sum(k * P.win_rate(pr, r, T, track=E.BOSS_HARD_TRACK[d], pow_share=ps) for pr, k in w), 1)
    return dict(d=round(dm, 1), h=h)


def take(pay, debt):
    if debt > 0:
        t = min(debt, C["DEBT_SHARE"] * pay); return pay - t, debt - t
    return pay, 0.0


def simulate(plan):
    cash, debt, mods, rows = 0.0, C["DEBT"], {}, []
    for rnd, d in enumerate(C["ROUNDS"]):
        kit = C["KITS"][d]
        pts = lambda: C["STOCK_TOTAL"] + sum(mods[k][1] for k in kit if k in mods)
        short = max(0.0, 10 * C["CAP_POWER"][rnd - 1] - pts()) if rnd else 0.0
        g = [int(plan["grinds"].get(f"R{rnd + 1} {C['RUNGS'][j]}", 0)) for j in range(7)]
        N = 6 + sum(g); ran = 0
        for j, rung in enumerate(C["RUNGS"]):
            rid = f"R{rnd + 1} {rung}"; err = []; T = C["TURNS"][j]
            cash_arr, debt_arr = cash, debt

            def buy(phase):
                nonlocal cash
                for b in plan["buys"]:
                    if b["at"] != rid or b["phase"] != phase:
                        continue
                    k = b["key"]
                    if k not in kit:
                        err.append(f"buy {k}: not a slot in this district"); continue
                    if k in mods and mods[k][0] >= rnd + 1:
                        err.append(f"buy {k}: already at the R{rnd + 1} tier"); continue
                    price = C["PRICE"][rnd] * ((1 - C["WHOLESALE"]) if rnd in (1, 2) else 1.0)
                    if price > cash + 1e-9:
                        err.append(f"buy {k}: needs ${price:,.0f}, have ${cash:,.0f}"); continue
                    cash -= price
                    if k in mods: mods[k][0] = rnd + 1
                    else: mods[k] = [rnd + 1, 0.0]

            def assign(pick, xp, what):
                if xp <= 0:
                    return 0.0
                if not pick:
                    err.append(f"{what} XP not assigned ({xp:.1f} lost)"); return xp
                if pick not in kit or pick not in mods:
                    err.append(f"{what} XP to {pick}: not an owned mod in this kit ({xp:.1f} lost)"); return xp
                left = xp
                for k in [pick] + [k for k in kit if k != pick]:
                    if k in mods and left > 0:
                        room = C["CEIL"][mods[k][0] - 1] - mods[k][1]
                        if room > 0:
                            add = min(room, left); mods[k][1] += add; left -= add
                return left

            buy("pre")
            lostG = 0.0
            for _ in range(g[j]):
                net, debt = take(C["PAY"]["kid"] * C["PAY_MULT"][rnd] * C["GRIND_PAY_FRAC"], debt); cash += net
                lostG += assign(plan["pickG"].get(rid), C["GRIND_XP"][rnd], "Grind")
            ran += g[j]
            skill = 0.6 + 0.2 * ran / N
            p = pts(); power = min(C["CAP_POWER"][rnd], p / 10); B = C["C_ROUND"][rnd] / C["TARGET_R"][d][j]; r = power / B
            base = plan["base"].get(d); stats = None; ok = True
            if not base or len(base) != 3 or abs(sum(base) - C["STOCK_TOTAL"]) > 1e-9 or any(x < C["BASE_MIN"] or x > C["BASE_MAX"] for x in base):
                err.append("base setup invalid"); ok = False
            else:
                stats = list(map(float, base))
                for k in kit:
                    if k in mods and mods[k][1] > 0:
                        sp = plan["splits"].get(d, {}).get(k)
                        if not sp or abs(sum(sp) - 100) > 1e-9 or min(sp) < 0 or sp[SI[k[0]]] < 100 * C["OWN_MIN"] - 1e-9:
                            err.append(f"split {k} invalid"); ok = False; continue
                        for i in range(3): stats[i] += mods[k][1] * sp[i] / 100
                if ok:
                    tot = sum(stats)
                    if any(x / tot < C["BAND"][0] - 1e-9 or x / tot > C["BAND"][1] + 1e-9 for x in stats):
                        err.append("build outside the 25-50% band"); ok = False
            ps = stats[0] / sum(stats) if ok else None
            win = pack(skill, r, T, d, ps) if ok else None
            net, debt = take(C["PAY"][C["KIND"][j]] * C["PAY_MULT"][rnd], debt); cash += net
            buy("post")
            xpw = C["STORY_XP"][rnd][j] + C["CATCHUP"]["k"] * C["CATCHUP"]["share"][j] * short
            lostW = assign(plan["pickW"].get(rid), xpw, "Win")
            ran += 1
            rows.append(dict(id=rid, skill=round(skill, 6), points=round(p, 4), r=round(r, 6), ps=None if ps is None else round(ps, 6),
                             win=win, cash=round(cash, 2), debt=round(debt, 2), xpw=round(xpw, 4), lostG=round(lostG, 4),
                             lostW=round(lostW, 4), mods={k: [v[0], round(v[1], 4)] for k, v in sorted(mods.items())}, errors=err))
    return rows


def error_script():
    """Second, small check of the validation paths: a bad base in Street, a bad split in Wangan, a band break in Touge."""
    p = script()
    p["base"] = dict(p["base"], street=[1600, 700, 700])
    p["splits"] = {**p["splits"], "wangan": dict(p["splits"]["wangan"], H1=[50, 50, 0])}
    p["splits"] = {**p["splits"], "touge": {k: [100, 0, 0] if k[0] == "P" else ([0, 100, 0] if k[0] == "H" else [0, 0, 100]) for k in p["splits"]["touge"]}}
    p["base"]["touge"] = [750, 750, 1500]
    return p


def script():
    """One scripted playthrough: sensible base/splits, the study's mixed-style grinds, buys on time, a fixed XP pick list,
    plus deliberate mistakes (an unaffordable buy, an unassigned win XP, a bad split, a duplicate buy) to test validation."""
    base = {"street": [1250, 875, 875], "wangan": [900, 900, 1200], "touge": [1200, 950, 850]}
    splits = {"street": {"P1": [100, 0, 0], "P2": [100, 0, 0], "H1": [40, 60, 0], "E1": [40, 0, 60]},
              "wangan": {"P1": [60, 0, 40], "H1": [0, 60, 40], "E1": [0, 0, 100], "E2": [0, 0, 100]},
              "touge": {"P1": [100, 0, 0], "H1": [20, 60, 20], "E1": [30, 0, 70], "E2": [30, 0, 70]}}
    grinds = {"R1 mat1": 3, "R1 boss": 10, "R2 kid1": 7, "R2 boss": 6, "R3 mat1": 5, "R3 boss": 7}
    buys = [dict(at="R1 kid1", phase="pre", key="P1"),                    # unaffordable ($0 on arrival)
            dict(at="R1 kid1", phase="post", key="P1"), dict(at="R1 kid1", phase="post", key="P2"),
            dict(at="R1 kid2", phase="post", key="H1"), dict(at="R1 kid2", phase="post", key="E1"),
            dict(at="R1 kid2", phase="post", key="E1"),                   # duplicate
            dict(at="R2 kid1", phase="pre", key="P1"), dict(at="R2 kid1", phase="pre", key="H1"),
            dict(at="R2 kid1", phase="pre", key="E1"), dict(at="R2 kid1", phase="pre", key="E2"),
            dict(at="R3 kid1", phase="pre", key="P1"), dict(at="R3 kid1", phase="pre", key="H1"),
            dict(at="R3 kid1", phase="pre", key="E1"), dict(at="R3 kid1", phase="pre", key="E2")]
    order = {"street": ["P1", "P2", "H1", "E1"], "wangan": ["E2", "E1", "P1", "H1"], "touge": ["P1", "E1", "H1", "E2"]}
    pickG, pickW = {}, {}
    for rnd, d in enumerate(C["ROUNDS"]):
        for j, rung in enumerate(C["RUNGS"]):
            rid = f"R{rnd + 1} {rung}"; o = order[d]
            pickW[rid] = o[j % 4]
            if grinds.get(rid): pickG[rid] = o[(j + 1) % 4]
    del pickW["R1 oh1"]                                                   # unassigned win XP
    return dict(base=base, splits=splits, grinds=grinds, buys=buys, pickG=pickG, pickW=pickW)


if __name__ == "__main__":
    plan = script()
    json.dump(plan, open(os.path.join(HERE, "script.json"), "w"), indent=1)
    rows = simulate(plan); eplan = error_script(); erows = simulate(eplan)
    json.dump(eplan, open(os.path.join(HERE, "script_errors.json"), "w"), indent=1)
    json.dump(dict(main=rows, errors=erows), open(os.path.join(HERE, "py_reference.json"), "w"), indent=1)
    print("error plan:", sorted({e for x in erows for e in x["errors"]}))
    for x in rows:
        print(x["id"], round(x["skill"], 3), x["points"], round(x["r"], 4), x["win"], x["cash"], x["debt"], x["lostG"], x["lostW"], x["errors"])
