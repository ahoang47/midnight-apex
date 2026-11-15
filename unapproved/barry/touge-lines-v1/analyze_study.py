"""Analyze results_<tag>.npz -> analysis.json (merge by tag)."""
from __future__ import annotations
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
META = json.load(open(os.path.join(HERE, "results_meta.json")))
D = ("touge", "wangan", "street")
OUT_PATH = os.path.join(HERE, "analysis.json")
try:
    OUT = json.load(open(OUT_PATH))
except FileNotFoundError:
    OUT = {}


def pct(x):
    return round(100 * float(x), 1)


def r2(x):
    return round(float(x), 2)


def r3(x):
    return [round(float(v), 3) for v in x]


def analyze(tag):
    M = META[tag]
    TR = [tuple(t) for t in M["tracks"]]
    DIST = np.array([d for d, _ in TR])
    L = M["lengths"]
    ST = M["styles"]
    TUNES = np.array(M["tunes"])
    NT, EV = 21, 21
    K = {k: i for i, k in enumerate(M["keys"])}
    n_batch = len(M["seeds"])
    Z = np.load(os.path.join(HERE, f"results_{tag}.npz"))

    def win_mean(mname):
        return Z[mname][..., K["win"], :].mean(0)

    def pick(mean, idx):
        return np.take_along_axis(mean, idx[..., None], -1)[..., 0]

    def cell_tuned(mean):
        return mean[..., :NT].argmax(-1)

    def dist_fixed(mean, d):
        m = mean[DIST == d][..., :NT].mean(axis=(0, 1, 2))
        i = int(m.argmax())
        return i, r3(TUNES[i]), pct(m.max())

    def slice_tab(x):
        return dict(
            all=pct(x.mean()),
            by_len={str(T): pct(x[:, k, :].mean()) for k, T in enumerate(L)},
            by_dist={d: pct(x[DIST == d].mean()) for d in D},
            by_dist_len={d: {str(T): pct(x[DIST == d][:, k, :].mean()) for k, T in enumerate(L)} for d in D},
        )

    def wrong_idx(mean):
        idx = np.zeros(mean.shape[:3], int)
        for ti, (d, _) in enumerate(TR):
            idx[ti] = mean[DIST != d][..., :NT].mean(0).argmax(-1)
        return idx

    def feel(idx):
        A = Z["avg_cap"].mean(0)

        def met(kname):
            return pick(A[..., K[kname], :], idx)

        lr = Z["avg_cap|lock_res"].mean(0)  # (tracks, len, style, tune, 3)
        lr = np.take_along_axis(lr, idx[..., None, None], 3)[..., 0, :]

        def pack(x, as_pct=True):
            f = pct if as_pct else r2
            return dict(
                all=f(x.mean()),
                by_len={str(T): f(x[:, k, :].mean()) for k, T in enumerate(L)},
                by_dist={d: f(x[DIST == d].mean()) for d in D},
                by_dist_len={d: {str(T): f(x[DIST == d][:, k, :].mean()) for k, T in enumerate(L)} for d in D},
                by_track={TR[i][1]: {str(T): f(x[i, k, :].mean()) for k, T in enumerate(L)} for i in range(len(TR))},
            )

        def bar(sub):
            s = sub.reshape(-1, 3).sum(0)
            return {r: pct(v) for r, v in zip(("POW", "HAN", "EN"), s / max(s.sum(), 1e-12))}

        return dict(
            corners_with_a_lock=pack(met("lock")),
            counter_locked=pack(met("rlock")),
            all_three_locked_clash_share=pack(met("limp")),
            lock_duration=pack(met("lockdur"), as_pct=False),
            locks_by_bar=dict(
                all=bar(lr),
                by_dist={d: bar(lr[DIST == d]) for d in D},
                by_dist_len={d: {str(T): bar(lr[DIST == d][:, k, :]) for k, T in enumerate(L)} for d in D},
                by_track={TR[i][1]: {str(T): bar(lr[i, k, :]) for k, T in enumerate(L)} for i in range(len(TR))},
            ),
        )

    win = {}
    for mname in ("avg_cap", "c8080", "perf_0.8", "perf_1.0", "best_cap", "greedy_cap",
                  "read1_best", "read1_greedy", "rand_best", "rand_greedy"):
        if mname not in Z.files:
            continue
        mean = win_mean(mname)
        ti = cell_tuned(mean)
        even = mean[..., EV]
        df_idx = np.zeros(mean.shape[:3], int)
        df_info = {}
        for d in D:
            i, split, _ = dist_fixed(mean, d)
            df_idx[DIST == d] = i
            df_info[d] = dict(tune_index=i, split_POW_HAN_EN=split)
        wr = wrong_idx(mean)
        tw, dfw, ev, ww = pick(mean, ti), pick(mean, df_idx), even, pick(mean, wr)
        per_track = {}
        for i, (d, name) in enumerate(TR):
            per_track[name] = dict(
                district=d,
                per_race_tuned={str(T): pct(tw[i, k].mean()) for k, T in enumerate(L)},
                district_fixed={str(T): pct(dfw[i, k].mean()) for k, T in enumerate(L)},
                even={str(T): pct(ev[i, k].mean()) for k, T in enumerate(L)},
                best_tune_by_len={
                    str(T): {st: dict(split_POW_HAN_EN=r3(TUNES[ti[i, k, s]]), win=pct(mean[i, k, s, ti[i, k, s]]))
                             for s, st in enumerate(ST)}
                    for k, T in enumerate(L)
                },
            )
        other_fixed = {}
        for d in D:
            others = [od for od in D if od != d]
            rows = {}
            for od in others:
                oi = df_info[od]["tune_index"]
                w = mean[DIST == d][..., oi]
                rows[od] = dict(split_POW_HAN_EN=df_info[od]["split_POW_HAN_EN"],
                                all=pct(w.mean()),
                                by_len={str(T): pct(w[:, k, :].mean()) for k, T in enumerate(L)})
            worse = min(others, key=lambda od: rows[od]["all"])
            other_fixed[d] = dict(by_other=rows, worse_other=worse, worse_all=rows[worse]["all"])
        # Touge/Wangan/Street: gap between directions or layouts at the district-fixed tune
        dir_gap = {}
        for d in D:
            names = [TR[i][1] for i in range(len(TR)) if DIST[i] == d]
            if len(names) >= 2:
                rates = {nm: per_track[nm]["district_fixed"] for nm in names}
                # max spread at each length (mean over styles already in district_fixed)
                spread = {str(T): round(max(rates[nm][str(T)] for nm in names) - min(rates[nm][str(T)] for nm in names), 1)
                          for T in L}
                dir_gap[d] = dict(rates=rates, spread_by_len=spread, max_spread=max(spread.values()))
        win[mname] = dict(
            district_fixed_tunes=df_info,
            per_race_tuned=slice_tab(tw),
            district_fixed=slice_tab(dfw),
            even=slice_tab(ev),
            wrong_cell=slice_tab(ww),
            wrong_district_fixed=other_fixed,
            gap_perrace_vs_even=pct((tw - ev).mean()),
            gap_perrace_vs_wrongcell=pct((tw - ww).mean()),
            gap_distfixed_vs_even=pct((dfw - ev).mean()),
            gap_perrace_vs_distfixed=pct((tw - dfw).mean()),
            gap_perrace_vs_distfixed_by_dist={d: pct((tw - dfw)[DIST == d].mean()) for d in D},
            gap_perrace_vs_distfixed_by_dist_len={
                d: {str(T): pct((tw - dfw)[DIST == d][:, k, :].mean()) for k, T in enumerate(L)} for d in D
            },
            vs_wangan_street_fixed={
                "touge_minus_wangan_by_len": {str(T): round(slice_tab(dfw)["by_dist_len"]["touge"][str(T)] - slice_tab(dfw)["by_dist_len"]["wangan"][str(T)], 1) for T in L},
                "touge_minus_street_by_len": {str(T): round(slice_tab(dfw)["by_dist_len"]["touge"][str(T)] - slice_tab(dfw)["by_dist_len"]["street"][str(T)], 1) for T in L},
            },
            direction_or_layout_spread_fixed=dir_gap,
            per_track=per_track,
        )

    skill = {}
    if all(m in Z.files for m in ("read1_best", "rand_best", "best_cap", "greedy_cap")):
        def tw_(m):
            mean = win_mean(m)
            return pick(mean, cell_tuned(mean))
        # For skill split, use each measure's own per-cell tune, and also district-fixed from avg_cap
        r1, rb = tw_("read1_best"), tw_("rand_best")
        # rand_best should use the same tune as read1_best for a fair reads gap (v4b did this)
        mean_r1 = win_mean("read1_best")
        i1 = cell_tuned(mean_r1)
        r1s = pick(mean_r1, i1)
        rbs = pick(win_mean("rand_best"), i1)
        b = tw_("best_cap"); g = tw_("greedy_cap")
        # pacing at read 0.6: best - greedy, each on its own best tune? v4b used each measure's tuned_idx
        # Actually v4b: gap(pick(best), pick(greedy)) with each's own tuned_idx — slightly inconsistent but match it.
        # reads: pick(read1_best, i1b) - pick(rand_best, i1b) same tune
        def gap_tab(A, B):
            d = A - B
            return dict(all=pct(d.mean()),
                        by_len={str(T): pct(d[:, k, :].mean()) for k, T in enumerate(L)},
                        by_dist={dd: pct(d[DIST == dd].mean()) for dd in D})
        skill = dict(
            reads_best_pacing=gap_tab(r1s, rbs),
            pacing_q06=gap_tab(b, g),
            random_best_win=pct(rbs.mean()),
            ratio_pacing_over_reads=round(float((b - g).mean() / max((r1s - rbs).mean(), 1e-9)), 3),
        )

    feel_out = {}
    if "avg_cap" in Z.files:
        mean = win_mean("avg_cap")
        ti = cell_tuned(mean)
        df_idx = np.zeros(ti.shape, int)
        for d in D:
            i, _, _ = dist_fixed(mean, d)
            df_idx[DIST == d] = i
        feel_out = dict(per_race_tuned=feel(ti), district_fixed=feel(df_idx),
                        even=feel(np.full(ti.shape, EV)))

    return dict(
        n=M["n"], n_seeds=n_batch, n_tracks=len(TR), tracks=M["tracks"],
        use_gravity=M.get("use_gravity"), line_edits=M.get("line_edits"),
        gravity=M.get("gravity"),
        win=win, skill=skill, feel_avg_cap=feel_out,
    )


if __name__ == "__main__":
    tags = sys.argv[1:] or list(META)
    for tag in tags:
        OUT[tag] = analyze(tag)
        w = OUT[tag]["win"].get("avg_cap", {})
        print(tag, "avg_cap district-fixed", w.get("district_fixed", {}).get("by_dist_len"))
        print(tag, "avg_cap per-race     ", w.get("per_race_tuned", {}).get("by_dist_len"))
        print(tag, "tunes", w.get("district_fixed_tunes"))
        print(tag, "touge vs W/S", w.get("vs_wangan_street_fixed"))
    json.dump(OUT, open(OUT_PATH, "w"), indent=1)
    print("wrote", OUT_PATH)
