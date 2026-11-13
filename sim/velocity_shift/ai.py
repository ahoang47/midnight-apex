from __future__ import annotations
"""Encounter shape helpers (laps, phases, legacy AI QTE ratio).

The personality / hand-scoring card AI (pick_ai_card, PERSONALITY_MAP) was
removed with the card draw on 2026-11-13. Opponents now always play their
district line (LINE_SET_C) under the boss heat rule (heat.boss_stance).
"""

import random

from .equations import apply_han_qte_mod

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

TYPICAL_QTE = 7.0           # baseline for independent AI QTE generation (legacy HP/DP only)


def get_phase(turn: int, encounter_type: str) -> int:
    """Return 0-indexed phase (lap) for a given turn and encounter type."""
    if encounter_type == "wild":
        return 0
    lap = ENCOUNTER_LAP_SIZES.get(encounter_type, 5)
    return (turn - 1) // lap


def get_total_phases(encounter_type: str) -> int:
    return ENCOUNTER_PHASES.get(encounter_type, 1)


def get_ai_qte(
    ratio: float,
    rng: random.Random,
    deterministic: bool,
    noise: float = 0.3,
    han_pct: float = 1 / 3,
) -> float:
    """LEGACY (HP/DP only): an independent AI QTE score on the 1–10 scale.

    The playable engine uses OPPONENT_QTE instead.
    """
    raw = TYPICAL_QTE * ratio
    if not deterministic:
        raw += rng.uniform(-noise, noise)
    return apply_han_qte_mod(raw, han_pct)
