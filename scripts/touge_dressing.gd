## touge_dressing.tscn: district dressing along the road (B.5b Touge frames: lamps, verge, guardrail, cedar cards; the
## Street branch is kept for the N90 Street district). Moved verbatim from main.gd _build_district (scene refactor 2026-11-12).
## Props stream with the RoadScroller so they stay on the pools painted into the road texture (stream()).
## @tool: in the editor it dresses the whole continuous course at scroll 0 from spec/display.json districts.<district>;
## at runtime main.gd calls build() for the straight and the course and stream() every frame.
@tool
extends Node3D
const ArtKit = preload("res://scripts/art_kit.gd")
const TrackRoad = preload("res://scripts/track_road.gd")

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
func build(art, pth, s0: float, s1: float, dk: String, nm: String) -> Dictionary:
	var D: Dictionary = art.DIST[dk]; var per: float = D.lamp_period_m; var W: float = art.road_W
	var g := Node3D.new(); g.name = nm; var items: Array = []
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
			add.call(lamp, a0 + n * per + float(L[0]), side * (float(D.lamp_post_d_m) if D.has("lamp_post_d_m") else W + 0.6))
	if dk == "touge":
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
	return {"group": g, "items": items, "a0": a0, "range": rng, "pth": pth}

static func stream(dd: Dictionary, scroll_m: float) -> void:
	for it in dd.items:
		var s: float = dd.a0 + fposmod(float(it.base) - scroll_m - dd.a0, dd.range)
		var p: Dictionary = dd.pth.point(s, it.d)
		(it.obj as Node3D).position = Vector3(p.x, 0, p.z); (it.obj as Node3D).rotation.y = atan2(p.tx, p.tz)

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
