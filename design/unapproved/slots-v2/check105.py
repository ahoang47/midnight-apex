"""Rule 1 exhaustive check: at story points, max over ALL loadouts drawable from the unlocked catalog (2 POW, 2 EN, 2 HAN slots,
each slot from its own unlocked mods) of total % = (SP at the level cap + Σ equipped mod stats) / reference must be <= 105%
and reach it. Total = POW + EN + HAN stat sum, as in equations.stat_shares / clash_progress (r = tot / boss_total) and
progression (r = (SP + mods) / B, cap MOD_CAP_FRACTION x reference). Writes check105.json."""
import json, itertools
import numpy as np
import model as M

E, P, S1 = M.E, M.P, M.S1
SP, _, _ = P.curves()


def history():
    """Per slot (line) tier history over the campaign from the slots-v1 scheme-C schedule, and the story points."""
    sch = [x for x in S1.schedule("C") if x["crew"] != "Finale"]
    tiers = [[] for _ in range(6)]; pts = []
    for x in sch:
        for i, val in enumerate(x["lines"]):
            if not tiers[i] or abs(tiers[i][-1] - val) > 1e-9:
                tiers[i].append(val)
        pts.append(dict(crew=x["crew"], rung=x["rung"], j=x["j"], L=x["L"], T=x["mods"], tiers=[list(t) for t in tiers]))
    return pts


def aero_ok(crew, j):
    rnd = int(crew[1]); order = M.E.DEFAULT_CREW_ORDER[rnd]; pos = order.index(crew.split()[1])
    return (rnd, pos + 1) > M.E.DEBT_CLEAR_AFTER or (rnd > M.E.DEBT_CLEAR_AFTER[0])


def catalog(pt, split, newest=6, with_aero=False, with_window=True):
    """Per slot: list of (label, stat vector). Newest `newest` mods per slot (36-mod example when every slot has 6).
    70/20/10 has two sidegrade variants per tier. Aero = same total as the tier (pool does not change the total).
    Window mod = 0 stats (it is a slot option, not a stat mod)."""
    cat = []
    for s in range(6):
        c = M.SLOT_CATS[s]; mods = []
        for t in reversed(pt["tiers"][s]):
            for sec, vec in M.variants(c, split):
                mods.append((f"{c}{s % 2 + 1} t{t:.2f} {sec or ''}", vec * t))
        mods = mods[:newest]
        if with_aero:
            mods.append((f"aero {c}{s % 2 + 1}", M.mod_vec(c, split) * pt["tiers"][s][-1]))   # total = top tier; any pool split
        if with_window:
            mods.append(("window", np.zeros(3)))
        cat.append(mods)
    return cat


def brute(pt, split, newest=6, with_aero=False, with_window=True):
    cat = catalog(pt, split, newest, with_aero, with_window)
    ref = SP[pt["L"]] / E.SP_CAP_FRACTION; sp = SP[pt["L"]]
    arr = [np.array([m[1] for m in c]) for c in cat]
    # all loadouts: sum over slots, vectorised
    tot = np.zeros(1); vecs = np.zeros((1, 3))
    for a in arr:
        vecs = (vecs[:, None, :] + a[None, :, :]).reshape(-1, 3)
    totals = (sp + vecs.sum(1)) / ref
    n = vecs.shape[0]
    shares = (sp / 3 + vecs) / (sp + vecs.sum(1))[:, None]
    sep = (sp + sum(max(m[1].sum() for m in c) for c in cat)) / ref
    # non-additive alternative: stat above BUILD_STAT_MAX_SHARE of the total would not count (clamp), to show the brute force is needed
    clamp = np.minimum(sp / 3 + vecs, E.BUILD_STAT_MAX_SHARE * (sp + vecs.sum(1))[:, None]).sum(1) / ref
    return dict(point=f"{pt['crew']} {pt['rung']} (j={pt['j']})", split=split, aero=with_aero, window=with_window, catalog_sizes=[len(c) for c in cat], loadouts=int(n),
                max_total_pct=round(100 * float(totals.max()), 6), separable_best_per_slot_pct=round(100 * sep, 6),
                reaches_105=bool(abs(totals.max() - E.MOD_CAP_FRACTION) < 1e-9), over_105=int((totals > E.MOD_CAP_FRACTION + 1e-9).sum()),
                share_min=round(float(shares.min()), 4), share_max=round(float(shares.max()), 4),
                outside_25_50=int(((shares < E.BUILD_STAT_MIN_SHARE - 1e-9) | (shares > E.BUILD_STAT_MAX_SHARE + 1e-9)).any(1).sum()),
                max_total_if_share_clamped_pct=round(100 * float(clamp.max()), 6))


def main():
    pts = history()
    out = dict(definition="total % = (SP + Σ mod stats) / reference; stat sum POW+EN+HAN (equations.stat_shares, progression r)", brute=[], campaign=[])
    picks = [i for i, p in enumerate(pts) if (p["crew"], p["j"]) in
             (("R1 Street", 6), ("R2 Wangan", 0), ("R2 Street", 6), ("R3 Street", 3), ("R3 Wangan", 6))]
    for i in picks:
        for split in M.SPLITS:
            for ae in (False, True):
                if ae and not aero_ok(pts[i]["crew"], pts[i]["j"]):
                    continue
                r = brute(pts[i], split, 6, ae); out["brute"].append(r); print(r, flush=True)
    # Austin's literal example [pt208u]: 36 mods = 6 stat mods per slot x 6 slots, no window/aero -> 6^6 = 46,656 loadouts
    out["austin36"] = []
    for i in [k for k, p in enumerate(pts) if all(len(t) >= 6 for t in p["tiers"])][:1] + [k for k, p in enumerate(pts) if (p["crew"], p["j"]) == ("R3 Wangan", 6)]:
        for split in ("100/0/0", "80/10/10"):
            r = brute(pts[i], split, 6, False, False); out["austin36"].append(r); print("36-mod", r, flush=True)
    # every story point: separable max (best per slot) vs 105%
    worst = 0
    for p in pts:
        ref = SP[p["L"]] / E.SP_CAP_FRACTION
        m = (SP[p["L"]] + sum(t[-1] for t in p["tiers"])) / ref
        out["campaign"].append(dict(point=f"{p['crew']} {p['rung']} j{p['j']}", max_total_pct=round(100 * m, 6)))
        worst = max(worst, abs(m - E.MOD_CAP_FRACTION))
    out["campaign_max_abs_dev_from_105_pct"] = 100 * worst
    print("campaign: every story point max total = 105% within", 100 * worst, "pct-points")
    json.dump(out, open("check105.json", "w"), indent=1)


if __name__ == "__main__":
    main()
