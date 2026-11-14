"""Headless check: does the LIVE sim engine (sim/velocity_shift SimulationRunner, G2 heat rules) reproduce the Variant C
at-cap boss win rates in RESULTS.md?  Barry, 2026-11-13, for the econ-v1 go-live.

The econ-v1 tables were made with resources_v4b.run_new on the touge-lines-v1 DRAFT track set (Street/Wangan 2 layouts
x CW/CCW, Touge 1 layout uphill/downhill, Touge grade PLACEHOLDER). This script installs that track set and the grade
tilt IN MEMORY ONLY (sim/config is not touched), then runs the live engine at the exact boss r with the district tunes,
3 boss styles, 4 profiles.  --live-tracks runs the same races on config/tracks_v1.json instead (no install).
--sweep-qte feeds the live runner the sweep's raw QTE (0.8 flat for the 0.8-timing profiles) instead of the live
visible-zone mapping raw_qte_score(r, q_time=0.8).

Usage (from this folder): python check_live_bosses.py [--n 2000] [--live-tracks] [--sweep-qte] [--out file.json]
"""
from __future__ import annotations
import argparse, json, os, sys, time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "sim"))

from velocity_shift import combat as C, heat as H, simulation as S, equations as E, match as MT  # noqa: E402
from velocity_shift.models import CombatantStats, MatchConfig  # noqa: E402

DRAFT = json.load(open(os.path.join(ROOT, "unapproved", "barry", "touge-lines-v1", "tracks_draft.json")))
GRADE_UP, GRADE_DOWN = 0.085, 0.050
TUNES = {"street": (0.50, 0.25, 0.25), "wangan": (0.25, 0.30, 0.45), "touge": (0.40, 0.30, 0.30)}   # POW, HAN, EN
BOSS = {"street": 1.0531373047294503, "wangan": 1.0405116620589814, "touge": 1.0656022367666107}  # exact grid r
PROFILES = {"c6060": (0.6, 0.6, 0.6), "c6080": (0.6, 0.8, 0.8), "c8060": (0.8, 0.6, 0.6), "c8080": (0.8, 0.8, 0.8)}
SEED0 = 20261113
_orig_tw = H._track_wear.__wrapped__ if hasattr(H._track_wear, "__wrapped__") else None


def install(live_tracks: bool, sweep_qte: bool):
    if not live_tracks:
        C._TRACKS_CACHE = {d: {n: list(s) for n, s in laps.items()} for d, laps in DRAFT["tracks"].items()}
        up = tuple(DRAFT["tracks"]["touge"]["T_Uphill"]); down = tuple(DRAFT["tracks"]["touge"]["T_Downhill"])
        base = _orig_tw

        from functools import lru_cache

        @lru_cache(maxsize=None)
        def tw(district, lap):
            w = base(district, lap)
            if district != "touge" or lap not in (up, down):
                return w
            m = (1 + GRADE_UP, 1.0, 1 - GRADE_DOWN) if lap == up else (1 - GRADE_DOWN, 1.0, 1 + GRADE_UP)
            raw = H.raw_track_demand(district, lap)
            w2 = [a * b for a, b in zip(w, m)]
            t0 = sum(r * a for r, a in zip(raw, w)); t1 = sum(r * a for r, a in zip(raw, w2))
            return tuple(a * t0 / t1 for a in w2)
        H._track_wear = tw
    H._avg_raw.cache_clear(); H.avg_heat_demand.cache_clear()
    if sweep_qte and not getattr(S.raw_qte_score, "_sweep", False):
        orig = E.raw_qte_score

        def rq(r, profile=None, q_time=None, window_mod=0.0):
            if q_time is not None and abs(q_time - 0.8) < 1e-12:
                return 0.8                      # sweep convention: 0.8-timing profiles score 0.8 flat
            return orig(r, profile=profile, q_time=q_time, window_mod=window_mod)
        rq._sweep = True
        S.raw_qte_score = rq; MT.raw_qte_score = rq   # runner plan + match payoff


def job(a):
    district, track, style, prof, n, live_tracks, sweep_qte = a
    install(live_tracks, sweep_qte)
    q, qt, pace = PROFILES[prof]
    r = BOSS[district]; opp = 300.0; tot = opp * r
    sp, sh, se = TUNES[district]
    player = CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50)
    o = opp / 3.0; opponent = CombatantStats(name="Opponent", pow=o, en=o, han=o, level=50)
    corners = list(C.official_tracks()[district][track])
    w = 0.0
    for k in range(n):
        cfg = MatchConfig(player_stats=player, opponent_stats=opponent, max_turns=30, seed=SEED0 + (sum(map(ord, track)) * 7 + E.BOSS_STYLES.index(style)) * 100_000 + k,
                          district=district, corners=corners, player_read=q, player_timing=qt, player_pacing=pace,
                          boss_style=style, encounter_type="boss")
        m = S.SimulationRunner(cfg).run().match
        w += 1.0 if m.player_total_progress > m.opponent_total_progress else 0.5 if m.player_total_progress == m.opponent_total_progress else 0.0
    return a, 100.0 * w / n


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--live-tracks", action="store_true"); ap.add_argument("--sweep-qte", action="store_true")
    ap.add_argument("--out", default=None); a = ap.parse_args()
    install(a.live_tracks, a.sweep_qte)
    trk = C.official_tracks()
    jobs = [(d, t, st, p, a.n, a.live_tracks, a.sweep_qte) for d in BOSS for t in sorted(trk[d]) for st in E.BOSS_STYLES for p in PROFILES]
    t0 = time.time(); res = {}
    with Pool(8) as pool:
        for (d, t, st, p, *_), v in pool.imap_unordered(job, jobs):
            res.setdefault(p, {}).setdefault(d, {}).setdefault(t, {})[st] = v
    out = {}
    for p in PROFILES:
        for d in BOSS:
            per = {t: sum(v.values()) / len(v) for t, v in res[p][d].items()}
            out.setdefault(p, {})[d] = dict(district=round(sum(per.values()) / len(per), 1), **{t: round(v, 1) for t, v in per.items()})
    meta = dict(n_per_track_style=a.n, live_tracks=a.live_tracks, sweep_qte=a.sweep_qte, boss_r=BOSS, seconds=round(time.time() - t0, 1))
    print(json.dumps(dict(meta=meta, wr=out), indent=1))
    if a.out:
        json.dump(dict(meta=meta, wr=out), open(os.path.join(HERE, a.out), "w"), indent=1)


if __name__ == "__main__":
    main()
