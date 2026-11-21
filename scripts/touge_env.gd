## TOUGE authored environment (Austin 2026-11-20, AGENTS.md: everything in the world is an authored asset; the road surface stays
## code). Loads Arthur's assets/env/touge/ (README.md there): ten turn sections, the turnout lot ground, three gallery files and
## the always-on backdrop, all at the identity transform around the code road. Materials map by name onto
## res://assets/tex/kit/env/<name>.png (the glbs embed no images); terrain textures run V = metres along s, so they scroll with the
## road like the old procedural bands. Lamp glows (and so the live lights and flares, main.gd _arthur_collect_lamp_records) spawn
## at each lamp_head_### empty.
## Collision: the *_col.glb proxies (terrain / walls / decks) plus the sections' rails and lamp posts (thin) as TriangleMesh BVHs:
## cam_guard.gd clip() and the QTE line of sight, the cedar drop (ground_y) and TERRAIN_CHECK read these, not an analytic model.
## Draw distance: cull() shows a section only when its bounds come within reach of a viewpoint (budget per section ~5-10k tris,
## < 50 draw calls; Arthur's README table: max 6.2k tris / 8 draws).
@tool
extends RefCounted
const ArtKit = preload("res://scripts/art_kit.gd")

const DIR := "res://assets/env/touge/"
const SECTIONS := ["touge_t01", "touge_t02", "touge_t03", "touge_t04", "touge_t05", "touge_t06", "touge_t07", "touge_t08",
	"touge_t09", "touge_t10", "touge_lot", "touge_gallery_a", "touge_gallery_b", "touge_gallery_c"]
const BACKDROP := "touge_backdrop"
## Arthur README material map: V tile (m) and the Cel A soft-surface radius (big surfaces keep smooth light)
const TILE := {"touge_hill": 8.0, "touge_cutface": 8.0, "touge_cutrock": 8.0, "touge_gravel": 4.0, "touge_concrete": 4.0, "asphalt": 8.0}
const SOFT := {"touge_hill": 8.0, "touge_cutface": 8.0, "touge_cutrock": 6.0, "touge_gravel": 4.0, "touge_concrete": 5.0, "asphalt": 10.0}
const THIN_MATS := ["touge_guardrail", "emit_reflector", "lamp_post"]   # camera clearance only (not terrain: no inside / LOS depth)

var root: Node3D
var glows: Node3D
var sections: Array = []     # {name, node, aabb, tris, draws}
var backdrop: Node3D
var lamp_heads: Array = []   # Vector3, world
var stats := {}

## ── build: instance every file under parent, map materials, glow sprites at the lamp heads ──
func build(art, parent: Node3D) -> void:
	root = Node3D.new(); root.name = "AuthoredEnv"; parent.add_child(root)
	glows = Node3D.new(); glows.name = "AuthoredLampGlows"; parent.add_child(glows)   # code-placed glow sprites (not terrain)
	var mats := {}
	var tt := 0; var dd := 0
	for nm in SECTIONS + [BACKDROP]:
		var ps: PackedScene = load(DIR + nm + ".glb")
		var inst: Node3D = ps.instantiate(); inst.name = nm; root.add_child(inst)
		var rec := {"name": nm, "node": inst, "aabb": AABB(), "tris": 0, "draws": 0}
		var first := true
		for mi in inst.find_children("*", "MeshInstance3D", true, false):
			var m3 := mi as MeshInstance3D
			m3.extra_cull_margin = 16384.0   # one draw per surface; frustum culling is ours (cull), the bounds are world-sized
			var ab: AABB = m3.transform * m3.mesh.get_aabb()
			rec.aabb = ab if first else (rec.aabb as AABB).merge(ab); first = false
			for si in m3.mesh.get_surface_count():
				var il: int = m3.mesh.surface_get_array_index_len(si)
				rec.tris += (il if il > 0 else m3.mesh.surface_get_array_len(si)) / 3; rec.draws += 1
				var src: Material = m3.mesh.surface_get_material(si)
				var mn: String = src.resource_name if src != null else ""
				if not mats.has(mn): mats[mn] = _mat(art, mn)
				m3.set_surface_override_material(si, mats[mn])
		for e in inst.find_children("lamp_head_*", "Node3D", true, false):
			var hp: Vector3 = (e as Node3D).transform.origin
			var par := (e as Node3D).get_parent() as Node3D
			while par != null and par != inst: hp = par.transform * hp; par = par.get_parent() as Node3D
			lamp_heads.append(hp)
			var gl: MeshInstance3D = art.glow_sprite("glow_lamp", Color(1, 1, 1), 1.5, 0.9)   # as the code lamps: 1.5 m billboard, 0.9
			gl.name = "LampGlow_%s" % e.name; gl.position = hp; glows.add_child(gl)
		tt += int(rec.tris); dd += int(rec.draws)
		if nm == BACKDROP: backdrop = inst
		else: sections.append(rec)
	stats = {"files": SECTIONS.size() + 1, "tris": tt, "draws": dd, "lamps": lamp_heads.size(), "materials": mats.keys()}

func _mat(art, mn: String) -> Material:
	var key := mn.to_lower()
	if key == "lamp_post": return art.env_mat   # env_vertex_lit: vertex colour = albedo, luma >= 0.5 head = full bright
	var m := ShaderMaterial.new(); m.shader = ArtKit.SCROLL_SH
	var tp := "res://assets/tex/kit/env/%s.png" % key
	m.set_shader_parameter("tex", load(tp) if ResourceLoader.exists(tp) else null)
	m.set_shader_parameter("tile", float(TILE.get(key, 1.0))); m.set_shader_parameter("scroll_m", 0.0)
	if TILE.has(key): m.set_meta("scrolls", true)   # terrain: V = course s, scrolls with the road (README); rails stay put
	if key.begins_with("emit_"): m.set_shader_parameter("cel_k", 0.0); m.set_shader_parameter("flatten", 0.0)
	if SOFT.has(key):
		m.set_shader_parameter("soft_surface", 1.0); m.set_shader_parameter("soft_radius", float(SOFT[key])); m.set_shader_parameter("soft_clamp_u", 0.0)
	return art.fogify(m)

## ── draw distance: a section is drawn when its bounds come within reach of any viewpoint (camera, mirror / player car) ──
func cull(points: Array, reach: float) -> Dictionary:
	var vt := 0; var vd := 0; var vn := 0
	for r in sections:
		var ab: AABB = r.aabb; var on := false
		for p in points:
			var q: Vector3 = p
			var c := Vector3(clampf(q.x, ab.position.x, ab.end.x), clampf(q.y, ab.position.y, ab.end.y), clampf(q.z, ab.position.z, ab.end.z))
			if c.distance_to(q) <= reach: on = true; break
		(r.node as Node3D).visible = on
		if on: vt += int(r.tris); vd += int(r.draws); vn += 1
	return {"sections": vn, "tris": vt, "draws": vd}

func show_all() -> void:
	for r in sections: (r.node as Node3D).visible = true

## ── collision (static, built once per run) ──
static var _col: TriangleMesh = null
static var _coln: PackedVector3Array      # per-face outward normal (from the vertex normals: TriangleMesh hits are two-sided)
static var _thin: TriangleMesh = null
static var _col_tris := 0; static var _thin_tris := 0

static func col_ready() -> bool:
	if _col != null: return true
	var faces := []; var nrm := []
	for nm in SECTIONS:
		var ps: PackedScene = load(DIR + nm + "_col.glb")
		if ps == null: continue
		var inst: Node3D = ps.instantiate()
		for mi in inst.find_children("*", "MeshInstance3D", true, false):
			_append(mi as MeshInstance3D, inst, faces, nrm, [])
		inst.free()
	_col = TriangleMesh.new(); _col.create_from_faces(PackedVector3Array(faces)); _col_tris = faces.size() / 3
	_coln = PackedVector3Array(nrm)
	var tf := []; var tn := []
	for nm in SECTIONS:
		var inst: Node3D = (load(DIR + nm + ".glb") as PackedScene).instantiate()
		for mi in inst.find_children("*", "MeshInstance3D", true, false):
			_append(mi as MeshInstance3D, inst, tf, tn, THIN_MATS)
		inst.free()
	_thin = TriangleMesh.new(); _thin.create_from_faces(PackedVector3Array(tf)); _thin_tris = tf.size() / 3
	return true

## faces of mi (in inst space) appended to out (+ one outward normal per face to nout); only surfaces whose material is in
## only (empty = all)
static func _append(mi: MeshInstance3D, inst: Node3D, out: Array, nout: Array, only: Array) -> void:
	var xf := mi.transform; var par := mi.get_parent() as Node3D
	while par != null and par != inst: xf = par.transform * xf; par = par.get_parent() as Node3D
	for si in mi.mesh.get_surface_count():
		if not only.is_empty():
			var src: Material = mi.mesh.surface_get_material(si)
			var mn: String = String(src.resource_name).to_lower() if src != null else ""
			if not only.has(mn): continue
		var arr: Array = mi.mesh.surface_get_arrays(si)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var nv: PackedVector3Array = arr[Mesh.ARRAY_NORMAL] if arr[Mesh.ARRAY_NORMAL] != null else PackedVector3Array()
		var ids: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		if ids.is_empty(): ids = PackedInt32Array(range(v.size()))
		for k in range(0, ids.size() - 2, 3):
			for j in 3: out.append(xf * v[ids[k + j]])
			if nv.size() == v.size(): nout.append((xf.basis * (nv[ids[k]] + nv[ids[k + 1]] + nv[ids[k + 2]])).normalized())
			else: nout.append(Vector3.UP)

const DIRS := [Vector3(1, 0, 0), Vector3(-1, 0, 0), Vector3(0, 1, 0), Vector3(0, -1, 0), Vector3(0, 0, 1), Vector3(0, 0, -1),
	Vector3(0.577, 0.577, 0.577), Vector3(-0.577, 0.577, 0.577), Vector3(0.577, 0.577, -0.577), Vector3(-0.577, 0.577, -0.577),
	Vector3(0.577, -0.577, 0.577), Vector3(-0.577, -0.577, 0.577), Vector3(0.577, -0.577, -0.577), Vector3(-0.577, -0.577, -0.577)]

## nearest hit of the 14-direction probe within r (approximate distance to the surface); 1e9 = none
static func _probe(tm: TriangleMesh, p: Vector3, r: float) -> float:
	var best := 1e9
	for d in DIRS:
		var h: Dictionary = tm.intersect_segment(p, p + d * r)
		if not h.is_empty(): best = minf(best, p.distance_to(h.position))
	return best

## the first terrain surface straight above p: [height above p, outward normal]; [] = open sky
static func _above(p: Vector3) -> Array:
	var h: Dictionary = _col.intersect_ray(p, Vector3.UP)
	if h.is_empty(): return []
	return [float(h.position.y) - p.y, _coln[int(h.face_index)]]

## penetration of the sphere (radius margin) round p into the authored geometry, cam_guard convention: > 0 = clips. Under
## ground (the first terrain surface above p faces up: we are below it, not under a deck soffit or an overhang wall) = margin +
## the depth to that surface, so a sight line through a hill reads metres of terrain; a thin part (rail, lamp post) adds at
## most margin.
static func clip(p: Vector3, margin: float) -> float:
	col_ready()
	var pen := -1e9
	var ab: Array = _above(p)
	if not ab.is_empty() and (ab[1] as Vector3).y > 0.0:
		return margin + float(ab[0])
	var dn := _probe(_col, p, margin)
	if dn < 1e8: pen = maxf(pen, margin - dn)
	var dt := _probe(_thin, p, margin)
	if dt < 1e8: pen = maxf(pen, margin - dt)
	return pen

## highest up-facing terrain surface under (x, top, z) (cedar foot); NAN = none within depth
static func ground_y(x: float, z: float, top: float, depth := 80.0) -> float:
	col_ready()
	var p := Vector3(x, top, z)
	for k in 4:   # step down past soffits / overhang undersides
		var h: Dictionary = _col.intersect_segment(p, Vector3(x, top - depth, z))
		if h.is_empty(): return NAN
		if _coln[int(h.face_index)].y > 0.2: return float(h.position.y)
		p = Vector3(x, float(h.position.y) - 0.05, z)
	return NAN

## first terrain hit on a -> b (TERRAIN-only line of sight); {} = clear
static func seg_hit(a: Vector3, b: Vector3) -> Dictionary:
	col_ready()
	return _col.intersect_segment(a, b)

static func col_faces() -> PackedVector3Array:
	col_ready()
	return _col.get_faces()
