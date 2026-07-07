class_name FaceController
extends Node

@onready var face_atk: TextureRect = $CanvasLayer/CenterContent/OpponentPanel/FaceStack/FaceATK
@onready var face_def: TextureRect = $CanvasLayer/CenterContent/OpponentPanel/FaceStack/FaceDEF
@onready var face_neu: TextureRect = $CanvasLayer/CenterContent/OpponentPanel/FaceStack/FaceNEU
@onready var tell_overlay: TextureRect = $CanvasLayer/CenterContent/OpponentPanel/FaceStack/TellOverlay

var _current_blend_target: int = Globals.Stance.ATTACK
var _crossfade_progress: float = 0.0
var _crossfade_duration: float = 0.5
var _is_crossfading: bool = false
var _from_stance: int = Globals.Stance.ATTACK
var _to_stance: int = Globals.Stance.ATTACK

func set_face_sequence(expressions: Array) -> void:
	face_atk.modulate.a = 0.0
	face_def.modulate.a = 0.0
	face_neu.modulate.a = 0.0
	tell_overlay.modulate.a = 0.0

func set_tell_alpha(intensity: float, is_deceptive: bool) -> void:
	tell_overlay.modulate.a = intensity * (1.0 if is_deceptive else 0.0)

func show_stance(stance: int) -> void:
	face_atk.modulate.a = 1.0 if stance == Globals.Stance.ATTACK else 0.0
	face_def.modulate.a = 1.0 if stance == Globals.Stance.DEFEND else 0.0
	face_neu.modulate.a = 1.0 if stance == Globals.Stance.NEUTRAL else 0.0
	_current_blend_target = stance

func crossfade_to(stance: int, duration: float = 0.5) -> void:
	_from_stance = _current_blend_target
	_to_stance = stance
	_crossfade_duration = duration
	_crossfade_progress = 0.0
	_is_crossfading = true

func _process(delta: float) -> void:
	if not _is_crossfading:
		return
	_crossfade_progress += delta / _crossfade_duration
	if _crossfade_progress >= 1.0:
		_crossfade_progress = 1.0
		_is_crossfading = false
		show_stance(_to_stance)
		return
	var t = _crossfade_progress
	face_atk.modulate.a = _get_stance_alpha(Globals.Stance.ATTACK, t)
	face_def.modulate.a = _get_stance_alpha(Globals.Stance.DEFEND, t)
	face_neu.modulate.a = _get_stance_alpha(Globals.Stance.NEUTRAL, t)

func _get_stance_alpha(stance: int, t: float) -> float:
	var from_val = 1.0 if _from_stance == stance else 0.0
	var to_val = 1.0 if _to_stance == stance else 0.0
	return lerp(from_val, to_val, t)

func start_blend_cycle(entry_stance: int, apex_stance: int, exit_stance: int) -> void:
	show_stance(entry_stance)
