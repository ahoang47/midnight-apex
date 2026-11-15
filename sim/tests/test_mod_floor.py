"""Mod unlocks (mods-v1, Austin 2026-11-14): level floors are replaced by rung unlocks. Reiko's shop opens on the
Prologue race-3 win (MOD_UNLOCK_RACE); each round's Mk1 set opens with the round, Mk2 after the mat1 win, Mk3 after
the mat2 win; the arc's MYTH1-4 after P1 / F1 / F2 / F3."""
import sys
sys.path.insert(0, ".")
from velocity_shift import equations as E, progression as P


def test_unlock_race_and_no_level_floor():
    assert E.MOD_UNLOCK_RACE == 3 and not E.mod_shop_open(2) and E.mod_shop_open(3)
    assert not hasattr(E, "MOD_TIER_LEVEL_FLOOR")
    assert E.T4_UNLOCK_RACE == "P1" and E.T4_PACKAGE == {"regular": 3, "aero": 1, "mod": "MYTH4"}


def test_unlock_schedule():
    for mid, u in E.MOD_UNLOCK.items():
        g, mk = E.MOD_CATALOG[mid]["group"], E.MOD_CATALOG[mid]["mk"]
        if g == "ARC":
            assert u == ("arc", {"MYTH1": "P1", "MYTH2": "F1", "MYTH3": "F2", "MYTH4": "F3"}[mk]), mid
        else:
            r = int(g[1]) - 1
            assert u == {"MK1": ("open", r), "MK2": (r, "mat1"), "MK3": (r, "mat2")}[mk], mid
    assert P.mod_unlocked("MOD_R1_POW_MK1", {("open", 0)}) and not P.mod_unlocked("MOD_R1_POW_MK2", {("open", 0)})
    assert P.mod_unlocked("MOD_R1_HAN_MK2_AERO", {(0, "mat1")})
    assert [a["id"] for a in P.finale_arc() if a["mod_unlock"]] == ["P1", "F1", "F2", "F3"]


def test_buyer_fills_from_mat1_on():
    """Every walk is (near) fully filled from R1 mat1 on; R1 kid1 / kid2 run on stock parts or a part set."""
    for mode in ("story", "mixed", "hard"):
        rows = [r for w in P.run(mode) for r in w["rows"]]
        assert all(r["fill"] >= 99.5 for r in rows[2:]), mode
        assert rows[0]["cash_pre"] == 0.0


def test_aero_rules():
    assert E.AERO_MAX_EQUIPPED == 1 and E.AERO_PRICE_MULT == 1.75 and E.AERO_UNLOCK_AFTER == 1 and E.AERO_FREE_POOL_MAX_FRACTION == 0.10
