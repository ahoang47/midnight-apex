"""CLIMB draft evaluation (Barry, 2026-11-19). Reads climb_grid.json (engine grid). NOT live.
Expected build ("mandatory path", design input): over the round's 20 mandatory races the car's points rise linearly from the
round entry to cap_{r-1} + F x room_r at the boss (F = 0.65 of the round's mod XP), entry = cap_{r-1} - (1 - F) x room_{r-1}.
Story rungs sit at mandatory-race slots 1, 4, 7, 10, 13, 16, 20 (2 wild-encounter beats before each later rung, 3 before the boss).
Full build = the round cap (all mods maxed; needs optional wild encounters on top of the 20).
Per variant: each non-boss rung's budget is set so the expected build's 80/80 win % hits a falling target (the climb); the boss
is set to the expected-build 80/80 closest to BOSS_T (50) among boss r that keep full-build 80/80 <= 95 and full-build 60/60 >= 30. -> climb_eval.json"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "sim"))
from velocity_shift import equations as E

G = json.load(open(os.path.join(HERE, "climb_grid.json")))
F = float(os.environ.get("F", "0.65"))
CAP = (3000.0, 3532.0, 4044.0, 4628.0); DIST = ("street", "wangan", "touge")
RUNGS = ("kid1", "kid2", "mat1", "mat2", "oh1", "oh2", "boss"); SLOT = (1, 4, 7, 10, 13, 16, 20)
TARGET = (95, 90, 84, 78, 70, 62)             # 80/80 win % at the expected build, kid1 .. oh2 (the climb)
BOSS_T = float(os.environ.get("BOSS_T", "50"))   # boss: 80/80 at the expected build, at most this (top of the climb)
LV = {"kid1": "kid", "kid2": "kid", "mat1": "mat", "mat2": "mat", "oh1": "oh", "oh2": "oh", "boss": "boss"}


def curve(var, d, lv, prof):
    if lv == "oh" and not G["variants"][var]["qte_rise"]:
        lv = "mat"
    pts = sorted((c["r"], c["win"]) for c in G["cells"] if c["var"] == var and c["d"] == d and c["lv"] == lv and c["prof"] == prof)
    run = []; m = -1
    for r, w in pts:                           # enforce monotone (noise) with a running max
        m = max(m, w); run.append((r, m))
    return run


def at(cv, r):
    if r <= cv[0][0]: return cv[0][1]
    if r >= cv[-1][0]: return cv[-1][1]
    for (r0, w0), (r1, w1) in zip(cv, cv[1:]):
        if r0 <= r <= r1:
            return w0 + (w1 - w0) * (r - r0) / (r1 - r0)


def inv(cv, w):
    """smallest r with win >= w (None if above the grid's top)."""
    if w <= cv[0][1]: return cv[0][0]
    for (r0, w0), (r1, w1) in zip(cv, cv[1:]):
        if w0 <= w <= w1 and w1 > w0:
            return r0 + (r1 - r0) * (w - w0) / (w1 - w0)
    return None


def points(i, f=F):
    room = [CAP[k + 1] - CAP[k] for k in range(3)]
    entry = CAP[i] - (1 - f) * room[i - 1] if i else CAP[0]
    boss = CAP[i] + f * room[i]
    return [entry + (boss - entry) * (s - 1) / 19 for s in SLOT], boss


res = dict(F=F, target_8080=TARGET, boss_target_8080=BOSS_T, variants={})
for var in G["variants"]:
    out = []
    for i, d in enumerate(DIST):
        pts, pb = points(i); rows = []
        for j, rung in enumerate(RUNGS[:-1]):
            c8, c6 = curve(var, d, LV[rung], "80/80"), curve(var, d, LV[rung], "60/60")
            r = inv(c8, TARGET[j]); clamp = r is None; r = r if r is not None else c8[-1][0]
            rf_j = r * CAP[i + 1] / pts[j]       # same opponent, car already maxed for the round (optional wins)
            rows.append(dict(rung=rung, points=round(pts[j]), r=round(r, 4), budget=round(pts[j] / 10 / r, 2),
                             live_budget=round(E.opponent_budget(i, j), 2), w8080=round(at(c8, r), 1), w6060=round(at(c6, r), 1), clamped=clamp,
                             full_r=round(rf_j, 4), full_6060=round(at(c6, rf_j), 1), full_r_off_grid=rf_j > G["r"][-1]))
        c8, c6 = curve(var, d, "boss", "80/80"), curve(var, d, "boss", "60/60"); full = CAP[i + 1] / 10
        cand = []
        for k in range(0, 2001):               # boss r at the expected build, scanned inside the grid so full r stays inside too
            re = 0.92 + 0.0001 * k; rf = re * full / (pb / 10)
            if rf > G["r"][-1]: break
            cand.append((re, rf, at(c8, re), at(c8, rf), at(c6, rf)))
        ok = [c for c in cand if c[3] <= 95.0 and c[4] >= 30.0]
        pool = ok or cand
        re, rf, b, f8, f6 = min(pool, key=lambda c: abs(c[2] - BOSS_T))
        r60 = re * (CAP[i] + 0.60 * (CAP[i + 1] - CAP[i])) / pb; r70 = re * (CAP[i] + 0.70 * (CAP[i + 1] - CAP[i])) / pb
        rows.append(dict(rung="boss", points=round(pb), r=round(re, 4), budget=round(pb / 10 / re, 2), live_budget=round(E.opponent_budget(i, 6), 2),
                         w8080=round(at(c8, re), 1), w6060=round(at(c6, re), 1), full_r=round(rf, 4), full_8080=round(f8, 1),
                         full_6060=round(f6, 1), w8080_at60pct=round(at(c8, r60), 1), w8080_at70pct=round(at(c8, r70), 1),
                         meets_pair=f8 <= 95.0 and f6 >= 30.0))
        out.append(dict(rnd=i + 1, district=d, rows=rows))
    res["variants"][var] = out
json.dump(res, open(os.path.join(HERE, "climb_eval.json"), "w"), indent=1)
for var, out in res["variants"].items():
    print("==", var)
    for o in out:
        print("  R%d" % o["rnd"], " | ".join("%s %.3f %s/%s%s" % (x["rung"], x["r"], x["w6060"], x["w8080"], "*" if x.get("clamped") else "") for x in o["rows"]),
              "|| full %s/%s r%.3f, 80/80 @60%%/70%% %s/%s pair_ok %s" % (o["rows"][-1]["full_6060"], o["rows"][-1]["full_8080"], o["rows"][-1]["full_r"], o["rows"][-1]["w8080_at60pct"], o["rows"][-1]["w8080_at70pct"], o["rows"][-1]["meets_pair"]))
