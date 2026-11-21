"""
Experience gauntlet: Austin's experience goals (design/07-economy-and-mods.md top, E.MS_TARGETS) checked on the LIVE sim with
no pins: live AI timing (N(OPPONENT_QTE, OPPONENT_QTE_SD) per turn), live player heat (HEAT_RELEASE), live crew stats
(MS_CREW_BUDGET), floors (MS_FLOOR_POINTS), round caps and max builds. Replaces the retired balance_gauntlet.py (Austin
2026-11-20 11:41 AM: "Yeah let's retire it and come up with a new gauntlet based on the experience goals.").

Cells per district (Street, Wangan, Touge), each through mod_skill.crew_config on the district's hardest live track, 3 boss
styles x n/3 seeds (96,000,000 + style x 100,000 + k, the same seeds as scripts/mod_skill_climb.py, so at the default n the
Street/Wangan cells reproduce config/mod_skill_climb_v1.json exactly; Touge is per-phase since the Touge passing go-live
2026-11-20, so its cells reproduce unapproved/barry/touge-passing-v1 variant I instead), ties count half:
  strong 80/80 at the floor, every rung      -> G1a (boss band), G1b, G3a, G3c, G4a
  weak 60/60 at the max build, every rung    -> G2a, G2b, G3b
  weak 60/60 at the floor, boss              -> G4b
  strong 80/80 at the max build, boss        -> G5 (+ E.MS_G5_ACCEPTED_MISS per district)
Every threshold comes from equations.py (MS_TARGETS, MS_BOSS_BAND, MS_G5_ACCEPTED_MISS). G1b and G2b are journey measures in the
design; until a live journey runner exists they are checked by the closed-form proxies below (labelled "proxy"):
  G1b proxy: expected story losses per round for the strong player challenging each rung at its floor = sum_j (1 - p_j) / p_j
  G2b proxy: expected attempts per round for the weak player at the max build = sum_j 1 / p_j over the 7 story races
             + the round's required wild encounters (MS_REQUIRED_WILDS) counted as one attempt each
Feel (report only, no targets set): turns starting with a locked gauge, limp clashes, mean lock length, races that hit all
three locked, at kid1 / oh1 / boss for the strong (floor) and weak (max) player, from the same races.

Standard error of a cell at win rate p: sqrt(p (1 - p) / n). Default n = 6000: 0.61 pp at the boss band (p ~ 0.67), 0.24 pp at
p ~ 0.96, <= 0.65 pp anywhere, against a 2 pp boss band and 3.0 pp ladder steps. --n 1200 (smoke) gives 1.36 pp.

Usage: python3 scripts/experience_gauntlet.py [--n 6000] [--workers N] [--json out.json]. Exit code 1 if any check fails.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from velocity_shift import equations as E, mod_skill as M      # noqa: E402
from velocity_shift.simulation import SimulationRunner           # noqa: E402

SEED = 96_000_000
STRONG, WEAK = 0.8, 0.6
FEEL_RUNGS = (0, 4, 6)                                           # kid1, oh1, boss


def max_build() -> dict:
    """Max build per rung: stock + earned on the mandatory path + the capped non-mandatory XP, inside the round cap."""
    out, e = {}, E.MS_STOCK_POINTS
    for rnd, d in enumerate(M.DISTRICTS):
        fl = E.MS_FLOOR_POINTS[d]
        row = tuple(min(E.MS_ROUND_CAP_POINTS[rnd], e + (f - fl[0]) + E.MS_NM_XP_CAP * E.MS_WILD_XP[rnd]) for f in fl)
        out[d] = row; e = row[-1]
    return out


def _feel(tr) -> tuple:
    L = [t.player_locked for t in tr]; runs, run = [], [0, 0, 0]
    for lk in L:
        for i in range(3):
            if lk[i]: run[i] += 1
            elif run[i]: runs.append(run[i]); run[i] = 0
    runs += [x for x in run if x]
    start = sum(any(L[i - 1]) for i in range(1, len(L)))
    limp = sum(x for t in tr for x in t.player_limp)
    return start, len(L), limp, 3 * len(L), runs, any(all(x) for x in L)


def job(t):
    rnd, j, q, which, si, k0, k1 = t; d = M.DISTRICTS[rnd]
    pts = E.MS_FLOOR_POINTS[d][j] if which == "floor" else max_build()[d][j]
    w = 0.0; f = [0, 0, 0, 0, [], 0]; want_feel = j in FEEL_RUNGS
    for k in range(k0, k1):
        m = SimulationRunner(M.crew_config(rnd, j, pts, seed=SEED + si * 100_000 + k, player_read=q, player_timing=q,
                                           player_pacing=q, boss_style=E.BOSS_STYLES[si])).run().match
        x, y = m.player_total_progress, m.opponent_total_progress
        w += 1.0 if x > y else 0.5 if x == y else 0.0
        if want_feel:
            s, T, l, C, r, a = _feel(m.turn_results)
            f[0] += s; f[1] += T; f[2] += l; f[3] += C; f[4] += r; f[5] += a
    return (rnd, j, q, which), w, k1 - k0, f


def run(n: int, workers: int, districts=None) -> dict:
    per = n // len(E.BOSS_STYLES); chunk = 500
    cells = []
    for rnd, d in enumerate(M.DISTRICTS):
        if districts and d not in districts: continue
        for j in range(7):
            cells += [(rnd, j, STRONG, "floor"), (rnd, j, WEAK, "max")]
        cells += [(rnd, 6, WEAK, "floor"), (rnd, 6, STRONG, "max")]
    J = [(*c, si, k0, min(per, k0 + chunk)) for c in cells for si in range(len(E.BOSS_STYLES)) for k0 in range(0, per, chunk)]
    J.sort(key=lambda t: -E.LADDER_TURNS[t[1]])                  # long races first
    with Pool(workers) as p: R = p.map(job, J, chunksize=1)
    acc = {}
    for key, w, m, f in R:
        a = acc.setdefault(key, [0.0, 0, [0, 0, 0, 0, [], 0]]); a[0] += w; a[1] += m
        for i in range(6): a[2][i] += f[i]
    return acc


def evaluate(acc: dict) -> tuple[dict, list]:
    T = E.MS_TARGETS; res, fails = {}, []
    for rnd, d in enumerate(M.DISTRICTS):
        if (rnd, 6, STRONG, "floor") not in acc: continue
        pct = lambda j, q, w: 100.0 * acc[(rnd, j, q, w)][0] / acc[(rnd, j, q, w)][1]
        sf = [pct(j, STRONG, "floor") for j in range(7)]; wm = [pct(j, WEAK, "max") for j in range(7)]
        bwf, bsm = pct(6, WEAK, "floor"), pct(6, STRONG, "max")
        steps = [a - b for a, b in zip(sf, sf[1:])]
        lo, hi = E.MS_BOSS_BAND; g1 = T["G1a_boss_strong_floor"]
        g1b = sum((100 - p) / p for p in sf)
        g2b = sum(100 / p for p in wm) + sum(E.MS_REQUIRED_WILDS)
        g5 = T["G5_boss_strong_max_build"] + E.MS_G5_ACCEPTED_MISS.get(d, 0.0)
        checks = [
            ("G1a boss strong at floor", sf[6], f"{max(lo, g1[0])}-{min(hi, g1[1])}", max(lo, g1[0]) <= sf[6] <= min(hi, g1[1])),
            ("G1b story losses/round (proxy)", g1b, f"{T['G1b_story_losses_strong'][0]}-{T['G1b_story_losses_strong'][1]}",
             T["G1b_story_losses_strong"][0] <= g1b <= T["G1b_story_losses_strong"][1]),
            ("G2a min weak at max", min(wm), f">= {T['G2a_min_weak_max_build']}", min(wm) >= T["G2a_min_weak_max_build"]),
            ("G2b attempts/round (proxy)", g2b, f"<= {T['G2b_weak_improving_attempts']}", g2b <= T["G2b_weak_improving_attempts"]),
            ("G3a drop kid1 -> boss", sf[0] - sf[6], f">= {T['G3a_drop_kid1_boss']}", sf[0] - sf[6] >= T["G3a_drop_kid1_boss"]),
            ("G3b boss read gap", sf[6] - wm[6], f">= {T['G3b_boss_read_gap']}", sf[6] - wm[6] >= T["G3b_boss_read_gap"]),
            ("G3c smallest step", min(steps), f">= {T['G3c_min_step']}", min(steps) >= T["G3c_min_step"]),
            ("G4a lowest strong at floor", min(sf), f">= {T['G4a_min_strong_floor']}", min(sf) >= T["G4a_min_strong_floor"]),
            ("G4b boss weak at floor", bwf, f"<= {T['G4b_boss_weak_floor_max']}", bwf <= T["G4b_boss_weak_floor_max"]),
            ("G5 boss strong at max", bsm, f"<= {g5:g}" + (" (accepted miss)" if d in E.MS_G5_ACCEPTED_MISS else ""), bsm <= g5),
        ]
        feel = {}
        for j in FEEL_RUNGS:
            for q, w, lab in ((STRONG, "floor", "strong"), (WEAK, "max", "weak")):
                s, Tn, l, C, r, a = acc[(rnd, j, q, w)][2]; n = acc[(rnd, j, q, w)][1]
                feel[f"{M.RUNGS[j]} {lab}"] = dict(turns_starting_locked_pct=round(100 * s / max(1, Tn - n), 1), limp_pct=round(100 * l / C, 1),
                                                    mean_lock_turns=round(sum(r) / max(1, len(r)), 2), races_all_locked_pct=round(100 * a / n, 1))
        res[d] = dict(strong_floor=[round(x, 2) for x in sf], weak_max=[round(x, 2) for x in wm], boss_weak_floor=round(bwf, 2),
                      boss_strong_max=round(bsm, 2), checks=[(c, round(v, 2), t, ok) for c, v, t, ok in checks], feel=feel,
                      n=acc[(rnd, 6, STRONG, "floor")][1])
        fails += [f"{d}: {c} = {v:.2f} (target {t})" for c, v, t, ok in checks if not ok]
    return res, fails


def report(res: dict, fails: list, n: int) -> None:
    se = 100 * math.sqrt(0.67 * 0.33 / n)
    print(f"Experience gauntlet (live sim, no pins), n = {n} per cell, SE at the boss band {se:.2f} pp")
    ds = list(res)
    print(f"{'check':34s}" + "".join(f"{d:>22s}" for d in ds))
    for i, (c, _, t, _) in enumerate(res[ds[0]]["checks"]):
        row = f"{c:34s}"
        for d in ds:
            _, v, t, ok = res[d]["checks"][i]; row += f"{('%.2f ' % v) + ('pass' if ok else 'FAIL'):>22s}"
        print(row + f"   target {res[ds[0]]['checks'][i][2]}" + ("" if all(res[d]["checks"][i][2] == res[ds[0]]["checks"][i][2] for d in ds) else
                                                              " (" + ", ".join(f"{d} {res[d]['checks'][i][2]}" for d in ds) + ")"))
    for d in ds:
        print(f"{d}: strong at floor {res[d]['strong_floor']} | weak at max {res[d]['weak_max']}")
    print("\nFeel (report only; no targets set): turns starting locked % / limp % / mean lock turns / races all-locked %")
    for d in ds:
        print(f"  {d}: " + " | ".join(f"{k} {v['turns_starting_locked_pct']}/{v['limp_pct']}/{v['mean_lock_turns']}/{v['races_all_locked_pct']}"
                                       for k, v in res[d]["feel"].items()))
    print("\nFAIL:\n  " + "\n  ".join(fails) if fails else "\nALL EXPERIENCE CHECKS PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--n", type=int, default=6000, help="races per cell (3 boss styles x n/3)")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--json", default=None)
    ap.add_argument("--district", action="append", default=None, help="limit to a district (repeatable)")
    a = ap.parse_args()
    res, fails = evaluate(run(a.n, a.workers, a.district))
    report(res, fails, a.n - a.n % len(E.BOSS_STYLES))
    if a.json:
        json.dump(dict(n=a.n, seed=SEED, results=res, fails=fails), open(a.json, "w"), indent=1)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
