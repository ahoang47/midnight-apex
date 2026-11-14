"""Unified G2 win-rate lookup from round-ladder-v1 sweeps + econ mixed sweep.

Exact-r hits are used for reported numbers. Linear interpolation is available
for the fitter only and is flagged when used.
"""
from __future__ import annotations
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RL = os.path.abspath(os.path.join(HERE, "..", "round-ladder-v1"))

PROFILES = ("c6060", "c6080", "c8060", "c8080")
# meas index per file
# r_sweep / picks: meas 0 = avg 60/60, meas 1 = c8080


def _load(npz, meta):
    m = json.load(open(meta))
    z = np.load(npz)
    return z["arr"], np.array(m["r_grid"], float), [tuple(t) for t in m["tracks"]], m


def _build():
    chunks = []
    # 60/60 = meas 0, 80/80 = meas 1
    for npz, meta in (
        (os.path.join(RL, "results_r_sweep.npz"), os.path.join(RL, "sweep_meta.json")),
        (os.path.join(RL, "results_picks.npz"), os.path.join(RL, "results_picks_meta.json")),
        (os.path.join(RL, "results_picks_grind.npz"), os.path.join(RL, "results_picks_grind_meta.json")),
    ):
        if os.path.exists(npz):
            arr, R, tracks, _ = _load(npz, meta)
            chunks.append(("old", arr, R, tracks))
    mixed = None
    mp = os.path.join(HERE, "results_mixed.npz")
    if os.path.exists(mp):
        arr, R, tracks, _ = _load(mp, os.path.join(HERE, "results_mixed_meta.json"))
        mixed = (arr, R, tracks)
    tracks = chunks[0][3]
    # stack old meas 0 and 1
    old_arr = np.concatenate([c[1] for c in chunks], axis=1)
    old_R = np.concatenate([c[2] for c in chunks])
    return old_arr, old_R, mixed, tracks


_OLD_ARR = _OLD_R = _MIXED = _TRACKS = None


def _init():
    global _OLD_ARR, _OLD_R, _MIXED, _TRACKS
    if _OLD_ARR is None:
        _OLD_ARR, _OLD_R, _MIXED, _TRACKS = _build()
        # means over seeds and styles
        # old: (meas, r, seeds, tracks, len, styles, keys)
        global _OLD_MEAN, _MIX_MEAN, _MIX_R
        _OLD_MEAN = _OLD_ARR.mean(axis=(2, 5))
        if _MIXED:
            _MIX_MEAN = _MIXED[0].mean(axis=(2, 5))
            _MIX_R = _MIXED[1]
        else:
            _MIX_MEAN = _MIX_R = None


def tracks():
    _init()
    return _TRACKS


def _idx(R, r, exact=False, tol=1e-9):
    i = int(np.argmin(np.abs(R - r)))
    err = abs(float(R[i]) - r)
    if exact and err > tol:
        return None, err
    return i, err


def wr(profile, r, T, district=None, track=None, key=0, allow_interp=False):
    """Return (win_pct, r_used, exact, source). key 0=win, 3=limp."""
    _init()
    k = {10: 0, 20: 1, 30: 2}[int(T)]
    if profile in ("c6060", "c8080"):
        meas = 0 if profile == "c6060" else 1
        mean, R, src = _OLD_MEAN, _OLD_R, "ladder-sweep"
    elif profile in ("c6080", "c8060"):
        if _MIX_MEAN is None:
            raise RuntimeError("mixed sweep not loaded")
        meas = 0 if profile == "c6080" else 1
        mean, R, src = _MIX_MEAN, _MIX_R, "mixed-sweep"
    else:
        raise ValueError(profile)
    i, err = _idx(R, r, exact=not allow_interp)
    if i is None and allow_interp:
        # linear between neighbors
        order = np.argsort(R)
        Rs = R[order]
        if r <= Rs[0] or r >= Rs[-1]:
            i = int(np.argmin(np.abs(R - r)))
            err = abs(float(R[i]) - r)
        else:
            j = int(np.searchsorted(Rs, r))
            w = (r - Rs[j - 1]) / (Rs[j] - Rs[j - 1])
            def val(jj):
                ii = int(order[jj])
                if track:
                    ti = next(t for t, (_, n) in enumerate(_TRACKS) if n == track)
                    return float(mean[meas, ii, ti, k, key])
                tis = [t for t, (d, _) in enumerate(_TRACKS) if d == district]
                return float(mean[meas, ii, tis, k, key].mean())
            v = (1 - w) * val(j - 1) + w * val(j)
            return 100 * v, float(r), False, src + "+interp"
    if i is None:
        raise KeyError(f"no exact r={r} in {src} (nearest err={err})")
    if track:
        ti = next(t for t, (_, n) in enumerate(_TRACKS) if n == track)
        v = float(mean[meas, i, ti, k, key])
    else:
        tis = [t for t, (d, _) in enumerate(_TRACKS) if d == district]
        v = float(mean[meas, i, tis, k, key].mean())
    return 100 * v, float(R[i]), err < 1e-9, src


if __name__ == "__main__":
    _init()
    print("old R", len(_OLD_R), "mixed", None if _MIX_R is None else len(_MIX_R), "tracks", len(_TRACKS))
    print("sanity 60/60 street 30 r=1.07", wr("c6060", 1.07, 30, district="street"))
