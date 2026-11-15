"""Study hooks for touge-lines-v1: draft tracks, Touge gravity wear, optional LINE_SET_C mains.

Does not edit sim/config or equations.py constants. Mutates in-memory tables and
clears demand caches so resources_v4b sees the draft set.
"""
from __future__ import annotations
import copy, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "sim"))
sys.path.insert(0, os.path.join(ROOT, "unapproved", "barry", "resources-v4", "retune"))
sys.path.insert(0, os.path.join(ROOT, "unapproved", "barry", "resources-v2"))
sys.path.insert(0, os.path.join(ROOT, "unapproved", "barry", "resources-v1"))

from velocity_shift import equations as E
from velocity_shift import combat as C
import resources_v4b as R
import resources_v2 as V2

DRAFT = json.load(open(os.path.join(HERE, "tracks_draft.json")))
G2 = json.load(open(os.path.join(ROOT, "unapproved", "barry", "resources-v4", "retune", "candidates_v4b.json")))["G2_slant_m10"]

# Arthur 2026-11-13 (districts README Pass 2): Touge approach 8.5%, exit 5%. PLACEHOLDER tilt.
GRADE_UP = 0.085
GRADE_DOWN = 0.050

_LINE_ORIG = copy.deepcopy(E.LINE_SET_C)
_WEAR_ORIG = R.wear_of
_APPLIED = {"id": None}


def _clear_caches():
    C._TRACKS_CACHE = None
    V2._AVG.clear(); V2._W.clear(); V2._AD.clear()
    R._ADV.clear(); R._CD.clear()
    # live heat caches (unused by v4b runs, kept consistent for demand scripts)
    try:
        from velocity_shift import heat as H
        H.corner_demand.cache_clear()
        H._avg_raw.cache_clear()
        H._track_wear.cache_clear()
        H.avg_heat_demand.cache_clear()
    except Exception:
        pass


def _install_tracks():
    # official_tracks() will accept a pre-built cache
    C._TRACKS_CACHE = {
        d: {name: list(seq) for name, seq in laps.items()}
        for d, laps in DRAFT["tracks"].items()
    }


def _direction(district, lap):
    if district != "touge":
        return None
    up = tuple(DRAFT["tracks"]["touge"]["T_Uphill"])
    down = tuple(DRAFT["tracks"]["touge"]["T_Downhill"])
    t = tuple(lap)
    if t == up:
        return "uphill"
    if t == down:
        return "downhill"
    return None


def _wear_of(district, lap, c):
    w = _WEAR_ORIG(district, lap, c)
    d = _direction(district, lap)
    if not d:
        return w
    if d == "uphill":
        m = np.array([1.0 + GRADE_UP, 1.0, 1.0 - GRADE_DOWN])  # POW, HAN, EN
    else:
        m = np.array([1.0 - GRADE_DOWN, 1.0, 1.0 + GRADE_UP])
    raw = V2.raw_demand(district, lap, c["AGG_STEP"], c["TANK_REF_Q"])
    w2 = np.asarray(w, float) * m
    tot0 = float((raw * w).sum())
    tot1 = float((raw * w2).sum())
    if tot1 <= 0:
        return w
    return w2 * (tot0 / tot1)


def _restore_lines():
    for d in E.LINE_SET_C:
        for k in E.LINE_SET_C[d]:
            E.LINE_SET_C[d][k] = list(_LINE_ORIG[d][k])


def apply(line_edits=None, use_gravity=True, tracks=True):
    """Apply draft tracks, optional Touge main-line edits (alts untouched), gravity on/off."""
    _restore_lines()
    if line_edits:
        for corner, main in line_edits.items():
            cur = list(E.LINE_SET_C["touge"][corner])
            if cur[0][0] != main[0]:
                raise ValueError(f"{corner} main {main} changes Entry {cur[0][0]}; alts would break")
            cur[0] = main
            E.LINE_SET_C["touge"][corner] = cur
    if tracks:
        _install_tracks()
    else:
        C._TRACKS_CACHE = None
    if use_gravity:
        R.wear_of = _wear_of
    else:
        R.wear_of = _WEAR_ORIG
    _clear_caches()
    if tracks:
        _install_tracks()  # _clear_caches set cache to None
    _APPLIED["id"] = (tuple(sorted((line_edits or {}).items())), use_gravity, tracks)
    return _APPLIED["id"]


def g2_cfg():
    return {k: v for k, v in G2.items() if not k.startswith("_")}


def g2_cap():
    return G2["_cap"]


def track_list():
    return sorted(R.tracks().items())  # [( (district, name), lap ), ...]
