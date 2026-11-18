"""Run 3: gym structure sweep (table model; tier stock A). Per round: 2 opening road races (today's kid1/kid2), then k crews of
2 lieutenants (20 turns) + a crew boss (30 turns), with m mandatory road races (10 turns) before each crew after the first.
The last crew boss is the round boss. Optional grinds exist but are NOT used here.
Opponent r targets (all [PH] except the existing rungs): opening roads = kid1/kid2 targets; mid-round roads = kid2 target;
crew c's lieutenants = linear between the mat1 and oh2 targets by crew position; crew c boss = linear between oh2 and the
round-boss target, reaching the boss target at crew k. Budget B = C_ROUND / target (planner rule).
Car XP per win, per race type = today's mod_skill story XP means [sim]: road = mean(kid1, kid2), lieutenant = mean(mat1..oh2),
crew boss = the round's boss XP. 'landing' = pre-boss XP / tier room. 'scaled' rescales every race's XP so the car reaches the cap
exactly at the round boss. Win % = live tables (shown cell; reading curve rises 0.6 -> 0.8 over the round's races).
Expected attempts per mandatory race = 100 / win % (a loss blocks; retry until a win; losses give no XP [PH]).
Spirit + driver tree: adds run2's measured mean (driver + spirit mult) delta by race type and profile (mixed walk) if run2.json exists.
--matched: every opponent budget is set from the car's expected power on the no-grind curve (B_i = P_i / target_i), so an
on-curve car meets each race at its target r; every crew boss is a 30-turn race at the round-boss target [PH]. -> run3.json / run3_matched.json"""
import json, os
from common import CN, ROUNDS, TURNS, TUNE, win, HERE

STOCK = [3000, 3532, 4044]; CAPPTS = [3532, 4044, 4628]
TR = CN["TARGET_R"]; SX = CN["STORY_XP"]
import sys
MATCHED = "--matched" in sys.argv   # budgets set from the car's expected (no-grind, scaled-XP) power: B_i = P_i / target_i [PH]
D2 = None
if os.path.exists(os.path.join(HERE, "run2.json")):
    rows = json.load(open(os.path.join(HERE, "run2.json")))["rows"]; D2 = {}
    for x in rows:
        if x["mode"] != "mixed":
            continue
        typ = "road" if x["j"] < 2 else "boss" if x["j"] == 6 else "lt"
        D2.setdefault((x["rnd"], typ, x["prof"]), []).append(x["mult"]["win"] - x["none"])
    D2 = {k: sum(v) / len(v) for k, v in D2.items()}


def layout(rnd, k, m):
    d = ROUNDS[rnd]; t = TR[d]; out = [("road", 10, t[0]), ("road", 10, t[1])]
    for c in range(1, k + 1):
        if c > 1:
            out += [("road", 10, t[1])] * m
        f = (c - 1) / (k - 1) if k > 1 else 1.0
        lt = t[2] + (t[5] - t[2]) * f
        out += [("lt", 20, lt), ("lt", 20, lt)]
        out.append(("boss", 30, t[6] if MATCHED else t[5] + (t[6] - t[5]) * (c / k)))
    return out


def xp_of(rnd, typ):
    s = SX[rnd]
    return {"road": (s[0] + s[1]) / 2, "lt": sum(s[2:6]) / 4, "boss": s[6]}[typ]


def round_eval(rnd, k, m, scaled):
    d = ROUNDS[rnd]; lay = layout(rnd, k, m); n = len(lay)
    xps = [xp_of(rnd, typ) for typ, _, _ in lay]
    room = CAPPTS[rnd] - STOCK[rnd]; pre = sum(xps[:-1])
    if scaled:
        xps = [x * room / pre for x in xps]
    pts = STOCK[rnd]; rows = []
    for i, ((typ, T, tgt), xp) in enumerate(zip(lay, xps)):
        r = tgt if MATCHED else min(CN["CAP_POWER"][rnd], pts / 10) / (CN["C_ROUND"][rnd] / tgt); s = 0.6 + 0.2 * i / (n - 1)
        w = {p: win(p, r, T, d, TUNE[d][0], s) for p in ("c6060", "c8080", "curve")}
        if D2:
            w.update({p + "+sd": min(100.0, max(0.0, w[p] + D2[(rnd + 1, typ, p)])) for p in ("c6060", "c8080", "curve")})
        rows.append(dict(typ=typ, T=T, target=round(tgt, 4), pts=round(pts, 1), r=round(r, 4), **{kk: round(v, 1) for kk, v in w.items()}))
        pts = min(CAPPTS[rnd], pts + xp)
    return dict(n=n, landing=round(pre / room, 3), rows=rows)


def att(rows, key):
    a = [100.0 / max(x[key], 0.1) for x in rows]
    return dict(per_race_mean=round(sum(a) / len(a), 2), per_race_max=round(max(a), 1), round_total=round(sum(a), 1))


out = {}
for k in (1, 2, 3, 4):
    for m in (1, 2, 3, 4):
        if k == 1 and m > 1:
            continue
        key = f"k{k} m{m}"; out[key] = {}
        for scaled in (False, True):
            for rnd in range(3):
                ev = round_eval(rnd, k, m, scaled)
                ev["attempts"] = {p: att(ev["rows"], p) for p in ev["rows"][0] if p.startswith("c") or p.startswith("curve")}
                ev["boss"] = {p: ev["rows"][-1][p] for p in ev["rows"][-1] if p.startswith("c")}
                out[key][f"{'scaled' if scaled else 'today_xp'} R{rnd + 1}"] = ev
json.dump(out, open(os.path.join(HERE, "run3_matched.json" if MATCHED else "run3.json"), "w"), indent=1)
print("config | races/round | landing R1/R2/R3 (today XP) | scaled: 60/60 attempts per race mean (max) and per round, R1/R2/R3 | boss 60/60 / 80/80")
for key, v in out.items():
    L = [v[f"today_xp R{i}"]["landing"] for i in (1, 2, 3)]
    sc = [v[f"scaled R{i}"] for i in (1, 2, 3)]
    sk = "c6060+sd" if D2 else "c6060"
    a = " / ".join(f"{e['attempts'][sk]['per_race_mean']} ({e['attempts'][sk]['per_race_max']}) {e['attempts'][sk]['round_total']}" for e in sc)
    b = " / ".join(f"{e['boss'].get('c6060+sd', e['boss']['c6060'])}/{e['boss'].get('c8080+sd', e['boss']['c8080'])}" for e in sc)
    print(f"{key} | {sc[0]['n']} | {L} | {a} | {b}")
