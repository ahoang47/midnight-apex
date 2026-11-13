"""Spot-check: does the live sim (sim/velocity_shift, G2 made live 2026-11-13) reproduce G2's full-run numbers?
For each cell (15 tracks x 10/20/30 turns x 3 boss styles) take the G2 tuned split for that measure from
results_v4b_G2_slant_m10.npz (argmax of the 9-batch mean, same as analyze_v4b.tuned_idx), run N live races
with that split, and compare the mean to the npz win rate at the same split. Writes live_spotcheck.json.
Usage: python3 live_spotcheck.py [N per cell]"""
import json, os, sys
from multiprocessing import Pool
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "sim"))
from velocity_shift.models import CombatantStats, MatchConfig      # noqa: E402
from velocity_shift.simulation import SimulationRunner             # noqa: E402
from velocity_shift import equations as E                          # noqa: E402

M = json.load(open(os.path.join(HERE, "results_v4b_meta.json")))
TR = [tuple(t) for t in M["tracks"]]; LAPS = M["laps"]; L = M["lengths"]; ST = M["styles"]
TUNES = np.array(M["tunes"]); NT = 21
N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
CAP = E.MOD_CAP_FRACTION
# measure: (r, q_read, q_time or None for the average QTE profile, pacing share)
MEAS = {"avg_cap": (CAP, 0.6, None, 0.6), "perf_0.8": (0.8, 1.0, 1.0, 1.0), "perf_1.0": (1.0, 1.0, 1.0, 1.0),
        "c8080": (CAP, 0.8, 0.8, 0.8)}


def cell(a):
    mname, ti, k, s, tune = a
    r, q, qt, pace = MEAS[mname]
    sp, sh, se = tune
    tot = 300.0 * r
    p = CombatantStats("P", pow=tot * sp, en=tot * se, han=tot * sh)
    o = CombatantStats("O", pow=100.0, en=100.0, han=100.0)
    w = 0.0
    for i in range(N):
        cfg = MatchConfig(player_stats=p, opponent_stats=o, max_turns=L[k], seed=9_000_000 + 100_000 * ti + 10_000 * k + 1000 * s + i,
                          district=TR[ti][0], corners=LAPS[ti], player_read=q, player_timing=qt, player_pacing=pace,
                          player_qte_profile=None if qt is not None else "average", boss_style=ST[s])
        m = SimulationRunner(cfg).run().match
        w += 1.0 if m.player_total_progress > m.opponent_total_progress else 0.5 if m.player_total_progress == m.opponent_total_progress else 0.0
    return a[:4], w / N


if __name__ == "__main__":
    Z = np.load(os.path.join(HERE, "results_v4b_G2_slant_m10.npz"))
    out = {"n_per_cell": N, "cap": CAP}
    for mname in MEAS:
        A = Z[mname][..., 0, :]                       # (9, 15, 3, 3, 22) win
        mean = A.mean(0)
        idx = mean[..., :NT].argmax(-1)
        jobs = [(mname, ti, k, s, tuple(TUNES[idx[ti, k, s]])) for ti in range(len(TR)) for k in range(3) for s in range(3)]
        with Pool(8) as pool:
            res = dict(pool.map(cell, jobs))
        live = np.zeros((len(TR), 3, 3)); ref = np.zeros_like(live)
        for (m_, ti, k, s), v in res.items():
            live[ti, k, s] = v; ref[ti, k, s] = mean[ti, k, s, idx[ti, k, s]]
        dist = np.array([d for d, _ in TR])
        out[mname] = dict(live=round(100 * live.mean(), 1), g2=round(100 * ref.mean(), 1),
                          live_by_len={T: round(100 * live[:, k].mean(), 1) for k, T in enumerate(L)},
                          g2_by_len={T: round(100 * ref[:, k].mean(), 1) for k, T in enumerate(L)},
                          live_by_dist={d: round(100 * live[dist == d].mean(), 1) for d in ("touge", "wangan", "street")},
                          g2_by_dist={d: round(100 * ref[dist == d].mean(), 1) for d in ("touge", "wangan", "street")},
                          max_cell_diff=round(100 * np.abs(live - ref).max(), 1))
        print(mname, json.dumps(out[mname]), flush=True)
    json.dump(out, open(os.path.join(HERE, "live_spotcheck.json"), "w"), indent=1)
