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
    """Swift-like han_pct=0.55, raw=7 → ~7.76."""
    eff = apply_han_qte_mod(7.0, 0.55)
    assert abs(eff - 7.7583) < 1e-4


def test_apply_han_qte_mod_low():
    """Bruiser-like han_pct=0.25, raw=7 → ~6.71."""
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
