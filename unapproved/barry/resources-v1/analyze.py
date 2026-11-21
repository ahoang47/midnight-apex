"""Turn results.json into the numbers and tables in RESULTS.md (writes analysis.json and tables.md)."""
from __future__ import annotations
import json, itertools
from collections import Counter, defaultdict
import numpy as np
import resources_v1 as R

res = json.load(open("results.json"))
META = res["meta"]
TUNES = np.array(META["tunes"]); NT = len(TUNES) - 1; EV = NT
LENGTHS = (10, 20, 30); STYLES = R.STYLES
TR = R.tracks(); TK = list(TR)
FIRST = [k for k in TK if k[1][1] == "1"]
DIST = ("touge", "wangan", "street")
CLEAR = 5.0


def nk(tk, T, st, kind, r, var="base", sc=True):
    return f"{tk[0]}/{tk[1]}|{T}|{st}|{kind}|{r}|{var}|{sc}"


def ok(tk, T, kind, r):
    return f"{tk[0]}/{tk[1]}|{T}|{kind}|{r}"


def W(k, src="new"):
    return 100 * np.array(res[src][k])          # (9 batches, tunes) in %


def tn(i):
    p, h, e = TUNES[i]
    return "even" if i == EV else f"P{round(100*p)}/H{round(100*h)}/E{round(100*e)}"


def diff_stats(Wc, i, j):
    """pooled diff (pp) and whether it is 'clear' (>= 5 pp, same sign in all 9 batches)."""
    d = Wc[:, i] - Wc[:, j]
    m = float(d.mean())
    return m, bool(abs(m) >= CLEAR and (np.all(d > 0) or np.all(d < 0)))


A = {}
L = []   # markdown lines

# ───────────── (a) retune gap at the cap, average play ─────────────
cells = {}
for tk, T, st in itertools.product(TK, LENGTHS, STYLES):
    cells[(tk, T, st)] = W(nk(tk, T, st, "average", 1.05))
rows = []
for (tk, T, st), Wc in cells.items():
    pooled = Wc.mean(0)
    b = int(np.argmax(pooled[:NT]))
    g_even, c_even = diff_stats(Wc, b, EV)
    oth_t = np.mean([cells[(t2, T, st)].mean(0)[:NT] for t2 in TK if t2 != tk], axis=0)
    j1 = int(np.argmax(oth_t)); g_ot, c_ot = diff_stats(Wc, b, j1)
    oth_d = np.mean([cells[(t2, T, st)].mean(0)[:NT] for t2 in TK if t2[0] != tk[0]], axis=0)
    j2 = int(np.argmax(oth_d)); g_od, c_od = diff_stats(Wc, b, j2)
    worst = int(np.argmin(pooled[:NT]))
    rows.append(dict(track=tk, T=T, style=st, best=tn(b), best_wr=float(pooled[b]), even_wr=float(pooled[EV]),
                     worst=tn(worst), worst_wr=float(pooled[worst]),
                     gap_even=g_even, clear_even=c_even, other_tracks_tune=tn(j1), gap_other_tracks=g_ot, clear_other_tracks=c_ot,
                     other_districts_tune=tn(j2), gap_other_districts=g_od, clear_other_districts=c_od))
A["retune_rows"] = [dict(r, track="/".join(r["track"])) for r in rows]


def agg(sel, f):
    v = [r[f] for r in rows if sel(r)]
    return float(np.mean(v)), float(np.max(v)), len(v)


L.append("### (a) Retune gap at the cap (r 1.05), average play, base model\n")
L.append("Mean over 5 tracks x 3 opponent styles per row (15 cells, 9,000 runs each). Gaps in percentage points; "
         "'clear' = at least 5 pp with the same sign in all 9 batches.\n")
L.append("| District | Turns | Even-spread win % | Best-tune win % | Best vs even (mean / max) | Clear vs even | Best vs best-on-other-tracks (mean / max) | Clear | Best vs best-on-other-districts (mean / max) | Clear | Most common best tune |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|")
summ = {}
for d, T in itertools.product(DIST, LENGTHS):
    s = lambda r: r["track"][0] == d and r["T"] == T
    sub = [r for r in rows if s(r)]
    ev = np.mean([r["even_wr"] for r in sub]); bw = np.mean([r["best_wr"] for r in sub])
    ge = agg(s, "gap_even"); go = agg(s, "gap_other_tracks"); gd = agg(s, "gap_other_districts")
    ce = sum(r["clear_even"] for r in sub); co = sum(r["clear_other_tracks"] for r in sub); cd = sum(r["clear_other_districts"] for r in sub)
    mc = Counter(r["best"] for r in sub).most_common(2)
    summ[f"{d}{T}"] = dict(even=ev, best=bw, gap_even=ge, gap_other_tracks=go, gap_other_districts=gd, clear=(ce, co, cd), common=mc)
    L.append(f"| {d.title()} | {T} | {ev:.1f} | {bw:.1f} | {ge[0]:.1f} / {ge[1]:.1f} | {ce}/15 | {go[0]:.1f} / {go[1]:.1f} | {co}/15 | {gd[0]:.1f} / {gd[1]:.1f} | {cd}/15 | "
             + ", ".join(f"{t} ({n})" for t, n in mc) + " |")
tot = dict(gap_even=agg(lambda r: True, "gap_even"), gap_other_tracks=agg(lambda r: True, "gap_other_tracks"),
           gap_other_districts=agg(lambda r: True, "gap_other_districts"),
           clear_even=sum(r["clear_even"] for r in rows), clear_other_tracks=sum(r["clear_other_tracks"] for r in rows),
           clear_other_districts=sum(r["clear_other_districts"] for r in rows), cells=len(rows))
A["retune_summary"] = summ; A["retune_total"] = tot
L.append(f"| **All** | | | | {tot['gap_even'][0]:.1f} / {tot['gap_even'][1]:.1f} | {tot['clear_even']}/{len(rows)} | "
         f"{tot['gap_other_tracks'][0]:.1f} / {tot['gap_other_tracks'][1]:.1f} | {tot['clear_other_tracks']}/{len(rows)} | "
         f"{tot['gap_other_districts'][0]:.1f} / {tot['gap_other_districts'][1]:.1f} | {tot['clear_other_districts']}/{len(rows)} | |\n")

# by style
L.append("By opponent style (all 15 tracks x 3 lengths = 45 cells each):\n")
L.append("| Style | Best vs even (mean) | Clear | Best vs best-on-other-districts (mean) | Clear | Most common best tunes |")
L.append("|---|---|---|---|---|---|")
for st in STYLES:
    s = lambda r: r["style"] == st
    sub = [r for r in rows if s(r)]
    L.append(f"| {st} | {agg(s,'gap_even')[0]:.1f} | {sum(r['clear_even'] for r in sub)}/45 | {agg(s,'gap_other_districts')[0]:.1f} | "
             f"{sum(r['clear_other_districts'] for r in sub)}/45 | " + ", ".join(f"{t} ({n})" for t, n in Counter(r['best'] for r in sub).most_common(3)) + " |")
L.append("")

# style retune: tune that is best vs a balanced boss, used against hot / conserver
sr = defaultdict(list)
for tk, T in itertools.product(TK, LENGTHS):
    bb = int(np.argmax(cells[(tk, T, "balanced")].mean(0)[:NT]))
    for st in ("hot_early", "conserver"):
        Wc = cells[(tk, T, st)]; b = int(np.argmax(Wc.mean(0)[:NT]))
        sr[st].append(diff_stats(Wc, b, bb))
A["style_retune"] = {st: dict(mean=float(np.mean([x[0] for x in v])), max=float(np.max([x[0] for x in v])), clear=int(sum(x[1] for x in v)), n=len(v)) for st, v in sr.items()}
# length retune: best-at-10 tune used in a 30-turn race
lr = []
for tk, st in itertools.product(TK, STYLES):
    b10 = int(np.argmax(cells[(tk, 10, st)].mean(0)[:NT])); Wc = cells[(tk, 30, st)]; b30 = int(np.argmax(Wc.mean(0)[:NT]))
    lr.append(diff_stats(Wc, b30, b10))
A["length_retune"] = dict(mean=float(np.mean([x[0] for x in lr])), max=float(np.max([x[0] for x in lr])), clear=int(sum(x[1] for x in lr)), n=len(lr))
L.append("Retuning for the opponent style or race length, same track (cost of keeping the wrong tune):\n")
L.append("| Switch | Mean gap (pp) | Max gap (pp) | Clear cells |")
L.append("|---|---|---|---|")
for st, v in A["style_retune"].items():
    L.append(f"| Tune best vs balanced boss, used vs {st} | {v['mean']:.1f} | {v['max']:.1f} | {v['clear']}/{v['n']} |")
v = A["length_retune"]; L.append(f"| Tune best at 10 turns, used at 30 turns | {v['mean']:.1f} | {v['max']:.1f} | {v['clear']}/{v['n']} |\n")

# ───────────── (b) dominance ─────────────
allp = np.array([Wc.mean(0)[:NT] for Wc in cells.values()])      # (135, 21)
g = int(np.argmax(allp.mean(0)))
loss = []; clear_worse = 0; within2 = 0
for Wc in cells.values():
    b = int(np.argmax(Wc.mean(0)[:NT])); m, c = diff_stats(Wc, b, g); loss.append(m); clear_worse += c; within2 += m <= 2
bestcount = Counter(tn(int(np.argmax(Wc.mean(0)[:NT]))) for Wc in cells.values())
per_d = {}
for d in DIST:
    sel = [i for i, k in enumerate(cells) if k[0][0] == d]
    gd = int(np.argmax(allp[sel].mean(0))); per_d[d] = (tn(gd), float(allp[sel].mean(0)[gd]), float(allp[sel].mean(0)[g]))
A["dominance"] = dict(global_tune=tn(g), global_mean_wr=float(allp.mean(0)[g]), even_mean_wr=float(np.mean([Wc.mean(0)[EV] for Wc in cells.values()])),
                      mean_loss=float(np.mean(loss)), max_loss=float(np.max(loss)), cells_clearly_worse=int(clear_worse),
                      cells_within_2pp=int(within2), n=len(loss), distinct_best=len(bestcount), best_counts=bestcount.most_common(),
                      per_district_best=per_d)
dm = A["dominance"]
L.append("### (b) Does one tune win everywhere?\n")
L.append(f"- Best single tune across all {dm['n']} cells: **{dm['global_tune']}**, mean win {dm['global_mean_wr']:.1f}% (even spread {dm['even_mean_wr']:.1f}%).")
L.append(f"- Against each cell's own best tune it gives up {dm['mean_loss']:.1f} pp on average (max {dm['max_loss']:.1f}); it is within 2 pp of the best in {dm['cells_within_2pp']}/{dm['n']} cells and clearly worse (5+ pp, all 9 batches) in {dm['cells_clearly_worse']}/{dm['n']}.")
L.append(f"- {dm['distinct_best']} different tunes are best somewhere: " + ", ".join(f"{t} ({n})" for t, n in dm['best_counts']) + ".")
L.append("- Best tune per district (mean win; the global tune's win in that district): " +
         "; ".join(f"{d.title()} {t} {a:.1f}% ({b:.1f}%)" for d, (t, a, b) in per_d.items()) + ".\n")

# ───────────── (c) combat targets ─────────────
KR = [("perfect", 0.8), ("perfect", 1.0), ("perfect", 1.05), ("perfect", 1.10), ("average", 0.8), ("average", 1.0), ("average", 1.05), ("average", 1.10)]
TARGET = {("perfect", 0.8): "10-25", ("perfect", 1.0): "wins (>= 85 per design/02 §0.4)", ("average", 1.05): "60-75 (cap 105%)", ("average", 1.10): "60-75 if cap moves to 110%"}
comb = {}
L.append("### (c) Combat targets (win %)\n")
L.append("New model: all 15 tracks x 3 lengths x 3 opponent styles (135 cells x 9,000 runs). Live model: 15 tracks x 3 lengths (no styles), same seeds. "
         "Perfect = reads every Entry (q_read 1.0) and perfect timing (raw QTE 1.0). Average = q_read 0.6 and the 'average' QTE profile at the visible zone for that r.\n")
L.append("| Play | r | Target | Live model, even spread (min-max by district x length) | New model, even spread (min-max) | New model, best tune per cell |")
L.append("|---|---|---|---|---|---|")
for kind, r in KR:
    ev_new = defaultdict(list); best_new = []
    for tk, T, st in itertools.product(TK, LENGTHS, STYLES):
        Wc = W(nk(tk, T, st, kind, r)).mean(0); ev_new[(tk[0], T)].append(Wc[EV]); best_new.append(Wc[:NT].max())
    ev_old = defaultdict(list)
    for tk, T in itertools.product(TK, LENGTHS):
        ev_old[(tk[0], T)].append(W(ok(tk, T, kind, r), "old").mean(0)[EV])
    en = [np.mean(v) for v in ev_new.values()]; eo = [np.mean(v) for v in ev_old.values()]
    comb[f"{kind}{r}"] = dict(old_even=float(np.mean(eo)), old_min=float(min(eo)), old_max=float(max(eo)),
                              new_even=float(np.mean(en)), new_min=float(min(en)), new_max=float(max(en)), new_best=float(np.mean(best_new)))
    c = comb[f"{kind}{r}"]
    L.append(f"| {kind} | {r:.2f} | {TARGET.get((kind, r), '-')} | {c['old_even']:.1f} ({c['old_min']:.1f}-{c['old_max']:.1f}) | {c['new_even']:.1f} ({c['new_min']:.1f}-{c['new_max']:.1f}) | {c['new_best']:.1f} |")
A["combat"] = comb
L.append("")
# variants on track #1 per district
L.append("Variants (track #1 of each district x 3 lengths x 3 styles = 27 cells, even spread / best tune per cell):\n")
L.append("| Variant | Perfect r 0.8 | Perfect r 1.0 | Average r 1.05 | Average r 1.10 | Best vs even at avg r 1.05 (mean pp) | Clear vs even |")
L.append("|---|---|---|---|---|---|---|")
var = {}
for v in ("base", "hard_block", "downgrade", "kappa_x3"):
    vals = {}
    for kind, r in [("perfect", 0.8), ("perfect", 1.0), ("average", 1.05), ("average", 1.10)]:
        e_, b_ = [], []
        for tk, T, st in itertools.product(FIRST, LENGTHS, STYLES):
            Wc = W(nk(tk, T, st, kind, r, v)).mean(0); e_.append(Wc[EV]); b_.append(Wc[:NT].max())
        vals[f"{kind}{r}"] = (float(np.mean(e_)), float(np.mean(b_)))
    gaps = []
    for tk, T, st in itertools.product(FIRST, LENGTHS, STYLES):
        Wc = W(nk(tk, T, st, "average", 1.05, v)); b = int(np.argmax(Wc.mean(0)[:NT])); gaps.append(diff_stats(Wc, b, EV))
    vals["gap_even"] = (float(np.mean([x[0] for x in gaps])), int(sum(x[1] for x in gaps)))
    var[v] = vals
    L.append(f"| {v} | " + " | ".join(f"{vals[k][0]:.1f} / {vals[k][1]:.1f}" for k in ("perfect0.8", "perfect1.0", "average1.05", "average1.1")) +
             f" | {vals['gap_even'][0]:.1f} | {vals['gap_even'][1]}/27 |")
A["variants"] = var
L.append("")

# ───────────── (d) how much the stat mix moves the win rate: live vs new ─────────────
L.append("### (d) How much the stat mix matters: live model vs new model\n")
L.append("Average play at r 1.05, 21 tunes at a fixed total. Spread = best tune minus worst tune; per cell, then averaged. "
         "New model uses the balanced boss (the live model has no styles), plus all styles for reference.\n")
L.append("| Model | Cells | Spread best-worst (mean / max pp) | Best vs even (mean / max pp) | Cells where best beats even clearly |")
L.append("|---|---|---|---|---|")
mix = {}
def mixrow(name, Ws):
    sp = [w.mean(0)[:NT].max() - w.mean(0)[:NT].min() for w in Ws]
    ge = [diff_stats(w, int(np.argmax(w.mean(0)[:NT])), EV) for w in Ws]
    mix[name] = dict(spread_mean=float(np.mean(sp)), spread_max=float(np.max(sp)), gap_even_mean=float(np.mean([x[0] for x in ge])),
                     gap_even_max=float(np.max([x[0] for x in ge])), clear=int(sum(x[1] for x in ge)), n=len(Ws))
    m = mix[name]
    L.append(f"| {name} | {m['n']} | {m['spread_mean']:.1f} / {m['spread_max']:.1f} | {m['gap_even_mean']:.1f} / {m['gap_even_max']:.1f} | {m['clear']}/{m['n']} |")
mixrow("Live (card draw, MU/ETA)", [W(ok(tk, T, "average", 1.05), "old") for tk, T in itertools.product(TK, LENGTHS)])
mixrow("New, balanced boss", [cells[(tk, T, "balanced")] for tk, T in itertools.product(TK, LENGTHS)])
mixrow("New, all styles", list(cells.values()))
A["stat_mix"] = mix
# live model's best tunes
oldbest = Counter(tn(int(np.argmax(W(ok(tk, T, "average", 1.05), "old").mean(0)[:NT]))) for tk, T in itertools.product(TK, LENGTHS))
A["old_best_tunes"] = oldbest.most_common()
L.append("\nLive model best tunes: " + ", ".join(f"{t} ({n})" for t, n in oldbest.most_common()) + ".\n")


# live model: retune gap and dominance on the same 45 track x length cells (for a fair comparison with the new model)
oc = {(tk, T): W(ok(tk, T, "average", 1.05), "old") for tk, T in itertools.product(TK, LENGTHS)}
nc = {(tk, T): cells[(tk, T, "balanced")] for tk, T in itertools.product(TK, LENGTHS)}
L.append("### Live vs new: retune gap and dominance on the same 45 cells (average play, r 1.05; new = balanced boss)\n")
L.append("| Model | Best vs best-on-other-districts (mean / max pp) | Clear | Best single tune | Its mean loss vs each cell's best (pp) | Cells clearly worse |")
L.append("|---|---|---|---|---|---|")
cmpd = {}
for name, cc in (("Live", oc), ("New (base)", nc)):
    gaps = []
    for (tk, T), Wc in cc.items():
        b = int(np.argmax(Wc.mean(0)[:NT]))
        oth = np.mean([cc[(t2, T)].mean(0)[:NT] for t2 in TK if t2[0] != tk[0]], axis=0)
        gaps.append(diff_stats(Wc, b, int(np.argmax(oth))))
    allp_ = np.array([Wc.mean(0)[:NT] for Wc in cc.values()]); g_ = int(np.argmax(allp_.mean(0)))
    ls = [diff_stats(Wc, int(np.argmax(Wc.mean(0)[:NT])), g_) for Wc in cc.values()]
    cmpd[name] = dict(gap_other_districts=float(np.mean([x[0] for x in gaps])), gap_max=float(np.max([x[0] for x in gaps])),
                      clear=int(sum(x[1] for x in gaps)), global_tune=tn(g_), global_loss=float(np.mean([x[0] for x in ls])),
                      global_clear_worse=int(sum(x[1] for x in ls)), n=len(gaps))
    c = cmpd[name]
    L.append(f"| {name} | {c['gap_other_districts']:.1f} / {c['gap_max']:.1f} | {c['clear']}/{c['n']} | {c['global_tune']} | {c['global_loss']:.1f} | {c['global_clear_worse']}/{c['n']} |")
A["live_vs_new_retune"] = cmpd
L.append("")
# scouting value
sc = {}
for st in ("hot_early", "conserver"):
    de, db = [], []
    for tk, T in itertools.product(FIRST, LENGTHS):
        a = W(nk(tk, T, st, "average", 1.05, "base", True)); b = W(nk(tk, T, st, "average", 1.05, "base", False))
        de.append(a.mean(0)[EV] - b.mean(0)[EV]); i = int(np.argmax(a.mean(0)[:NT])); db.append(a.mean(0)[i] - b.mean(0)[i])
    sc[st] = dict(even=float(np.mean(de)), best=float(np.mean(db)))
A["scouting"] = sc
L.append("### Scouting value (knowing the boss's style vs assuming the default 65/21/14), average play r 1.05, track #1 per district\n")
L.append("| Style | Win gain from knowing the style, even spread (pp) | Same, with the best tune (pp) |")
L.append("|---|---|---|")
for st, v in sc.items():
    L.append(f"| {st} | {v['even']:.1f} | {v['best']:.1f} |")
L.append("")

# demand table
L.append("### Track demand (per turn, perfect counter-player vs 65/21/14 boss, incl. passive wear) and even-spread tanks\n")
L.append("| Track | Fuel | Suspension | Brakes |")
L.append("|---|---|---|---|")
for tk in TK:
    dm_ = R.track_demand(tk[0], TR[tk])
    L.append(f"| {tk[1]} | {dm_[0]:.2f} | {dm_[1]:.2f} | {dm_[2]:.2f} |")
a = R.avg_demand(); tank10, rec = R.tanks(np.array([[1/3, 1/3, 1/3]]), 10)
L.append(f"| **Cross-track average** | {a[0]:.2f} | {a[1]:.2f} | {a[2]:.2f} |\n")
L.append(f"Even-spread tanks at r 1.0 for a 10-turn race: fuel {tank10[0,0]:.2f}, suspension {tank10[0,1]:.2f} (recovers {rec[0,1]:.2f}/turn), brakes {tank10[0,2]:.2f} "
         f"(fuel and brakes scale with race length; suspension does not).\n")
A["demand"] = {"/".join(tk): R.track_demand(tk[0], TR[tk]).tolist() for tk in TK}
open("tables.md", "w").write("\n".join(L))
json.dump(A, open("analysis.json", "w"), indent=1, default=str)
print("\n".join(L))
