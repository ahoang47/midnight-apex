from __future__ import annotations
"""Headless batch runner for statistical analysis and balance testing.

Runs multiple matches with variant configs and exports results as JSON.
Both sides use AI card selection.
"""

import json
import random
from dataclasses import dataclass, asdict
from typing import Callable

from .models import Stance, Card, ClashResult, PersonalityConfig, MatchConfig, MatchResult
from .match import run_match
from .trace import TraceLogger
from .ai import pick_ai_card, get_personality, get_ai_qte, get_phase, \
    ENCOUNTER_RATIOS
from .equations import PLAYER_QTE_MIN, PLAYER_QTE_MAX, PERFECT_QTE

# The stance that beats each stance (equations.resolve_stance rules).
_COUNTER = {
    Stance.ATTACK: Stance.DEFEND,
    Stance.DEFEND: Stance.NEUTRAL,
    Stance.NEUTRAL: Stance.ATTACK,
}


@dataclass
class SimulationResult:
    """A single simulation run's outcome and input snapshot."""
    match: MatchResult
    seed: int | None
    config_snapshot: dict


class SimulationRunner:
    """Executes a single match with AI-driven card selection for both sides."""

    def __init__(self, cfg: MatchConfig):
        self.cfg = cfg
        self._rng = random.Random(cfg.seed)
        self._personality = get_personality(cfg.rival_personality)

    def run(self) -> SimulationResult:
        trace = TraceLogger()
        result = run_match(
            self.cfg,
            self._make_player_card_fn(),
            self._make_player_qte_fn(),
            self._make_opponent_card_fn(),
            self._make_opponent_qte_fn(),
            trace,
        )
        return SimulationResult(
            match=result,
            seed=self.cfg.seed,
            config_snapshot=self._snapshot(),
        )

    def _play_quality(self) -> tuple[float, float] | None:
        """(q_read, q_time) for the simulated player, or None for the old
        random player. See MatchConfig.player_read / player_timing."""
        c = self.cfg
        if c.player_quality is None and c.player_read is None and c.player_timing is None:
            return None
        base = c.player_quality if c.player_quality is not None else 0.0
        read = c.player_read if c.player_read is not None else base
        timing = c.player_timing if c.player_timing is not None else base
        return read, timing

    def _make_player_card_fn(self) -> Callable:
        rng = self._rng
        pq = self._play_quality()
        if pq is None:
            return lambda t, ci, hand, opp_hand, clashes: rng.choice(hand)
        q = pq[0]

        # Play-quality player. The AI's pick does not depend on which card
        # the player chooses (it sees the player's whole remaining hand), so
        # we make the AI's pick here first, cache it, and hand the same card
        # to the opponent callback. With probability q (= q_read) the player
        # "reads" it and counters; otherwise it picks at random.
        self._cached_ai_card = None
        history: list[Stance] = []
        personality = self._personality
        enc = self.cfg.encounter_type

        def fn(t, ci, hand, opp_hand, clashes):
            ai_card = pick_ai_card(opp_hand, hand, get_phase(t, enc), personality,
                                   ci, clashes, t, list(history), rng)
            self._cached_ai_card = ai_card
            if rng.random() < q:
                target = _COUNTER[ai_card.stance]
                pick = next((c for c in hand if c == target), None)
                if pick is None:
                    pick = next((c for c in hand if c == ai_card.stance), None)
                if pick is None:
                    pick = hand[0]
            else:
                pick = rng.choice(hand)
            history.append(pick.stance)
            return pick
        return fn

    def _make_player_qte_fn(self) -> Callable[[int], float]:
        pq = self._play_quality()
        if pq is None:
            return lambda t: self._rng.uniform(1.0, 10.0)
        q = pq[1]
        def fn(t):
            if self._rng.random() < q:
                return PERFECT_QTE
            return self._rng.uniform(PLAYER_QTE_MIN, PLAYER_QTE_MAX)
        return fn

    def _make_opponent_card_fn(self) -> Callable:
        personality = self._personality
        rng = self._rng
        def fn(t: int, ci: int, hand: list[Card], player_hand: list[Card],
               phase_index: int, personality_: PersonalityConfig | None,
               clashes: list[ClashResult], stance_history: list[Stance]) -> Card:
            cached = getattr(self, "_cached_ai_card", None)
            if cached is not None:
                self._cached_ai_card = None
                # Return the exact object from the AI's hand (Card equality
                # is stance-based, so remove() works either way).
                return cached
            return pick_ai_card(hand, player_hand, phase_index, personality,
                                ci, clashes, t, stance_history, rng)
        return fn

    def _make_opponent_qte_fn(self) -> Callable[[int], float]:
        ratio = self.cfg.opponent_qte_ratio
        if ratio is None:
            ratio = ENCOUNTER_RATIOS.get(self.cfg.encounter_type, 1.0)
        return lambda t: get_ai_qte(ratio, self._rng, self.cfg.deterministic)

    def _snapshot(self) -> dict:
        return {
            "player": asdict(self.cfg.player_stats),
            "opponent": asdict(self.cfg.opponent_stats),
            "max_turns": self.cfg.max_turns,
            "seed": self.cfg.seed,
            "deterministic": self.cfg.deterministic,
            "personality": self.cfg.rival_personality,
            "player_quality": self.cfg.player_quality,
            "player_read": self.cfg.player_read,
            "player_timing": self.cfg.player_timing,
            "opponent_qte_ratio": self.cfg.opponent_qte_ratio,
        }


def simulate_batch(
    base_cfg: MatchConfig,
    variants: list[dict] | None = None,
) -> list[SimulationResult]:
    results = []
    cfgs = [base_cfg]
    if variants:
        for v in variants:
            import copy
            cfg = copy.deepcopy(base_cfg)
            for key, val in v.items():
                setattr(cfg, key, val)
            cfgs.append(cfg)
    for cfg in cfgs:
        results.append(SimulationRunner(cfg).run())
    return results


def export_results(results: list[SimulationResult], path: str) -> None:
    data = []
    for r in results:
        entry = {
            "seed": r.seed,
            "config": r.config_snapshot,
            "winner": r.match.winner,
            "player_position": round(r.match.player_position, 4),
            "opponent_position": round(r.match.opponent_position, 4),
            "turns_played": r.match.turns_played,
            "player_total_dp": round(r.match.player_total_dp, 4),
            "opponent_total_dp": round(r.match.opponent_total_dp, 4),
            "turns": [
                {
                    "turn": t.turn_number,
                    "player_dp": round(t.player_dp, 4),
                    "opponent_dp": round(t.opponent_dp, 4),
                    "battle_winner": t.battle_winner,
                    "battle_mult": round(t.battle_mult, 4),
                }
                for t in r.match.turn_results
            ],
        }
        data.append(entry)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
