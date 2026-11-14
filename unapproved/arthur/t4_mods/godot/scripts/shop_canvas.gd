## Draws the 1280x960 shop comparison. Loaded by shop_compare.gd.
extends Control

const OUT_W := 1280
const OUT_H := 960

const NAVY := Color8(11, 23, 43)
const ROOM := Color8(8, 13, 28)
const PANEL := Color8(10, 16, 32)
const WELL := Color8(6, 10, 22)
const INK := Color8(8, 8, 14)
const WHITE := Color8(220, 230, 242)
const DIM := Color8(140, 159, 180)
const DIMMER := Color8(96, 108, 132)
const EDGE := Color8(42, 58, 88)
const AMB := Color8(85, 117, 160)

const T1 := Color8(58, 74, 104)
const T2 := Color8(92, 140, 152)
const T3 := Color8(196, 208, 224)
const T4_ICE := Color8(168, 208, 200)
const T4_IN := Color8(92, 140, 152)

const POW := Color8(44, 184, 74)
const HAN := Color8(240, 200, 40)

const METAL := Color8(168, 178, 190)
const METAL_D := Color8(88, 96, 110)
const METAL_L := Color8(210, 216, 226)
const BODY := Color8(36, 42, 54)
const TYRE := Color8(22, 20, 24)

var fa: FontFile
var fn: FontFile

const CARDS := [
	{
		"tier": "T1", "name": "STREET LIP", "rank": "STREET",
		"border": T1, "stamp": T1, "selected": false, "tag": "",
		"metal": Color8(120, 128, 140), "accent": Color8(58, 74, 104),
	},
	{
		"tier": "T2", "name": "SPORT SPOILER", "rank": "SPORT",
		"border": T2, "stamp": T2, "selected": false, "tag": "",
		"metal": Color8(168, 178, 190), "accent": T2,
	},
	{
		"tier": "T3", "name": "RACE WING", "rank": "RACE",
		"border": T3, "stamp": T3, "selected": false, "tag": "",
		"metal": Color8(210, 216, 226), "accent": Color8(196, 208, 224),
	},
	{
		"tier": "T4", "name": "FINALE WING", "rank": "FINALE",
		"border": T4_ICE, "stamp": T4_ICE, "selected": true, "tag": "NEW",
		"metal": Color8(200, 220, 216), "accent": T4_ICE,
	},
]


func _draw() -> void:
	draw_rect(Rect2(0, 0, OUT_W, OUT_H), ROOM)
	# Outer menu frame
	_panel(24, 20, 1232, 920, PANEL, EDGE, 2)
	_header()
	_cards()
	_footer()


func _header() -> void:
	draw_rect(Rect2(24, 20, 1232, 88), Color8(8, 12, 24))
	draw_rect(Rect2(24, 106, 1232, 2), EDGE)
	t(fa, 48, 32, "REIKO", 30, WHITE)
	# Selected tab
	var tab_x := 220
	draw_rect(Rect2(tab_x, 36, 112, 36), PANEL)
	_border(tab_x, 36, 112, 36, T4_ICE if false else AMB, 2)
	t(fa, tab_x + 56, 42, "PARTS", 16, WHITE, "m")
	t(fn, 360, 46, "SABINE'S GARAGE", 16, DIM)
	# After-rift state, no dollar figure
	t(fa, 1232, 32, "FULL PRICE", 16, T3, "r")
	t(fn, 1232, 58, "WHOLESALE CLOSED", 14, DIMMER, "r")
	# Sub row under the hairline
	t(fn, 48, 118, "SHOP  /  AERO  /  COMPARE TIERS", 15, DIM)
	t(fn, 1232, 118, "STAND-IN NAMES  ·  CATALOG TBD", 14, DIMMER, "r")


func _cards() -> void:
	var x0 := 48
	var y0 := 156
	var w := 286
	var h := 680
	var gap := 16
	for i in CARDS.size():
		_card(x0 + i * (w + gap), y0, w, h, CARDS[i], i)


func _card(x: int, y: int, w: int, h: int, c: Dictionary, idx: int) -> void:
	var fill := Color8(10, 16, 32)
	if c.selected:
		fill = Color8(12, 22, 36)
	draw_rect(Rect2(x, y, w, h), fill)
	_border(x, y, w, h, c.border, 2)
	if String(c.tier) == "T4":
		_border(x + 4, y + 4, w - 8, h - 8, T4_IN, 1)
	# Header strip
	var hs := 40
	draw_rect(Rect2(x + 2, y + 2, w - 4, hs), Color8(6, 10, 20))
	draw_rect(Rect2(x + 2, y + 2 + hs, w - 4, 2), c.border)
	t(fa, x + 16, y + 10, String(c.tier), 20, c.stamp)
	t(fn, x + 64, y + 14, String(c.rank), 16, WHITE)
	if String(c.tag) != "":
		var tw := int(fn.get_string_size(String(c.tag), HORIZONTAL_ALIGNMENT_LEFT, -1, 14).x) + 16
		var tx := x + w - 16 - tw
		draw_rect(Rect2(tx, y + 10, tw, 22), Color8(16, 32, 32))
		_border(tx, y + 10, tw, 22, T4_ICE, 1)
		t(fa, tx + tw / 2, y + 12, String(c.tag), 14, T4_ICE, "m")
	# Icon well
	var wx := x + 16
	var wy := y + 58
	var ww := w - 32
	var wh := 250
	draw_rect(Rect2(wx, wy, ww, wh), WELL)
	_border(wx, wy, ww, wh, Color8(28, 40, 62), 1)
	_wing(wx, wy, ww, wh, idx, c)
	# Copy
	var cy := wy + wh + 20
	t(fa, x + w / 2, cy, String(c.name), 20, WHITE, "m")
	t(fn, x + w / 2, cy + 36, "AERO  ·  ANY SLOT", 15, DIM, "m")
	# Stat chips, no invented magnitudes
	var row := cy + 80
	t(fn, x + 20, row, "PRIMARY", 13, DIMMER)
	_chip(x + w - 20, row - 2, "POW", POW, true)
	var row2 := row + 36
	t(fn, x + 20, row2, "TRADE-OFF", 13, DIMMER)
	_chip(x + w - 20, row2 - 2, "HAN", HAN, true)
	# Price reserved, no figure
	var row3 := row2 + 48
	draw_rect(Rect2(x + 16, row3, w - 32, 1), EDGE)
	t(fn, x + 20, row3 + 16, "PRICE", 13, DIMMER)
	t(fa, x + w - 20, row3 + 14, "—", 20, DIM, "r")
	# Fit note
	var row4 := row3 + 64
	t(fn, x + 20, row4, "FITS", 13, DIMMER)
	t(fn, x + w - 20, row4, "ANY SHELL", 14, WHITE, "r")
	# Footer of card: car-side note
	var note_y := y + h - 86
	draw_rect(Rect2(x + 16, note_y, w - 32, 1), EDGE)
	var note := "STOCK LIP"
	if idx == 1:
		note = "TRUNK SPOILER"
	elif idx == 2:
		note = "RACE WING"
	elif idx == 3:
		note = "TALLER WING + ENDPLATES"
	t(fn, x + w / 2, note_y + 16, "ON THE CAR", 12, DIMMER, "m")
	t(fn, x + w / 2, note_y + 38, note, 14, WHITE, "m")


func _footer() -> void:
	draw_rect(Rect2(24, 852, 1232, 2), EDGE)
	t(fn, 48, 868, "T1 STEEL-NAVY   T2 MERCURY   T3 PALE STEEL   T4 ICE TEAL + DOUBLE RULE", 14, DIM)
	t(fn, 48, 894, "NO PRICES  ·  ECON-V1 NOT LIVE  ·  UNAPPROVED  ·  PIXEL-HARD 1280x960", 13, DIMMER)


func _wing(x: int, y: int, w: int, h: int, idx: int, c: Dictionary) -> void:
	# Rear 3/4 of a short deck + the aero part. Silhouette steps up with tier.
	var cx := x + w / 2
	var deck_y := y + h - 70
	# Deck / boot
	var dpts := PackedVector2Array([
		Vector2(cx - 78, deck_y + 8),
		Vector2(cx + 70, deck_y - 6),
		Vector2(cx + 86, deck_y + 28),
		Vector2(cx - 62, deck_y + 44),
	])
	draw_colored_polygon(dpts, BODY)
	_poly_outline(dpts, Color8(16, 18, 26), 2)
	# Rear lamp bar
	draw_rect(Rect2(cx - 54, deck_y + 16, 26, 6), Color8(120, 24, 24))
	draw_rect(Rect2(cx + 28, deck_y + 8, 26, 6), Color8(120, 24, 24))
	# Wheels hint
	_wheel(cx - 40, deck_y + 50, 16)
	_wheel(cx + 58, deck_y + 40, 16)
	var metal: Color = c.metal
	var accent: Color = c.accent
	var dark := Color(metal.r * 0.45, metal.g * 0.45, metal.b * 0.45)
	if idx == 0:
		# T1 short ducktail: a raised metal lip that clearly overhangs the rear.
		var lip_top := PackedVector2Array([
			Vector2(cx - 72, deck_y - 10),
			Vector2(cx + 68, deck_y - 24),
			Vector2(cx + 74, deck_y - 14),
			Vector2(cx - 66, deck_y + 0),
		])
		draw_colored_polygon(lip_top, metal)
		_poly_outline(lip_top, dark, 2)
		# Rear face of the lip, so it reads as a separate part, not a deck highlight.
		var lip_face := PackedVector2Array([
			Vector2(cx - 72, deck_y - 10),
			Vector2(cx - 66, deck_y + 0),
			Vector2(cx - 70, deck_y + 14),
			Vector2(cx - 80, deck_y + 2),
		])
		draw_colored_polygon(lip_face, dark)
		_poly_outline(lip_face, Color8(20, 22, 28), 1)
	elif idx == 1:
		# T2 raised trunk spoiler, small endplates
		var blade := PackedVector2Array([
			Vector2(cx - 74, deck_y - 22),
			Vector2(cx + 72, deck_y - 36),
			Vector2(cx + 76, deck_y - 24),
			Vector2(cx - 70, deck_y - 10),
		])
		draw_colored_polygon(blade, metal)
		_poly_outline(blade, dark, 2)
		# Stalks
		draw_rect(Rect2(cx - 36, deck_y - 12, 8, 16), dark)
		draw_rect(Rect2(cx + 36, deck_y - 22, 8, 16), dark)
		# Small endplates
		draw_rect(Rect2(cx - 80, deck_y - 30, 8, 22), accent)
		draw_rect(Rect2(cx + 74, deck_y - 44, 8, 22), accent)
		_border(cx - 80, deck_y - 30, 8, 22, dark, 1)
		_border(cx + 74, deck_y - 44, 8, 22, dark, 1)
	elif idx == 2:
		# T3 race wing, taller, larger endplates
		var blade := PackedVector2Array([
			Vector2(cx - 86, deck_y - 48),
			Vector2(cx + 82, deck_y - 64),
			Vector2(cx + 88, deck_y - 48),
			Vector2(cx - 80, deck_y - 32),
		])
		draw_colored_polygon(blade, metal)
		_poly_outline(blade, dark, 2)
		# Mid relief line
		draw_line(Vector2(cx - 78, deck_y - 42), Vector2(cx + 80, deck_y - 58), dark, 1)
		# Dual stalks
		var s1 := PackedVector2Array([Vector2(cx - 40, deck_y - 32), Vector2(cx - 32, deck_y - 32), Vector2(cx - 28, deck_y + 6), Vector2(cx - 40, deck_y + 6)])
		var s2 := PackedVector2Array([Vector2(cx + 28, deck_y - 44), Vector2(cx + 36, deck_y - 44), Vector2(cx + 40, deck_y - 6), Vector2(cx + 28, deck_y - 6)])
		draw_colored_polygon(s1, dark)
		draw_colored_polygon(s2, dark)
		# Endplates
		draw_rect(Rect2(cx - 94, deck_y - 66, 12, 40), accent)
		draw_rect(Rect2(cx + 86, deck_y - 82, 12, 40), accent)
		_border(cx - 94, deck_y - 66, 12, 40, dark, 1)
		_border(cx + 86, deck_y - 82, 12, 40, dark, 1)
	else:
		# T4 finale wing: taller still, second element, bigger endplates, ice mark
		# Lower element
		var low := PackedVector2Array([
			Vector2(cx - 82, deck_y - 36),
			Vector2(cx + 78, deck_y - 50),
			Vector2(cx + 84, deck_y - 38),
			Vector2(cx - 76, deck_y - 24),
		])
		draw_colored_polygon(low, dark)
		_poly_outline(low, Color8(20, 24, 32), 1)
		# Main blade
		var blade := PackedVector2Array([
			Vector2(cx - 96, deck_y - 78),
			Vector2(cx + 90, deck_y - 96),
			Vector2(cx + 98, deck_y - 76),
			Vector2(cx - 88, deck_y - 58),
		])
		draw_colored_polygon(blade, metal)
		_poly_outline(blade, dark, 2)
		draw_line(Vector2(cx - 88, deck_y - 70), Vector2(cx + 90, deck_y - 88), dark, 1)
		# Stalks
		var s1 := PackedVector2Array([Vector2(cx - 44, deck_y - 58), Vector2(cx - 34, deck_y - 58), Vector2(cx - 28, deck_y + 6), Vector2(cx - 44, deck_y + 6)])
		var s2 := PackedVector2Array([Vector2(cx + 30, deck_y - 72), Vector2(cx + 40, deck_y - 72), Vector2(cx + 46, deck_y - 8), Vector2(cx + 30, deck_y - 8)])
		draw_colored_polygon(s1, dark)
		draw_colored_polygon(s2, dark)
		# Big endplates
		draw_rect(Rect2(cx - 108, deck_y - 104, 16, 62), accent)
		draw_rect(Rect2(cx + 96, deck_y - 122, 16, 62), accent)
		_border(cx - 108, deck_y - 104, 16, 62, dark, 2)
		_border(cx + 96, deck_y - 122, 16, 62, dark, 2)
		# Ice mark: a flat bar on each endplate, no glow
		draw_rect(Rect2(cx - 104, deck_y - 96, 8, 6), T4_ICE)
		draw_rect(Rect2(cx + 100, deck_y - 114, 8, 6), T4_ICE)


func _wheel(cx: int, cy: int, r: int) -> void:
	draw_circle(Vector2(cx, cy), r, TYRE)
	draw_circle(Vector2(cx, cy), r - 4, METAL_D)
	draw_circle(Vector2(cx, cy), 4, METAL)
	draw_arc(Vector2(cx, cy), r, 0.0, TAU, 24, Color8(12, 12, 16), 1.0, false)


func _chip(x1: int, y: int, label: String, col: Color, dark_text: bool) -> void:
	var sz := 14
	var tw := int(fn.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, sz).x) + 16
	var x0 := x1 - tw
	var h := 22
	draw_rect(Rect2(x0, y, tw, h), col)
	_border(x0, y, tw, h, INK, 1)
	var tc := INK if (dark_text or col == HAN) else WHITE
	t(fa, x0 + tw / 2, y + 3, label, sz, tc, "m", false)


func _panel(x: int, y: int, w: int, h: int, fill: Color, edge: Color, tpx: int) -> void:
	draw_rect(Rect2(x, y, w, h), fill)
	_border(x, y, w, h, edge, tpx)


func _border(x: int, y: int, w: int, h: int, col: Color, tpx: int) -> void:
	# Hard axis-aligned border, no rounded corners, no AA.
	draw_rect(Rect2(x, y, w, tpx), col)
	draw_rect(Rect2(x, y + h - tpx, w, tpx), col)
	draw_rect(Rect2(x, y, tpx, h), col)
	draw_rect(Rect2(x + w - tpx, y, tpx, h), col)


func _poly_outline(pts: PackedVector2Array, col: Color, width: float) -> void:
	var q := pts.duplicate()
	q.append(pts[0])
	draw_polyline(q, col, width, false)


func t(font: FontFile, x: float, y: float, s: String, sz: int, col: Color, anchor := "l", shadow := true) -> void:
	var w := font.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz).x
	var X := roundf(x)
	if anchor == "m":
		X = roundf(x - w / 2.0)
	elif anchor == "r":
		X = roundf(x - w)
	var B := roundf(y + font.get_ascent(sz))
	if shadow:
		draw_string(font, Vector2(X + 2, B + 2), s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz, INK)
	draw_string(font, Vector2(X, B), s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz, col)
