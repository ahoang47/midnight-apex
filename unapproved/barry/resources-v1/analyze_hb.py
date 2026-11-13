"""Tables for the full-size hard-block rerun (results_hb.json -> tables_hb.md, analysis_hb.json)."""
import json, itertools
from collections import Counter, defaultdict
import numpy as np
import resources_v1 as R

res = json.load(open("results_hb.json"))
TUNES = np.array(res["meta"]["tunes"]); NT = len(TUNES) - 1; EV = NT
LENGTHS = (10, 20, 30); STYLES = R.STYLES; TR = R.tracks(); TK = list(TR); DIST = ("touge", "wangan", "street")


def W(tk, T, st, kind, r):
    return 100 * np.array(res["new"][f"{tk[0]}/{tk[1]}|{T}|{st}|{kind}|{r}|hb_b|True"])


def tn(i):
    p, h, e = TUNES[i]
    return "even" if i == EV else f"P{round(100*p)}/H{round(100*h)}/E{round(100*e)}"


def ds(Wc, i, j):
    d = Wc[:, i] - Wc[:, j]; m = float(d.mean())
    return m, bool(abs(m) >= 5 and (np.all(d > 0) or np.all(d < 0)))


A = {}; L = []
cells = {(tk, T, st): W(tk, T, st, "average", 1.05) for tk, T, st in itertools.product(TK, LENGTHS, STYLES)}
rows = []
for (tk, T, st), Wc in cells.items():
    p = Wc.mean(0); b = int(np.argmax(p[:NT]))
    oth = np.mean([cells[(t2, T, st)].mean(0)[:NT] for t2 in TK if t2[0] != tk[0]], axis=0)
    otht = np.mean([cells[(t2, T, st)].mean(0)[:NT] for t2 in TK if t2 != tk], axis=0)
    ge = ds(Wc, b, EV); gd = ds(Wc, b, int(np.argmax(oth))); gt = ds(Wc, b, int(np.argmax(otht)))
    rows.append(dict(d=tk[0], T=T, st=st, best=tn(b), bw=float(p[b]), ev=float(p[EV]), ge=ge, gd=gd, gt=gt))
L.append("### Hard-block B (hard block, KAPPA_SCALE 1.25, TANK_FACTOR 0.4): retune gap at r 1.05, average play\n")
L.append("| District | Turns | Even win % | Best-tune win % | Best vs even (mean pp, clear) | Best vs best-on-other-tracks (mean pp, clear) | Best vs best-on-other-districts (mean pp, clear) | Most common best tune |")
L.append("|---|---|---|---|---|---|---|---|")
summ = {}
for d, T in itertools.product(DIST, LENGTHS):
    s = [r for r in rows if r["d"] == d and r["T"] == T]
    f = lambda k: (np.mean([r[k][0] for r in s]), sum(r[k][1] for r in s))
    summ[f"{d}{T}"] = dict(even=float(np.mean([r['ev'] for r in s])), best=float(np.mean([r['bw'] for r in s])),
                           ge=f("ge"), gt=f("gt"), gd=f("gd"), common=Counter(r['best'] for r in s).most_common(2))
    m = summ[f"{d}{T}"]
    L.append(f"| {d.title()} | {T} | {m['even']:.1f} | {m['best']:.1f} | {m['ge'][0]:.1f} ({m['ge'][1]}/15) | {m['gt'][0]:.1f} ({m['gt'][1]}/15) | {m['gd'][0]:.1f} ({m['gd'][1]}/15) | "
             + ", ".join(f"{t} ({n})" for t, n in m['common']) + " |")
tot = {k: (float(np.mean([r[k][0] for r in rows])), float(np.max([r[k][0] for r in rows])), int(sum(r[k][1] for r in rows))) for k in ("ge", "gt", "gd")}
A["retune_summary"] = summ; A["retune_total"] = tot
L.append(f"| **All** | | | | {tot['ge'][0]:.1f} (max {tot['ge'][1]:.1f}; {tot['ge'][2]}/135) | {tot['gt'][0]:.1f} (max {tot['gt'][1]:.1f}; {tot['gt'][2]}/135) | {tot['gd'][0]:.1f} (max {tot['gd'][1]:.1f}; {tot['gd'][2]}/135) | |\n")
# style / length retune
sr = {}
for st in ("hot_early", "conserver"):
    v = []
    for tk, T in itertools.product(TK, LENGTHS):
        bb = int(np.argmax(cells[(tk, T, "balanced")].mean(0)[:NT])); Wc = cells[(tk, T, st)]
        v.append(ds(Wc, int(np.argmax(Wc.mean(0)[:NT])), bb))
    sr[st] = (float(np.mean([x[0] for x in v])), float(np.max([x[0] for x in v])), int(sum(x[1] for x in v)))
lr = []
for tk, st in itertools.product(TK, STYLES):
    b10 = int(np.argmax(cells[(tk, 10, st)].mean(0)[:NT])); Wc = cells[(tk, 30, st)]
    lr.append(ds(Wc, int(np.argmax(Wc.mean(0)[:NT])), b10))
A["style_retune"] = sr; A["length_retune"] = (float(np.mean([x[0] for x in lr])), float(np.max([x[0] for x in lr])), int(sum(x[1] for x in lr)))
L.append("| Switch | Mean gap (pp) | Max gap (pp) | Clear cells |")
L.append("|---|---|---|---|")
for st, v in sr.items():
    L.append(f"| Best-vs-balanced tune used vs {st} | {v[0]:.1f} | {v[1]:.1f} | {v[2]}/45 |")
v = A["length_retune"]; L.append(f"| Best-at-10-turns tune used at 30 turns | {v[0]:.1f} | {v[1]:.1f} | {v[2]}/45 |\n")
# dominance
allp = np.array([Wc.mean(0)[:NT] for Wc in cells.values()]); g = int(np.argmax(allp.mean(0)))
ls = [ds(Wc, int(np.argmax(Wc.mean(0)[:NT])), g) for Wc in cells.values()]
bc = Counter(tn(int(np.argmax(Wc.mean(0)[:NT]))) for Wc in cells.values())
A["dominance"] = dict(global_tune=tn(g), global_wr=float(allp.mean(0)[g]), even_wr=float(np.mean([Wc.mean(0)[EV] for Wc in cells.values()])),
                      loss=float(np.mean([x[0] for x in ls])), max_loss=float(np.max([x[0] for x in ls])), clear_worse=int(sum(x[1] for x in ls)),
                      within2=int(sum(x[0] <= 2 for x in ls)), best_counts=bc.most_common())
dm = A["dominance"]
L.append(f"Dominance: best single tune **{dm['global_tune']}** (mean {dm['global_wr']:.1f}%, even {dm['even_wr']:.1f}%) gives up {dm['loss']:.1f} pp on average vs each cell's best "
         f"(max {dm['max_loss']:.1f}); within 2 pp in {dm['within2']}/135 cells, clearly worse in {dm['clear_worse']}/135. Best tunes: " + ", ".join(f"{t} ({n})" for t, n in dm['best_counts']) + ".\n")
# combat
L.append("| Play | r | Target | Even spread (min-max by district x length) | Best tune per cell |")
L.append("|---|---|---|---|---|")
TG = {("perfect", 0.8): "10-25", ("perfect", 1.0): "wins", ("average", 1.05): "60-75", ("average", 1.10): "60-75 if cap is 110%"}
comb = {}
for kind, r in [("perfect", 0.8), ("perfect", 1.0), ("average", 1.0), ("average", 1.05), ("average", 1.10)]:
    ev = defaultdict(list); bt = []
    for tk, T, st in itertools.product(TK, LENGTHS, STYLES):
        p = W(tk, T, st, kind, r).mean(0); ev[(tk[0], T)].append(p[EV]); bt.append(p[:NT].max())
    e = [np.mean(v) for v in ev.values()]
    comb[f"{kind}{r}"] = dict(even=float(np.mean(e)), mn=float(min(e)), mx=float(max(e)), best=float(np.mean(bt)),
                              by_district={d: float(np.mean([np.mean(ev[(d, T)]) for T in LENGTHS])) for d in DIST})
    c = comb[f"{kind}{r}"]
    L.append(f"| {kind} | {r:.2f} | {TG.get((kind, r), '-')} | {c['even']:.1f} ({c['mn']:.1f}-{c['mx']:.1f}) | {c['best']:.1f} |")
A["combat"] = comb
L.append("\nBy district, even spread: " + "; ".join(f"{k}: " + ", ".join(f"{d} {v:.1f}" for d, v in c['by_district'].items()) for k, c in comb.items()) + "\n")
open("tables_hb.md", "w").write("\n".join(L)); json.dump(A, open("analysis_hb.json", "w"), indent=1, default=str)
print("\n".join(L))
