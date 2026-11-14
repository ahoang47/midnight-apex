"""Mod tier level floors (econ-v1, Austin go-ahead 2026-11-13): T1 L0, T2 L13, T3 L30, T4 L47 + the P1 win."""
import sys
sys.path.insert(0, ".")
from velocity_shift import equations as E, progression as P


def test_floors_sit_at_round_starts():
    f = E.MOD_TIER_LEVEL_FLOOR
    assert f == {"T1": 0, "T2": 13, "T3": 30, "T4": 47}
    caps = E.CAP_LEVEL
    assert f["T2"] == caps[0] + 1 and f["T3"] == caps[1] + 1 and f["T4"] == caps[2] + 1   # first level of R2 / R3 / finale
    assert f["T4"] <= E.FINALE_CAP_LEVEL[0]                                              # reachable before F1


def test_floor_gates_tier_availability():
    for tier, lv in E.MOD_TIER_LEVEL_FLOOR.items():
        if lv > 0:
            assert not P.mod_tier_available(tier, lv - 1, rounds_done=3, t4_unlocked=True)   # "requires level N"
        assert P.mod_tier_available(tier, lv, rounds_done=3, t4_unlocked=True)
    assert not P.mod_tier_available("T4", 60, rounds_done=3, t4_unlocked=False)          # T4 also needs the P1 win
    assert E.T4_UNLOCK_RACE == "P1" and E.T4_PACKAGE == {"regular": 5, "aero": 1}


def test_shop_funds_the_cap_on_the_mixed_walk():
    """Criterion 1: after debt, R1 cash covers 6 x T1; each later round's income covers 6 x that tier (list price)."""
    w = P.run("mixed"); n = E.MOD_SLOTS
    left = w[0]["money"] - n * E.mod_price("T1")
    assert w[0]["debt"] == 0.0 and left >= 0
    pool2 = left + w[1]["money"] - w[0]["money"]; assert pool2 >= n * E.mod_price("T2")
    pool3 = pool2 - n * E.mod_price("T2") + w[2]["money"] - w[1]["money"]; assert pool3 >= n * E.mod_price("T3")


def test_aero_rules():
    assert E.AERO_MAX_EQUIPPED == 1 and E.AERO_PRICE_MULT == 1.75 and E.AERO_UNLOCK_AFTER == 1 and E.AERO_FREE_POOL_MAX_FRACTION == 0.10
