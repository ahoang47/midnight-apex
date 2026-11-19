"""skill-points-v1 (Austin 2026-11-14): whole skill points at 10x, 25-50 % stat band, spent points lock, 20 % retune
budget at district changes. Pinned numbers: the skill-points-v1 retune (B = 20 %), approved and made live in commit c877a19."""
import sys
sys.path.insert(0, ".")
import pytest
from velocity_shift import equations as E, progression as P
from velocity_shift.heat import HeatGauges
from velocity_shift.models import Stance


def test_whole_points_curve():
    assert E.SP_POINT_SCALE == 10 and E.skill_points(0) == 2400
    gains = [E.skill_points_gained(L) for L in range(1, 116)]
    assert gains[0] == 19 and min(gains) == 19 and max(gains) == 48 and all(isinstance(g, int) for g in gains)
    assert all(abs(E.sp_at_level(L) - E.sp_curve(L)) <= 0.05 + 1e-9 for L in range(116))   # rounding <= 0.05 SP
    assert [E.skill_points(c) for c in E.CAP_LEVEL] == [2640, 3022, 3458]


def test_band_enforced():
    assert E.stat_band(2400) == (600, 1200)
    assert E.check_build((1200, 600, 600)) == (1200, 600, 600)
    for bad in ((1201, 600, 599), (2400, 0, 0), (1000.5, 700, 699.5), (-1, 1201, 1200)):
        with pytest.raises(ValueError):
            E.check_build(bad)


def test_retune_budget():
    assert E.RETUNE_BUDGET_FRACTION == 0.20 and E.retune_budget(2640) == 528
    assert E.RETUNE_ARC_RACES == ("P1", "M11", "M21", "M31")
    a = P.retune((1320, 660, 660), "wangan")
    assert a == (792, 660, 1188) and sum(a) == 2640                     # 528 POW -> EN, POW stops at 30 %
    with pytest.raises(ValueError):
        E.check_retune((1320, 660, 660), (660, 660, 1320))              # 660 moved > 528
    with pytest.raises(ValueError):
        E.check_retune((1320, 660, 660), (1320, 660, 700))              # a retune cannot add points
    assert P.retune((792, 756, 1474), "touge") == (1359, 756, 907)      # Wangan -> Touge: 567 of 604 reaches the tune


def test_new_points_greedy_in_band():
    a = P.add_points((792, 660, 1188), 382, "wangan")
    lo, hi = E.stat_band(sum(a))
    assert sum(a) == 3022 and all(lo <= x <= hi for x in a)
    assert a[0] == 792                                                   # spent POW is never removed
    b = P.Build("wangan", (792, 660, 1188), 12)
    assert b.at(29) == (792, 756, 1474) and round(100 * b.pow_share(29), 1) == 26.2


def test_off_tune_delta():
    r = E.BOSS_TARGET_R["wangan"]
    assert P.track_win("c8080", r, 30, "W3_C1_Outer", 0.25) == P.track_win("c8080", r, 30, "W3_C1_Outer")
    assert P.track_win("c8080", r, 30, "W3_C1_Outer", 0.45) < P.track_win("c8080", r, 30, "W3_C1_Outer") - 10


def test_at_cap_bosses_with_retune_limit():
    rows = P.boss_check_at_cap()
    assert [(x["pow_share"], x["c6060"], x["c8080"]) for x in rows] == [(50.0, 31.2, 93.9), (26.2, 41.5, 93.6), (45.0, 31.1, 91.3)]   # 2026-11-19 retune
    assert all(x["ok"] for x in rows)


def test_zero_stat_does_not_divide_by_zero():
    g = HeatGauges((1.0, 0.0, 0.0), 1.0, (1.0, 1.0, 1.0))
    assert min(g.cap) > 0 and g.overrun_if(Stance.HAN, g_corner()) >= 0 and len(g.fill()) == 3


def g_corner():
    from velocity_shift.heat import CORNER_HEAT_COST
    return next(iter(CORNER_HEAT_COST))
