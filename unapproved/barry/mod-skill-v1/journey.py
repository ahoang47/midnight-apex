"""PLAYER JOURNEY (Barry, 2026-11-19, Austin direct): one round, R1 Street, Monte Carlo over M players on journey_grid.json
(engine win %, bilinear in skill q and r). Skill curve: q(a) = min(Q1, Q0 + (Q1 - Q0) * a / A), a = race attempts made so far
in the round (wins and losses; every attempt is practice). Losses are free retries (retry fee 0).
Run 1: mandatory only, 7 story + 13 required wild encounters (2 before kid2..oh2, 3 before the boss).
Run 2: mandatory + non-mandatory races (substory / picked fight; modelled as a 10-turn race at the kid1 budget paying a
wild encounter's XP 13 and $550). Policy: before each story race, race non-mandatory until the story race's win chance is
>= GOAL, or the non-mandatory XP cap (NM_CAP XP-paying wins per round) or the round cap (3,532) is reached.
Floors (climb_floor.py): earned points on arrival on the mandatory path. -> journey.json"""
import json, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, "journey_grid.json")))
TAB = {}
for lv, q, r, w in G["cells"]:
    TAB[(lv, q, r)] = w / 100.0
QS = G["q"]; RS = G["r"]
CAP0, CAP1 = 3000, 3532; WE_XP = 13; WE_CASH = 550.0
FLOOR = dict(kid1=3000, kid2=3055, mat1=3110, mat2=3165, oh1=3220, oh2=3275, boss=3346)
BUD = dict(kid1=293.98, kid2=306.16, mat1=309.14, mat2=317.38, oh1=325.1, oh2=332.93, boss=332.58, we=293.98)
LVL = dict(kid1="r10", kid2="r10", mat1="r20", mat2="r20", oh1="r20", oh2="r20", boss="boss", we="r10")
SXP = dict(kid1=29, kid2=29, mat1=29, mat2=29, oh1=29, oh2=32, boss=0)
CASH = dict(kid1=1000.0, kid2=1000.0, mat1=2500.0, mat2=2500.0, oh1=2500.0, oh2=2500.0, boss=8000.0)
SEQ = ["kid1", "we", "we", "kid2", "we", "we", "mat1", "we", "we", "mat2", "we", "we", "oh1", "we", "we", "oh2", "we", "we", "we", "boss"]


def interp(xs, x):
    x = min(max(x, xs[0]), xs[-1])
    for k in range(len(xs) - 1):
        if x <= xs[k + 1] + 1e-12:
            t = (x - xs[k]) / (xs[k + 1] - xs[k]); return k, t
    return len(xs) - 2, 1.0


def p(kind, q, pts):
    lv = LVL[kind]; r = pts / 10 / BUD[kind]; rs = RS[lv]
    i, a = interp(QS, q); j, b = interp(rs, r)
    f = lambda qi, rj: TAB[(lv, QS[qi], rs[rj])]
    return (1 - a) * ((1 - b) * f(i, j) + b * f(i, j + 1)) + a * ((1 - b) * f(i + 1, j) + b * f(i + 1, j + 1))


def journey(run, Q0, Q1, A, M=20000, NM_CAP=15, GOAL=0.5, seed=7, seq=None, sxp=None, floor=None):
    SEQ_ = seq or SEQ; SXP_ = sxp or SXP; FLOOR_ = floor or FLOOR
    rng = random.Random(seed); q = lambda a: min(Q1, Q0 + (Q1 - Q0) * a / A)
    rows = [dict(slot=i + 1, race=k, q=0.0, pts=0.0, p=0.0, att=0.0, nm_wins=0.0, nm_att=0.0, cash=0.0, max_att=0) for i, k in enumerate(SEQ_)]
    tot = dict(att=0.0, nm_wins=0.0, stuck=0)
    for _ in range(M):
        a = 0; pts = CAP0; cash = 0.0; nmw = 0
        for i, k in enumerate(SEQ_):
            row = rows[i]; nma = 0; nmw0 = nmw
            if run == 2 and k != "we":
                while p(k, q(a), pts) < GOAL and nmw < NM_CAP and pts < CAP1:
                    while True:
                        a += 1; nma += 1
                        if rng.random() < p("we", q(a - 1), pts): break
                    nmw += 1; pts = min(CAP1, pts + WE_XP); cash += WE_CASH
            row["nm_wins"] += nmw - nmw0; row["nm_att"] += nma
            row["q"] += q(a); row["pts"] += pts; pk = p(k, q(a), pts); row["p"] += pk; n = 0
            while True:
                n += 1; a += 1
                if rng.random() < p(k, q(a - 1), pts) or n >= 400: break
            if n >= 400: tot["stuck"] += 1
            row["att"] += n; row["max_att"] = max(row["max_att"], n)
            pts = min(CAP1, pts + (WE_XP if k == "we" else SXP_[k])); cash += WE_CASH if k == "we" else CASH[k]; row["cash"] += cash
        tot["att"] += a; tot["nm_wins"] += nmw
    for row in rows:
        for key in ("q", "pts", "p", "att", "nm_wins", "nm_att", "cash"):
            row[key] = round(row[key] / M, 4 if key in ("q", "p") else 2)
        row["floor"] = FLOOR_.get(row["race"])
    return dict(run=run, Q0=Q0, Q1=Q1, A=A, M=M, NM_CAP=NM_CAP, GOAL=GOAL, rows=rows,
                attempts=round(tot["att"] / M, 2), nm_wins=round(tot["nm_wins"] / M, 2), stuck=tot["stuck"])


if __name__ == "__main__":
    out = []
    for Q0 in (0.50, 0.60):
        for run in (1, 2):
            out.append(journey(run, Q0, 0.80, 40))
    out.append(journey(2, 0.50, 0.80, 40, NM_CAP=10)); out.append(journey(2, 0.50, 0.80, 40, GOAL=0.7))
    # fixed-skill references for the cap check: boss win chance at the cap
    ref = {f"boss_q{q}_pts{pt}": round(100 * p("boss", q, pt), 1) for q in (0.6, 0.8) for pt in (3346, 3532)}
    json.dump(dict(runs=out, ref=ref), open(os.path.join(HERE, "journey.json"), "w"), indent=1)
    print(ref)
    for o in out:
        print("RUN", o["run"], "Q0", o["Q0"], "cap", o["NM_CAP"], "goal", o["GOAL"], "attempts", o["attempts"], "nm_wins", o["nm_wins"], "stuck", o["stuck"])
        for r in o["rows"]:
            print("   %2d %-4s q %.3f pts %7.1f floor %5s p1 %5.1f att %5.2f nm %5.2f/%5.2f cash %8.0f max %d" % (r["slot"], r["race"], r["q"], r["pts"], r["floor"], 100 * r["p"], r["att"], r["nm_wins"], r["nm_att"], r["cash"], r["max_att"]))
