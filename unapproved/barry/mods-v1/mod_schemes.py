"""mods-v1 (draft, Barry 2026-11-14): whole-point mod schemes on the 10x skill-point scale, and the car split each one
reaches at every segment cap (R1-R3, arc steps 1-4) for a player who follows the live skill-point rules (25-50 % SP
band, spent points lock, 20 % retune at district changes) and places SP to compensate for the mods.

Live mod model (equations.py): combat = min(C_ceiling, 1.07 x P(L)), P = SP/0.8, i.e. mods fill up to 0.3375 x SP.
On the 10x scale: car points = skill_points(L) + mod points, capped at 1.3375 x skill_points(L) and the round / finale
ceiling. A scheme keeps live balance on the total if a full set of the newest tier always fills that gap."""
import math, itertools, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "sim"))
from velocity_shift import equations as E, progression as P

TUNE = E.DISTRICT_TUNE
SEGS = [  # name, district, entry level, cap level, ceiling (10x points), tier
    ("R1", "street", 0, 12, 10 * E.C_ROUND[0], "T1"),
    ("R2", "wangan", 12, 29, 10 * E.C_ROUND[1], "T2"),
    ("R3", "touge", 29, 46, 10 * E.C_ROUND[2], "T3"),
]
_fc = P.finale_caps()
for i, (d, a, b) in enumerate((("touge", 46, 64), ("wangan", 64, 79), ("street", 79, 94), ("touge", 94, 115))):
    SEGS.append((f"F{i + 1}", d, a, b, 10 * _fc[i][0], "T4"))

SCHEMES = {
    "A_6fixed": dict(slots=6, fixed=("POW", "POW", "HAN", "HAN", "EN", "EN"), pts={"T1": 149, "T2": 171, "T3": 196, "T4": 334}),
    "B_6free": dict(slots=6, fixed=None, pts={"T1": 149, "T2": 171, "T3": 196, "T4": 334}),
    "C_4free": dict(slots=4, fixed=None, pts={"T1": 223, "T2": 256, "T3": 293, "T4": 501}),
    "D_8free": dict(slots=8, fixed=None, pts={"T1": 112, "T2": 128, "T3": 147, "T4": 251}),
}
IDX = {"POW": 0, "HAN": 1, "EN": 2}

def need(seg):
    _, d, a, L, C, t = seg
    sp = E.skill_points(L)
    return min(C, 1.3375 * sp) - sp

def check_fill():
    out = {}
    for k, s in SCHEMES.items():
        rows = []
        for seg in SEGS:
            n, have = need(seg), s["slots"] * s["pts"][seg[5]]
            rows.append((seg[0], round(n, 1), have, have >= n - 1e-9))
        # also every level of each round with the tier available there (T2 opens L13, T3 L30, T4 at P1 / L47)
        worst = 99
        for L in range(0, 116):
            tier = "T1" if L < 13 else "T2" if L < 30 else "T3" if L < 47 else "T4"
            rnd = 0 if L <= 12 else 1 if L <= 29 else 2 if L <= 46 else None
            sp = E.skill_points(L)
            ceil_ = 10 * E.C_ROUND[rnd] if rnd is not None else 10 * _fc[[64, 79, 94, 115].index(next(c for c in (64, 79, 94, 115) if L <= c))][0]
            gap = min(ceil_, 1.3375 * sp) - sp
            worst = min(worst, s["slots"] * s["pts"][tier] - gap)
        out[k] = dict(caps=rows, min_margin_any_level=round(worst, 1))
    return out

# ── SP policy with a target share vector (generalised live add_points / retune) ──
def add_points(alloc, n, tgt_sh):
    a = list(alloc); T = sum(a) + n; tgt = [s * T for s in tgt_sh]; lo, hi = E.stat_band(T)
    for i in range(3):
        g = min(max(0, lo - a[i]), n); a[i] += g; n -= g
    while n > 0:
        cand = [i for i in range(3) if a[i] < hi]
        i = max(cand, key=lambda k: tgt[k] - a[k])
        if tgt[i] - a[i] < 1:
            for k in range(3):
                g = min(n, int(round(tgt_sh[k] * n)) if k < 2 else n, hi - a[k]); a[k] += g; n -= g
            if n > 0:
                k = min(range(3), key=lambda k: a[k] / T); a[k] += n; n = 0
            break
        step = max(1, min(n, int(tgt[i] - a[i]), hi - a[i])); a[i] += step; n -= step
    return E.check_build(a)

def retune(alloc, tgt_sh, frac=E.RETUNE_BUDGET_FRACTION):
    a = list(alloc); T = sum(a); budget = E.retune_budget(T, frac); lo, hi = E.stat_band(T)
    tgt = [s * T for s in tgt_sh]
    while budget > 0:
        sur = [i for i in range(3) if a[i] - tgt[i] >= 1 and a[i] > lo]
        dfc = [i for i in range(3) if tgt[i] - a[i] >= 1 and a[i] < hi]
        if not sur or not dfc: break
        i = max(sur, key=lambda k: a[k] - tgt[k]); j = max(dfc, key=lambda k: tgt[k] - a[k])
        m = min(budget, int(a[i] - tgt[i]), int(tgt[j] - a[j]), a[i] - lo, hi - a[j])
        if m <= 0: break
        a[i] -= m; a[j] += m; budget -= m
    return E.check_retune(alloc, a, frac)

def mod_vectors(s, tier, aero=False):
    """All (label, POW/HAN/EN points) a full set can give. aero: one slot is an aero part (same total, base
    = total - pool in that slot's stat, pool = floor(10 % x total) placed freely in steps of 1)."""
    v = s["pts"][tier]; out = []
    if s["fixed"]:
        combos = [tuple(s["fixed"])]
    else:
        combos = [c for c in itertools.combinations_with_replacement(("POW", "HAN", "EN"), s["slots"])]
    for c in combos:
        base = [0, 0, 0]
        for x in c: base[IDX[x]] += v
        if not aero:
            out.append(("".join(x[0] for x in c), tuple(base)))
        else:
            pool = int(math.floor(E.AERO_FREE_POOL_MAX_FRACTION * v + 1e-9))
            for slot in set(c):                     # which slot holds the aero (its base stays that stat)
                for pp in range(0, pool + 1, max(1, pool // 6)):
                    for ph in range(0, pool - pp + 1, max(1, pool // 6)):
                        pe = pool - pp - ph; b = list(base); b[IDX[slot]] -= pool
                        b[0] += pp; b[1] += ph; b[2] += pe
                        out.append(("".join(x[0] for x in c) + f"+aero@{slot[0]}({pp}/{ph}/{pe})", tuple(b)))
    return out

def car(sp_alloc, mods, seg):
    """Car points after the 1.07 x P / ceiling clip (mods scaled down proportionally when over)."""
    n = need(seg) if seg[3] == E.skill_points.__defaults__ else None
    sp = sum(sp_alloc); _, d, a, L, C, t = seg
    gap = min(C, 1.3375 * sp) - sp; m = sum(mods); k = min(1.0, gap / m) if m else 0.0
    return tuple(x + k * y for x, y in zip(sp_alloc, mods))

def shares(v):
    t = sum(v); return tuple(x / t for x in v)

def dist(sh, d):
    return sum(abs(a - b) for a, b in zip(sh, TUNE[d]))

def walk(scheme, aero=False, aero_from="R2", lock_t4=False):
    """Segment by segment: pick the mod set (and SP target) whose car split at the cap is closest to the district tune,
    keeping SP inside its band and the car inside 25-50 %. Returns rows with SP, mods, car shares."""
    s = SCHEMES[scheme]; alloc = P.start_build(); L_prev = 0; rows = []
    order = [x[0] for x in SEGS]
    for seg in SEGS:
        name, d, a, L, C, tier = seg
        use_aero = aero and order.index(name) >= order.index(aero_from)
        best = None
        cands = mod_vectors(s, tier, use_aero)
        if lock_t4 and name in ("F2", "F3", "F4"):
            cands = [(rows[3]["mods"], rows[3]["mod_pts"])]          # T4 parts bought for F1 keep their stats
        for lab, mv in cands:
            sp_T = E.skill_points(L); gap = min(C, 1.3375 * sp_T) - sp_T; k = min(1.0, gap / sum(mv))
            m_eff = [k * x for x in mv]; tot = sp_T + sum(m_eff)
            want = [TUNE[d][i] * tot - m_eff[i] for i in range(3)]
            lo, hi = 0.25 * sp_T, 0.50 * sp_T
            want = [min(hi, max(lo, w)) for w in want]; sw = sum(want); q = tuple(w / sw for w in want)
            al = alloc if name == "R1" else retune(alloc, q)
            al = add_points(al, E.skill_points(L) - E.skill_points(L_prev if name != "R1" else 0), q) if name != "R1" else \
                add_points(al, E.skill_points(L) - E.skill_points(0), q)
            cv = car(al, mv, seg); sh = shares(cv)
            if (min(sh) < 0.25 - 1e-9 or max(sh) > 0.50 + 1e-9) and len(cands) > 1:
                continue
            sc = dist(sh, d)
            if best is None or sc < best[0] - 1e-12:
                best = (sc, lab, mv, al, sh, q)
        sc, lab, mv, al, sh, q = best
        rows.append(dict(seg=name, district=d, cap=L, tier=tier, mods=lab, mod_pts=mv, sp=al, sp_share=tuple(round(100 * x, 1) for x in shares(al)),
                         car_share=tuple(round(100 * x, 1) for x in sh), car_split=tuple(round(x, 4) for x in sh), dist=round(100 * sc, 2),
                         q=q, sp_prev=alloc))
        alloc, L_prev = al, L
    return rows

if __name__ == "__main__":
    import json
    print(json.dumps(check_fill(), indent=1))
    for k in SCHEMES:
        for aero, lk in ((False, False), (True, False), (False, True)):
            print("==", k, "aero" if aero else "", "T4 locked" if lk else "")
            for r in walk(k, aero, lock_t4=lk): print("  ", r["seg"], r["district"], "L", r["cap"], r["mods"], "SP", r["sp_share"], "car", r["car_share"], "off", r["dist"])
