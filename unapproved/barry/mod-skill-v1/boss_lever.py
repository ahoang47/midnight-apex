"""BOSS 65-70 % LEVERS (Barry, 2026-11-19, Austin: "Think we can get a strong story player to 65-70%?"). Engine n = 6000 per
cell, climb_grid protocol (hard track, 3 boss styles, ties half, district tune, opponent 300 units, encounter "boss").
Target: 80/80 boss at the floor = 66 % (inside 65-70; 66 not 67.5 so the boss stays <= oh2 + 1 for G3a with oh2 unchanged:
Street oh2 66.2). Recommended setup S1 M13r cap 15: old boss floors 3346 / 3865 / 4424, boss budgets 332.58 / 390.35 / 437.06,
Street boss kappa x0.5.
  (b) raise the boss floor (story XP in the oh2 -> boss gap); boss budget and max build unchanged
  (a) lower the boss budget at the old floor (same floor r as (b)), then read the full build
  (c) soften the boss AI QTE (MatchConfig.opponent_qte_ratio) at the old floor, then read the full build
-> boss_lever.json"""
import json, os
from multiprocessing import Pool
import climb_grid as CG
from climb_grid import E, C, CombatantStats, MatchConfig, SimulationRunner
HERE = os.path.dirname(os.path.abspath(__file__))
N = 6000; T = 66.0; SEED = 98_000_000
D = ("street", "wangan", "touge"); KS = (0.5, 1.0, 1.0)
FLOOR = (3346, 3865, 4424); CAPP = (3532, 4044, 4628); BUD = (332.58, 390.35, 437.06)


def cell(i, q, r, ratio=None, n=N, seed=SEED):
    d = D[i]; E.KAPPA_BY_LENGTH.clear(); E.KAPPA_BY_LENGTH.update({k: v * KS[i] for k, v in CG.KAPPA0.items()})
    sp, sh, se = E.DISTRICT_TUNE[d]; bp, bh, be = E.BOSS_STAT_SHARES[d]; tot = 300.0 * r; w = 0.0; m = 0
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(n // 3):
            cfg = MatchConfig(player_stats=CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50),
                              opponent_stats=CombatantStats(name="Opponent", pow=300 * bp, en=300 * be, han=300 * bh, level=50),
                              max_turns=30, seed=seed + si * 100_000 + k, district=d,
                              corners=list(C.official_tracks()[d][E.BOSS_HARD_TRACK[d]]), player_read=q, player_timing=q,
                              player_pacing=q, boss_style=st, encounter_type="boss", opponent_qte_ratio=ratio)
            mm = SimulationRunner(cfg).run().match; x, y = mm.player_total_progress, mm.opponent_total_progress
            w += 1.0 if x > y else 0.5 if x == y else 0.0; m += 1
    return round(100 * w / m, 2)


def search(f, lo, hi, steps=8):
    """f increasing; bisection for f = T, stop within +-0.75"""
    tr = []
    for _ in range(steps):
        mid = (lo + hi) / 2; v = f(mid); tr.append((round(mid, 5), v))
        if abs(v - T) <= 0.75: return mid, v, tr
        lo, hi = (mid, hi) if v < T else (lo, mid)
    return mid, v, tr


def lever_b(i):
    r0 = FLOOR[i] / 10 / BUD[i]
    r, v, tr = search(lambda r: cell(i, 0.8, r), r0, CAPP[i] / 10 / BUD[i])
    pts = round(r * 10 * BUD[i]); r = pts / 10 / BUD[i]
    return dict(lever="b", d=D[i], floor_new=pts, delta=pts - FLOOR[i], r_floor=round(r, 4), w8080_floor=cell(i, 0.8, r),
                w6060_floor=cell(i, 0.6, r), full_r=round(CAPP[i] / 10 / BUD[i], 4), w8080_full=cell(i, 0.8, CAPP[i] / 10 / BUD[i]),
                w6060_full=cell(i, 0.6, CAPP[i] / 10 / BUD[i]), trace=tr)


def lever_a(i, r_floor):
    bud = round(FLOOR[i] / 10 / r_floor, 2); rf = CAPP[i] / 10 / bud
    return dict(lever="a", d=D[i], budget_new=bud, budget_old=BUD[i], r_floor=round(FLOOR[i] / 10 / bud, 4), full_r=round(rf, 4),
                w8080_full=cell(i, 0.8, rf), w6060_full=cell(i, 0.6, rf))


def lever_c(i):
    r0 = FLOOR[i] / 10 / BUD[i]
    x, v, tr = search(lambda x: cell(i, 0.8, r0, ratio=x), 1.0, 0.70)   # lower ratio -> sloppier boss -> f rises
    rf = CAPP[i] / 10 / BUD[i]
    return dict(lever="c", d=D[i], ai_qte_ratio=round(x, 4), ai_qte_mean=round(0.8 * x, 4), w8080_floor=v,
                w6060_floor=cell(i, 0.6, r0, ratio=x), w8080_full=cell(i, 0.8, rf, ratio=x), w6060_full=cell(i, 0.6, rf, ratio=x), trace=tr)


def job(t):
    kind, i = t
    return lever_b(i) if kind == "b" else lever_c(i)


if __name__ == "__main__":
    with Pool(6) as p:
        res = p.map(job, [("b", i) for i in range(3)] + [("c", i) for i in range(3)], chunksize=1)
        b = [x for x in res if x["lever"] == "b"]
        a = p.starmap(lever_a, [(i, b[i]["r_floor"]) for i in range(3)])
    out = dict(target=T, n=N, b=b, a=a, c=[x for x in res if x["lever"] == "c"])
    json.dump(out, open(os.path.join(HERE, "boss_lever.json"), "w"), indent=1)
    for k in ("b", "a", "c"):
        for x in out[k]: print(k, x)
