"""slots-v1 model: slot schemes, stat-mod schedules, window-mod loadouts, oracle and progression hook.

Barry, 2026-11-11. Draft, NOT approved. Reads the repo sim at proto-build 4cb5401 (equations.py, progression.py)
and the official clash-count banks (wr_shortcut.py, copied unchanged from design/notes/qte-v1).
"""
from __future__ import annotations
import sys, math
import numpy as np
sys.path.insert(0, "/workspace/midnight-apex/sim")
from velocity_shift import equations as E, progression as P   # noqa: E402
import wr_shortcut as W                                         # noqa: E402

PROFILES = ("weak", "average", "strong")
MAX_WINDOW_MODS = 3                         # most window mods one loadout may carry (also capped at n-1)
WINDOW_SIZES = (0.10, 0.20, 0.30)          # multiplicative widening of w(r), engine MatchConfig.qte_window_mod semantics
BANKS = W.load_banks()
DISTRICTS = ("touge", "wangan", "street")

# ---------------------------------------------------------------- schemes
# Slot count by campaign phase. A: +1 slot at each round opening (R2, R3) and at the finale unlock.
SCHEMES = {
    "A": {"R1": 3, "R2": 4, "R3": 5, "Finale": 6},
    "B": {"R1": 3, "R2": 3, "R3": 3, "Finale": 3},
    "C": {"R1": 6, "R2": 6, "R3": 6, "Finale": 6},
}


RESTOCK_FRACTION = 0.25


def phase(crew: str) -> str:
    return "Finale" if crew == "Finale" else crew.split()[0]


def schedule(scheme: str):
    """Stat-mod line values at every story rung (rule 1: the n equipped top tiers sum to exactly MOD_SHARE_OF_REF * ref).

    Lines = slots. Mods unlock at race 4 (after the race-3 win) with every line at T/n. After that each story win unlocks
    new tier in ONE line, the currently smallest, raised by the whole increment dT (one purchase per win). When dT is
    larger than RESTOCK_FRACTION of an average line (round openings), it is a restock instead: dT raises the smallest
    lines toward a common level (water-filling, several purchases), so lines stay as even as rule 1 allows. A slot added mid-campaign (scheme A) starts empty and takes the increment of
    the win that unlocks it, then later increments until it catches up (it cannot start full without breaking rule 1). Finale (cap-exempt): each finale rung's mods (base + finale mods) split evenly over the n slots.
    Returns list of dicts per story rung (prologue rows excluded) with lines, total, purchase (line index, old, new value).
    """
    R, Lf, Lstep, budgets, B_last = P.ladder()
    SP, _, _ = P.curves()
    out = []; lines = None
    for x in R:
        if x["crew"] == "Prologue":
            continue
        n = SCHEMES[scheme][phase(x["crew"])]; T = x["mods"]
        if lines is None:
            lines = [T / n] * n; buy = ("initial", n, T / n)
        else:
            while len(lines) < n:
                lines.append(0.0)
            dT = T - sum(lines)
            if dT <= 1e-9:
                buy = None                                   # 0-level win: no new stat tier possible (rule 1)
            elif dT > RESTOCK_FRACTION * T / n:
                buy = waterfill(lines, dT)                   # big step (round opening / new slot): restock, lines evened
            else:
                i = min(range(n), key=lambda k: lines[k]); old = lines[i]; lines[i] += dT; buy = [(i, old, lines[i])]
        assert abs(sum(lines) - T) < 1e-6
        out.append(dict(crew=x["crew"], rung=x["rung"], j=x["j"], B=x["B"], L=x["L"], mods=T, n=n, lines=list(lines), buy=buy))
    base = E.MOD_SHARE_OF_REF * B_last
    for (nm, d, B), Lc in zip(E.FINALE, Lf):
        n = SCHEMES[scheme]["Finale"]
        mods = E.MOD_CAP_FRACTION * B - SP[Lc] - base
        T = base + mods
        out.append(dict(crew="Finale", rung=nm, j=E.TAPER_FINALE_RUNG, B=B, L=Lc, mods=T, n=n, lines=[T / n] * n, buy=("finale", n, T / n)))
    return out


def waterfill(lines, dT):
    """Raise the smallest lines toward a common level by dT in total. Returns list of (line, old, new) purchases."""
    order = sorted(range(len(lines)), key=lambda k: lines[k]); rem = dT; k = 1
    while k < len(order) and rem > (lines[order[k]] - lines[order[k - 1]]) * k + 1e-12:
        rem -= (lines[order[k]] - lines[order[k - 1]]) * k; lvl = lines[order[k]]
        for i in order[:k]:
            lines[i] = lvl
        k += 1
    lvl = lines[order[k - 1]] + rem / k
    buys = []
    for i in order[:k]:
        buys.append((i, None, lvl)); lines[i] = lvl
    return buys


# ---------------------------------------------------------------- oracle
def qhat(r: float, profile: str, wm: float) -> float:
    return E.expected_hit_quality(E.QTE_SKILL_SIGMA_OVER_A0[profile], E.qte_zone_width(r, wm))


def wr_vec(r: float, profile: str, wm: float, district: str) -> np.ndarray:
    """9 win rates (3 seeds x 10/20/30 turns), percent. district 'pooled' = equal-weight mean of the three districts."""
    q = qhat(r, profile, wm)
    if district == "pooled":
        return np.mean([wr_vec_q(r, q, d) for d in DISTRICTS], axis=0)
    return wr_vec_q(r, q, district)


def wr_vec_q(r, q, d):
    return np.array([W.wr_one(BANKS[d][(sd, L)], r, q, L) for sd in W.SEEDS for L in W.LENGTHS])


def mid(v) -> float:
    return 0.5 * (float(np.min(v)) + float(np.max(v)))


def loadouts(lines, B):
    """All-stat plus k window mods (k = 1..min(3, n-1)) of one size; drops the k smallest stat lines. Yields (name, dr, wm)."""
    yield ("all stat", 0.0, 0.0)
    s = sorted(lines)
    for k in range(1, min(MAX_WINDOW_MODS, len(lines) - 1) + 1):
        dr = sum(s[:k]) / B
        for w in WINDOW_SIZES:
            yield (f"{k}x+{int(w * 100)}%", dr, k * w)


# ---------------------------------------------------------------- progression with a loadout policy
def run(scheme: str | None, profile: str = "average", policy: str = "forced"):
    """Copy of progression.run (4cb5401) with the clear test made profile- and loadout-aware.

    scheme None = official baseline (all stat mods, official clear rule) but evaluated with this oracle.
    Clear = best loadout's pooled mid win rate at the skip state >= CLEAR_THRESHOLD (50), as in the official rule.
    """
    SP, XC, X = P.curves(); R, Lf, Lstep, budgets, B_last = P.ladder()
    sched = {(s["crew"], s["rung"], s["j"]): s for s in schedule(scheme or "B")}
    xp = 0.0; rows = []; story = grind = lost = 0.0

    def grind_to(v, cap, j):
        n = 0
        while XC[cap] - v > 1e-9 and n <= 200:
            Ln = P._level(XC, v, cap) + 1
            v = min(v + E.grind_payout_fraction(Ln, j) * X[Ln], XC[cap]); n += 1
        return n, v

    def best(r, lines, B, district):
        opts = [("all stat", 0.0, 0.0)] if scheme is None else list(loadouts(lines, B))
        res = [(mid(wr_vec(r - dr, profile, wm, district)), nm) for nm, dr, wm in opts]
        return max(res)

    for i, x in enumerate(R):
        cap = x["L"]
        if xp > XC[cap] + 1e-9:
            lost += xp - XC[cap]; xp = XC[cap]
        L = P._level(XC, xp, cap)
        r_skip = (SP[L] + x["mods"]) / x["B"]
        if x["kind"] == "scripted":
            clear = True; pick = "-"; m = None
        else:
            s = sched[(x["crew"], x["rung"], x["j"])]
            m, pick = best(r_skip, s["lines"], x["B"], "pooled"); clear = m >= E.CLEAR_THRESHOLD
        n, v2 = grind_to(xp, cap, max(0, x["j"]))
        g = n if (policy == "forced" and not clear) else 0
        if g:
            grind += v2 - xp; xp = v2
        rows.append(dict(crew=x["crew"], rung=x["rung"], j=x["j"], B=x["B"], cap=cap, L=L, r_skip=r_skip,
                         r_tgt=(SP[cap] + x["mods"]) / x["B"], grind_races=g, clear=clear, skip_pick=pick, skip_mid=m))
        nxt = R[i + 1]["L"] if i + 1 < len(R) else Lf[0]
        unl = XC[Lstep if i + 1 == len(R) else nxt] - XC[cap]
        if x["k"] == 2:
            add = 0.0
        elif x["kind"] == "boss" or x["k"] == 3:
            add = E.STORY_XP_BOSS * unl
        else:
            lam = E.STORY_XP_LT_ROUND_OPEN if x["ro"] else E.STORY_XP_LT
            add = max(lam * unl, E.STORY_XP_LT_FLOOR * X[max(1, nxt)])
        before = xp; xp = min(xp + add, XC[nxt]); lost += before + add - xp; story += xp - before
    base = E.MOD_SHARE_OF_REF * B_last
    for (nm, d, B), Lc in zip(E.FINALE, Lf):
        if xp > XC[Lc]:
            lost += xp - XC[Lc]; xp = XC[Lc]
        L = P._level(XC, xp, Lc); n, v2 = grind_to(xp, Lc, E.TAPER_FINALE_RUNG)
        mods = E.MOD_CAP_FRACTION * B - SP[Lc] - base
        g = n if policy == "forced" else 0          # finale: official forced policy always grinds to cap (86/14 split)
        if g:
            grind += v2 - xp; xp = v2
        rows.append(dict(crew="Finale", rung=nm, j=E.TAPER_FINALE_RUNG, B=B, cap=Lc, L=L, r_skip=(SP[L] + base + mods) / B,
                         r_tgt=(SP[Lc] + base + mods) / B, grind_races=g, clear=None, skip_pick="-", skip_mid=None, district=d))
    return rows, dict(grind_races=sum(r["grind_races"] for r in rows), levels=Lf[-1], lost_xp=round(lost))
