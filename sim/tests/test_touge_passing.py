"""Touge passing go-live (Austin 2026-11-20 6:00 PM PT): Touge resolves per phase with smoothed phase QTEs; Street/Wangan don't."""
from velocity_shift import equations as E, mod_skill as M
from velocity_shift.simulation import SimulationRunner


def _match(rnd, **kw):
    d = M.DISTRICTS[rnd]
    cfg = M.crew_config(rnd, 6, E.MS_FLOOR_POINTS[d][6], seed=96_000_000, player_read=0.8, player_timing=0.8,
                        player_pacing=0.8, boss_style=E.BOSS_STYLES[0], **kw)
    return SimulationRunner(cfg).run().match


def test_only_touge_is_per_phase():
    assert E.PER_PHASE_DISTRICTS == ("touge",)
    assert E.PHASE_SMOOTH_W == 0.35
    assert E.MS_CREW_BUDGET["touge"] == (364.96, 389.10, 400.41, 411.94, 421.80, 432.32, 442.14)


def test_touge_turns_carry_phase_qte_and_order():
    m = _match(2)
    for t in m.turn_results:
        assert len(t.player_clash_qte) == 3 and len(t.opponent_clash_qte) == 3 and len(t.phase_order) == 3
    assert m.turn_results[-1].phase_order[-1] == ("player" if m.player_total_progress > m.opponent_total_progress else
                                                  "opponent" if m.opponent_total_progress > m.player_total_progress else "even")


def test_street_wangan_stay_per_turn():
    for rnd in (0, 1):
        m = _match(rnd)
        assert all(not t.player_clash_qte and not t.phase_order for t in m.turn_results)


def test_force_per_turn_on_touge():
    m = _match(2, per_phase=False)
    assert all(not t.player_clash_qte for t in m.turn_results)
    assert m.player_total_progress != _match(2).player_total_progress


def test_smooth_phase_qte():
    assert E.smooth_phase_qte([0.8, 0.4, 1.0], 0.35) == [0.8, E.round_qte_score(0.35 * 0.4 + 0.65 * 0.8),
                                                        E.round_qte_score(0.35 * 1.0 + 0.65 * 0.6)]
    assert E.smooth_phase_qte([0.8, 0.4, 1.0], 1.0) == [0.8, 0.4, 1.0]
