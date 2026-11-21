## HUD layout check (Austin pt137u pic 3: "left HUD panels cut off by the screen edge", panels overlapping).
## Run under a real (xvfb) display at one window size, e.g.
##   xvfb-run -s "-screen 0 2560x1080x24" godot --path . --rendering-driver opengl3 -s res://tools/touge_race/hud_layout_check.gd -- --win 2560x1080 --out DIR --no-menu --seed 366035919
## (tools/touge_race/hud_layout_check.py runs every size). For the race HUD states SELECT Entry / Apex, TIMING (QTE), RESULT
## it renders each visible HUD panel alone into the 1280x960 HUD layer and takes its drawn pixels (alpha > 0) as the panel's
## footprint, then maps the layer into the window through the real stretch transform. FAIL when a footprint
##   - leaves the window or comes within EDGE_MIN window px of its edge (cut off), or
##   - shares pixels with another panel's footprint (overlap; the pause / finish overlays are excluded, they dim the frame).
## Saves the whole window (DisplayServer.screen_get_image) per size as hud_<W>x<H>.png.
extends SceneTree
const EDGE_MIN := 2.0
const STEP := 2   # footprint sample step in HUD px
var m
var W := 1280; var H := 960; var out_dir := "/tmp/hud_check"
var n := 0
var started := false

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	for i in args.size():
		if args[i] == "--win": var p: PackedStringArray = args[i + 1].split("x"); W = int(p[0]); H = int(p[1])
		if args[i] == "--out": out_dir = args[i + 1]
	DirAccess.make_dir_recursive_absolute(out_dir)
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	m = load("res://scenes/main.tscn").instantiate(); root.add_child(m)

func _process(_d: float) -> bool:
	n += 1
	if n == 5 and not started:
		started = true; _run()
	return false

func _frames(k: int) -> void:
	for i in k: await RenderingServer.frame_post_draw

func _wait(pred: Callable, max_frames := 4000) -> void:
	var i := 0
	while not pred.call() and i < max_frames: await process_frame; i += 1

## footprint of one HUD panel: hide every other panel, render the HUD layer, collect alpha > 0 pixels
func _footprint(key: String) -> Dictionary:
	var P: Dictionary = m.hud.P
	var keep := {key: true}
	if key in ["lanes", "entry", "plan"]: keep["select"] = true
	var was := {}
	for k in P: was[k] = P[k].visible; P[k].visible = was[k] and keep.has(k)
	for k in ["lanes", "entry", "plan"]:   # children of LineSelect: keep only the one asked for
		if k != key and P.has(k): P[k].visible = false
	await _frames(2)
	var img: Image = m.hud_vp.get_texture().get_image()
	for k in P: P[k].visible = was[k]
	var pts := {}; var r := Rect2i(); var first := true
	for y in range(0, img.get_height(), STEP):
		for x in range(0, img.get_width(), STEP):
			if img.get_pixel(x, y).a > 0.05:
				pts[Vector2i(x, y)] = true
				if first: r = Rect2i(x, y, 1, 1); first = false
				else: r = r.expand(Vector2i(x, y))
	return {"pts": pts, "rect": r}

func _check_state(tag: String, res: Dictionary) -> void:
	m.busy = true   # main stops drawing / stepping while we isolate panels
	await _frames(1)
	var P: Dictionary = m.hud.P
	var keys := []
	for k in P:
		if k == "select" or k == "pause" or k == "finish" or k == "menu": continue
		if P[k].visible and (k not in ["lanes", "entry", "plan"] or P.select.visible): keys.append(k)
	var fp := {}
	for k in keys: fp[k] = await _footprint(k)
	# HUD layer (1280x960) -> window: the HudRect shows it over the 640x480 base canvas, stretched (canvas_items, keep) into the window
	var xf: Transform2D = m.get_viewport().get_final_transform() * m.hud_rect.get_global_transform()
	var sx: float = m.hud_rect.size.x / 1280.0
	var issues := []
	var rects := {}
	for k in keys:
		var r: Rect2i = fp[k].rect
		if r.size == Vector2i.ZERO: continue
		var a: Vector2 = xf * (Vector2(r.position) * sx); var b: Vector2 = xf * (Vector2(r.end) * sx)
		rects[k] = [a.x, a.y, b.x, b.y]
		var mg := minf(minf(a.x, a.y), minf(float(W) - b.x, float(H) - b.y))
		if mg < EDGE_MIN: issues.append("%s: %s within %.1f px of the window edge (rect %s)" % [tag, k, mg, str(rects[k])])
	for i in keys.size():
		for j in range(i + 1, keys.size()):
			var pa: Dictionary = fp[keys[i]].pts; var pb: Dictionary = fp[keys[j]].pts
			var ra: Rect2i = fp[keys[i]].rect; var rb: Rect2i = fp[keys[j]].rect
			if not ra.intersects(rb): continue
			var ov := 0
			for p in pa:
				if pb.has(p): ov += 1
			if ov > 0: issues.append("%s: %s overlaps %s (%d px)" % [tag, keys[i], keys[j], ov * STEP * STEP])
	res[tag] = {"rects": rects, "issues": issues}
	m.busy = false

func _run() -> void:
	await _frames(10)
	var res := {}
	var ws: Vector2i = DisplayServer.window_get_size()
	print("HUD_WINDOW %dx%d (asked %dx%d) content_scale_stretch=%d" % [ws.x, ws.y, W, H, root.content_scale_stretch])
	W = ws.x; H = ws.y
	await _wait(func(): return m.core != null and m.core.phase == "SELECT")
	await _frames(20)
	await _check_state("select_entry", res)
	await _frames(4)   # let main redraw the full HUD (the last isolated panel is still on screen)
	var shot: Image = DisplayServer.screen_get_image(0)
	if shot == null or shot.is_empty(): shot = m.get_viewport().get_texture().get_image()
	shot.save_png(out_dir.path_join("hud_%dx%d.png" % [W, H]))
	m.handle_key(KEY_ENTER); await _frames(30)
	await _check_state("select_apex", res)
	m.handle_key(KEY_ENTER); await process_frame; m.handle_key(KEY_ENTER)
	await _wait(func(): return m.core.phase == "TIMING" and m.qte_seg == "sweep")
	await _frames(5)
	await _check_state("timing_qte", res)
	await _wait(func(): return m.core.phase == "RESULT" and m.reveal >= 3)
	await _frames(10)
	await _check_state("result", res)
	var all := []
	for t in res: all.append_array(res[t].issues)
	for s in all: print("HUD_ISSUE ", s)
	FileAccess.open(out_dir.path_join("hud_%dx%d.json" % [W, H]), FileAccess.WRITE).store_string(JSON.stringify(res, " "))
	print("HUD_LAYOUT_CHECK %dx%d states=%d issues=%d %s" % [W, H, res.size(), all.size(), "PASS" if all.is_empty() else "FAIL"])
	quit(0 if all.is_empty() else 1)
