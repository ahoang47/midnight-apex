extends Node

func load_battle(config: MatchConfig) -> void:
	get_tree().change_scene_to_file("res://scenes/Battle.tscn")
	await get_tree().scene_changed
	var turn_manager = get_tree().current_scene.find_child("TurnManager", true, false)
	if turn_manager and turn_manager.has_method("start_match"):
		turn_manager.start_match(config)

func load_menu() -> void:
	pass

func load_results(result: Dictionary) -> void:
	pass
