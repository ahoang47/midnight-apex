extends Node

@onready var overlay: CenterContainer = $CanvasLayer/QTEOverlay
@onready var prompt_label: Label = $CanvasLayer/QTEOverlay/QTEPromptLabel
@onready var mash_indicator: TextureProgressBar = $CanvasLayer/QTEOverlay/MashIndicator
@onready var timing_indicator: Control = $CanvasLayer/QTEOverlay/TimingIndicator
@onready var qte_target: TextureRect = $CanvasLayer/QTEOverlay/TimingIndicator/QteTarget
@onready var qte_marker: TextureRect = $CanvasLayer/QTEOverlay/TimingIndicator/QteMarker

var _qte_type: int
var _difficulty: Dictionary = {}
var _running: bool = false
var _elapsed: float = 0.0
var _duration: float = 3.5
var _press_count: int = 0
var _mash_fill: float = 0.0
var _timing_phase: float = 0.0
var _successful_presses: int = 0
var _total_opportunities: int = 0
var _last_tick_time: float = 0.0
var _input_ready: bool = true

signal qte_completed(score)

func start(qte_type: int, difficulty: Dictionary) -> void:
	_qte_type = qte_type
	_difficulty = difficulty
	_running = true
	_elapsed = 0.0
	_press_count = 0
	_mash_fill = 0.0
	_timing_phase = 0.0
	_successful_presses = 0
	_total_opportunities = 0
	_last_tick_time = 0.0

	overlay.visible = true

	if qte_type == Globals.QteType.MASH:
		mash_indicator.visible = true
		timing_indicator.visible = false
		prompt_label.text = "MASH! (Space/X)"
		mash_indicator.value = 0.0
		mash_indicator.max_value = 100.0
	else:
		mash_indicator.visible = false
		timing_indicator.visible = true
		prompt_label.text = "TIMING! (Enter/Z)"

func stop() -> float:
	_running = false
	overlay.visible = false

	if _qte_type == Globals.QteType.MASH:
		var score = (_mash_fill / 100.0) * 10.0
		emit_signal("qte_completed", clamp(score, 1.0, 10.0))
		return clamp(score, 1.0, 10.0)
	else:
		var score = float(_successful_presses) / max(1, _total_opportunities) * 10.0
		emit_signal("qte_completed", clamp(score, 1.0, 10.0))
		return clamp(score, 1.0, 10.0)

func _process(delta: float) -> void:
	if not _running:
		return
	_elapsed += delta

	if _qte_type == Globals.QteType.MASH:
		_process_mash(delta)
	else:
		_process_timing(delta)

	if _elapsed >= _duration:
		stop()

func _process_mash(delta: float) -> void:
	var speed_mult = _difficulty.get("speed_multiplier", 1.0)
	_mash_fill -= delta * 15.0 * speed_mult
	_mash_fill = max(0.0, _mash_fill)
	mash_indicator.value = _mash_fill

func _process_timing(delta: float) -> void:
	_timing_phase += delta * 2.0
	var marker_pos = sin(_timing_phase * TAU) * 0.5 + 0.5
	qte_marker.position.x = marker_pos * timing_indicator.size.x

func try_press() -> void:
	if not _running:
		return
	if _qte_type == Globals.QteType.MASH:
		_mash_fill = min(100.0, _mash_fill + 8.0)
		mash_indicator.value = _mash_fill
		_press_count += 1
	else:
		var window_ms = _difficulty.get("timing_window_ms", 800)
		var window_fraction = window_ms / 1000.0 * 2.0
		var marker_pos = sin(_timing_phase * TAU) * 0.5 + 0.5
		var center = 0.5
		if abs(marker_pos - center) < window_fraction:
			_successful_presses += 1
		_total_opportunities += 1

static func qte_difficulty(player_level: int, opponent_level: int) -> Dictionary:
	var gap = opponent_level - player_level
	return {
		"timing_window_ms": max(Globals.QTE_TIMING_WINDOW_MIN_MS,
			Globals.QTE_TIMING_WINDOW_BASE_MS - gap * Globals.QTE_TIMING_WINDOW_PER_GAP),
		"speed_multiplier": 1.0 + max(0, gap) * Globals.QTE_MASH_SPEED_PER_GAP,
	}
