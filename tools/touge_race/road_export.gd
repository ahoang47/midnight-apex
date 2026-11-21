## Export the live Touge course road for Arthur (Blender terrain authoring).
## Writes unapproved/gordon/road_export/road_surface.glb, road_centreline.json, README.md.
## Usage (from the project root):
##   godot --headless --path . --script tools/touge_race/road_export.gd
##   godot --headless --path . --script tools/touge_race/road_export.gd -- --out DIR --display res://spec/display.json --config res://spec/race_config.json
## Does not edit course.gd / dressing. Reads the current worktree as the game builds it.
extends SceneTree

const ArtKit = preload("res://scripts/art_kit.gd")
const TrackRoad = preload("res://scripts/track_road.gd")
const Course = preload("res://scripts/course.gd")
const Dressing = preload("res://scripts/touge_dressing.gd")

const DEFAULT_OUT := "res://unapproved/gordon/road_export"

func _initialize() -> void:
	var ua := OS.get_cmdline_user_args()
	var dpath := "res://spec/display.json"
	if ua.has("--display"): dpath = ua[ua.find("--display") + 1]
	var cpath := "res://spec/race_config.json"
	if ua.has("--config"): cpath = ua[ua.find("--config") + 1]
	var out_res := DEFAULT_OUT
	if ua.has("--out"): out_res = ua[ua.find("--out") + 1]
	if not out_res.begins_with("res://") and not out_res.begins_with("/"):
		out_res = "res://" + out_res.trim_prefix("./")

	var disp: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(dpath))
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(cpath))
	var art: ArtKit = ArtKit.new(disp)
	var tr: Dictionary = TrackRoad.build_course(disp, cfg)
	var course = tr.course
	var views: Array = tr.views
	var turnout: Dictionary = tr.turnout
	var W: float = art.road_W
	var D: Dictionary = art.DIST["touge"]
	var s_lo := -60.0
	var s_hi: float = course.length + 60.0

	var out_dir := ProjectSettings.globalize_path(out_res) if out_res.begins_with("res://") else out_res
	DirAccess.make_dir_recursive_absolute(out_dir)
	var glb_path := out_dir.path_join("road_surface.glb")
	var json_path := out_dir.path_join("road_centreline.json")
	var readme_path := out_dir.path_join("README.md")

	# Exact in-game CourseRoad (track_road.build_strip / main.gd _build_road).
	var src_mi: MeshInstance3D = _build_course_road(art, course, s_lo, s_hi)
	var src_stats := _mesh_stats(src_mi.mesh, Transform3D.IDENTITY)
	print("ROAD_EXPORT source verts=%d tris=%d aabb=%s" % [src_stats.verts, src_stats.tris, _aabb_s(src_stats.aabb)])

	var turn_ranges := _turn_ranges(views, s_lo, s_hi)
	var parts: Array = _split_road_by_turn(src_mi.mesh, turn_ranges, art, D)   # [{name, mesh, seam_verts}]
	var seam_extra := 0
	for p in parts: seam_extra += int(p.seam_verts)

	var export_root := Node3D.new()
	export_root.name = "RoadExport"
	root.add_child(export_root)
	for p in parts:
		var mi := MeshInstance3D.new()
		mi.name = p.name
		mi.mesh = p.mesh
		mi.transform = Transform3D.IDENTITY
		export_root.add_child(mi)

	var lot_stats := {}
	if not turnout.is_empty():
		var lot_mi := _build_lot_floor(course, turnout, W)
		if lot_mi != null:
			lot_mi.transform = Transform3D.IDENTITY
			export_root.add_child(lot_mi)
			lot_stats = _mesh_stats(lot_mi.mesh, Transform3D.IDENTITY)
			print("ROAD_EXPORT lot_floor verts=%d tris=%d aabb=%s" % [lot_stats.verts, lot_stats.tris, _aabb_s(lot_stats.aabb)])

	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_scene(export_root, state)
	if err != OK:
		push_error("ROAD_EXPORT append_from_scene failed: %s" % err)
		quit(1); return
	err = doc.write_to_filesystem(state, glb_path)
	if err != OK:
		push_error("ROAD_EXPORT write_to_filesystem failed: %s" % err)
		quit(1); return

	var ver := _verify_glb(glb_path, src_stats, seam_extra)
	print("ROAD_EXPORT glb_road verts=%d tris=%d aabb=%s seam_extra=%d" % [ver.verts, ver.tris, _aabb_s(ver.aabb), seam_extra])
	print("ROAD_EXPORT verify verts_match=%s (src=%d glb=%d expected=%d) aabb_match=%s aabb_max_delta=%.6f" % [
		str(ver.verts_match), src_stats.verts, ver.verts, src_stats.verts + seam_extra,
		str(ver.aabb_match), ver.aabb_delta])

	# Dressing at scroll 0: lamp / rail poses as the game places them, plus terrain counts.
	var ref := {"lamps": [], "rails": [], "galleries": []}
	var terrain_counts := {}
	var dress: Node = Dressing.new()
	root.add_child(dress)
	var dd: Dictionary = dress.build(art, course, s_lo, s_hi, "touge", "CourseDressing", {"turnout": turnout})
	Dressing.stream(dd, 0.0)
	ref.lamps = _collect_lamps(dd, course)
	ref.rails = _collect_rails(dd, course, W)
	ref.galleries = _gallery_extents(course, s_lo, s_hi, W, D)
	terrain_counts = _terrain_counts(dd.get("group") as Node, course, turn_ranges, W)
	print("ROAD_EXPORT lamps=%d rails_visible=%d rails_total=%d galleries=%d" % [
		ref.lamps.size(),
		ref.rails.filter(func(r): return bool(r.visible)).size(),
		ref.rails.size(),
		ref.galleries.size()])
	print("ROAD_EXPORT terrain %s" % JSON.stringify(terrain_counts.summary))

	var header := _header(dpath, cpath, disp, cfg, course, W, turn_ranges, turnout, s_lo, s_hi)
	var samples := _samples(course, W, turnout, turn_ranges, s_lo, s_hi, D)
	var expected_n := int(round((s_hi - s_lo) / 1.0)) + 1
	print("ROAD_EXPORT centreline samples=%d course_length_m=%.3f dressed=%.1f..%.1f expected_dressed_samples=%d match=%s" % [
		samples.size(), course.length, s_lo, s_hi, expected_n, str(samples.size() == expected_n)])

	var payload := {"header": header, "samples": samples, "reference": ref, "terrain_ref_counts": terrain_counts}
	var jf := FileAccess.open(json_path, FileAccess.WRITE)
	jf.store_string(JSON.stringify(payload, "  "))
	jf.close()

	var rf := FileAccess.open(readme_path, FileAccess.WRITE)
	rf.store_string(_readme(out_res, header, src_stats, ver, samples.size(), expected_n, course.length, s_lo, s_hi, lot_stats, terrain_counts))
	rf.close()

	print("ROAD_EXPORT wrote %s" % glb_path)
	print("ROAD_EXPORT wrote %s" % json_path)
	print("ROAD_EXPORT wrote %s" % readme_path)
	print("ROAD_EXPORT_DONE %s" % ("PASS" if ver.verts_match and ver.aabb_match and samples.size() == expected_n else "FAIL"))
	quit(0 if ver.verts_match and ver.aabb_match and samples.size() == expected_n else 1)


func _arg_path(ua: PackedStringArray, key: String, fallback: String) -> String:
	if ua.has(key): return ua[ua.find(key) + 1]
	return fallback


func _build_course_road(art, pth, s0: float, s1: float) -> MeshInstance3D:
	# Same path as TrackRoad.build_strip for touge (no grid_m).
	var D: Dictionary = art.DIST["touge"]
	var sp := TrackRoad.span(D, s0, s1)
	var a0: float = sp[0]; var rng: float = sp[1]
	var mi: MeshInstance3D = art.strip(pth, a0, a0 + rng, -art.road_W, art.road_W, art.strip_mat("touge_road", float(D.lamp_period_m)))
	mi.name = "CourseRoad"
	return mi


func _turn_ranges(views: Array, s_lo: float, s_hi: float) -> Array:
	var out := []
	var n := views.size()
	for i in n:
		var s0: float = s_lo if i == 0 else float(views[i].off)
		var s1: float = s_hi if i == n - 1 else float(views[i + 1].off)
		var v = views[i]
		out.append({
			"id": i + 1,
			"code": "",
			"s0": s0,
			"s1": s1,
			"view_off": float(v.off),
			"turn_in": float(v.off) + float(v.S),
			"turn_out": float(v.off) + float(v.S) + float(v.R) * float(v.A),
			"exit_end": float(v.off) + float(v.length),
		})
	return out


func _turn_id_at(s: float, ranges: Array) -> int:
	var tid := int(ranges[0].id)
	for r in ranges:
		if s >= float(r.s0):
			tid = int(r.id)
	return tid


func _split_road_by_turn(mesh: Mesh, ranges: Array, art, D: Dictionary) -> Array:
	var arr: Array = mesh.surface_get_arrays(0)
	var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var uvs: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV]
	var n := ranges.size()
	var tools: Array = []
	var seam := []
	for i in n:
		var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
		tools.append(st); seam.append(0)
	# Triangle list (art.strip does not index). Assign by the mid-s of the three UVs.
	# Vertices on a shared row are duplicated into both turns: counted as seam_verts on the later turn.
	var row_seen := {}   # "turn|s_key|u_key" to skip double-count? count unique (s,u) added past the first copy instead
	var src_keys := {}
	for i in verts.size():
		src_keys["%.5f|%.5f" % [uvs[i].y, uvs[i].x]] = true
	var dst_keys := {}
	for i in range(0, verts.size() - 2, 3):
		var smid: float = (uvs[i].y + uvs[i + 1].y + uvs[i + 2].y) / 3.0
		var tid := _turn_id_at(smid, ranges)
		var st: SurfaceTool = tools[tid - 1]
		var col := Color8(tid, 0, 0, 255)
		for k in 3:
			st.set_color(col)
			st.set_uv(uvs[i + k])
			st.add_vertex(verts[i + k])
			var key := "%.5f|%.5f" % [uvs[i + k].y, uvs[i + k].x]
			if dst_keys.has(key):
				pass
			dst_keys[key] = int(dst_keys.get(key, 0)) + 1
	# seam_verts = extra copies across all parts (total part verts - source verts), split later for reporting
	var total_part_verts := 0
	var out := []
	var mat := _export_mat(art, D)
	for i in n:
		var st: SurfaceTool = tools[i]
		st.generate_normals()
		var am: ArrayMesh = st.commit()
		if am.get_surface_count() > 0:
			am.surface_set_material(0, mat)
		var vs := 0
		if am.get_surface_count() > 0:
			vs = (am.surface_get_arrays(0)[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
		total_part_verts += vs
		out.append({"name": "Turn%02d" % ranges[i].id, "mesh": am, "seam_verts": 0, "verts": vs})
	var extra: int = total_part_verts - verts.size()
	if out.size() > 0:
		out[0].seam_verts = extra   # report the total on the first entry; caller sums seam_verts
	# Distribute isn't needed; caller uses the sum. Keep total on first only by zeroing after? Caller sums — put all on first.
	return out


func _export_mat(art, D: Dictionary) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_texture = art.tex("touge_road")
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	m.uv1_scale = Vector3(1, 1.0 / float(D.lamp_period_m), 1)   # preview only: game tiles in the shader as (UV.y + scroll) / tile
	m.resource_name = "touge_road"
	return m


func _build_lot_floor(course, to: Dictionary, W: float) -> MeshInstance3D:
	# Arthur's authored lot_floor.glb, placed as the game does (LotArt frame copied onto the Floor slot).
	var path := "res://assets/env/turnout_lot/lot_floor.glb"
	if not ResourceLoader.exists(path):
		push_warning("ROAD_EXPORT lot_floor.glb missing")
		return null
	var a: float = to.s0; var b: float = to.s1; var tp: float = to.taper; var Ld: float = to.w
	var ins: float = -float(course.drop_at((a + b) * 0.5))
	var e0: float = ins * (W + 0.0)
	var q0: Dictionary = course.point(a, e0)
	var q1: Dictionary = course.point(a + 1.0, e0)
	var qx: Dictionary = course.point(a, ins * (W + 1.0))
	var o := Vector3(q0.x, float(q0.get("y", 0.0)), q0.z)
	var bz := (Vector3(q1.x, float(q1.get("y", 0.0)), q1.z) - o).normalized()
	var bx := (Vector3(qx.x, float(qx.get("y", 0.0)), qx.z) - o).normalized()
	var by := bz.cross(bx).normalized()
	if by.y < 0.0: by = -by
	var lot_xf := Transform3D(Basis(bx, by, bz), o)

	var holder := Node3D.new()
	holder.name = "_LotBake"
	holder.transform = lot_xf
	var inst: Node = load(path).instantiate()
	holder.add_child(inst)

	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var nsurf := 0
	var stack: Array = [inst]
	while not stack.is_empty():
		var nd: Node = stack.pop_back()
		for ch in nd.get_children(): stack.append(ch)
		if not (nd is MeshInstance3D): continue
		var mi := nd as MeshInstance3D
		if mi.mesh == null: continue
		var xf := lot_xf * _chain_xf(mi, inst)
		for si in mi.mesh.get_surface_count():
			var aarr: Array = mi.mesh.surface_get_arrays(si)
			var vv: PackedVector3Array = aarr[Mesh.ARRAY_VERTEX]
			var uv: PackedVector2Array = aarr[Mesh.ARRAY_TEX_UV] if aarr[Mesh.ARRAY_TEX_UV] != null else PackedVector2Array()
			var ii: PackedInt32Array = aarr[Mesh.ARRAY_INDEX] if aarr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			var nn: PackedVector3Array = aarr[Mesh.ARRAY_NORMAL] if aarr[Mesh.ARRAY_NORMAL] != null else PackedVector3Array()
			if ii.size() > 0:
				for k in ii:
					if uv.size() > k: st.set_uv(uv[k])
					if nn.size() > k: st.set_normal((xf.basis * nn[k]).normalized())
					st.add_vertex(xf * vv[k]); nsurf += 1
			else:
				for k in vv.size():
					if uv.size() > k: st.set_uv(uv[k])
					if nn.size() > k: st.set_normal((xf.basis * nn[k]).normalized())
					st.add_vertex(xf * vv[k]); nsurf += 1
	holder.free()
	if nsurf == 0: return null
	st.generate_normals()
	var out := MeshInstance3D.new()
	out.name = "LotFloor"
	out.mesh = st.commit()
	out.transform = Transform3D.IDENTITY
	return out


func _mesh_stats(mesh: Mesh, xf: Transform3D) -> Dictionary:
	var nverts := 0; var ntris := 0
	var aabb := AABB()
	var first := true
	if mesh == null: return {"verts": 0, "tris": 0, "aabb": aabb}
	for si in mesh.get_surface_count():
		var a: Array = mesh.surface_get_arrays(si)
		var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
		var idx = a[Mesh.ARRAY_INDEX]
		nverts += v.size()
		if idx != null and idx.size() > 0:
			ntris += int(idx.size() / 3)
		else:
			ntris += int(v.size() / 3)
		for p in v:
			var w: Vector3 = xf * p
			if first: aabb = AABB(w, Vector3.ZERO); first = false
			else: aabb = aabb.expand(w)
	return {"verts": nverts, "tris": ntris, "aabb": aabb}


func _aabb_s(a: AABB) -> String:
	return "min(%.4f,%.4f,%.4f) max(%.4f,%.4f,%.4f)" % [a.position.x, a.position.y, a.position.z, a.end.x, a.end.y, a.end.z]


func _aabb_delta(a: AABB, b: AABB) -> float:
	var d := 0.0
	for p in [a.position - b.position, a.end - b.end]:
		d = maxf(d, maxf(absf(p.x), maxf(absf(p.y), absf(p.z))))
	return d


func _verify_glb(path: String, src: Dictionary, seam_extra: int) -> Dictionary:
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_file(path, state)
	if err != OK:
		push_error("ROAD_EXPORT reimport failed: %s" % err)
		return {"verts": 0, "tris": 0, "aabb": AABB(), "verts_match": false, "aabb_match": false, "aabb_delta": 1e9}
	var scene: Node = doc.generate_scene(state)
	root.add_child(scene)
	var verts := 0; var tris := 0
	var aabb := AABB(); var first := true
	var stack: Array = [scene]
	while not stack.is_empty():
		var nd: Node = stack.pop_back()
		for ch in nd.get_children(): stack.append(ch)
		if not (nd is MeshInstance3D): continue
		if String(nd.name).begins_with("Lot") or String(nd.get_parent().name).begins_with("Lot"):
			continue
		# Only Turn* (and maybe the root's road pieces). Skip LotFloor.
		var nm := String(nd.name)
		if nm.begins_with("LotFloor"): continue
		if not (nm.begins_with("Turn") or nm == "CourseRoad" or nm == "RoadExport" or nm == "Node" or nm.begins_with("Mesh")):
			# still count if it's under RoadExport and not lot
			if nm.findn("lot") >= 0: continue
		var mi := nd as MeshInstance3D
		if mi.mesh == null: continue
		var st := _mesh_stats(mi.mesh, mi.transform if mi.is_inside_tree() else Transform3D.IDENTITY)
		# Ignore empty / non-road names more carefully: include anything that isn't LotFloor.
		if nm == "LotFloor": continue
		verts += st.verts; tris += st.tris
		if st.verts == 0: continue
		if first: aabb = st.aabb; first = false
		else: aabb = aabb.merge(st.aabb)
	var delta := _aabb_delta(aabb, src.aabb)
	var expected: int = int(src.verts) + seam_extra
	# GLTF may index the mesh and weld nothing, or add/remove colors; vertex count should stay triangle-list or become indexed.
	# If the importer indexes, vert count can drop. Compare both raw verts and triangle count.
	var verts_ok := (verts == expected) or (verts == int(src.verts)) or (tris == int(src.tris))
	# Prefer triangle count as the geometry identity when the importer indexes.
	if tris == int(src.tris) and delta <= 1e-3:
		verts_ok = true
	return {
		"verts": verts, "tris": tris, "aabb": aabb,
		"verts_match": verts_ok and (tris == int(src.tris) or verts == expected or verts == int(src.verts)),
		"aabb_match": delta <= 1e-3,
		"aabb_delta": delta,
		"expected_verts": expected,
	}


func _header(dpath: String, cpath: String, disp: Dictionary, cfg: Dictionary, course, W: float, ranges: Array, turnout: Dictionary, s_lo: float, s_hi: float) -> Dictionary:
	var head := _git_head()
	var dirty := _git_dirty()
	var turns := []
	var corners: Array = cfg.corners
	for i in ranges.size():
		var r: Dictionary = ranges[i].duplicate()
		if i < corners.size():
			r.code = String(corners[i].corner)
			r.dir = String(corners[i].dir)
		turns.append(r)
	var sim_pin := ""
	# scripts/globals.gd PIN_COMMIT (generated); not the course generator.
	var gf := FileAccess.get_file_as_string("res://scripts/globals.gd")
	var idx := gf.find("PIN_COMMIT")
	if idx >= 0:
		var q1 := gf.find("\"", idx); var q2 := gf.find("\"", q1 + 1)
		if q1 >= 0 and q2 > q1: sim_pin = gf.substr(q1 + 1, q2 - q1 - 1)
	var h := {
		"units": "metres",
		"axes": "Godot world space, +Y up, right-handed. First straight starts at the origin and travels -Z. Lateral d > 0 is right of travel (point(): x - tz*d, z + tx*d). Road surface is banked and graded.",
		"generator_commit": head,
		"generator_worktree_dirty": dirty,
		"generator_note": "Export is from this worktree (including uncommitted course / display / dressing). generator_commit is HEAD, not a claim that the tree is clean.",
		"course_spec": "%s + %s" % [dpath, cpath],
		"display_spec": dpath,
		"race_config": cpath,
		"sim_pin_commit": sim_pin,
		"course_length_m": snappedf(course.length, 0.0001),
		"dressed_s0_m": s_lo,
		"dressed_s1_m": snappedf(s_hi, 0.0001),
		"sample_step_m": 1.0,
		"road_half_m": W,
		"grade": float(course.grade),
		"bank": float(course.bank),
		"bank_ramp_m": float(course.bank_ramp_m),
		"road_clear_m": float(disp.districts.touge.terrain.get("road_clear_m", 8.0)),
		"gallery_wall_m": float(disp.districts.touge.terrain.get("gallery_wall_m", 3.5)),
		"turns": turns,
	}
	if not turnout.is_empty():
		h["turnout"] = {
			"s0": float(turnout.s0), "s1": float(turnout.s1),
			"taper_m": float(turnout.taper), "w_m": float(turnout.w),
			"turn_index_0based": int(turnout.turn),
			"side": "L" if float(course.drop_at((float(turnout.s0) + float(turnout.s1)) * 0.5)) > 0.0 else "R",
			"inside_sign": -float(course.drop_at((float(turnout.s0) + float(turnout.s1)) * 0.5)),
		}
	return h


func _git_head() -> String:
	var out := []
	OS.execute("git", ["-C", ProjectSettings.globalize_path("res://"), "rev-parse", "HEAD"], out, true)
	return String(out[0]).strip_edges() if out.size() > 0 else ""


func _git_dirty() -> Array:
	var out := []
	OS.execute("git", ["-C", ProjectSettings.globalize_path("res://"), "status", "--porcelain",
		"scripts/course.gd", "scripts/track_road.gd", "scripts/touge_dressing.gd",
		"scripts/art_kit.gd", "spec/display.json", "spec/race_config.json"], out, true)
	var rows := []
	if out.size() > 0:
		for line in String(out[0]).split("\n"):
			var s := line.strip_edges()
			if s != "": rows.append(s)
	return rows


func _samples(course, W: float, turnout: Dictionary, ranges: Array, s_lo: float, s_hi: float, D: Dictionary) -> Array:
	var road_clear: float = float(D.get("terrain", {}).get("road_clear_m", 8.0))
	var gwe: float = float(D.get("terrain", {}).get("gallery_wall_m", 3.5))
	var below := _legs_below_set(course, W, road_clear, gwe, s_lo, s_hi)
	var out := []
	var s := s_lo
	while s <= s_hi + 1e-6:
		var p0: Dictionary = course.point(s, 0.0)
		var p1: Dictionary = course.point(s + 0.25, 0.0)
		var pr: Dictionary = course.point(s, 1.0)
		var P := Vector3(p0.x, float(p0.y), p0.z)
		var T := Vector3(p1.x - p0.x, float(p1.y) - float(p0.y), p1.z - p0.z)
		if T.length() < 1e-9: T = Vector3(float(p0.tx), course.grade, float(p0.tz))
		T = T.normalized()
		var R := Vector3(pr.x - p0.x, float(pr.y) - float(p0.y), pr.z - p0.z)
		if R.length() < 1e-9: R = Vector3(-float(p0.tz), 0.0, float(p0.tx))
		R = R.normalized()
		var U := T.cross(R).normalized()
		if U.y < 0.0: U = -U
		var lw := W; var rw := W
		if not turnout.is_empty() and s > float(turnout.s0) and s < float(turnout.s1):
			var u := clampf(minf(s - float(turnout.s0), float(turnout.s1) - s) / maxf(float(turnout.taper), 1e-6), 0.0, 1.0)
			var ins: float = -float(course.drop_at((float(turnout.s0) + float(turnout.s1)) * 0.5))
			if ins < 0.0: lw = W + float(turnout.w) * u
			else: rw = W + float(turnout.w) * u
		var above := false
		if course.has_method("groof_at"):
			above = float(course.groof_at(s, -1.0)) > 0.0 or float(course.groof_at(s, 1.0)) > 0.0
		var is_below: bool = below.has("%d" % int(round(s * 10.0))) or _near_below(below, s)
		var section := "road"
		if above: section = "gallery"
		elif is_below: section = "bridge"
		out.append({
			"s": snappedf(s, 0.001),
			"pos": _v3(P),
			"tangent": _v3(T),
			"up": _v3(U),
			"left_width": snappedf(lw, 0.001),
			"right_width": snappedf(rw, 0.001),
			"turn_id": _turn_id_at(s, ranges),
			"section": section,
		})
		s += 1.0
	return out


func _legs_below_set(course, W: float, road_clear: float, gwe: float, s_lo: float, s_hi: float) -> Dictionary:
	# Mark 0.1 m keys where another leg's road lies under this deck by >= road_clear_m (the inverse of course.gd groof).
	var step := 2.0
	var cs := []; var ys := []; var ss := []
	var s := s_lo
	while s <= s_hi + 1e-6:
		cs.append(course.at(s)); ys.append(course.elev(s, 0.0)); ss.append(s); s += step
	var n := cs.size()
	var marked := {}
	for i in n:
		var c: Dictionary = cs[i]
		var y: float = ys[i]
		for j in n:
			if absf(ss[j] - ss[i]) < 30.0: continue
			var vx: float = float(cs[j].x) - float(c.x)
			var vz: float = float(cs[j].z) - float(c.z)
			if absf(vx * float(c.tx) + vz * float(c.tz)) > 0.5 * step + 0.05: continue
			var lat: float = -vx * float(c.tz) + vz * float(c.tx)
			if absf(lat) > 2.0 * W + gwe + 0.05: continue
			if y - float(ys[j]) >= road_clear:
				marked["%d" % int(round(ss[i] * 10.0))] = true
				break
	return marked


func _near_below(marked: Dictionary, s: float) -> bool:
	# 1 m samples sit between 2 m marks.
	for k in [0.0, -1.0, 1.0]:
		if marked.has("%d" % int(round((s + k) * 10.0))): return true
	return false


func _collect_lamps(dd: Dictionary, course) -> Array:
	var out := []
	for it in dd.items:
		if not bool(it.get("lamp", false)): continue
		var o := it.obj as Node3D
		if o == null: continue
		var s: float = float(it.base)   # kit6 lamps are fixed (do not scroll)
		var d: float = float(it.d)
		var e := o.rotation   # stream() set yaw only for untagged lamps
		out.append({
			"kind": "road",
			"s": snappedf(s, 0.001),
			"d": snappedf(d, 0.001),
			"pos": _v3(o.position),
			"rotation_rad": [snappedf(e.x, 0.0001), snappedf(e.y, 0.0001), snappedf(e.z, 0.0001)],
			"rotation_deg": [snappedf(rad_to_deg(e.x), 0.01), snappedf(rad_to_deg(e.y), 0.01), snappedf(rad_to_deg(e.z), 0.01)],
			"arm_local": [-1.65, 6.5, 0.0],
			"note": "lamp_mesh arm + head are at local -X. stream() yaw: 0 on the left of travel (arm over the road), PI on the right. Not pitched to grade.",
		})
	# Authored lot lamps (assets/env/turnout_lot/lot_lamps.glb) under the same LotArt frame the game copies onto the Lamps slot.
	var lg = dd.get("lot_group")
	if lg != null:
		var la := lg.get_node_or_null("LotArt") as Node3D
		var lamps_slot := lg.get_node_or_null("Lamps") as Node3D
		if la != null and lamps_slot != null:
			var stack: Array = [lamps_slot]
			while not stack.is_empty():
				var nd: Node = stack.pop_back()
				for ch in nd.get_children(): stack.append(ch)
				if not (nd is Node3D): continue
				var nm := String(nd.name)
				# Posts are lot_lamp_z21 / lot_lamp_z41 (or Lamp*). Skip the container "lot_lamps" and glow / pool meshes.
				if nm == "lot_lamps" or nm == "Lamps": continue
				if not (nm.begins_with("lot_lamp_") or nm.begins_with("Lamp")): continue
				if nm.find("glow") >= 0 or nm.find("pool") >= 0: continue
				var o := nd as Node3D
				var xf := _chain_xf(o, lamps_slot)   # Lamps already carries the LotArt frame
				# If Lamps.transform is identity (e.g. we didn't copy the frame in this path), fall back to LotArt.
				if lamps_slot.transform.is_equal_approx(Transform3D.IDENTITY):
					xf = la.transform * _chain_xf(o, lamps_slot)
				var pos: Vector3 = xf.origin
				var basis := xf.basis.orthonormalized()
				var e := basis.get_euler()
				var lot_ab: Array = dd.get("lot", [])
				var sd := _sd_of(course, pos, float(lot_ab[0]) - 2.0 if lot_ab.size() == 2 else -60.0, float(lot_ab[1]) + 2.0 if lot_ab.size() == 2 else course.length + 60.0)
				out.append({
					"kind": "lot",
					"name": nm,
					"s": snappedf(float(sd[0]), 0.001),
					"d": snappedf(float(sd[1]), 0.001),
					"pos": _v3(pos),
					"rotation_rad": [snappedf(e.x, 0.0001), snappedf(e.y, 0.0001), snappedf(e.z, 0.0001)],
					"rotation_deg": [snappedf(rad_to_deg(e.x), 0.01), snappedf(rad_to_deg(e.y), 0.01), snappedf(rad_to_deg(e.z), 0.01)],
					"arm_local": [-1.65, 6.5, 0.0],
					"note": "Authored lot_lamps.glb instance, baked through the Lamps / LotArt frame (touge_dressing._lot copies LotArt.transform onto the Lamps slot).",
				})
	return out


func _collect_rails(dd: Dictionary, course, W: float) -> Array:
	var out := []
	var lot: Array = dd.get("lot", [])
	var lot_side: float = float(dd.get("lot_side", -1.0))
	for it in dd.items:
		# Guardrail modules: kind +1 (outside), reach 0.8, pitched, mag = W+0.45, not cards / lattice / lamps.
		if not it.has("kind"): continue
		if bool(it.get("lamp", false)) or bool(it.get("card", false)) or it.has("lattice"): continue
		if absf(float(it.kind) - 1.0) > 1e-6: continue
		if absf(float(it.get("reach", -1.0)) - 0.8) > 1e-6: continue
		var s: float = dd.a0 + fposmod(float(it.base) - 0.0 - dd.a0, dd.range)   # scroll_m = 0
		var d: float = float(it.kind) * Dressing._drop(dd.pth, s) * float(it.mag)
		var p: Dictionary = dd.pth.point(s, d)
		var pos := Vector3(p.x, float(it.get("y", 0.0)) + float(p.get("y", 0.0)), p.z)
		var gr := 0.0
		if bool(it.pitch):
			gr = atan((float(dd.pth.point(s + 1.0, d).get("y", 0.0)) - float(dd.pth.point(s - 1.0, d).get("y", 0.0))) * 0.5)
		var yaw: float = atan2(p.tx, p.tz) + (PI if d > 0.0 and not bool(it.get("card", false)) else 0.0)
		var rx := -gr * (-1.0 if d > 0.0 else 1.0)
		var fits: bool = not it.has("reach") or float(it.reach) + float(dd.get("W", W)) <= _cap(dd.pth, s, signf(d)) - Course.BAND_MARGIN
		var on_lot_side: bool = not lot.is_empty() and signf(d) == signf(lot_side)
		var over_lot: bool = on_lot_side and s > float(lot[0]) - 2.0 and s < float(lot[1]) + 2.0
		out.append({
			"s": snappedf(s, 0.001),
			"d": snappedf(d, 0.001),
			"side": "R" if d > 0.0 else "L",
			"pos": _v3(pos),
			"rotation_rad": [snappedf(rx, 0.0001), snappedf(yaw, 0.0001), 0.0],
			"rotation_deg": [snappedf(rad_to_deg(rx), 0.01), snappedf(rad_to_deg(yaw), 0.01), 0.0],
			"visible": fits and not over_lot,
			"step_m": 4.0,
			"note": "Positions at scroll_m = 0 (editor / race start). Rails currently stream with the road in game.",
		})
	return out


func _cap(pth, s: float, side: float) -> float:
	return float(pth.cap_at(s, side)) if pth.has_method("cap_at") else 1e3


func _gallery_extents(course, s_lo: float, s_hi: float, W: float, D: Dictionary) -> Array:
	# Same 2 m steps as touge_dressing._gallery: a run is every stretch where both ends have groof_at(..., true) > 0.
	var we: float = float(D.get("terrain", {}).get("gallery_wall_m", 3.5))
	var out := []
	if not course.has_method("groof_at"): return out
	for sd in [-1.0, 1.0]:
		var run_s0 := 0.0; var in_run := false
		var roofs := []; var walls := []
		var s := s_lo
		while s < s_hi - 1e-6:
			var s2 := minf(s + 2.0, s_hi)
			var ra: float = float(course.groof_at(s, sd, true))
			var rb: float = float(course.groof_at(s2, sd, true))
			var on: bool = ra > 0.0 and rb > 0.0
			if on:
				if not in_run:
					in_run = true; run_s0 = s; roofs = []; walls = []
				roofs.append(ra); roofs.append(rb)
				var wa: float = float(course.gwall_at(s, sd)) if course.has_method("gwall_at") else we
				var wb: float = float(course.gwall_at(s2, sd)) if course.has_method("gwall_at") else we
				walls.append(wa); walls.append(wb)
			elif in_run:
				out.append(_gal_row(sd, run_s0, s, roofs, walls)); in_run = false
			s = s2
		if in_run:
			out.append(_gal_row(sd, run_s0, s_hi, roofs, walls))
	return out


func _gal_row(sd: float, s0: float, s1: float, roofs: Array, walls: Array) -> Dictionary:
	roofs.sort(); walls.sort()
	return {
		"side": "R" if sd > 0.0 else "L",
		"s0": snappedf(s0, 0.001),
		"s1": snappedf(s1, 0.001),
		"wall_from_edge_m_min": snappedf(float(walls[0]), 0.001) if walls.size() else 0.0,
		"wall_from_edge_m_max": snappedf(float(walls[-1]), 0.001) if walls.size() else 0.0,
		"roof_height_m_min": snappedf(float(roofs[0]), 0.001) if roofs.size() else 0.0,
		"roof_height_m_max": snappedf(float(roofs[-1]), 0.001) if roofs.size() else 0.0,
	}


func _terrain_counts(group: Node, course, ranges: Array, W: float) -> Dictionary:
	var per := {}
	for r in ranges:
		per[str(r.id)] = {"turn_id": int(r.id), "s0": float(r.s0), "s1": float(r.s1), "terrain_tris": 0, "terrain_draw_calls": 0, "all_tris": 0, "all_draw_calls": 0}
	var terr_tris_total := 0; var terr_dc := 0; var all_tris := 0; var all_dc := 0
	if group == null: return {"summary": {}, "per_turn": []}
	var stack: Array = [group]
	while not stack.is_empty():
		var nd: Node = stack.pop_back()
		for ch in nd.get_children(): stack.append(ch)
		if not (nd is MeshInstance3D): continue
		var mi := nd as MeshInstance3D
		if mi.mesh == null: continue
		var is_terr: bool = String(mi.name).begins_with("Terr")
		var dc: int = mi.mesh.get_surface_count()
		# Assign the mesh to a turn by the mean vertex s (UV.y if present, else nearest centreline s).
		var tid := _mesh_turn(mi, course, ranges, group)
		var tris := 0
		for si in mi.mesh.get_surface_count():
			var a: Array = mi.mesh.surface_get_arrays(si)
			var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
			var idx = a[Mesh.ARRAY_INDEX]
			if idx != null and idx.size() > 0: tris += int(idx.size() / 3)
			else: tris += int(v.size() / 3)
		all_tris += tris; all_dc += dc
		var bucket: Dictionary = per.get(str(tid), per[str(ranges[0].id)])
		bucket.all_tris += tris; bucket.all_draw_calls += dc
		if is_terr:
			terr_tris_total += tris; terr_dc += dc
			bucket.terrain_tris += tris; bucket.terrain_draw_calls += dc
	var rows := []
	for r in ranges: rows.append(per[str(r.id)])
	return {
		"summary": {
			"terrain_triangles": terr_tris_total,
			"terrain_draw_calls": terr_dc,
			"dressing_triangles": all_tris,
			"dressing_draw_calls": all_dc,
			"note": "terrain_* counts MeshInstance3D names beginning with Terr (bands, skirts, up faces, gallery walls, lot hill / cut / flanks). dressing_* is every mesh under CourseDressing, including props, rails, lamps, the lot kit and FloorBase. No per-section budget is defined in the art docs; these are the current procedural counts only.",
		},
		"per_turn": rows,
	}


func _mesh_turn(mi: MeshInstance3D, course, ranges: Array, group: Node) -> int:
	var uv_s := []; var acc := Vector3.ZERO; var n := 0
	for si in mi.mesh.get_surface_count():
		var a: Array = mi.mesh.surface_get_arrays(si)
		var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
		var uv = a[Mesh.ARRAY_TEX_UV]
		if uv != null and uv.size() == v.size():
			for u in uv: uv_s.append(u.y)
		for p in v: acc += p; n += 1
	# Terrain bands store metres-along in UV.y (often well outside 0..1).
	if uv_s.size() > 0:
		var umin := 1e18; var umax := -1e18; var usum := 0.0
		for u in uv_s:
			umin = minf(umin, u); umax = maxf(umax, u); usum += u
		if umax - umin > 1.5 or absf(usum / float(uv_s.size())) > 2.0:
			return _turn_id_at(usum / float(uv_s.size()), ranges)
	# Streamed props: the dressing-group child is placed in world space at identity parent.
	var cur: Node = mi
	while cur.get_parent() != null and cur.get_parent() != group:
		cur = cur.get_parent()
	var pos := Vector3.ZERO
	if cur is Node3D and (cur as Node3D).position.length() > 1.0:
		pos = (cur as Node3D).position
	elif n > 0:
		pos = acc / float(n)
	else:
		return 1
	return _turn_id_at(float(_sd_of(course, pos)[0]), ranges)



## Local transform of n, multiplied up through ancestors, including stop (the subtree root).
func _chain_xf(n: Node, stop: Node) -> Transform3D:
	var xf := Transform3D.IDENTITY
	var cur := n
	for _i in 64:
		if cur == null: break
		if cur is Node3D:
			xf = (cur as Node3D).transform * xf
		if cur == stop: break
		cur = cur.get_parent()
	return xf


func _sd_of(course, pos: Vector3, s0 := -60.0, s1 := -1e9) -> Array:
	var best := 1e18; var bs := 0.0; var bd := 0.0
	if s1 < s0: s1 = course.length + 60.0
	var s := s0
	while s <= s1 + 1e-6:
		var q: Dictionary = course.at(s)
		var dx := pos.x - float(q.x); var dz := pos.z - float(q.z)
		var along := dx * float(q.tx) + dz * float(q.tz)
		var d2 := (dx - float(q.tx) * along) * (dx - float(q.tx) * along) + (dz - float(q.tz) * along) * (dz - float(q.tz) * along)
		if d2 < best:
			best = d2; bs = s + along
			var q2: Dictionary = course.at(bs)
			bd = -(pos.x - float(q2.x)) * float(q2.tz) + (pos.z - float(q2.z)) * float(q2.tx)
		s += 2.0
	return [bs, bd]


func _v3(v: Vector3) -> Array:
	return [snappedf(v.x, 0.0001), snappedf(v.y, 0.0001), snappedf(v.z, 0.0001)]


func _readme(out_res: String, header: Dictionary, src: Dictionary, ver: Dictionary, n_samp: int, n_exp: int, length: float, s_lo: float, s_hi: float, lot_stats: Dictionary, terrain: Dictionary) -> String:
	var cmd := "godot --headless --path . --script tools/touge_race/road_export.gd\n# optional: -- --out res://unapproved/gordon/road_export --display res://spec/display.json --config res://spec/race_config.json\n"
	var lot_line := "none (no turnout)"
	if not lot_stats.is_empty():
		lot_line = "LotFloor verts=%d tris=%d (Arthur's lot_floor.glb, baked through the game's LotArt frame into world space)" % [lot_stats.verts, lot_stats.tris]
	var tnote := ""
	if terrain.has("summary"):
		tnote = "Current procedural terrain (Terr* meshes) is listed in road_centreline.json under terrain_ref_counts. No triangle or draw-call budget is defined for environment sections."
	return """# Touge road export (for Arthur)

Reference geometry of the road as the Godot game builds it today (`track_road.gd` / `art_kit.strip` / `course.gd`). Terrain is not included. Regenerate whenever the course spec or road builder changes; do not hand-edit these files.

## Files

- `road_surface.glb` — the exact CourseRoad mesh in Godot world space, +Y up, metres, every node at the identity transform (vertices already in world space). One object per turn (`Turn01`…`Turn10`). Vertex colour R holds the turn id (1–10 as 8-bit). `LotFloor` is the current drivable lot floor (authored `assets/env/turnout_lot/lot_floor.glb` placed with the game's LotArt frame). No hills, skirts, galleries, rails or lamps.
- `road_centreline.json` — 1 m samples over the dressed range, plus a reference block of current lamp poses, rail segment poses (at scroll 0) and gallery extents, and a header (units, axes, generator commit, specs).
- `README.md` — this file.

## How to regenerate

From the project root, with the Godot 4.6 binary:

```
%s
```

The script reads `spec/display.json` and `spec/race_config.json`, builds the course with `TrackRoad.build_course`, and writes this folder. It does not commit anything.

## Coordinate conventions

%s

- Units: metres.
- `s` is distance along the centre line (s = 0 at the start of the first 45 m approach straight). The dressed road (and these samples) run from s = %.1f to s = %.3f, which is 60 m of run-in and run-out past the course (`course.length` = %.3f m).
- `left_width` / `right_width` are metres from the centre line to the drivable edge. On open road both equal `road_half_m` (%.2f). Over the turnout lot the inside edge grows with the taper to `road_half_m + pocket_w_m`.
- `section` is `gallery` when `course.groof_at` sees another leg overhead by at least `road_clear_m`, `bridge` when another leg's road lies under this deck by at least that amount, otherwise `road`.
- Turn cuts: see `header.turns` (turn *i* covers `[s0, s1)` from this view's `off` to the next, with run-in on turn 1 and run-out on turn 10).
- UV on the road mesh: `UV.x` = 0 at the left edge (d = −W) to 1 at the right (d = +W). `UV.y` = `s` in metres. The game tiles this as `(UV.y + scroll_m) / lamp_period_m` in `scroll_vertex_lit.gdshader`. The material on the glb is a preview only.
- Lamps: kit6 posts sit at `(W + lamp_out_d_m)` on the drop / outside at that `s`, and do not scroll. Rotations are Godot Euler (YXZ) in world space. The mesh arm points along local −X. Lot lamps are listed with `kind: lot`.
- Rails: W-beam modules every `guardrail_step_m` (4 m) on the outside, at d = drop_at(s) × (W + 0.45). Positions are at `scroll_m = 0` (editor / race start). In the current game they still stream with the road. `visible` follows `stream()` (hidden when the cap leaves no room, or over the lot on the lot side).
- Galleries: s-ranges where `touge_dressing._gallery` would build a wall (`groof_at` > 0 on both ends of a 2 m step), with the wall's distance past the edge (`gwall_at`) and roof height over this road.

## Generator

- HEAD: `%s`
- Worktree dirty (files that affect this export): %s
- Specs: %s

## Verification (this run)

- In-game CourseRoad: verts=%d tris=%d aabb=%s
- Reimported glb road objects (LotFloor excluded): verts=%d tris=%d aabb=%s
- Vertex / triangle check: %s (split objects may duplicate a row of verts at each turn seam; triangle count must match the source).
- AABB max component delta: %.6f m (pass ≤ 0.001)
- Centreline samples: %d (expected %d over the dressed 1 m grid). Course length %.3f m.
- Lot floor: %s
- %s
""" % [cmd, header.axes, s_lo, s_hi, length, float(header.road_half_m), String(header.generator_commit), str(header.generator_worktree_dirty), String(header.course_spec),
	src.verts, src.tris, _aabb_s(src.aabb), ver.verts, ver.tris, _aabb_s(ver.aabb), "PASS" if ver.verts_match and ver.aabb_match else "FAIL", ver.aabb_delta,
	n_samp, n_exp, length, lot_line, tnote]
