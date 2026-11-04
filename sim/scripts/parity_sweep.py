"""
Skill parity sweep — how play quality q and the stat gap set win rate.

Source of truth for design/08-skill-parity.md. Every figure in that doc
comes from a run of this script.

Play quality q (MatchConfig.player_quality, see equations.py):
  each clash, with probability q the player reads the AI's real pick and
  counters it; each turn, with probability q the QTE is perfect. Otherwise
  the player picks a random card / rolls a uniform 1-10 QTE (q=0 is the old
  random player).
  The two halves can be set independently: q_read (MatchConfig.player_read)
  and q_time (MatchConfig.player_timing). In this script a cell's q is either
  a float (both axes) or a (q_read, q_time) pair.

Configs
  parity_<enc> : same level, AI QTE ratio 1.0, <enc>'s turns and phases
  game_<enc>   : today's game rule (cli.py:305): opponent level and AI QTE
                 both scaled by ENCOUNTER_RATIOS[enc]

Usage (from sim/):
  python3 scripts/parity_sweep.py curve            # win rate vs q, all configs
  python3 scripts/parity_sweep.py gap              # level-ratio x q grid + fit
  python3 scripts/parity_sweep.py levers           # q50 under candidate constant changes
  python3 scripts/parity_sweep.py all --out results.json
  python3 scripts/parity_sweep.py grid2d --out grid2d.json  # q_read x q_time at parity
Options: --seeds N (per archetype pair per cell), --workers N
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, ".")

from velocity_shift import ai as _ai, equations as _eq, match as _match
from velocity_shift.ai import ENCOUNTER_RATIOS
from velocity_shift.cars import ARCHETYPES, build_stats
from velocity_shift.cli import ENCOUNTER_MAX_TURNS
from velocity_shift.models import CombatantStats, MatchConfig, Stance
from velocity_shift.simulation import SimulationRunner, _COUNTER

ARCHS = list(ARCHETYPES)
PAIRS = list(itertools.product(ARCHS, ARCHS))          # 25 pairs, 5 mirrors
ENCS = ["wild", "lieutenant", "boss"]
LEVELS = [10, 30, 50, 80]
Q_GRID = [round(i * 0.05, 2) for i in range(21)]


# ── Lever prototypes (scratch only; equations.py is not edited) ──────

class _ReadingAIRunner(SimulationRunner):
    """AI that, with probability ai_read, counters the player's actual card
    (overriding the pick the player may have read). Prototype lever only."""

    def __init__(self, cfg, ai_read):
        super().__init__(cfg)
        self.ai_read = ai_read

    def _make_player_card_fn(self):
        inner = super()._make_player_card_fn()
        def fn(t, ci, hand, opp_hand, clashes):
            pick = inner(t, ci, hand, opp_hand, clashes)
            self._last_player = pick.stance
            return pick
        return fn

    def _make_opponent_card_fn(self):
        inner = super()._make_opponent_card_fn()
        def fn(t, ci, hand, player_hand, phase_index, pers, clashes, hist):
            card = inner(t, ci, hand, player_hand, phase_index, pers, clashes, hist)
            if self._rng.random() < self.ai_read:
                target = _COUNTER[self._last_player]
                alt = next((c for c in hand if c == target), None)
                if alt is not None:
                    return alt
            return card
        return fn


def _apply_levers(lv: dict):
    _eq.CLASH_STAKES = lv.get("clash_stakes", 0.35)
    _eq.BATTLE_BONUS = lv.get("battle_bonus", 0.05)
    _match.RUBBER_BAND_FRACTION = lv.get("rubber_band", 0.15)
    import velocity_shift.combat as _combat
    _combat.BATTLE_BONUS = _eq.BATTLE_BONUS


def _quality_kwargs(q):
    """q is a float (player_quality) or a (q_read, q_time) pair."""
    if isinstance(q, (list, tuple)):
        return {"player_read": q[0], "player_timing": q[1]}
    return {"player_quality": q}


def _cell(task):
    """Run one cell. task = (config, enc, level, level_ratio, q, seeds, levers, base_seed)."""
    cfg_kind, enc, level, lratio, q, seeds, levers, base_seed = task
    _apply_levers(levers)
    qte_ratio = levers.get("ai_qte_ratio")
    if cfg_kind == "game":
        lratio = ENCOUNTER_RATIOS[enc]
        if qte_ratio is None:
            qte_ratio = ENCOUNTER_RATIOS[enc]
    elif qte_ratio is None:
        qte_ratio = 1.0
    o_level = max(1, round(level * lratio))
    ai_read = levers.get("ai_read", 0.0)
    wins = n = 0
    for pi, (pa, oa) in enumerate(PAIRS):
        p = build_stats(pa, level)
        o = build_stats(oa, o_level)
        for s in range(seeds):
            seed = base_seed + pi * 100003 + s
            cfg = MatchConfig(
                player_stats=CombatantStats("Player", *p, level=level),
                opponent_stats=CombatantStats("Opponent", *o, level=o_level),
                max_turns=ENCOUNTER_MAX_TURNS[enc], seed=seed,
                encounter_type=enc, rival_personality=oa,
                opponent_qte_ratio=qte_ratio, **_quality_kwargs(q),
            )
            r = _ReadingAIRunner(cfg, ai_read) if ai_read else SimulationRunner(cfg)
            wins += r.run().match.winner == "Player"
            n += 1
    return {"config": cfg_kind, "enc": enc, "level": level, "o_level": o_level,
            "level_ratio": o_level / level, "q": q, "wins": wins, "n": n,
            "levers": levers}


def _pair_cell(task):
    """Per-archetype-pair win rate (for the parity spread)."""
    enc, level, q, pa, oa, seeds = task
    _apply_levers({})
    p = build_stats(pa, level); o = build_stats(oa, level)
    wins = 0
    for s in range(seeds):
        cfg = MatchConfig(CombatantStats("Player", *p, level=level),
                          CombatantStats("Opponent", *o, level=level),
                          max_turns=ENCOUNTER_MAX_TURNS[enc], seed=7_000_000 + s,
                          encounter_type=enc, rival_personality=oa,
                          player_quality=q, opponent_qte_ratio=1.0)
        wins += SimulationRunner(cfg).run().match.winner == "Player"
    return {"enc": enc, "level": level, "q": q, "pa": pa, "oa": oa, "wins": wins, "n": seeds}


# ── Fitting (pure stdlib) ────────────────────────────────────────────

def q50(points):
    """Linear interpolation of the q where win rate crosses 0.5.
    points = [(q, rate)] sorted by q. None if no crossing."""
    pts = sorted(points)
    if pts[0][1] >= 0.5:
        return 0.0
    for (q0, r0), (q1, r1) in zip(pts, pts[1:]):
        if r0 < 0.5 <= r1:
            return q0 + (0.5 - r0) * (q1 - q0) / (r1 - r0)
    return None


def fit_logistic(rows):
    """Binomial max-likelihood fit of
         P(win) = 1 / (1 + exp(-(a*(q - q0) - b*ln(r))))
    with r = opponent level / player level. Parametrised as
    z = c0 + a*q - b*ln r (q0 = -c0/a). Damped Newton-Raphson (step
    halving on the log-likelihood), pure stdlib."""
    X = [(1.0, row["q"], -math.log(row["level_ratio"])) for row in rows]

    def loglik(w):
        ll = 0.0
        for x, row in zip(X, rows):
            z = sum(wi * xi for wi, xi in zip(w, x))
            # log p = -log(1+e^-z), log(1-p) = -log(1+e^z), computed stably
            lp = -_log1pexp(-z); lq = -_log1pexp(z)
            ll += row["wins"] * lp + (row["n"] - row["wins"]) * lq
        return ll

    w = [0.0, 0.0, 0.0]
    ll = loglik(w)
    for _ in range(200):
        g = [0.0] * 3
        H = [[0.0] * 3 for _ in range(3)]
        for x, row in zip(X, rows):
            z = sum(wi * xi for wi, xi in zip(w, x))
            p = _sigmoid(z)
            k, n = row["wins"], row["n"]
            for i in range(3):
                g[i] += (k - n * p) * x[i]
                for j in range(3):
                    H[i][j] += n * p * (1 - p) * x[i] * x[j]
        for i in range(3):
            H[i][i] += 1e-6
        step = _solve(H, g)
        t = 1.0
        while True:
            w_new = [wi + t * si for wi, si in zip(w, step)]
            ll_new = loglik(w_new)
            if ll_new >= ll or t < 1e-6:
                break
            t /= 2
        done = abs(ll_new - ll) < 1e-8
        w, ll = w_new, ll_new
        if done:
            break
    c0, a, b = w
    se = worst = 0.0
    for x, row in zip(X, rows):
        p = _sigmoid(sum(wi * xi for wi, xi in zip(w, x)))
        d = row["wins"] / row["n"] - p
        se += d * d; worst = max(worst, abs(d))
    return {"a": a, "q0": -c0 / a, "b": b, "rms_err": math.sqrt(se / len(rows)),
            "max_err": worst, "cells": len(rows)}


def fit_features(rows, feats):
    """Binomial max-likelihood logistic fit, z = w . feats(row), with
    feats(row) -> list of floats (include 1.0 for the intercept). Same
    damped Newton-Raphson as fit_logistic. Returns weights and errors."""
    X = [feats(r) for r in rows]
    k = len(X[0])

    def loglik(w):
        ll = 0.0
        for x, row in zip(X, rows):
            z = sum(wi * xi for wi, xi in zip(w, x))
            ll += row["wins"] * -_log1pexp(-z) + (row["n"] - row["wins"]) * -_log1pexp(z)
        return ll

    w = [0.0] * k
    ll = loglik(w)
    for _ in range(300):
        g = [0.0] * k
        H = [[0.0] * k for _ in range(k)]
        for x, row in zip(X, rows):
            p = _sigmoid(sum(wi * xi for wi, xi in zip(w, x)))
            n = row["n"]
            for i in range(k):
                g[i] += (row["wins"] - n * p) * x[i]
                for j in range(k):
                    H[i][j] += n * p * (1 - p) * x[i] * x[j]
        for i in range(k):
            H[i][i] += 1e-6
        step = _solve(H, g)
        t = 1.0
        while True:
            w_new = [wi + t * si for wi, si in zip(w, step)]
            ll_new = loglik(w_new)
            if ll_new >= ll or t < 1e-6:
                break
            t /= 2
        done = abs(ll_new - ll) < 1e-8
        w, ll = w_new, ll_new
        if done:
            break
    se = worst = 0.0
    for x, row in zip(X, rows):
        d = row["wins"] / row["n"] - _sigmoid(sum(wi * xi for wi, xi in zip(w, x)))
        se += d * d; worst = max(worst, abs(d))
    return {"w": w, "rms_err": math.sqrt(se / len(rows)), "max_err": worst,
            "cells": len(rows), "loglik": ll}


def _sigmoid(z):
    if z >= 0:
        return 1 / (1 + math.exp(-z))
    e = math.exp(z)
    return e / (1 + e)


def _log1pexp(z):
    return z + math.log1p(math.exp(-z)) if z > 0 else math.log1p(math.exp(z))


def _solve(A, y):
    n = len(y)
    M = [row[:] + [y[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, n + 1):
                    M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]


# ── Sweeps ───────────────────────────────────────────────────────────

def run(tasks, fn, workers):
    with Pool(workers) as pool:
        return pool.map(fn, tasks, chunksize=1)


def sweep_curve(seeds, workers):
    tasks = []
    for kind in ("parity", "game"):
        for enc in ENCS:
            for L in LEVELS:
                for q in Q_GRID:
                    tasks.append((kind, enc, L, 1.0, q, seeds, {}, 1_000_000))
    return run(tasks, _cell, workers)


def sweep_pairs(seeds, workers):
    tasks = [(enc, 50, q, pa, oa, seeds) for enc in ENCS
             for q in Q_GRID for pa, oa in PAIRS]
    return run(tasks, _pair_cell, workers)


GAP_RATIOS = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]
GAP_Q = [round(i * 0.1, 1) for i in range(11)]


def sweep_gap(seeds, workers):
    tasks = [("parity", enc, 50, lr, q, seeds, {}, 2_000_000)
             for enc in ENCS for lr in GAP_RATIOS for q in GAP_Q]
    return run(tasks, _cell, workers)


LEVERS = [
    {"name": "current"},
    {"name": "ai_qte_ratio 1.2 (QTE 8.4)", "ai_qte_ratio": 1.2},
    {"name": "ai_qte_ratio 10/7 (QTE 10)", "ai_qte_ratio": 10 / 7},
    {"name": "clash_stakes 0.20", "clash_stakes": 0.20},
    {"name": "clash_stakes 0.60", "clash_stakes": 0.60},
    {"name": "battle_bonus 0.20", "battle_bonus": 0.20},
    {"name": "rubber_band 0.50", "rubber_band": 0.50},
    {"name": "rubber_band 0.05", "rubber_band": 0.05},
    {"name": "ai_read 0.30", "ai_read": 0.30},
    {"name": "ai_read 0.50", "ai_read": 0.50},
    {"name": "ai_read 0.70", "ai_read": 0.70},
    {"name": "ai_read 0.80", "ai_read": 0.80},
    {"name": "ai_read 0.85", "ai_read": 0.85},
    {"name": "ai_read 0.90", "ai_read": 0.90},
    {"name": "ai_read 0.30 + QTE 10", "ai_read": 0.30, "ai_qte_ratio": 10 / 7},
    {"name": "ai_read 0.40 + QTE 10", "ai_read": 0.40, "ai_qte_ratio": 10 / 7},
    {"name": "ai_read 0.60 + QTE 8.4", "ai_read": 0.60, "ai_qte_ratio": 1.2},
    {"name": "ai_read 0.70 + QTE 8.4", "ai_read": 0.70, "ai_qte_ratio": 1.2},
    {"name": "ai_read 0.50 + QTE 10", "ai_read": 0.50, "ai_qte_ratio": 10 / 7},
    {"name": "ai_read 0.60 + QTE 10", "ai_read": 0.60, "ai_qte_ratio": 10 / 7},
]


def sweep_levers(seeds, workers, levers=LEVERS, enc="lieutenant", level=50):
    tasks = []
    for lv in levers:
        cfg = {k: v for k, v in lv.items() if k != "name"}
        for q in Q_GRID:
            tasks.append(("parity", enc, level, 1.0, q, seeds, cfg, 3_000_000))
    res = run(tasks, _cell, workers)
    out = []
    for lv in levers:
        cfg = {k: v for k, v in lv.items() if k != "name"}
        rows = [r for r in res if r["levers"] == cfg]
        pts = [(r["q"], r["wins"] / r["n"]) for r in rows]
        out.append({"name": lv["name"], "levers": cfg, "q50": q50(pts),
                    "curve": sorted(pts), "n_per_q": rows[0]["n"]})
    return out


GRID2D_Q = [0.0, 0.25, 0.5, 0.75, 0.9, 1.0]
GRID2D_ENCS = ["lieutenant", "boss"]


def sweep_grid2d(seeds, workers, encs=GRID2D_ENCS, levels=LEVELS):
    """Stat parity, AI QTE ratio 1.0: every (q_read, q_time) on GRID2D_Q,
    for each encounter length and level. N per cell = 25 pairs x seeds."""
    tasks = [("parity", enc, L, 1.0, (qr, qt), seeds, {}, 4_000_000)
             for enc in encs for L in levels for qr in GRID2D_Q for qt in GRID2D_Q]
    return run(tasks, _cell, workers)


def _report_grid2d(res):
    out = {}
    for enc in sorted({r["enc"] for r in res}, key=ENCS.index):
        rows = [r for r in res if r["enc"] == enc]
        levels = sorted({r["level"] for r in rows})
        pooled = {}
        for r in rows:
            key = tuple(r["q"])
            w, n = pooled.get(key, (0, 0))
            pooled[key] = (w + r["wins"], n + r["n"])
        n_cell = next(iter(pooled.values()))[1]
        print(f"\ngrid2d parity_{enc}: win % pooled over L{levels}, N={n_cell} per cell"
              f"\n  rows q_read, cols q_time")
        print("  qr\\qt" + "".join(f"  {qt:5.2f}" for qt in GRID2D_Q))
        for qr in GRID2D_Q:
            print(f"  {qr:5.2f}" + "".join(
                f"  {pooled[(qr, qt)][0] / pooled[(qr, qt)][1] * 100:5.1f}" for qt in GRID2D_Q))
        prow = [{"q": list(k), "wins": v[0], "n": v[1]} for k, v in pooled.items()]
        additive = fit_features(prow, lambda r: [1.0, r["q"][0], r["q"][1]])
        inter = fit_features(prow, lambda r: [1.0, r["q"][0], r["q"][1], r["q"][0] * r["q"][1]])
        c, ar, at = additive["w"]
        print(f"  additive logit fit: z = {c:.2f} + {ar:.2f}*q_read + {at:.2f}*q_time"
              f"   rms {additive['rms_err']*100:.1f} pts  max {additive['max_err']*100:.1f} pts")
        c2, ar2, at2, ai2 = inter["w"]
        print(f"  with interaction:   z = {c2:.2f} + {ar2:.2f}*q_read + {at2:.2f}*q_time"
              f" + {ai2:.2f}*q_read*q_time   rms {inter['rms_err']*100:.1f} pts"
              f"  max {inter['max_err']*100:.1f} pts  (delta loglik {inter['loglik']-additive['loglik']:.1f})")
        # q_time needed to reach 50% at each q_read (linear interpolation on the grid)
        for qr in GRID2D_Q:
            pts = [(qt, pooled[(qr, qt)][0] / pooled[(qr, qt)][1]) for qt in GRID2D_Q]
            v = q50(pts)
            print(f"  q_read {qr:4.2f}: q_time for 50% = {'never' if v is None else f'{v:.3f}'}")
        out[enc] = {"pooled": prow, "additive": additive, "interaction": inter}
    return out


def _fmt_curve(res, kind, enc):
    print(f"\n{kind}_{enc}: win rate by q (rows) and level (cols); N per cell = "
          f"{next(r['n'] for r in res if r['config']==kind and r['enc']==enc)}")
    print("   q  " + "".join(f"  L{L:<4}" for L in LEVELS) + "  pooled")
    for q in Q_GRID:
        cells = [r for r in res if r["config"] == kind and r["enc"] == enc and r["q"] == q]
        by = {r["level"]: r for r in cells}
        pooled = sum(r["wins"] for r in cells) / sum(r["n"] for r in cells)
        print(f"  {q:4.2f}" + "".join(f"  {by[L]['wins']/by[L]['n']*100:5.1f}" for L in LEVELS)
              + f"  {pooled*100:5.1f}")
    for L in LEVELS:
        pts = [(r["q"], r["wins"] / r["n"]) for r in res
               if r["config"] == kind and r["enc"] == enc and r["level"] == L]
        v = q50(pts)
        print(f"  q50 L{L}: {'n/a (never 50%)' if v is None else f'{v:.3f}'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["curve", "pairs", "gap", "levers", "validate", "fit", "grid2d", "all"])
    ap.add_argument("--in", dest="inp", default=None, help="fit: results JSON from an earlier 'gap' or 'all' run")
    ap.add_argument("--ai-read", type=float, default=0.0, help="validate: prototype AI read rate")
    ap.add_argument("--ai-qte-ratio", type=float, default=None, help="validate: AI QTE ratio")
    ap.add_argument("--seeds", type=int, default=80, help="seeds per archetype pair per cell")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    data = {}
    if a.what in ("curve", "all"):
        res = sweep_curve(a.seeds, a.workers); data["curve"] = res
        for kind in ("parity", "game"):
            for enc in ENCS:
                _fmt_curve(res, kind, enc)
    if a.what in ("pairs", "all"):
        res = sweep_pairs(max(1, a.seeds * 5), a.workers); data["pairs"] = res
        for enc in ENCS:
            qs = []
            for pa, oa in PAIRS:
                pts = [(r["q"], r["wins"] / r["n"]) for r in res
                       if r["enc"] == enc and r["pa"] == pa and r["oa"] == oa]
                qs.append((q50(pts), pa, oa))
            vals = [v for v, _, _ in qs if v is not None]
            print(f"\npairs parity_{enc} L50 (N={res[0]['n']} per pair per q): "
                  f"q50 min {min(vals):.3f} median {sorted(vals)[len(vals)//2]:.3f} max {max(vals):.3f}")
            for v, pa, oa in sorted(qs, key=lambda t: (t[0] is None, t[0])):
                print(f"   {pa:>10} vs {oa:<10} q50 = {v if v is None else round(v, 3)}")
    if a.what in ("gap", "all"):
        res = sweep_gap(max(1, a.seeds // 2), a.workers); data["gap"] = res
        data["fit"] = {}
        for enc in ENCS:
            rows = [r for r in res if r["enc"] == enc]
            print(f"\ngap parity_{enc} L50: win % by q (rows) x opponent level ratio (cols), N={rows[0]['n']}")
            print("   q " + "".join(f"  {lr:5.2f}" for lr in GAP_RATIOS))
            for q in GAP_Q:
                by = {r["level_ratio"]: r for r in rows if r["q"] == q}
                print(f"  {q:3.1f}" + "".join(
                    f"  {by[k]['wins']/by[k]['n']*100:5.1f}" for k in sorted(by)))
            for lr in sorted({r["level_ratio"] for r in rows}):
                pts = [(r["q"], r["wins"] / r["n"]) for r in rows if r["level_ratio"] == lr]
                v = q50(pts)
                print(f"  q50 at ratio {lr:.2f}: {'n/a' if v is None else f'{v:.3f}'}")
            f = fit_logistic(rows); data["fit"][enc] = f
            print(f"  logistic fit: a={f['a']:.2f}  q0={f['q0']:.3f}  b={f['b']:.2f}  "
                  f"rms err={f['rms_err']*100:.1f} pts  max err={f['max_err']*100:.1f} pts  ({f['cells']} cells)")
    if a.what in ("levers", "all"):
        res = sweep_levers(a.seeds, a.workers); data["levers"] = res
        print(f"\nlevers (parity_lieutenant L50, N={res[0]['n_per_q']} per q):")
        for r in res:
            v = r["q50"]
            c = dict(r["curve"])
            print(f"  {r['name']:<28} q50={'n/a' if v is None else f'{v:.3f}':>6}   "
                  f"win% q=0.5 {c[0.5]*100:5.1f}  q=0.8 {c[0.8]*100:5.1f}  q=0.9 {c[0.9]*100:5.1f}  q=1.0 {c[1.0]*100:5.1f}")
    if a.what == "grid2d":
        res = sweep_grid2d(a.seeds, a.workers); data["grid2d"] = res
        data["grid2d_fit"] = _report_grid2d(res)
    if a.what == "fit":
        with open(a.inp) as fh:
            res = json.load(fh)["gap"]
        for enc in ENCS:
            f = fit_logistic([r for r in res if r["enc"] == enc])
            print(f"  fit parity_{enc}: a={f['a']:.2f}  q0={f['q0']:.3f}  b={f['b']:.2f}  "
                  f"rms err={f['rms_err']*100:.1f} pts  max err={f['max_err']*100:.1f} pts  ({f['cells']} cells)")
        f = fit_logistic(res)
        print(f"  fit pooled:          a={f['a']:.2f}  q0={f['q0']:.3f}  b={f['b']:.2f}  "
              f"rms err={f['rms_err']*100:.1f} pts  max err={f['max_err']*100:.1f} pts  ({f['cells']} cells)")
    if a.what == "validate":
        lv = {"ai_read": a.ai_read}
        if a.ai_qte_ratio is not None:
            lv["ai_qte_ratio"] = a.ai_qte_ratio
        print(f"\nvalidate levers {lv} (parity configs, all levels):")
        res = []
        for enc in ENCS:
            for L in LEVELS:
                r = sweep_levers(a.seeds, a.workers, [dict(name=f"{enc} L{L}", **lv)], enc, L)[0]
                res.append(r)
                c = dict(r["curve"]); v = r["q50"]
                print(f"  {r['name']:<14} N={r['n_per_q']}  q50={'n/a' if v is None else f'{v:.3f}':>6}  "
                      f"win% q=0.5 {c[0.5]*100:5.1f}  q=0.8 {c[0.8]*100:5.1f}  q=0.9 {c[0.9]*100:5.1f}  q=1.0 {c[1.0]*100:5.1f}")
        data["validate"] = res
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(data, fh, indent=1)


if __name__ == "__main__":
    main()
