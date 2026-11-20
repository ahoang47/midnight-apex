"""mod_skill progression (LIVE, Austin approved 2026-11-19 "Approved for all"): S1 one crew per round, M13r (7 story +
6 required wild encounters), stat-locked crews with earned-XP floors (no underdog bonus), non-mandatory XP cap 15 per
round, Mk1/2/3 115/124/133 per slot (R1), Street boss at half stat weight. Targets = E.MS_TARGETS (Austin's G1-G5 + G3c,
design/07). The climb table is config/mod_skill_climb_v1.json (scripts/mod_skill_climb.py, n=6000, live engine)."""
import json
import os
import sys
sys.path.insert(0, ".")
import pytest
from velocity_shift import equations as E, mod_skill as M
from velocity_shift.models import MatchConfig
from velocity_shift.simulation import SimulationRunner

CLIMB = json.load(open(os.path.join(os.path.dirname(__file__), "..", "config", "mod_skill_climb_v1.json")))
T = E.MS_TARGETS


def _col(d, key):
    return [CLIMB["table"][d][r][key] for r in M.RUNGS]


def test_constants():
    assert E.MS_ROUND_CAP_POINTS == (3532, 4060, 4628)   # Wangan 4044 -> 4060 (release-0.5 go-live)
    assert E.MS_TIER_POINTS[0] == (115, 124, 133)                      # approved Mk1/Mk2/Mk3 per slot, R1
    assert all(t[2] == c for t, c in zip(E.MS_TIER_POINTS, E.MS_MOD_CEILING))
    assert E.MS_MANDATORY_PER_ROUND == 13 == len(M.mandatory_sequence(0)) and M.mandatory_sequence(0).count("wild") == 6
    assert E.MS_NM_XP_CAP == 15 and E.MS_BOSS_KAPPA_MULT == {"street": 0.5, "wangan": 1.0, "touge": 1.0}
    assert CLIMB["floor"] == {d: list(v) for d, v in E.MS_FLOOR_POINTS.items()}


def test_floors_are_the_mandatory_path_and_rise():
    assert M.mandatory_path_points() == E.MS_FLOOR_POINTS
    seq = [p for d in M.DISTRICTS for p in E.MS_FLOOR_POINTS[d]]
    assert all(b >= a for a, b in zip(seq, seq[1:]))
    for rnd, d in enumerate(M.DISTRICTS):                             # the boss floor = the round's mandatory XP, and
        assert E.MS_FLOOR_POINTS[d][6] <= E.MS_ROUND_CAP_POINTS[rnd]  # always reachable inside the round's cap
        if rnd:
            assert E.MS_FLOOR_POINTS[d][0] == E.MS_FLOOR_POINTS[M.DISTRICTS[rnd - 1]][6]


def test_crews_are_stat_locked_and_rise():
    for rnd, d in enumerate(M.DISTRICTS):
        b = [M.crew_budget(rnd, r) for r in M.RUNGS]
        assert b == list(E.MS_CREW_BUDGET[d]) and all(y > x for x, y in zip(b, b[1:]))
    assert E.legacy_opponent_budget(0, 0) != E.opponent_budget(0, 0)  # legacy walk keeps its own (superseded) budgets


def test_floor_check_uses_earned_ledger():
    g = M.Garage()
    g.slots[0] = [0, 1, 0.0]                                        # one Mk1 slot: 115 points of room
    lost = g.assign(200)
    assert lost == 85 and g.points() == 3115 and g.ledger == 3200   # unassignable XP is lost from the car ...
    assert M.can_challenge(g.ledger, 0, "mat2")                     # ... but counts toward the floor (3165)
    assert not M.can_challenge(g.points(), 0, "mat2")
    assert not M.can_challenge(3164.9, 0, "mat2") and M.can_challenge(3165, 0, "mat2")


def test_non_mandatory_cap():
    assert [M.nm_xp(0, k) for k in (0, 14, 15, 40)] == [13, 13, 0, 0]
    assert [M.nm_xp(r, 0) for r in range(3)] == list(E.MS_WILD_XP)


def test_garage_shop_and_debt():
    g = M.Garage(money=0.0); g.credit(1000)
    assert g.debt == E.DEBT_AMOUNT - 650 and g.money == 350
    g.shop(0, M.unlocked_mk(0, set()))
    assert sum(1 for s in g.slots if s) == 2 and g.money == 50       # Mk1 $150 each, Mk2 locked until the mat1 win
    assert M.unlocked_mk(0, {(0, "mat1")}) == 2 and M.unlocked_mk(0, {(0, "mat1"), (0, "mat2")}) == 3


def test_ladder_strictly_harder_g3c():
    for d in M.DISTRICTS:
        s = _col(d, "strong_floor")
        steps = [a - b for a, b in zip(s, s[1:])]
        assert min(steps) >= T["G3c_min_step"], (d, steps)
        assert s[0] - s[-1] >= T["G3a_drop_kid1_boss"]


def test_boss_band_and_targets():
    for d in M.DISTRICTS:
        boss = CLIMB["table"][d]["boss"]
        assert T["G1a_boss_strong_floor"][0] <= boss["strong_floor"] <= T["G1a_boss_strong_floor"][1], d          # G1a strong boss at floor 65-70
        assert 66.0 <= boss["strong_floor"] <= 68.0, d                          # Austin: keep the boss at 66-68
        assert min(_col(d, "weak_max")) >= T["G2a_min_weak_max_build"], d                         # G2a 60/60 at max >= 30 everywhere
        assert boss["strong_floor"] - boss["weak_max"] >= T["G3b_boss_read_gap"], d           # G3b
        assert min(_col(d, "strong_floor")) >= T["G4a_min_strong_floor"], d                     # G4a
        assert boss["weak_floor"] <= T["G4b_boss_weak_floor_max"], d                                # G4b
        assert boss["strong_max"] <= T["G5_boss_strong_max_build"] + E.MS_G5_ACCEPTED_MISS.get(d, 0.0), d                                 # G5


def test_kappa_mult_default_is_live_behaviour():
    import dataclasses
    assert {f.name: f.default for f in dataclasses.fields(MatchConfig)}["kappa_mult"] == 1.0
    cfg = M.crew_config(0, "boss", 3392, seed=1, player_read=0.8, player_timing=0.8, player_pacing=0.8)
    assert cfg.kappa_mult == 0.5 and cfg.max_turns == 30 and M.crew_config(1, "boss", 3904).kappa_mult == 1.0
    assert M.crew_config(0, "oh2", 3275).kappa_mult == 1.0


def _wins(rnd, rung, pts, q, n):
    w = 0.0
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(n):
            m = SimulationRunner(M.crew_config(rnd, rung, pts, seed=CLIMB["seed"] + si * 100_000 + k, player_read=q,
                                               player_timing=q, player_pacing=q, boss_style=st)).run().match
            w += 1.0 if m.player_total_progress > m.opponent_total_progress else 0.5 if m.player_total_progress == m.opponent_total_progress else 0.0
    return w


def test_engine_spot_check_street_boss():
    """Deterministic regression: the first 100 seeds per style of the climb's Street boss strong-at-floor cell (n=300
    measured 69.33 % with the live engine after the release-0.5 go-live (was 68.33 at release 0.3); the n=6000 table reads 66.25 %)."""
    assert round(100 * _wins(0, "boss", E.MS_FLOOR_POINTS["street"][6], 0.8, 100) / 300, 2) == 69.33
