"""Live-engine race batches on the LIVE stand-in tracks (sim/config/tracks_v1.json), G2 heat rules, live QTE mapping.

Draft for econ-v1-live-tracks (Barry 2026-11-13). Imports sim/ read-only; installs nothing.
Profiles (q_read, q_time = E[s] at the default zone mapped through the live visible zone, pacing share):
  c6060 (0.6, 0.6, 0.6)  c6080 (0.6, 0.8, 0.8)  c8060 (0.8, 0.6, 0.6)  c8080 (0.8, 0.8, 0.8)
"""
from __future__ import annotations
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "sim"))
from velocity_shift import combat as C, simulation as S, equations as E  # noqa: E402
from velocity_shift.models import CombatantStats, MatchConfig  # noqa: E402

PROFILES = {"c6060": (0.6, 0.6, 0.6), "c6080": (0.6, 0.8, 0.8), "c8060": (0.8, 0.6, 0.6), "c8080": (0.8, 0.8, 0.8)}
STYLES = E.BOSS_STYLES
LENGTHS = (10, 20, 30)


def tracks():
    return {d: dict(t) for d, t in C.official_tracks().items()}


def batch(district, track, length, style, prof, r, tune, n, seed):
    """Win % (ties = half) of n live races. tune = (POW, HAN, EN) shares."""
    q, qt, pace = PROFILES[prof]
    opp = 300.0; tot = opp * r; sp, sh, se = tune
    player = CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50)
    o = opp / 3.0; opponent = CombatantStats(name="Opponent", pow=o, en=o, han=o, level=50)
    corners = list(C.official_tracks()[district][track])
    w = 0.0
    for k in range(n):
        cfg = MatchConfig(player_stats=player, opponent_stats=opponent, max_turns=length, seed=seed + k,
                          district=district, corners=corners, player_read=q, player_timing=qt, player_pacing=pace,
                          boss_style=style, encounter_type="boss")
        m = S.SimulationRunner(cfg).run().match
        a, b = m.player_total_progress, m.opponent_total_progress
        w += 1.0 if a > b else 0.5 if a == b else 0.0
    return 100.0 * w / n


def seed_of(*parts):
    """Deterministic seed from strings/ints (no Python hash randomisation)."""
    h = 20261113
    for p in parts:
        for ch in str(p):
            h = (h * 131 + ord(ch)) % 1_000_000_007
    return h * 10
