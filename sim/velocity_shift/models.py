from __future__ import annotations
"""Data classes and enumerations for the combat engine.

No logic — only type definitions. All stat ranges are 0+ with no upper bound.
Card equality is stance-based (two cards with the same stance are equal).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Stance(Enum):
    """The three rock-paper-scissors stances a card can hold."""
    ATTACK = "attack"
    DEFEND = "defend"
    NEUTRAL = "neutral"


@dataclass(eq=False)
class Card:
    """A single card in a combatant's deck."""
    stance: Stance

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Stance):
            return self.stance == other
        if isinstance(other, Card):
            return self.stance == other.stance
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.stance)


class StanceOutcome(Enum):
    """Result of a single clash resolved by resolve_stance()."""
    WIN = 1
    NEUTRAL = 0
    LOSS = -1


@dataclass
class CombatantStats:
    """A combatant's core stats and level.

    Stats (POW/EN/HAN) have no upper bound. HP is derived from
    level alone: max_hp = level × HP_PER_LEVEL (from equations).
    """
    name: str
    pow: float
    en: float
    han: float
    level: int = 1


@dataclass
class TurnState:
    """Snapshot of all inputs for a single turn's resolution."""
    turn_number: int
    player_cards: list = field(default_factory=list)
    opponent_cards: list = field(default_factory=list)
    player_qte: float = 0.0
    opponent_qte: float = 0.0


@dataclass
class TurnResult:
    """Output produced by resolving a single turn."""
    turn_number: int
    player_cards: list = field(default_factory=list)
    opponent_cards: list = field(default_factory=list)
    player_dp: float = 0.0
    opponent_dp: float = 0.0
    player_progress: float = 0.0
    opponent_progress: float = 0.0
    player_clash_progress: list[float] = field(default_factory=list)
    opponent_clash_progress: list[float] = field(default_factory=list)
    battle_outcomes: list[StanceOutcome] = field(default_factory=list)
    battle_winner: Optional[str] = None
    battle_mult: float = 1.0
    player_qte: float = 0.0
    opponent_qte: float = 0.0
    player_hand: list = field(default_factory=list)
    opponent_hand: list = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)
    # Set when the match is using district line tables (LINE_SET_C).
    corner_type: Optional[str] = None
    opponent_line: list = field(default_factory=list)


@dataclass
class MatchResult:
    """Accumulated state and final outcome of a complete match."""
    player_name: str
    opponent_name: str
    total_turns: int
    turns_played: int = 0
    player_total_dp: float = 0.0
    opponent_total_dp: float = 0.0
    player_total_progress: float = 0.0
    opponent_total_progress: float = 0.0
    player_max_hp: float = 0.0
    opponent_max_hp: float = 0.0
    turn_results: list[TurnResult] = field(default_factory=list)
    winner: Optional[str] = None
    player_position: float = 0.0
    opponent_position: float = 0.0


@dataclass
class MatchConfig:
    """Complete configuration to run a match.

    Encounter difficulty is determined by the level gap between
    combatants — no additional tuning parameters.
    """
    player_stats: CombatantStats
    opponent_stats: CombatantStats
    # Official races are 10-corner laps × 1/2/3 = 10/20/30 turns. kappa
    # is selected from this planned length via kappa_for_length, not from
    # len(corners) (the lap). Default is one lap (kappa for 10). A leftover
    # default of 99 would silently snap to the 30-turn kappa.
    max_turns: int = 10
    seed: Optional[int] = None
    deterministic: bool = True
    verbose: bool = False
    rival_personality: str = ""
    encounter_type: str = "wild"
    # Opt-in (None keeps old behaviour): simulated-player play quality q in
    # [0, 1], see equations.PERFECT_QTE and simulation.SimulationRunner.
    player_quality: Optional[float] = None
    # Opt-in split of play quality into two independent skills, each in
    # [0, 1]. player_read: chance per clash of reading the AI's real pick
    # and countering it. player_timing: expected hit quality at the default
    # QTE zone (back-compat override). In the playable engine it is evaluated
    # at the race's fixed r via raw_qte_score (the visible zone), not used
    # as a hidden multiplier. Each one, if set, overrides player_quality for
    # its own axis; an axis left unset falls back to player_quality (so
    # player_quality=q is shorthand for read=timing=q), and to 0 (random)
    # if that is unset too. All three None (the default) keeps the old
    # random player exactly, unless player_qte_profile is set.
    player_read: Optional[float] = None
    player_timing: Optional[float] = None
    # Named PLACEHOLDER skill profile ("weak" / "average" / "strong").
    # When set, the playable engine uses that profile's σ at qte_zone_width
    # (r, qte_window_mod) and ignores player_timing for the raw QTE score.
    player_qte_profile: Optional[str] = None
    # Multiplicative window-only mod on the visible zone (0.10 = +10% of
    # qte_zone_width(r)). Slot competition and the 105%-all-slots rule
    # belong to the upcoming slot sim and are not applied here.
    qte_window_mod: float = 0.0
    # Opt-in (None = ENCOUNTER_RATIOS[encounter_type]): override the ratio
    # that scales the AI's QTE, e.g. 1.0 for a pure stat-parity test.
    opponent_qte_ratio: Optional[float] = None
    # Opt-in district line tables (LINE_SET_C). When both are set, match.py
    # picks the opponent's whole line once per corner/turn from the match
    # RNG and plays those three stances; personality/archetype hand
    # requirements are not used. `corners` is a lap of corner codes (typically
    # 10) and repeats for longer races. District may be title case or lowercase.
    district: Optional[str] = None
    corners: Optional[list[str]] = None
    # Default (False) is the final-v1 Phi/tau playable engine. True restores
    # the older HP/DP + rubber-band path (resolve_turn_legacy, persistent decks).
    legacy_hp_dp: bool = False


class PhaseType(Enum):
    AGGRESSIVE = "aggressive"
    REACTIVE = "reactive"
    UNPREDICTABLE = "unpredictable"


@dataclass
class PersonalityPhase:
    phase_type: PhaseType
    weights: dict | None = None
    behavior_override: str | None = None
    hand_requirements: dict | None = None


@dataclass
class PersonalityConfig:
    name: str
    phases: list[PersonalityPhase]


@dataclass
class ClashResult:
    clash_index: int
    player_card: Stance
    opponent_card: Stance
    outcome: StanceOutcome
