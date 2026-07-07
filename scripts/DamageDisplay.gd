extends Node

@onready var player_bar: TextureProgressBar = $CanvasLayer/BottomBar/DPBarPlayer
@onready var opponent_bar: TextureProgressBar = $CanvasLayer/CenterContent/OpponentPanel/DPBarOpponent
@onready var position_label: Label = $CanvasLayer/TopBar/PositionLabel

func animate_bars(player_new_total: float, opponent_new_total: float,
		player_max_hp: float, opponent_max_hp: float) -> void:
	var tween = create_tween()
	tween.set_parallel(true)
	tween.tween_property(player_bar, "value", player_new_total, 0.8)
	tween.tween_property(opponent_bar, "value", opponent_new_total, 0.8)
	player_bar.max_value = player_max_hp
	opponent_bar.max_value = opponent_max_hp
