"""slots-v2 analysis: key cells (Q3/Q4/aero), grind counts (Q5). Writes results.json.
Same statistical bar as slots-v1: N=4000 per bank, seeds 20261113-15 x 10/20/30 turns (9 banks), paired deltas."""
import json, sys, time
import numpy as np
import model as M

E, P, S1 = M.E, M.P, M.S1
DOM, NOISE = 5.0, 1.5
POOLS = (0.10, 0.20, 0.30)


def classify(d):
    m = float(np.mean(d))
    if m >= DOM and np.all(d > 0):
        return "dominant"
    if m <= -DOM and np.all(d < 0):
        return "dominated"
    if abs(m) < NOISE:
        return "even"
    return "lean+" if m > 0 else "lean-"


def aero_ok(crew):
    if crew == "Finale":
        return True
    if crew == "Prologue":
        return False
    rnd = int(crew[1]); pos = E.DEFAULT_CREW_ORDER[rnd].index(crew.split()[1])
    return (rnd, pos) >= (E.DEBT_CLEAR_AFTER[0], E.DEBT_CLEAR_AFTER[1])   # (2,1): second R2 crew onward (pos is 0-based)


SCHED = {(s["crew"], s["rung"], s["j"]): s for s in S1.schedule("C")}


def key_cells():
    rows, _ = S1.run(None, "average")        # official progression state (153 races); r values only
    cells = []
    for r in rows:
        if r["crew"] == "Prologue":
            continue
        d = (r.get("district") or r["crew"].split()[1]).lower()
        s = SCHED[(r["crew"], r["rung"], r["j"])]
        base = dict(crew=r["crew"], rung=r["rung"], j=r["j"], district=d, B=r["B"], T=s["mods"], v=np.array(s["lines"]), aero=aero_ok(r["crew"]))
        if r["crew"] != "Finale":
            if r["j"] == 3:
                cells.append(dict(base, cell="mature #2 skipped", r=r["r_skip"]))
            if r["j"] == 6:
                cells.append(dict(base, cell="boss at target", r=r["r_tgt"])); cells.append(dict(base, cell="boss skipped", r=r["r_skip"]))
        elif r["rung"] in ("Myth #2", "Summit"):
            cells.append(dict(base, cell=f"{r['rung']} skipped", r=r["r_skip"]))
    return cells


def configs_for(cell, split, pool, window=True):
    v = cell["v"]; sp = cell["r"] * cell["B"] - cell["T"]
    spv = np.full(3, sp / 3)
    out = []
    for lab, vec, wm, kind in M.austin_loadouts(split, v, cell["aero"] and pool is not None, pool):
        if wm and not window:
            continue
        out.append((lab, spv + vec, wm, kind or ("window" if wm else "fixed")))
    return out


def analyse_cell(cell, split, profile):
    res = dict(cell=cell["cell"], crew=cell["crew"], district=cell["district"], split=split, profile=profile, r=round(cell["r"], 4), aero_available=cell["aero"])
    sp = cell["r"] * cell["B"] - cell["T"]; v = cell["T"] / 6       # free mixes: equal slots (counterfactual)
    default = np.full(3, sp / 3) + M.default_vec(split, cell["v"])
    base = M.wr_batch([(default, 0.0)], cell["B"], profile, cell["district"])[0]
    res["balanced_mid"] = round(M.mid(base), 2)
    # Austin layout, no aero (fixed + window any slot)
    cf = configs_for(cell, split, None)
    V = M.wr_batch([(c[1], c[2]) for c in cf], cell["B"], profile, cell["district"])
    D = V - base
    fixed = [i for i, c in enumerate(cf) if c[3] == "fixed"]; win = [i for i, c in enumerate(cf) if c[3] == "window"]
    bf = max(fixed, key=lambda i: D[i].mean()); wf = min(fixed, key=lambda i: D[i].mean()); bw = max(win, key=lambda i: D[i].mean())
    res["fixed_best"] = dict(label=cf[bf][0], delta=round(float(D[bf].mean()), 2), verdict=classify(D[bf]), mid=round(M.mid(V[bf]), 2))
    res["fixed_worst"] = dict(label=cf[wf][0], delta=round(float(D[wf].mean()), 2), verdict=classify(D[wf]), mid=round(M.mid(V[wf]), 2))
    res["fixed_spread"] = round(float(D[bf].mean() - D[wf].mean()), 2)
    dw = V[bw] - V[bf]
    res["window_best"] = dict(label=cf[bw][0], delta_vs_best_fixed=round(float(dw.mean()), 2), verdict=classify(dw), mid=round(M.mid(V[bw]), 2))
    res["window_by_slot"] = {}
    for cat in M.CATS:
        ii = [i for i in win if f"window@{cat}[" in cf[i][0]]
        b = max(ii, key=lambda i: D[i].mean())
        res["window_by_slot"][cat] = round(float((V[b] - V[bf]).mean()), 2)
    # aero (retuned per race) vs the fixed mod it replaces
    if cell["aero"]:
        res["aero"] = {}
        for pool in POOLS:
            ca = [c for c in configs_for(cell, split, pool) if c[3] == "aero"]
            VA = M.wr_batch([(c[1], c[2]) for c in ca], cell["B"], profile, cell["district"])
            ba = int(np.argmax(VA.mean(1))); da = VA[ba] - V[bf]
            caw = [c for c in configs_for(cell, split, pool) if c[3] == "aero+window"]
            VW = M.wr_batch([(c[1], c[2]) for c in caw], cell["B"], profile, cell["district"])
            bw2 = int(np.argmax(VW.mean(1))); dw2 = VW[bw2] - V[bf]
            res["aero"][f"{int(pool * 100)}%"] = dict(label=ca[ba][0], delta_vs_best_fixed=round(float(da.mean()), 2), verdict=classify(da),
                                                       with_window=dict(label=caw[bw2][0], delta_vs_best_fixed=round(float(dw2.mean()), 2), verdict=classify(dw2)))
    # counterfactual: free category mixes (not Austin's layout)
    fm = M.free_mixes(split, v)
    VF = M.wr_batch([(np.full(3, sp / 3) + vec, 0.0) for _, vec in fm], cell["B"], profile, cell["district"])
    DF = VF - base
    order = np.argsort(-DF.mean(1))
    res["free_mix"] = dict(best=fm[order[0]][0], best_delta=round(float(DF[order[0]].mean()), 2), best_verdict=classify(DF[order[0]]),
                           worst=fm[order[-1]][0], worst_delta=round(float(DF[order[-1]].mean()), 2),
                           all={fm[i][0]: round(float(DF[i].mean()), 2) for i in range(len(fm))})
    return res


def main():
    cells = key_cells()
    out = dict(meta=dict(N_per_bank=4000, seeds=list(M.SEEDS), lengths=list(M.LENGTHS), grid_step=M.STEP, window=M.WINDOW, zone_cap=M.ZONE_CAP,
                         pools=POOLS, splits=M.SPLITS, dom_pp=DOM, noise_pp=NOISE), cells=[])
    from multiprocessing import Pool
    with Pool(8) as p:
        out["cells"] = p.starmap(analyse_cell, [(c, s, f) for c in cells for s in M.SPLITS for f in M.PROFILES], chunksize=1)
    json.dump(out, open("results.json", "w"), separators=(",", ":"), default=float)


if __name__ == "__main__":
    main()
