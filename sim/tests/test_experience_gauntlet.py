"""Smoke test for scripts/experience_gauntlet.py (the full check runs as its own CI step at n = 6000)."""
import os
import sys

from velocity_shift import equations as E

_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "experience_gauntlet.py")
sys.path.insert(0, os.path.dirname(_p))
import experience_gauntlet as G   # noqa: E402  (importable by name so the worker pool can pickle its job)


def test_smoke_runs_every_goal_on_one_district():
    res, fails = G.evaluate(G.run(30, 2, ["street"]))
    names = [c[0].split()[0] for c in res["street"]["checks"]]
    assert names == ["G1a", "G1b", "G2a", "G2b", "G3a", "G3b", "G3c", "G4a", "G4b", "G5"]
    assert set(res["street"]["feel"]) == {f"{r} {w}" for r in ("kid1", "oh1", "boss") for w in ("strong", "weak")}
    assert all(f.startswith("street: ") for f in fails)


def test_targets_come_from_equations():
    src = open(_p).read()
    assert "MS_TARGETS" in src and "MS_BOSS_BAND" in src and "MS_G5_ACCEPTED_MISS" in src
    assert E.MS_BOSS_BAND[0] >= E.MS_TARGETS["G1a_boss_strong_floor"][0] and E.MS_BOSS_BAND[1] <= E.MS_TARGETS["G1a_boss_strong_floor"][1]


def test_max_build_matches_the_climb_pin():
    import json
    climb = json.load(open(os.path.join(os.path.dirname(_p), "..", "config", "mod_skill_climb_v1.json")))
    assert {d: list(v) for d, v in G.max_build().items()} == climb["max_build"]
