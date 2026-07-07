extends Node

var _entry_stance: int = Globals.Stance.ATTACK
var _apex_stance: int = Globals.Stance.ATTACK
var _exit_stance: int = Globals.Stance.ATTACK
var _blend_schedule: float = 0.0
var _running: bool = false

signal stance_blend_updated(stance)

func start_blend_cycle(entry_stance: int, apex_stance: int,
		exit_stance: int, corner_direction: String) -> void:
	_entry_stance = entry_stance
	_apex_stance = apex_stance
	_exit_stance = exit_stance
	_blend_schedule = 0.0
	_running = true

func update_blend(delta: float) -> void:
	if not _running:
		return
	_blend_schedule += delta
	var current_stance = _entry_stance
	if _blend_schedule >= 8.0:
		current_stance = _exit_stance
	elif _blend_schedule >= 4.0:
		current_stance = _apex_stance
	emit_signal("stance_blend_updated", current_stance)

func set_tell_alpha(intensity: float, is_deceptive: bool) -> void:
	pass

func stop() -> void:
	_running = false
