## WANGAN COPY (Arthur, unapproved): Gordon's touge_dressing.gd; district 'wangan' is dressed by wangan_dressing.gd (`# WANGAN:`).
## touge_dressing.tscn: district dressing along the road (B.5b Touge frames: lamps, verge, guardrail, cedar cards; the
## Street branch is kept for the N90 Street district). Moved verbatim from main.gd _build_district (scene refactor 2026-11-12).
## Props stream with the RoadScroller so they stay on the pools painted into the road texture (stream()).
## @tool: in the editor it dresses the whole continuous course at scroll 0 from spec/display.json districts.<district>;
## at runtime main.gd calls build() for the straight and the course and stream() every frame.
@tool
extends Node3D
const ArtKit = preload("res://scripts/art_kit.gd")
const TrackRoad = preload("res://scripts/track_road.gd")
const Course = preload("res://scripts/course.gd")
const WanganDressing = preload("res://scripts/wangan_dressing.gd")
const TougeEnv = preload("res://scripts/touge_env.gd")
const CamGuard = preload("res://scripts/cam_guard.gd")

@export_file("*.json") var display_spec := "res://spec/display.json"
@export_file("*.json") var race_config := "res://spec/race_config.json"
@export var district := "touge"
## editor preview only: draw the district fog (off = the whole course stays readable from a top view)
@export var preview_fog := false:
	set(v): preview_fog = v; if is_inside_tree() and Engine.is_editor_hint(): _editor_build()
@export var preview_in_editor := true:
	set(v): preview_in_editor = v; if is_inside_tree() and Engine.is_editor_hint(): _editor_build()
@export_tool_button("Rebuild dressing") var rebuild_dressing = _editor_build

func clear() -> void:
	for ch in get_children():
		remove_child(ch); ch.queue_free()

## {group, items, a0, range, pth}; group is added as a child named nm
func build(art, pth, s0: float, s1: float, dk: String, nm: String, opts: Dictionary = {}) -> Dictionary:
	if dk == "wangan":   # WANGAN: the expressway deck kit (scripts/wangan_dressing.gd)
		var wd := WanganDressing.build(art, pth, s0, s1, nm, opts)
		add_child(wd.group)
		return wd
	var D: Dictionary = art.DIST[dk]; var per: float = D.lamp_period_m; var W: float = art.road_W
	var g := Node3D.new(); g.name = nm; var items: Array = []
	if dk == "touge" and opts.get("env", null) != null: opts.env.build(art, g)   # Arthur's authored terrain (touge_env.gd)
	_items_ref = items
	var sp := TrackRoad.span(D, s0, s1); var a0: float = sp[0]; var rng: float = sp[1]
	var add := func(obj: Node3D, base: float, d: float) -> void:
		g.add_child(obj); items.append({"obj": obj, "base": base, "d": d})
	var env = opts.get("env", null)   # TOUGE course: touge_env.gd (Arthur's authored terrain, rails and lamps are in it)
	for n in (0 if env != null else int(rng / per)):
		for L in D.lamps:
			var side: float = L[1]
			var lamp := Node3D.new()
			var post := MeshInstance3D.new(); post.mesh = art.lamp_mesh(); post.material_override = art.env_mat; post.extra_cull_margin = 16384.0; lamp.add_child(post)
			var gl: MeshInstance3D = art.glow_sprite("glow_lamp", Color(1, 1, 1), 1.5, 0.9)  # tinted texture (make_tone_tex.py per-lamp), 1.5 m billboard at 0.9 (build_v5.py:276)
			gl.position = Vector3(-1.3, 6.3, 0); lamp.add_child(gl)
			var dsd := _drop(pth, a0 + n * per + float(L[0]))   # TOUGE: lamps on the outside of the corner at their spot (Austin t121 item 11)
			var ld: float = (W + float(D.lamp_out_d_m)) * dsd if bool(D.get("kit6", false)) else side * (float(D.lamp_post_d_m) if D.has("lamp_post_d_m") else W + 0.6)
			add.call(lamp, a0 + n * per + float(L[0]), ld)
			# Austin pt137u (lamps faced away from the road): lamp_mesh's arm + head are at local -X, and stream() yaws items by
			# atan2(tx, tz), which puts local -X on the RIGHT of travel. The old scale.x = side mirror sent the arm away from the road
			# on both sides (and flipped the single-sided quads' winding). Turn the lamp round instead of mirroring it: yaw 0 on the
			# left (arm reaches right, over the road), PI on the right (arm reaches left).
			items[-1].yaw = PI if ld > 0.0 else 0.0
			if bool(D.get("kit6", false)): items[-1].fixed = true; items[-1].lamp = true   # Austin t116u: lamps never scroll (the treadmill moves everything else)
	if dk == "touge" and bool(D.get("kit6", false)):   # TOUGE race: Arthur's 6 m touge kit (display.json districts.touge _touge6 / _kit6_doc)
		_kit6(art, pth, g, add, a0, rng, D, W, opts.get("turnout", {}), env)
	elif dk == "touge":
		for sd in [-1.0, 1.0]:
			g.add_child(art.strip(pth, a0, a0 + rng, sd * W, sd * (W + float(D.verge_w_m)), art.strip_mat("touge_verge", 6.0)))
			g.add_child(art.strip(pth, a0, a0 + rng, sd * (W + float(D.wall_d_m)), 0.0, art.strip_mat("touge_rail", 4.0), float(D.wall_h_m)))
		var k := 0; var spc: float = D.cedar_spacing_m; var out: float = D.outside_side
		while k * spc < rng:   # B.5b frames (build_lsc.py:221-234): 2 outside cedars + an inside one (p .8) per step
			var trees := []
			for j in 2: trees.append([out * lerpf(D.cedar_out_d_m[0], D.cedar_out_d_m[1], ArtKit.hash01(k * 5 + j)), lerpf(D.cedar_h_m[0], D.cedar_h_m[1], ArtKit.hash01(k * 2 + j + 0.5))])
			if ArtKit.hash01(k * 7 + 0.3) < float(D.cedar_in_p): trees.append([-out * lerpf(D.cedar_in_d_m[0], D.cedar_in_d_m[1], ArtKit.hash01(k * 9 + 0.7)), lerpf(D.cedar_in_h_m[0], D.cedar_in_h_m[1], ArtKit.hash01(k * 4 + 0.9))])
			for ti in trees.size():
				var tr: Array = trees[ti]; var h: float = tr[1]
				var c: Node3D = art.cross_card("touge_cedar_a" if ArtKit.hash01(k + ti * 7) < 0.5 else "touge_cedar_b", h * float(D.cedar_w_ratio), h)
				add.call(c, a0 + k * spc + (ArtKit.hash01(k * 3 + ti) - 0.5) * 4.0, tr[0])
			k += 1
	else:
		var sw: float = D.sidewalk_w_m
		for sd in [-1.0, 1.0]:
			g.add_child(art.strip(pth, a0, a0 + rng, sd * W, sd * (W + sw), art.strip_mat("street_walk", 4.0), 0.0, 0.02))
			g.add_child(art.strip(pth, a0, a0 + rng, sd * (W + sw), 0.0, art.strip_mat("street_facade", float(D.facade_tile_m)), float(D.facade_h_m)))
		var k := 0
		while k * 12 < rng:
			var sd := 1.0 if k % 2 else -1.0; var i: int = k % D.neon.size()
			var sign := Node3D.new(); var y := 3.5 + ArtKit.hash01(k) * 3.0
			sign.add_child(art.card("street_neon_%d" % i, 0.6, 2.4, y))
			var gl: MeshInstance3D = art.glow_sprite("glow_white", Color(D.neon[i]), 3.2, 0.45); gl.position = Vector3(0, y + 1.2, 0); sign.add_child(gl)
			add.call(sign, a0 + k * 12 + 5, sd * (W + sw - 0.7))
			k += 1
		var KINDS := [["street_cut_cone", 0.5, 0.7], ["street_cut_bike", 1.6, 1.1], ["street_cut_plant", 0.9, 1.0], ["street_cut_vending", 1.0, 1.9]]
		k = 0
		while k * float(D.prop_spacing_m) < rng:
			for sd in [-1, 1]:
				if ArtKit.hash01(k * 11 + sd) < 0.35: continue
				var kd: Array = KINDS[int(floor(ArtKit.hash01(k * 13 + sd) * 4))]
				add.call(art.card(kd[0], kd[1], kd[2]), a0 + k * float(D.prop_spacing_m) + 2, sd * (W + 1.0 + ArtKit.hash01(k * 17 + sd) * (sw - 1.6)))
			k += 1
	add_child(g)
	var res := {"group": g, "items": items, "a0": a0, "range": rng, "pth": pth, "W": W}
	if env != null and dk == "touge":   # cedar feet on the authored ground (Arthur 2026-11-20 items 1-2), lattice trimmed at flips (item 3)
		res.cedar_lanes = _cedar_lanes(pth, items, a0, rng, W, D)
		res.cut = _cut_table(pth, a0, rng, W)
		res.flips = []
		for k in range(1, pth.drop_runs.size()): res.flips.append(float(pth.drop_runs[k][0]))
	if dk == "touge" and bool(D.get("kit6", false)) and not opts.get("turnout", {}).is_empty():
		res.lot = [float(opts.turnout.s0), float(opts.turnout.s1)]; res.lot_side = -_drop(pth, (res.lot[0] + res.lot[1]) * 0.5); res.lot_group = to_lot_group
	return res

## TOUGE race: Arthur's touge v2 kit (mountain_districts/godot/scripts/district_preview.gd:807-841 _dress_touge_v2) on the
## streamed course. Inside (-course.drop_at(s), the inside of each corner): gravel shoulder, 法枠 lattice cut slope (mtn_lattice_slope_g, 4 m modules at W+0.7,
## gain 0.66), hill band, cedars on top, delineators on the shoulder. Outside (course.drop_at(s), the outside of each corner): verge, W-beam guardrail modules,
## the slope falling away, cedar tops below, delineators on the rail line.
## Austin 2026-11-19 (t115u/t116u): every roadside element scrolls in lockstep with the road (walls, lattice, guardrails, verge,
## road): the bands use the road's scroll material and every module is a streamed item; the sodium lamps do NOT scroll
## (fixed items, see build()). The turnout parking area is fixed geometry (_lot); streamed inside items are hidden over it.
func _kit6(art, pth, g: Node3D, add: Callable, a0: float, rng: float, D: Dictionary, W: float, to: Dictionary, env = null) -> void:
	var grav := _envmat(art, "touge_gravel", 4.0); var verge: ShaderMaterial = art.strip_mat("touge_verge", 6.0)
	var gw: float = D.gravel_w_m
	var lot := []   # course s range the lot replaces on the inside
	if not to.is_empty(): lot = [float(to.s0), float(to.s1)]
	# static bands per drop run (Austin t121 item 11: outside of each corner = guardrail + drop, inside = cut slope / lattice)
	# Austin pt137u pic 5 (void past the dressing): the slope / hill bands continue past the approved kit out to the camera
	# reach (course.gd terrain_profile, display.json districts.touge.terrain), with a skirt under any edge another leg cuts
	# Austin 2026-11-20 (AGENTS.md: the world is authored): on the course the ground, cut and rock faces, galleries, rails and lamps
	# are Arthur's assets (touge_env.gd). The code bands below are the scroll straight's only (the treadmill between corners).
	if env == null:
		var P_OUT: Array = Course.terrain_profile(D, true); var P_IN: Array = Course.terrain_profile(D, false)
		var skirt: float = float(D.get("terrain", {}).get("skirt_m", 0.0))
		var runs: Array = _runs(pth, a0, a0 + rng)
		for run in runs:
			var r0: float = run[0]; var r1: float = run[1]; var out: float = run[2]; var ins := -out
			var inside_runs := [[r0, r1]]
			if not lot.is_empty() and lot[1] > r0 and lot[0] < r1: inside_runs = [[r0, maxf(r0, lot[0])], [minf(r1, lot[1]), r1]]
			for r in inside_runs:
				if r[1] - r[0] < 0.5: continue
				g.add_child(_vband(art, pth, r[0], r[1], ins, W, 0.0, 0.02, gw, 0.02, grav))
				# under the gravel / cut-face seam (gw) and 2 m on under the face (it rises ~1 m there): a ray grazing the gravel slipped through that seam into the empty space
				# under the bands (void replay t09_qte0_chase: turn 10's cut at s 907, 0.1 m over the gravel). Hidden under the cut.
				g.add_child(_vband(art, pth, r[0], r[1], ins, W, 0.5, -0.06, gw + 2.0, -0.06, grav))
				# from the gravel edge, not from the lattice top (W + 8.7): a cut face under the lattice modules (the straight line
				# gravel -> 7.6 m at 8.7 m runs 2-3 m behind each module's face, so it never shows through one). Modules are 4 m items
				# placed by their centre's side, so wherever none covers a stretch (a drop-side flip mid-module, a lot end, a module
				# the cap hides) the face is still there instead of sky (Austin pt137u item 4, void sweep t05_lot_exit_flank)
				g.add_child(_pband(pth, r[0], r[1], ins, W, P_IN.slice(1), verge, skirt))
			if inside_runs.size() == 2:   # the road's cut ends at each lot end: close its cross-section down to the floor (the flank
				# modules are yawed along the taper diagonal, so their leading edge leaves a sliver against an open band end;
				# void sweep t05_lot_exit_flank / lot_overview)
				var flat := [[0.0, 0.0], [float(P_IN[-1][0]), 0.0]]
				for sb in [float(lot[0]), float(lot[1])]: g.add_child(_xface(pth, sb, ins, W, P_IN, flat, verge))
			g.add_child(_vband(art, pth, r0, r1, out, W, 0.0, 0.0, float(D.verge_out_w_m), 0.0, verge))
			g.add_child(_pband(pth, r0, r1, out, W, P_OUT.slice(1), verge, skirt))
			for sd in [-1.0, 1.0]:   # road-edge underlay: the road strip and the bands are sampled differently along s, so on a
				# curve their edge chords leave hairline slivers; a strip just under the road edge closes them (never seen otherwise)
				g.add_child(_vband(art, pth, r0, r1, sd, W, -0.8, -0.06, 0.6, -0.06, grav))
		if pth.has_method("groof_at"):   # gallery walls where another leg runs overhead (course.gd groof)
			for sd in [-1.0, 1.0]: g.add_child(_gallery(pth, a0, a0 + rng, sd, W, float(D.get("terrain", {}).get("gallery_wall_m", 3.5)), P_OUT, P_IN, verge))
		for k in range(1, runs.size()):   # where the drop side flips, close the cross-section between the two profiles
			var sb: float = runs[k][0]
			for sd in [-1.0, 1.0]:
				var pa: Array = P_OUT if sd == float(runs[k - 1][2]) else P_IN
				var pb: Array = P_OUT if sd == float(runs[k][2]) else P_IN
				# twice, FLIP_FACE before and after the flip, not once on it: the two runs' band rows end exactly at the flip and only
				# met the face edge to edge, with the face's extra profile vertices along that edge (T-junctions), so grazing rays found
				# pixel cracks into the empty space under the bands (void sweep t03_qte0_chase s 253, t08_plan_A / t08_qte1_chase
				# s 799). Each face now stands behind a band edge (the low run's side: under the high band; the other: in front of it).
				if pa != pb:
					for off in [-FLIP_FACE, FLIP_FACE]: g.add_child(_xface(pth, sb + off, sd, W, pa, pb, verge))
					# and a backing 0.25 m under each run's band, each running 0.3 m PAST the flip, and one under the road edge: every
					# band / underlay / road row of the two runs ends on the plane s = sb, so a ray running down that plane (t01_plan_A
					# at s 63) slid between all of them; the backings overlap across it, so such a ray meets ground, not sky
					g.add_child(_pband(pth, sb - 2.0, sb + 0.3, sd, W, pa.slice(1), verge, 0.0, 1.0, -0.25))
					g.add_child(_pband(pth, sb - 0.3, sb + 2.0, sd, W, pb.slice(1), verge, 0.0, 1.0, -0.25))
					g.add_child(_vband(art, pth, sb - 2.0, sb + 2.0, sd, W, -1.5, -0.3, 1.0, -0.3, grav, 1.0))
	# streamed modules: kind -1 = inside, +1 = outside; stream() puts them on the side the course has at their current s
	var s := a0
	while s < a0 + rng:   # lattice cut slope, 4 m modules (Arthur v2: s + 2, -(W + 0.7), gain 0.66)
		add.call(prop_g(art, "mtn_lattice_slope_g", 0.66), s + 2.0, W + gw); var tl: Dictionary = _tag(-1.0, true); tl.reach = 5.7; tl.lattice = float(D.lattice_step_m)
		s += float(D.lattice_step_m)
	var k := 0; s = a0
	while s < a0 + rng:
		var h := lerpf(10.0, 15.0, ArtKit.hash01(k * 2.3))
		var c: Node3D = art.cross_card("touge_cedar_a" if ArtKit.hash01(k * 1.7) < 0.5 else "touge_cedar_b", h * 0.3333, h)
		add.call(c, s + ArtKit.hash01(k) * 2.0, W + 9.5 + ArtKit.hash01(k * 5.1) * 6.0); var ti: Dictionary = _tag(-1.0, false, true); ti.y = 7.6; ti.h = h; ti.reach = float(ti.mag) - W + 1.0
		s += 4.0; k += 1
	s = a0
	while env == null and s < a0 + rng:   # course: the rails are static in Arthur's sections
		add.call(prop_g(art, "touge_guardrail", 1.0), s, W + 0.45); _tag(1.0, true).reach = 0.8
		s += float(D.guardrail_step_m)
	k = 0; s = a0
	while s < a0 + rng:
		var h2 := lerpf(11.0, 16.0, ArtKit.hash01(k * 4.7 + 1.0))
		var c2: Node3D = art.cross_card("touge_cedar_a" if ArtKit.hash01(k * 1.3) < 0.5 else "touge_cedar_b", h2 * 0.3333, h2)
		add.call(c2, s + ArtKit.hash01(k * 2.0) * 4.0, W + 5.0 + ArtKit.hash01(k * 7.3) * 14.0); var to2: Dictionary = _tag(1.0, false, true); to2.y = -h2 * 0.55 - 2.0; to2.h = h2; to2.reach = float(to2.mag) - W + 1.0
		s += 3.6; k += 1
	for dl in [[a0 + 2.0, 1.0, W + 0.62], [a0 + 6.0, -1.0, W + 0.5]]:   # Arthur v2: two delineator rows, 8 m apart
		s = dl[0]
		while s < a0 + rng:
			add.call(prop_g(art, "mtn_delineator", 1.0, 0.55), s, dl[2]); _tag(dl[1], false)
			s += 8.0
	if not to.is_empty(): _lot(art, pth, g, D, W, -_drop(pth, (lot[0] + lot[1]) * 0.5), to, env)

## TOUGE: roadside band at e0..e1 m beyond the road edge on side (heights y0..y1, linear in e), clamped per s to the room the course
## leaves on that side (course.cap_at: hairpin interiors / tight arcs), so bands of the two legs never overlap or fold over
const CAP_MARGIN := Course.BAND_MARGIN
const FLIP_FACE := 0.15   # the cross-section face at a drop-side flip is built this far to each side of it
static func _cap(pth, s: float, side: float) -> float:
	return float(pth.cap_at(s, side)) if pth.has_method("cap_at") else 1e3
## far terrain room (course.gd rule 3) and the cliff drop its skirt must close
static func _tcap(pth, s: float, side: float) -> float:
	return float(pth.tcap_at(s, side)) if pth.has_method("tcap_at") else _cap(pth, s, side)
static func _tband(pth, s: float, side: float) -> float:   # where the terrain band ends (course.gd tband: margin inside, or lapped over a lower level)
	return float(pth.tband_at(s, side)) if pth.has_method("tband_at") else _tcap(pth, s, side) - CAP_MARGIN
static func _tstep(pth, s: float, side: float) -> float:
	return float(pth.tstep_at(s, side)) if pth.has_method("tstep_at") else 0.0

## row positions for a band over [s0, s1]: every step from s0 AND every course.gd cap sample boundary (where the rooms step),
## the same for every band, so bands that meet along a seam (the verge strip and the slope band, the gravel and the cut) share
## their seam vertices on a curve instead of meeting chord to chord
static func _srows(pth, s0: float, s1: float, step: float) -> Array:
	var ss := [s0]
	var cs0: float = float(pth.get("cap_s0")) if pth.get("cap_s0") != null else s0; var cst: float = float(pth.get("cap_step")) if pth.get("cap_step") != null else 1e9
	var k := 1
	var nb := cs0 + (floorf((s0 - cs0) / cst + 1e-6) + 1.0) * cst
	while true:
		var ns := minf(minf(s0 + k * step, nb), s1)
		if ns >= s1 - 1e-6: break
		if ns >= s0 + k * step - 1e-6: k += 1
		if ns >= nb - 1e-6: nb += cst
		if ns > float(ss[-1]) + 1e-4: ss.append(ns)
	ss.append(s1)
	return ss

func _vband(art, pth, s0: float, s1: float, side: float, W: float, e0: float, y0: float, e1: float, y1: float, mat: ShaderMaterial, step := 2.0) -> MeshInstance3D:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var ss: Array = _srows(pth, s0, s1, step)   # rows shared with the bands it meets; each strip clamped to its own interval's room
	var row := func(s: float, room: float) -> Array:
		var a := minf(e0, room); var b := clampf(e1, a, maxf(a, room))
		var ua := (a - e0) / (e1 - e0); var ub := (b - e0) / (e1 - e0)
		return [[ArtKit.pp(pth, s, side * (W + a), lerpf(y0, y1, ua)), Vector2(ua, s)], [ArtKit.pp(pth, s, side * (W + b), lerpf(y0, y1, ub)), Vector2(ub, s)]]
	for i in range(1, ss.size()):
		var room := _cap(pth, (float(ss[i - 1]) + float(ss[i])) * 0.5, side) - W - CAP_MARGIN
		var p: Array = row.call(float(ss[i - 1]), room); var q: Array = row.call(float(ss[i]), room)
		for v in [p[0], q[0], p[1], p[1], q[0], q[1]]:
			st.set_uv(v[1]); st.add_vertex(v[0])
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat; mi.extra_cull_margin = 16384.0
	mi.name = "TerrVBand_%d_%d" % [int(s0), int(side)]
	return mi

## TOUGE: a roadside band through the profile points prof ([[e, y], ...], e = metres beyond the road edge), clamped per s to the
## room the course leaves (course.cap_at) like _vband, plus a skirt_m curtain hanging under the outer edge: where another leg
## cuts the band the step between the two levels is closed, so no camera sees the clear colour through it.
func _pband(pth, s0: float, s1: float, side: float, W: float, prof: Array, mat: ShaderMaterial, skirt: float, step := 2.0, dy := 0.0) -> MeshInstance3D:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var e0: float = prof[0][0]; var span: float = maxf(0.01, float(prof[1][0]) - e0)   # UV.x keeps the first segment's density
	# Strip edges: every step AND every course.gd cap sample boundary. The room (tband), tup, tstep and tskmax are constant
	# between two cap samples, so each strip is built from ITS OWN interval's values at both ends. Rows used to be clamped
	# each to the room at their own s and shared by both strips: where the room jumped between two rows (5 m -> 100 m at a
	# boundary with another leg) one triangle fanned 75 m across that leg, a wedge over its road / lot / hillside (pt155u,
	# TERRAIN_CHECK TerrPBand_463_1 at s 730). A room step at a boundary is now a straight edge across the band, closed by a
	# skirt panel under the wider strip's extra width.
	var ss: Array = _srows(pth, s0, s1, step)
	var room_of := func(sm: float) -> float:
		var room := _tband(pth, sm, side) - W
		return maxf(minf(e0, room), room)
	# one row at sv for the interval around sm, with columns at the profile points plus the band ends of the strips on both
	# sides of this row (extra), so two strips meeting on a row share every vertex up to the narrower one's end (no T-junction
	# cracks along a room step)
	var row_at := func(sv: float, sm: float, extra: Array) -> Array:
		var hi: float = room_of.call(sm)
		var es := []
		for p in prof: es.append(clampf(float(p[0]), minf(e0, hi), hi))
		for x in extra:
			if float(x) > minf(e0, hi) and float(x) < hi: es.append(float(x))
		es.sort()
		var row := []; var last_e := -1e9
		for e in es:
			if absf(float(e) - last_e) < 1e-3: continue
			last_e = e
			row.append([ArtKit.pp(pth, sv, side * (W + e), Course.prof_y(prof, e) + dy), Vector2((e - e0) / span, sv), e])
		var up: float = float(pth.tup_at(sm, side)) if pth.has_method("tup_at") else 0.0
		var sk := 0.0
		if skirt > 0.0:   # down to the neighbour's terrain where a cliff meets it (tstep), at least skirt_m
			sk = maxf(skirt, _tstep(pth, sm, side) + 1.0)
			if pth.has_method("tskmax_at"): sk = minf(sk, float(pth.tskmax_at(sm, side)))   # never into another road's clear space
		return [row, up, sk, hi]
	var tri := func(a: Array, b: Array, c: Array) -> void:
		for v in [a, b, c]:
			st.set_uv(v[1]); st.add_vertex(v[0])
	var prev: Array = []
	for i in range(1, ss.size()):
		var sa: float = ss[i - 1]; var sb: float = ss[i]; var sm := (sa + sb) * 0.5
		var hl: float = room_of.call(sa - 1e-3) if i > 1 else room_of.call(sm)
		var hr: float = room_of.call(sb + 1e-3) if i < ss.size() - 1 else room_of.call(sm)
		var A: Array = row_at.call(sa, sm, [hl]); var B: Array = row_at.call(sb, sm, [hr])
		var p: Array = A[0]; var q: Array = B[0]
		var ia := 0; var ib := 0   # zipper between the two rows (both end at this strip's band end)
		while ia < p.size() - 1 or ib < q.size() - 1:
			var adv_a := ib >= q.size() - 1 or (ia < p.size() - 1 and float(p[ia + 1][2]) <= float(q[ib + 1][2]))
			if adv_a: tri.call(p[ia], q[ib], p[ia + 1]); ia += 1
			else: tri.call(p[ia], q[ib], q[ib + 1]); ib += 1
		var sk: float = A[2]
		if sk > 0.0:   # skirt under the band end
			var a0: Array = p[-1]; var b0: Array = q[-1]
			tri.call(a0, b0, [(a0[0] as Vector3) - Vector3(0, sk, 0), Vector2(0, sa)]); tri.call([(a0[0] as Vector3) - Vector3(0, sk, 0), Vector2(0, sa)], b0, [(b0[0] as Vector3) - Vector3(0, sk, 0), Vector2(0, sb)])
		# the cut face continues up to the leg above (course.gd tup): its top runs through the sample heights (tup_lerp), so it
		# follows that surface; a per-interval constant (min / max of two samples) left steps of up to 2 m under it (a slot to the
		# sky, lot replay t05_lot_overview) or over it
		var ua: float = A[1]; var ub: float = ua
		if ua > 0.0 and pth.has_method("tup_lerp"): ua = maxf(0.0, float(pth.tup_lerp(sa, side))); ub = maxf(0.0, float(pth.tup_lerp(sb, side)))
		if ua > 0.0 or ub > 0.0:
			var a0: Array = p[-1]; var b0: Array = q[-1]
			var a1 := [(a0[0] as Vector3) + Vector3(0, ua, 0), (a0[1] as Vector2) + Vector2(ua / span, 0)]
			var b1 := [(b0[0] as Vector3) + Vector3(0, ub, 0), (b0[1] as Vector2) + Vector2(ub / span, 0)]
			tri.call(a0, b0, a1); tri.call(a1, b0, b1)
		if not prev.is_empty() and absf(float(prev[3]) - float(A[3])) > 0.05:   # room step at sa: skirt panel under the wider side's extra edge
			var W2: Array = prev if float(prev[3]) > float(A[3]) else A
			var e_lo := minf(float(prev[3]), float(A[3])); var e_hi := maxf(float(prev[3]), float(A[3])); var skd: float = maxf(float(W2[2]), 1.0)
			var cols := []
			for v in (W2[0] as Array):
				if float(v[2]) >= e_lo - 1e-3: cols.append(v)
			for g in range(1, cols.size()):
				var ta: Array = cols[g - 1]; var tb: Array = cols[g]
				var ba := [(ta[0] as Vector3) - Vector3(0, skd, 0), Vector2(0, sa)]; var bb := [(tb[0] as Vector3) - Vector3(0, skd, 0), Vector2(0, sa)]
				tri.call(ta, tb, ba); tri.call(ba, tb, bb)
		prev = B
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat; mi.extra_cull_margin = 16384.0
	mi.name = "TerrPBand_%d_%d" % [int(s0), int(side)]
	return mi

## TOUGE gallery wall on side at we m past the edge: from this road's ground (its profile at we, 1 m into it) up to the leg
## overhead (course.groof_at, +0.5 m into it), on every 2 m step where both ends have a leg overhead; closed end faces are not
## needed, the overhead leg's own bands/skirts meet the wall's ends.
const GAP_TOP := 0.05
func _gallery(pth, s0: float, s1: float, side: float, W: float, we: float, p_out: Array, p_in: Array, mat: ShaderMaterial) -> MeshInstance3D:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var s := s0; var nq := 0
	while s < s1 - 1e-6:
		var s2 := minf(s + 2.0, s1)
		# the wall top stays GAP_TOP under the surface overhead (pt155u TERRAIN_CHECK: + 0.5 m "into it" stood 0.5 m up through
		# turn 5's road and lot, s 448-536); that surface is double-sided and runs on over the wall line, so it closes the top
		var ra: float = float(pth.groof_at(s, side, true)); var rb: float = float(pth.groof_at(s2, side, true))
		if ra > 0.0 and rb > 0.0:
			var pa: Array = p_out if _drop(pth, s) == side else p_in; var pb: Array = p_out if _drop(pth, s2) == side else p_in
			var wa: float = float(pth.gwall_at(s, side)) if pth.has_method("gwall_at") else we; var wb: float = float(pth.gwall_at(s2, side)) if pth.has_method("gwall_at") else we
			var a0 := ArtKit.pp(pth, s, side * (W + wa), Course.prof_y(pa, wa) - 1.0); var a1 := ArtKit.pp(pth, s, side * (W + wa), ra - GAP_TOP)
			var b0 := ArtKit.pp(pth, s2, side * (W + wb), Course.prof_y(pb, wb) - 1.0); var b1 := ArtKit.pp(pth, s2, side * (W + wb), rb - GAP_TOP)
			for v in [[a0, Vector2(0, s)], [b0, Vector2(0, s2)], [a1, Vector2(ra / 4.0, s)], [a1, Vector2(ra / 4.0, s)], [b0, Vector2(0, s2)], [b1, Vector2(rb / 4.0, s2)]]:
				st.set_uv(v[1]); st.add_vertex(v[0])
			nq += 1
		s = s2
	var mi := MeshInstance3D.new(); mi.name = "TerrGallery%s" % ("R" if side > 0.0 else "L")
	if nq > 0: mi.mesh = st.commit()
	mi.material_override = mat; mi.extra_cull_margin = 16384.0
	return mi

## TOUGE: the cross-section face at s between two side profiles (outside slope -> inside cut where the drop side flips)
func _xface(pth, s: float, side: float, W: float, pa: Array, pb: Array, mat: ShaderMaterial) -> MeshInstance3D:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var room := _tband(pth, s, side) - W   # same end as the bands it closes
	var es := []
	for p in pa + pb: es.append(minf(float(p[0]), maxf(room, 0.0)))
	es.sort()
	var cols := []
	for e in es:
		if not cols.is_empty() and absf(float(e) - float(cols[-1][0])) < 0.05: continue
		cols.append([e, ArtKit.pp(pth, s, side * (W + e), Course.prof_y(pa, e)), ArtKit.pp(pth, s, side * (W + e), Course.prof_y(pb, e))])
	for i in range(1, cols.size()):
		var a: Array = cols[i - 1]; var b: Array = cols[i]
		for v in [a[1], a[2], b[1], b[1], a[2], b[2]]:
			st.set_uv(Vector2(0, s)); st.add_vertex(v)
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat; mi.extra_cull_margin = 16384.0
	mi.name = "TerrXFace_%d_%d" % [int(s), int(side)]
	return mi

## [s0, s1, drop side] runs of pth over [a, b] (course.drop_runs; a plain straight has drop_const)
static func _runs(pth, a: float, b: float) -> Array:
	var cuts := [a]
	for r in pth.get("drop_runs") if pth.get("drop_runs") != null else []:
		if float(r[0]) > a and float(r[0]) < b: cuts.append(float(r[0]))
	cuts.append(b)
	var out := []
	for i in cuts.size() - 1: out.append([cuts[i], cuts[i + 1], _drop(pth, (cuts[i] + cuts[i + 1]) * 0.5)])
	return out

static func _drop(pth, s: float) -> float:
	return float(pth.drop_at(s)) if pth.has_method("drop_at") else 1.0

## TOUGE course, Arthur 2026-11-20 items 1-2: cedar cards stand on the authored ground, not at a fixed height over the road (the
## inside ones floated 7.6 m up over the hairpins' low ground; the overhead road's outside ones hung into the gallery below).
## Cards keep their streamed (s, |d|) slot; |d| is snapped to 0.5 m lanes and each lane gets the ground height under it every
## metre of s (touge_env.ground_y on the *_col proxies, 1 m interpolation in stream()). NAN = no card there: no ground within
## reach, or another leg's road (plus its gallery line and the card's half width) runs between that ground and the card top.
const CEDAR_LANE := 0.5; const CEDAR_SINK := 0.3; const CEDAR_HMAX := 16.0
func _cedar_lanes(pth, items: Array, a0: float, rng: float, W: float, D: Dictionary) -> Dictionary:
	var gw: float = float(D.get("terrain", {}).get("gallery_wall_m", 3.5))
	var cg = CamGuard.new(); cg.setup(pth, W, D, {"margin_m": 0.3, "rail_box": [0.33, 0.7, 0.85], "lamp_r_m": 0.3}, {}, [])
	var lanes := {}
	for it in items:
		if not bool(it.get("card", false)) or not it.has("kind"): continue
		var mag := snappedf(float(it.mag), CEDAR_LANE); it.mag = mag
		var key := "%d_%.1f" % [int(it.kind), mag]; it.lane = key
		if lanes.has(key): continue
		var tab := PackedFloat32Array(); tab.resize(int(ceil(rng)) + 2)
		for i in tab.size():
			var sv := a0 + float(i)
			var dd_d: float = float(it.kind) * _drop(pth, sv) * mag
			var q: Dictionary = pth.point(sv, dd_d)
			var ry: float = float(pth.elev(sv, 0.0))
			var gy: float = TougeEnv.ground_y(float(q.x), float(q.z), ry + 20.0, 60.0)
			if not is_nan(gy):
				for L in cg.legs_at(float(q.x), float(q.z), W + gw + 3.0):
					var ls: float = L[0]
					if absf(ls - sv) < 30.0 or ls < -60.0 or ls > pth.length + 60.0: continue   # this leg's own road
					var ly: float = float(pth.elev(ls, float(L[1])))
					if absf(float(L[1])) < W + gw + 2.5 and ly > gy - 1.0 and ly < gy + CEDAR_HMAX + 1.0: gy = NAN; break
			tab[i] = gy
		lanes[key] = tab
	return lanes

## where the authored cut stands on the inside, every metre of s: the ground 3 m past the inside edge is >= 0.5 m over the road
## edge (drop_side_check.gd DROP_SIDE_AUTHORED uses the same test). No cut = a bridge or deck (turn 4 s 319-399, turn 5 s 439-546):
## the streamed lattice modules are trimmed / hidden there instead of hanging in the air.
func _cut_table(pth, a0: float, rng: float, W: float) -> PackedByteArray:
	var tab := PackedByteArray(); tab.resize(int(ceil(rng)) + 2)
	for i in tab.size():
		var sv := a0 + float(i); var ins: float = -_drop(pth, sv)
		var q: Dictionary = pth.point(sv, ins * (W + 3.0)); var ry: float = float(pth.elev(sv, ins * W))
		var gy: float = TougeEnv.ground_y(float(q.x), float(q.z), ry + 12.0, 40.0)
		tab[i] = 1 if (not is_nan(gy) and gy >= ry + 0.5) else 0
	return tab

static func _lane_y(tab: PackedFloat32Array, a0: float, s: float) -> float:
	var u := s - a0; var i := clampi(int(floor(u)), 0, tab.size() - 2); var f := clampf(u - float(i), 0.0, 1.0)
	var y0 := tab[i]; var y1 := tab[i + 1]
	if is_nan(y0) or is_nan(y1): return NAN
	return lerpf(y0, y1, f)

## tag the last streamed item: side (for hiding over the lot), pitched to the grade, cedar card (camera-near cull)
func _tag(kind: float, pitch: bool, card := false) -> Dictionary:
	var it: Dictionary = _items_ref[-1]
	it.kind = kind; it.mag = absf(float(it.d)); it.side = kind; it.pitch = pitch; it.card = card
	return it

## TOUGE turnout parking area (Austin t114u: "a paved lot off to the side of the road with a clear entrance and exit, painted
## stalls, curbs or wheel stops, a lamp or two, maybe a vending machine or sign"). Cut into the hill on the inside, fixed to the
## course (it never scrolls; main.gd freezes the road scroll while the cars use it). Arthur's approved 16 m two-row kit is
## instanced in scenes/turnout_lot.tscn (assets/env/turnout_lot/*.glb). slot() skips any layer that already has art; empty
## slots still get the old procedural placeholders. Numbers: display.json turnout (lane depths retuned to the kit aisle).
const LOT_SCENE := preload("res://scenes/turnout_lot.tscn")
func _lot(art, pth, g: Node3D, D: Dictionary, W: float, ins: float, to: Dictionary, env = null) -> void:
	var T: Dictionary = to.cfg
	var a: float = to.s0; var b: float = to.s1; var tp: float = to.taper; var Ld: float = to.w
	var lg: TurnoutLot = LOT_SCENE.instantiate(); lg.name = "TurnoutLot"; g.add_child(lg)   # WorldVP/Dressing/CourseDressing/TurnoutLot
	var asph := _static_mat(art, "touge_road", float(D.lamp_period_m)); var curb := _static_mat(art, "street_curb", 2.0)
	var paint := _paint_mat(art, 0.9)
	var grav := _static_mat(art, "touge_gravel", 4.0); var verge := _static_mat(art, "touge_verge", 6.0)
	var e := func(dd: float) -> float: return ins * (W + dd)   # metres beyond the road edge on the inside -> signed d
	# LotArt frame for Arthur: origin at the road edge at the entrance, +X into the lot, +Z along travel, pitched to the grade
	var la := lg.get_node("LotArt") as Node3D
	var q0: Dictionary = pth.point(a, e.call(0.0)); var q1: Dictionary = pth.point(a + 1.0, e.call(0.0)); var qx: Dictionary = pth.point(a, e.call(1.0))
	var o := Vector3(q0.x, float(q0.get("y", 0.0)), q0.z)
	var bz := (Vector3(q1.x, float(q1.get("y", 0.0)), q1.z) - o).normalized(); var bx := (Vector3(qx.x, float(qx.get("y", 0.0)), qx.z) - o).normalized()
	var by := bz.cross(bx).normalized()
	if by.y < 0.0: by = -by
	la.transform = Transform3D(Basis(bx, by, bz), o)
	# Arthur's glbs are in LotArt space: copy the frame onto every slot that already has art (README drop-in note)
	for nm in ["Floor", "Curbs", "StallLines", "WheelStops", "BackWall", "HillTop", "Lamps", "Props"]:
		var sl := lg.get_node_or_null(nm) as Node3D
		if sl != null and sl.get_child_count() > 0:
			sl.transform = la.transform
	_shade_lot(art, lg)
	var n: Node3D = lg.slot("Floor")
	if n:   # floor: full depth between the tapers, tapered entrance / exit (linear in 8 slices)
		n.add_child(art.band(pth, a + tp, b - tp, e.call(-0.02), 0.03, e.call(Ld), 0.03, asph, 1.0, 4))
		for i in 8:
			var u0 := i / 8.0; var u1 := (i + 1) / 8.0
			# out to the flank modules' base line (0.7 + Ld * u, the diagonal) + 0.3 m under them: the slices used to stop at
			# Ld * u1, 0.7 m short of the base at each slice's far end, a dashed crack along both flanks (void sweep lot_top_down)
			n.add_child(art.band(pth, a + tp * u0, a + tp * u1, e.call(-0.02), 0.03, e.call(Ld * u1 + 1.0), 0.03, asph, tp / 8.0, 2))
			n.add_child(art.band(pth, b - tp * u1, b - tp * u0, e.call(-0.02), 0.03, e.call(Ld * u1 + 1.0), 0.03, asph, tp / 8.0, 2))
	# the ground the lot is cut into, under whatever floor art the Floor / Curbs slots hold: Arthur's lot_floor.glb / lot_curbs.glb
	# are fixed shapes, so the procedural taper floor above never ran and the glb's edge did not reach the yawed flank modules'
	# base (a sliver of sky along both flanks, void sweep t05_lot_exit_flank / lot_overview). 5 cm under the floor art, out to
	# 1 m under the flank base line (0.7 + Ld u) and the back modules (Ld + 0.7), in 1 m slices over the tapers.
	# ONE sheet with shared rows (outer edge 1 m past the flank / back base line, 1.7 + Ld u(s)): separate slices met in T-junctions
	# and the 1 m-step middle band stopped short of b - tp, leaving pixel cracks into the empty space under the floor (void
	# replay t05_lot_from_exit_high).
	if env == null:   # course: the ground under the lot edge is Arthur's touge_lot.glb (asphalt / gravel / cut / hill)
		var fb := Node3D.new(); fb.name = "FloorBase"; lg.add_child(fb)
		var ss := []; var s_ := a
		while s_ < b - 1e-3: ss.append(s_); s_ = minf(s_ + 1.0, b) if s_ + 1.0 < b - 0.25 else b
		ss.append(b)
		for sx in [a + tp, b - tp]:
			if not ss.has(sx): ss.append(sx)
		ss.sort()
		var fst := SurfaceTool.new(); fst.begin(Mesh.PRIMITIVE_TRIANGLES); var frows := []
		for sv in ss:
			var uu := clampf(minf(float(sv) - a, b - float(sv)) / maxf(tp, 1e-3), 0.0, 1.0)
			var row := []
			for j in 5:
				var dd := lerpf(-0.3, 1.7 + Ld * uu, j / 4.0)
				row.append([ArtKit.pp(pth, sv, e.call(dd), -0.05), Vector2(j / 4.0, sv)])
			frows.append(row)
		for i in range(1, frows.size()):
			for j in 4:
				for v in [frows[i - 1][j], frows[i][j], frows[i - 1][j + 1], frows[i - 1][j + 1], frows[i][j], frows[i][j + 1]]:
					fst.set_uv(v[1]); fst.add_vertex(v[0])
		var fmi := MeshInstance3D.new(); fmi.mesh = fst.commit(); fmi.material_override = asph; fmi.extra_cull_margin = 16384.0; fb.add_child(fmi)
	var ic: Array = T.island_d_m; var ch: float = T.curb_h_m
	n = lg.slot("Curbs")
	if n:   # island curb between the road and the lot (entrance and exit stay open), back curb, gravel strip behind it
		_box_strip(art, pth, n, a + tp + 1.0, b - tp - 1.0, e.call(ic[0]), e.call(ic[1]), ch, curb)
		_box_strip(art, pth, n, a + tp, b - tp, e.call(Ld), e.call(Ld + 0.35), ch, curb)
		# gravel strip to 0.3 m under the back modules' base: 4 m modules are chords of the curved lot edge, so a strip that ended
		# exactly at Ld + 0.7 left a crack at every module joint (void sweep lot_top_down)
		n.add_child(art.band(pth, a + tp, b - tp, e.call(Ld + 0.35), 0.03, e.call(Ld + 1.0), 0.03, grav))
	var sw: float = T.stall_w_m; var sd: float = T.stall_d_m
	var n_st := int(floor((b - a - 2.0 * tp - 2.0) / sw))
	var st0 := (a + b) * 0.5 - n_st * sw * 0.5
	n = lg.slot("StallLines")
	if n:   # perpendicular bays along the back curb: flat white paint, never inked (Cel A road-marking rule, as the chevrons)
		for i in n_st + 1:
			var sl := st0 + i * sw
			n.add_child(art.band(pth, sl - 0.06, sl + 0.06, e.call(Ld - sd), 0.045, e.call(Ld), 0.045, paint, 0.12, 2))
		n.add_child(art.band(pth, st0, st0 + n_st * sw, e.call(Ld - sd - 0.06), 0.045, e.call(Ld - sd + 0.06), 0.045, paint, 1.0, 1))
	n = lg.slot("WheelStops")
	if n:
		for i in n_st:
			var sc := st0 + (i + 0.5) * sw
			_box_strip(art, pth, n, sc - 0.8, sc + 0.8, e.call(Ld - 0.85), e.call(Ld - 0.65), 0.13, curb, 0.4)
	n = lg.slot("BackWall")
	if n:   # the inside lattice slope stepped back to the back curb, diagonal over the tapers
		var s := a + tp
		while s < b - tp - 0.1:
			_fixed_prop(art, pth, n, prop_g(art, "mtn_lattice_slope_g", 0.66), s + 2.0, e.call(Ld + 0.7), 0.0, true)
			s += float(D.lattice_step_m)
		for end in [[a, 1.0], [b, -1.0]]:   # entrance / exit flanks: modules along the taper diagonal
			var s_a: float = end[0]; var dir: float = end[1]
			var dl := Vector2(tp, Ld).length(); var nmod := int(ceil(dl / 4.0))
			for j in nmod:
				var f := (j + 0.5) / nmod
				var sm := s_a + dir * tp * f; var dm := lerpf(0.7, Ld + 0.7, f)
				var yaw := atan2(Ld, tp) * dir * (-ins)
				_fixed_prop(art, pth, n, prop_g(art, "mtn_lattice_slope_g", 0.66), sm, e.call(dm), yaw, true).scale.z = dl / nmod / 4.0 * 1.05
	n = lg.slot("HillTop")
	if n:   # Austin pt137u: the road's inside hill band (_kit6: W + 8.7 .. W + 18, y 7.6 .. 10) stepped back behind the lot. It
		# follows the cut line over the tapers too (1 m slices), so it meets the road's band at s0 / s1 with no void behind the flanks.
		# The hill continues out to the camera reach like the road's (_kit6 _pband, course.gd terrain_profile).
		if env == null:   # course: the lot hill / flank hills are Arthur's touge_lot.glb
			var hp: Array = Course.terrain_profile(D, false).slice(3)   # [18, 10] .. [reach, top]
			# capped like the road's own inside band (_pband: course.tband_at, skirts, up faces), on the lot-aware profile (course.gd
			# lot_cut): an uncapped band ran out to reach_m over / through other legs (pt155u)
			# the cut face behind the back modules is the band's first segment (from 1.5 m under the floor at Ld + 0.7): one mesh,
			# so the face / hill seam shares its vertices (a separate 2 m-row cut face left dashes of sky along the seam)
			var lp: Array = [[Ld + 0.7, -1.5]]
			for pq in Course.terrain_profile(D, false).slice(2): lp.append([float(pq[0]) + Ld, float(pq[1])])
			var hb2 := _pband(pth, a + tp, b - tp, ins, W, lp, verge, float(D.get("terrain", {}).get("skirt_m", 0.0))); hb2.name = "TerrLotHill"; n.add_child(hb2)
			# Austin pt137u item 4 (gap beside the lot): the old taper hill was 1 m slices stepped back by Ld * u from W + 8.7, but the
			# flank modules are YAWED along the taper diagonal, so their 8 m top edge runs along the diagonal's normal, not across
			# the road. The slices missed it (sky wedges behind each flank and at both back corners, void sweep lot_top_down /
			# lot_exit_flank). _lot_flank_hill builds the hill from the flank's real top line, closes it to the road's cut at s0 / s1
			# and to the back wall at the corner, and fills the corner wedge between the last flank module and the first back module.
			_lot_flank_hill(pth, n, a, 1.0, tp, Ld, hp, e, verge)
			_lot_flank_hill(pth, n, b, -1.0, tp, Ld, hp, e, verge)
		for i in int((b - a) / 4.0):   # cedars on the cut top behind the lot
			var h := lerpf(10.0, 15.0, ArtKit.hash01(i * 3.7 + 9.0))
			var c: Node3D = art.cross_card("touge_cedar_a" if ArtKit.hash01(i * 2.1) < 0.5 else "touge_cedar_b", h * 0.3333, h)
			var f2 := clampf(minf(i * 4.0, (b - a) - i * 4.0) / tp, 0.0, 1.0)
			var cp := _fixed_prop(art, pth, n, c, a + i * 4.0 + 1.0, e.call(lerpf(9.5, Ld + 9.5, f2) + ArtKit.hash01(i * 5.3) * 5.0), 0.0, false, 7.6)
			if env != null:   # on the authored hill behind the lot (Arthur item 1), not at a fixed 7.6 m
				var gy := TougeEnv.ground_y(cp.position.x, cp.position.z, cp.position.y + 20.0, 60.0)
				if is_nan(gy): cp.visible = false
				else: cp.position.y = gy - CEDAR_SINK
	n = lg.slot("Lamps")
	if n:   # two sodium lamps on the back curb, arms over the stalls, with a ground pool
		for ls in T.lamp_s_frac:
			var lamp := Node3D.new(); lamp.name = "Lamp%d" % n.get_child_count()
			var post := MeshInstance3D.new(); post.mesh = art.lamp_mesh(); post.material_override = art.env_mat; post.extra_cull_margin = 16384.0; lamp.add_child(post)
			var gl: MeshInstance3D = art.glow_sprite("glow_lamp", Color(1, 1, 1), 1.5, 0.9); gl.position = Vector3(-1.3, 6.3, 0); lamp.add_child(gl)
			var pool: MeshInstance3D = art.decal("glow_lamp", 9.0, 9.0, 0.0, true, float(T.pool_strength)); pool.position = Vector3(-1.3, 0.06, 0); lamp.add_child(pool)
			# lamp mesh arm points to local -X; the course frame has +d = right: on the left (ins < 0) the arm must point to +d
			_fixed_prop(art, pth, n, lamp, lerpf(a + tp, b - tp, float(ls)), e.call(Ld + 0.2), PI / 2.0 * (1.0 if ins < 0.0 else -1.0) + PI / 2.0, false)
	n = lg.slot("Props")
	if n:   # vending machine between the bays (districts street_vending.glb)
		_fixed_prop(art, pth, n, prop_g(art, "street_vending", 1.0, 1.0), lerpf(a + tp, b - tp, float(T.vending_s_frac)), e.call(Ld + 0.4), 0.0, false, 0.15)
	lg.set_meta("lamps", lg.lamps())
	to_lot_group = lg

## the hill behind one lot flank (s_a = lot end, dir = +1 entrance / -1 exit; e = metres beyond the edge -> signed d). The
## flank modules sit along the diagonal (s_a, 0.7) -> (s_a + dir tp, Ld + 0.7) with their 8 m depth along its normal, so their
## top edge (y 7.6) is that diagonal moved 8 m along n = (-dir Ld, tp) / |(tp, Ld)|. Rows, each [inner edge at 7.6, then the
## inside hill profile out to reach]: the road's own cut at s_a (inner edge W + 8.7) -> the top edge where it crosses s_a ->
## along the top edge -> the back wall's hill start at (s_a + dir tp, Ld + 8.7). Consecutive rows share vertices, so the
## surface is closed. Plus the corner wedge face (flank end face -> back module start face) from the floor up to 7.6.
func _lot_flank_hill(pth, parent: Node3D, s_a: float, dir: float, tp: float, Ld: float, hp: Array, e: Callable, mat: ShaderMaterial) -> void:
	var dl := Vector2(tp, Ld).length(); var ns := -dir * Ld / dl; var nd := tp / dl
	var top := func(f: float) -> Vector2: return Vector2(s_a + dir * tp * f + 8.0 * ns, 0.7 + Ld * f + 8.0 * nd)
	var f0 := clampf(8.0 * Ld / (dl * tp), 0.0, 1.0)   # where the top edge crosses s_a
	# Every seam with the cut face / corner wedge below uses the SAME (s, d) vertices: pp() maps through the curved road, so two
	# meshes that only agree on a line's end points bow apart between them (dotted pixel cracks along the flank top and the
	# corner, void replay t05_lot_top_down).
	var inner := [Vector2(s_a, 8.7)]
	var nf := maxi(2, int(ceil(tp)))
	var fs := []
	for i in nf + 1: fs.append(lerpf(f0, 1.0, float(i) / nf))
	for f in fs: inner.append(top.call(f))
	var t1: Vector2 = top.call(1.0); var c1 := Vector2(s_a + dir * tp, Ld + 8.7)
	for j in range(1, 7): inner.append(t1.lerp(c1, j / 6.0))
	var prof := [[8.7, 7.6], [18.0, 10.0]] + hp.slice(1)
	var rows := []
	var side := signf(float(e.call(0.0)))
	for q in inner:
		var row := []
		var room: float = _tband(pth, q.x, side) - float(absf(float(e.call(0.0))))   # the road's band end at this s (course.tband_at)
		for k in prof.size():
			var dd: float = minf((q as Vector2).y + float(prof[k][0]) - 8.7, maxf(room, (q as Vector2).y))
			row.append([ArtKit.pp(pth, q.x, e.call(dd), float(prof[k][1])), Vector2(float(prof[k][0]) / 9.3, q.x)])
		rows.append(row)
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(1, rows.size()):
		var p: Array = rows[i - 1]; var r: Array = rows[i]
		for k in range(1, p.size()):
			for v in [p[k - 1], r[k - 1], p[k], p[k], r[k - 1], r[k]]:
				st.set_uv(v[1]); st.add_vertex(v[0])
	# cut face behind the flank modules: base line (1.5 m under the floor, which is a thin sheet) -> top edge (7.6), a straight
	# slope 1-2 m behind the module face (as
	# the road's own cut face, _kit6), so a ray under a module's bottom edge or between its beams meets ground, not sky
	# (void sweep t05_lot_exit_flank: a sliver along the flank base)
	var fc := fs.duplicate()
	if f0 > 1e-3: fc.push_front(0.0)
	for i in fc.size() - 1:
		var fa: float = fc[i]; var fb: float = fc[i + 1]
		var ba := Vector2(s_a + dir * tp * fa, 0.7 + Ld * fa); var bb := Vector2(s_a + dir * tp * fb, 0.7 + Ld * fb)
		var ta: Vector2 = top.call(fa); var tb: Vector2 = top.call(fb)
		var q := [[ArtKit.pp(pth, ba.x, e.call(ba.y), -1.5), Vector2(0, ba.x)], [ArtKit.pp(pth, bb.x, e.call(bb.y), -1.5), Vector2(0, bb.x)],
			[ArtKit.pp(pth, ta.x, e.call(ta.y), 7.6), Vector2(1, ta.x)], [ArtKit.pp(pth, tb.x, e.call(tb.y), 7.6), Vector2(1, tb.x)]]
		for v in [q[0], q[1], q[2], q[2], q[1], q[3]]:
			st.set_uv(v[1]); st.add_vertex(v[0])
	# corner wedge: apex = last flank module's base end (s_a + dir tp, Ld + 0.7) on the floor; edges up to its top end and to the
	# back module's start top (Ld + 8.7); a fan of 6 strips so the face follows the lattice rise (7.6 over 8 m)
	var apex := Vector2(s_a + dir * tp, Ld + 0.7)
	for j in 6:
		var u0 := float(j) / 6.0; var u1 := float(j + 1) / 6.0
		var p0: Vector2 = t1.lerp(c1, u0); var p1: Vector2 = t1.lerp(c1, u1)
		var va := ArtKit.pp(pth, apex.x, e.call(apex.y), 0.03); var v0 := ArtKit.pp(pth, p0.x, e.call(p0.y), 7.6); var v1 := ArtKit.pp(pth, p1.x, e.call(p1.y), 7.6)
		for v in [[va, Vector2(0, apex.x)], [v0, Vector2(1, p0.x)], [v1, Vector2(1, p1.x)]]:
			st.set_uv(v[1]); st.add_vertex(v[0])
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat; mi.extra_cull_margin = 16384.0
	mi.name = "TerrLotFlankHill%s" % ("A" if dir > 0.0 else "B"); parent.add_child(mi)

## flat road paint (start stripe, stall lines): the chevron shader, unlit, fogged, absent from the cel G-buffer -> never inked
const PAINT_SH := preload("res://shaders/chevron_vertex_lit.gdshader")
func _paint_mat(art, gain: float) -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = PAINT_SH
	m.set_shader_parameter("tex", load("res://assets/tex/kit/env/line_white.png"))
	m.set_shader_parameter("tint", Vector3(1, 1, 1)); m.set_shader_parameter("gain", gain)
	m.render_priority = 2
	art.scroll_mats.append(m)   # district fog (apply_fog sets fog_color / near / far)
	return m

var to_lot_group: Node3D = null

## a curb-like box along pth (top + two faces), h high
func _box_strip(art, pth, parent: Node3D, s0: float, s1: float, d0: float, d1: float, h: float, mat: ShaderMaterial, step := 2.0) -> void:
	parent.add_child(art.band(pth, s0, s1, d0, h, d1, h, mat, step, 1))
	parent.add_child(art.band(pth, s0, s1, d0, 0.0, d0, h, mat, step, 1))
	parent.add_child(art.band(pth, s0, s1, d1, h, d1, 0.0, mat, step, 1))
	for sv in [s0, s1]:   # end caps
		var q0 := ArtKit.pp(pth, sv, d0); var q1 := ArtKit.pp(pth, sv, d1)
		var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
		for v in [[q0, Vector2(0, 0)], [q1, Vector2(1, 0)], [q0 + Vector3(0, h, 0), Vector2(0, 1)], [q1, Vector2(1, 0)], [q1 + Vector3(0, h, 0), Vector2(1, 1)], [q0 + Vector3(0, h, 0), Vector2(0, 1)]]:
			st.set_uv(v[1]); st.add_vertex(v[0])
		var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat; mi.extra_cull_margin = 16384.0; parent.add_child(mi)

## a prop fixed to the course at (s, d): Arthur's convention (local +X away from the road, right side turned round), pitched to the grade
func _fixed_prop(_art, pth, parent: Node3D, n: Node3D, s: float, d: float, yaw: float, pitch: bool, y := 0.0) -> Node3D:
	var q: Dictionary = pth.point(s, d)
	n.position = Vector3(q.x, y + float(q.get("y", 0.0)), q.z)
	var gr := atan((float(pth.point(s + 1.0, d).get("y", 0.0)) - float(pth.point(s - 1.0, d).get("y", 0.0))) * 0.5) if pitch else 0.0
	n.rotation = Vector3(-gr * (-1.0 if d > 0.0 else 1.0), atan2(q.tx, q.tz) + (PI if d > 0.0 else 0.0) + yaw, 0.0)
	parent.add_child(n)
	return n

## glb prop with Arthur's per-instance gain (district_preview.gd:371 _shade): materials keyed by name + gain
static var _gmats := {}
func prop_g(art, n: String, gain: float, emit_gain := 1.0) -> Node3D:
	var inst: Node3D = WanganDressing._scene(n).instantiate()
	_shade_g(art, inst, gain, emit_gain)
	return inst

func _shade_g(art, n: Node, gain: float, emit_gain: float) -> void:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		for si in mi.mesh.get_surface_count():
			var src := mi.get_active_material(si)
			var nm: String = src.resource_name if src != null else ""
			var key := "%d|%s|%.2f|%.2f" % [art.get_instance_id(), nm, gain, emit_gain]
			if not _gmats.has(key):
				var m := ShaderMaterial.new(); m.shader = ArtKit.SCROLL_SH
				var ep := "res://assets/tex/kit/env/%s.png" % nm.to_lower()
				m.set_shader_parameter("tex", load(ep) if ResourceLoader.exists(ep) else ((src as BaseMaterial3D).albedo_texture if src is BaseMaterial3D else null))
				m.set_shader_parameter("tile", 1.0); m.set_shader_parameter("scroll_m", 0.0)
				m.set_shader_parameter("gain", emit_gain if nm.begins_with("Emit_") else gain)
				if nm.begins_with("Emit_"): m.set_shader_parameter("cel_k", 0.0); m.set_shader_parameter("flatten", 0.0)
				m.set_meta("persist", true); art.fogify(m); _gmats[key] = m
			mi.set_surface_override_material(si, _gmats[key])
		mi.extra_cull_margin = 16384.0
	for ch in n.get_children(): _shade_g(art, ch, gain, emit_gain)

## Arthur's turnout kit shaders (art/kits/turnout_lot/README.md): floor/verge/cut/cedars = scroll + soft_surface;
## stall lines / road paint = chevron (never inked); Emit_* = cel_k 0; curbs, wheel stops, lattice, poles, sign,
## vending body = default prop toon + ink. Textures come from the imported glb.
static var _lot_mats := {}
func _shade_lot(art, root: Node) -> void:
	_shade_lot_n(art, root)

func _shade_lot_n(art, n: Node) -> void:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		for si in mi.mesh.get_surface_count():
			var src := mi.get_active_material(si)
			var nm: String = src.resource_name if src != null else String(n.name)
			var kind := _lot_kind(nm)
			var tex: Texture2D = _lot_tex(src)
			var key := "%d|%s|%s" % [art.get_instance_id(), nm, kind]
			if not _lot_mats.has(key):
				# glow / pool: alpha lives in the texture; scroll.gdshader would hard-discard a < 0.5.
				# Additive unshaded, same idea as art.decal, so the 6 m ovals stay soft.
				if kind == "pool":
					var sm := StandardMaterial3D.new()
					sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
					sm.albedo_texture = tex
					sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
					sm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
					sm.albedo_color = Color(1, 1, 1, 0.7)
					sm.disable_fog = true
					sm.render_priority = 1
					sm.set_meta("persist", true)
					_lot_mats[key] = sm
				else:
					var m := ShaderMaterial.new()
					if kind == "paint":
						m.shader = PAINT_SH
						m.set_shader_parameter("tex", tex)
						m.set_shader_parameter("tint", Vector3(1, 1, 1))
						m.set_shader_parameter("gain", 0.95)
						m.render_priority = 2
					else:
						m.shader = ArtKit.SCROLL_SH
						m.set_shader_parameter("tex", tex)
						m.set_shader_parameter("tile", 1.0)
						m.set_shader_parameter("scroll_m", 0.0)
						m.set_shader_parameter("gain", 1.0)
						if kind == "soft":
							m.set_shader_parameter("soft_surface", 1.0)
						elif kind == "emit":
							m.set_shader_parameter("cel_k", 0.0)
							m.set_shader_parameter("flatten", 0.0)
					m.set_meta("persist", true)
					art.fogify(m)
					_lot_mats[key] = m
			mi.set_surface_override_material(si, _lot_mats[key])
		mi.extra_cull_margin = 16384.0
	for ch in n.get_children():
		_shade_lot_n(art, ch)

## Arthur's kit exports Emission-only materials (albedo_texture is empty; the png is on emission_texture).
## Linked lattice modules from lib/ still use albedo.
func _lot_tex(src) -> Texture2D:
	if src is BaseMaterial3D:
		var bm := src as BaseMaterial3D
		if bm.emission_texture != null:
			return bm.emission_texture
		return bm.albedo_texture
	return null

func _lot_kind(nm: String) -> String:
	var low := nm.to_lower()
	if nm.begins_with("Emit_") or low.begins_with("emit_"):
		return "emit"
	if low.begins_with("lot_paint") or low.begins_with("lot_decal") or low.find("stall_line") >= 0:
		return "paint"
	if low.find("glow") >= 0 or low.find("pool") >= 0:
		return "pool"
	if low.find("asphalt") >= 0 or low.find("verge") >= 0 or low.find("cut_slope") >= 0 or low.find("cedar") >= 0 or (low.find("road") >= 0 and low.find("paint") < 0):
		return "soft"
	return "prop"

var _items_ref: Array = []
func items_last() -> Dictionary:
	return _items_ref[-1]

## non-scrolling copy of a strip material (the lot never scrolls)
func _static_mat(art, n: String, tile: float) -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = ArtKit.SCROLL_SH
	var p := "res://assets/tex/kit/env/%s.png" % n
	m.set_shader_parameter("tex", load(p) if ResourceLoader.exists(p) else art.tex(n)); m.set_shader_parameter("tile", tile); m.set_shader_parameter("scroll_m", 0.0)
	return art.fogify(m)

func _envmat(art, n: String, tile: float) -> ShaderMaterial:
	var m := ShaderMaterial.new(); m.shader = ArtKit.SCROLL_SH
	m.set_shader_parameter("tex", load("res://assets/tex/kit/env/%s.png" % n)); m.set_shader_parameter("tile", tile)
	m.set_meta("scrolls", true)
	return art.fogify(m)

## streamed items wrap over [a0, a0 + range) with the road scroll; fixed items (touge lamps) stay put. TOUGE kit6: items on the
## inside are hidden over the turnout lot (dd.lot = [s0, s1]); props follow Arthur's orientation (local +X away from the road).
static func stream(dd: Dictionary, scroll_m: float) -> void:
	var lot: Array = dd.get("lot", [])
	for it in dd.items:
		var s: float = float(it.base) if it.get("fixed", false) else dd.a0 + fposmod(float(it.base) - scroll_m - dd.a0, dd.range)
		var dd_d: float = float(it.d)
		if it.has("kind"): dd_d = float(it.kind) * _drop(dd.pth, s) * float(it.mag)   # TOUGE: inside / outside of the corner at s
		var p: Dictionary = dd.pth.point(s, dd_d)
		var o := it.obj as Node3D
		o.position = Vector3(p.x, float(it.get("y", 0.0)) + float(p.get("y", 0.0)), p.z)
		var grounded := true
		if it.has("lane") and dd.has("cedar_lanes"):   # authored ground (cedar lanes); no ground / over a road = not drawn
			var gy := _lane_y(dd.cedar_lanes[it.lane], dd.a0, s)
			grounded = not is_nan(gy)
			if grounded: o.position.y = gy - CEDAR_SINK
		if it.has("side"):   # TOUGE kit6 (Arthur's prop convention, district_preview.gd:365-367)
			var gr := 0.0
			if bool(it.pitch): gr = atan((float(dd.pth.point(s + 1.0, dd_d).get("y", 0.0)) - float(dd.pth.point(s - 1.0, dd_d).get("y", 0.0))) * 0.5)
			o.rotation = Vector3(-gr * (-1.0 if dd_d > 0.0 else 1.0), atan2(p.tx, p.tz) + (PI if dd_d > 0.0 and not bool(it.card) else 0.0), 0.0)
			var on_lot_side: bool = not lot.is_empty() and signf(dd_d) == signf(float(dd.get("lot_side", -1.0)))
			var fits: bool = not it.has("reach") or float(it.reach) + float(dd.get("W", 0.0)) <= _cap(dd.pth, s, signf(dd_d)) - CAP_MARGIN
			var over_lot: bool = on_lot_side and s > float(lot[0]) - 2.0 and s < float(lot[1]) + 2.0
			if it.has("lattice"):
				# A 4 m module takes the side of its centre. It is trimmed (scaled along s about the kept part's middle, as the lot's own
				# flank modules are) instead of hidden, so the cut is always faced whatever the scroll:
				#  - Austin pt137u item 4: at the lot ends, to the part outside the lot (hiding left a 0..4 m gap that moved with the treadmill);
				#  - Arthur 2026-11-20 item 3: at a drop-side flip (course.drop_runs), to the part on its centre's side, so it never runs
				#    past the flip off the cut and its concrete wing wall (s 63, 253, 463, 647, 729, 799, 975).
				o.scale.z = 1.0
				var half: float = float(it.lattice) * 0.5; var lo := s - half; var hi := s + half
				for f in dd.get("flips", []):
					if float(f) > lo and float(f) < hi:
						if float(f) > s: hi = float(f)
						else: lo = float(f)
				if dd.has("cut"):   # course: only on the authored cut (no module on a bridge / deck, trimmed at its ends)
					var ct: PackedByteArray = dd.cut; var ci := clampi(int(round(s - float(dd.a0))), 0, ct.size() - 1)
					if ct[ci] == 0: hi = lo
					else:
						var j := ci
						while j > 0 and ct[j - 1] == 1 and float(dd.a0) + float(j) > lo: j -= 1
						lo = maxf(lo, float(dd.a0) + float(j) - 0.5)
						j = ci
						while j < ct.size() - 1 and ct[j + 1] == 1 and float(dd.a0) + float(j) < hi: j += 1
						hi = minf(hi, float(dd.a0) + float(j) + 0.5)
				if over_lot or (on_lot_side and hi > float(lot[0]) and lo < float(lot[1])):
					if lo < float(lot[0]) and s < float(lot[0]) + half: hi = minf(hi, float(lot[0]))
					elif hi > float(lot[1]) and s > float(lot[1]) - half: lo = maxf(lo, float(lot[1]))
					else: hi = lo   # wholly over the lot
				over_lot = hi - lo < 0.2
				if not over_lot and (absf(lo - (s - half)) > 1e-4 or absf(hi - (s + half)) > 1e-4):
					var sm: float = (lo + hi) * 0.5
					var pm: Dictionary = dd.pth.point(sm, dd_d)
					o.position = Vector3(pm.x, float(it.get("y", 0.0)) + float(pm.get("y", 0.0)), pm.z)
					o.rotation.y = atan2(pm.tx, pm.tz) + PI if dd_d > 0.0 else atan2(pm.tx, pm.tz)
					o.scale.z = (hi - lo) / float(it.lattice)
			o.visible = fits and not over_lot and grounded
		else:
			o.rotation.y = atan2(p.tx, p.tz) + float(it.get("yaw", 0.0))   # WANGAN: y / yaw per item

func _ready() -> void:
	if Engine.is_editor_hint(): _editor_build()

func _editor_build() -> void:
	clear()
	if not preview_in_editor: return
	var disp := ArtKit.load_json(display_spec); var cfg := ArtKit.load_json(race_config)
	var art = ArtKit.new(disp)
	var tr := TrackRoad.build_course(disp, cfg)
	stream(build(art, tr.course, -60.0, tr.course.length + 60.0, district, "CourseDressing"), 0.0)
	art.apply_fog(district)
	if not preview_fog:
		for m in art.scroll_mats: m.set_shader_parameter("fog_amount", 0.0)
