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
from .combat import plan_player_cards, official_tracks
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
        self._planned_line: list[Stance] | None = None

    def run(self) -> SimulationResult:
        trace = TraceLogger()
        result = run_match(
            self.cfg,
            self._make_player_card_fn(),
            self._make_player_qte_fn(),
            self._make_opponent_card_fn(),
            self._make_opponent_qte_fn(),
            trace,
            on_line_picked=self._on_line_picked,
            on_deal=self._on_deal,
        )
        return SimulationResult(
            match=result,
            seed=self.cfg.seed,
            config_snapshot=self._snapshot(),
        )

    def _on_line_picked(self, turn: int, corner: str, line: list[Stance]) -> None:
        self._planned_line = line
        self._corner = corner
        self._assigned: list[Card] | None = None

    def _on_deal(self, turn: int, p_hand: list[Card], o_hand: list[Card]) -> None:
        """After the hand is dealt, lock in the v4 read + assign_hand plan."""
        if self.cfg.legacy_hp_dp:
            return
        pq = self._play_quality()
        if pq is None or not (self.cfg.district and self.cfg.corners):
            return
        self._assigned = plan_player_cards(
            self.cfg.district, self._corner, self._planned_line, p_hand, pq[0], self._rng,
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
        legacy = self.cfg.legacy_hp_dp
        use_lines = bool(self.cfg.district and self.cfg.corners)

        if use_lines and pq is not None and not legacy:
            def fn_v4(t, ci, hand, opp_hand, clashes):
                return self._assigned[ci]
            return fn_v4

        if pq is None:
            return lambda t, ci, hand, opp_hand, clashes: rng.choice(hand)
        q = pq[0]

        # Fallback (no district, or legacy_hp_dp): per-clash counter of the AI pick.
        self._cached_ai_card = None
        history: list[Stance] = []
        personality = self._personality
        enc = self.cfg.encounter_type

        def fn(t, ci, hand, opp_hand, clashes):
            if use_lines:
                target_stance = self._planned_line[ci]
                if rng.random() < q:
                    target = _COUNTER[target_stance]
                    pick = next((c for c in hand if c == target), None)
                    if pick is None:
                        pick = next((c for c in hand if c == target_stance), None)
                    if pick is None:
                        pick = hand[0]
                else:
                    pick = rng.choice(hand)
                history.append(pick.stance)
                return pick
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
        if self.cfg.legacy_hp_dp:
            if pq is None:
                return lambda t: self._rng.uniform(PLAYER_QTE_MIN, PLAYER_QTE_MAX)
            q = pq[1]
            def fn_legacy(t):
                if self._rng.random() < q:
                    return PERFECT_QTE
                return self._rng.uniform(PLAYER_QTE_MIN, PLAYER_QTE_MAX)
            return fn_legacy
        # Playable engine: q_time is a skill in [0, 1], not a Bernoulli QTE roll.
        if pq is None:
            return lambda t: self._rng.uniform(0.1, 1.0)
        q_time = pq[1]
        return lambda t: q_time

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
            "district": self.cfg.district,
            "corners": list(self.cfg.corners) if self.cfg.corners else None,
            "legacy_hp_dp": self.cfg.legacy_hp_dp,
        }


def simulate_win_rate(
    district: str,
    r: float,
    q: float,
    length: int,
    seed: int,
    n_per_track: int = 200,
    opp_total: float = 300.0,
) -> float:
    """Win rate (%) of a SimulationRunner batch on a district's official tracks.

    Balanced builds, player total = r * opp_total, q_read = q_time = q,
    opponent QTE from the engine constant. Ties count as a half-win, same
    as the winrate_n4000.json oracle. Seeds are spaced so tracks and races
    do not share nearby Python Random() seeds (consecutive integers are
    correlated and biased a small batch).
    """
    from .models import CombatantStats

    tracks = official_tracks()[district.lower()]
    names = list(tracks)
    p_stat = opp_total * r / 3.0
    o_stat = opp_total / 3.0
    player = CombatantStats(name="Player", pow=p_stat, en=p_stat, han=p_stat, level=50)
    opponent = CombatantStats(name="Opponent", pow=o_stat, en=o_stat, han=o_stat, level=50)
    wins = ties = n = 0
    for ti, name in enumerate(names):
        corners = list(tracks[name])
        for k in range(n_per_track):
            cfg = MatchConfig(
                player_stats=player,
                opponent_stats=opponent,
                max_turns=length,
                seed=seed + length * 1_000_000 + ti * 10_000 + k,
                district=district,
                corners=corners,
                player_read=q,
                player_timing=q,
                encounter_type="boss",
            )
            m = SimulationRunner(cfg).run().match
            if m.winner == "Player" or m.player_total_progress > m.opponent_total_progress:
                wins += 1
            elif m.winner == "Tie" or m.player_total_progress == m.opponent_total_progress:
                ties += 1
            n += 1
    return 100.0 * (wins + 0.5 * ties) / n


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
