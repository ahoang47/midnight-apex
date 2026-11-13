"""Analysis of results_v3_<CAND>.npz -> analysis_v3.json + tables_v3.md.
Tune choice per cell (track x length x style) uses the 9-batch mean win; the clear test uses the 9 per-batch differences
(clear = mean difference >= 5 pp and all 9 batch differences with the same sign).
Usage: python3 analyze_v3.py CAND [CAND ...]"""
import json, sys
from collections import defaultdict
import numpy as np

M = json.load(open("results_v3_meta.json"))
TR = [tuple(t) for t in M["tracks"]]; LAPS = M["laps"]; DIST = np.array([d for d, _ in TR]); D = ("touge", "wangan", "street")
L = M["lengths"]; NT = 21; EV = 21
K = {k: i for i, k in enumerate(M["keys"])}
GRID = np.array(M["tunes"][:NT])
try:
    OUT = json.load(open("analysis_v3.json"))
except FileNotFoundError:
    OUT = {}


def pct(x): return round(100 * float(x), 1)
def r2(x): return round(float(x), 2)


def tuned_idx(a): return a[..., K["win"], :NT].mean(0).argmax(-1)               # (15,3,3)
def pick(a, idx, k="win"): return np.take_along_axis(a[..., K[k], :], idx[None, ..., None], -1)[..., 0]   # (9,15,3,3)
def pick_x(x, idx): return np.take_along_axis(x, idx[None, ..., None].reshape(1, *idx.shape, 1, *([1] * (x.ndim - 5))), 4)[:, :, :, :, 0]


def wrong_idx(a):
    m = a.mean(0)[..., K["win"], :NT]
    idx = np.zeros(m.shape[:3], int)
    for ti, (d, _) in enumerate(TR):
        idx[ti] = m[DIST != d].mean(0).argmax(-1)
    return idx


def clear(diff):
    mu = diff.mean(0); s = np.sign(diff)
    same = (s == s[0:1]).all(0) & (s[0] != 0)
    return float(((mu >= 0.05) & same).mean())


def even_idx(a): return np.full(a.shape[1:4], EV)


def car_stats(Z, A, idx):
    """Overrun / lock stats for the car chosen by idx (15,3,3) at average play at the cap."""
    s = {}
    for k in ("ov", "ovc", "lock", "pen", "rlock", "rov", "rovplay", "rswitch", "limp"):
        s[k] = pct(pick(A, idx, k).mean())
    s["streak_mean"] = r2(pick(A, idx, "streak").mean())
    ovc = pick(A, idx, "ovc").mean(); s["pen_per_overrun_clash"] = pct(pick(A, idx, "pen").mean() / max(ovc, 1e-9))
    nl = pick_x(Z["avg_cap|n_locks"], idx).sum(); du = pick_x(Z["avg_cap|dur"], idx).sum()
    s["lock_dur_mean"] = r2(du / max(nl, 1))
    h = pick_x(Z["avg_cap|hist"], idx).sum((0, 1, 2, 3)); h = h / max(h.sum(), 1)
    s["lock_dur_share"] = {"0": pct(h[0]), "1": pct(h[1]), "2": pct(h[2]), "3+": pct(h[3:].sum())}
    s["streak_p90"] = r2(pick_x(Z["avg_cap|streak_p90"], idx).mean()); s["streak_max"] = int(pick_x(Z["avg_cap|streak_max"], idx).max())
    lr = pick_x(Z["avg_cap|lock_res"], idx).sum((0, 1, 2, 3)); s["locks_by_res_fuel_susp_brake"] = [pct(x) for x in lr / max(lr.sum(), 1)]
    s["locks_per_race"] = r2(nl / (9 * M["n"] * idx.size))
    for k_, T in enumerate(L):
        s[f"len{T}"] = dict(ov=pct(pick(A, idx, "ov")[:, :, k_].mean()), lock=pct(pick(A, idx, "lock")[:, :, k_].mean()),
                            rlock=pct(pick(A, idx, "rlock")[:, :, k_].mean()), streak=r2(pick(A, idx, "streak")[:, :, k_].mean()),
                            pen=pct(pick(A, idx, "pen")[:, :, k_].mean()))
    for d in D:
        m = DIST == d
        s[f"lock_{d}"] = pct(pick(A, idx, "lock")[:, m].mean()); s[f"ov_{d}"] = pct(pick(A, idx, "ov")[:, m].mean())
        s[f"rlock_{d}"] = pct(pick(A, idx, "rlock")[:, m].mean())
    return s


def clustering(Z, idx):
    """Lock rate by corner type, by (previous corner, corner) pair, by turn-in-lap and by lap (tuned car, avg play)."""
    lt = pick_x(Z["avg_cap|lock_t"], idx).mean(0)        # (15,3,3,30)
    ty = defaultdict(list); pr = defaultdict(list); pos = defaultdict(list); lap_no = defaultdict(list)
    for ti in range(len(TR)):
        lap = LAPS[ti]
        for k_, T in enumerate(L):
            for st in range(3):
                for t in range(T):
                    v = lt[ti, k_, st, t]
                    ty[lap[t % 10]].append(v)
                    if t > 0:
                        pr[(lap[(t - 1) % 10], lap[t % 10])].append(v)
                    pos[t % 10].append(v)
                    if T == 30:
                        lap_no[t // 10 + 1].append(v)
    allv = np.mean([v for x in ty.values() for v in x])
    out = dict(overall=pct(allv), by_corner={k: [pct(np.mean(v)), len(v)] for k, v in sorted(ty.items(), key=lambda kv: -np.mean(kv[1]))},
               by_lap_30turn={k: pct(np.mean(v)) for k, v in sorted(lap_no.items())},
               by_turn_in_lap={k: pct(np.mean(v)) for k, v in sorted(pos.items())})
    prs = sorted(((k, np.mean(v), len(v)) for k, v in pr.items() if len(v) >= 30), key=lambda x: -x[1])
    out["top_pairs"] = [[f"{a}->{b}", pct(m), n] for (a, b), m, n in prs[:6]]
    out["bottom_pairs"] = [[f"{a}->{b}", pct(m), n] for (a, b), m, n in prs[-4:]]
    return out


for cand in sys.argv[1:]:
    Z = np.load(f"results_v3_{cand}.npz")
    A, P8, P1 = Z["avg_cap"], Z["perf_0.8"], Z["perf_1.0"]
    ti, wi, ei = tuned_idx(A), wrong_idx(A), even_idx(A)
    r = dict(cfg=M["candidates"][cand])
    r.update(perf08_tuned=pct(pick(P8, tuned_idx(P8)).mean()), perf08_even=pct(P8[..., K["win"], EV].mean()),
             perf10_tuned=pct(pick(P1, tuned_idx(P1)).mean()), perf10_even=pct(P1[..., K["win"], EV].mean()),
             avg_tuned=pct(pick(A, ti).mean()), avg_even=pct(A[..., K["win"], EV].mean()), avg_wrong=pct(pick(A, wi).mean()))
    for k_, T in enumerate(L):
        r[f"len{T}_combat"] = dict(perf08=pct(pick(P8, tuned_idx(P8))[:, :, k_].mean()), perf10=pct(pick(P1, tuned_idx(P1))[:, :, k_].mean()),
                                   avg=pct(pick(A, ti)[:, :, k_].mean()))
    r["perf08_by_district"] = {d: pct(pick(P8, tuned_idx(P8))[:, DIST == d].mean()) for d in D}
    r["perf10_by_district"] = {d: pct(pick(P1, tuned_idx(P1))[:, DIST == d].mean()) for d in D}
    r["tuned"] = car_stats(Z, A, ti); r["even"] = car_stats(Z, A, ei); r["wrong"] = car_stats(Z, A, wi)
    r["perf10_tuned_lock"] = pct(pick(P1, tuned_idx(P1), "lock").mean()); r["perf10_tuned_rlock"] = pct(pick(P1, tuned_idx(P1), "rlock").mean())
    r["clustering_tuned"] = clustering(Z, ti)
    Tw, Ev, Wr = pick(A, ti), A[..., K["win"], EV], pick(A, wi)
    r.update(gap_even=pct((Tw - Ev).mean()), clear_even=pct(clear(Tw - Ev)), gap_wrong=pct((Tw - Wr).mean()), clear_wrong=pct(clear(Tw - Wr)),
             gap_wrong_max_cell=pct((Tw - Wr).mean(0).max()))
    wc = np.unravel_index((Tw - Wr).mean(0).argmax(), Tw.shape[1:])
    r["worst_cell"] = dict(track=TR[wc[0]][1], length=L[wc[1]], style=M["styles"][wc[2]], tuned_split=GRID[ti[wc]].tolist(),
                           wrong_split=GRID[wi[wc]].tolist(), tuned_win=pct(Tw.mean(0)[wc]), wrong_win=pct(Wr.mean(0)[wc]))
    r["gap_by_len"] = {T: [pct((Tw - Ev)[:, :, k_].mean()), pct((Tw - Wr)[:, :, k_].mean())] for k_, T in enumerate(L)}
    r["one_tune"] = None
    m = A.mean(0)[..., K["win"], :NT]; best1 = int(m.mean((0, 1, 2)).argmax())
    loss = (m.max(-1) - m[..., best1])
    r["one_tune"] = dict(split=GRID[best1].tolist(), mean_loss_vs_cell_best=pct(loss.mean()), max_loss=pct(loss.max()),
                         cells_within_2pp=pct((loss <= 0.02).mean()))
    for d in D:
        s = DIST == d
        r[d] = dict(tuned=pct(Tw[:, s].mean()), even=pct(Ev[:, s].mean()), gap_even=pct((Tw - Ev)[:, s].mean()),
                    clear_even=pct(clear((Tw - Ev)[:, s])), gap_wrong=pct((Tw - Wr)[:, s].mean()), clear_wrong=pct(clear((Tw - Wr)[:, s])),
                    worst_wrong=pct((Tw - Wr)[:, s].mean(0).max()), tuned_split=np.round(GRID[ti[s]].reshape(-1, 3).mean(0), 3).tolist())
    # budgeting: rationing (lambda 0.6, H 3) vs greedy, and a stronger rationer (lambda 2, H 4); each with its own best tune
    G_, R2 = Z["greedy_cap"], Z["ration2_cap"]
    Gw = pick(G_, tuned_idx(G_)); R2w = pick(R2, tuned_idx(R2))
    r.update(greedy_tuned=pct(Gw.mean()), ration2_tuned=pct(R2w.mean()),
             pacing_gap=pct((Tw - Gw).mean()), pacing_clear=pct(clear(Tw - Gw)), pacing_neg_clear=pct(clear(Gw - Tw)),
             pacing_max_cell=pct(np.abs((Tw - Gw).mean(0)).max()),
             pacing2_gap=pct((R2w - Gw).mean()), pacing2_clear=pct(clear(R2w - Gw)), pacing2_neg_clear=pct(clear(Gw - R2w)),
             pacing2_max_cell=pct(np.abs((R2w - Gw).mean(0)).max()),
             greedy_lock=pct(pick(G_, tuned_idx(G_), "lock").mean()), ration2_lock=pct(pick(R2, tuned_idx(R2), "lock").mean()),
             greedy_ov=pct(pick(G_, tuned_idx(G_), "ov").mean()), ration2_ov=pct(pick(R2, tuned_idx(R2), "ov").mean()),
             pacing_by_len={T: [pct((Tw - Gw)[:, :, k_].mean()), pct((R2w - Gw)[:, :, k_].mean())] for k_, T in enumerate(L)})
    R1, RN = Z["read1_cap"], Z["random_cap"]
    i1 = tuned_idx(R1)
    r.update(read1_tuned=pct(pick(R1, i1).mean()), random_same_tune=pct(pick(RN, i1).mean()),
             read_gap=pct((pick(R1, i1) - pick(RN, i1)).mean()), read_gap_clear=pct(clear(pick(R1, i1) - pick(RN, i1))),
             avg_vs_random=pct((Tw - pick(RN, ti)).mean()), random_best_tune=pct(pick(RN, tuned_idx(RN)).mean()),
             read1_lock=pct(pick(R1, i1, "lock").mean()), read1_rlock=pct(pick(R1, i1, "rlock").mean()),
             random_lock=pct(pick(RN, i1, "lock").mean()))
    OUT[cand] = r
    print(cand, json.dumps({k: v for k, v in r.items() if not isinstance(v, dict)}, default=str))
json.dump(OUT, open("analysis_v3.json", "w"), indent=1, default=str)
