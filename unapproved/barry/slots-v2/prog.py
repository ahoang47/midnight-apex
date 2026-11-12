"""slots-v2 grind counts: progression.run (proto-build) copy with a loadout-aware clear test.
At each story rung the player takes the best allowed loadout at the skip state (pooled mid); clear = mid >= 50 (official).
Policies: balanced (all six top-tier mods, symmetric secondaries) | layout (+ 70/20/10 sidegrade choice) |
window (+ one +75% window mod in any slot, 1.15 w0 cap) | aeroXX (+ one aero part, pool XX%, any slot, from DEBT_CLEAR_AFTER)."""
import json, sys
import numpy as np
import model as M
import cells as R

E, P = M.E, M.P


def best_mid(sp, v, B, split, policy, aero_ok, profile):
    spv = np.full(3, sp / 3)
    if policy == "balanced":
        cf = [("balanced", spv + M.default_vec(split, v), 0.0)]
    else:
        m0, lab0 = best_mid(sp, v, B, split, "balanced", aero_ok, profile)
        if m0 >= E.CLEAR_THRESHOLD:
            return m0, lab0                     # already clears with the plain loadout; choice cannot add grind
        pool = float(policy[4:6]) / 100 if policy.startswith("aero") else None
        cf = []
        # 70/20/10 + aero: secondaries held at the default (the sidegrade choice is worth <1 pp, see results.json), else too slow
        for lab, vec, wm, kind in M.austin_loadouts(split, v, aero_ok and pool is not None, pool, default_secs_only=(pool is not None and split == "70/20/10")):
            if (policy == "layout" or policy.endswith("nw")) and wm:
                continue
            cf.append((lab, spv + vec, wm))
    V = M.wr_batch([(c[1], c[2]) for c in cf], B, profile, "pooled")
    mids = [M.mid(x) for x in V]; i = int(np.argmax(mids))
    return mids[i], cf[i][0]


def run(split, policy, profile, cap_alloc=None):
    if cap_alloc:
        E.CAP_ALLOC_CREW, E.CAP_ALLOC_ROUND_OPEN = cap_alloc
    SP, XC, X = P.curves(); Rl, Lf, Lstep, budgets, B_last = P.ladder()
    sched = {(s["crew"], s["rung"], s["j"]): s for s in M.S1.schedule("C")}
    xp = 0.0; rows = []; lost = 0.0

    def grind_to(v, cap, j):
        n = 0
        while XC[cap] - v > 1e-9 and n <= 200:
            Ln = P._level(XC, v, cap) + 1
            v = min(v + E.grind_payout_fraction(Ln, j) * X[Ln], XC[cap]); n += 1
        return n, v

    for i, x in enumerate(Rl):
        cap = x["L"]
        if xp > XC[cap] + 1e-9:
            lost += xp - XC[cap]; xp = XC[cap]
        L = P._level(XC, xp, cap)
        if x["kind"] == "scripted":
            clear, m, pick = True, None, "-"
        else:
            m, pick = best_mid(SP[L], (np.array(sched[(x["crew"], x["rung"], x["j"])]["lines"]) if x["crew"] != "Prologue" else x["mods"] / 6), x["B"], split, policy, R.aero_ok(x["crew"]), profile); clear = m >= E.CLEAR_THRESHOLD
        n, v2 = grind_to(xp, cap, max(0, x["j"]))
        g = 0 if clear else n
        if g:
            xp = v2
        rows.append(dict(crew=x["crew"], rung=x["rung"], j=x["j"], grind=g, mid=None if m is None else round(m, 2), pick=pick, sp=SP[L], B=x["B"]))
        nxt = Rl[i + 1]["L"] if i + 1 < len(Rl) else Lf[0]
        unl = XC[Lstep if i + 1 == len(Rl) else nxt] - XC[cap]
        if x["k"] == 2:
            add = 0.0
        elif x["kind"] == "boss" or x["k"] == 3:
            add = E.STORY_XP_BOSS * unl
        else:
            lam = E.STORY_XP_LT_ROUND_OPEN if x["ro"] else E.STORY_XP_LT
            add = max(lam * unl, E.STORY_XP_LT_FLOOR * X[max(1, nxt)])
        before = xp; xp = min(xp + add, XC[nxt]); lost += before + add - xp
    base = E.MOD_SHARE_OF_REF * B_last
    for (nm, d, B), Lc in zip(E.FINALE, Lf):
        if xp > XC[Lc]:
            lost += xp - XC[Lc]; xp = XC[Lc]
        n, v2 = grind_to(xp, Lc, E.TAPER_FINALE_RUNG); xp = v2      # finale: official policy always grinds to cap (86/14)
        rows.append(dict(crew="Finale", rung=nm, j=E.TAPER_FINALE_RUNG, grind=n, mid=None, pick="-"))
    return rows, dict(grind_races=sum(r["grind"] for r in rows), levels=Lf[-1], lost_xp=round(lost))


def job(a):
    split, policy, prof = a
    rows, t = run(split, policy, prof)
    rec = dict(total=t, per_rung=[(r["crew"], r["rung"], r["j"], r["grind"], r["mid"], r["pick"]) for r in rows])
    print(split, policy, prof, t, flush=True)
    return f"{split}|{policy}|{prof}", rec


def main():
    from multiprocessing import Pool
    jobs = [(s, p, f) for s in M.SPLITS for p in ("balanced", "layout", "window", "aero10nw", "aero20nw", "aero30nw", "aero10", "aero20", "aero30")
            if not (p == "layout" and s != "70/20/10") for f in M.PROFILES]
    with Pool(8) as pool:
        out = dict(pool.map(job, jobs, chunksize=1))
    json.dump(out, open("results_grind.json", "w"), separators=(",", ":"))


if __name__ == "__main__":
    main()
