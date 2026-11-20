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
const WanganDressing = preload("res://scripts/wangan_dressing.gd")

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
	_items_ref = items
	var sp := TrackRoad.span(D, s0, s1); var a0: float = sp[0]; var rng: float = sp[1]
	var add := func(obj: Node3D, base: float, d: float) -> void:
		g.add_child(obj); items.append({"obj": obj, "base": base, "d": d})
	for n in int(rng / per):
		for L in D.lamps:
			var side: float = L[1]
			var lamp := Node3D.new()
			var post := MeshInstance3D.new(); post.mesh = art.lamp_mesh(); post.material_override = art.env_mat; post.extra_cull_margin = 16384.0; lamp.add_child(post)
			var gl: MeshInstance3D = art.glow_sprite("glow_lamp", Color(1, 1, 1), 1.5, 0.9)  # tinted texture (make_tone_tex.py per-lamp), 1.5 m billboard at 0.9 (build_v5.py:276)
			gl.position = Vector3(-1.3, 6.3, 0); lamp.add_child(gl)
			lamp.scale.x = side  # arm reaches over the road on either side
			var dsd := _drop(pth, a0 + n * per + float(L[0]))   # TOUGE: lamps on the outside of the corner at their spot (Austin t121 item 11)
			var ld: float = (W + float(D.lamp_out_d_m)) * dsd if bool(D.get("kit6", false)) else side * (float(D.lamp_post_d_m) if D.has("lamp_post_d_m") else W + 0.6)
			if bool(D.get("kit6", false)): lamp.scale.x = dsd   # arm reaches back over the road
			add.call(lamp, a0 + n * per + float(L[0]), ld)
			if bool(D.get("kit6", false)): items[-1].fixed = true; items[-1].lamp = true   # Austin t116u: lamps never scroll (the treadmill moves everything else)
	if dk == "touge" and bool(D.get("kit6", false)):   # TOUGE race: Arthur's 6 m touge kit (display.json districts.touge _touge6 / _kit6_doc)
		_kit6(art, pth, g, add, a0, rng, D, W, opts.get("turnout", {}))
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
func _kit6(art, pth, g: Node3D, add: Callable, a0: float, rng: float, D: Dictionary, W: float, to: Dictionary) -> void:
	var grav := _envmat(art, "touge_gravel", 4.0); var verge: ShaderMaterial = art.strip_mat("touge_verge", 6.0)
	var gw: float = D.gravel_w_m
	var lot := []   # course s range the lot replaces on the inside
	if not to.is_empty(): lot = [float(to.s0), float(to.s1)]
	# static bands per drop run (Austin t121 item 11: outside of each corner = guardrail + drop, inside = cut slope / lattice)
	for run in _runs(pth, a0, a0 + rng):
		var r0: float = run[0]; var r1: float = run[1]; var out: float = run[2]; var ins := -out
		var inside_runs := [[r0, r1]]
		if not lot.is_empty() and lot[1] > r0 and lot[0] < r1: inside_runs = [[r0, maxf(r0, lot[0])], [minf(r1, lot[1]), r1]]
		for r in inside_runs:
			if r[1] - r[0] < 0.5: continue
			g.add_child(_vband(art, pth, r[0], r[1], ins, W, 0.0, 0.02, gw, 0.02, grav))
			g.add_child(_vband(art, pth, r[0], r[1], ins, W, 8.7, 7.6, 18.0, 10.0, verge))
		g.add_child(_vband(art, pth, r0, r1, out, W, 0.0, 0.0, float(D.verge_out_w_m), 0.0, verge))
		g.add_child(_vband(art, pth, r0, r1, out, W, 0.55, 0.0, 9.0, -7.5, verge))
	# streamed modules: kind -1 = inside, +1 = outside; stream() puts them on the side the course has at their current s
	var s := a0
	while s < a0 + rng:   # lattice cut slope, 4 m modules (Arthur v2: s + 2, -(W + 0.7), gain 0.66)
		add.call(prop_g(art, "mtn_lattice_slope_g", 0.66), s + 2.0, W + gw); _tag(-1.0, true).reach = 5.7
		s += float(D.lattice_step_m)
	var k := 0; s = a0
	while s < a0 + rng:
		var h := lerpf(10.0, 15.0, ArtKit.hash01(k * 2.3))
		var c: Node3D = art.cross_card("touge_cedar_a" if ArtKit.hash01(k * 1.7) < 0.5 else "touge_cedar_b", h * 0.3333, h)
		add.call(c, s + ArtKit.hash01(k) * 2.0, W + 9.5 + ArtKit.hash01(k * 5.1) * 6.0); var ti: Dictionary = _tag(-1.0, false, true); ti.y = 7.6; ti.reach = float(ti.mag) - W + 1.0
		s += 4.0; k += 1
	s = a0
	while s < a0 + rng:
		add.call(prop_g(art, "touge_guardrail", 1.0), s, W + 0.45); _tag(1.0, true).reach = 0.8
		s += float(D.guardrail_step_m)
	k = 0; s = a0
	while s < a0 + rng:
		var h2 := lerpf(11.0, 16.0, ArtKit.hash01(k * 4.7 + 1.0))
		var c2: Node3D = art.cross_card("touge_cedar_a" if ArtKit.hash01(k * 1.3) < 0.5 else "touge_cedar_b", h2 * 0.3333, h2)
		add.call(c2, s + ArtKit.hash01(k * 2.0) * 4.0, W + 5.0 + ArtKit.hash01(k * 7.3) * 14.0); var to2: Dictionary = _tag(1.0, false, true); to2.y = -h2 * 0.55 - 2.0; to2.reach = float(to2.mag) - W + 1.0
		s += 3.6; k += 1
	for dl in [[a0 + 2.0, 1.0, W + 0.62], [a0 + 6.0, -1.0, W + 0.5]]:   # Arthur v2: two delineator rows, 8 m apart
		s = dl[0]
		while s < a0 + rng:
			add.call(prop_g(art, "mtn_delineator", 1.0, 0.55), s, dl[2]); _tag(dl[1], false)
			s += 8.0
	if not to.is_empty(): _lot(art, pth, g, D, W, -_drop(pth, (lot[0] + lot[1]) * 0.5), to)

## TOUGE: roadside band at e0..e1 m beyond the road edge on side (heights y0..y1, linear in e), clamped per s to the room the course
## leaves on that side (course.cap_at: hairpin interiors / tight arcs), so bands of the two legs never overlap or fold over
const CAP_MARGIN := 0.4
static func _cap(pth, s: float, side: float) -> float:
	return float(pth.cap_at(s, side)) if pth.has_method("cap_at") else 1e3

func _vband(art, pth, s0: float, s1: float, side: float, W: float, e0: float, y0: float, e1: float, y1: float, mat: ShaderMaterial, step := 2.0) -> MeshInstance3D:
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rows := []
	var s := s0
	while true:
		var room := _cap(pth, s, side) - W - CAP_MARGIN
		var a := minf(e0, room); var b := clampf(e1, a, maxf(a, room))
		var ua := (a - e0) / (e1 - e0); var ub := (b - e0) / (e1 - e0)
		rows.append([[ArtKit.pp(pth, s, side * (W + a), lerpf(y0, y1, ua)), Vector2(ua, s)], [ArtKit.pp(pth, s, side * (W + b), lerpf(y0, y1, ub)), Vector2(ub, s)]])
		if s >= s1 - 1e-6: break
		s = minf(s + step, s1)
	for i in range(1, rows.size()):
		var p: Array = rows[i - 1]; var q: Array = rows[i]
		for v in [p[0], q[0], p[1], p[1], q[0], q[1]]:
			st.set_uv(v[1]); st.add_vertex(v[0])
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = mat; mi.extra_cull_margin = 16384.0
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
func _lot(art, pth, g: Node3D, D: Dictionary, W: float, ins: float, to: Dictionary) -> void:
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
			n.add_child(art.band(pth, a + tp * u0, a + tp * u1, e.call(-0.02), 0.03, e.call(Ld * u1), 0.03, asph, tp / 8.0, 2))
			n.add_child(art.band(pth, b - tp * u1, b - tp * u0, e.call(-0.02), 0.03, e.call(Ld * u1), 0.03, asph, tp / 8.0, 2))
	var ic: Array = T.island_d_m; var ch: float = T.curb_h_m
	n = lg.slot("Curbs")
	if n:   # island curb between the road and the lot (entrance and exit stay open), back curb, gravel strip behind it
		_box_strip(art, pth, n, a + tp + 1.0, b - tp - 1.0, e.call(ic[0]), e.call(ic[1]), ch, curb)
		_box_strip(art, pth, n, a + tp, b - tp, e.call(Ld), e.call(Ld + 0.35), ch, curb)
		n.add_child(art.band(pth, a + tp, b - tp, e.call(Ld + 0.35), 0.03, e.call(Ld + 0.7), 0.03, grav))
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
	if n:
		n.add_child(art.band(pth, a + tp, b - tp, e.call(Ld + 8.7), 7.6, e.call(Ld + 18.0), 10.0, verge))
		for i in int((b - a) / 4.0):   # cedars on the cut top behind the lot
			var h := lerpf(10.0, 15.0, ArtKit.hash01(i * 3.7 + 9.0))
			var c: Node3D = art.cross_card("touge_cedar_a" if ArtKit.hash01(i * 2.1) < 0.5 else "touge_cedar_b", h * 0.3333, h)
			var f2 := clampf(minf(i * 4.0, (b - a) - i * 4.0) / tp, 0.0, 1.0)
			_fixed_prop(art, pth, n, c, a + i * 4.0 + 1.0, e.call(lerpf(9.5, Ld + 9.5, f2) + ArtKit.hash01(i * 5.3) * 5.0), 0.0, false, 7.6)
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
		if it.has("side"):   # TOUGE kit6 (Arthur's prop convention, district_preview.gd:365-367)
			var gr := 0.0
			if bool(it.pitch): gr = atan((float(dd.pth.point(s + 1.0, dd_d).get("y", 0.0)) - float(dd.pth.point(s - 1.0, dd_d).get("y", 0.0))) * 0.5)
			o.rotation = Vector3(-gr * (-1.0 if dd_d > 0.0 else 1.0), atan2(p.tx, p.tz) + (PI if dd_d > 0.0 and not bool(it.card) else 0.0), 0.0)
			var on_lot_side: bool = not lot.is_empty() and signf(dd_d) == signf(float(dd.get("lot_side", -1.0)))
			var fits: bool = not it.has("reach") or float(it.reach) + float(dd.get("W", 0.0)) <= _cap(dd.pth, s, signf(dd_d)) - CAP_MARGIN
			o.visible = fits and not (on_lot_side and s > float(lot[0]) - 2.0 and s < float(lot[1]) + 2.0)
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
