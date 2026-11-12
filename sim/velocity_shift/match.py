from __future__ import annotations
"""Multi-turn match loop — draw, play, resolve, repeat.

Each turn consists of 3 sequential clashes. After each card is played
the player sees the result before picking the next card.

The default engine is final-v1 Phi/tau progress (visible QTE zone,
kappa, LINE_SET_C). Set MatchConfig.legacy_hp_dp to use the older HP/DP path.
"""

import copy
from random import Random
from typing import Callable, Optional

from .models import Stance, StanceOutcome, Card, CombatantStats, MatchConfig, MatchResult, \
    TurnResult, TurnState, ClashResult, PersonalityConfig
from .combat import resolve_turn, resolve_turn_legacy, pick_line, stances_to_cards, corner_at_turn, draw_weighted_hand, plan_player_cards
from .equations import resolve_stance, HP_PER_LEVEL, apply_han_qte_mod, RUBBER_BAND_FRACTION, OPPONENT_QTE, raw_qte_score, mean_phase_qte, phase_raw_qte
from .deck import Deck
from .trace import TraceLogger
from .ai import get_personality, get_phase, get_total_phases


def run_match(
    cfg: MatchConfig,
    get_player_card: Callable[[int, int, list[Card], list[Card], list[ClashResult]], Card],
    get_player_qte: Callable[[int], float | list | tuple | None],
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
    on_line_picked: Optional[Callable[[int, str, list[Stance]], None]] = None,
) -> MatchResult:
    """Run a full match between two combatants.

    Each turn:
      1. Both sides draw 6 cards.
      2. For each of 3 clash positions:
          a. Player picks 1 card from their remaining hand.
          b. Opponent picks 1 card from their remaining hand.
          c. The clash is resolved and the result is broadcast.
      3. Default: each clash adds Phi/tau progress (higher total wins, ties allowed).
         legacy_hp_dp: damage is computed for all 3 clashes (battle_mult, mitigation).

    The match ends after *max_turns*.

    Callbacks:
        on_deal(turn, player_hand, opponent_hand)
        on_clash_resolved(turn, clash_index, player_card, opponent_card, outcome)
        on_turn_complete(turn, turn_result, cum_player_progress, cum_opponent_progress)
        on_lap_complete(phase_index, total_phases)
        on_line_picked(turn, corner_type, line) — when district line tables are in use
    """
    player = copy.copy(cfg.player_stats)
    opponent = copy.copy(cfg.opponent_stats)
    personality = get_personality(cfg.rival_personality) if cfg.rival_personality else None
    legacy = cfg.legacy_hp_dp

    player_max_hp = player.level * HP_PER_LEVEL
    opponent_max_hp = opponent.level * HP_PER_LEVEL
    avg_max_hp = (player_max_hp + opponent_max_hp) / 2
    rubber_band_threshold = avg_max_hp * RUBBER_BAND_FRACTION if legacy else 0.0

    result = MatchResult(
        player_name=player.name,
        opponent_name=opponent.name,
        total_turns=cfg.max_turns,
        player_max_hp=player_max_hp,
        opponent_max_hp=opponent_max_hp,
    )
    main_trace = trace or TraceLogger()

    rng = Random(cfg.seed) if cfg.seed is not None else Random()
    p_deck = o_deck = None
    if legacy:
        p_deck = Deck.build(player.pow, player.en, player.han, rng)
        o_deck = Deck.build(opponent.pow, opponent.en, opponent.han, rng, reshuffle_on_end=True)

    # District line tables: a whole line is drawn once per corner/turn from
    # this same match RNG. Personality/archetype hand requirements are skipped.
    use_lines = bool(cfg.district and cfg.corners)

    player_stance_history: list[Stance] = []
    prev_phase: int = -1

    for turn_num in range(1, cfg.max_turns + 1):
        phase_index = get_phase(turn_num, cfg.encounter_type)
        total_phases = get_total_phases(cfg.encounter_type)

        if phase_index != prev_phase:
            if on_lap_complete:
                on_lap_complete(phase_index, total_phases)
            prev_phase = phase_index

        planned_line: list[Stance] | None = None
        corner: str | None = None
        if use_lines:
            corner = corner_at_turn(cfg.corners, turn_num)
            planned_line = pick_line(cfg.district, corner, rng)
            if on_line_picked:
                on_line_picked(turn_num, corner, planned_line)

        planned_player: list[Card] | None = None
        if legacy:
            p_hand = p_deck.draw(6)
            if use_lines:
                o_hand = stances_to_cards(planned_line)
            else:
                phase = personality.phases[phase_index] if personality and phase_index < len(personality.phases) else None
                reqs = phase.hand_requirements if phase else None
                o_hand = o_deck.prepare_turn_hand(reqs)
        else:
            # Oracle-style: 6 cards i.i.d. from stat-weighted deck, no persistent shoe.
            # When q_read is set, the v4 read + assign also runs on this same match RNG
            # (line already drawn; then hand; then read rolls and assign_hand).
            p_hand = draw_weighted_hand(player.pow, player.en, player.han, rng)
            if use_lines:
                o_hand = stances_to_cards(planned_line)
                q_read = cfg.player_read if cfg.player_read is not None else cfg.player_quality
                if q_read is not None:
                    planned_player = plan_player_cards(
                        cfg.district, corner, planned_line, p_hand, q_read, rng,
                    )
            else:
                o_hand = draw_weighted_hand(opponent.pow, opponent.en, opponent.han, rng)

        if on_deal:
            on_deal(turn_num, p_hand, o_hand)

        p_remaining = list(p_hand)
        o_remaining = list(o_hand)
        p_cards: list[Card] = []
        o_cards: list[Card] = []
        clash_history: list[ClashResult] = []

        for clash_pos in range(3):
            if planned_player is not None:
                p_card = planned_player[clash_pos]
            else:
                p_card = get_player_card(turn_num, clash_pos, p_remaining, o_remaining, clash_history)
            if use_lines:
                o_card = o_remaining[0]
            else:
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

        if legacy:
            p_qte = get_player_qte(turn_num)
            p_han_pct = player.han / (player.pow + player.en + player.han) if (player.pow + player.en + player.han) > 0 else 1 / 3
            p_qte = apply_han_qte_mod(p_qte, p_han_pct)
            o_qte = get_opponent_qte(turn_num)
            o_han_pct = opponent.han / (opponent.pow + opponent.en + opponent.han) if (opponent.pow + opponent.en + opponent.han) > 0 else 1 / 3
            o_qte = apply_han_qte_mod(o_qte, o_han_pct)
        else:
            # Playable engine: raw q_time in [0, 1]. HAN is applied inside
            # clash_progress (no knot_window). If a skill profile or
            # player_timing is configured, the score is E[s] at the race's
            # fixed r (and qte_window_mod); otherwise the callback value is
            # already a raw score (CLI / explicit test callbacks). A 3-tuple
            # of Entry/Apex/Exit scores is averaged into that single raw_qte
            # (unplayed / None = 0; Austin, 2026-11-11); clash math is unchanged.
            # Opponent timing is OPPONENT_QTE.
            p_phases: list[float] = []
            if cfg.player_qte_profile or cfg.player_timing is not None or cfg.player_quality is not None:
                p_tot = player.pow + player.en + player.han
                o_tot = opponent.pow + opponent.en + opponent.han
                r = p_tot / o_tot if o_tot else 1.0
                q_time = cfg.player_timing if cfg.player_timing is not None else cfg.player_quality
                p_qte = raw_qte_score(
                    r,
                    profile=cfg.player_qte_profile,
                    q_time=None if cfg.player_qte_profile else q_time,
                    window_mod=cfg.qte_window_mod,
                )
            else:
                cb = get_player_qte(turn_num)
                if isinstance(cb, (list, tuple)) and len(cb) == 3 and not isinstance(cb, (str, bytes)):
                    p_phases = [phase_raw_qte(v) for v in cb]
                    p_qte = mean_phase_qte(cb)
                else:
                    p_qte = cb
            o_qte = OPPONENT_QTE

        turn_state = TurnState(
            turn_number=turn_num,
            player_cards=p_cards,
            opponent_cards=o_cards,
            player_qte=p_qte,
            opponent_qte=o_qte,
            player_qte_phases=p_phases if not legacy else [],
        )

        if legacy:
            player_gap = result.player_total_dp - result.opponent_total_dp
            turn_result = resolve_turn_legacy(
                turn_state, player, opponent,
                main_trace, player_gap=player_gap,
                rubber_band_threshold=rubber_band_threshold,
            )
        else:
            turn_result = resolve_turn(
                turn_state, player, opponent,
                main_trace, race_length=cfg.max_turns,
            )
        turn_result.player_hand = list(p_hand)
        turn_result.opponent_hand = list(o_hand)
        if use_lines:
            turn_result.corner_type = corner
            turn_result.opponent_line = list(planned_line)

        if legacy:
            result.player_total_dp += turn_result.player_dp
            result.opponent_total_dp += turn_result.opponent_dp
        else:
            result.player_total_progress += turn_result.player_progress
            result.opponent_total_progress += turn_result.opponent_progress
            result.player_total_dp = result.player_total_progress
            result.opponent_total_dp = result.opponent_total_progress
        result.turn_results.append(turn_result)

        if on_turn_complete:
            on_turn_complete(
                turn_num, turn_result,
                result.player_total_progress if not legacy else result.player_total_dp,
                result.opponent_total_progress if not legacy else result.opponent_total_dp,
            )

        result.turns_played = turn_num

        if legacy:
            p_deck.end_turn(p_cards, p_remaining)
            o_deck.end_turn(o_cards, o_remaining)

    if legacy:
        result.player_position = result.player_total_dp / result.opponent_max_hp if result.opponent_max_hp else 0.0
        result.opponent_position = result.opponent_total_dp / result.player_max_hp if result.player_max_hp else 0.0
        if result.player_position > result.opponent_position:
            result.winner = result.player_name
        else:
            result.winner = result.opponent_name
    else:
        gp = result.player_total_progress
        go = result.opponent_total_progress
        total = gp + go
        result.player_position = gp / total if total else 0.5
        result.opponent_position = go / total if total else 0.5
        if gp > go:
            result.winner = result.player_name
        elif go > gp:
            result.winner = result.opponent_name
        else:
            result.winner = "Tie"

    return result
