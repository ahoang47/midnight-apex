## CEL-SHADED EXPERIMENT (unapproved, Austin 2026-11-14: "As an experiment, could you do a pass as a cel-shaded style?").
## Copy of the district-looks script: same camera, cars, road, dressing and HUD; the cel look lives in the shaders
## (toon ramp + flatten in scroll/env/car, ink in post) and in _capture (G-buffer passes, two flavours).
## Unapproved district-looks mockup (Austin 2026-11-13: "the road reads really wide ... draft the looks for all 3
## districts"). Same E3B HUD (resource_meters/godot: hud.gd + resource_stack.gd, unchanged) and the same Entry chase
## frame, over one district scene per run: DISTRICT=touge|street|wangan. Road width + dressing per district:
##   touge  : 6.0 m two-lane pass, no painted lines, close guardrail on the drop, cut slope + cedars inside.
##   street : 8.4 m two-lane city street with Gordon's lined street road, shops, poles, wires, vending machines.
##   wangan : the E3B road as is (11.9 m, 3 lanes) with its lane lines back, jersey barriers, tall sodium lamps,
##            distant city towers.
## Props are glTF from ../blender/build_assets.py (unlit in Godot via Gordon's scroll shader). Does not edit Gordon's files.
extends Control
const ArtKit = preload("res://scripts/art_kit.gd")
const TrackRoad = preload("res://scripts/track_road.gd")
const Track = preload("res://scripts/track.gd")
const POST_SH = preload("res://shaders/post.gdshader")
const SCROLL_SH = preload("res://shaders/scroll.gdshader")
const Chevrons = preload("res://scripts/district_chevrons.gd")

const DIR := "L"
const STANCE_COL := {"A": "POW", "D": "EN", "S": "HAN"}
const LANE_OF := {"OUT": "outside", "MID": "center", "IN": "inside"}
const SPEED_MS := 25.0
const RIVAL_AHEAD := 9.0
const OVERVIEW_S := 24.0
const CHASE_S := 8.0
const CANON_APEX := "D"
const CANON_EXIT := "A"

## Per-district look. road_half = half the asphalt width (m). lane = OUT/IN offset from centre for cars + chevrons.
const DISTRICTS := {
	"touge": {"road_half": 3.0, "lane": 1.45, "chev": 0.58, "road_tex": "touge_road", "road_tile": 48.0, "road_scroll": 32.0,
		"fog": "#0B172B", "fog_near": 9.0, "fog_far": 78.0, "sky": "touge", "band": "touge_ridge", "prop_gain": 1.0},
	"street": {"road_half": 4.2, "lane": 2.0, "chev": 0.78, "road_tex": "street_road", "road_tile": 24.0,
		"fog": "#0B172B", "fog_near": 14.0, "fog_far": 105.0, "sky": "street", "band": "street_skyline", "prop_gain": 1.0},
	"wangan": {"road_half": 5.95, "lane": 3.3, "chev": 1.0, "road_tex": "wangan_road", "road_tile": 48.0,
		"fog": "#0B172B", "fog_near": 22.0, "fog_far": 360.0, "sky": "street", "band": "street_skyline", "prop_gain": 1.0},
}

var DK := "touge"
var DC: Dictionary
var LANE_W := 3.3
var disp: Dictionary
var art
var course
var course_full
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
var env_root: Node3D
var prop_cache := {}
var tris := 0
var cam_pull := false

func _fr(file: String, load: Dictionary, extra: Dictionary = {}) -> Dictionary:
	# E3B full frame exactly as e3b_full.png: Entry select, OUT/POW hovered, mixed mid loads under LIMIT.
	# rival_ds / rival_lane: rival placement relative to the player. lead / gap_s feed the (prominent) tie-gap box.
	var res := {"variant": "E3B", "fuel": 8, "brakes": 8, "susp": 8, "pips": 8, "load": load}
	var fr := {"file": file, "entry_lane": "OUT", "entry": "A", "apex": "", "exit": "",
		"hover": 0, "locked": false, "show_rival": true, "stop": 0, "cam": "chase", "resources": res,
		"rival_ds": RIVAL_AHEAD, "rival_lane": "IN", "lead": 0.0, "gap_s": 0.0, "role": "std"}
	for k in extra: fr[k] = extra[k]
	return fr

## Cat and mouse (touge, presentation only, scoring unchanged): no passes, so half the race leads, half follows.
func _frames() -> Array:
	var L := {"fuel": 0.42, "brakes": 0.58, "susp": 0.30}
	var out := [_fr("%s.png" % DK, L)]
	if OS.get_environment("CEL_ALL") == "":
		return out   # cel experiment: the three standard district frames only (CEL_ALL=1 for the cat/mouse set)
	if DK == "touge":
		# CAT: rival ahead in the player's own line, taillights sitting in the chevrons. Standard camera.
		out.append(_fr("touge_cat.png", L, {"rival_ds": 11.0, "rival_lane": "OUT", "rival_d_nudge": -0.25, "lead": -0.12, "gap_s": 0.44, "role": "cat"}))
		# MOUSE: rival 6.5 m behind, slightly inside so its lamps clear the player's tail. Headlights light the road + the player.
		out.append(_fr("touge_mouse.png", L, {"rival_ds": -6.5, "rival_lane": "OUT", "rival_d_nudge": -0.9, "lead": 0.10, "gap_s": 0.26, "role": "mouse"}))
		out.append(_fr("touge_mouse_far.png", L, {"rival_ds": -24.0, "rival_lane": "OUT", "rival_d_nudge": -0.6, "lead": 0.36, "gap_s": 0.96, "role": "mouse"}))
		# Mouse-view options (Austin 2026-11-13: the far mouse cam "would make it hard to read the opponent").
		# A bigmirror / B lookback / C highcam, each at a medium (10 m) and far (24 m) gap.
		for g in [["", -10.0, 0.40, 0.11], ["_far", -24.0, 0.96, 0.36]]:
			var base := {"rival_ds": g[1], "rival_lane": "OUT", "rival_d_nudge": -0.9, "lead": g[3], "gap_s": g[2], "role": "mouse"}
			var a := base.duplicate(); a["mode"] = "bigmirror"
			a["hud"] = {"inset": {"rect": [128, 6, 384, 128], "label": "REAR VIEW"}, "gap_box": {"x": 522.0, "y": 8.0, "w": 110.0, "compact": true}, "sign_y": 152.0}
			out.append(_fr("mouse_bigmirror%s.png" % g[0], L, a))
			var b := base.duplicate(); b["mode"] = "lookback"
			b["hud"] = {"inset": {"rect": [200, 6, 240, 112], "label": "AHEAD"}, "gap_box": {"x": 222.0, "y": 132.0, "w": 196.0}, "sign_cx": 482.0, "sign_y": 20.0}
			out.append(_fr("mouse_lookback%s.png" % g[0], L, b))
			var c := base.duplicate(); c["mode"] = "highcam"
			out.append(_fr("mouse_highcam%s.png" % g[0], L, c))
		# B revised (Austin 2026-11-13): head-on look-back. Centred reverse cam, rival dead-centre in the lane.
		# "The rear view will always stay a rear view": the E3B mirror is untouched. Standard sign + gap box.
		for g in [["", -10.0, 0.40, 0.11], ["_far", -24.0, 0.96, 0.36]]:
			out.append(_fr("mouse_lookback_headon%s.png" % g[0], L, {"rival_ds": g[1], "rival_lane": "OUT", "rival_d_nudge": 0.0, "lead": g[3], "gap_s": g[2], "role": "mouse", "mode": "headon"}))
		if OS.get_environment("MOUSE_CAM_TEST") != "":
			out.append(_fr("touge_mouse_pulled.png", L, {"rival_ds": -6.5, "rival_lane": "OUT", "rival_d_nudge": -0.9, "lead": 0.10, "gap_s": 0.26, "role": "mouse", "cam_pull": true}))
	return out

func _ready() -> void:
	DK = OS.get_environment("DISTRICT") if OS.get_environment("DISTRICT") != "" else "touge"
	DC = DISTRICTS[DK]
	LANE_W = float(DC.lane)
	fog = Color(DC.fog)
	out_dir = ProjectSettings.globalize_path("res://").path_join("..")
	disp = ArtKit.load_json("res://spec/display.json")
	art = ArtKit.new(disp)
	art.road_W = float(DC.road_half)
	art.DIST[DK] = {"fog": DC.fog, "fog_near": DC.fog_near, "fog_far": DC.fog_far, "lamp_period_m": DC.road_tile}
	_build_viewports()
	_build_course()
	_build_world()
	_load_cars()
	var only := OS.get_environment("FRAME")
	for fr in _frames():
		if only != "" and String(fr.file) != only: continue
		_apply_frame(fr, "chase")
		await _settle(8)
		await _capture(out_dir.path_join(fr.file))
	print("DISTRICT_OK ", DK, " env_tris ", tris)
	get_tree().quit(0)

# ---------------------------------------------------------------------------------------------------
# Touge grade (Austin 2026-11-13: "give the touge road a real grade"). Climb at 8.5 % up the approach, easing
# over a crest through the hairpin (grade 0 at ~75 % of the arc), then falling at 5 % out of it. The hairpin banks
# up to 6 % (outside high). Street / Wangan stay flat. Everything (road, verges, props, cars, chevrons, cameras)
# reads its height from elev(s, d).
var _elev_tab := PackedFloat32Array()
const ELEV_S0 := -120.0
const ELEV_STEP := 0.5

func grade_at(s: float) -> float:
	var crest: float = S + R * A * 0.75
	if s < 28.0: return 0.085
	if s < crest: return lerpf(0.085, 0.0, Track.smooth((s - 28.0) / (crest - 28.0)))
	return lerpf(0.0, -0.05, Track.smooth((s - crest) / 30.0))

func _build_elev() -> void:
	_elev_tab.resize(int((S1 + 140.0 - ELEV_S0) / ELEV_STEP) + 2)
	var y := 0.0
	var y0 := 0.0
	for i in _elev_tab.size():
		var s := ELEV_S0 + i * ELEV_STEP
		if i > 0: y += grade_at(s - ELEV_STEP * 0.5) * ELEV_STEP
		_elev_tab[i] = y
		if absf(s) < 0.01: y0 = y
	for i in _elev_tab.size(): _elev_tab[i] -= y0   # s = 0 at y = 0

func bank_at(s: float) -> float:
	var a0: float = S; var a1: float = S + R * A
	var k := Track.smooth((s - (a0 - 10.0)) / 18.0) * (1.0 - Track.smooth((s - (a1 - 8.0)) / 18.0))
	return 0.06 * k

func elev(s: float, d: float) -> float:
	if DK != "touge" or _elev_tab.is_empty(): return 0.0
	var f := (s - ELEV_S0) / ELEV_STEP
	var i := clampi(int(floor(f)), 0, _elev_tab.size() - 2)
	var base := lerpf(_elev_tab[i], _elev_tab[i + 1], clampf(f - i, 0.0, 1.0))
	return base + bank_at(s) * d * -Track.inside_sign(DIR)

func _build_course() -> void:
	var cfg: Dictionary = ArtKit.load_json("res://spec/race_config.json")
	var tr: Dictionary = TrackRoad.build_course(disp, cfg)
	course_full = tr.course
	course = tr.views[0]
	view = course
	S = float(course.S); R = float(course.R); A = float(course.A); E = float(course.E)
	if DK == "touge": _build_elev()

func _load_cars() -> void:
	player_car = $WorldVP/PlayerCar
	rival_car = $WorldVP/RivalCar
	var CS: Dictionary = disp.car_shading
	player_car.setup(art, CS)
	rival_car.setup(art, CS)
	art.apply_fog(DK)

# ---------------------------------------------------------------------------------------------------
# World: road + district dressing (static, scroll 0). s range covers the mirror view behind and the hairpin ahead.
const S0 := -70.0
const S1 := 150.0

func _build_world() -> void:
	sky_root = $WorldVP/Sky
	sky_mat = sky_root.build()
	sky_mat.set_shader_parameter("tex", load("res://art/%s_sky.png" % DC.sky))
	sky_mat.set_shader_parameter("band_tex", load("res://art/%s.png" % DC.band))
	world_vp.world_3d.environment.background_color = fog
	env_root = Node3D.new(); env_root.name = "District_" + DK
	world_vp.add_child(env_root)
	var W: float = art.road_W
	# Finer grid than Gordon's strip (1 m x 1 m instead of 3 m x 2 m) so affine warping does not wobble the
	# painted lines near the camera (Austin: lane lines "get wobbly when close to camera").
	var rm: ShaderMaterial = art.strip_mat(String(DC.road_tex), float(DC.road_tile))
	rm.set_shader_parameter("scroll_m", float(DC.get("road_scroll", 0.0)))
	rm.set_shader_parameter("flat_radius", 6.0)   # cel: asphalt grain wants a wider flatten than props
	var road := grid_strip(S0, S1, -W, W, rm, 1.0, 1.0)
	road.name = "Road"
	match DK:
		"touge": _dress_touge(W)
		"street": _dress_street(W)
		"wangan": _dress_wangan(W)
	art.apply_fog(DK)
	chevrons = Chevrons.new()
	chevrons.name = "Chevrons"
	chevrons.width_k = float(DC.chev)
	chevrons.spacing_k = lerpf(1.0, float(DC.chev), 0.5)
	if DK == "touge": chevrons.elev_fn = elev
	world_vp.add_child(chevrons)

func grid_strip(s0: float, s1: float, d0: float, d1: float, mat: ShaderMaterial, col_m: float, row_m: float) -> MeshInstance3D:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var nc: int = maxi(1, ceili(absf(d1 - d0) / col_m))
	var rows: Array = []
	var s := s0
	while s <= s1 + 1e-6:
		var row: Array = []
		for j in nc + 1:
			var u := float(j) / nc
			var dd := d0 + (d1 - d0) * u
			row.append([ArtKit.pp(course_full, s, dd, elev(s, dd)), Vector2(u, s)])
		rows.append(row); s += row_m
	for i in range(1, rows.size()):
		for j in nc:
			for v in [rows[i - 1][j], rows[i][j], rows[i - 1][j + 1], rows[i - 1][j + 1], rows[i][j], rows[i][j + 1]]:
				st.set_uv(v[1]); st.add_vertex(v[0])
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat; mi.extra_cull_margin = 16384.0
	env_root.add_child(mi); tris += _mesh_tris(mi.mesh)
	return mi

func _mesh_tris(m: Mesh) -> int:
	var n := 0
	if m == null: return 0
	for i in m.get_surface_count():
		var a := m.surface_get_arrays(i)
		var idx = a[Mesh.ARRAY_INDEX]
		n += (idx.size() if idx != null else (a[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()) / 3
	return n

## band strip: along s, from (d0, y0) to (d1, y1) across; UV.x 0..1 across, UV.y = metres along / tile
func band(s0: float, s1: float, d0: float, y0: float, d1: float, y1: float, mat: ShaderMaterial, step := 2.0) -> MeshInstance3D:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var s := s0
	var prev := []
	while s <= s1 + 1e-6:
		var a: Vector3 = ArtKit.pp(course_full, s, d0, y0 + elev(s, d0))
		var b: Vector3 = ArtKit.pp(course_full, s, d1, y1 + elev(s, d1))
		var row := [[a, Vector2(0, s)], [b, Vector2(1, s)]]
		if not prev.is_empty():
			for v in [prev[0], row[0], prev[1], prev[1], row[0], row[1]]:
				st.set_uv(v[1]); st.add_vertex(v[0])
		prev = row; s += step
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat; mi.extra_cull_margin = 16384.0
	env_root.add_child(mi); tris += _mesh_tris(mi.mesh)
	return mi

func tex_mat(n: String, tile: float, gain := 1.0) -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = SCROLL_SH
	m.set_shader_parameter("tex", load("res://art/env/%s.png" % n)); m.set_shader_parameter("tile", tile)
	m.set_shader_parameter("gain", gain)
	return art.fogify(m)

## glTF prop from assets/env, re-shaded unlit (Gordon's scroll shader, static UVs). Emit_* surfaces full-bright.
func prop(n: String, s: float, d: float, y := 0.0, yaw := 0.0, gain := 1.0, emit_gain := 1.0) -> Node3D:
	if not prop_cache.has(n): prop_cache[n] = load("res://assets/env/%s.glb" % n)
	var inst: Node3D = prop_cache[n].instantiate()
	_shade(inst, gain, emit_gain)
	var q: Dictionary = course_full.point(s, d)
	inst.position = Vector3(q.x, y + elev(s, d), q.z)
	# local +X = away from the road: left side as built, right side turned round. Pitched to the grade.
	var gr := atan((elev(s + 1.0, d) - elev(s - 1.0, d)) * 0.5)
	inst.rotation = Vector3(-gr * (-1.0 if d > 0.0 else 1.0), atan2(q.tx, q.tz) + (PI if d > 0.0 else 0.0) + yaw, 0.0)
	env_root.add_child(inst)
	return inst

func _shade(n: Node, gain: float, emit_gain: float) -> void:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		tris += _mesh_tris(mi.mesh)
		for si in mi.mesh.get_surface_count():
			var src := mi.get_active_material(si)
			var nm: String = src.resource_name if src != null else ""
			var key := "%s|%.2f|%.2f" % [nm, gain, emit_gain]
			var m: ShaderMaterial
			if prop_cache.has(key):
				m = prop_cache[key]
			else:
				m = ShaderMaterial.new(); m.shader = SCROLL_SH
				m.set_shader_parameter("tex", (src as BaseMaterial3D).albedo_texture if src is BaseMaterial3D else null)
				m.set_shader_parameter("tile", 1.0); m.set_shader_parameter("scroll_m", 0.0)
				m.set_shader_parameter("gain", emit_gain if nm.begins_with("Emit_") else gain)
				if nm.begins_with("Emit_"):
					m.set_shader_parameter("cel_k", 0.0); m.set_shader_parameter("flatten", 0.0)   # lit signs / windows / lamp heads stay full-bright and as painted
				art.fogify(m); prop_cache[key] = m
			mi.set_surface_override_material(si, m)
		mi.extra_cull_margin = 16384.0
	for ch in n.get_children(): _shade(ch, gain, emit_gain)

func lamp_glow(parent: Node3D, local: Vector3, size := 1.5, strength := 0.9) -> void:
	var gl: MeshInstance3D = art.glow_sprite("glow_lamp", Color(1, 1, 1), size, strength)
	gl.position = local; parent.add_child(gl)

func cedar(s: float, d: float, y: float, h: float, k: int) -> void:
	var c: Node3D = art.cross_card("touge_cedar_a" if ArtKit.hash01(k * 1.7) < 0.5 else "touge_cedar_b", h * 0.3333, h)
	var q: Dictionary = course_full.point(s, d)
	c.position = Vector3(q.x, y + elev(s, d), q.z); c.rotation.y = atan2(q.tx, q.tz) + ArtKit.hash01(k * 3.1) * 0.6
	env_root.add_child(c); tris += 4

## Gordon's touge lamp (post + arm + #F0C894 head) with its glow, on side sd (+1 right / -1 left)
func gordon_lamp(s: float, d: float, sd: float) -> void:
	var lamp := Node3D.new()
	var post := MeshInstance3D.new(); post.mesh = art.lamp_mesh(); post.material_override = art.env_mat; post.extra_cull_margin = 16384.0; lamp.add_child(post)
	lamp_glow(lamp, Vector3(-1.3, 6.3, 0))
	lamp.scale.x = sd
	var q: Dictionary = course_full.point(s, d)
	lamp.position = Vector3(q.x, elev(s, d), q.z); lamp.rotation.y = atan2(q.tx, q.tz)
	env_root.add_child(lamp); tris += 6

# --- TOUGE: 6 m pass. Right = corner outside = drop side; left = inside = cut slope ---------------
func _dress_touge(W: float) -> void:
	var grav := tex_mat("touge_gravel", 4.0)
	var verge: ShaderMaterial = art.strip_mat("touge_verge", 6.0)
	# inside (left): 0.7 m gravel shoulder, then the cut slope modules (Blender) + cedars on top
	band(S0, S1, -W, 0.0, -(W + 0.7), 0.02, grav)
	var k := 0
	var s := S0
	while s < S1:
		prop("touge_cutslope_a" if k % 2 == 0 else "touge_cutslope_b", s, -(W + 0.7), 0.0, 0.0, 0.8)
		s += 4.6; k += 1
	# fill behind the slope tops so the inside of the hairpin reads as a hill, not a void
	band(S0, S1, -(W + 8.5), 8.1, -(W + 16.0), 9.5, verge)
	k = 0; s = S0
	while s < S1:
		var h := lerpf(10.0, 15.0, ArtKit.hash01(k * 2.3))
		cedar(s + ArtKit.hash01(k) * 3.0, -(W + 7.5 + ArtKit.hash01(k * 5.1) * 6.0), 7.6, h, k)
		s += 5.0; k += 1
	# outside (right): 0.5 m grass verge, guardrail right at the edge, then the drop (slope down + cedar tops below)
	band(S0, S1, W, 0.0, W + 0.55, 0.0, verge)
	s = S0
	while s < S1:
		prop("touge_guardrail", s, W + 0.45, 0.0, 0.0)
		s += 4.0
	band(S0, S1, W + 0.55, 0.0, W + 9.0, -7.5, verge)
	k = 0; s = S0
	while s < S1:
		var h2 := lerpf(11.0, 16.0, ArtKit.hash01(k * 4.7 + 1.0))
		cedar(s + ArtKit.hash01(k * 2.0) * 4.0, W + 5.0 + ArtKit.hash01(k * 7.3) * 14.0, -h2 * 0.55 - 2.0, h2, k + 300)
		s += 3.6; k += 1
	# sparse sodium lamps on the outside, one every 48 m at s = 16 + 48k (road scroll 32 moves the painted pools there)
	s = -80.0
	while s < S1:
		if s > S0: gordon_lamp(s, W + 0.75, 1.0)
		s += 48.0

# --- STREET: 8.4 m two-lane street, sidewalks, shops, poles + wires, vending machines -------------
func _dress_street(W: float) -> void:
	var SW := 2.6
	var curb := tex_mat("street_curb", 1.0)
	var pave := tex_mat("street_paving", 2.0)
	for sd in [-1.0, 1.0]:
		band(S0, S1, sd * W, 0.0, sd * W, 0.15, curb)
		band(S0, S1, sd * W, 0.15, sd * (W + SW), 0.15, pave)
	# shopfront rows (Blender kit) set back behind the sidewalk
	var widths := [7.0, 6.0, 7.5, 6.5]
	for sd in [-1.0, 1.0]:
		var s := S0 + (0.0 if sd < 0 else 3.0)
		var k := 0 if sd < 0 else 2
		while s < S1 - 30.0:  # past the fog the rows are invisible; keeps the scene near the ~12k guide
			var i: int = k % 4
			var w: float = widths[i]
			prop("street_shop_%d" % i, s + w * 0.5, sd * (W + SW), 0.15, 0.0, 0.55, 0.6)
			if ArtKit.hash01(k * 3.3 + sd) < 0.45:
				prop("street_vending", s + w - 1.0, sd * (W + SW - 0.8), 0.15, 0.0, 0.7, 0.5)
			s += w + 0.4; k += 1
	# utility poles at the curb, lamps over the pools painted in Gordon's street road (left s%24==0, right s%24==12)
	var poles := {-1.0: [], 1.0: []}
	for sd in [-1.0, 1.0]:
		var s2 := (0.0 if sd < 0 else 12.0) - 72.0
		while s2 < S1:
			if s2 > S0:
				var p := prop("street_pole", s2, sd * (W + 0.35), 0.15)
				lamp_glow(p, Vector3(-1.35, 5.2, 0), 1.3, 0.8)
				poles[sd].append(s2)
			s2 += 24.0
	# overhead wires: 3 per side between poles + a crossing pair every other span
	var wire := tex_mat("street_metal", 1.0, 0.55)
	for sd in [-1.0, 1.0]:
		var arr: Array = poles[sd]
		for i in arr.size() - 1:
			for off in [[-0.8, 9.2], [0.8, 9.2], [0.0, 8.6]]:
				_wire(arr[i], sd * (W + 0.35) + float(off[0]), off[1], arr[i + 1], sd * (W + 0.35) + float(off[0]), off[1], wire)
	for i in range(0, (poles[-1.0] as Array).size(), 2):
		var sa: float = poles[-1.0][i]
		_wire(sa, -(W + 0.35), 9.2, sa + 12.0, W + 0.35, 9.2, wire)

func _wire(sa: float, da: float, ya: float, sb: float, db: float, yb: float, mat: ShaderMaterial) -> void:
	# sagging catenary as thin camera-agnostic ribbons (two crossed quads), 8 segments
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 8
	var pts := []
	for i in n + 1:
		var t := float(i) / n
		var p: Vector3 = ArtKit.pp(course_full, lerpf(sa, sb, t), lerpf(da, db, t), lerpf(ya, yb, t) - 0.55 * 4.0 * t * (1.0 - t))
		pts.append(p)
	for i in n:
		var a: Vector3 = pts[i]; var b: Vector3 = pts[i + 1]
		for off in [Vector3(0, 0.035, 0), Vector3(0.035, 0, 0.035)]:
			for v in [a - off, a + off, b - off, b - off, a + off, b + off]:
				st.set_uv(Vector2(0.5, 0.5)); st.add_vertex(v)
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat; mi.extra_cull_margin = 16384.0
	env_root.add_child(mi); tris += n * 4

# --- WANGAN: the E3B road as is (11.9 m) with lane lines, jersey barriers, deck fascia, tall lamps, city ----
func _dress_wangan(W: float) -> void:
	var conc := tex_mat("wangan_concrete", 6.0)
	for sd in [-1.0, 1.0]:
		band(S0, S1, sd * W, 0.0, sd * (W + 0.9), 0.0, conc)                 # shoulder strip
		band(S0, S1, sd * (W + 1.15), 0.0, sd * (W + 1.15), -1.6, conc)       # deck fascia (the drop below is open)
		var s := S0
		while s < S1:
			prop("wangan_jersey", s, sd * (W + 0.75), 0.0, 0.0, 0.62)
			s += 2.47
	# tall sodium lamps on the barriers, arms over the lanes, both sides staggered 24 m
	for sd in [1.0, -1.0]:
		var s3 := (0.0 if sd > 0 else 24.0) - 96.0
		while s3 < S1:
			if s3 > S0:
				var p := prop("wangan_lamp", s3, sd * (W + 0.75), 0.0)
				lamp_glow(p, Vector3(-4.5, 11.6, 0), 2.0, 0.85)
			s3 += 48.0
	# distant city: emissive towers across the bay, far past the deck (150-320 m), sunk so only the upper floors show
	var k := 0
	for spec in [[40.0, 190.0, -40.0], [110.0, 240.0, -30.0], [-20.0, 280.0, -20.0], [170.0, 210.0, -45.0], [70.0, 320.0, -10.0],
			[-60.0, 230.0, -35.0], [230.0, 260.0, -25.0], [20.0, -260.0, -30.0], [120.0, -300.0, -20.0], [200.0, -230.0, -40.0]]:
		prop("wangan_tower_%d" % (k % 3), spec[0], spec[1], spec[2], ArtKit.hash01(k * 1.3) * 0.8, 1.0, 0.75)
		k += 1
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
	post_mat.set_shader_parameter("fog_color", Vector3(fog.r, fog.g, fog.b))
	post_mat.set_shader_parameter("fog_near", float(DC.fog_near))
	post_mat.set_shader_parameter("fog_far", float(DC.fog_far))
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
		var cm: Dictionary = disp.camera
		var pose: Array = _chase_pose(course.point(player_s, 0.0))
		var cpos: Vector3 = pose[0]; var tgt: Vector3 = pose[1]
		if cam_pull:
			# mouse test: same family, pulled back + up a little so the chaser can show behind the player
			var q0: Dictionary = course.point(player_s, 0.0)
			var tv := Vector3(q0.tx, 0, q0.tz)
			cpos += -tv * 2.2 + Vector3(0, 0.9, 0)
		cpos.y += elev(player_s - float(cm.back) - (2.2 if cam_pull else 0.0), float(cm.side))
		tgt.y += elev(player_s + float(cm.look_ahead), float(cm.look_side))
		cam.position = cpos
		cam.look_at(tgt, Vector3.UP)
		cam.fov = float(cm.fov)
	else:
		var stop := 1 if kind == "apex" else 2
		var pose2: Array = _stop_pose(stop)
		cam.position = pose2[0]
		cam.look_at(pose2[1], Vector3.UP)
		cam.fov = pose2[2]
	glow_cam.fov = cam.fov
	glow_cam.global_transform = cam.global_transform
	sky_root.position = cam.position

# ---------------------------------------------------------------------------------------------------
# Cat and mouse lighting (faked, no dynamic lights). Built once, toggled per frame.
var fx_nodes: Array = []
var player_lit_mats: Array = []
const CAR_LIT_SH = preload("res://shaders/car_lit.gdshader")

func _set_lights(fr: Dictionary, player_s: float) -> void:
	for n in fx_nodes: (n as Node).queue_free()
	fx_nodes.clear()
	for m in player_lit_mats: (m as ShaderMaterial).set_shader_parameter("rear_k", 0.0)
	var role := String(fr.get("role", "std"))
	if role == "mouse":
		var near := absf(float(fr.rival_ds)) < 12.0
		# 1) the chaser's own beam on the road, long enough to pass under the player (child of the rival, follows grade)
		var throw: MeshInstance3D = art.decal("headlight_throw", 5.0, 17.0, 2.2 + 8.5, true, 0.95 if near else 0.4)
		rival_car.add_child(throw); fx_nodes.append(throw)
		# 2) bigger head glows so the chaser reads in the rear-view inset even far back
		for x in [-0.6, 0.6]:
			var g: MeshInstance3D = art.glow_sprite("glow_head", Color(1, 1, 1), 1.5 if near else 3.6, 0.85 if near else 1.0)
			g.position = Vector3(x, 0.68, 2.1); rival_car.add_child(g); fx_nodes.append(g)
		if near:
			# 3) the player's own shadow thrown forward into the chaser's beam (dark, not additive)
			var sh: MeshInstance3D = art.decal("blob_shadow", 1.9, 6.5, 2.1 + 3.0, false, 0.85)
			sh.material_override.render_priority = 2
			player_car.add_child(sh); fx_nodes.append(sh)
			# 4) the beam lighting the player's tail / rear deck (car_lit.gdshader rear light)
			var hp: Vector3 = rival_car.global_transform * Vector3(0, 0.68, 2.1)
			var fwd: Vector3 = (rival_car.global_transform.basis * Vector3(0, 0, 1)).normalized()
			_ensure_player_lit()
			for m in player_lit_mats:
				m.set_shader_parameter("rear_pos", hp); m.set_shader_parameter("rear_dir", fwd)
				m.set_shader_parameter("rear_k", 1.1); m.set_shader_parameter("rear_range", 13.0)
	elif role == "cat":
		# taillight wash on the road just behind the leader, sitting in the chevrons
		var tw: MeshInstance3D = art.decal("glow_tail", 2.8, 3.6, -3.0, true, 0.7)
		rival_car.add_child(tw); fx_nodes.append(tw)
		for x in [-0.58, 0.58]:   # slightly bigger tail glows so the leader reads down the chevrons
			var t: MeshInstance3D = art.glow_sprite("glow_tail", Color(1, 1, 1), 1.1, 0.8)
			t.position = Vector3(x, 0.8, -2.08); rival_car.add_child(t); fx_nodes.append(t)

func _ensure_player_lit() -> void:
	if not player_lit_mats.is_empty(): return
	for m in player_car.mats:
		var sm := m as ShaderMaterial
		sm.shader = CAR_LIT_SH
		player_lit_mats.append(sm)

# ---------------------------------------------------------------------------------------------------
# Mouse-view options. Inset = the second camera (mirror_vp), composited by the post shader at hud.inset.rect.
const HEADON_Z := -1.0     # along the car from its centre (rear bumper is about -2.1)
const HEADON_Y := 1.22
const HEADON_LOOK_Y := 0.55

func _apply_mode(fr: Dictionary, player_s: float, d_entry: float) -> void:
	var mode := String(fr.get("mode", ""))
	var r: Array = [disp.mirror.x, disp.mirror.y, disp.mirror.w, disp.mirror.h]
	var flip := 1.0
	cam.near = 0.1; glow_cam.near = 0.1
	mirror_cam.fov = float(disp.mirror.fov)
	if fr.has("hud") and fr.hud.has("inset"): r = fr.hud.inset.rect
	if mode == "bigmirror":
		# same rear camera and lens; 2x the inset, rendered at 2x so it stays as crunchy as the main view
		mirror_cam.fov = float(disp.mirror.fov) * 1.12
	elif mode == "lookback":
		# main view: low reverse camera over the player's tail, looking back down the hill at the chaser
		# low, off the player's outside rear quarter, so the tail + taillight sit in the near corner of the frame
		var q: Dictionary = course.point(player_s - 0.5, d_entry + 1.2)
		var rv: Dictionary = course.point(player_s - 12.0, d_entry - 0.7)
		cam.position = Vector3(q.x, elev(player_s - 0.5, d_entry + 1.2) + 1.38, q.z)
		cam.look_at(Vector3(rv.x, elev(player_s - 12.0, d_entry) - 0.05, rv.z), Vector3.UP)
		cam.fov = float(disp.camera.fov)
		glow_cam.global_transform = cam.global_transform; glow_cam.fov = cam.fov
		sky_root.position = cam.position
		# inset: the standard forward chase view (same camera as every other frame), not mirrored
		var cm: Dictionary = disp.camera
		var pose: Array = _chase_pose(course.point(player_s, 0.0))
		var cpos: Vector3 = pose[0]; var tgt: Vector3 = pose[1]
		cpos.y += elev(player_s - float(cm.back), float(cm.side)); tgt.y += elev(player_s + float(cm.look_ahead), float(cm.look_side))
		mirror_cam.position = cpos; mirror_cam.look_at(tgt, Vector3.UP)
		mirror_cam.fov = 40.0
		mirror_cam.near = 0.1
		flip = 0.0
	elif mode == "headon":
		# main view: centred reverse camera just ahead of the rear deck, square to the road, looking straight back
		var hs: float = player_s + HEADON_Z
		var hq: Dictionary = course.point(hs, d_entry)
		var lb: float = 30.0
		var hr: Dictionary = course.point(player_s - lb, d_entry)
		cam.position = Vector3(hq.x, elev(hs, d_entry) + HEADON_Y, hq.z)
		cam.look_at(Vector3(hr.x, elev(player_s - lb, d_entry) + HEADON_LOOK_Y, hr.z), Vector3.UP)
		cam.fov = float(disp.camera.fov)
		cam.near = 0.05
		glow_cam.global_transform = cam.global_transform; glow_cam.fov = cam.fov; glow_cam.near = cam.near
		sky_root.position = cam.position
		# mirror stays the normal E3B rear view (pose set in _apply_frame), same rect/frame/label/flip
	elif mode == "highcam":
		# higher, steeper chase camera, pulled back behind the chaser so both cars sit on the road above the band.
		# The pull-back follows the gap (capped), like a two-car framing cam.
		var gap: float = absf(float(fr.rival_ds))
		var back: float = clampf(gap + 12.0, 22.0, 38.0)
		var up: float = 6.0 + back * 0.17
		var ts: float = player_s + 4.0 - 0.45 * maxf(gap - 10.0, 0.0) * 1.4   # aim drifts back toward the chaser as the gap grows
		var q0: Dictionary = course.point(player_s - back, 1.0)
		var tg: Dictionary = course.point(ts, 0.3)
		cam.position = Vector3(q0.x, elev(player_s - back, 1.0) + up, q0.z)
		cam.look_at(Vector3(tg.x, elev(ts, 0.0) - 2.6, tg.z), Vector3.UP)
		cam.fov = float(disp.camera.fov)
		glow_cam.global_transform = cam.global_transform; glow_cam.fov = cam.fov
		sky_root.position = cam.position
	if mode != "lookback": mirror_cam.near = float(disp.mirror.near)
	var sz := Vector2i(int(r[2]), int(r[3]))
	if mirror_vp.size != sz: mirror_vp.size = sz
	post_mat.set_shader_parameter("mirror_rect", Vector4(float(r[0]), float(r[1]), float(r[2]), float(r[3])))
	post_mat.set_shader_parameter("mirror_flip", flip)

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
	car.position = Vector3(p.x, elev(s, d), p.z)
	var pitch := atan((elev(s + 1.2, d) - elev(s - 1.2, d)) / 2.4)
	var roll := atan((elev(s, d + 0.8) - elev(s, d - 0.8)) / 1.6)   # +d = road right = car local -X
	car.rotation = Vector3(-pitch, atan2(p.tx, p.tz), -roll)
	return p

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
		_place_car(rival_car, player_s + float(fr.rival_ds), _lane_d(String(fr.rival_lane)) + float(fr.get("rival_d_nudge", 0.0)))
	cam_pull = bool(fr.get("cam_pull", false))
	_place_camera(cam_kind, player_s)
	_set_lights(fr, player_s)
	var t := Vector3(pp.tx, 0, pp.tz)
	var p := Vector3(pp.x, elev(player_s, d_entry), pp.z)
	mirror_cam.position = p + Vector3(0, float(disp.mirror.cam_up), 0)
	var mt: Vector3 = p - t * float(disp.mirror.look_back)
	mt.y = elev(player_s - float(disp.mirror.look_back), d_entry) + float(disp.mirror.look_y)
	mirror_cam.look_at(mt, Vector3.UP)
	_apply_mode(fr, player_s, d_entry)
	# Mirror only on the chase camera (and the overview, so that sheet keeps a rear view).
	var mirror_on := cam_kind == "chase" or cam_kind == "overview"
	post_mat.set_shader_parameter("mirror_on", 1.0 if mirror_on else 0.0)
	_build_line(fr, d_entry, player_s)
	var left: float = 4.8
	var turn_m: float = left * SPEED_MS
	# Floating OUT / MID / IN labels (and their down-arrows) are off.
	# The coloured road chevrons alone show the planned line. lanes.gd is
	# Arthur's line-preview overlay (also copied in Gordon's two-corner HUD
	# at unapproved/gordon/two-corner/godot/scripts/hud/lanes.gd); passing
	# null skips it. Chevron meshes are unchanged.
	var lanes = null
	_show_hud(fr, lanes, turn_m, left, mirror_on)

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
	chevrons.build(course, segs, fog, float(DC.fog_near), float(DC.fog_far))

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
		"lead": float(fr.get("lead", 0.0)), "gap": float(fr.get("lead", 0.0)), "gap_s": float(fr.get("gap_s", 0.0)), "left": left, "total": 12.0,
		"slots": slots, "hand": ["A", "A", "S", "S", "D", "D"], "used": [],
		"qte": null, "line": "", "rline": "", "outs": [],
		"plate": plate, "locked_hold": false, "mirror": mirror_on, "play_phase": 0,
		"plan": plan, "turn_m": turn_m, "dir": DIR, "lanes": lanes,
		"result": {}, "reveal": 0, "cont_left": 8.0, "leader_changed": false,
		"winner": "", "cum_p": 0.0, "cum_o": 0.0, "last_corner": false, "fin": null,
		"resources": fr.get("resources", {})
	}.merged(fr.get("hud", {}), true)

# --- cel: G-buffer passes ------------------------------------------------------------------------------
# Same frame rendered twice more with the global cel_gbuf = 1 (view normals) and 2 (packed linear depth). Every
# shader in the scene draws through the same vertex code, so the passes line up pixel for pixel. Decals
# (StandardMaterial3D blob shadows / beams) are hidden in those passes so they cannot pollute the buffers.
func _decals(n: Node, out: Array) -> void:
	if n is MeshInstance3D and (n as MeshInstance3D).material_override is StandardMaterial3D and (n as Node3D).visible:
		out.append(n)
	for ch in n.get_children(): _decals(ch, out)

func _grab(vp: SubViewport) -> ImageTexture:
	var im := vp.get_texture().get_image()
	im.convert(Image.FORMAT_RGB8)
	return ImageTexture.create_from_image(im)

func _gbuffer() -> void:
	var hide: Array = []
	if OS.get_environment("CEL_KEEPDECALS") == "": _decals(world_vp, hide)
	print("cel: hiding ", hide.size(), " decals")
	for n in hide: (n as Node3D).visible = false
	var env: Environment = world_vp.world_3d.environment
	var bg := env.background_color
	env.background_color = Color(1, 1, 1)
	for pass_i in [1, 2]:
		RenderingServer.global_shader_parameter_set("cel_gbuf", float(pass_i))
		await _settle(4)
		var gt := _grab(world_vp)
		if OS.get_environment("CEL_DEBUG") != "": gt.get_image().save_png("/tmp/cel_g%d_%s.png" % [pass_i, DK])
		post_mat.set_shader_parameter("gn_tex" if pass_i == 1 else "gd_tex", gt)
		post_mat.set_shader_parameter("mn_tex" if pass_i == 1 else "md_tex", _grab(mirror_vp))
	RenderingServer.global_shader_parameter_set("cel_gbuf", 0.0)
	env.background_color = bg
	for n in hide: (n as Node3D).visible = true
	await _settle(4)

func _capture(path: String) -> void:
	await _settle(4)
	await _gbuffer()
	# flavour A: cel + the PSX RGB555 / Bayer pass (name_cel.png); flavour B: clean, no dither (name_cel_clean.png)
	for fl in [["_cel", 1.0], ["_cel_clean", 0.0]]:
		post_mat.set_shader_parameter("dither_on", fl[1])
		post_mat.set_shader_parameter("ink_on", 0.0 if OS.get_environment("CEL_NOINK") != "" else 1.0)
		await _settle(3)
		await _write(path.get_basename() + String(fl[0]) + ".png")

func _write(path: String) -> void:
	await _settle(2)
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
