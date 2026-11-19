## Standalone 2D export of the E3B HUD icons. No 3D scene.
## Run: godot --path godot --scene res://scenes/icon_export.tscn
extends Node

const COL := {
	"fuel": Color8(44, 184, 74),
	"brakes": Color8(232, 40, 44),
	"susp": Color8(240, 200, 40),
}
const PANEL := Color8(10, 14, 36)

func _ready() -> void:
	var out_dir := ProjectSettings.globalize_path("res://").path_join("..")
	# In-band design size is r=10 (brakes/coolant) or r=11 (shock) in 640-space.
	# 16 / 64 / 128 are pixel-hard review sizes, drawn at that canvas, not upscaled.
	await _export(out_dir, "brakes", "icon_en_brake", COL.brakes, [16, 64, 128])
	await _export(out_dir, "susp", "icon_han_shock", COL.susp, [16, 64, 128])
	# White-on-transparent masters at 128. Dark highlight so the caliper slot punches through.
	await _export_one(out_dir.path_join("icon_en_brake_master.png"), "brakes", 128, Color.WHITE, true, Color8(40, 44, 52))
	await _export_one(out_dir.path_join("icon_han_shock_master.png"), "susp", 128, Color.WHITE, true, Color8(40, 44, 52))
	# In-band size (r=10 / r=11) on the panel colour, as drawn in the 640 HUD space.
	await _export_one(out_dir.path_join("icon_en_brake_20.png"), "brakes", 24, COL.brakes, false, Color8(200, 210, 220), 10.0)
	await _export_one(out_dir.path_join("icon_han_shock_22.png"), "susp", 26, COL.susp, false, Color8(200, 210, 220), 11.0)
	await _export_one(out_dir.path_join("icon_pow_coolant_20.png"), "fuel", 24, COL.fuel, false, Color8(200, 210, 220), 10.0)
	# Enlarged panel-colour review copies used by the icon sheet.
	for kind in ["fuel", "brakes", "susp"]:
		var names := {"fuel": "pow_coolant", "brakes": "en_brake", "susp": "han_shock"}
		var tag: String = String(names[kind])
		await _export_one(out_dir.path_join("icon_%s_64_panel.png" % tag), kind, 64, COL[kind], false, Color8(200, 210, 220))
		await _export_one(out_dir.path_join("icon_%s_128_panel.png" % tag), kind, 128, COL[kind], false, Color8(200, 210, 220))
	print("ICON_EXPORT_OK ", out_dir)
	get_tree().quit(0)


func _export(out_dir: String, kind: String, prefix: String, col: Color, sizes: Array) -> void:
	for px in sizes:
		var r := float(px) * 0.42
		await _export_one(out_dir.path_join("%s_%d.png" % [prefix, px]), kind, int(px), col, false, Color8(200, 210, 220), r)


func _export_one(path: String, kind: String, px: int, col: Color, transparent: bool, highlight: Color, r: float = -1.0) -> void:
	if r < 0.0:
		r = float(px) * 0.42
	var vp := SubViewport.new()
	vp.size = Vector2i(px, px)
	vp.transparent_bg = transparent
	vp.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.disable_3d = true
	vp.msaa_2d = Viewport.MSAA_DISABLED
	vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	var c := Control.new()
	c.set_script(load("res://scripts/hud/resource_stack.gd"))
	c.size = Vector2(px, px)
	c.position = Vector2.ZERO
	c.icon_job = {
		"kind": kind,
		"cx": float(px) * 0.5,
		"cy": float(px) * 0.5,
		"r": r,
		"col": col,
		"transparent": transparent,
		"bg": PANEL,
		"highlight": highlight,
	}
	vp.add_child(c)
	add_child(vp)
	c.queue_redraw()
	for i in 6:
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	if img.get_format() != Image.FORMAT_RGBA8:
		img.convert(Image.FORMAT_RGBA8)
	if transparent:
		# Punch near-black background (and the dark bore / cut) to alpha 0,
		# keep near-white ink as white. Mid highlight becomes a transparent cut.
		_punch_black(img)
	img.save_png(path)
	print("wrote ", path)
	vp.queue_free()


func _punch_black(img: Image) -> void:
	for y in img.get_height():
		for x in img.get_width():
			var p := img.get_pixel(x, y)
			var lum := (p.r + p.g + p.b) / 3.0
			if lum < 0.18:
				img.set_pixel(x, y, Color(0, 0, 0, 0))
			elif lum > 0.72:
				img.set_pixel(x, y, Color(1, 1, 1, p.a))
			else:
				# Highlight arc and mid greys: treat as a cut on the master.
				img.set_pixel(x, y, Color(0, 0, 0, 0))
