"""Batches: live SimulationRunner vs SpiritRunner on the same seeds (paired). Profiles as econ-v1-live-tracks/livesim.py."""
from __future__ import annotations
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from spirit_match import SpiritRunner, Spirit, S  # noqa
from velocity_shift import combat as C, equations as E  # noqa
from velocity_shift.models import CombatantStats, MatchConfig  # noqa

TUNE = {"street": (0.5, 0.25, 0.25), "wangan": (0.25, 0.25, 0.5), "touge": (0.45, 0.25, 0.3)}  # POW, HAN, EN


def cfg_of(d, track, T, style, q, qt, pace, r, tune, seed):
    tot = 300.0 * r; sp, sh, se = tune
    pl = CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50)
    op = CombatantStats(name="Opponent", pow=100.0, en=100.0, han=100.0, level=50)
    return MatchConfig(player_stats=pl, opponent_stats=op, max_turns=T, seed=seed, district=d,
                       corners=list(C.official_tracks()[d][track]), player_read=q, player_timing=qt,
                       player_pacing=pace, boss_style=style, encounter_type="boss")


def wv(m):
    a, b = m.player_total_progress, m.opponent_total_progress
    return 1.0 if a > b else 0.5 if a == b else 0.0


def paired(d, tracks, T, skill, r, n, spirits, seed0=20261118, tune=None):
    """Same seeds with and without each Spirit; n races per (track x boss style).
    Returns dict(base=%, n=races, se_base=pp, sp=[dict(win=%, delta=pp, se_delta=pp (paired), acts, buff_turns)])."""
    import math
    q, qt, pace = skill
    tune = tune or TUNE[d]
    w0 = 0.0; N = 0; acc = [[0.0, 0.0, 0.0, 0.0, 0.0] for _ in spirits]   # win, d, d^2, acts, buff turns
    for ti, tr in enumerate(tracks):
        for si, st in enumerate(E.BOSS_STYLES):
            for k in range(n):
                seed = seed0 + T * 1_000_000 + ti * 100_000 + si * 10_000 + k
                b = wv(SpiritRunner(cfg_of(d, tr, T, st, q, qt, pace, r, tune, seed)).run()); w0 += b; N += 1
                for j, sp in enumerate(spirits):
                    mo = []
                    w = wv(SpiritRunner(cfg_of(d, tr, T, st, q, qt, pace, r, tune, seed), sp, mo).run())
                    a = acc[j]; a[0] += w; a[1] += w - b; a[2] += (w - b) ** 2; a[3] += mo[0][0]; a[4] += mo[0][1]
    p = w0 / N
    out = dict(base=100 * p, n=N, se_base=100 * math.sqrt(max(p * (1 - p), 1e-12) / N), sp=[])
    for a in acc:
        md = a[1] / N; var = max(a[2] / N - md * md, 0.0)
        out["sp"].append(dict(win=100 * a[0] / N, delta=100 * md, se_delta=100 * math.sqrt(var / N), acts=a[3] / N, buff_turns=a[4] / N))
    return out


def check_identity(n=40):
    """spirit=None copy == live SimulationRunner, race by race (progress totals)."""
    bad = 0
    for d in TUNE:
        tr = next(iter(C.official_tracks()[d]))
        for k in range(n):
            c = cfg_of(d, tr, 30, E.BOSS_STYLES[k % 3], 0.7, 0.7, 0.7, 1.05, TUNE[d], 777 + k)
            a = S.SimulationRunner(c).run().match; b = SpiritRunner(c).run()
            bad += (a.player_total_progress != b.player_total_progress) or (a.opponent_total_progress != b.opponent_total_progress)
    return bad, 3 * n
