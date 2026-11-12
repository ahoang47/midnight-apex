"""slots-v2 model: 3 categories x 2 slots (POW / EN / HAN-primary mods), secondary-split placeholders, window and aero
mods (any slot, max one each), share-aware oracle, exhaustive 105% check, and a loadout-aware progression run.

Barry, 2026-11-11. Draft, NOT approved. Reads the live sim (proto-build) read-only.
"""
from __future__ import annotations
import sys, os, itertools, math
import numpy as np
for p in ("/workspace/barry-drafts/slots-v1", os.path.join(os.path.dirname(__file__), "..", "slots-v1")):
    sys.path.insert(0, p)
sys.path.insert(0, "/workspace/midnight-apex/sim")
from velocity_shift import equations as E, progression as P   # noqa: E402
import wr_shortcut as W                                         # noqa: E402  (phi, kappa; unchanged from qte-v1)
import slots_model as S1                                        # noqa: E402  (slots-v1 scheme C stat schedule)

CATS = ("POW", "EN", "HAN")
IDX = {"POW": 0, "HAN": 1, "EN": 2}          # stat vector order used everywhere here: (POW, HAN, EN) = deck (Attack, Steady, Defend)
SPLITS = {"100/0/0": (1.0, 0.0, 0.0), "80/10/10": (0.8, 0.1, 0.1), "70/20/10": (0.7, 0.2, 0.1)}   # PLACEHOLDERS (primary, sec, ter)
SLOT_CATS = ("POW", "POW", "EN", "EN", "HAN", "HAN")
WINDOW = 0.75                                # slots-v1 candidate: one +75% window mod
ZONE_CAP = 1.15                              # qte-v1 total-zone cap (x w0)
PROFILES = ("weak", "average", "strong")
STEP = 0.025
GRID_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "counts")
SEEDS, LENGTHS, DISTRICTS = W.SEEDS, W.LENGTHS, ("touge", "wangan", "street")
OTHERS = {"POW": ("HAN", "EN"), "EN": ("POW", "HAN"), "HAN": ("POW", "EN")}


# ------------------------------------------------------------------ mods
def mod_vec(cat: str, split: str, sec: str | None = None) -> np.ndarray:
    """Stat vector (POW, HAN, EN) of a 1-point mod of category `cat`. For 70/20/10, `sec` names the stat that gets 20."""
    a, b, c = SPLITS[split]
    o1, o2 = OTHERS[cat]
    if sec is None:
        sec = o1
    ter = o2 if sec == o1 else o1
    v = np.zeros(3); v[IDX[cat]] = a; v[IDX[sec]] += b; v[IDX[ter]] += c
    return v


def variants(cat: str, split: str):
    """Distinct sidegrade variants of one tier: 70/20/10 has two (which other stat gets 20); others one."""
    if split == "70/20/10":
        return [(o, mod_vec(cat, split, o)) for o in OTHERS[cat]]
    return [(None, mod_vec(cat, split))]


# ------------------------------------------------------------------ oracle on the share grid
_BANK = {}


def bank(kp, kh):
    key = (kp, kh)
    if key not in _BANK:
        raw = dict(np.load(os.path.join(GRID_DIR, f"p{kp:+d}_h{kh:+d}.npz")))
        _BANK[key] = {(d, sd, L): raw[f"{d}_{sd}_{L}"].astype(float) for d in DISTRICTS for sd in SEEDS for L in LENGTHS}
    return _BANK[key]


def zone(r, wm):
    z0 = E.qte_zone_width(r, 0.0)
    return z0 if wm == 0 else min(E.qte_zone_width(r, wm), max(ZONE_CAP, z0))


def _wr_from_bank(bk, d, r, shares, qraw):
    p, h, e = shares
    qe = min(max(qraw * (1.0 + E.ETA * (h - 1 / 3)), 0.0), 1.0)
    mw = 1.0 + E.MU * (p - 1 / 3); mo = 1.0 + E.MU * (e - 1 / 3)
    ph = W.phi(qe) * np.array([mw, mo, mo]); po = W.phi(W.OPPONENT_QTE)
    out = []
    for sd in SEEDS:
        for L in LENGTHS:
            cnt = bk[(d, sd, L)]
            gp = (r ** W.KAPPA[L]) * (cnt @ ph); go = cnt[:, ::-1] @ po
            out.append(100.0 * float(np.mean((gp > go) + 0.5 * (gp == go))))
    return np.array(out)


def tri(shares):
    """Barycentric triangle on the (kp, kh) grid containing the share point; returns [((kp,kh), weight)]."""
    x = (shares[0] - 1 / 3) / STEP; y = (shares[1] - 1 / 3) / STEP
    i, j = math.floor(x + 1e-12), math.floor(y + 1e-12); fx, fy = x - i, y - j
    if fx + fy <= 1:
        return [((i, j), 1 - fx - fy), ((i + 1, j), fx), ((i, j + 1), fy)]
    return [((i + 1, j + 1), fx + fy - 1), ((i + 1, j), 1 - fy), ((i, j + 1), 1 - fx)]


def wr(stats, B, profile, wm, district):
    """9 win rates (%) for player stats (POW, HAN, EN) vs a balanced opponent of budget B. district 'pooled' = equal mean."""
    stats = np.asarray(stats, float); tot = stats.sum(); r = tot / B; sh = stats / tot
    qraw = E.expected_hit_quality(E.QTE_SKILL_SIGMA_OVER_A0[profile], zone(r, wm))
    ds = DISTRICTS if district == "pooled" else (district,)
    acc = 0
    for (kp, kh), w in tri(sh):
        if w <= 1e-12:
            continue
        bk = bank(kp, kh)
        acc = acc + w * np.mean([_wr_from_bank(bk, d, r, sh, qraw) for d in ds], axis=0)
    return acc


def mid(v):
    return 0.5 * (float(np.min(v)) + float(np.max(v)))


# ------------------------------------------------------------------ loadouts (Austin layout and counterfactual)
def austin_loadouts(split, v, aero_ok, aero_pool=None, pool_grid=4, default_secs_only=False):
    """All distinct stat vectors of mod loadouts under 2 POW / 2 EN / 2 HAN slots, each slot at its top tier (value v).
    Options: 70/20/10 sidegrade choice per slot; one window mod in any slot (that slot's stat mod removed); one aero part in
    any slot (from DEBT_CLEAR_AFTER): base (1-pool)*v with the slot's split, pool*v freely assigned (grid step 1/pool_grid).
    Yields (label, mods_vector, window_mod)."""
    per_slot = [variants(c, split) for c in SLOT_CATS]
    v = np.broadcast_to(np.asarray(v, float), (6,))      # per-slot top-tier value (scalar = equal slots)
    seen = {}
    allocs = [np.array([a, b, pool_grid - a - b]) / pool_grid for a in range(pool_grid + 1) for b in range(pool_grid + 1 - a)]
    combos = itertools.product(*[range(len(ps)) for ps in per_slot])
    if default_secs_only:                                 # secondaries fixed to the alternating default (P1->H, P2->E, ...)
        combos = [tuple(s % 2 if len(per_slot[s]) > 1 else 0 for s in range(6))]
    for combo in combos:
        vecs = [per_slot[s][combo[s]][1] * v[s] for s in range(6)]
        secs = "".join("-" if per_slot[s][combo[s]][0] is None else per_slot[s][combo[s]][0][0] for s in range(6))
        base = sum(vecs)
        cands = [(f"fixed[{secs}]", base, 0.0, None)]
        for s in range(6):
            cands.append((f"window@{SLOT_CATS[s]}[{secs}]", base - vecs[s], WINDOW, None))
        if aero_ok and aero_pool is not None:
            for s in range(6):
                for al in allocs:
                    av = (1 - aero_pool) * vecs[s] + aero_pool * v[s] * al
                    cands.append((f"aero@{SLOT_CATS[s]} pool->P{al[0]:.2f}/H{al[1]:.2f}/E{al[2]:.2f}[{secs}]", base - vecs[s] + av, 0.0, "aero"))
                    for s2 in range(6):
                        if s2 != s:
                            cands.append((f"aero@{SLOT_CATS[s]}+window@{SLOT_CATS[s2]} P{al[0]:.2f}/H{al[1]:.2f}/E{al[2]:.2f}[{secs}]",
                                          base - vecs[s] - vecs[s2] + av, WINDOW, "aero+window"))
        for lab, vec, wm, kind in cands:
            key = (tuple(np.round(vec, 9)), wm)
            if key not in seen:
                seen[key] = (lab, vec, wm, kind)
    return list(seen.values())


def default_vec(split, v):
    """The 'plain' 2/2/2 loadout: every slot at its top tier, 70/20/10 secondaries alternated (P1->H, P2->E, ...) so they cancel."""
    v = np.broadcast_to(np.asarray(v, float), (6,))
    return sum(mod_vec(c, split, OTHERS[c][s % 2]) * v[s] for s, c in enumerate(SLOT_CATS))


def free_mixes(split, v):
    """COUNTERFACTUAL (not Austin's layout): any category in any slot. 70/20/10 secondaries go half/half (balanced)."""
    out = []
    for nP in range(7):
        for nE in range(7 - nP):
            nH = 6 - nP - nE
            vec = np.zeros(3)
            for cat, n in (("POW", nP), ("EN", nE), ("HAN", nH)):
                if split == "70/20/10":
                    o1, o2 = OTHERS[cat]
                    vec += v * (n / 2) * (mod_vec(cat, split, o1) + mod_vec(cat, split, o2))
                else:
                    vec += v * n * mod_vec(cat, split)
            out.append((f"{nP}P/{nE}E/{nH}H", vec))
    return out


def wr_batch(configs, B, profile, district):
    """Batched wr(): configs = [(stats(POW,HAN,EN), window_mod)]. Returns array (K, 9). Same math as wr()."""
    K = len(configs)
    sig = E.QTE_SKILL_SIGMA_OVER_A0[profile]
    rs = np.empty(K); PH = np.empty((3, K)); tris = []
    for k, (st, wm) in enumerate(configs):
        st = np.asarray(st, float); tot = st.sum(); r = tot / B; sh = st / tot
        qraw = E.expected_hit_quality(sig, zone(r, wm))
        qe = min(max(qraw * (1.0 + E.ETA * (sh[1] - 1 / 3)), 0.0), 1.0)
        mw = 1.0 + E.MU * (sh[0] - 1 / 3); mo = 1.0 + E.MU * (sh[2] - 1 / 3)
        PH[:, k] = W.phi(qe) * np.array([mw, mo, mo]); rs[k] = r; tris.append(tri(sh))
    po = W.phi(W.OPPONENT_QTE)
    verts = {}
    for k, t in enumerate(tris):
        for v, w in t:
            if w > 1e-12:
                verts.setdefault(v, []).append((k, w))
    ds = DISTRICTS if district == "pooled" else (district,)
    out = np.zeros((K, 9))
    for v, lst in verts.items():
        bk = bank(*v); ks = np.array([k for k, _ in lst]); ws = np.array([w for _, w in lst])
        col = 0
        for sd in SEEDS:
            for L in LENGTHS:
                acc = np.zeros(len(ks))
                for d in ds:
                    cnt = bk[(d, sd, L)]
                    gp = (cnt @ PH[:, ks]) * (rs[ks] ** W.KAPPA[L]); go = (cnt[:, ::-1] @ po)[:, None]
                    acc += 100.0 * np.mean((gp > go) + 0.5 * (gp == go), axis=0)
                out[ks, col] += ws * acc / len(ds); col += 1
    return out
