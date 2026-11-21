"""Analysis of results_v2.npz -> analysis_v2.json + tables_v2.md. All numbers are win/blocked percentages.
Tune choice per cell (track x length x style) uses the 9-batch mean; the clear test uses the 9 per-batch differences
(clear = mean difference >= 5 pp and all 9 batch differences with the same sign)."""
import json
import numpy as np

Z = np.load("results_v2.npz"); M = json.load(open("results_v2_meta.json"))
TR = [tuple(t) for t in M["tracks"]]; DIST = np.array([d for d, _ in TR]); D = ("touge", "wangan", "street")
L = M["lengths"]; NT = 21; EV = 21
W, BLK, BLKR, RB, LIMP = range(5)
GRID = np.array(M["tunes"][:NT])
out = {}; md = []


def pct(x): return round(100 * float(x), 1)


def tuned_idx(a):          # a: (9,15,3,3,5,22) -> best tune per cell (15,3,3)
    return a[:, :, :, :, W, :NT].mean(0).argmax(-1)


def pick(a, idx, k=W):     # -> (9,15,3,3)
    return np.take_along_axis(a[:, :, :, :, k, :], idx[None, ..., None], -1)[..., 0]


def lowdry_idx(a):
    m = a.mean(0); win = m[..., W, :NT]; blk = m[..., BLK, :NT]
    sc = np.where(blk <= 0.15, win, -1 + 0 * win)
    fb = blk.argmin(-1); best = sc.argmax(-1)
    return np.where((blk <= 0.15).any(-1), best, fb)


def wrong_idx(a):          # best tune of the other two districts (mean curve over their tracks), same length & style
    m = a.mean(0)[..., W, :NT]  # (15,3,3,21)
    idx = np.zeros(m.shape[:3], int)
    for ti, (d, _) in enumerate(TR):
        oth = m[DIST != d].mean(0)
        idx[ti] = oth.argmax(-1)
    return idx


def clear(diff):           # diff (9,15,3,3) -> fraction of cells clear
    mu = diff.mean(0); s = np.sign(diff)
    same = (s == s[0:1]).all(0) & (s[0] != 0)
    return float(((mu >= 0.05) & same).mean())


def even_idx(a): return np.full(a.shape[1:4], EV)


CANDS = list(M["candidates"])
md.append("# resources-v2 tables (full runs: 9 batches x 1000 races, 15 laps x 10/20/30 turns x 3 boss styles)\n")
md.append("## Combat targets and block rates (average play at the cap; perfect play at 0.8 / 1.0)\n")
md.append("| Candidate | Perfect 0.8 tuned | low-dry | even | Perfect 1.0 tuned | even | Avg cap tuned | low-dry | even | Tuned: races with a block | races with a read blocked | read corners blocked | Even: races blocked | Wrong-district: races blocked | Low-dry: races blocked |")
md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for c in CANDS:
    A = Z[f"{c}|avg_cap"]; P8 = Z[f"{c}|perf_0.8"]; P1 = Z[f"{c}|perf_1.0"]
    ti, li, wi = tuned_idx(A), lowdry_idx(A), wrong_idx(A)
    r = dict(
        perf08_tuned=pct(pick(P8, tuned_idx(P8)).mean()), perf08_lowdry=pct(pick(P8, lowdry_idx(P8)).mean()), perf08_even=pct(P8[..., W, EV].mean()),
        perf10_tuned=pct(pick(P1, tuned_idx(P1)).mean()), perf10_even=pct(P1[..., W, EV].mean()),
        avg_tuned=pct(pick(A, ti).mean()), avg_lowdry=pct(pick(A, li).mean()), avg_even=pct(A[..., W, EV].mean()),
        blk_tuned=pct(pick(A, ti, BLK).mean()), blkr_tuned=pct(pick(A, ti, BLKR).mean()), rb_tuned=pct(pick(A, ti, RB).mean()),
        limp_tuned=pct(pick(A, ti, LIMP).mean()),
        blk_even=pct(A[..., BLK, EV].mean()), rb_even=pct(A[..., RB, EV].mean()), blk_wrong=pct(pick(A, wi, BLK).mean()), rb_wrong=pct(pick(A, wi, RB).mean()),
        blk_lowdry=pct(pick(A, li, BLK).mean()), rb_lowdry=pct(pick(A, li, RB).mean()),
        perf10_blk_tuned=pct(pick(P1, tuned_idx(P1), BLK).mean()), perf10_rb_tuned=pct(pick(P1, tuned_idx(P1), RB).mean()),
        blk_tuned_by_len={L[k]: pct(pick(A, ti, BLK)[:, :, k].mean()) for k in range(3)},
        rb_tuned_by_len={L[k]: pct(pick(A, ti, RB)[:, :, k].mean()) for k in range(3)},
        blk_even_by_len={L[k]: pct(A[:, :, k, :, BLK, EV].mean()) for k in range(3)},
        blk_wrong_by_len={L[k]: pct(pick(A, wi, BLK)[:, :, k].mean()) for k in range(3)},
        cells_tuned_blk_le15=pct((pick(A, ti, BLK).mean(0) <= 0.15).mean()),
        cells_tuned_rb_le5=pct((pick(A, ti, RB).mean(0) <= 0.05).mean()),
        cells_with_lowdry_tune=pct((A.mean(0)[..., BLK, :NT] <= 0.15).any(-1).mean()),
    )
    # retune gaps (average play at cap)
    T_ = pick(A, ti); Ev = A[..., W, EV]; Wr = pick(A, wi); Ld = pick(A, li)
    r.update(gap_even=pct((T_ - Ev).mean()), gap_wrong=pct((T_ - Wr).mean()),
             clear_even=pct(clear(T_ - Ev)), clear_wrong=pct(clear(T_ - Wr)),
             gap_wrong_max_cell=pct((T_ - Wr).mean(0).max()),
             lowdry_gap_even=pct((Ld - Ev).mean()), lowdry_clear_even=pct(clear(Ld - Ev)),
             gap_even_by_len={L[k]: pct((T_ - Ev)[:, :, k].mean()) for k in range(3)},
             gap_wrong_by_len={L[k]: pct((T_ - Wr)[:, :, k].mean()) for k in range(3)})
    for d in D:
        s = DIST == d
        r[f"tuned_{d}"] = pct(T_[:, s].mean()); r[f"even_{d}"] = pct(Ev[:, s].mean())
        r[f"gap_even_{d}"] = pct((T_ - Ev)[:, s].mean()); r[f"gap_wrong_{d}"] = pct((T_ - Wr)[:, s].mean())
        r[f"gap_wrong_max_{d}"] = pct((T_ - Wr)[:, s].mean(0).max()); r[f"clear_wrong_{d}"] = pct(clear((T_ - Wr)[:, s]))
        r[f"clear_even_{d}"] = pct(clear((T_ - Ev)[:, s]))
        r[f"blk_tuned_{d}"] = pct(pick(A, ti, BLK)[:, s].mean())
        r[f"tuned_split_{d}"] = np.round(GRID[ti[s]].reshape(-1, 3).mean(0), 3).tolist()
    # live-read measures (only main candidates)
    if f"{c}|read1_cap" in Z.files:
        R1 = Z[f"{c}|read1_cap"]; RN = Z[f"{c}|random_cap"]; NR = Z[f"{c}|noration_cap"]; US = Z[f"{c}|unscouted_cap"]
        B1 = Z[f"{c}|b1_scouted_cap"]; B1u = Z[f"{c}|b1_unscouted_cap"]
        i1 = tuned_idx(R1)
        r.update(read1_tuned=pct(pick(R1, i1).mean()), random_same_tune=pct(pick(RN, i1).mean()), random_best_tune=pct(pick(RN, tuned_idx(RN)).mean()),
                 read_gap=pct((pick(R1, i1) - pick(RN, i1)).mean()), read_gap_clear=pct(clear(pick(R1, i1) - pick(RN, i1))),
                 avg_vs_random_gap=pct((T_ - pick(RN, ti)).mean()),
                 random_blk=pct(pick(RN, i1, BLK).mean()), read1_blk=pct(pick(R1, i1, BLK).mean()), read1_rb=pct(pick(R1, i1, RB).mean()),
                 pacing_gap=pct((T_ - pick(NR, ti)).mean()), pacing_gap_maxabs_cell=pct(np.abs((T_ - pick(NR, ti)).mean(0)).max()),
                 scout_b03=pct((T_ - pick(US, ti)).mean()), scout_b03_clear=pct(clear(T_ - pick(US, ti))),
                 scout_b1=pct((pick(B1, tuned_idx(B1)) - pick(B1u, tuned_idx(B1))).mean()),
                 scout_b1_clear=pct(clear(pick(B1, tuned_idx(B1)) - pick(B1u, tuned_idx(B1)))),
                 scout_b1_by_style={s: pct((pick(B1, tuned_idx(B1)) - pick(B1u, tuned_idx(B1)))[:, :, :, k].mean()) for k, s in enumerate(M["styles"])},
                 scout_b03_by_style={s: pct((T_ - pick(US, ti))[:, :, :, k].mean()) for k, s in enumerate(M["styles"])})
    out[c] = r
    md.append(f"| {c} | {r['perf08_tuned']} | {r['perf08_lowdry']} | {r['perf08_even']} | {r['perf10_tuned']} | {r['perf10_even']} | {r['avg_tuned']} | {r['avg_lowdry']} | {r['avg_even']} | {r['blk_tuned']} | {r['blkr_tuned']} | {r['rb_tuned']} | {r['blk_even']} | {r['blk_wrong']} | {r['blk_lowdry']} |")

# live model read gap (card draw, r 1.05, average QTE; tune = best per cell for q_read 1; the live model has no boss style)
LR, LA, LN = Z["live_read1"], Z["live_avg"], Z["live_random"]
li_ = LR.mean(0).argmax(-1)   # (15,3)
pk = lambda a, i: np.take_along_axis(a, i[None, ..., None], -1)[..., 0]
out["live"] = dict(read1_tuned=pct(pk(LR, li_).mean()), random_same_tune=pct(pk(LN, li_).mean()), read_gap=pct((pk(LR, li_) - pk(LN, li_)).mean()),
                   avg_tuned=pct(pk(LA, LA.mean(0).argmax(-1)).mean()), avg_vs_random_gap=pct((pk(LA, LA.mean(0).argmax(-1)) - pk(LN, LA.mean(0).argmax(-1))).mean()),
                   read1_even=pct(LR[..., EV].mean()), random_even=pct(LN[..., EV].mean()))
json.dump(out, open("analysis_v2.json", "w"), indent=1)

def tab(title, keys, labels):
    md.append(f"\n## {title}\n"); md.append("| Candidate | " + " | ".join(labels) + " |"); md.append("|---|" + "---|" * len(labels))
    for c in CANDS:
        md.append(f"| {c} | " + " | ".join(str(out[c].get(k, "n/a")) for k in keys) + " |")

tab("Retune gap (average play at the cap)", ["gap_even", "clear_even", "gap_wrong", "clear_wrong", "gap_wrong_max_cell", "lowdry_gap_even", "lowdry_clear_even"],
    ["Tuned - even (pp)", "% cells clear", "Tuned - wrong district (pp)", "% cells clear", "Worst cell wrong-district penalty", "Low-dry tune - even", "% cells clear"])
tab("By district (average play at the cap)", [f"{k}_{d}" for d in D for k in ("tuned", "gap_even", "gap_wrong", "gap_wrong_max", "blk_tuned")],
    [f"{d} {k}" for d in D for k in ("tuned win", "gap vs even", "gap vs wrong", "worst wrong", "tuned blocked")])
tab("Block rates by race length (average play at the cap, % of races with any wanted stance blocked)",
    [f"{k}" for k in ("blk_tuned_by_len", "rb_tuned_by_len", "blk_even_by_len", "blk_wrong_by_len", "gap_even_by_len", "gap_wrong_by_len")],
    ["Tuned blocked", "Tuned read corners blocked", "Even blocked", "Wrong blocked", "Gap vs even", "Gap vs wrong"])
tab("Cells", ["cells_tuned_blk_le15", "cells_tuned_rb_le5", "cells_with_lowdry_tune", "perf10_blk_tuned", "perf10_rb_tuned", "limp_tuned"],
    ["% cells where the max-win tune is blocked in <=15% of races", "% cells read-blocked <=5%", "% cells where some tune is blocked <=15%", "Perfect 1.0 tuned races blocked", "Perfect 1.0 read corners blocked", "Tuned clashes in limp (%)"])
md.append("\n## Reads vs pacing vs scouting (average QTE at the cap, tuned car)\n")
md.append("| Candidate | Perfect reads (q 1) | Random stances, same tune | Read gap | % cells clear | Avg (q 0.6) - random | Pacing gap (rationing - greedy) | Largest cell pacing effect | Scouting value, style blend 0.3 | Scouting value, style blend 1.0 | % cells clear (1.0) |")
md.append("|---|---|---|---|---|---|---|---|---|---|---|")
for c in CANDS:
    r = out[c]
    if "read_gap" in r:
        md.append(f"| {c} | {r['read1_tuned']} | {r['random_same_tune']} | {r['read_gap']} | {r['read_gap_clear']} | {r['avg_vs_random_gap']} | {r['pacing_gap']} | {r['pacing_gap_maxabs_cell']} | {r['scout_b03']} | {r['scout_b1']} | {r['scout_b1_clear']} |")
lv = out["live"]
md.append(f"| live model (card draw, r 1.05) | {lv['read1_tuned']} | {lv['random_same_tune']} | {lv['read_gap']} | | {lv['avg_vs_random_gap']} | | | | | |")
open("tables_v2.md", "w").write("\n".join(md) + "\n")
print("\n".join(md))
