## WANGAN (Arthur, unapproved experiment, Austin 2026-11-15): the elevated bayshore expressway kit for the two-corner
## playtest, built in the same shape as Gordon's touge_dressing.gd (one dressing per road strip, props streamed with the
## RoadScroller so they stay on the sodium pools painted into env/wangan_road.png).
##   deck (per strip): cast parapets on both edges (the Blender module bent onto the course, so the sweepers get a
##   continuous curved wall), deck fascia + soffit, tall sodium lamps staggered 24 m with arms over the lanes, a pier under
##   every expansion joint, km posts, overhead sign gantries, sodium streaks on the water under the lamps.
##   static (once): bay water plane, far city towers across the bay, harbour cranes, a cable-stayed bridge.
## Props are glTF from ../blender/build_wangan.py, re-shaded unlit through the cel scroll shader. Every material name maps to
## res://assets/tex/kit/env/<name>.png; Emit_* surfaces are full-bright (no toon bands, no flatten).
extends RefCounted
const ArtKit = preload("res://scripts/art_kit.gd")
const TrackRoad = preload("res://scripts/track_road.gd")
const CEL_BIT_DECAL := 1 << 17   # layer 18: seen by the colour cameras, never by the ink G-buffer (decals are never inked)

static var _scenes := {}
static var _mats := {}
static var _parapet_src: Array = []   # [positions, uvs] of the Blender parapet module (Godot axes: x away from road, y up, z forward)

static func _scene(n: String) -> PackedScene:
	if not _scenes.has(n): _scenes[n] = load("res://assets/env/%s.glb" % n)
	return _scenes[n]

## unlit cel material for one glTF material name (cached per art kit, so _apply_district finds them in art.scroll_mats)
static func prop_mat(art, nm: String) -> ShaderMaterial:
	var key := "%d|%s" % [art.get_instance_id(), nm]
	if _mats.has(key): return _mats[key]
	var m := ShaderMaterial.new(); m.shader = ArtKit.SCROLL_SH
	m.set_shader_parameter("tex", art.tex("env/" + nm.to_lower()))
	m.set_shader_parameter("tile", 1.0); m.set_shader_parameter("scroll_m", 0.0)
	if nm.begins_with("Emit_"):
		m.set_shader_parameter("cel_k", 0.0); m.set_shader_parameter("flatten", 0.0)   # lamp heads, windows, aviation lights: full-bright, crisp
	elif nm.begins_with("wangan_sign") or nm == "wangan_kpost":
		m.set_shader_parameter("flatten", 0.0)   # keep the sign lettering crisp (toon bands still apply)
	m.set_meta("persist", true); art.fogify(m); _mats[key] = m
	return m

static func _shade(art, n: Node) -> void:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		for si in mi.mesh.get_surface_count():
			var src := mi.get_active_material(si)
			mi.set_surface_override_material(si, prop_mat(art, src.resource_name if src != null else "wangan_galv"))
		mi.extra_cull_margin = 16384.0
	for ch in n.get_children(): _shade(art, ch)

static func prop(art, n: String) -> Node3D:
	var inst: Node3D = _scene(n).instantiate()
	_shade(art, inst)
	return inst

static func tri_count(n: Node) -> int:
	var t := 0
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		var m: Mesh = (n as MeshInstance3D).mesh
		for i in m.get_surface_count():
			var a := m.surface_get_arrays(i); var idx = a[Mesh.ARRAY_INDEX]
			t += (idx.size() if idx != null and idx.size() > 0 else (a[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()) / 3
	for ch in n.get_children(): t += tri_count(ch)
	return t

static func _parapet_module() -> Array:
	if not _parapet_src.is_empty(): return _parapet_src
	var inst: Node3D = _scene("wangan_parapet").instantiate()
	var mi: MeshInstance3D = inst.find_children("*", "MeshInstance3D", true, false)[0] if not (inst is MeshInstance3D) else inst
	var a := mi.mesh.surface_get_arrays(0)
	var xf: Transform3D = mi.transform if mi != inst else Transform3D.IDENTITY
	var pos: PackedVector3Array = a[Mesh.ARRAY_VERTEX]; var uv: PackedVector2Array = a[Mesh.ARRAY_TEX_UV]; var idx = a[Mesh.ARRAY_INDEX]
	var P := []; var U := []
	var order: Array = range(pos.size()) if idx == null or idx.size() == 0 else Array(idx)
	for i in order: P.append(xf * pos[i]); U.append(uv[i])
	inst.free()
	_parapet_src = [P, U]
	return _parapet_src

## the parapet module repeated every 4 m along pth on one side and bent onto the path (continuous wall through the
## sweepers, no gaps between straight blocks). UV.x = around the profile (Blender), UV.y = metres along -> strip_mat tile 4.
static func parapet(art, pth, a0: float, a1: float, side: float, d_face: float) -> MeshInstance3D:
	var src := _parapet_module(); var P: Array = src[0]; var U: Array = src[1]
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var s := a0 + 2.0
	while s < a1:
		var tri := []
		for i in P.size():
			var v: Vector3 = P[i]; var sv: float = s + v.z
			tri.append([ArtKit.pp(pth, sv, side * (d_face + v.x), v.y), Vector2(U[i].x, sv)])
			if tri.size() == 3:
				if side < 0.0: tri.reverse()
				for t in tri: st.set_uv(t[1]); st.add_vertex(t[0])
				tri = []
		s += 4.0
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.extra_cull_margin = 16384.0
	mi.material_override = art.strip_mat("env/wangan_parapet", 4.0)
	return mi

static func _streak(art, w: float, l: float, strength: float) -> MeshInstance3D:
	var mi: MeshInstance3D = art.decal("env/wangan_streak", w, l, 0.0, true, strength)
	mi.layers = CEL_BIT_DECAL
	return mi

## {group, items, a0, range, pth}: same contract as touge_dressing.build. opts: {"gantries": [s, ...]}
static func build(art, pth, s0: float, s1: float, nm: String, opts: Dictionary = {}) -> Dictionary:
	var D: Dictionary = art.DIST["wangan"]; var per: float = D.lamp_period_m; var W: float = art.road_W
	var g := Node3D.new(); g.name = nm; var items: Array = []
	var sp := TrackRoad.span(D, s0, s1); var a0: float = sp[0]; var rng: float = sp[1]
	var add := func(obj: Node3D, base: float, d: float, y := 0.0, yaw := 0.0) -> void:
		g.add_child(obj); items.append({"obj": obj, "base": base, "d": d, "y": y, "yaw": yaw})
	var pd: float = D.parapet_d_m; var de: float = D.deck_edge_d_m; var soff: float = D.soffit_y_m
	for sd in [-1.0, 1.0]:
		var pm := parapet(art, pth, a0, a0 + rng, sd, pd); pm.name = "Parapet%s" % ("L" if sd < 0 else "R"); g.add_child(pm)
		var fas: MeshInstance3D = art.band(pth, a0, a0 + rng, sd * de, -0.95, sd * de, soff, art.strip_mat("env/wangan_fascia", 6.0))
		fas.name = "Fascia%s" % ("L" if sd < 0 else "R"); g.add_child(fas)
		var lip: MeshInstance3D = art.band(pth, a0, a0 + rng, sd * (pd + 0.5), -0.95, sd * de, -0.95, art.strip_mat("env/wangan_fascia", 6.0))
		g.add_child(lip)
	var sof: MeshInstance3D = art.band(pth, a0, a0 + rng, -de, soff, de, soff, art.strip_mat("env/wangan_underside", 4.0), 4.0, 4)
	sof.name = "Soffit"; g.add_child(sof)
	for n in int(rng / per):
		for L in D.lamps:   # wangan_lamp: built for the left edge (+X away from the road); the right side is mirrored (scale.x -1)
			var side: float = L[1]
			var lamp := Node3D.new()
			var p := prop(art, "wangan_lamp"); lamp.add_child(p)
			var gl: MeshInstance3D = art.glow_sprite("glow_lamp", Color(1, 1, 1), 2.0, 0.85); gl.position = Vector3(-4.5, 11.6, 0); lamp.add_child(gl)
			var stk := _streak(art, 3.0, 14.0, 0.16); stk.position = Vector3(6.5, float(D.water_y_m) + 0.05, 4.0); lamp.add_child(stk)   # faint sodium smear on the bay under the deck edge
			lamp.scale.x = -side   # course d > 0 (right) = node local -X
			add.call(lamp, a0 + n * per + float(L[0]), side * (pd + 0.25))
		var pier := prop(art, "wangan_pier")
		add.call(pier, a0 + n * per + float(D.pier_s_m), 0.0)
		var kp := prop(art, "wangan_kpost")
		add.call(kp, a0 + n * per + float(D.kpost_s_m), -(pd + 0.05))
	for gs in opts.get("gantries", []):
		var gt := prop(art, "wangan_gantry")
		add.call(gt, float(gs), 0.0)
	return {"group": g, "items": items, "a0": a0, "range": rng, "pth": pth}

## static far dressing, built once around the course: the bay water (follows the camera in whole tiles so its texture stays
## world-locked), towers along the far shore, harbour cranes, the bay bridge, and dim sodium streaks under the towers.
static func build_static(art, course, parent: Node) -> Dictionary:
	var D: Dictionary = art.DIST["wangan"]
	var g := Node3D.new(); g.name = "WanganFar"; parent.add_child(g)
	# water: 1536 m square, 48 m cells, UV.x = x / 48 (tile across), UV.y = z metres (tile 48 along)
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var half := 768.0; var cell := 48.0; var n := int(2 * half / cell); var y: float = D.water_y_m
	for i in n:
		for j in n:
			var x0 := -half + i * cell; var z0 := -half + j * cell
			var q := [Vector3(x0, y, z0), Vector3(x0 + cell, y, z0), Vector3(x0, y, z0 + cell), Vector3(x0 + cell, y, z0 + cell)]
			for k in [0, 2, 1, 1, 2, 3]:
				st.set_uv(Vector2(q[k].x / cell, q[k].z)); st.add_vertex(q[k])
	var water := MeshInstance3D.new(); water.name = "Bay"; water.mesh = st.commit(); water.extra_cull_margin = 16384.0
	var wm: ShaderMaterial = art.strip_mat("env/wangan_water", cell); wm.remove_meta("scrolls"); wm.set_meta("persist", true)
	water.material_override = wm; g.add_child(water)
	# far set pieces, placed in course-frame terms (s along, d lateral; d < 0 = left of the first straight) so they sit across
	# the bay whatever the corner radii are
	var far := Node3D.new(); far.name = "FarSet"; g.add_child(far)
	var put := func(n_: String, s: float, d: float, yy: float, yaw: float, sc := 1.0) -> Node3D:
		var q: Dictionary = course.point(s, d)
		var o := prop(art, n_); o.position = Vector3(q.x, yy, q.z); o.rotation.y = atan2(q.tx, q.tz) + yaw; o.scale = Vector3.ONE * sc
		far.add_child(o); return o
	# the city: a low band of towers on the far shore to the left / ahead of the first sweeper
	var towers := [[60.0, -230.0, -46.0], [120.0, -260.0, -40.0], [175.0, -215.0, -52.0], [240.0, -270.0, -36.0], [300.0, -240.0, -48.0],
		[20.0, -300.0, -30.0], [360.0, -300.0, -34.0], [205.0, -330.0, -26.0], [420.0, -250.0, -44.0], [90.0, -340.0, -24.0]]
	for k in towers.size():
		var t: Array = towers[k]
		var o: Node3D = put.call("wangan_tower_%d" % (k % 3), t[0], t[1], t[2], ArtKit.hash01(k * 1.3) * 0.8, 0.9)
		var stk := _streak(art, 14.0, 70.0, 0.10); stk.position = Vector3(o.position.x, y + 0.08, o.position.z + 0.0); stk.rotation.y = o.rotation.y; g.add_child(stk)
	# harbour cranes on the right-hand quay, booms out over the water
	for c in [[150.0, 260.0, 0.6], [185.0, 275.0, 0.5], [230.0, 255.0, 0.7], [520.0, 300.0, 0.45]]:
		put.call("wangan_crane", c[0], c[1], y, PI * 0.5 + c[2])
	# the bay bridge, ahead across the water after corner 2 (spans left-right of the far exit)
	put.call("wangan_bridge", course.length + 260.0, -40.0, y, PI * 0.5 + 0.25)
	return {"group": g, "water": water}
