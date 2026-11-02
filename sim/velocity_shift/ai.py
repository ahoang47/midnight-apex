from __future__ import annotations
"""AI opponent card selection with phase-aware, personality-driven scoring.

Each card is scored independently:
    MoveScore = EVWeight + PhaseWeight + PersonalityWeight + Randomness

AI has full knowledge of both hands. The opponent's deck reshuffles each
turn to guarantee pattern-consistent hands.
"""

import random
from collections import Counter

from .models import Stance, StanceOutcome, Card, PhaseType, PersonalityConfig, PersonalityPhase, ClashResult
from .equations import resolve_stance, apply_han_qte_mod

ENCOUNTER_RATIOS = {
    "wild": 0.75,
    "lieutenant": 1.1,
    "boss": 1.2,
}


ENCOUNTER_PHASES = {
    "wild": 1,
    "lieutenant": 2,
    "boss": 3,
}

ENCOUNTER_LAP_SIZES = {
    "wild": 10,
    "lieutenant": 10,
    "boss": 10,
}

TYPICAL_QTE = 7.0           # baseline for independent AI QTE generation


def get_phase(turn: int, encounter_type: str) -> int:
    """Return 0-indexed phase for a given turn and encounter type."""
    if encounter_type == "wild":
        return 0
    lap = ENCOUNTER_LAP_SIZES.get(encounter_type, 5)
    return (turn - 1) // lap


def get_total_phases(encounter_type: str) -> int:
    return ENCOUNTER_PHASES.get(encounter_type, 1)


def _get_stance(c: object) -> Stance:
    """Unwrap a Card or Stance to a bare Stance enum."""
    if isinstance(c, Card):
        return c.stance
    if isinstance(c, Stance):
        return c
    raise TypeError(f"Expected Card or Stance, got {type(c).__name__}")


def ev_weight(card: Card, opponent_hand: list[Card]) -> float:
    """Expected value against every card in opponent's remaining hand."""
    if not opponent_hand:
        return 0.0
    total = sum(
        resolve_stance(card.stance, _get_stance(oc)).value
        for oc in opponent_hand
    )
    return total / len(opponent_hand)


def calculate_phase_weight(card: Card, phase: PersonalityPhase, clash_index: int) -> float:
    """Return phase-type weight for a card, 0 for breather slot (index 2)."""
    if not phase.weights or clash_index == 2:
        return 0.0
    return phase.weights.get(card.stance, 0.0)


def _apply_override(
    override: str,
    hand: list[Card],
    opponent_hand: list[Card],
    clash_index: int,
    previous_clashes: list[ClashResult],
    turn_number: int,
    player_stance_history: list[Stance],
) -> Card:
    if override == "highest_ev":
        return max(hand, key=lambda c: ev_weight(c, opponent_hand))

    if override == "second_highest_ev":
        sorted_cards = sorted(hand, key=lambda c: ev_weight(c, opponent_hand), reverse=True)
        return sorted_cards[1] if len(sorted_cards) > 1 else sorted_cards[0]

    if override == "third_highest_ev":
        sorted_cards = sorted(hand, key=lambda c: ev_weight(c, opponent_hand), reverse=True)
        return sorted_cards[2] if len(sorted_cards) > 2 else sorted_cards[-1]

    if override == "alternate":
        pattern = [Stance.ATTACK, Stance.DEFEND, Stance.ATTACK]
        if turn_number % 2 == 0:
            pattern = [Stance.DEFEND, Stance.ATTACK, Stance.DEFEND]
        preferred = pattern[clash_index]
        for c in hand:
            if c == preferred:
                return c
        return max(hand, key=lambda c: ev_weight(c, opponent_hand))

    if override == "counter":
        if not player_stance_history:
            return max(hand, key=lambda c: ev_weight(c, opponent_hand))
        counts = Counter(player_stance_history)
        most_common = counts.most_common(1)[0][0]
        counters = {
            Stance.ATTACK: Stance.DEFEND,
            Stance.DEFEND: Stance.NEUTRAL,
            Stance.NEUTRAL: Stance.ATTACK,
        }
        target = counters[most_common]
        for c in hand:
            if c == target:
                return c
        return max(hand, key=lambda c: ev_weight(c, opponent_hand))

    if override == "repeat_win":
        winning = [cr.opponent_card for cr in previous_clashes if cr.outcome == StanceOutcome.WIN]
        if not winning:
            return max(hand, key=lambda c: ev_weight(c, opponent_hand))
        target = winning[-1]
        for c in hand:
            if c == target:
                return c
        return max(hand, key=lambda c: ev_weight(c, opponent_hand))

    return max(hand, key=lambda c: ev_weight(c, opponent_hand))


def pick_ai_card(
    hand: list[Card],
    opponent_hand: list[Card],
    phase_index: int,
    personality: PersonalityConfig,
    clash_index: int,
    previous_clashes: list[ClashResult],
    turn_number: int,
    player_stance_history: list[Stance],
    rng: random.Random,
) -> Card:
    """Select one card from *hand* using the MoveScore formula.

    MoveScore = EVWeight + PhaseWeight + PersonalityWeight + Randomness

    Behavior overrides take precedence over the standard formula.
    Unpredictable phase rolls 70% EV / 30% random.
    """
    phase = personality.phases[phase_index]

    if phase.behavior_override:
        return _apply_override(
            phase.behavior_override, hand, opponent_hand,
            clash_index, previous_clashes, turn_number,
            player_stance_history,
        )

    if phase.phase_type == PhaseType.UNPREDICTABLE:
        if rng.random() < 0.3:
            return rng.choice(hand)
        return max(hand, key=lambda c: ev_weight(c, opponent_hand))

    scores = {}
    for card in hand:
        ev = ev_weight(card, opponent_hand)
        pw = calculate_phase_weight(card, phase, clash_index)
        r = rng.uniform(-0.5, 0.5)
        scores[card] = ev + pw + r

    return max(scores, key=scores.get)


# ── Personality definitions ──────────────────────────────────────────

AGGRESSIVE_DRIVER = PersonalityConfig(
    name="Aggressive",
    phases=[
        PersonalityPhase(
            phase_type=PhaseType.AGGRESSIVE,
            weights={Stance.ATTACK: 3, Stance.DEFEND: 0, Stance.NEUTRAL: 1},
            hand_requirements={Stance.ATTACK: 2},
        ),
        PersonalityPhase(
            phase_type=PhaseType.REACTIVE,
            behavior_override="counter",
            hand_requirements={Stance.ATTACK: 1, Stance.DEFEND: 1, Stance.NEUTRAL: 1},
        ),
        PersonalityPhase(
            phase_type=PhaseType.UNPREDICTABLE,
        ),
    ],
)

DEFENSIVE_DRIVER = PersonalityConfig(
    name="Defensive",
    phases=[
        PersonalityPhase(
            phase_type=PhaseType.REACTIVE,
            behavior_override="counter",
            hand_requirements={Stance.ATTACK: 1, Stance.DEFEND: 1, Stance.NEUTRAL: 1},
        ),
        PersonalityPhase(
            phase_type=PhaseType.AGGRESSIVE,
            weights={Stance.ATTACK: 3, Stance.DEFEND: 0, Stance.NEUTRAL: 1},
            hand_requirements={Stance.ATTACK: 2},
        ),
        PersonalityPhase(
            phase_type=PhaseType.UNPREDICTABLE,
        ),
    ],
)

PRECISE_DRIVER = PersonalityConfig(
    name="Precise",
    phases=[
        PersonalityPhase(
            phase_type=PhaseType.AGGRESSIVE,
            behavior_override="highest_ev",
            hand_requirements={Stance.ATTACK: 1, Stance.DEFEND: 1, Stance.NEUTRAL: 1},
        ),
        PersonalityPhase(
            phase_type=PhaseType.REACTIVE,
            behavior_override="counter",
            hand_requirements={Stance.ATTACK: 1, Stance.DEFEND: 1, Stance.NEUTRAL: 1},
        ),
        PersonalityPhase(
            phase_type=PhaseType.UNPREDICTABLE,
        ),
    ],
)

BALANCED_DRIVER = PersonalityConfig(
    name="Balanced",
    phases=[
        PersonalityPhase(
            phase_type=PhaseType.AGGRESSIVE,
            behavior_override="alternate",
            hand_requirements={Stance.ATTACK: 2, Stance.DEFEND: 1},
        ),
        PersonalityPhase(
            phase_type=PhaseType.REACTIVE,
            behavior_override="counter",
            hand_requirements={Stance.ATTACK: 1, Stance.DEFEND: 1, Stance.NEUTRAL: 1},
        ),
        PersonalityPhase(
            phase_type=PhaseType.REACTIVE,
            behavior_override="repeat_win",
            hand_requirements={Stance.ATTACK: 1, Stance.DEFEND: 1, Stance.NEUTRAL: 1},
        ),
    ],
)

ADAPTIVE_DRIVER = PersonalityConfig(
    name="Adaptive",
    phases=[
        PersonalityPhase(
            phase_type=PhaseType.AGGRESSIVE,
            behavior_override="third_highest_ev",
            hand_requirements={Stance.ATTACK: 1, Stance.DEFEND: 1, Stance.NEUTRAL: 1},
        ),
        PersonalityPhase(
            phase_type=PhaseType.REACTIVE,
            behavior_override="second_highest_ev",
            hand_requirements={Stance.ATTACK: 1, Stance.DEFEND: 1, Stance.NEUTRAL: 1},
        ),
        PersonalityPhase(
            phase_type=PhaseType.UNPREDICTABLE,
        ),
    ],
)

PERSONALITY_MAP = {
    "Aggressive": AGGRESSIVE_DRIVER,
    "Defensive": DEFENSIVE_DRIVER,
    "Precise": PRECISE_DRIVER,
    "Balanced": BALANCED_DRIVER,
    "Adaptive": ADAPTIVE_DRIVER,
}


def get_personality(archetype: str) -> PersonalityConfig:
    """Look up personality config by archetype name."""
    return PERSONALITY_MAP.get(archetype, AGGRESSIVE_DRIVER)


def get_ai_qte(
    ratio: float,
    rng: random.Random,
    deterministic: bool,
    noise: float = 0.3,
    han_pct: float = 1 / 3,
) -> float:
    """Generate an independent AI QTE score.

    Baseline is TYPICAL_QTE × ratio, then modified by HAN proportion.
    No ceiling — the natural qte_factor clamp in combat.py handles bounds.
    In deterministic mode the noise is omitted.
    """
    raw = TYPICAL_QTE * ratio
    if not deterministic:
        raw += rng.uniform(-noise, noise)
    return apply_han_qte_mod(raw, han_pct)
