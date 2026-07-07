class_name StraightTimer
extends TextureProgressBar

var total_time: float = 12.0
var phase_times: Array[float] = [4.0, 4.0, 4.0]
var current_phase: int = 0
var _elapsed: float = 0.0
var _running: bool = false

signal phase_timeout(phase_index)
signal straight_complete

func start() -> void:
	_elapsed = 0.0
	current_phase = 0
	_running = true
	max_value = total_time
	value = 0.0

func _process(delta: float) -> void:
	if not _running:
		return
	_elapsed += delta
	value = _elapsed
	if _elapsed >= total_time:
		_running = false
		emit_signal("straight_complete")
		return
	var new_phase = _get_phase_at_time(_elapsed)
	if new_phase != current_phase:
		current_phase = new_phase
		emit_signal("phase_timeout", current_phase)

func stop() -> void:
	_running = false

func _get_phase_at_time(t: float) -> int:
	var accum = 0.0
	for i in range(phase_times.size()):
		accum += phase_times[i]
		if t < accum:
			return i
	return phase_times.size() - 1
