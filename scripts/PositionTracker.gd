extends Node

var player_total_dp: float = 0.0
var opponent_total_dp: float = 0.0

signal position_changed(label)

func add_turn_damage(player_dp: float, opponent_dp: float) -> void:
	player_total_dp += player_dp
	opponent_total_dp += opponent_dp

func get_player_gap() -> float:
	return player_total_dp - opponent_total_dp

func get_rubber_band_threshold(avg_max_hp: float) -> float:
	return avg_max_hp * Globals.RUBBER_BAND_PCT

func get_position_label() -> String:
	if player_total_dp > opponent_total_dp:
		return "1st"
	elif player_total_dp < opponent_total_dp:
		return "2nd"
	return "--"
