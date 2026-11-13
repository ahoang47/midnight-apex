## Unapproved resource-meter concept mockup. Reuses the line-preview Godot project (Gordon's two-corner
## scenes + Arthur's PLAN THE LINE HUD) and composites a left-side resource stack over the Entry chase frame.
## Does not edit Gordon's files. Meters are purely visual; cost / empty rules are not decided.
extends Control
const ArtKit = preload("res://scripts/art_kit.gd")
const Course = preload("res://scripts/course.gd")
const TrackRoad = preload("res://scripts/track_road.gd")
const Track = preload("res://scripts/track.gd")
const Dressing = preload("res://scripts/touge_dressing.gd")
const POST_SH = preload("res://shaders/post.gdshader")
const Chevrons = preload("res://scripts/line_chevrons.gd")

const DIR := "L"
const CODE := "HP"
const LANE_W := 3.3
const STANCE_COL := {"A": "POW", "D": "EN", "S": "HAN"}
const LANE_OF := {"OUT": "outside", "MID": "center", "IN": "inside"}
const SPEED_MS := 25.0  # display.json road_scroller: 0.05 * 1.0 * 500
const RIVAL_AHEAD := 9.0  # visual_gap.min_spacing_m on a tie
const OVERVIEW_S := 24.0
const CHASE_S := 8.0  # Gordon's s_player during SELECT
const CANON_APEX := "D"
const CANON_EXIT := "A"

var disp: Dictionary
var art
var course  # Course.View of corner 1 (local s, like Gordon's path)
var course_full  # continuous two-corner Course
var view
var cam: Camera3D
var glow_cam: Camera3D
var mirror_cam: Camera3D
var cam_rig
var world_vp: SubViewport
var mirror_vp: SubViewport
var glow_vp: SubViewport
var hud_vp: SubViewport
var hud
var post_mat: ShaderMaterial
var post_rect: TextureRect
var hud_rect: TextureRect
var player_car: Node3D
var rival_car: Node3D
var sky_root: Node3D
var sky_mat: ShaderMaterial
var chevrons: Node3D
var comp_vp: SubViewport
var out_dir: String
var S: float
var R: float
var A: float
var E: float
var fog: Color
var lamp_items: Array = []
var cedar_hidden: Array = []  # originals we toggled; reset per shot

## Same Entry chase framing as a_entry_out_pow.png, so the stack can be judged next to the current HUD.
## phase: "select" = Entry hover OUT/POW; "after_pow" = Entry locked, Apex hover EN;
##        "after_han" = Entry OUT/POW + Apex HAN locked, Exit hover; "next" = next-turn Entry select.
func _res(variant: String, fuel: int, brakes: int, susp: int, extra: Dictionary = {}) -> Dictionary:
	var d := {"variant": variant, "fuel": fuel, "brakes": brakes, "susp": susp, "pips": 8}
	for k in extra:
		d[k] = extra[k]
	return d

func _fr(file: String, res: Dictionary, phase: String = "select") -> Dictionary:
	var fr := {
		"file": file, "entry_lane": "OUT", "entry": "A", "apex": "", "exit": "",
		"hover": 0, "locked": false, "show_rival": true, "stop": 0, "cam": "chase",
		"resources": res,
	}
	if phase == "after_pow":
		fr.apex = "D"
		fr.hover = 1
		fr.stop = 1
	elif phase == "after_han":
		fr.apex = "S"
		fr.hover = 2
		fr.stop = 2
	elif phase == "next":
		# Same shot, but the plan panel is back at Entry select for the next turn.
		fr.entry = "A"
		fr.apex = ""
		fr.exit = ""
		fr.hover = 0
		fr.stop = 0
	return fr

func _e_res(variant: String, fuel: int, brakes: int, susp: int, extra: Dictionary = {}) -> Dictionary:
	# HEAT uses the fuel key (headroom left). Badges are OVERHEAT / LIMP, not LOW / EMPTY.
	return _res(variant, fuel, brakes, susp, extra)


func _e_frames(tag: String, variant: String, states: Array = []) -> Array:
	var all := [
		_fr("%s_full.png" % tag, _e_res(variant, 8, 8, 8), "select"),
		_fr("%s_drain.png" % tag, _e_res(variant, 5, 8, 8, {"ghosts": {"fuel": 3}, "spent": "fuel"}), "after_pow"),
		_fr("%s_low.png" % tag, _e_res(variant, 2, 3, 5, {"warn": ["fuel", "brakes"], "blink": true, "badge": {"fuel": "OVERHEAT"}}), "after_pow"),
		_fr("%s_empty.png" % tag, _e_res(variant, 0, 2, 4, {"warn": ["fuel"], "badge": {"fuel": "LIMP"}}), "after_pow"),
		_fr("%s_susp_spent.png" % tag, _e_res(variant, 0, 2, 2, {"ghosts": {"susp": 3}, "spent": "susp", "badge": {"fuel": "LIMP"}}), "after_han"),
		_fr("%s_susp_refill.png" % tag, _e_res(variant, 0, 2, 8, {"flash": "susp", "badge": {"fuel": "LIMP", "susp": "RECOVER"}}), "next"),
	]
	if states.is_empty():
		return all
	var keep := {}
	for s in states:
		keep[s] = true
	var out: Array = []
	for fr in all:
		for s in states:
			if String(fr.file).ends_with("%s.png" % s):
				out.append(fr)
				break
	return out


func _all_frames() -> Array:
	var out: Array = []
	for v in ["A", "B", "C", "D"]:
		var tag := String(v).to_lower()
		out.append(_fr("%s_full.png" % tag, _res(v, 8, 8, 8), "select"))
		out.append(_fr("%s_drain.png" % tag, _res(v, 5, 8, 8, {"ghosts": {"fuel": 3}, "spent": "fuel"}), "after_pow"))
		out.append(_fr("%s_low.png" % tag, _res(v, 2, 3, 5, {"warn": ["fuel", "brakes"], "blink": true, "badge": {"fuel": "LOW"}}), "after_pow"))
		out.append(_fr("%s_empty.png" % tag, _res(v, 0, 2, 4, {"warn": ["fuel"], "badge": {"fuel": "EMPTY"}}), "after_pow"))
		out.append(_fr("%s_susp_spent.png" % tag, _res(v, 0, 2, 2, {"ghosts": {"susp": 3}, "spent": "susp", "badge": {"fuel": "EMPTY"}}), "after_han"))
		out.append(_fr("%s_susp_refill.png" % tag, _res(v, 0, 2, 8, {"flash": "susp", "badge": {"fuel": "EMPTY", "susp": "RECOVER"}}), "next"))
	# E1 (default E): full International Rally bottom band. All heat / limp states.
	out.append_array(_e_frames("e", "E"))
	# E2: bottom band + slim top strip. Full + low are enough to judge the layout.
	out.append_array(_e_frames("e2", "E2", ["full", "low"]))
	# E3: E1 minus the band map; HAIRPIN L under the sign; E/A/X next to the plan.
	out.append_array(_e_frames("e3", "E3", ["full", "drain", "low", "empty"]))
	# E3B: heat/load meters, new EN/HAN icons. See _e3b_frames.
	out.append_array(_e3b_frames())
	return out


func _e3b_res(load: Dictionary, extra: Dictionary = {}) -> Dictionary:
	# Heat/load fills (0 cool … 1 full). Integers on fuel/brakes/susp are unused
	# by the E3B trough (it reads `load`) but kept so older painters stay safe.
	var d := _e_res("E3B", 8, 8, 8, extra)
	d["load"] = load
	return d


func _e3b_fr(file: String, load: Dictionary, extra: Dictionary = {}, entry: String = "A") -> Dictionary:
	var fr: Dictionary = _fr(file, _e3b_res(load, extra), "select")
	fr.entry = entry
	fr.hover = 0
	return fr


func _e3b_frames() -> Array:
	# Mid mixed loads, all below LIMIT. Featured stance stays OUT/POW.
	var out: Array = []
	out.append(_e3b_fr("e3b_full.png", {"fuel": 0.42, "brakes": 0.58, "susp": 0.30}))
	# One bar (POW / engine heat) through the state model.
	out.append(_e3b_fr("e3b_state_cool.png", {"fuel": 0.16, "brakes": 0.40, "susp": 0.34}))
	out.append(_e3b_fr("e3b_state_mid.png", {"fuel": 0.45, "brakes": 0.40, "susp": 0.34}))
	out.append(_e3b_fr("e3b_state_overrun.png", {"fuel": 0.90, "brakes": 0.40, "susp": 0.34}))
	# Full lock: hover MID/HAN because POW is unavailable.
	out.append(_e3b_fr("e3b_state_locked.png", {"fuel": 1.0, "brakes": 0.40, "susp": 0.34}, {"locked": ["fuel"]}, "S"))
	# Locked, cooling (between RELEASE 0.55 and full). Still locked.
	out.append(_e3b_fr("e3b_state_cooling.png", {"fuel": 0.68, "brakes": 0.40, "susp": 0.34}, {"locked": ["fuel"]}, "S"))
	# Just under RELEASE: unlocked again, POW selectable.
	out.append(_e3b_fr("e3b_state_unlocked.png", {"fuel": 0.50, "brakes": 0.40, "susp": 0.34}))
	# Full-frame narrative shots: one stat (POW) in OVERRUN, then LOCKED.
	out.append(_e3b_fr("e3b_overrun.png", {"fuel": 0.90, "brakes": 0.42, "susp": 0.34}))
	out.append(_e3b_fr("e3b_locked.png", {"fuel": 1.0, "brakes": 0.42, "susp": 0.34}, {"locked": ["fuel"]}, "S"))
	return out


func _ready() -> void:
	out_dir = ProjectSettings.globalize_path("res://").path_join("..")
	disp = ArtKit.load_json("res://spec/display.json")
	art = ArtKit.new(disp)
	fog = Color(disp.districts.touge.fog)
	_build_viewports()
	_build_course()
	_build_world()
	_load_cars()
	var only := OS.get_environment("ONLY")
	for fr in _all_frames():
		var ev := String(fr.resources.variant)
		if only != "" and String(fr.file) != only and only != ev and not (only == "E" and ev.begins_with("E")):
			continue
		_apply_frame(fr, String(fr.cam))
		await _settle(8)
		await _capture(out_dir.path_join(fr.file))
	print("RESOURCE_METERS_OK ", out_dir)
	get_tree().quit(0)


func _in_list(arr: Array, file: String) -> bool:
	for fr in arr:
		if String(fr.file) == file:
			return true
	return false

func _settle(n: int = 6) -> void:
	for i in n:
		await get_tree().process_frame
		await RenderingServer.frame_post_draw

func _build_viewports() -> void:
	world_vp = $WorldVP
	world_vp.world_3d = World3D.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = fog
	env.ambient_light_source = Environment.AMBIENT_SOURCE_DISABLED
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	world_vp.world_3d.environment = env
	world_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	world_vp.msaa_3d = Viewport.MSAA_DISABLED
	world_vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	world_vp.size = Vector2i(640, 480)
	cam_rig = $WorldVP/CameraRig
	cam = cam_rig.cam
	cam.fov = 52.0
	cam.near = 0.1
	cam.far = 400.0
	cam.current = true
	mirror_vp = $MirrorVP
	mirror_vp.world_3d = world_vp.world_3d
	mirror_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	mirror_vp.size = Vector2i(int(disp.mirror.w), int(disp.mirror.h))
	mirror_cam = $MirrorVP/MirrorCam
	mirror_cam.fov = disp.mirror.fov
	mirror_cam.near = float(disp.mirror.near)
	mirror_cam.far = 300.0
	mirror_cam.current = true
	glow_vp = $GlowVP
	glow_vp.world_3d = world_vp.world_3d
	glow_vp.size = Vector2i(640, 480)
	glow_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	glow_vp.msaa_3d = Viewport.MSAA_DISABLED
	glow_cam = $GlowVP/GlowCam
	glow_cam.fov = cam.fov
	glow_cam.near = 0.1
	glow_cam.far = 400.0
	glow_cam.cull_mask = 2
	var genv := Environment.new()
	genv.background_mode = Environment.BG_COLOR
	genv.background_color = Color.BLACK
	glow_cam.environment = genv
	glow_cam.current = true
	post_mat = ShaderMaterial.new()
	post_mat.shader = POST_SH
	post_mat.set_shader_parameter("mirror_rect", Vector4(disp.mirror.x, disp.mirror.y, disp.mirror.w, disp.mirror.h))
	post_mat.set_shader_parameter("res", Vector2(640, 480))
	post_mat.set_shader_parameter("scene_tex", world_vp.get_texture())
	post_mat.set_shader_parameter("mirror_tex", mirror_vp.get_texture())
	post_mat.set_shader_parameter("glow_tex", glow_vp.get_texture())
	post_mat.set_shader_parameter("bloom_k", float(disp.palette.bloom[0]))
	post_mat.set_shader_parameter("sat", float(disp.palette.sat))
	post_mat.set_shader_parameter("mirror_on", 1.0)
	post_rect = $Post
	post_rect.size = Vector2(640, 480)
	post_rect.stretch_mode = TextureRect.STRETCH_SCALE
	post_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	post_rect.texture = world_vp.get_texture()
	post_rect.material = post_mat
	comp_vp = SubViewport.new()
	comp_vp.size = Vector2i(640, 480)
	comp_vp.transparent_bg = false
	comp_vp.disable_3d = true
	comp_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	comp_vp.msaa_2d = Viewport.MSAA_DISABLED
	comp_vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	add_child(comp_vp)
	var cr := TextureRect.new()
	cr.size = Vector2(640, 480)
	cr.stretch_mode = TextureRect.STRETCH_SCALE
	cr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	cr.texture = world_vp.get_texture()
	cr.material = post_mat
	comp_vp.add_child(cr)
	hud_vp = $HudVP
	hud_vp.size = Vector2i(1280, 960)
	hud_vp.transparent_bg = true
	hud_vp.disable_3d = true
	hud_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	hud_vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	hud_rect = $HudRect
	hud_rect.visible = false
	hud = $HudVP/Hud
	hud.scale = Vector2(2, 2)
	hud.setup(load("res://art/font_6x9.png"), JSON.parse_string(FileAccess.get_file_as_string("res://art/font.json")), load("res://art/panel9.png"), load("res://art/logo_v3.png"))
	post_rect.visible = false

func _build_course() -> void:
	# Same continuous Touge course as Gordon's two-corner build (HP L then N90 R).
	var cfg: Dictionary = ArtKit.load_json("res://spec/race_config.json")
	var tr: Dictionary = TrackRoad.build_course(disp, cfg)
	course_full = tr.course
	course = tr.views[0]
	view = course
	S = float(course.S)
	R = float(course.R)
	A = float(course.A)
	E = float(course.E)

func _build_world() -> void:
	sky_root = $WorldVP/Sky
	sky_mat = sky_root.build()
	var track = $WorldVP/Track
	var dressing = $WorldVP/Dressing
	track.clear(); dressing.clear()
	art.reset_for_rebuild()
	var cr = track.build_strip(art, course_full, -80.0, course_full.length + 40.0, "touge", "CourseRoad")
	var dd = dressing.build(art, course_full, -80.0, course_full.length + 40.0, "touge", "CourseDressing")
	Dressing.stream(dd, 0.0)
	lamp_items = dd.items
	art.apply_fog("touge")
	sky_mat.set_shader_parameter("tex", art.tex("touge_sky"))
	sky_mat.set_shader_parameter("band_tex", art.tex("touge_ridge"))
	world_vp.world_3d.environment.background_color = fog
	chevrons = Chevrons.new()
	chevrons.name = "Chevrons"
	world_vp.add_child(chevrons)
	# Keep Gordon's touge road (no pack overlay, no extra pool decals) so the
	# asphalt stays dark navy grey like shots11, with grit in his sodium pools.

func _load_cars() -> void:
	player_car = $WorldVP/PlayerCar
	rival_car = $WorldVP/RivalCar
	var CS: Dictionary = disp.car_shading
	player_car.setup(art, CS)
	rival_car.setup(art, CS)
	for c in [player_car, rival_car]:
		for ch in c.get_children():
			if ch is MeshInstance3D and (ch as MeshInstance3D).material_override is ShaderMaterial:
				art.glow_mats.append((ch as MeshInstance3D).material_override)
	art.apply_fog("touge")

func _chase_pose(pp: Dictionary) -> Array:
	# B.5b fixed chase camera: offsets are not mirrored for left corners (display.json camera).
	var t := Vector3(pp.tx, 0, pp.tz)
	var p := Vector3(pp.x, 0, pp.z)
	var rt := Vector3(-pp.tz, 0, pp.tx)
	var cm: Dictionary = disp.camera
	return [
		p - t * float(cm.back) + rt * float(cm.side) + Vector3(0, float(cm.height), 0),
		p + t * float(cm.look_ahead) + rt * float(cm.look_side) + Vector3(0, float(cm.look_y), 0)
	]

func _stop_pose(stop: int) -> Array:
	# Same math as Gordon main.gd _stop_pose (select_cam apex / exit).
	var k: float = Track.inside_sign(DIR)
	var arc: float = R * A
	var q: Dictionary = disp.select_cam.apex if stop == 1 else disp.select_cam.exit
	var out_m: float = float(q.cam_out_m)
	var cp: Dictionary = course.point(S + arc * float(q.cam_arc), -k * out_m)
	var ts: float = S + arc * float(q.tgt_arc) if stop == 1 else S + arc + float(q.tgt_after_m)
	var tp: Dictionary = course.point(ts, k * float(q.tgt_in_m))
	return [Vector3(cp.x, float(q.cam_h), cp.z), Vector3(tp.x, float(q.tgt_y), tp.z), float(q.fov)]

func _place_camera(kind: String, player_s: float) -> void:
	if kind == "overview":
		# High and on the outside of the left hairpin so the whole hook reads.
		var ins := Track.inside_sign(DIR)
		var look_p: Dictionary = course.point(S + R * A * 0.40, ins * 1.5)
		var back: Dictionary = course.point(8.0, -ins * 12.0)
		cam.position = Vector3(back.x, 16.0, back.z)
		cam.look_at(Vector3(look_p.x, 0.0, look_p.z), Vector3.UP)
		cam.fov = 54.0
	elif kind == "chase":
		var pose: Array = _chase_pose(course.point(player_s, 0.0))
		cam.position = pose[0]
		cam.look_at(pose[1], Vector3.UP)
		cam.fov = float(disp.camera.fov)
	else:
		var stop := 1 if kind == "apex" else 2
		var pose2: Array = _stop_pose(stop)
		cam.position = pose2[0]
		cam.look_at(pose2[1], Vector3.UP)
		cam.fov = pose2[2]
	glow_cam.fov = cam.fov
	glow_cam.global_transform = cam.global_transform
	sky_root.position = cam.position

func _lane_d(lane: String) -> float:
	return Track.lane_offset(LANE_OF[lane], DIR, LANE_W)

func _end_d(_start_d: float, stance: String) -> float:
	# Austin pass 4: POW hugs the outer line, EN cuts hard to the inner line, HAN sits clearly mid-lane.
	# Full lane-width spacing so the three variants read apart side-by-side. Each segment still starts at the previous end.
	var ins := Track.inside_sign(DIR)
	if stance == "A":
		return -ins * LANE_W
	if stance == "S":
		return 0.0
	return ins * LANE_W

func _place_car(car: Node3D, s: float, d: float) -> Dictionary:
	var p: Dictionary = course.point(s, d)
	car.position = Vector3(p.x, 0, p.z)
	car.rotation.y = atan2(p.tx, p.tz)
	return p

func _lane_markers(player_s: float, turn_m: float) -> Dictionary:
	# Gordon main.gd: markers over the road ahead, 640-space unproject. Never a rival marker (B.4).
	var ahead: float = player_s + clampf(turn_m, 14.0, 40.0)
	var ln := {"A": "outside", "S": "center", "D": "inside"}
	var out := {}
	for k in ln:
		var q: Dictionary = course.point(ahead, Track.lane_offset(ln[k], DIR, LANE_W))
		var wp := Vector3(q.x, 0.05, q.z)
		out[k] = null if cam.is_position_behind(wp) else cam.unproject_position(wp)
	return out

func _apply_frame(fr: Dictionary, cam_kind: String) -> void:
	var player_s: float = CHASE_S if cam_kind != "overview" else OVERVIEW_S
	var entry_lane: String = fr.entry_lane
	var d_entry := _lane_d(entry_lane)
	var pp := _place_car(player_car, player_s, d_entry)
	# Apex / Exit stops show geometry only (B.5b / shots11 / hide_cars_at_stops).
	var cars_on: bool = (cam_kind == "overview" or cam_kind == "chase")
	player_car.visible = cars_on
	# Rival only at Entry, 9 m ahead; IN so it does not stack on an OUT player and matches shots11's left-side tell.
	rival_car.visible = cars_on and bool(fr.show_rival)
	if rival_car.visible:
		_place_car(rival_car, player_s + RIVAL_AHEAD, _lane_d("IN"))
	_place_camera(cam_kind, player_s)
	var t := Vector3(pp.tx, 0, pp.tz)
	var p := Vector3(pp.x, 0, pp.z)
	mirror_cam.position = p + Vector3(0, float(disp.mirror.cam_up), 0)
	mirror_cam.look_at(p - t * float(disp.mirror.look_back) + Vector3(0, float(disp.mirror.look_y), 0), Vector3.UP)
	# Mirror only on the chase camera (and the overview, so that sheet keeps a rear view).
	var mirror_on := cam_kind == "chase" or cam_kind == "overview"
	post_mat.set_shader_parameter("mirror_on", 1.0 if mirror_on else 0.0)
	_build_line(fr, d_entry, player_s)
	var left: float = 4.8
	var turn_m: float = left * SPEED_MS
	var lanes = _lane_markers(player_s, turn_m) if cam_kind == "chase" else null
	_show_hud(fr, lanes, turn_m, left, mirror_on)
	_set_cedars(cam_kind)

func _reset_cedars() -> void:
	for it in lamp_items:
		if _is_cedar(it.obj):
			it.obj.visible = true

func _set_cedars(cam_kind: String) -> void:
	_reset_cedars()
	if cam_kind == "overview":
		_thin_cedars_overview()
	else:
		# Gordon / build_lsc: drop cedars within 5.5 m of the camera so they do not sit in the lens.
		for it in lamp_items:
			if not _is_cedar(it.obj):
				continue
			var o: Node3D = it.obj
			var dx := o.position.x - cam.position.x
			var dz := o.position.z - cam.position.z
			o.visible = Vector2(dx, dz).length() >= 5.5

func _thin_cedars_overview() -> void:
	# Inside-of-corner cedars hide the line from the high camera; drop those, plus a keep-out around the lens.
	var ins := Track.inside_sign(DIR)
	var a0 := S - 8.0
	var a1 := S + R * A + 12.0
	for it in lamp_items:
		var o: Node3D = it.obj
		if not _is_cedar(o):
			continue
		var d: float = float(it.d)
		var s: float = float(it.base)
		if d * ins > 0.0:
			o.visible = false
			continue
		if s >= a0 and s <= a1 and absf(d) < 10.0:
			o.visible = false
			continue
		if Vector2(o.position.x, o.position.z).distance_to(Vector2(cam.position.x, cam.position.z)) < 16.0:
			o.visible = false
			continue
		# near-side (outside) trees on the entry that sit in this high shot
		if s < S + 16.0 and d * ins < 0.0 and absf(d) < 22.0:
			o.visible = false

func _is_cedar(o: Node3D) -> bool:
	if o.get_child_count() != 2:
		return false
	var a := o.get_child(0)
	var b := o.get_child(1)
	return a is MeshInstance3D and b is MeshInstance3D and absf((b as Node3D).rotation.y - PI / 2.0) < 0.1

func _build_line(fr: Dictionary, d_entry: float, player_s: float) -> void:
	# Always chain Entry -> Apex -> Exit (B.5d). Unchosen follow-on segments use the
	# canonical defaults (Apex EN, Exit POW) and draw dimmer / pending.
	var s_e0 := player_s + 3.0
	var s_e1 := S
	var s_a1 := S + R * A
	var s_x1 := S + R * A + minf(E, 24.0)
	var hover: int = int(fr.hover)
	var locked: bool = bool(fr.locked)
	var ap: String = String(fr.apex) if String(fr.apex) != "" else CANON_APEX
	var ex: String = String(fr.exit) if String(fr.exit) != "" else CANON_EXIT
	var apex_pending: bool = (not locked) and String(fr.apex) == "" and hover < 1
	var exit_pending: bool = (not locked) and String(fr.exit) == "" and hover < 2
	var d0 := d_entry
	var d1 := d_entry
	var d2 := _end_d(d1, ap)
	var d3 := _end_d(d2, ex)
	var segs: Array = []
	segs.append({"s0": s_e0, "s1": s_e1, "d0": d0, "d1": d1, "stance": fr.entry, "hovered": hover == 0, "pending": false})
	segs.append({"s0": s_e1, "s1": s_a1, "d0": d1, "d1": d2, "stance": ap, "hovered": hover == 1, "pending": apex_pending})
	segs.append({"s0": s_a1, "s1": s_x1, "d0": d2, "d1": d3, "stance": ex, "hovered": hover == 2, "pending": exit_pending})
	chevrons.build(course, segs, fog, float(disp.districts.touge.fog_near), float(disp.districts.touge.fog_far))

func _icon() -> Dictionary:
	var pts := []
	var arc: float = R * A
	var s0: float = S - 14.0
	var s1: float = S + arc + 14.0
	for i in 25:
		var q: Dictionary = course.point(lerpf(s0, s1, i / 24.0), 0.0)
		pts.append(Vector2(q.x, q.z))
	var st := []
	for sv in [S - 6.0, S + arc * 0.5, S + arc + 6.0]:
		var q2: Dictionary = course.point(sv, 0.0)
		st.append(Vector2(q2.x, q2.z))
	return {"pts": pts, "stops": st}

func _show_hud(fr: Dictionary, lanes, turn_m: float, left: float, mirror_on: bool = true) -> void:
	var hover: int = int(fr.hover)
	var phase: int = 3 if bool(fr.locked) else (2 if String(fr.exit) != "" or hover == 2 else (1 if String(fr.apex) != "" or hover == 1 else 0))
	if bool(fr.locked):
		phase = 3
	var sel := "A"
	if hover == 0: sel = String(fr.entry)
	elif hover == 1: sel = String(fr.apex)
	elif hover == 2: sel = String(fr.exit)
	var ORDER := ["A", "S", "D"]
	var sel_i := ORDER.find(sel)
	if sel_i < 0: sel_i = 0
	var entry_code: String = fr.entry if phase > 0 else ""
	var avail := {"A": 2, "S": 2, "D": 2}
	if phase > 0 and String(fr.entry) != "": avail[String(fr.entry)] -= 1
	if phase > 1 and String(fr.apex) != "": avail[String(fr.apex)] -= 1
	if phase > 2 and String(fr.exit) != "": avail[String(fr.exit)] -= 1
	var plate := {"name": "HAIRPIN L", "icon": _icon(), "mode": "LOCK" if bool(fr.locked) else "VIEW", "stop": 0 if bool(fr.locked) else int(fr.stop), "done": 3 if bool(fr.locked) else phase}
	var plan := {"phase": phase, "sel": sel_i, "avail": avail, "avail_entry": {"A": 2, "S": 2, "D": 2}, "entry": entry_code}
	var slots := [null, null, null]
	if phase > 0: slots[0] = fr.entry
	if phase > 1: slots[1] = fr.apex
	if phase > 2 or bool(fr.locked): slots[2] = fr.exit
	hud.show_state(_hud_state(fr, phase, sel_i, avail, entry_code, slots, plate, plan, lanes, turn_m, left, mirror_on))
	# Leave out Gordon's debug box (F9 dump / seed / rig).
	if hud.P.has("debug"):
		hud.P.debug.visible = false

func _hud_state(fr: Dictionary, phase: int, sel_i: int, avail: Dictionary, entry_code: String, slots: Array, plate: Dictionary, plan: Dictionary, lanes, turn_m: float, left: float, mirror_on: bool = true) -> Dictionary:
	return {
		"phase": "SELECT", "title": "CORNER 1/2 TOUGE HP (L)", "sub": "line preview", "build": "preview",
		"lead": 0.0, "gap": 0.0, "left": left, "total": 12.0,
		"slots": slots, "hand": ["A", "A", "S", "S", "D", "D"], "used": [],
		"qte": null, "line": "", "rline": "", "outs": [],
		"plate": plate, "locked_hold": false, "mirror": mirror_on, "play_phase": 0,
		"plan": plan, "turn_m": turn_m, "dir": DIR, "lanes": lanes,
		"result": {}, "reveal": 0, "cont_left": 8.0, "leader_changed": false,
		"winner": "", "cum_p": 0.0, "cum_o": 0.0, "last_corner": false, "fin": null,
		"resources": fr.get("resources", {})
	}

func _capture(path: String) -> void:
	await _settle(4)
	var native := comp_vp.get_texture().get_image()
	if native.get_format() != Image.FORMAT_RGBA8 and native.get_format() != Image.FORMAT_RGB8:
		native.convert(Image.FORMAT_RGBA8)
	native.resize(1280, 960, Image.INTERPOLATE_NEAREST)
	var hud_img := hud_vp.get_texture().get_image()
	if hud_img.get_format() != Image.FORMAT_RGBA8:
		hud_img.convert(Image.FORMAT_RGBA8)
	native.convert(Image.FORMAT_RGBA8)
	native.blend_rect(hud_img, Rect2i(0, 0, 1280, 960), Vector2i.ZERO)
	var out := Image.new()
	out.copy_from(native)
	out.convert(Image.FORMAT_RGB8)
	out.save_png(path)
	print("wrote ", path)
