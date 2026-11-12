## Headless (xvfb) Godot 4.6.3 render of the line-select Entry frame, with pack-based PSX roads.
## 3D: 640x480, no AA, bloom/sat, RGB555 + 4x4 Bayer, 2x nearest.
## Classic HUD is composited at 640 then dithered (matches the Blender before.png pipeline).
## Sharp HUD is drawn after the 2x upscale at 1280x960 (new B.5c).
extends Control

const CX := 12.0
const CY := 0.0
const RAD := 12.0
const HALF := 5.0
const LANE_OUT := -3.3
const FOG := Color8(11, 23, 43)
const ZENITH := Color8(1, 4, 8)
const AMB := Color8(85, 117, 160)
const LAMP := Color8(240, 200, 148)
const AMB_K := 0.8
const LAMP_K := 0.85
const STEPS := 3.0
const LANE_GK := 0.55
const FOG_NEAR := 9.0
const FOG_FAR := 78.0
const VSCALE := 13.333333  # metres along per V-repeat of road_3lane.png (10m * 256/192)

var LA: float
var S0 := -110.0
var S1: float
var lamp_heads: Array[Vector3] = []
var world_vp: SubViewport
var glow_vp: SubViewport
var mirror_vp: SubViewport
var lit_vp: SubViewport
var classic_vp: SubViewport
var bayer_vp: SubViewport
var sharp_root: Control
var cam: Camera3D
var glow_cam: Camera3D
var mirror_cam: Camera3D
var post_mat: ShaderMaterial
var road_mats: Array[ShaderMaterial] = []
var out_dir: String
var player: Node3D
var rival: Node3D

func _ready() -> void:
	LA = PI * RAD
	S1 = LA + 90.0
	out_dir = ProjectSettings.globalize_path("res://").path_join("..")
	_build_viewports()
	_build_world()
	_load_cars()
	_place_cameras()
	await _settle()
	await _render_all()
	print("ROAD_TEST_OK ", out_dir)
	get_tree().quit(0)

func _settle() -> void:
	for i in 8:
		await get_tree().process_frame
		await RenderingServer.frame_post_draw

func track(s: float, off: float) -> Dictionary:
	# Blender (x, y forward, z up) -> Godot (x, y up, z = -y). Entry heading +Y becomes -Z.
	if s < 0.0:
		return {"p": Vector3(off, 0.0, -s), "f": Vector3(0.0, 0.0, -1.0)}
	if s <= LA:
		var phi := PI - s / RAD
		var r := RAD - off
		var p := Vector3(CX + r * cos(phi), 0.0, -(CY + r * sin(phi)))
		var f := Vector3(sin(phi), 0.0, cos(phi))
		return {"p": p, "f": f}
	var p2 := Vector3(CX + RAD - off, 0.0, s - LA)
	return {"p": p2, "f": Vector3(0.0, 0.0, 1.0)}

func _gpos(bx: float, by: float, bz: float) -> Vector3:
	return Vector3(bx, bz, -by)

func _samples(s0: float, s1: float) -> Array:
	var out: Array = []
	var s := s0
	while s < s1:
		out.append(s)
		s += 0.5 if (s >= 0.0 and s <= LA) else 2.0
	out.append(s1)
	return out

func vlight(p: Vector3, nrm: Vector3) -> Color:
	var k := 0.19 + 0.05 * maxf(0.0, nrm.y)
	k *= maxf(0.45, 1.0 - maxf(0.0, p.y - 3.0) / 25.0) * AMB_K
	var c := Vector3(AMB.r, AMB.g, AMB.b) * k
	for L in lamp_heads:
		var d := p.distance_to(L)
		var lv := maxf(0.0, 1.0 - d / 13.0)
		lv = floor(lv * STEPS) / STEPS
		var gk := LANE_GK if nrm.y > 0.7 else 1.0
		c += Vector3(LAMP.r, LAMP.g, LAMP.b) * lv * LAMP_K * gk
	c = Vector3(minf(1.0, c.x * 0.5), minf(1.0, c.y * 0.5), minf(1.0, c.z * 0.5))
	return Color(c.x, c.y, c.z, 1.0)

func _tex(n: String) -> Texture2D:
	return load("res://art/%s.png" % n) as Texture2D

func _road_mat(tex_name: String, alpha := false) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/road.gdshader")
	var t := _tex(tex_name)
	m.set_shader_parameter("tex_lin", t)
	m.set_shader_parameter("tex_near", t)
	m.set_shader_parameter("use_nearest", 0)
	m.set_shader_parameter("fog_color", Vector3(FOG.r, FOG.g, FOG.b))
	m.set_shader_parameter("fog_near", FOG_NEAR)
	m.set_shader_parameter("fog_far", FOG_FAR)
	m.set_shader_parameter("alpha_cut", 1 if alpha else 0)
	m.set_meta("tex_name", tex_name)
	m.set_meta("alpha_cut", 1 if alpha else 0)
	road_mats.append(m)
	return m

func _set_filter(nearest: bool) -> void:
	var sh: Shader = load("res://shaders/road_near.gdshader") if nearest else load("res://shaders/road.gdshader")
	var v := 1 if nearest else 0
	for m in road_mats:
		var tex_name: String = m.get_meta("tex_name")
		var t2 := _tex(tex_name)
		m.shader = sh
		m.set_shader_parameter("tex_lin", t2)
		m.set_shader_parameter("tex_near", t2)
		m.set_shader_parameter("use_nearest", v)
		m.set_shader_parameter("fog_color", Vector3(FOG.r, FOG.g, FOG.b))
		m.set_shader_parameter("fog_near", FOG_NEAR)
		m.set_shader_parameter("fog_far", FOG_FAR)
		m.set_shader_parameter("alpha_cut", int(m.get_meta("alpha_cut")))
	for vp in [world_vp, glow_vp, mirror_vp, lit_vp, classic_vp, bayer_vp]:
		vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS

func _strip(name: String, s0: float, s1: float, prof: Array, mat: ShaderMaterial, vscale: float, world: Node) -> MeshInstance3D:
	# prof = array of [off, z, u]
	var ss: Array = _samples(s0, s1)
	var n: int = prof.size()
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(ss.size() - 1):
		for j in range(n - 1):
			var corners: Array = []
			for pair in [[ss[i], prof[j]], [ss[i], prof[j + 1]], [ss[i + 1], prof[j + 1]], [ss[i + 1], prof[j]]]:
				var s: float = pair[0]
				var pr: Array = pair[1]
				var tr: Dictionary = track(s, float(pr[0]))
				var p: Vector3 = tr.p + Vector3(0, float(pr[1]), 0)
				var uv := Vector2(float(pr[2]), s / vscale)
				var nrm := Vector3.UP
				corners.append([p, uv, nrm])
			# two triangles: 0,1,2 and 0,2,3
			for idx in [0, 1, 2, 0, 2, 3]:
				var c: Array = corners[idx]
				st.set_uv(c[1])
				st.set_color(vlight(c[0], c[2]))
				st.add_vertex(c[0])
	var mi := MeshInstance3D.new()
	mi.name = name
	mi.mesh = st.commit()
	mi.material_override = mat
	mi.extra_cull_margin = 16384.0
	world.add_child(mi)
	return mi

func _new_vp(size: Vector2i, transparent := false, is_3d := true) -> SubViewport:
	var vp := SubViewport.new()
	vp.size = size
	vp.transparent_bg = transparent
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.msaa_3d = Viewport.MSAA_DISABLED
	vp.msaa_2d = Viewport.MSAA_DISABLED
	vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	if is_3d:
		# world assigned later
		pass
	else:
		vp.disable_3d = true
	add_child(vp)
	return vp

func _build_viewports() -> void:
	world_vp = _new_vp(Vector2i(640, 480))
	world_vp.world_3d = World3D.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = FOG
	env.ambient_light_source = Environment.AMBIENT_SOURCE_DISABLED
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	world_vp.world_3d.environment = env
	cam = Camera3D.new()
	cam.fov = 56.7
	cam.near = 0.1
	cam.far = 600.0
	cam.keep_aspect = Camera3D.KEEP_HEIGHT
	world_vp.add_child(cam)
	cam.current = true

	mirror_vp = _new_vp(Vector2i(192, 64))
	mirror_vp.world_3d = world_vp.world_3d
	mirror_cam = Camera3D.new()
	mirror_cam.fov = 46.4
	mirror_cam.near = 0.1
	mirror_cam.far = 300.0
	mirror_cam.keep_aspect = Camera3D.KEEP_HEIGHT
	mirror_vp.add_child(mirror_cam)
	mirror_cam.current = true

	glow_vp = _new_vp(Vector2i(640, 480))
	glow_vp.world_3d = world_vp.world_3d
	glow_cam = Camera3D.new()
	glow_cam.fov = 56.7
	glow_cam.near = 0.1
	glow_cam.far = 600.0
	glow_cam.keep_aspect = Camera3D.KEEP_HEIGHT
	glow_cam.cull_mask = 2
	var genv := Environment.new()
	genv.background_mode = Environment.BG_COLOR
	genv.background_color = Color.BLACK
	glow_cam.environment = genv
	glow_vp.add_child(glow_cam)
	glow_cam.current = true

	# Lit 3D (bloom + sat + mirror), no Bayer yet
	lit_vp = _new_vp(Vector2i(640, 480), false, false)
	post_mat = ShaderMaterial.new()
	post_mat.shader = load("res://shaders/post.gdshader")
	post_mat.set_shader_parameter("scene_tex", world_vp.get_texture())
	post_mat.set_shader_parameter("mirror_tex", mirror_vp.get_texture())
	post_mat.set_shader_parameter("glow_tex", glow_vp.get_texture())
	post_mat.set_shader_parameter("bloom_k", 0.22)
	post_mat.set_shader_parameter("sat", 1.05)
	post_mat.set_shader_parameter("res", Vector2(640, 480))
	post_mat.set_shader_parameter("mirror_rect", Vector4(224, 16, 192, 64))
	post_mat.set_shader_parameter("mirror_on", 1.0)
	post_mat.set_shader_parameter("quantize", 0.0)
	var lit_rect := TextureRect.new()
	lit_rect.size = Vector2(640, 480)
	lit_rect.stretch_mode = TextureRect.STRETCH_SCALE
	lit_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	lit_rect.texture = world_vp.get_texture()
	lit_rect.material = post_mat
	lit_vp.add_child(lit_rect)

	# Classic: lit + HUD at 640, then Bayer, then we upscale in CPU/GPU when saving
	classic_vp = _new_vp(Vector2i(640, 480), false, false)
	var cbase := TextureRect.new()
	cbase.size = Vector2(640, 480)
	cbase.stretch_mode = TextureRect.STRETCH_SCALE
	cbase.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	cbase.texture = lit_vp.get_texture()
	cbase.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	classic_vp.add_child(cbase)
	var chud := preload("res://hud.gd").new()
	classic_vp.add_child(chud)
	chud.setup("classic")

	bayer_vp = _new_vp(Vector2i(640, 480), false, false)
	var bmat := ShaderMaterial.new()
	bmat.shader = load("res://shaders/bayer.gdshader")
	bmat.set_shader_parameter("src", classic_vp.get_texture())
	bmat.set_shader_parameter("res", Vector2(640, 480))
	var brect := TextureRect.new()
	brect.size = Vector2(640, 480)
	brect.stretch_mode = TextureRect.STRETCH_SCALE
	brect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	brect.texture = classic_vp.get_texture()
	brect.material = bmat
	bayer_vp.add_child(brect)

	# Sharp: Bayer the lit 3D only, 2x nearest, HUD on top at 1280
	# We build this into a 1280x960 SubViewport at save time so we can swap the 3D texture.
	sharp_root = Control.new()
	sharp_root.size = Vector2(1280, 960)
	# Added later into a viewport in _capture_sharp

func _build_world() -> void:
	var w: Node = world_vp
	# Sky cylinder
	_build_sky(w)
	# Lamps first so vlight can use their heads
	for s in [-62.0, -13.0, LA * 0.70, LA + 26.0]:
		_add_lamp(w, s, -7.3)
	# Road: U 0..1 across full 10 m, V = metres / 13.333 (pack tile)
	var road_mat := _road_mat("road_3lane")
	_strip("Road", S0, S1, [[-HALF, 0.18, 0.0], [0.0, 0.18, 0.5], [HALF, 0.18, 1.0]], road_mat, VSCALE, w)
	# Kerb / shoulder / gutter from pack concrete
	var conc := _road_mat("concrete_kerb")
	_strip("ShoulderOut", S0, S1, [[-HALF - 1.7, 0.17, 0.0], [-HALF, 0.18, 0.425]], conc, 4.0, w)
	_strip("GutterIn", S0, S1, [[HALF, 0.18, 0.0], [HALF + 0.25, 0.05, 0.3], [HALF + 0.6, 0.3, 1.0]], conc, 4.0, w)
	# Cut bank + drop
	var slope := _road_mat("slope")
	var hill_prof: Array = []
	for o in [5.6, 6.4, 7.6, 9.0, 10.5, 12.0]:
		var t := clampf((o - 5.6) / 6.4, 0.0, 1.0)
		hill_prof.append([o, 0.3 + 2.9 * pow(t, 1.2), (o - 5.6) / 2.0])
	_strip("InsideHill", S0, S1, hill_prof, slope, 4.0, w)
	var drop_prof: Array = []
	for o in [-6.7, -8.0, -10.5, -13.5, -17.7]:
		var t2 := clampf((-6.7 - o) / 11.0, 0.0, 1.0)
		drop_prof.append([o, 0.17 - 9.2 * pow(t2, 1.3), (-6.7 - o) / 2.0])
	_strip("OutsideDrop", S0, S1, drop_prof, slope, 4.0, w)
	# Low ground
	_flat_ground(w, slope)
	# Guardrail
	var gr := _road_mat("guardrail")
	_strip("Guardrail", S0, S1, [[-5.95, 0.42, 1.0], [-5.86, 0.61, 0.5], [-5.95, 0.80, 0.0]], gr, 4.0, w)
	# Cedars (after cameras we'd cull; we place cameras first in _place_cameras then could skip, do a keep-out later)
	_add_cedars(w)
	# Chevron boards near the hairpin
	_add_chevrons(w)
	# Lamp pool decals
	_add_pools(w)

func _flat_ground(w: Node, mat: ShaderMaterial) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pts := [Vector3(-260, -9.05, 260), Vector3(280, -9.05, 260), Vector3(280, -9.05, -260), Vector3(-260, -9.05, -260)]
	var uvs := [Vector2(0, 0), Vector2(90, 0), Vector2(90, 90), Vector2(0, 90)]
	for idx in [0, 1, 2, 0, 2, 3]:
		st.set_uv(uvs[idx])
		st.set_color(vlight(pts[idx], Vector3.UP))
		st.add_vertex(pts[idx])
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mat
	w.add_child(mi)

func _add_lamp(w: Node, s: float, off: float) -> void:
	var tr: Dictionary = track(s, off)
	var mid: Dictionary = track(s, 0.0)
	var face: Vector3 = (mid.p - tr.p).normalized()
	var base: Vector3 = tr.p + Vector3(0, -0.25, 0)
	var head: Vector3 = base + face * 1.7 + Vector3(0, 6.35, 0)
	lamp_heads.append(head)
	# simple post + arm + head (unlit, vertex-coloured)
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/road.gdshader")
	# no tex: use a 1x1 white? easier a StandardMaterial unshaded
	var sm := StandardMaterial3D.new()
	sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	sm.vertex_color_use_as_albedo = true
	sm.disable_fog = true
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pc := vlight(base + Vector3(0, 3, 0), Vector3.RIGHT)
	# post
	_box(st, base + Vector3(0, 3.25, 0), 0.12, 6.5, 0.12, pc)
	var arm_c := vlight(head, Vector3.UP)
	_box(st, base + face * 0.85 + Vector3(0, 6.35, 0), 1.5, 0.12, 0.12, arm_c)
	var hc := Color(LAMP.r, LAMP.g, LAMP.b, 1.0)
	_box(st, head, 0.4, 0.25, 0.3, hc)
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = sm
	w.add_child(mi)
	# glow sprite
	var gl := _glow("glow_blend50_0", 1.5, 0.9)
	gl.position = head + Vector3(0, -0.15, 0)
	w.add_child(gl)

func _box(st: SurfaceTool, c: Vector3, sx: float, sy: float, sz: float, col: Color) -> void:
	var hx := sx * 0.5
	var hy := sy * 0.5
	var hz := sz * 0.5
	var v := [
		c + Vector3(-hx, -hy, -hz), c + Vector3(hx, -hy, -hz), c + Vector3(hx, hy, -hz), c + Vector3(-hx, hy, -hz),
		c + Vector3(-hx, -hy, hz), c + Vector3(hx, -hy, hz), c + Vector3(hx, hy, hz), c + Vector3(-hx, hy, hz)
	]
	var faces := [[0, 1, 2, 3], [5, 4, 7, 6], [4, 0, 3, 7], [1, 5, 6, 2], [3, 2, 6, 7], [4, 5, 1, 0]]
	for f in faces:
		for idx in [0, 1, 2, 0, 2, 3]:
			st.set_color(col)
			st.set_uv(Vector2.ZERO)
			st.add_vertex(v[f[idx]])

func _glow(tex_name: String, size: float, strength: float) -> MeshInstance3D:
	var qm := QuadMesh.new()
	qm.size = Vector2(1, 1)
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/glow.gdshader")
	m.set_shader_parameter("tex", _tex(tex_name))
	m.set_shader_parameter("color", Vector3(1, 1, 1))
	m.set_shader_parameter("strength", strength)
	m.set_shader_parameter("size", Vector2(size, size))
	m.set_shader_parameter("snap_res", Vector2(640, 480))
	m.set_shader_parameter("fog_near", FOG_NEAR)
	m.set_shader_parameter("fog_far", FOG_FAR)
	m.render_priority = 5
	var mi := MeshInstance3D.new()
	mi.mesh = qm
	mi.material_override = m
	mi.extra_cull_margin = 16384.0
	mi.layers = 3
	return mi

func _add_pools(w: Node) -> void:
	var pm := ShaderMaterial.new()
	pm.shader = load("res://shaders/pool.gdshader")
	pm.set_shader_parameter("tex", _tex("pool_blend50_0"))
	pm.set_shader_parameter("strength", 0.09 * 1.8)
	for L in lamp_heads:
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var ss: Array = []
		for s in _samples(S0, S1):
			var tr: Dictionary = track(s, 0.0)
			if tr.p.distance_to(Vector3(L.x, 0, L.z)) < 15.0:
				ss.append(s)
		if ss.size() < 2:
			continue
		var offs := [-6.7, -5.0, -2.5, 0.0, 2.5, 5.0, 5.6]
		var rows: Array = []
		for s in ss:
			var row: Array = []
			for o in offs:
				var tr: Dictionary = track(s, o)
				var y := 0.20 if o > -5.01 else 0.19
				var p: Vector3 = tr.p + Vector3(0, y, 0)
				var uv := Vector2((p.x - L.x) / 13.0 + 0.5, (p.z - L.z) / 13.0 + 0.5)
				row.append([p, uv])
			rows.append(row)
		for i in range(rows.size() - 1):
			for j in range(offs.size() - 1):
				var q := [rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]]
				for idx in [0, 1, 2, 0, 2, 3]:
					st.set_uv(q[idx][1])
					st.add_vertex(q[idx][0])
		var mi := MeshInstance3D.new()
		mi.mesh = st.commit()
		mi.material_override = pm
		mi.extra_cull_margin = 16384.0
		w.add_child(mi)

func _card(tex_name: String, w: float, h: float, pos: Vector3, yaw: float, alpha := true) -> MeshInstance3D:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var vs := [Vector3(-w / 2, 0, 0), Vector3(w / 2, 0, 0), Vector3(w / 2, h, 0), Vector3(-w / 2, h, 0)]
	var uvs := [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)]
	for idx in [0, 1, 2, 0, 2, 3]:
		st.set_uv(uvs[idx])
		st.set_color(vlight(pos + Vector3(0, vs[idx].y, 0), Vector3.BACK))
		st.add_vertex(vs[idx])
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = _road_mat(tex_name, alpha)
	mi.position = pos
	mi.rotation.y = yaw
	mi.extra_cull_margin = 16384.0
	return mi

func _drop_z(off: float) -> float:
	var t := clampf((-6.7 - off) / 11.0, 0.0, 1.0)
	return 0.17 - 9.2 * pow(t, 1.3)

func _hill_z(off: float) -> float:
	var t := clampf((off - 5.6) / 6.4, 0.0, 1.0)
	return 0.3 + 2.9 * pow(t, 1.2)

func _add_cedars(w: Node) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	var cam_keep: Array[Vector3] = [
		_gpos(1.4, -35.6, 3.10),  # chase
		_gpos(0, -28, 1.60)
	]
	var trees: Array = []
	var s := S0
	while s < S1:
		for i in 2:
			var o := -rng.randf_range(9.0, 34.0)
			var tr: Dictionary = track(s + rng.randf_range(-2, 2), o)
			var z := _drop_z(o) if o > -17.7 else -9.05
			trees.append([tr.p + Vector3(0, z, 0), rng.randf_range(11, 16)])
		if rng.randf() < 0.8:
			var o2 := rng.randf_range(7.2, 12.0)
			var tr2: Dictionary = track(s + rng.randf_range(-2, 2), o2)
			trees.append([tr2.p + Vector3(0, _hill_z(o2) - 0.2, 0), rng.randf_range(9, 14)])
		s += 3.2 if (s >= 0.0 and s <= LA) else 4.5
	for i in 30:
		var x := 12.0 + rng.randf_range(-3, 3)
		var yb := rng.randf_range(-60, -4)
		trees.append([_gpos(x, yb, _hill_z(12) - 0.2), rng.randf_range(10, 15)])
	for t in trees:
		var p: Vector3 = t[0]
		var h: float = t[1]
		var skip := false
		for ck in cam_keep:
			if Vector2(p.x, p.z).distance_to(Vector2(ck.x, ck.z)) < 5.5:
				skip = true
				break
		if skip:
			continue
		var a := rng.randf() * PI
		w.add_child(_card("cedar", h / 3.0, h, p, a, true))
		w.add_child(_card("cedar", h / 3.0, h, p, a + PI / 2.0, true))

func _add_chevrons(w: Node) -> void:
	# a few boards on the outside of the approach, like the approved frame
	for s in [-8.0, 2.0, 8.0, 14.0]:
		var tr: Dictionary = track(s, -6.2)
		var yaw := atan2(tr.f.x, tr.f.z)
		w.add_child(_card("chevron", 0.7, 0.7, tr.p + Vector3(0, 0.9, 0), yaw, false))

func _build_sky(w: Node) -> void:
	var sky_m := ShaderMaterial.new()
	sky_m.shader = load("res://shaders/sky.gdshader")
	sky_m.set_shader_parameter("tex", _tex("sky_blend50"))
	sky_m.set_shader_parameter("alpha_cut", 0)
	var sc := Vector3(12, 0, 0)
	for i in 12:
		var a0 := TAU * i / 12.0
		var a1 := TAU * (i + 1) / 12.0
		# blender cylinder in XY; godot XZ. radius 330, y -40..330
		var p0 := sc + Vector3(cos(a0), 0, -sin(a0)) * 330.0
		var p1 := sc + Vector3(cos(a1), 0, -sin(a1)) * 330.0
		_sky_quad(w, [p0 + Vector3(0, -40, 0), p1 + Vector3(0, -40, 0), p1 + Vector3(0, 330, 0), p0 + Vector3(0, 330, 0)], [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)], sky_m)
	for j in 2:
		var rmat := ShaderMaterial.new()
		rmat.shader = load("res://shaders/sky.gdshader")
		rmat.set_shader_parameter("tex", _tex("ridge_far" if j == 0 else "ridge_near"))
		rmat.set_shader_parameter("alpha_cut", 1)
		var rr := 270.0 if j == 0 else 210.0
		var hh := 70.0 if j == 0 else 46.0
		var sh := 0.0 if j == 0 else 0.13
		for i in 12:
			var a0 := TAU * i / 12.0 + sh
			var a1 := TAU * (i + 1) / 12.0 + sh
			var q0 := sc + Vector3(cos(a0), 0, -sin(a0)) * rr
			var q1 := sc + Vector3(cos(a1), 0, -sin(a1)) * rr
			var u0 := fmod(i * 0.41 + j * 0.5, 1.0)
			_sky_quad(w, [q0 + Vector3(0, -30, 0), q1 + Vector3(0, -30, 0), q1 + Vector3(0, hh, 0), q0 + Vector3(0, hh, 0)], [Vector2(u0, 0), Vector2(u0 + 0.5, 0), Vector2(u0 + 0.5, 1), Vector2(u0, 1)], rmat)

func _sky_quad(w: Node, pts: Array, uvs: Array, mat: ShaderMaterial) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for idx in [0, 1, 2, 0, 2, 3]:
		st.set_uv(uvs[idx])
		st.add_vertex(pts[idx])
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mat
	mi.extra_cull_margin = 16384.0
	w.add_child(mi)

func _look(c: Camera3D, origin: Vector3, target: Vector3) -> void:
	c.position = origin
	c.look_at(target, Vector3.UP)

func _place_cameras() -> void:
	# build_lsc.py chase: player root (0,-28,0.16) + (1.4,-7.6,2.94), look (3.6,-6,-0.9)
	_look(cam, _gpos(1.4, -35.6, 3.10), _gpos(3.6, -6.0, -0.9))
	_look(glow_cam, cam.position, _gpos(3.6, -6.0, -0.9))
	# mirror: (0,-28,1.60) looking at (0,-60,-2.2)
	_look(mirror_cam, _gpos(0.0, -32.0, 1.55), _gpos(0.0, -70.0, -2.2))  # 4 m behind the bumper, looking back along the approach

func _load_cars() -> void:
	# Prefer the already-imported two-corner copies if present, else the repo cars.
	var mx5 := "res://cars/car_mx5.glb"
	var s2k := "res://cars/car_s2000.glb"
	var env_m := "res://cars/mx5_env.png" if ResourceLoader.exists("res://cars/mx5_env.png") else "res://art/env_street.png"
	var env_s := "res://cars/s2000_env.png" if ResourceLoader.exists("res://cars/s2000_env.png") else "res://art/env_street.png"
	player = _make_car(mx5, env_m, "mx5", _gpos(0.0, -28.0, 0.16))
	rival = _make_car(s2k, env_s, "s2000", _gpos(LANE_OUT, -16.0, 0.16))

func _make_car(glb: String, env_png: String, id: String, loc: Vector3) -> Node3D:
	var holder := Node3D.new()
	if not ResourceLoader.exists(glb):
		push_warning("missing " + glb)
		world_vp.add_child(holder)
		return holder
	var inst: Node3D = (load(glb) as PackedScene).instantiate()
	holder.add_child(inst)
	var env_tex: Texture2D = load(env_png) as Texture2D
	_shade_car(inst, env_tex, id)
	# Entry heading is world -Z. Two-corner uses yaw = atan2(tx, tz) = PI on this heading
	# (the lean glbs face +Z). PI points the body down the road, rear toward the chase cam.
	holder.rotation.y = PI
	holder.position = loc + Vector3(0, 0.32, 0)  # sit tyres on the 0.18 m road (glb AABB min y ~ -0.29)
	print("CAR ", id, " at ", loc, " added")
	# Blob shadow
	var blob := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(2.3, 5.2)
	blob.mesh = pm
	var bm := StandardMaterial3D.new()
	bm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	bm.albedo_texture = _tex("blob_shadow")
	bm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	bm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	bm.disable_fog = true
	blob.material_override = bm
	blob.position = Vector3(0, 0.02, 0)
	holder.add_child(blob)
	# S2000 lean has no glow FX. Lean glbs face +Z; after yaw=PI the rear faces the chase cam
	# (local -Z). MX5 keeps its own FX_LampGlow from the glb.
	if id == "s2000":
		for x in [-0.66, 0.66]:
			var th := _glow("glow_tail", 0.75, 0.65)
			th.position = Vector3(x, 0.76, -2.04)
			holder.add_child(th)
			var hd := _glow("glow_head", 0.42, 0.20)
			hd.position = Vector3(x, 0.64, 2.10)
			holder.add_child(hd)
	world_vp.add_child(holder)
	return holder


func _aabb_of(n: Node) -> AABB:
	var acc := AABB()
	var first := true
	var stack: Array = [n]
	while stack.size() > 0:
		var x: Node = stack.pop_back()
		if x is MeshInstance3D and (x as MeshInstance3D).mesh != null:
			var mi := x as MeshInstance3D
			var a := mi.global_transform * mi.get_aabb()
			if first:
				acc = a; first = false
			else:
				acc = acc.merge(a)
		for ch in x.get_children():
			stack.append(ch)
	return acc

func _shade_car(n: Node, env_tex: Texture2D, id: String) -> void:
	if n is RigidBody3D:
		var rb := n as RigidBody3D
		rb.freeze = true
		rb.freeze_mode = RigidBody3D.FREEZE_MODE_STATIC
		rb.gravity_scale = 0.0
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		if String(mi.name).contains("FX_LampGlow"):
			mi.layers = 3
			mi.visible = true
		elif mi.mesh != null:
			for si in mi.mesh.get_surface_count():
				var src := mi.get_active_material(si)
				var m := ShaderMaterial.new()
				m.shader = load("res://shaders/car_simple.gdshader")
				var tex: Texture2D = (src as BaseMaterial3D).albedo_texture if src is BaseMaterial3D else null
				if tex == null and src is BaseMaterial3D:
					# some lean surfaces use the material name only; keep the imported albedo_color visible
					pass
				m.set_shader_parameter("albedo_tex", tex)
				m.set_shader_parameter("has_tex", tex != null)
				m.set_shader_parameter("env_equirect", env_tex)
				var nm := src.resource_name if src != null else ""
				var is_glass := nm.contains("Glass")
				var is_paint := nm.contains("Paint")
				var is_lamp := nm.contains("Lamp")
				m.set_shader_parameter("tint", Vector3(0.45, 0.6, 0.75) if is_glass else Vector3(1, 1, 1))
				m.set_shader_parameter("env_tint", Vector3(0.80, 0.86, 1.0))
				var bc: Color = (src as BaseMaterial3D).albedo_color if src is BaseMaterial3D else Color(0.6, 0.6, 0.6)
				m.set_shader_parameter("base_col", Vector3(bc.r, bc.g, bc.b))
				m.set_shader_parameter("spec_scale", 0.9 if is_glass else (0.55 if is_paint else 0.15))
				m.set_shader_parameter("env_strength", 0.45 if is_glass else (0.22 if id == "mx5" else 0.28))
				m.set_shader_parameter("ambient", 0.5)
				m.set_shader_parameter("spec_power", 48.0)
				m.set_shader_parameter("key_dir", Vector3(-0.35, 0.82, -0.45))  # blender key was (-0.35, 0.45, 0.82) in Y-up? blender Y forward; convert
				m.set_shader_parameter("emissive", is_lamp)
				m.set_shader_parameter("snap_res", Vector2(640, 480))
				m.set_shader_parameter("fog_color", Vector3(FOG.r, FOG.g, FOG.b))
				m.set_shader_parameter("fog_near", FOG_NEAR)
				m.set_shader_parameter("fog_far", FOG_FAR)
				mi.set_surface_override_material(si, m)
	for ch in n.get_children():
		_shade_car(ch, env_tex, id)

func _capture_classic(path: String) -> void:
	var img := bayer_vp.get_texture().get_image()
	if img.get_format() != Image.FORMAT_RGB8:
		img.convert(Image.FORMAT_RGB8)
	img.resize(1280, 960, Image.INTERPOLATE_NEAREST)
	img.save_png(path)
	print("wrote ", path)

func _capture_sharp(path: String) -> void:
	# Bayer the lit 3D (no HUD), 2x nearest, draw sharp HUD on top.
	var vp := _new_vp(Vector2i(640, 480), false, false)
	var bmat := ShaderMaterial.new()
	bmat.shader = load("res://shaders/bayer.gdshader")
	bmat.set_shader_parameter("src", lit_vp.get_texture())
	bmat.set_shader_parameter("res", Vector2(640, 480))
	var br := TextureRect.new()
	br.size = Vector2(640, 480)
	br.stretch_mode = TextureRect.STRETCH_SCALE
	br.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	br.texture = lit_vp.get_texture()
	br.material = bmat
	vp.add_child(br)
	await _settle()
	var native := vp.get_texture().get_image()
	native.resize(1280, 960, Image.INTERPOLATE_NEAREST)
	# blit into a 1280 viewport with sharp HUD
	var hi := _new_vp(Vector2i(1280, 960), false, false)
	var tex := ImageTexture.create_from_image(native)
	var tr := TextureRect.new()
	tr.size = Vector2(1280, 960)
	tr.stretch_mode = TextureRect.STRETCH_SCALE
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.texture = tex
	tr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	hi.add_child(tr)
	var hud := preload("res://hud.gd").new()
	hi.add_child(hud)
	hud.setup("sharp")
	await _settle()
	var out := hi.get_texture().get_image()
	if out.get_format() != Image.FORMAT_RGB8:
		out.convert(Image.FORMAT_RGB8)
	out.save_png(path)
	print("wrote ", path)
	vp.queue_free()
	hi.queue_free()

func _render_all() -> void:
	_set_filter(false)
	await _settle()
	_capture_classic(out_dir.path_join("after_smooth.png"))
	await _capture_sharp(out_dir.path_join("after_smooth_sharpui.png"))
	_set_filter(true)
	await _settle()
	_capture_classic(out_dir.path_join("after_nearest.png"))
	await _capture_sharp(out_dir.path_join("after_nearest_sharpui.png"))
