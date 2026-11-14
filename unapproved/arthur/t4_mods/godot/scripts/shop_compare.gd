## Unapproved T4 shop comparison frame. Pixel-hard 1280x960, flat menus
## (solid fills, 1-2 px hard borders, no bevel, gloss or grain).
## Names are stand-ins. Prices omitted (econ-v1 is not live).
extends Node

const OUT_W := 1280
const OUT_H := 960

const NAVY := Color8(11, 23, 43)       # B.2a fog #0B172B
const ROOM := Color8(8, 13, 28)
const PANEL := Color8(10, 16, 32)
const WELL := Color8(6, 10, 22)
const INK := Color8(8, 8, 14)
const WHITE := Color8(220, 230, 242)
const DIM := Color8(140, 159, 180)
const DIMMER := Color8(96, 108, 132)
const EDGE := Color8(42, 58, 88)
const AMB := Color8(85, 117, 160)      # B.2a ambient #5575A0

# Tier markers. Avoid POW #2CB84A, HAN #F0C828, EN #E8282C, hot #FF701C,
# and sodium fills (too close to HAN). Sodium stays on lamps, not cards.
const T1 := Color8(58, 74, 104)        # dim steel-navy
const T2 := Color8(92, 140, 152)       # mercury ambient #5C8C98
const T3 := Color8(196, 208, 224)      # pale machined steel
const T4_ICE := Color8(168, 208, 200)  # ice teal, flat, no glow
const T4_IN := Color8(92, 140, 152)    # mercury inner rule

const POW := Color8(44, 184, 74)
const HAN := Color8(240, 200, 40)
const EN := Color8(232, 40, 44)

const METAL := Color8(168, 178, 190)
const METAL_D := Color8(88, 96, 110)
const METAL_L := Color8(210, 216, 226)
const BODY := Color8(36, 42, 54)

var fa: FontFile
var fn: FontFile


func _ready() -> void:
	fa = _load_font("res://fonts/ArchivoBlack-Regular.ttf")
	fn = _load_font("res://fonts/NimbusSans-Bold.otf")
	if fa == null or fn == null:
		push_error("missing fonts")
		get_tree().quit(1)
		return
	var vp := SubViewport.new()
	vp.size = Vector2i(OUT_W, OUT_H)
	vp.transparent_bg = false
	vp.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.disable_3d = true
	vp.msaa_2d = Viewport.MSAA_DISABLED
	vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	var canvas := Control.new()
	canvas.set_script(preload("res://scripts/shop_canvas.gd"))
	canvas.size = Vector2(OUT_W, OUT_H)
	canvas.set("fa", fa)
	canvas.set("fn", fn)
	vp.add_child(canvas)
	add_child(vp)
	canvas.queue_redraw()
	for i in 8:
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	if img.get_format() != Image.FORMAT_RGBA8:
		img.convert(Image.FORMAT_RGBA8)
	if img.get_width() != OUT_W or img.get_height() != OUT_H:
		img.resize(OUT_W, OUT_H, Image.INTERPOLATE_NEAREST)
	var path := ProjectSettings.globalize_path("res://").path_join("..").path_join("t4_shop_compare.png")
	img.save_png(path)
	print("wrote ", path, " ", img.get_width(), "x", img.get_height())
	get_tree().quit(0)


func _load_font(p: String) -> FontFile:
	if not ResourceLoader.exists(p):
		return null
	var src: FontFile = load(p)
	if src == null:
		return null
	var f: FontFile = src.duplicate()
	f.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	f.hinting = TextServer.HINTING_NONE
	f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
	return f
