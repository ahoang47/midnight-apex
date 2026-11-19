## track.tscn: the Touge road surface (StraightRoad + the continuous course road, guide §13.1), built from code so the editor
## viewport shows exactly what the game draws. @tool: in the editor the road rebuilds from spec/display.json +
## spec/race_config.json whenever the scene opens or "Rebuild road" is pressed. At runtime main.gd calls build_course() and
## rebuild() for each corner (the road is rebuilt with the upcoming corner's straight). Geometry numbers are the display
## PLACEHOLDERS of display.json (road.straight_m / exit_m / by_code, lane_width_m, districts.<dk>.lamp_period_m); the inspector
## shows them read-only under "Spec values" so the JSON stays the single source.
@tool
extends Node3D
const ArtKit = preload("res://scripts/art_kit.gd")
const Course = preload("res://scripts/course.gd")

@export_file("*.json") var display_spec := "res://spec/display.json"
@export_file("*.json") var race_config := "res://spec/race_config.json"
## district whose road texture the editor preview uses (the race picks it per corner from race_config.json)
@export var district := "touge"
## editor preview only: draw the district fog (off = the whole course stays readable from a top view)
@export var preview_fog := false:
	set(v): preview_fog = v; if is_inside_tree() and Engine.is_editor_hint(): _editor_build()
@export var preview_in_editor := true:
	set(v): preview_in_editor = v; if is_inside_tree() and Engine.is_editor_hint(): _editor_build()
@export_tool_button("Rebuild road") var rebuild_road = _editor_build

var road_W := 5.5
var _spec := {}

## straight S, corner 1, join, corner 2, exit. The join is 10 + (S - 8) m so the car ends corner 1's playback exactly where
## corner 2's selection starts (s = 8 on corner 2's scroll straight): one continuous road, no teleport. (moved from main.gd)
static func build_course(disp: Dictionary, cfg: Dictionary) -> Dictionary:
	var S: float = disp.road.straight_m
	var course = Course.new(); course.add_straight(S)
	var views := []; var straights := []
	var n: int = cfg.corners.size()
	for i in n:
		var c: Dictionary = cfg.corners[i]
		var g: Dictionary = disp.road.by_code.get(String(c.corner), {"corner_radius_m": 20.0, "corner_angle_deg": 90.0})
		var R: float = g.corner_radius_m; var A: float = deg_to_rad(float(g.corner_angle_deg)); var sg := 1.0 if String(c.dir) == "L" else -1.0
		var anchor: float = course.length - S
		var E: float = float(disp.road.exit_m) if i == n - 1 else 10.0 + S - 8.0
		course.add_arc(R, A, sg).add_straight(E)
		views.append(Course.View.new(course, anchor, S, R, A, E, sg))
	for i in n:
		var a: Dictionary = course.at(views[i].off)
		straights.append(Course.new(a.x, a.z, a.tx, a.tz).add_straight(100000.0))
	return {"course": course, "views": views, "straights": straights}

## the period-aligned range a district covers along pth (shared with touge_dressing.gd so props sit on the painted pools)
static func span(D: Dictionary, s0: float, s1: float) -> Array:   # [a0, range] as 64-bit floats (not Vector2: float32)
	var per: float = D.lamp_period_m
	var a0 := floorf(s0 / per) * per; var rng: float = ceilf((s1 - a0) / per) * per
	return [a0, rng]

func clear() -> void:
	for ch in get_children():
		remove_child(ch); ch.queue_free()

## one road strip along pth (s0..s1, snapped to the lamp period), added as a child named nm; returns it
func build_strip(art, pth, s0: float, s1: float, dk: String, nm: String) -> MeshInstance3D:
	var D: Dictionary = art.DIST[dk]; var per: float = D.lamp_period_m; var W: float = art.road_W
	var sp := span(D, s0, s1); var a0: float = sp[0]; var rng: float = sp[1]
	var mi: MeshInstance3D = art.strip(pth, a0, a0 + rng, -W, W, art.strip_mat(dk + "_road", per))
	mi.name = nm; add_child(mi)
	return mi

func _ready() -> void:
	if Engine.is_editor_hint(): _editor_build()

func _editor_build() -> void:
	clear()
	if not preview_in_editor: return
	var disp := ArtKit.load_json(display_spec); var cfg := ArtKit.load_json(race_config)
	var art = ArtKit.new(disp); road_W = art.road_W
	var tr := build_course(disp, cfg)
	build_strip(art, tr.course, -60.0, tr.course.length + 60.0, district, "CourseRoad")
	art.apply_fog(district)
	if not preview_fog:
		for m in art.scroll_mats: m.set_shader_parameter("fog_amount", 0.0)
	_spec = {"straight_m": float(disp.road.straight_m), "exit_m": float(disp.road.exit_m), "lane_width_m": float(disp.lane_width_m),
		"road_half_width_m": art.road_W, "course_length_m": float(tr.course.length), "lamp_period_m": float(art.DIST[district].lamp_period_m)}
	for code in disp.road.by_code: _spec["%s_radius_m" % code] = float(disp.road.by_code[code].corner_radius_m); _spec["%s_angle_deg" % code] = float(disp.road.by_code[code].corner_angle_deg)
	notify_property_list_changed()

## read-only mirrors of the spec numbers (edit spec/display.json, then Rebuild road)
func _get_property_list() -> Array:
	var out := [{"name": "Spec values (display.json, read-only)", "type": TYPE_NIL, "usage": PROPERTY_USAGE_GROUP, "hint_string": "spec_"}]
	for k in _spec: out.append({"name": "spec_" + k, "type": TYPE_FLOAT, "usage": PROPERTY_USAGE_EDITOR | PROPERTY_USAGE_READ_ONLY})
	return out

func _get(p: StringName):
	var s := String(p)
	if s.begins_with("spec_") and _spec.has(s.substr(5)): return _spec[s.substr(5)]
	return null
