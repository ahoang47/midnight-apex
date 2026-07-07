extends Camera3D

var _default_pos: Vector3 = Vector3(0, 5, 8)
var _corner_offset_left: Vector3 = Vector3(-3, 0.5, 1)
var _corner_offset_right: Vector3 = Vector3(3, 0.5, 1)

func _ready() -> void:
	position = _default_pos

func transition_to_corner(corner_direction: String) -> void:
	var target = _default_pos
	if corner_direction == "left":
		target += _corner_offset_left
	elif corner_direction == "right":
		target += _corner_offset_right
	var tween = create_tween()
	tween.set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(self, "position", target, 1.0)

func transition_to_straight() -> void:
	var tween = create_tween()
	tween.set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(self, "position", _default_pos, 1.0)

func swing_overtake() -> void:
	var tween = create_tween()
	tween.tween_property(self, "position:x", position.x + 1.0, 0.15)
	tween.tween_property(self, "position:x", position.x, 0.15)

func look_at_target(target: Vector3) -> void:
	look_at(target)
