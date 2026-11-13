"""Heat / load gauges (resources-v4b G2, Austin approved 2026-11-13).

Rules: equations.py "Heat / load resource system"; implementation: heat.py.
The win-rate check is a small smoke test of the G2 headline numbers; the full
reproduction is unapproved/barry/resources-v4/retune/live_spotcheck.py.
"""
from velocity_shift import equations as E
from velocity_shift.heat import HeatGauges, avg_heat_demand, track_wear, raw_track_demand, boss_stance, corner_demand
from velocity_shift.combat import official_tracks
from velocity_shift.models import Stance
from velocity_shift.simulation import simulate_win_rate


def test_wear_normalises_total_and_slants_mix():
    avg = sum(avg_heat_demand())
    for d, tr in official_tracks().items():
        for lap in tr.values():
            raw = raw_track_demand(d, lap)
            w = track_wear(d, lap)
            tot = sum(x * y for x, y in zip(raw, w))
            assert abs(tot - avg) < 1e-9
            # the slanted mix is HEAT_DEMAND_SLANT x further from even than the raw mix
            for x, y in zip(raw, w):
                assert abs((x * y / tot - 1 / 3) - E.HEAT_DEMAND_SLANT * (x / sum(raw) - 1 / 3)) < 1e-9


def test_capacity_and_recovery_scale_with_share_and_r():
    even = HeatGauges((1 / 3, 1 / 3, 1 / 3), 1.0, (1, 1, 1))
    a = avg_heat_demand()
    for i in range(3):
        assert abs(even.cap[i] - E.HEAT_CAP_TURNS * a[i]) < 1e-12
        assert abs(even.rec[i] - E.HEAT_RECOVERY * a[i]) < 1e-12
    pow_car = HeatGauges((0.5, 0.25, 0.25), 1.07, (1, 1, 1))
    assert pow_car.cap[0] > even.cap[0] * 1.07 and pow_car.cap[1] < even.cap[1] * 1.07
    assert abs(sum(c / x for c, x in zip(pow_car.cap, even.cap)) - 3 * 1.07) < 1e-9


def test_overrun_lock_and_hysteresis():
    g = HeatGauges((1 / 3, 1 / 3, 1 / 3), 1.0, (1, 1, 1))
    g.begin_turn()
    g.load[0] = g.cap[0] - 0.1                    # nearly full: still selectable, play overruns
    m, x, limp = g.play(Stance.POW, "SW")
    assert not limp and x > 0 and m == max(E.OVERRUN_FLOOR, 1 - E.OVERRUN_SLOPE * x) and m < 1
    assert g.locked[0] and not g.selectable(Stance.POW)
    g.load[0] = E.HEAT_RELEASE * g.cap[0] + g.rec[0] + 1e-6   # after recovery: just above release -> still locked
    g.end_turn("CR")
    assert g.locked[0]
    g.load[0] = 0.0
    g.end_turn("CR")
    assert not g.locked[0]


def test_repeat_surcharge():
    g = HeatGauges((1 / 3, 1 / 3, 1 / 3), 1.0, (1, 1, 1))
    g.begin_turn()
    c1 = g.cost(Stance.EN, "HP"); g.play(Stance.EN, "HP")
    c2 = g.cost(Stance.EN, "HP")
    assert abs(c2 - c1 * (1 + E.HEAT_REPEAT_SURCHARGE)) < 1e-12


def test_limp_when_all_locked_and_boss_swap():
    g = HeatGauges((1 / 3, 1 / 3, 1 / 3), 1.0, (1, 1, 1), release=0.8)
    g.locked = [True, False, True]
    assert boss_stance(g, Stance.POW) == Stance.HAN
    g.locked = [True, True, True]
    g.load = [g.cap[0], 0.5 * g.cap[1], g.cap[2]]
    assert boss_stance(g, Stance.POW) == Stance.HAN
    m, x, limp = g.play(Stance.HAN, "CR")
    assert limp and m == E.LIMP_MULT


def test_corner_demand_reference_reader():
    d = corner_demand("touge", "HP")
    assert len(d) == 3 and all(x > 0 for x in d)


def test_g2_smoke_targets():
    """Small-N smoke test on one track per district (G2 full runs: perfect at 100% = 100;
    perfect at 80% on 20/30 turns well below perfect at 100%; average at the cap well above 50%)."""
    cap = E.MOD_CAP_FRACTION
    tuned = {"street": (0.5, 0.25, 0.25), "touge": (0.3, 0.25, 0.45), "wangan": (0.25, 0.35, 0.4)}
    perf100 = perf80 = avg = 0.0
    for d, sh in tuned.items():
        name = [next(iter(official_tracks()[d]))]
        perf100 += simulate_win_rate(d, 1.0, 1.0, 20, 11, n_per_track=40, shares=sh, track_names=name) / 3
        perf80 += simulate_win_rate(d, 0.8, 1.0, 30, 12, n_per_track=60, shares=sh, track_names=name) / 3
        avg += simulate_win_rate(d, cap, 0.6, 20, 13, n_per_track=80, shares=sh, track_names=name) / 3
    assert perf100 >= 95.0, perf100
    assert perf80 <= 45.0, perf80
    assert 50.0 <= avg <= 90.0, avg
