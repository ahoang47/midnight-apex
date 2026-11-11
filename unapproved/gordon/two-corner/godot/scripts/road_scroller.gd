## guide §14.2 RoadScroller: uv_offset += scroll_speed * factor * delta.
## transition_to_corner: set_speed(1.5), after 0.5 s set_speed(0.6). Mirrors threejs/src/track.js RoadScroller.
extends RefCounted
var cfg: Dictionary
var uv_offset := 0.0
var factor := 1.0
var burst := 0.0

func _init(c: Dictionary) -> void:
	cfg = c; factor = c.straight_factor

func set_speed(f: float) -> void: factor = f
func transition_to_corner() -> void:
	set_speed(cfg.corner_burst_factor); burst = cfg.corner_burst_s
func transition_to_straight() -> void:
	burst = 0.0; set_speed(cfg.straight_factor)
func update(dt: float) -> void:
	if burst > 0.0:
		burst -= dt
		if burst <= 0.0: set_speed(cfg.corner_factor)
	uv_offset += float(cfg.scroll_speed) * factor * dt
func scroll_m() -> float: return uv_offset * float(cfg.road_uv_length_m)
func speed_ms() -> float: return float(cfg.scroll_speed) * factor * float(cfg.road_uv_length_m)
