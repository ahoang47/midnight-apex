## Shared stand-in art builders (art_direction Part B recipes; textures from spec/gen_art.py). Moved verbatim out of main.gd
## (scene refactor, 2026-11-12) so the @tool scenes (track.tscn, touge_dressing.tscn, sky.tscn, car.tscn) build the same meshes
## and materials in the editor that the game builds at runtime. One instance per running game (main.gd owns it); each @tool
## scene makes its own in the editor. Every number comes from spec/display.json or was already in main.gd before the move.
@tool
extends RefCounted
const ENV_SH = preload("res://shaders/env.gdshader")
const SCROLL_SH = preload("res://shaders/scroll.gdshader")
const GLOW_SH = preload("res://shaders/glow.gdshader")

var disp: Dictionary
var DIST: Dictionary
var PAL: Dictionary
var road_W := 5.5
var env_mat: ShaderMaterial
var tex_cache := {}
var card_mats := {}
var scroll_mats: Array[ShaderMaterial] = []
var glow_mats: Array[ShaderMaterial] = []
var LAMP_MESH: ArrayMesh
var GLOW_QUAD: QuadMesh

func _init(d: Dictionary) -> void:
	disp = d; DIST = d.districts; PAL = d.palette
	road_W = float(d.lane_width_m) * 1.5 + 1.0
	env_mat = ShaderMaterial.new(); env_mat.shader = ENV_SH
	env_mat.set_shader_parameter("snap_res", Vector2(int(d.render.internal_w), int(d.render.internal_h)))

static func load_json(p: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(p))

func tex(n: String) -> Texture2D:
	if not tex_cache.has(n): tex_cache[n] = load("res://art/%s.png" % n)
	return tex_cache[n]

func fogify(m: ShaderMaterial) -> ShaderMaterial:
	scroll_mats.append(m); m.set_shader_parameter("snap_res", Vector2(disp.render.internal_w, disp.render.internal_h))
	return m

## strip material: v = (metres along + scroll) / tile -> scrolls with the RoadScroller (§14.2)
func strip_mat(n: String, tile: float) -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = SCROLL_SH
	m.set_shader_parameter("tex", tex(n)); m.set_shader_parameter("tile", tile)
	m.set_meta("scrolls", true)
	return fogify(m)

## cut-out card material (static UVs)
func card_mat(n: String) -> ShaderMaterial:
	if not card_mats.has(n):
		var m := ShaderMaterial.new(); m.shader = SCROLL_SH
		m.set_shader_parameter("tex", tex(n)); m.set_shader_parameter("tile", 1.0); m.set_shader_parameter("scroll_m", 0.0)
		card_mats[n] = fogify(m)
	return card_mats[n]

## before a rebuild: keep only the cached card materials, forget the glow materials (main.gd _build_road)
func reset_for_rebuild() -> void:
	scroll_mats = scroll_mats.filter(func(m): return card_mats.values().has(m))
	glow_mats.clear()

func glow_sprite(n: String, col: Color, size: float, strength: float) -> MeshInstance3D:
	if GLOW_QUAD == null: GLOW_QUAD = QuadMesh.new(); GLOW_QUAD.size = Vector2(1, 1)
	var m := ShaderMaterial.new(); m.shader = GLOW_SH
	m.set_shader_parameter("tex", tex(n)); m.set_shader_parameter("color", Vector3(col.r, col.g, col.b))
	m.set_shader_parameter("strength", strength); m.set_shader_parameter("size", Vector2(size, size))
	m.set_shader_parameter("snap_res", Vector2(disp.render.internal_w, disp.render.internal_h)); m.render_priority = 5
	glow_mats.append(m)
	var mi := MeshInstance3D.new(); mi.mesh = GLOW_QUAD; mi.material_override = m; mi.extra_cull_margin = 16384.0
	mi.layers = 3  # main view + glow-only bloom pass
	return mi

static func pp(pth, s: float, d: float, y: float = 0.0) -> Vector3:
	var q: Dictionary = pth.point(s, d)
	return Vector3(q.x, y, q.z)

## one strip along pth, tessellated across/up (keeps affine warping readable); UV.x 0..1 across/up, UV.y = metres along
func strip(pth, s0: float, s1: float, d0: float, d1: float, mat: ShaderMaterial, wall := 0.0, y := 0.0) -> MeshInstance3D:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var nc: int = maxi(1, ceili((wall if wall > 0.0 else absf(d1 - d0)) / 3.0))
	var rows: Array = []
	var s := s0
	while s <= s1 + 1e-6:
		var row: Array = []
		for j in nc + 1:
			var u := float(j) / nc
			var p: Vector3 = pp(pth, s, d0, y + wall * u) if wall > 0.0 else pp(pth, s, d0 + (d1 - d0) * u, y)
			row.append([p, Vector2(u, s)])
		rows.append(row); s += 2.0
	for i in range(1, rows.size()):
		for j in nc:
			var q := [rows[i - 1][j], rows[i][j], rows[i - 1][j + 1], rows[i - 1][j + 1], rows[i][j], rows[i][j + 1]]
			for v in q:
				st.set_uv(v[1]); st.add_vertex(v[0])
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat; mi.extra_cull_margin = 16384.0
	return mi

## card: w x h quad standing on y (plane = across/up, facing along the road). Godot UV v runs top-down.
func card(n: String, w: float, h: float, y := 0.0) -> MeshInstance3D:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var v := [[Vector3(-w / 2, y, 0), Vector2(0, 1)], [Vector3(w / 2, y, 0), Vector2(1, 1)], [Vector3(-w / 2, y + h, 0), Vector2(0, 0)], [Vector3(w / 2, y + h, 0), Vector2(1, 0)]]
	for i in [0, 2, 1, 1, 2, 3]:
		st.set_uv(v[i][1]); st.add_vertex(v[i][0])
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = card_mat(n); mi.extra_cull_margin = 16384.0
	return mi

func cross_card(n: String, w: float, h: float) -> Node3D:
	var g := Node3D.new(); var a := card(n, w, h); var b := card(n, w, h); b.rotation.y = PI / 2
	g.add_child(a); g.add_child(b); return g

## lamp: post + arm + head, unlit vertex colour (B.1); same numbers as Three.js lampGeo
func lamp_mesh() -> ArrayMesh:
	if LAMP_MESH != null: return LAMP_MESH
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var h := 6.5; var pc := Color(0.16, 0.16, 0.18)
	quad(st, Vector3(-0.1, 0, 0), Vector3(0.1, 0, 0), Vector3(-0.1, h, 0), Vector3(0.1, h, 0), pc)
	quad(st, Vector3(0, h - 0.1, 0), Vector3(-1.4, h - 0.1, 0), Vector3(0, h + 0.05, 0), Vector3(-1.4, h + 0.05, 0), pc)
	quad(st, Vector3(-1.0, h - 0.25, 0), Vector3(-1.6, h - 0.25, 0), Vector3(-1.0, h, 0), Vector3(-1.6, h, 0), Color(PAL.lamp))  # emissive head: B.2a #F0C894
	LAMP_MESH = st.commit()
	return LAMP_MESH

static func quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, col: Color) -> void:
	for v in [a, c, b, b, c, d]:
		st.set_color(col); st.add_vertex(v)

## display-only pattern, not the sim RNG (identical to track.js hash)
static func hash01(k: float) -> float:
	var x := sin(k * 127.1 + 311.7) * 43758.5453
	return x - floor(x)

func decal(n: String, w: float, l: float, z: float, additive: bool, strength: float) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(w, l); mi.mesh = pm
	var m := StandardMaterial3D.new(); m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; m.albedo_texture = tex(n)
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR; m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = Color(1, 1, 1, strength); m.disable_fog = true; m.render_priority = 1
	if additive: m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mi.material_override = m; mi.position = Vector3(0, 0.03, z)
	return mi

## district fog on every material this kit made (+ extra, e.g. car materials); main.gd _apply_district, editor previews
func apply_fog(dk: String, extra: Array = []) -> void:
	var D: Dictionary = DIST[dk]; var fc := Color(D.fog)
	var fv := Vector3(fc.r, fc.g, fc.b)
	for m in scroll_mats + extra + [env_mat]:
		m.set_shader_parameter("fog_color", fv); m.set_shader_parameter("fog_near", float(D.fog_near)); m.set_shader_parameter("fog_far", float(D.fog_far))
	for m in glow_mats:
		m.set_shader_parameter("fog_near", float(D.fog_near)); m.set_shader_parameter("fog_far", float(D.fog_far))
