from __future__ import annotations
"""Pure mathematical functions for combat calculations.

All functions are stateless — no side effects, no mutable state.
Every formula is deterministic given its inputs.

All game-rule constants live here as module-level names, NOT
per-encounter configurable parameters. To tune the game, change
these values and re-run.
"""

from .models import Stance, StanceOutcome

# ── Game-rule constants (global knobs, not per-encounter) ──────────────

CLASH_STAKES = 0.35           # clash_mult = 1 ± CLASH_STAKES
BATTLE_BONUS = 0.05           # battle_mult bonus per win-margin point
MITIGATION_PER_1000 = 0.4     # EN reduction factor per 1000 EN
MITIGATION_FLOOR = 0.1        # minimum damage fraction (10 % always gets through)
HP_PER_LEVEL = 180            # max_hp = level × HP_PER_LEVEL
QTE_NORMALIZER = 10.0         # qte_factor = score / QTE_NORMALIZER
HAN_QTE_WEIGHT = 0.5         # shared modifier for both sides
RUBBER_BAND_FRACTION = 0.15  # full rubber-band at a DP gap of this × average max HP

# ── Simulated-player play quality (opt-in, MatchConfig.player_quality) ──
# q in [0, 1] = the fraction of the race the player "plays right".
#   * Card read: each clash, with probability q the player reads the
#     opponent's real pick and plays its counter (else a tie card, else
#     any card); otherwise the player picks a random card.
#   * QTE: each turn, with probability q the player hits PERFECT_QTE;
#     otherwise the score is uniform in [PLAYER_QTE_MIN, PLAYER_QTE_MAX].
# q = 0 reproduces the old random player exactly (random card, uniform QTE).
# The two parts are independent skills: MatchConfig.player_read (q_read,
# card read) and MatchConfig.player_timing (q_time, QTE). player_quality=q
# is shorthand for q_read = q_time = q.
PLAYER_QTE_MIN = 1.0
PLAYER_QTE_MAX = 10.0
PERFECT_QTE = 10.0


def qte_factor(qte_score: float) -> float:
    """Normalise a QTE score (1–10) to a 0.1–1.0 multiplier."""
    return qte_score / QTE_NORMALIZER


def apply_han_qte_mod(qte_score: float, han_pct: float) -> float:
    """Modify a QTE score by HAN proportion. Same formula for both sides.
    han_pct = han / (pow + en + han).
    Neutral at han_pct == 1/3, scales linearly with HAN_QTE_WEIGHT.
    """
    return qte_score * (1.0 + HAN_QTE_WEIGHT * (han_pct - 1 / 3))


def clash_mult(outcome: StanceOutcome) -> float:
    """Return the damage multiplier for a single clash result.

    * WIN    → 1 + CLASH_STAKES
    * NEUTRAL → 1.0
    * LOSS   → 1 - CLASH_STAKES
    """
    return 1.0 + CLASH_STAKES * outcome.value


def compute_damage(
    pow_stat: float,
    qte_factor: float,
    clash_mult: float,
    battle_mult: float,
) -> float:
    """Compute raw damage for one clash.

    Formula: max(0, POW × QTE_factor × clash_mult × battle_mult)
    """
    return max(0.0, pow_stat * qte_factor * clash_mult * battle_mult)


def damage_mitigation(en_stat: float, qte_factor: float) -> float:
    """Return the mitigation multiplier that reduces incoming damage.

    At least MITIGATION_FLOOR × 100 % of damage always gets through.
    Reduction = (EN / 1000) × MITIGATION_PER_1000 × QTE_factor
    """
    reduction = (en_stat / 1000.0) * MITIGATION_PER_1000 * qte_factor
    return max(MITIGATION_FLOOR, 1.0 - reduction)


def resolve_stance(a: Stance, b: Stance) -> StanceOutcome:
    """Resolve a single rock-paper-scissors clash between two stances.

    Rules:
        ATTACK > NEUTRAL > DEFEND > ATTACK
        Same stance → NEUTRAL
    """
    if a == b:
        return StanceOutcome.NEUTRAL
    if (a == Stance.ATTACK and b == Stance.NEUTRAL) or \
       (a == Stance.NEUTRAL and b == Stance.DEFEND) or \
       (a == Stance.DEFEND and b == Stance.ATTACK):
        return StanceOutcome.WIN
    return StanceOutcome.LOSS
