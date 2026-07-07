extends Node

signal match_started(cfg)
signal straight_started(turn, turn_type, stances, bluff_flags)
signal phase_pick(phase_index, phase_name)
signal card_selected(stance)
signal phase_pick_timeout(phase_index)
signal corner_started(player_stances, opponent_stances)
signal clash_resolved(position, player_stance, opponent_stance, outcome)
signal corner_ended(qte_score)
signal damage_batch_done(player_dp, opponent_dp, cum_p, cum_o, battle_mult)
signal turn_ended(turn)
signal lap_began(phase, total)
signal match_ended(winner, player_name, opponent_name)
