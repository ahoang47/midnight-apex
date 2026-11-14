"""Baseline diagnosis for touge-lines-v1: why one fixed Touge tune fails at 20/30 turns.

Uses the G2 full-run npz (9 x 1000, no new races) plus live heat.py demand/wear
(same LINE_SET_C / tracks as the live sim). Writes diagnosis.json.
"""
from __future__ import annotations
import json, os, sys
from collections import Counter
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RETUNE = os.path.join(ROOT, "unapproved", "barry", "resources-v4", "retune")
sys.path.insert(0, os.path.join(ROOT, "sim"))
from velocity_shift import equations as E
from velocity_shift import combat as C
from velocity_shift import heat as H

M = json.load(open(os.path.join(RETUNE, "results_v4b_meta.json")))
TR = [tuple(t) for t in M["tracks"]]
DIST = np.array([d for d, _ in TR])
LAPS = M["laps"]
L = M["lengths"]
ST = M["styles"]
TUNES = np.array(M["tunes"])
NT, EV = 21, 21
KEYS = {k: i for i, k in enumerate(M["keys"])}
D = ("touge", "wangan", "street")
SIG = {"touge": ("HP", "ES", "DR")}  # signature corners (story/corner_lines.md); do not edit those lines
RES = ("POW", "HAN", "EN")


def pct(x):
    return round(100 * float(x), 1)


def r2(x):
    return round(float(x), 2)


def r3(x):
    return [round(float(v), 3) for v in x]


def r4(x):
    return [round(float(v), 4) for v in x]


def mix(x):
    x = np.asarray(x, float)
    return r3(x / x.sum())


Z = np.load(os.path.join(RETUNE, "results_v4b_G2_slant_m10.npz"))


def win_mean(mname):
    return Z[mname][..., KEYS["win"], :].mean(0)  # (15, 3, 3, 22)


def pick(mean, idx):
    return np.take_along_axis(mean, idx[..., None], -1)[..., 0]


def cell_tuned_idx(mean):
    return mean[..., :NT].argmax(-1)  # (15, 3, 3)


def district_fixed_idx(mean, d):
    """Single tune that maximises mean win over this district's tracks x lengths x styles."""
    m = mean[DIST == d][..., :NT].mean(axis=(0, 1, 2))  # (21,)
    return int(m.argmax()), r3(TUNES[int(m.argmax())]), pct(m.max())


def district_fixed_by_len_idx(mean, d, k):
    m = mean[DIST == d][:, k, :][..., :NT].mean(axis=(0, 1))
    return int(m.argmax()), r3(TUNES[int(m.argmax())]), pct(m.max())


def lock_pick(extra_key, idx):
    """idx is (15,3,3). extra arrays are (9,15,3,3,22,...) — take mean over batches then the tune."""
    A = Z[extra_key].mean(0)  # (15,3,3,22,...)
    # take along axis 3 (tune)
    sl = [slice(None)] * A.ndim
    # build advanced index
    out = np.take_along_axis(A, np.expand_dims(idx, axis=tuple(range(3, A.ndim))), 3)
    return np.squeeze(out, axis=3)


out = {
    "source": "results_v4b_G2_slant_m10.npz + live heat.py / LINE_SET_C / tracks_v1.json",
    "signature_touge_corners": list(SIG["touge"]),
    "note": "one-tune-per-district = argmax of mean win over that district's 5 tracks x 3 lengths x 3 styles (21-split grid).",
}

# ── corner mix ────────────────────────────────────────────────────────
corner_mix = {}
for ti, ((d, name), lap) in enumerate(zip(TR, LAPS)):
    c = Counter(lap)
    sig = SIG.get(d, ())
    n_sig = sum(c[k] for k in sig)
    corner_mix[name] = dict(
        district=d,
        lap=lap,
        counts={k: int(c[k]) for k in sorted(c)},
        signature_corners=n_sig,
        signature_share=r2(n_sig / 10),
        non_signature={k: int(c[k]) for k in sorted(c) if k not in sig},
    )
out["corner_mix"] = corner_mix

# ── demand / wear (live heat, q=HEAT_REF_Q=0.6) ──────────────────────
demand = {}
avg = H.avg_heat_demand()
out["avg_heat_demand"] = dict(POW_HAN_EN=r4(avg), mix=mix(avg), total=r2(sum(avg)))
# also raw average
raws, wears, finals = [], [], []
for (d, name), lap in zip(TR, LAPS):
    raw = H.raw_track_demand(d, lap)
    wear = H.track_wear(d, lap)
    final = tuple(raw[i] * wear[i] for i in range(3))
    raws.append(raw); wears.append(wear); finals.append(final)
    # per-corner contribution to raw
    per_c = {}
    for k in lap:
        cd = H.corner_demand(d, k)
        per_c.setdefault(k, r4(cd))
    demand[name] = dict(
        district=d,
        raw_POW_HAN_EN=r4(raw), raw_mix=mix(raw), raw_total=r2(sum(raw)),
        wear_POW_HAN_EN=r4(wear),
        after_wear_POW_HAN_EN=r4(final), after_wear_mix=mix(final), after_wear_total=r2(sum(final)),
        corner_demand_q06=per_c,
    )
out["demand_by_track"] = demand
# district means
for d in D:
    ix = [i for i, (dd, _) in enumerate(TR) if dd == d]
    raw_m = np.mean([raws[i] for i in ix], 0)
    fin_m = np.mean([finals[i] for i in ix], 0)
    out.setdefault("demand_by_district", {})[d] = dict(
        raw_mix=mix(raw_m), raw_POW_HAN_EN=r4(raw_m),
        after_wear_mix=mix(fin_m), after_wear_POW_HAN_EN=r4(fin_m),
    )

# counter mix of mains (what a perfect reader plays) and expected q=0.6 play
# is already in corner_demand. Also report main-line counter stance counts per track.
def stance_counts(letters):
    c = Counter(letters)
    return {s: c.get(s, 0) for s in "PEH"}


def counter_letter(ch):
    return {"E": "H", "H": "P", "P": "E"}[ch]


main_play = {}
for (d, name), lap in zip(TR, LAPS):
    mains = [C.line_triples(d, k)[0] for k in lap]
    counters = ["".join(counter_letter(ch) for ch in ln) for ln in mains]
    main_letters = "".join(mains)
    ctr_letters = "".join(counters)
    main_play[name] = dict(
        district=d,
        mains=mains,
        counters=counters,
        main_stance_counts=stance_counts(main_letters),
        counter_stance_counts=stance_counts(ctr_letters),
        main_mix=mix([main_letters.count(x) for x in "PHE"]),
        counter_mix=mix([ctr_letters.count(x) for x in "PHE"]),
        signature_mains=[(k, C.line_triples(d, k)[0]) for k in lap if k in SIG.get(d, ())],
    )
out["main_and_counter_mix"] = main_play

# ── win rates: per-race tuned vs district-fixed vs even ───────────────
win_tables = {}
for mname in ("avg_cap", "c8080", "perf_0.8", "perf_1.0", "best_cap", "greedy_cap",
              "read1_best", "read1_greedy", "rand_best", "rand_greedy"):
    mean = win_mean(mname)
    ti = cell_tuned_idx(mean)
    even = mean[..., EV]
    # district-fixed: one index per district, broadcast
    df_idx = np.zeros(mean.shape[:3], int)
    df_info = {}
    for d in D:
        i, split, _ = district_fixed_idx(mean, d)
        df_idx[DIST == d] = i
        df_info[d] = dict(tune_index=i, split_POW_HAN_EN=split)
    # wrong-district cell method (existing): best of other districts' tracks, same length & style
    wr_idx = np.zeros(mean.shape[:3], int)
    for ti_ in range(len(TR)):
        d = DIST[ti_]
        wr_idx[ti_] = mean[DIST != d][..., :NT].mean(0).argmax(-1)
    # wrong-district-fixed: each other district's single fixed tune; take the one that
    # was best on its own district (the player's "I brought my Street car to Touge").
    # Report mean win using each other district's fixed tune, and the worse of the two.
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
        # worse of the two other district tunes (mean over the district)
        worse = min(others, key=lambda od: rows[od]["all"])
        other_fixed[d] = dict(by_other=rows, worse_other=worse, worse_all=rows[worse]["all"])

    tw = pick(mean, ti)
    df = pick(mean, df_idx)
    wr = pick(mean, wr_idx)

    def slice_tab(x):
        return dict(
            all=pct(x.mean()),
            by_len={str(T): pct(x[:, k, :].mean()) for k, T in enumerate(L)},
            by_dist={d: pct(x[DIST == d].mean()) for d in D},
            by_dist_len={d: {str(T): pct(x[DIST == d][:, k, :].mean()) for k, T in enumerate(L)} for d in D},
        )

    # per-track (mean over styles) for touge especially
    per_track = {}
    for i, (d, name) in enumerate(TR):
        per_track[name] = dict(
            district=d,
            per_race_tuned={str(T): pct(tw[i, k].mean()) for k, T in enumerate(L)},
            district_fixed={str(T): pct(df[i, k].mean()) for k, T in enumerate(L)},
            even={str(T): pct(even[i, k].mean()) for k, T in enumerate(L)},
            best_tune_by_len={
                str(T): {
                    st: dict(split_POW_HAN_EN=r3(TUNES[ti[i, k, s]]), win=pct(mean[i, k, s, ti[i, k, s]]))
                    for s, st in enumerate(ST)
                }
                for k, T in enumerate(L)
            },
        )

    win_tables[mname] = dict(
        district_fixed_tunes=df_info,
        per_race_tuned=slice_tab(tw),
        district_fixed=slice_tab(df),
        even=slice_tab(even),
        wrong_cell=slice_tab(wr),
        wrong_district_fixed=other_fixed,
        gap_perrace_vs_even=pct((tw - even).mean()),
        gap_perrace_vs_wrongcell=pct((tw - wr).mean()),
        gap_distfixed_vs_even=pct((df - even).mean()),
        gap_perrace_vs_distfixed=pct((tw - df).mean()),
        gap_perrace_vs_distfixed_by_dist={d: pct((tw - df)[DIST == d].mean()) for d in D},
        gap_perrace_vs_distfixed_by_dist_len={
            d: {str(T): pct((tw - df)[DIST == d][:, k, :].mean()) for k, T in enumerate(L)} for d in D
        },
        per_track=per_track,
    )
out["win"] = win_tables

# ── best-tune variation on Touge ──────────────────────────────────────
mean = win_mean("avg_cap")
ti = cell_tuned_idx(mean)
var = {}
for d in D:
    ix = np.where(DIST == d)[0]
    splits = TUNES[ti[ix]]  # (5, 3, 3, 3)
    var[d] = dict(
        mean_split=r3(splits.reshape(-1, 3).mean(0)),
        # unique tunes used
        n_unique_tunes=int(len({tuple(np.round(s, 5)) for s in splits.reshape(-1, 3)})),
        by_track={
            TR[i][1]: {
                str(T): {st: r3(TUNES[ti[i, k, s]]) for s, st in enumerate(ST)}
                for k, T in enumerate(L)
            }
            for i in ix
        },
        by_track_mean={
            TR[i][1]: r3(TUNES[ti[i]].reshape(-1, 3).mean(0))
            for i in ix
        },
        by_len_mean={
            str(T): r3(TUNES[ti[ix][:, k, :]].reshape(-1, 3).mean(0))
            for k, T in enumerate(L)
        },
        # spread: max L1 distance between any two cell best-tunes
        max_l1=r2(max(
            np.abs(a - b).sum()
            for a in splits.reshape(-1, 3)
            for b in splits.reshape(-1, 3)
        )),
        # also best tune if forced one-per-track (mean over length x style)
        one_per_track={
            TR[i][1]: (lambda j: dict(split_POW_HAN_EN=r3(TUNES[j]), win_all=pct(mean[i][..., j].mean()),
                                      by_len={str(T): pct(mean[i, k, :, j].mean()) for k, T in enumerate(L)}))(
                int(mean[i][..., :NT].mean(axis=(0, 1)).argmax())
            )
            for i in ix
        },
    )
out["best_tune_variation"] = var

# ── lock-feel under district-fixed vs per-race (avg_cap) ──────────────
def feel_for(idx, tag):
    A = Z["avg_cap"].mean(0)  # (15,3,3,12,22)
    def metric(kname):
        sl = A[..., KEYS[kname], :]
        return pick(sl, idx)

    lock = metric("lock")
    rlock = metric("rlock")
    limp = metric("limp")
    lockdur = metric("lockdur")
    lr = lock_pick("avg_cap|lock_res", idx)  # (15,3,3,3) POW,HAN,EN lock counts
    # share of locks by bar
    lr_sum = lr.sum(axis=-1, keepdims=True)
    lr_share = np.divide(lr, np.maximum(lr_sum, 1e-12))

    def pack(x, extra=None):
        d = dict(
            all=pct(x.mean()) if extra is None else r2(x.mean()),
            by_len={str(T): (pct(x[:, k, :].mean()) if extra is None else r2(x[:, k, :].mean())) for k, T in enumerate(L)},
            by_dist={d: (pct(x[DIST == d].mean()) if extra is None else r2(x[DIST == d].mean())) for d in D},
            by_dist_len={
                d: {str(T): (pct(x[DIST == d][:, k, :].mean()) if extra is None else r2(x[DIST == d][:, k, :].mean()))
                    for k, T in enumerate(L)}
                for d in D
            },
            by_track_len={
                TR[i][1]: {str(T): (pct(x[i, k, :].mean()) if extra is None else r2(x[i, k, :].mean()))
                           for k, T in enumerate(L)}
                for i in range(len(TR))
            },
        )
        return d

    # locks_by_res shares
    def bar_share(arr):
        # arr (15,3,3,3)
        def sm(mask):
            s = arr[mask].sum(axis=tuple(range(arr[mask].ndim - 1))) if False else arr[mask].reshape(-1, 3).sum(0)
            return r3(s / max(s.sum(), 1e-12))
        # easier:
        def sm2(sub):
            s = sub.reshape(-1, 3).sum(0)
            return {res: pct(v) for res, v in zip(RES, s / max(s.sum(), 1e-12))}
        return dict(
            all=sm2(arr),
            by_dist={d: sm2(arr[DIST == d]) for d in D},
            by_dist_len={d: {str(T): sm2(arr[DIST == d][:, k, :]) for k, T in enumerate(L)} for d in D},
            by_track={TR[i][1]: {str(T): sm2(arr[i, k, :]) for k, T in enumerate(L)} for i in range(len(TR))},
        )

    return dict(
        tag=tag,
        corners_with_a_lock=pack(lock),
        counter_locked=pack(rlock),
        all_three_locked_clash_share=pack(limp),
        lock_duration=pack(lockdur, extra="r2"),
        locks_by_bar=bar_share(lr_share * 0 + lr),  # use counts not pre-normalized shares
    )


# rebuild idx
ti = cell_tuned_idx(win_mean("avg_cap"))
df_idx = np.zeros(ti.shape, int)
for d in D:
    i, _, _ = district_fixed_idx(win_mean("avg_cap"), d)
    df_idx[DIST == d] = i
even_idx = np.full(ti.shape, EV)

out["feel_avg_cap"] = dict(
    per_race_tuned=feel_for(ti, "per_race_tuned"),
    district_fixed=feel_for(df_idx, "district_fixed"),
    even=feel_for(even_idx, "even"),
)

# ── also: district-fixed tune's win curve vs each track (to see which tracks the fixed tune fails on)
mean = win_mean("avg_cap")
i_t, split_t, _ = district_fixed_idx(mean, "touge")
out["touge_fixed_tune_detail"] = dict(
    split_POW_HAN_EN=split_t,
    tune_index=i_t,
    # how this tune ranks on each cell (1 = best)
    rank_by_track_len_style={},
)
for i, (d, name) in enumerate(TR):
    if d != "touge":
        continue
    rows = {}
    for k, T in enumerate(L):
        for s, st in enumerate(ST):
            order = mean[i, k, s, :NT]
            rank = int((order > order[i_t]).sum() + 1)
            rows.setdefault(str(T), {})[st] = dict(
                win_fixed=pct(order[i_t]),
                win_best=pct(order.max()),
                best_split=r3(TUNES[order.argmax()]),
                rank_of_fixed=rank,
                gap_vs_best=pct(order.max() - order[i_t]),
            )
    out["touge_fixed_tune_detail"]["rank_by_track_len_style"][name] = rows

# ── corner-type demand for touge vs others (helps pick which mains to edit)
ctype = {}
for d in D:
    rows = {}
    for k in ("HP", "CR", "DR", "IR", "N90", "CH", "ES", "SW"):
        cd = H.corner_demand(d, k)
        main = C.line_triples(d, k)
        rows[k] = dict(
            lines=main,
            signature=(k in SIG.get(d, ())),
            demand_q06_POW_HAN_EN=r4(cd),
            demand_mix=mix(cd),
            count_on_district=int(sum(lap.count(k) for (dd, _), lap in zip(TR, LAPS) if dd == d)),
        )
    ctype[d] = rows
out["corner_type_demand"] = ctype

path = os.path.join(HERE, "diagnosis.json")
json.dump(out, open(path, "w"), indent=1)
print("wrote", path)
# short stdout summary
w = out["win"]["avg_cap"]
print("AVG 60/60 at cap")
print("  per-race tuned by dist/len", w["per_race_tuned"]["by_dist_len"])
print("  district-fixed by dist/len", w["district_fixed"]["by_dist_len"])
print("  district-fixed tunes", w["district_fixed_tunes"])
print("  even by dist/len", w["even"]["by_dist_len"])
print("TOUGE fixed", out["touge_fixed_tune_detail"]["split_POW_HAN_EN"])
print("best tune variation max L1", {d: var[d]["max_l1"] for d in D})
print("best tune by track mean", var["touge"]["by_track_mean"])
print("best tune by len mean", {d: var[d]["by_len_mean"] for d in D})
print("demand after wear", {d: out["demand_by_district"][d]["after_wear_mix"] for d in D})
print("raw demand", {d: out["demand_by_district"][d]["raw_mix"] for d in D})
