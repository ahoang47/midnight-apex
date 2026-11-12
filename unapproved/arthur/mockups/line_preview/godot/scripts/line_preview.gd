## Unapproved B.5d line-preview mockup. Reuses Gordon's two-corner scenes (track, dressing, sky, cars, HUD)
## on a copy; does not edit his files. Renders 5 frames + leaves them for make_sheet.py.
extends Control
const ArtKit = preload("res://scripts/art_kit.gd")
const Course = preload("res://scripts/course.gd")
const TrackRoad = preload("res://scripts/track_road.gd")
const Track = preload("res://scripts/track.gd")
const Dressing = preload("res://scripts/touge_dressing.gd")
const POST_SH = preload("res://shaders/post.gdshader")
const Chevrons = preload("res://scripts/line_chevrons.gd")

const DIR := "R"
const CODE := "HP"
const LANE_W := 3.3
const STANCE_COL := {"A": "ATK", "D": "DEF", "S": "NEU"}
## Entry stays in the chosen lane; Apex/Exit end-offsets use the placeholder bend map.
const LANE_OF := {"OUT": "outside", "MID": "center", "IN": "inside"}

var disp: Dictionary
var art
var course
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

## Frames (brief): 1 Entry=OUT hover ATK; 2 Entry locked OUT/ATK, Apex hover DEF;
## 3 same, Apex hover ATK; 4 Entry IN/DEF, Apex NEU, Exit hover ATK; 5 all three locked.
const FRAMES := [
	{"file": "1_entry_out_atk.png", "entry_lane": "OUT", "entry": "A", "apex": "", "exit": "", "hover": 0, "locked": false, "show_rival": true, "stop": 0},
	{"file": "2_apex_def.png", "entry_lane": "OUT", "entry": "A", "apex": "D", "exit": "", "hover": 1, "locked": false, "show_rival": false, "stop": 1},
	{"file": "3_apex_atk.png", "entry_lane": "OUT", "entry": "A", "apex": "A", "exit": "", "hover": 1, "locked": false, "show_rival": false, "stop": 1},
	{"file": "4_exit_atk.png", "entry_lane": "IN", "entry": "D", "apex": "S", "exit": "A", "hover": 2, "locked": false, "show_rival": false, "stop": 2},
	{"file": "5_locked.png", "entry_lane": "IN", "entry": "D", "apex": "S", "exit": "A", "hover": -1, "locked": true, "show_rival": false, "stop": 0},
]

func _ready() -> void:
	out_dir = ProjectSettings.globalize_path("res://").path_join("..")
	disp = ArtKit.load_json("res://spec/display.json")
	# More lamps so the pack asphalt reads around the whole hairpin; no orange wash.
	disp.districts.touge.lamp_period_m = 22.0
	disp.districts.touge.outside_side = -1.0  # right hairpin: outside is -d
	disp.districts.touge.lamps = [[0, -1]]
	art = ArtKit.new(disp)
	fog = Color(disp.districts.touge.fog)
	_build_viewports()
	_build_course()
	_build_world()
	_load_cars()
	_place_overview_camera()
	await _settle(10)
	for fr in FRAMES:
		_apply_frame(fr)
		await _settle(8)
		await _capture(out_dir.path_join(fr.file))
	print("LINE_PREVIEW_OK ", out_dir)
	get_tree().quit(0)

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
	# 3D-only composite (for a clean B.5c capture: dither at 640, 2x, then sharp HUD)
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
	hud_rect.visible = false  # we composite HUD after the 2x upscale ourselves
	hud = $HudVP/Hud
	hud.scale = Vector2(2, 2)
	hud.setup(load("res://art/font_6x9.png"), JSON.parse_string(FileAccess.get_file_as_string("res://art/font.json")), load("res://art/panel9.png"), load("res://art/logo_v3.png"))
	# hide the 640 window chrome so xvfb is just a black clear; captures use the viewports
	post_rect.visible = false

func _build_course() -> void:
	S = float(disp.road.straight_m)
	R = float(disp.road.by_code[CODE].corner_radius_m)
	A = deg_to_rad(float(disp.road.by_code[CODE].corner_angle_deg))
	E = float(disp.road.exit_m)
	# Single right hairpin, same conventions as course.gd (forward -Z, d>0 = right of travel).
	course = Course.new(0.0, 0.0, 0.0, -1.0).add_straight(S).add_arc(R, A, -1.0).add_straight(E)
	view = Course.View.new(course, 0.0, S, R, A, E, -1.0)

func _build_world() -> void:
	sky_root = $WorldVP/Sky
	sky_mat = sky_root.build()
	var track = $WorldVP/Track
	var dressing = $WorldVP/Dressing
	track.clear(); dressing.clear()
	art.reset_for_rebuild()
	var cr = track.build_strip(art, course, -80.0, course.length + 40.0, "touge", "CourseRoad")
	var dd = dressing.build(art, course, -80.0, course.length + 40.0, "touge", "CourseDressing")
	Dressing.stream(dd, 0.0)
	lamp_items = dd.items
	_apply_pack_road(cr)
	_add_pools()
	art.apply_fog("touge")
	sky_mat.set_shader_parameter("tex", art.tex("touge_sky"))
	sky_mat.set_shader_parameter("band_tex", art.tex("touge_ridge"))
	world_vp.world_3d.environment.background_color = fog
	chevrons = Chevrons.new()
	chevrons.name = "Chevrons"
	world_vp.add_child(chevrons)

func _apply_pack_road(mi: MeshInstance3D) -> void:
	var m: ShaderMaterial = mi.material_override
	var t: Texture2D = load("res://art/road_3lane.png")
	m.set_shader_parameter("tex", t)
	m.set_shader_parameter("tile", 13.333)  # pack 3-lane tile, metres along
	m.set_shader_parameter("gain", 1.38)    # slightly brighter base so grit reads off-pool; no orange
	m.set_shader_parameter("scroll_m", 0.0)

func _add_pools() -> void:
	# Soft sodium pools under each lamp so the pack asphalt lights up in steps, still pale #F0C894.
	if not ResourceLoader.exists("res://art/pool_blend50_0.png"):
		return
	var seen := {}
	for it in lamp_items:
		var s: float = float(it.base)
		var key := snappedf(s, 1.0)
		if seen.has(key):
			continue
		seen[key] = true
		var mid: Dictionary = course.point(s, 0.0)
		var p := Vector3(mid.x, 0.03, mid.z)
		var dec: MeshInstance3D = art.decal("pool_blend50_0", 13.0, 13.0, 0.0, true, 0.09 * 1.8 * 1.15)
		dec.position = p
		# rotate the plane to sit in XZ (PlaneMesh is Y-up already)
		world_vp.add_child(dec)

func _load_cars() -> void:
	player_car = $WorldVP/PlayerCar
	rival_car = $WorldVP/RivalCar
	var CS: Dictionary = disp.car_shading
	player_car.setup(art, CS)
	rival_car.setup(art, CS)
	# car glow sprites need district fog
	for c in [player_car, rival_car]:
		for ch in c.get_children():
			if ch is MeshInstance3D and (ch as MeshInstance3D).material_override is ShaderMaterial:
				art.glow_mats.append((ch as MeshInstance3D).material_override)
	art.apply_fog("touge")

func _place_overview_camera() -> void:
	# High enough above and behind the car to see the whole right hairpin line, with the car still in frame.
	var look_p: Dictionary = course.point(S + R * A * 0.40, 1.5)
	var back: Dictionary = course.point(8.0, -12.0)
	var cam_pos := Vector3(back.x, 16.0, back.z)
	var look := Vector3(look_p.x, 0.0, look_p.z)
	cam.position = cam_pos
	cam.look_at(look, Vector3.UP)
	cam.fov = 54.0
	glow_cam.fov = cam.fov
	glow_cam.global_transform = cam.global_transform
	sky_root.position = cam.position

func _lane_d(lane: String) -> float:
	return Track.lane_offset(LANE_OF[lane], DIR, LANE_W)

func _end_d(start_d: float, stance: String) -> float:
	# Placeholder bends (B.5d): ATK cuts toward the inside by 2/3 of a lane, DEF holds the outside, NEU mid-lane.
	var ins := Track.inside_sign(DIR)  # +1 for R
	var outside := -ins * LANE_W
	if stance == "D":
		return outside
	if stance == "S":
		return 0.0
	# ATK: cut 2/3 lane toward the inside from where this segment starts, stay on the road
	var cut := start_d + ins * (LANE_W * 2.0 / 3.0)
	return clampf(cut, -LANE_W * 1.35, LANE_W * 1.35)

func _place_car(car: Node3D, s: float, d: float) -> Dictionary:
	var p: Dictionary = course.point(s, d)
	car.position = Vector3(p.x, 0, p.z)
	car.rotation.y = atan2(p.tx, p.tz)
	return p

func _apply_frame(fr: Dictionary) -> void:
	var entry_lane: String = fr.entry_lane
	var d_entry := _lane_d(entry_lane)
	var pp := _place_car(player_car, 24.0, d_entry)
	player_car.visible = true
	rival_car.visible = bool(fr.show_rival)
	if rival_car.visible:
		_place_car(rival_car, 34.0, _lane_d("OUT"))
	# Mirror: car's rear-view, looking back down the approach (not a blank box).
	var t := Vector3(pp.tx, 0, pp.tz)
	var p := Vector3(pp.x, 0, pp.z)
	mirror_cam.position = p + Vector3(0, float(disp.mirror.cam_up), 0)
	mirror_cam.look_at(p - t * float(disp.mirror.look_back) + Vector3(0, float(disp.mirror.look_y), 0), Vector3.UP)
	post_mat.set_shader_parameter("mirror_on", 1.0)
	glow_cam.global_transform = cam.global_transform
	sky_root.position = cam.position
	_build_line(fr, d_entry)
	_show_hud(fr)
	_thin_cedars()

func _thin_cedars() -> void:
	# Inside-of-corner cedars were sitting on the hairpin and hiding the line; drop those, and any cedar close to the carriageway around the arc.
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
		# keep a keep-out around the camera, and drop the near-side trees that sit on the entry in this shot
		if Vector2(o.position.x, o.position.z).distance_to(Vector2(cam.position.x, cam.position.z)) < 16.0:
			o.visible = false
			continue
		if s < S + 16.0 and d < 0.0 and absf(d) < 22.0:
			o.visible = false

func _is_cedar(o: Node3D) -> bool:
	if o.get_child_count() != 2:
		return false
	var a := o.get_child(0)
	var b := o.get_child(1)
	return a is MeshInstance3D and b is MeshInstance3D and absf((b as Node3D).rotation.y - PI / 2.0) < 0.1

func _build_line(fr: Dictionary, d_entry: float) -> void:
	var s_e0 := 27.0
	var s_e1 := S            # Entry ends at turn-in
	var s_a1 := S + R * A    # Apex ends at exit-of-arc
	var s_x1 := S + R * A + minf(E, 24.0)
	var segs: Array = []
	# Entry: starts (and stays) in the chosen Entry lane. Colour = Entry stance.
	var d0 := d_entry
	var d1 := d_entry
	segs.append({"s0": s_e0, "s1": s_e1, "d0": d0, "d1": d1, "stance": fr.entry, "hovered": int(fr.hover) == 0})
	# Apex / Exit only once that phase is in play (hovered or confirmed)
	if String(fr.apex) != "" or int(fr.hover) >= 1:
		var ap: String = fr.apex if String(fr.apex) != "" else "A"
		var d2 := _end_d(d1, ap)
		segs.append({"s0": s_e1, "s1": s_a1, "d0": d1, "d1": d2, "stance": ap, "hovered": int(fr.hover) == 1})
		d1 = d2
	if String(fr.exit) != "" or int(fr.hover) >= 2:
		var ex: String = fr.exit if String(fr.exit) != "" else "A"
		var d3 := _end_d(d1, ex)
		segs.append({"s0": s_a1, "s1": s_x1, "d0": d1, "d1": d3, "stance": ex, "hovered": int(fr.hover) == 2})
	# Frame 1 only draws Entry (hover is 0, apex/exit empty) — good.
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

func _show_hud(fr: Dictionary) -> void:
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
	var plate := {"name": "HAIRPIN R", "icon": _icon(), "mode": "LOCK" if bool(fr.locked) else "VIEW", "stop": 0 if bool(fr.locked) else int(fr.stop), "done": 3 if bool(fr.locked) else phase}
	var plan := {"phase": phase, "sel": sel_i, "avail": avail, "avail_entry": {"A": 2, "S": 2, "D": 2}, "entry": entry_code}
	var slots := [null, null, null]
	if phase > 0: slots[0] = fr.entry
	if phase > 1: slots[1] = fr.apex
	if phase > 2 or bool(fr.locked): slots[2] = fr.exit
	hud.show_state(_hud_state(fr, phase, sel_i, avail, entry_code, slots, plate, plan))
	if hud.P.has("debug"):
		hud.P.debug.visible = false

func _hud_state(fr: Dictionary, phase: int, sel_i: int, avail: Dictionary, entry_code: String, slots: Array, plate: Dictionary, plan: Dictionary) -> Dictionary:
	return {
		"phase": "SELECT", "title": "CORNER 1/2 TOUGE HP (R)", "sub": "line preview", "build": "preview",
		"lead": -0.05, "gap": -0.05, "left": 4.8, "total": 12.0,
		"slots": slots, "hand": ["A", "A", "S", "S", "D", "D"], "used": [],
		"qte": null, "line": "", "rline": "", "outs": [],
		"plate": plate, "locked_hold": false, "mirror": true, "play_phase": 0,
		"plan": plan, "turn_m": 60.0, "dir": DIR, "lanes": null,
		"result": {}, "reveal": 0, "cont_left": 8.0, "leader_changed": false,
		"winner": "", "cum_p": 0.0, "cum_o": 0.0, "last_corner": false, "fin": null
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
	# HUD is already 1280x960 (drawn at scale 2). Composite sharp on top of the upscaled 3D.
	native.convert(Image.FORMAT_RGBA8)
	native.blend_rect(hud_img, Rect2i(0, 0, 1280, 960), Vector2i.ZERO)
	var out := Image.new()
	out.copy_from(native)
	out.convert(Image.FORMAT_RGB8)
	out.save_png(path)
	print("wrote ", path)
