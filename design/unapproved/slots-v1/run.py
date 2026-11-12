"""slots-v1: compare slot schemes A (3->6), B (fixed 3), C (fixed 6) with window-only mods competing for slots.

Barry, 2026-11-11. Draft, NOT approved. Writes results.json; RESULTS.md is written by hand from it.
Oracle: official clash-count banks (q_read 0.6, N=4000 per district per seed per length, seeds 20261113-15, 10/20/30 turns),
lines-v1 S-A + W-A tables, KAPPA_BY_LENGTH, opponent QTE 1.0, visible QTE zone from equations.py (4cb5401), PLACEHOLDER σ.
"""
import json, sys
import numpy as np
import slots_model as S

E, P = S.E, S.P
DOM = 5.0      # |mean paired Δ| >= 5 pp with the same sign in all 9 banks = no-brainer
NOISE = 1.5


def classify(d):
    m = float(np.mean(d))
    if m >= DOM and np.all(d > 0):
        return "dominant"
    if m <= -DOM and np.all(d < 0):
        return "dominated"
    if abs(m) < NOISE:
        return "even"
    return "lean+" if m > 0 else "lean-"


def key_cells():
    """Cells at the official progression state (average player, forced grind, all-stat, 4cb5401 + this oracle)."""
    rows, _ = S.run(None, "average")
    cells = []
    for r in rows:
        if r["crew"] in ("Prologue",):
            continue
        d = r.get("district") or r["crew"].split()[1]
        if r["crew"] != "Finale" and r["j"] == 3:
            cells.append(dict(cell="mature #2 skipped", crew=r["crew"], rung=r["rung"], j=r["j"], r=r["r_skip"], district=d.lower()))
        if r["crew"] != "Finale" and r["j"] == 6:
            cells.append(dict(cell="boss at target", crew=r["crew"], rung=r["rung"], j=r["j"], r=r["r_tgt"], district=d.lower()))
            cells.append(dict(cell="boss skipped", crew=r["crew"], rung=r["rung"], j=r["j"], r=r["r_skip"], district=d.lower()))
        if r["crew"] == "Finale" and r["rung"] in ("Myth #2", "Summit"):
            cells.append(dict(cell=f"{r['rung']} skipped", crew="Finale", rung=r["rung"], j=r["j"], r=r["r_skip"], district=d.lower()))
            cells.append(dict(cell=f"{r['rung']} at target", crew="Finale", rung=r["rung"], j=r["j"], r=r["r_tgt"], district=d.lower()))
    return cells


def trade_table(scheme, cells):
    sched = {(s["crew"], s["rung"], s["j"]): s for s in S.schedule(scheme)}
    out = []
    for c in cells:
        s = sched[(c["crew"], c["rung"], c["j"])]
        for prof in S.PROFILES:
            base = S.wr_vec(c["r"], prof, 0.0, c["district"])
            opts = []
            for nm, dr, wm in S.loadouts(s["lines"], s["B"]):
                if nm == "all stat":
                    continue
                v = S.wr_vec(c["r"] - dr, prof, wm, c["district"])
                d = v - base
                opts.append(dict(loadout=nm, r=c["r"] - dr, dr=dr, mid=S.mid(v), band=[round(float(v.min()), 1), round(float(v.max()), 1)],
                                 delta_mean=round(float(d.mean()), 2), delta_min=round(float(d.min()), 2), delta_max=round(float(d.max()), 2),
                                 verdict=classify(d)))
            best = max(opts, key=lambda o: o["delta_mean"])
            out.append(dict(**c, scheme=scheme, profile=prof, n=s["n"], slot_min=round(min(s["lines"]), 2), slot_mean=round(s["mods"] / s["n"], 2),
                            B=round(s["B"], 1), dr_one_slot=round(min(s["lines"]) / s["B"], 4),
                            base_mid=round(S.mid(base), 2), base_band=[round(float(base.min()), 1), round(float(base.max()), 1)],
                            options=opts, best=best))
    return out


def break_even(scheme, cells):
    """Window size w* (one window mod) where the average player's mean paired Δ = 0, per cell (bisection on wm in [0, 3])."""
    sched = {(s["crew"], s["rung"], s["j"]): s for s in S.schedule(scheme)}
    out = []
    for c in cells:
        s = sched[(c["crew"], c["rung"], c["j"])]; dr = min(s["lines"]) / s["B"]
        res = {}
        for prof in S.PROFILES:
            base = S.wr_vec(c["r"], prof, 0.0, c["district"]).mean()
            f = lambda wm: S.wr_vec(c["r"] - dr, prof, wm, c["district"]).mean() - base
            if f(3.0) < 0:
                res[prof] = ">3.00"; continue
            lo, hi = 0.0, 3.0
            for _ in range(30):
                m = 0.5 * (lo + hi)
                lo, hi = (m, hi) if f(m) < 0 else (lo, m)
            res[prof] = round(hi, 3)
        out.append(dict(cell=c["cell"], crew=c["crew"], rung=c["rung"], scheme=scheme, w_star=res))
    return out


def feel(scheme):
    sch = S.schedule(scheme)
    camp = [x for x in sch if x["crew"] != "Finale"]
    buys = []; dead = []; spend = {"R1": 0.0, "R2": 0.0, "R3": 0.0, "Finale": 0.0}; under = []
    for x in sch:
        ph = S.phase(x["crew"])
        if x["buy"] is None:
            dead.append(f"{x['crew']} {x['rung']}")
        elif isinstance(x["buy"], tuple):
            spend[ph] += x["buy"][1] * x["buy"][2]; buys.append(dict(where=f"{x['crew']} {x['rung']}", n=x["buy"][1], gain_pct=None))
        else:
            for i, old, new in x["buy"]:
                spend[ph] += new
                buys.append(dict(where=f"{x['crew']} {x['rung']}", n=1, gain_sp=round(new - (old or 0), 2),
                                 gain_pct=None if not old else round(100 * (new - old) / old, 1)))
        ratio = min(x["lines"]) / (x["mods"] / x["n"])
        if ratio < 0.9:
            under.append(dict(where=f"{x['crew']} {x['rung']}", min_over_mean=round(ratio, 2)))
    g = [b["gain_pct"] for b in buys if b.get("gain_pct") is not None]
    return dict(scheme=scheme, slots=S.SCHEMES[scheme], purchases=sum(b["n"] for b in buys), story_wins_with_no_new_stat_tier=len(dead),
                no_tier_wins=dead, upgrade_pct_median=float(np.median(g)), upgrade_pct_p10=float(np.percentile(g, 10)), upgrade_pct_p90=float(np.percentile(g, 90)),
                spend_stat_units={k: round(v, 1) for k, v in spend.items()}, spend_total=round(sum(spend.values()), 1),
                rungs_with_a_slot_under_90pct_of_mean=under)


def main():
    cells = key_cells()
    data = dict(meta=dict(N_per_bank=4000, seeds=list(S.W.SEEDS), lengths=list(S.W.LENGTHS), q_read=0.6, banks="official (final-v1 Touge mask, lines-v1 SSA / AAD)",
                sigma=E.QTE_SKILL_SIGMA_OVER_A0, window_sizes=S.WINDOW_SIZES, dom_threshold_pp=DOM, noise_pp=NOISE, restock_fraction=S.RESTOCK_FRACTION),
                cells=cells, trades={}, break_even={}, feel={}, grind={})
    for sc in "ABC":
        print("scheme", sc, flush=True)
        data["trades"][sc] = trade_table(sc, cells)
        data["break_even"][sc] = break_even(sc, cells)
        data["feel"][sc] = feel(sc)
    for prof in S.PROFILES:
        rows, t = S.run(None, prof)
        data["grind"][f"baseline|{prof}"] = dict(total=t, walls=[(r["crew"], r["rung"], r["grind_races"]) for r in rows if r["grind_races"]])
        for sc in "ABC":
            rows, t = S.run(sc, prof)
            data["grind"][f"{sc}|{prof}"] = dict(total=t, walls=[(r["crew"], r["rung"], r["grind_races"]) for r in rows if r["grind_races"]],
                                                 window_picks=[(r["crew"], r["rung"], r["skip_pick"], round(r["skip_mid"], 2)) for r in rows
                                                               if r["skip_pick"] not in ("-", "all stat")])
            print(sc, prof, t, flush=True)
    json.dump(data, open("results.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
