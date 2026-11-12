"""Unit tests for all pure equation functions in velocity_shift.equations."""
from velocity_shift.equations import qte_factor, clash_mult, compute_damage, resolve_stance, \
    damage_mitigation, apply_han_qte_mod
from velocity_shift.models import Stance, StanceOutcome


def test_qte_factor():
    """QTE normalisation: 10→1.0, 5→0.5, 1→0.1, 0→0.0."""
    assert qte_factor(10) == 1.0
    assert qte_factor(5) == 0.5
    assert qte_factor(1) == 0.1
    assert qte_factor(0) == 0.0


def test_clash_mult():
    """Clash multiplier: WIN=1.35, NEUTRAL=1, LOSS=0.65 (stakes baked at 0.35)."""
    assert clash_mult(StanceOutcome.WIN) == 1.35
    assert clash_mult(StanceOutcome.LOSS) == 0.65
    assert clash_mult(StanceOutcome.NEUTRAL) == 1.0


def test_compute_damage():
    """Damage formula: POW × QTE × clash × battle, floored at 0."""
    dmg = compute_damage(100, 1.0, 1.35, 1.0)
    assert abs(dmg - 135.0) < 1e-6

    dmg = compute_damage(100, 0.5, 0.65, 1.05)
    assert abs(dmg - 34.125) < 1e-6

    dmg = compute_damage(100, 1.0, -0.5, 1.0)
    assert dmg == 0.0

    dmg = compute_damage(0, 1.0, 1.0, 1.0)
    assert dmg == 0.0

    dmg = compute_damage(100, 1.0, 1.0, 0.0)
    assert dmg == 0.0


def test_resolve_stance():
    """RPS rules: ATK>NEU>DEF>ATK; same stance → NEUTRAL."""
    assert resolve_stance(Stance.ATTACK, Stance.ATTACK) == StanceOutcome.NEUTRAL
    assert resolve_stance(Stance.ATTACK, Stance.NEUTRAL) == StanceOutcome.WIN
    assert resolve_stance(Stance.ATTACK, Stance.DEFEND) == StanceOutcome.LOSS
    assert resolve_stance(Stance.NEUTRAL, Stance.NEUTRAL) == StanceOutcome.NEUTRAL
    assert resolve_stance(Stance.NEUTRAL, Stance.DEFEND) == StanceOutcome.WIN
    assert resolve_stance(Stance.NEUTRAL, Stance.ATTACK) == StanceOutcome.LOSS
    assert resolve_stance(Stance.DEFEND, Stance.DEFEND) == StanceOutcome.NEUTRAL
    assert resolve_stance(Stance.DEFEND, Stance.ATTACK) == StanceOutcome.WIN
    assert resolve_stance(Stance.DEFEND, Stance.NEUTRAL) == StanceOutcome.LOSS


def test_apply_han_qte_mod_neutral():
    """Balanced han_pct=1/3 → no change."""
    assert apply_han_qte_mod(7.0, 1/3) == 7.0


def test_apply_han_qte_mod_high():
    """Precise-like han_pct=0.55, raw=7 → ~7.76."""
    eff = apply_han_qte_mod(7.0, 0.55)
    assert abs(eff - 7.7583) < 1e-4


def test_apply_han_qte_mod_low():
    """Aggressive-like han_pct=0.25, raw=7 → ~6.71."""
    eff = apply_han_qte_mod(7.0, 0.25)
    assert abs(eff - 6.7083) < 1e-4


def test_apply_han_qte_mod_zero_han():
    """han_pct=0 → ~5.83 (maximum penalty)."""
    eff = apply_han_qte_mod(7.0, 0.0)
    assert abs(eff - 5.8333) < 1e-4


def test_damage_mitigation():
    """Mitigation: reduction = (EN/1000) × 0.4 × QTE, floored at 0.1."""
    assert damage_mitigation(0, 1.0) == 1.0
    assert damage_mitigation(1000, 0.0) == 1.0
    assert abs(damage_mitigation(1000, 1.0) - 0.6) < 1e-6
    assert abs(damage_mitigation(500, 0.5) - 0.9) < 1e-6
    assert damage_mitigation(10000, 1.0) == 0.1


from velocity_shift.equations import (
    timing_value, clash_payoff, clash_progress, kappa_for_length, knot_window,
    expected_hit_quality, qte_zone_width, raw_qte_score, QTE_SKILL_SIGMA_OVER_A0,
    mean_phase_qte, phase_raw_qte, PHASE_QTE_UNPLAYED,
    QTE_ZONE_WIDTH_105, AVERAGE_PLAY_Q,
    W0, T_MAX, L_MAX, KAPPA_BY_LENGTH,
)
from velocity_shift.models import StanceOutcome


def test_timing_value_endpoints():
    assert timing_value(0.0) == 0.0
    assert abs(timing_value(1.0) - 1.0) < 1e-12
    assert 0.0 < timing_value(0.5) < 1.0


def test_clash_payoff_at_perfect_timing():
    assert abs(clash_payoff(StanceOutcome.WIN, 1.0) - 1.0) < 1e-12
    assert abs(clash_payoff(StanceOutcome.NEUTRAL, 1.0) - T_MAX) < 1e-12
    assert abs(clash_payoff(StanceOutcome.LOSS, 1.0) - L_MAX) < 1e-12
    assert abs(clash_payoff(StanceOutcome.WIN, 0.0) - W0) < 1e-12
    assert clash_payoff(StanceOutcome.NEUTRAL, 0.0) == 0.0
    assert clash_payoff(StanceOutcome.LOSS, 0.0) == 0.0


def test_clash_progress_balanced_at_parity():
    """Balanced stats, r=1, q=1, window off (or r=1.05 with window on): V=1, M=1, g=Phi."""
    kap = kappa_for_length(20)
    for outcome, expected in (
        (StanceOutcome.WIN, 1.0),
        (StanceOutcome.NEUTRAL, T_MAX),
        (StanceOutcome.LOSS, L_MAX),
    ):
        g = clash_progress(outcome, 1.0, 100, 100, 100, 300, kap)
        assert abs(g - expected) < 1e-12, (outcome, g, expected)
        # r=1.05; 105+105+105 vs 300. No knot_window factor on q_time.
        g2 = clash_progress(outcome, 1.0, 105, 105, 105, 300, kap)
        V = (315 / 300) ** kap
        assert abs(g2 - V * expected) < 1e-12, (outcome, g2, V * expected)


def test_kappa_for_length_official_and_nearest():
    assert kappa_for_length(10) == KAPPA_BY_LENGTH[10]
    assert kappa_for_length(20) == KAPPA_BY_LENGTH[20]
    assert kappa_for_length(30) == KAPPA_BY_LENGTH[30]
    assert kappa_for_length(11) == KAPPA_BY_LENGTH[10]
    # Legacy hidden window (oracle / zone-table generator only).
    assert knot_window(1.05) == 1.0
    assert knot_window(0.80) == 0.41


def test_expected_hit_quality_at_default_zone_matches_qte_v1():
    """PLACEHOLDER σ: weak/average/strong E[s] at w0 is 0.4 / 0.6 / 0.8."""
    for name, target in (("weak", 0.4), ("average", 0.6), ("strong", 0.8)):
        e = expected_hit_quality(QTE_SKILL_SIGMA_OVER_A0[name], 1.0)
        assert abs(e - target) < 1e-12, (name, e, target)


def test_qte_zone_width_at_knots_and_window_mod():
    for r, w in QTE_ZONE_WIDTH_105:
        got = qte_zone_width(r)
        assert abs(got - w) < 1e-12, (r, got, w)
    # Average player's E[s] at the unmodded zone equals 0.6 * legacy W(r).
    for r in (0.80, 0.95, 1.00, 1.0355, 1.05, 1.10):
        e = raw_qte_score(r, profile="average")
        assert abs(e - AVERAGE_PLAY_Q * knot_window(r)) < 1e-12, (r, e)
    # +20% window mod widens the zone; does not change mid-race (r is fixed).
    assert abs(qte_zone_width(1.05, window_mod=0.20) - 1.20) < 1e-12
    assert qte_zone_width(1.05, 0.20) > qte_zone_width(1.05, 0.0)


def test_mean_phase_qte_averages_three_scores():
    assert mean_phase_qte((1.0, 0.4, 0.8)) == (1.0 + 0.4 + 0.8) / 3.0
    assert mean_phase_qte([0.0, 0.6, 1.2]) == (0.0 + 0.6 + 1.2) / 3.0
    # A scalar is the turn raw_qte as-is (default / profile path unchanged).
    assert mean_phase_qte(0.6) == 0.6


def test_mean_phase_qte_unplayed_counts_as_zero():
    assert phase_raw_qte(None) == PHASE_QTE_UNPLAYED == 0.0
    assert mean_phase_qte((1.0, None, 0.5)) == (1.0 + 0.0 + 0.5) / 3.0
    assert mean_phase_qte((None, None, None)) == 0.0
    assert mean_phase_qte(None) == 0.0


def test_parity_knot_067_and_zone_width_slots_v2():
    """Austin approved 2026-11-11 (slots-v2): r=1.00 knot 0.68 -> 0.67; zone generated from it."""
    from velocity_shift.equations import KNOT_WINDOW_105, qte_zone_width
    assert dict(KNOT_WINDOW_105)[1.00] == 0.67
    assert abs(qte_zone_width(1.00) - 0.5698111340658429) < 1e-12
    assert round(qte_zone_width(1.02), 4) == 0.7170
    assert qte_zone_width(1.05) == 1.0 and round(qte_zone_width(0.95), 4) == 0.3448


def test_aero_free_pool_cap_inside_mod_cap():
    from velocity_shift.equations import (AERO_FREE_POOL_MAX_FRACTION, AERO_MAX_EQUIPPED, AERO_COUNTS_IN_MOD_CAP,
                                          aero_free_pool_max)
    assert AERO_FREE_POOL_MAX_FRACTION == 0.10 and AERO_MAX_EQUIPPED == 1 and AERO_COUNTS_IN_MOD_CAP
    assert abs(aero_free_pool_max(40.0) - 4.0) < 1e-12
    assert aero_free_pool_max(-1.0) == 0.0
