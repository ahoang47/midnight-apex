extends Node

var straight_base_z: float = 0.0

func snap_to_gap(gap: float, max_gap: float) -> void:
	var target_z = straight_base_z + lerp(-5.0, 5.0, clampf(gap / max_gap, -1.0, 1.0))
	var tween = create_tween()
	tween.tween_property(get_parent(), "position:z", target_z, 0.5)

func play_surge() -> void:
	var tween = create_tween()
	tween.set_trans(Tween.TRANS_BOUNCE)
	tween.tween_property(get_parent(), "position:z", get_parent().position.z - 0.5, 0.3)
	tween.tween_property(get_parent(), "position:z", get_parent().position.z, 0.3)

func play_drop() -> void:
	var tween = create_tween()
	tween.set_trans(Tween.TRANS_BOUNCE)
	tween.tween_property(get_parent(), "position:z", get_parent().position.z + 0.5, 0.3)
	tween.tween_property(get_parent(), "position:z", get_parent().position.z, 0.3)

func begin_corner_traversal(path: Curve3D, duration: float = 3.5) -> void:
	pass

func play_overtake() -> void:
	pass
