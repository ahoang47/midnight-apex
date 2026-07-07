extends Node

@onready var phase_label: Label = $CanvasLayer/TopBar/PhaseLabel

func announce_lap(phase: int, total: int) -> void:
	phase_label.text = "LAP " + str(phase + 1) + "/" + str(total)
	var tween = create_tween()
	tween.tween_property(phase_label, "modulate:a", 0.0, 0.0)
	tween.tween_property(phase_label, "modulate:a", 1.0, 0.3)
	tween.tween_interval(1.5)
	tween.tween_property(phase_label, "modulate:a", 0.0, 0.3)
