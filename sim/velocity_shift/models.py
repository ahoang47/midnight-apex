from __future__ import annotations
"""Data classes and enumerations for the combat engine.

No logic — only type definitions. All stat ranges are 0+ with no upper bound.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Stance(Enum):
    """The three rock-paper-scissors stances, named by stat.

    Backend code, data and line tables refer to stances only by stat (Austin,
    2026-11-12). Each stance loads its own heat gauge: POW = engine heat,
    HAN = suspension load, EN = brake/tire heat (heat.py). Gauge arrays use
    equations.HEAT_ORDER (POW, HAN, EN), not this member order.
    Old -> new map: design/02-equations-reference.md §6.0.
    """
    POW = "POW"
    EN = "EN"
    HAN = "HAN"


class StanceOutcome(Enum):
    """Result of a single clash resolved by resolve_stance() (DRAW = same stance)."""
    WIN = 1
    DRAW = 0
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
    player_stances: list = field(default_factory=list)
    opponent_stances: list = field(default_factory=list)
    player_qte: float = 0.0
    opponent_qte: float = 0.0
    # Per-clash heat payoff multipliers (overrun_mult or LIMP_MULT); empty = all 1.0.
    player_heat_mults: list = field(default_factory=list)
    opponent_heat_mults: list = field(default_factory=list)
    # Optional Entry/Apex/Exit raw scores. When set (length 3), the turn's
    # player_qte is their mean; None / unplayed counts as 0 (Austin).
    # Clash math still uses the single averaged player_qte.
    player_qte_phases: list = field(default_factory=list)


@dataclass
class TurnResult:
    """Output produced by resolving a single turn."""
    turn_number: int
    player_stances: list = field(default_factory=list)
    opponent_stances: list = field(default_factory=list)
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
    player_qte_phases: list[float] = field(default_factory=list)  # inputs that were averaged into player_qte
    # Heat: per-clash payoff multipliers, and each side's gauges after the turn
    # (load / capacity in HEAT_ORDER POW, HAN, EN; locked flags; limp clash flags).
    player_heat_mults: list[float] = field(default_factory=list)
    opponent_heat_mults: list[float] = field(default_factory=list)
    player_heat_fill: list[float] = field(default_factory=list)
    opponent_heat_fill: list[float] = field(default_factory=list)
    player_locked: list[bool] = field(default_factory=list)
    opponent_locked: list[bool] = field(default_factory=list)
    player_limp: list[bool] = field(default_factory=list)
    opponent_limp: list[bool] = field(default_factory=list)
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
    rival_personality: str = ""   # label only (the personality card AI was removed 2026-11-13)
    encounter_type: str = "wild"
    # Opt-in (None keeps old behaviour): simulated-player play quality q in
    # [0, 1], see equations.PERFECT_QTE and simulation.SimulationRunner.
    player_quality: Optional[float] = None
    # Opt-in split of play quality into independent skills, each in
    # [0, 1]. player_read: chance per corner of reading the boss's line
    # (else each clash ties with prob q_read, else loses). player_timing: expected hit quality at the default
    # QTE zone (back-compat override). In the playable engine it is evaluated
    # at the race's fixed r via raw_qte_score (the visible zone), not used
    # as a hidden multiplier. Each one, if set, overrides player_quality for
    # its own axis; an axis left unset falls back to player_quality (so
    # player_quality=q is shorthand for read=timing=q), and to 0 (random)
    # if that is unset too. All three None (the default) keeps the old
    # random player exactly, unless player_qte_profile is set.
    player_read: Optional[float] = None
    player_timing: Optional[float] = None
    # Simulated player's heat pacing: share of turns it paces with the reserve
    # rule (equations.PACE_*); other turns it plays greedy. None = same as the
    # read skill (average player 0.6, perfect 1.0; resources-v4b).
    player_pacing: Optional[float] = None
    # Boss line style (sim only, PLACEHOLDER): "balanced" (live 65/21/14),
    # "hot_early" or "conserver" (equations.BOSS_STYLES).
    boss_style: str = "balanced"
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
    # District line tables (LINE_SET_C) and the lap. Required by the playable
    # engine: match.py picks the opponent's whole line once per corner/turn
    # from the match RNG, and the corners set the heat costs. `corners` is a
    # lap of corner codes (typically 10) and repeats for longer races.
    # District may be title case or lowercase. If either is missing, match.py
    # uses DEFAULT_DISTRICT's first official track.
    district: Optional[str] = None
    corners: Optional[list[str]] = None


@dataclass
class ClashResult:
    clash_index: int
    player_stance: Stance
    opponent_stance: Stance
    outcome: StanceOutcome


@dataclass
class ClashContext:
    """What the player knows when picking a stance for one clash (heat system).

    `gauges` is the player's live heat.HeatGauges (read it, do not mutate it):
    gauges.selectable_stances(), gauges.fill(), gauges.mult_if(stance, corner).
    The boss's line is not included (the player must read it).
    """
    turn: int
    clash_index: int
    race_length: int
    district: str
    corner: str
    lap: list
    r: float
    gauges: object
    previous_clashes: list = field(default_factory=list)
