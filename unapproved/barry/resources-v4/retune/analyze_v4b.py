"""Analysis of results_v4_<CAND>.npz -> analysis_v4b.json.
Tune choice per cell (track x length x style) uses the 9-batch mean win; the clear test uses the 9 per-batch differences
(clear = mean difference >= 5 pp and all 9 batch differences with the same sign).
Per-district averages index tracks by district name (fixes the v3 q8080 NaN bug, where the district test compared a
(district, name) tuple to a string and averaged an empty selection).
Usage: python3 analyze_v4.py CAND [CAND ...]"""
import json, sys
import numpy as np

M = json.load(open("results_v4b_meta.json"))
TR = [tuple(t) for t in M["tracks"]]; DIST = np.array([d for d, _ in TR]); D = ("touge", "wangan", "street")
L = M["lengths"]; NT = 21; EV = 21
K = {k: i for i, k in enumerate(M["keys"])}
GRID = np.array(M["tunes"][:NT])
try:
    OUT = json.load(open("analysis_v4b.json"))
except FileNotFoundError:
    OUT = {}


def pct(x): return round(100 * float(x), 1)
def r2(x): return round(float(x), 2)
def tuned_idx(a): return a[..., K["win"], :NT].mean(0).argmax(-1)
def pick(a, idx, k="win"): return np.take_along_axis(a[..., K[k], :], idx[None, ..., None], -1)[..., 0]
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


def by_len(x): return {T: pct(x[:, :, k_].mean()) for k_, T in enumerate(L)}
def by_dist(x): return {d: pct(x[:, DIST == d].mean()) for d in D}


def gap(A_, B_):
    d = A_ - B_
    return dict(gap=pct(d.mean()), clear=pct(clear(d)), neg_clear=pct(clear(-d)), by_len={T: pct(d[:, :, k_].mean()) for k_, T in enumerate(L)},
                by_len_clear={T: pct(clear(d[:, :, k_])) for k_, T in enumerate(L)}, max_cell=pct(np.abs(d.mean(0)).max()))


def feel(Z, mname, idx):
    A = Z[mname]; s = {}
    for k in ("ov", "ovc", "lock", "pen", "rlock", "rov", "rovplay", "rswitch", "limp"):
        s[k] = pct(pick(A, idx, k).mean())
    s["streak_mean"] = r2(pick(A, idx, "streak").mean())
    ovc = pick(A, idx, "ovc").mean(); s["pen_per_overrun_clash"] = pct(pick(A, idx, "pen").mean() / max(ovc, 1e-9))
    if f"{mname}|n_locks" in Z:
        nl = pick_x(Z[f"{mname}|n_locks"], idx).sum(); du = pick_x(Z[f"{mname}|dur"], idx).sum()
        s["lock_dur_mean"] = r2(du / max(nl, 1))
        h = pick_x(Z[f"{mname}|hist"], idx).sum((0, 1, 2, 3)); h = h / max(h.sum(), 1)
        s["lock_dur_share"] = {"0": pct(h[0]), "1": pct(h[1]), "2": pct(h[2]), "3": pct(h[3]), "4+": pct(h[4:].sum())}
        s["locks_per_race"] = r2(nl / (9 * M["n"] * idx.size))
        lr = pick_x(Z[f"{mname}|lock_res"], idx).sum((0, 1, 2, 3)); s["locks_by_res_pow_han_en"] = [pct(x) for x in lr / max(lr.sum(), 1)]
        lt = pick_x(Z[f"{mname}|lock_t"], idx).mean(0)   # (15,3,3,30)
        s["lock_by_lap_30turn"] = [pct(lt[:, 2, :, 10 * j:10 * j + 10].mean()) for j in range(3)]
    for k in ("lock", "rlock", "ovc"):
        s[f"{k}_by_len"] = by_len(pick(A, idx, k)); s[f"{k}_by_dist"] = by_dist(pick(A, idx, k))
    s["lockdur_by_len"] = {T: r2(pick(A, idx, "lockdur")[:, :, k_].mean()) for k_, T in enumerate(L)}
    return s


for cand in sys.argv[1:]:
    Z = np.load(f"results_v4b_{cand}.npz")
    r = dict(cfg=M["candidates"][cand])
    A = Z["avg_cap"]; ti, wi, ei = tuned_idx(A), wrong_idx(A), even_idx(A)
    combat = {}
    for m in ("perf_0.8", "perf_1.0", "avg_cap", "c8080", "best_cap", "greedy_cap", "read1_best", "read1_greedy"):
        X = Z[m]; i_ = tuned_idx(X); tw = pick(X, i_); ev = X[..., K["win"], EV]
        combat[m] = dict(tuned=pct(tw.mean()), even=pct(ev.mean()), tuned_by_len=by_len(tw), even_by_len=by_len(ev),
                         tuned_by_dist=by_dist(tw), even_by_dist=by_dist(ev),
                         tuned_2030=pct(tw[:, :, 1:].mean()), even_2030=pct(ev[:, :, 1:].mean()))
    combat["avg_cap"]["wrong"] = pct(pick(A, wi).mean()); combat["avg_cap"]["wrong_by_len"] = by_len(pick(A, wi))
    r["combat"] = combat
    Tw, Ev, Wr = pick(A, ti), A[..., K["win"], EV], pick(A, wi)
    r["retune_even"] = gap(Tw, Ev); r["retune_wrong"] = gap(Tw, Wr)
    r["retune_by_dist"] = {d: dict(even=pct((Tw - Ev)[:, DIST == d].mean()), even_clear=pct(clear((Tw - Ev)[:, DIST == d])),
                                   wrong=pct((Tw - Wr)[:, DIST == d].mean()), wrong_clear=pct(clear((Tw - Wr)[:, DIST == d])),
                                   tuned_split=np.round(GRID[ti[DIST == d]].reshape(-1, 3).mean(0), 3).tolist()) for d in D}
    wc = np.unravel_index((Tw - Wr).mean(0).argmax(), Tw.shape[1:])
    r["worst_wrong_cell"] = dict(track=TR[wc[0]][1], length=L[wc[1]], style=M["styles"][wc[2]], gap=pct((Tw - Wr).mean(0)[wc]),
                                 tuned_split=GRID[ti[wc]].tolist(), tuned_win=pct(Tw.mean(0)[wc]), wrong_split=GRID[wi[wc]].tolist(), wrong_win=pct(Wr.mean(0)[wc]))
    # skill split
    def tw_(m): X = Z[m]; return pick(X, tuned_idx(X))
    R1b, R1g = Z["read1_best"], Z["read1_greedy"]
    i1b, i1g = tuned_idx(R1b), tuned_idx(R1g)
    r["reads_best_pacing"] = gap(pick(R1b, i1b), pick(Z["rand_best"], i1b))            # perfect read vs random guess, both best pacing, same tune
    r["reads_greedy"] = gap(pick(R1g, i1g), pick(Z["rand_greedy"], i1g))
    r["reads_avg_vs_perfect"] = gap(tw_("read1_best"), tw_("best_cap"))                 # q 1.0 vs q 0.6, both best pacing
    r["pacing_q06"] = gap(tw_("best_cap"), tw_("greedy_cap"))                           # best pacing vs greedy at read 0.6
    r["pacing_q1"] = gap(tw_("read1_best"), tw_("read1_greedy"))
    r["pacing_avg_vs_greedy"] = gap(Tw, tw_("greedy_cap"))                              # 60% pacing vs greedy at read 0.6
    r["random_best_win"] = pct(pick(Z["rand_best"], i1b).mean()); r["random_greedy_win"] = pct(pick(Z["rand_greedy"], i1g).mean())
    r["ratio_pacing_q06_over_reads"] = round(r["pacing_q06"]["gap"] / max(r["reads_best_pacing"]["gap"], 1e-9), 3)
    r["ratio_pacing_q1_over_reads"] = round(r["pacing_q1"]["gap"] / max(r["reads_best_pacing"]["gap"], 1e-9), 3)
    r["feel_avg_tuned"] = feel(Z, "avg_cap", ti); r["feel_avg_even"] = feel(Z, "avg_cap", ei)
    r["feel_best_tuned"] = feel(Z, "best_cap", tuned_idx(Z["best_cap"])); r["feel_greedy_tuned"] = feel(Z, "greedy_cap", tuned_idx(Z["greedy_cap"]))
    r["feel_perf10_tuned"] = feel(Z, "perf_1.0", tuned_idx(Z["perf_1.0"]))
    OUT[cand] = r
    print(cand, json.dumps({k: v for k, v in r.items() if not isinstance(v, dict)}, default=str))
    print(json.dumps(r["combat"]["avg_cap"]), json.dumps(r["pacing_q06"]), json.dumps(r["reads_best_pacing"]))
json.dump(OUT, open("analysis_v4b.json", "w"), indent=1, default=str)
