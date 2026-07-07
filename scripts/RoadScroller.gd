extends Node

@export var material: ShaderMaterial

var scroll_speed: float = 0.05
var _uv_offset: Vector2 = Vector2.ZERO
var _scrolling: bool = false

func start_scrolling() -> void:
	_scrolling = true

func stop_scrolling() -> void:
	_scrolling = false

func set_speed(factor: float) -> void:
	scroll_speed = 0.05 * factor

func _process(delta: float) -> void:
	if not _scrolling:
		return
	_uv_offset.y += scroll_speed * delta
	_set_shader_uv_offset()

func _set_shader_uv_offset() -> void:
	if material:
		material.set_shader_parameter("uv_offset", _uv_offset)

func transition_to_corner() -> void:
	set_speed(1.5)
	var timer = get_tree().create_timer(0.5)
	await timer.timeout
	set_speed(0.6)
