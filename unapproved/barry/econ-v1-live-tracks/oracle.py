"""Live-track win-rate oracle, plugged into the econ-v1 draft machinery (model / evaluate / run_betting_levers /
run_finale_arc) in place of econ-v1 wr.wr.  Barry 2026-11-13, draft only.

Data: sweep_*.json from run_sweep.py (live engine, live stand-in tracks). Linear interpolation in r (the live grid is
0.01 apart, so nearest-point would be up to 0.005 off); flat outside the grid. Several sweeps merge (finer points win).

Hard cells on the live tracks (there are no CW/CCW or uphill/downhill variants in config/tracks_v1.json):
  Street boss  S1 -> S1_Shibuya_Grid (the R1 boss track, same layout as the draft S1; CW and CCW both map to it)
  Touge        uphill -> HARD_TOUGE (default T1_Akina_Switchbacks, the layout the draft uphill was built from);
               "downhill" is reported as the same track (no reversed laps exist live)
The worst track per district is reported separately (worst_track()).
"""
from __future__ import annotations
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ECON = os.path.abspath(os.path.join(HERE, "..", "econ-v1"))
HARD_TOUGE = os.environ.get("HARD_TOUGE", "T1_Akina_Switchbacks")
MAP = {"S1_Shibuya_Grid_CW": "S1_Shibuya_Grid", "S1_Shibuya_Grid_CCW": "S1_Shibuya_Grid",
       "T_Uphill": HARD_TOUGE, "T_Downhill": HARD_TOUGE}
_D = None


def load(paths=None):
    global _D
    if _D is not None and paths is None:
        return _D
    files = paths or [os.path.join(HERE, f) for f in os.environ.get("ORACLE_FILES", "sweep_main.json").split(",")]
    tracks = None; data = {}   # data[pr][T][track] = {r: win}
    for f in files:
        s = json.load(open(f))
        tr = [tuple(t) for t in s["tracks"]]
        tracks = tracks or tr
        for pr, byL in s["win"].items():
            for L, rows in byL.items():
                for ri, r in enumerate(s["r"]):
                    for ti, (d, n) in enumerate(tr):
                        data.setdefault(pr, {}).setdefault(int(L), {}).setdefault(n, {})[round(float(r), 6)] = rows[ri][ti]
    pfiles = [f for f in os.environ.get("ORACLE_POINTS", "").split(",") if f]
    for f in pfiles:   # exact-r high-N point checks (30-turn) override / add grid points
        s = json.load(open(os.path.join(HERE, f)))
        for k, v in s["win"].items():
            d, n, r, pr = k.split("|")
            data[pr][int(s.get("T", 30))][n][round(float(r), 6)] = v
    _D = dict(tracks=tracks, data=data, files=[os.path.basename(f) for f in files] + pfiles)
    return _D


def track_wr(pr, r, T, name):
    pts = load()["data"][pr][int(T)][name]
    rs = sorted(pts)
    if r <= rs[0]:
        return pts[rs[0]]
    if r >= rs[-1]:
        return pts[rs[-1]]
    import bisect
    i = bisect.bisect_left(rs, r)
    if abs(rs[i] - r) < 1e-9:
        return pts[rs[i]]
    a, b = rs[i - 1], rs[i]; w = (r - a) / (b - a)
    return (1 - w) * pts[a] + w * pts[b]


def names(district):
    return [n for d, n in load()["tracks"] if d == district]


def district_wr(pr, r, T, district):
    ns = names(district)
    return sum(track_wr(pr, r, T, n) for n in ns) / len(ns)


def worst_track(pr, r, T, district):
    return min(((track_wr(pr, r, T, n), n) for n in names(district)))


def wr(profile, r, T, district=None, track=None, key=0, allow_interp=False):
    """Drop-in for econ-v1 wr.wr: (win %, r_used, exact, source). key != 0 (limp) has no live data: returns 0."""
    if key != 0:
        return 0.0, float(r), False, "live-tracks(no-limp)"
    if track and MAP.get(track, track) == "mean":
        return district_wr(profile, r, T, "touge"), float(r), False, "live-tracks(mean)"
    if track:
        return track_wr(profile, r, T, MAP.get(track, track)), float(r), False, "live-tracks"
    return district_wr(profile, r, T, district), float(r), False, "live-tracks"


def install():
    """Point the econ-v1 modules at this oracle. Call before importing evaluate / run_betting_levers / run_finale_arc."""
    if ECON not in sys.path:
        sys.path.insert(0, ECON)
    import wr as W
    W.wr = wr
    return W
