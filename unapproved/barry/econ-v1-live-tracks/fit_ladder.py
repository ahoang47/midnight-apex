"""Re-fit the per-rung target r (kid1..oh2) per round on the live-track oracle, boss r given. Draft.
Search: random monotone ladders (each rung in [boss r, 1.24], non-increasing kid1->boss) + local refinement;
per-round score from econ-v1 evaluate.walk_round (story / mixed / hard policies), criteria 2/3/4 per round."""
import json, os, sys, random, io, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

DIST = ("street", "wangan", "touge")


def round_eval(E, M, rnd, enter, p):
    out = {}
    for mode in ("story", "mixed", "hard"):
        L, bag, money, debt = enter[mode]
        out[mode] = E.walk_round(rnd, L, bag, money, debt, p, grind_mode=mode)
    return out


def score(w, rnd):
    """Penalty (0 = all per-round targets hit) + detail."""
    pen = 0.0; why = []
    m = w["mixed"]
    wall, post = m["wall_grind"], m["post_wall_to_cap"]
    if m["wall_name"] is None:
        pen += 30; why.append("no wall")
    else:
        if wall < 3: pen += 10 * (3 - wall); why.append(f"wall {wall}<3")
        if wall > 6: pen += 10 * (wall - 6); why.append(f"wall {wall}>6")
    if post > 10: pen += 10 * (post - 10); why.append(f"post {post}>10")
    if post < 8: pen += 2 * (8 - post); why.append(f"post {post}<8")
    # 80/80 story >=50 district and hard on every rung
    import evaluate as E
    for row in w["story"]["rows"]:
        pk = row["wr"]["c8080"]
        lo = min(pk["district"]["win"], E.hard_win(pk))
        if lo < 50:
            pen += 3 * (50 - lo); why.append(f"8080 {row['name']} {lo}")
    # 10-turn grind at the mixed wall
    for row in m["rows"]:
        if row["name"] == m["wall_name"]:
            for pr in ("c6080", "c8060"):
                if row["grind10"][pr] < 65:
                    pen += 2 * (65 - row["grind10"][pr]); why.append(f"g10 {pr} {row['grind10'][pr]}")
            if row["grind10"]["c6060"] < 40:
                pen += 2 * (40 - row["grind10"]["c6060"]); why.append(f"g10 6060 {row['grind10']['c6060']}")
    return pen, why


def fit_round(M, mods, rnd, boss_r, base, n_rand=4000, seed=1):
    E = mods["evaluate"]; d = DIST[rnd]
    p = M.EconParams()
    capL = M.CAP_L
    enter = {}
    for mode in ("story", "mixed", "hard"):
        L0 = 0 if rnd == 0 else capL[rnd - 1]
        enter[mode] = (L0, 0.0, 0.0, p.debt_amount if rnd == 0 else 0.0)
    rng = random.Random(seed)

    def ev(lad):
        M.LADDER_R_C[d] = tuple(lad) + (boss_r,)
        w = round_eval(E, M, rnd, enter, p)
        pen, why = score(w, rnd)
        change = sum(abs(a - b) for a, b in zip(lad, base[:6]))
        return pen, change, why, w

    best = None
    cands = [tuple(max(v, boss_r) for v in base[:6])]
    for _ in range(n_rand):
        v = sorted((round(rng.uniform(boss_r, 1.24), 3) for _ in range(6)), reverse=True)
        cands.append(tuple(v))
    for lad in cands:
        pen, ch, why, w = ev(lad)
        key = (round(pen, 3), ch)
        if best is None or key < best[0]:
            best = (key, lad, why)
    # local refine: +-0.002..0.01 coordinate moves keeping monotone
    lad = list(best[1]); improved = True
    while improved:
        improved = False
        for j in range(6):
            for dlt in (-0.01, -0.005, -0.002, 0.002, 0.005, 0.01):
                t = lad[:]; t[j] = round(t[j] + dlt, 3)
                if t[j] > 1.24 or t[j] < boss_r: continue
                if any(t[k] < t[k + 1] for k in range(5)) or t[5] < boss_r: continue
                pen, ch, why, w = ev(t)
                if (round(pen, 3), ch) < best[0]:
                    best = ((round(pen, 3), ch), tuple(t), why); lad = t; improved = True
    M.LADDER_R_C[d] = tuple(best[1]) + (boss_r,)
    return dict(district=d, ladder=list(best[1]) + [boss_r], pen=best[0][0], change=round(best[0][1], 3), why=best[2])


if __name__ == "__main__":
    boss = json.loads(os.environ.get("BOSS", '{"street":1.043,"wangan":1.040,"touge":1.069}'))
    lad0 = {d: tuple(core.LIVE_LADDER[d][:6]) + (boss[d],) for d in DIST}
    M, mods = core.setup(lad0)
    out = []
    for rnd in range(3):
        r = fit_round(M, mods, rnd, boss[DIST[rnd]], core.LIVE_LADDER[DIST[rnd]], n_rand=int(os.environ.get("NR", 3000)))
        print(r, flush=True); out.append(r)
    json.dump(dict(boss=boss, hard_touge=core.oracle.HARD_TOUGE, fits=out),
              open(os.path.join(core.HERE, os.environ.get("OUT", "fit_ladder.json")), "w"), indent=1)
