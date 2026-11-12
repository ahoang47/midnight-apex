"""Crew-local level floor on the mature #2 mod tier (slots-v2 fix b3, Austin approved 2026-11-12)."""
import os
import sys
sys.path.insert(0, ".")
from velocity_shift import equations as E, progression as P

_NOTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "design", "notes", "slots-v2")


def test_floor_constants_are_the_derivation_in_every_order():
    """MOD_TIER_LEVEL_FLOOR is the output of derive_mod_tier_floors() and is keyed by play position (all 216 orders)."""
    assert set(E.MOD_TIER_LEVEL_FLOOR) == {(r, p) for r in (1, 2, 3) for p in range(3)}
    for order in P.all_orders():
        assert P.derive_mod_tier_floors(order) == E.MOD_TIER_LEVEL_FLOOR
    R = P.ladder()[0]
    for x in R:
        if x["kind"] != "scripted" and x["j"] == E.MOD_TIER_FLOOR_RUNG:
            assert P.mod_tier_floor(x["rnd"], x["pos"], x["j"]) <= x["L"]          # never above the rung's level cap


def test_floor_gates_tier_availability():
    for (rnd, pos), f in E.MOD_TIER_LEVEL_FLOOR.items():
        assert not P.mod_tier_available(rnd, pos, E.MOD_TIER_FLOOR_RUNG, f - 1)    # "requires level N", even if affordable
        assert P.mod_tier_available(rnd, pos, E.MOD_TIER_FLOOR_RUNG, f)
        for j in range(7):
            if j != E.MOD_TIER_FLOOR_RUNG:
                assert P.mod_tier_available(rnd, pos, j, 0)                         # only the mature #2 tier is floored


def test_locked_tier_races_with_previous_mods_until_floor():
    """Below the floor the mature #2 skip state keeps the previous rung's mods; the tier is fitted once the level is reached."""
    for policy in ("forced", "never"):
        rows, _ = P.run(policy)
        crews = [r for r in rows if r["crew"] not in ("Prologue", "Finale")]
        locked = [r for r in crews if r["tier_locked"]]
        assert locked and all(r["j"] == E.MOD_TIER_FLOOR_RUNG and r["story_level"] < r["tier_floor"] for r in locked)
        for r in crews:
            if r["j"] == E.MOD_TIER_FLOOR_RUNG:
                prev = next(p for p in crews if p["crew"] == r["crew"] and p["j"] == r["j"] - 1)
                assert r["mods_skip"] == (prev["mods"] if r["tier_locked"] else r["mods"])
            elif r["j"] > E.MOD_TIER_FLOOR_RUNG:
                m3 = next(p for p in crews if p["crew"] == r["crew"] and p["j"] == E.MOD_TIER_FLOOR_RUNG)
                if not m3["tier_locked"] or r["story_level"] >= m3["tier_floor"] or m3["grind_races"]:
                    assert r["mods_skip"] == r["mods"]
    rows, _ = P.run("forced")
    m2 = {r["crew"]: r for r in rows if r["j"] == E.MOD_TIER_FLOOR_RUNG and r["crew"] != "Finale"}
    assert [c for c, r in m2.items() if r["tier_locked"]] == ["R1 Touge"]      # average play: the only locked skip state
    assert m2["R1 Touge"]["grind_races"] == 7                                   # ... already a wall: same grind as before


def test_strong_mature2_not_decided_by_newest_mod():
    """Study check (b3): no strong-profile mature #2 (or boss) clear depends on the newest mod, balanced/window/aero10,
    default order. Uses the share-grid oracle (numpy + banks outside the repo); skipped when those are not on the machine."""
    try:
        import numpy  # noqa: F401
        sys.path.insert(0, _NOTES)
        import b3_check as C
        if not os.path.exists(os.path.join(C.M.GRID_DIR, "p+0_h+0.npz")):
            raise ImportError("share-grid banks not found")
    except ImportError as e:
        try:
            import pytest
            pytest.skip(f"oracle unavailable: {e}")
        except ImportError:
            print(f"SKIP test_strong_mature2_not_decided_by_newest_mod: {e}")
            return
    for policy in C.POLICIES:
        rows, g = C.run(policy, "strong")
        assert C.decisive(rows) == [], (policy, C.decisive(rows))
        assert g == 100, (policy, g)
