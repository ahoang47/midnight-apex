from __future__ import annotations
"""Multi-turn match loop — draw, play, resolve, repeat.

Each turn consists of 3 sequential clashes.  After each card is played
the player sees the result before picking the next card.  Phases (laps)
dictate opponent behaviour patterns and are announced at boundaries.

Difficulty is driven entirely by the level gap between combatants.
"""

import copy
from random import Random
from typing import Callable, Optional

from .models import Stance, StanceOutcome, Card, CombatantStats, MatchConfig, MatchResult, \
    TurnResult, TurnState, ClashResult, PersonalityConfig
from .combat import resolve_turn
from .equations import resolve_stance, HP_PER_LEVEL, apply_han_qte_mod, RUBBER_BAND_FRACTION
from .deck import Deck
from .trace import TraceLogger
from .ai import get_personality, get_phase, get_total_phases


def run_match(
    cfg: MatchConfig,
    get_player_card: Callable[[int, int, list[Card], list[Card], list[ClashResult]], Card],
    get_player_qte: Callable[[int], float],
    get_opponent_card: Callable[
        [int, int, list[Card], list[Card], int, PersonalityConfig | None, list[ClashResult], list[Stance]],
        Card,
    ],
    get_opponent_qte: Callable[[int], float],
    trace: TraceLogger | None = None,
    on_deal: Optional[Callable[[int, list[Card], list[Card]], None]] = None,
    on_clash_resolved: Optional[Callable[[int, int, Card, Card, StanceOutcome], None]] = None,
    on_turn_complete: Optional[Callable[[int, TurnResult, float, float], None]] = None,
    on_lap_complete: Optional[Callable[[int, int], None]] = None,
    on_clashes_complete: Optional[Callable[[int, list[ClashResult]], None]] = None,
) -> MatchResult:
    """Run a full match between two combatants.

    Each turn:
      1. Both sides draw 6 cards.
      2. For each of 3 clash positions:
          a. Player picks 1 card from their remaining hand.
          b. Opponent picks 1 card from their remaining hand.
          c. The clash is resolved and the result is broadcast.
      3. Damage is computed for all 3 clashes (battle_mult, mitigation).

    The match ends after *max_turns*.  The higher position wins.

    Callbacks:
        on_deal(turn, player_hand, opponent_hand)
        on_clash_resolved(turn, clash_index, player_card, opponent_card, outcome)
        on_turn_complete(turn, turn_result, cum_player_dp, cum_opponent_dp)
        on_lap_complete(phase_index, total_phases)
    """
    player = copy.copy(cfg.player_stats)
    opponent = copy.copy(cfg.opponent_stats)
    personality = get_personality(cfg.rival_personality) if cfg.rival_personality else None

    player_max_hp = player.level * HP_PER_LEVEL
    opponent_max_hp = opponent.level * HP_PER_LEVEL
    avg_max_hp = (player_max_hp + opponent_max_hp) / 2
    rubber_band_threshold = avg_max_hp * RUBBER_BAND_FRACTION

    result = MatchResult(
        player_name=player.name,
        opponent_name=opponent.name,
        total_turns=cfg.max_turns,
        player_max_hp=player_max_hp,
        opponent_max_hp=opponent_max_hp,
    )
    main_trace = trace or TraceLogger()

    rng = Random(cfg.seed) if cfg.seed is not None else Random()
    p_deck = Deck.build(player.pow, player.en, player.han, rng)
    o_deck = Deck.build(opponent.pow, opponent.en, opponent.han, rng, reshuffle_on_end=True)

    player_stance_history: list[Stance] = []
    prev_phase: int = -1

    for turn_num in range(1, cfg.max_turns + 1):
        phase_index = get_phase(turn_num, cfg.encounter_type)
        total_phases = get_total_phases(cfg.encounter_type)

        if phase_index != prev_phase:
            if on_lap_complete:
                on_lap_complete(phase_index, total_phases)
            prev_phase = phase_index

        p_hand = p_deck.draw(6)

        phase = personality.phases[phase_index] if personality and phase_index < len(personality.phases) else None
        reqs = phase.hand_requirements if phase else None
        o_hand = o_deck.prepare_turn_hand(reqs)

        if on_deal:
            on_deal(turn_num, p_hand, o_hand)

        p_remaining = list(p_hand)
        o_remaining = list(o_hand)
        p_cards: list[Card] = []
        o_cards: list[Card] = []
        clash_history: list[ClashResult] = []

        for clash_pos in range(3):
            p_card = get_player_card(turn_num, clash_pos, p_remaining, o_remaining, clash_history)
            o_card = get_opponent_card(
                turn_num, clash_pos, o_remaining, p_remaining,
                phase_index, personality, clash_history, player_stance_history,
            )

            p_remaining.remove(p_card)
            o_remaining.remove(o_card)
            p_cards.append(p_card)
            o_cards.append(o_card)

            outcome = resolve_stance(p_card.stance, o_card.stance)
            cr = ClashResult(clash_pos, p_card.stance, o_card.stance, outcome)
            clash_history.append(cr)
            player_stance_history.append(p_card.stance)

            if on_clash_resolved:
                on_clash_resolved(turn_num, clash_pos, p_card, o_card, outcome)

        if on_clashes_complete:
            on_clashes_complete(turn_num, clash_history)

        p_qte = get_player_qte(turn_num)
        p_han_pct = player.han / (player.pow + player.en + player.han) if (player.pow + player.en + player.han) > 0 else 1 / 3
        p_qte = apply_han_qte_mod(p_qte, p_han_pct)

        o_qte = get_opponent_qte(turn_num)
        o_han_pct = opponent.han / (opponent.pow + opponent.en + opponent.han) if (opponent.pow + opponent.en + opponent.han) > 0 else 1 / 3
        o_qte = apply_han_qte_mod(o_qte, o_han_pct)

        turn_state = TurnState(
            turn_number=turn_num,
            player_cards=p_cards,
            opponent_cards=o_cards,
            player_qte=p_qte,
            opponent_qte=o_qte,
        )

        player_gap = result.player_total_dp - result.opponent_total_dp

        turn_result = resolve_turn(
            turn_state, player, opponent,
            main_trace, player_gap=player_gap,
            rubber_band_threshold=rubber_band_threshold,
        )
        turn_result.player_hand = list(p_hand)
        turn_result.opponent_hand = list(o_hand)

        result.player_total_dp += turn_result.player_dp
        result.opponent_total_dp += turn_result.opponent_dp
        result.turn_results.append(turn_result)

        if on_turn_complete:
            on_turn_complete(turn_num, turn_result, result.player_total_dp, result.opponent_total_dp)

        result.turns_played = turn_num

        p_deck.end_turn(p_cards, p_remaining)
        o_deck.end_turn(o_cards, o_remaining)

    result.player_position = result.player_total_dp / result.opponent_max_hp
    result.opponent_position = result.opponent_total_dp / result.player_max_hp

    if result.player_position > result.opponent_position:
        result.winner = result.player_name
    else:
        result.winner = result.opponent_name

    return result
