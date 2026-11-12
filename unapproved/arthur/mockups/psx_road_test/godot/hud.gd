## Line-select Entry HUD. Two styles:
##   classic — 640x480, 1-bit Nimbus Sans Narrow, thin panels (matches art/ui/line_select_cam/post_lsc.py frame 1)
##   sharp   — 1280x960, bold drop-shadowed type and chunky bevelled plates (Racing Lagoon / GT 1-2 / Test Drive)
## Stance colours (art_direction B.5): ATK #2CB84A, DEF #E8282C, NEU #F0C828 with dark text.
extends Control

const COL := {"ATK": Color8(44, 184, 74), "DEF": Color8(232, 40, 44), "NEU": Color8(240, 200, 40)}
const WHITE := Color8(220, 230, 242)
const DIM := Color8(140, 159, 180)
const DIMMER := Color8(96, 108, 132)
const EDGE := Color8(71, 94, 127)
const EDGE_L := Color8(150, 172, 205)
const AMBER := Color8(255, 184, 56)
const AMBER_D := Color8(150, 90, 20)
const PANEL := Color8(10, 14, 36)
const INK := Color8(8, 10, 16)
const SOD := Color8(240, 200, 148)
const PICKS := [["ENTRY", "MID", "NEU"], ["APEX", "IN", "DEF"], ["EXIT", "OUT", "ATK"]]

var style := "classic"  # "classic" | "sharp"
var fn: FontFile
var fi: FontFile
var fb: FontFile  # heavy title font (sharp only)

func setup(p_style: String) -> void:
	style = p_style
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	if style == "sharp":
		size = Vector2(1280, 960)
		fn = _font("res://fonts/NimbusSans-Bold.otf", false)
		fi = _font("res://fonts/NimbusSansNarrow-BoldOblique.otf", false)
		fb = _font("res://fonts/ArchivoBlack-Regular.ttf", false)
	else:
		size = Vector2(640, 480)
		fn = _font("res://fonts/NimbusSansNarrow-Bold.otf", true)
		fi = _font("res://fonts/NimbusSansNarrow-BoldOblique.otf", true)
		fb = fn
	queue_redraw()

func _font(p: String, hard: bool) -> FontFile:
	var f: FontFile = (load(p) as FontFile).duplicate()
	if hard:
		f.antialiasing = TextServer.FONT_ANTIALIASING_NONE
		f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
		f.oversampling = 1.0
	else:
		f.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
		f.hinting = TextServer.HINTING_NORMAL
	return f

func S() -> float:
	return 2.0 if style == "sharp" else 1.0

func _txt(x: float, y: float, s: String, sz: int, col: Color, anchor := "lt", sh := true, it := false, heavy := false) -> void:
	var f: FontFile = fb if heavy else (fi if it else fn)
	var k := S()
	var z := int(round(float(sz) * k))
	var w := f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, z).x
	var X := x * k
	var B := y * k + f.get_ascent(z)
	if anchor == "rt" or anchor == "rm":
		X -= w
	elif anchor == "mt" or anchor == "mm":
		X -= w / 2.0
	if anchor.ends_with("m"):
		B = y * k + (f.get_ascent(z) - f.get_descent(z)) / 2.0
	X = roundf(X); B = roundf(B)
	var sh_off := (4.0 if style == "sharp" else 1.0)
	if sh:
		draw_string(f, Vector2(X + sh_off, B + sh_off), s, HORIZONTAL_ALIGNMENT_LEFT, -1, z, INK)
		if style == "sharp":
			draw_string(f, Vector2(X + sh_off * 0.5, B + sh_off * 0.5), s, HORIZONTAL_ALIGNMENT_LEFT, -1, z, Color(0, 0, 0, 0.7))
	draw_string(f, Vector2(X, B), s, HORIZONTAL_ALIGNMENT_LEFT, -1, z, col)

func _cut(x: float, y: float, x1: float, y1: float, c: float = 5.0) -> PackedVector2Array:
	var k := S()
	return PackedVector2Array([
		Vector2(x, y) * k, Vector2(x1 - c, y) * k, Vector2(x1, y + c) * k,
		Vector2(x1, y1) * k, Vector2(x + c, y1) * k, Vector2(x, y1 - c) * k
	])

func _panel(x: float, y: float, x1: float, y1: float, col: Color = EDGE, c: float = 5.0) -> void:
	var pts := _cut(x, y, x1, y1, c)
	if style == "sharp":
		# Chunky bevelled plate: fill, dark bottom/right, light top/left, thick ink edge.
		var k := S()
		var sh := PackedVector2Array()
		for p in pts:
			sh.append(p + Vector2(3, 4))
		draw_colored_polygon(sh, Color(0, 0, 0, 0.55))
		draw_colored_polygon(pts, PANEL)
		_bevel(pts)
		var q := pts.duplicate(); q.append(pts[0])
		draw_polyline(q, Color(col.r, col.g, col.b, 1.0), 3.0)
		draw_polyline(q, INK, 1.0)
	else:
		draw_colored_polygon(pts, Color(PANEL, 0.5))  # drawn on a transparent layer; compositor does 50/50
		# For classic we actually composite semi/solid in the Control itself:
		# post_lsc used a separate semi layer at 50%. Here we draw the panel at alpha 0.5 then the edge solid.
		var q := pts.duplicate(); q.append(pts[0])
		draw_polyline(q, col, 1.0)

func _bevel(pts: PackedVector2Array) -> void:
	# Highlight along the top-left edges, shade along the bottom-right.
	if pts.size() < 3:
		return
	var hi := Color8(90, 110, 160, 220)
	var lo := Color8(0, 0, 0, 160)
	# top edge
	draw_line(pts[0] + Vector2(1, 1), pts[1] + Vector2(-1, 1), hi, 2.0)
	# left-ish last edge
	draw_line(pts[0] + Vector2(1, 1), pts[pts.size() - 1] + Vector2(1, -1), hi, 2.0)
	# bottom
	draw_line(pts[3] + Vector2(0, -1), pts[4] + Vector2(0, -1), lo, 2.0)
	draw_line(pts[2] + Vector2(-1, 0), pts[3] + Vector2(-1, 0), lo, 2.0)

func _chip(x: float, y: float, st: String, label: String = "", w: float = 49.0) -> void:
	var k := S()
	var h := 14.0
	var pts_src := [Vector2(x + 4, y), Vector2(x + w, y), Vector2(x + w - 4, y + h), Vector2(x, y + h)]
	var pts := PackedVector2Array()
	for p in pts_src:
		pts.append(p * k)
	var fill: Color = COL[st]
	draw_colored_polygon(pts, fill)
	if style == "sharp":
		draw_line(pts[0] + Vector2(0, 1), pts[1] + Vector2(0, 1), Color(1, 1, 1, 0.35), 2.0)
		draw_line(pts[2] + Vector2(0, -1), pts[3] + Vector2(0, -1), Color(0, 0, 0, 0.35), 2.0)
		var q := pts.duplicate(); q.append(pts[0])
		draw_polyline(q, INK, 2.0)
	else:
		var q := pts.duplicate(); q.append(pts[0])
		draw_polyline(q, INK, 1.0)
	var txcol := INK if st == "NEU" else Color.WHITE
	_txt(x + w / 2.0, y + 7.0, label if label != "" else st, 11, txcol, "mm", false)

func _draw() -> void:
	# Frame 1: Entry pick, timer 04.8s, 10 lit ticks, active ENTRY MID/NEU, Apex/Exit not set.
	if style == "classic":
		_draw_mirror_frame()
	else:
		_draw_mirror_frame_sharp()
	_draw_timer()
	_draw_corner_plate()
	_draw_selector()

func _draw_mirror_frame() -> void:
	draw_rect(Rect2(221, 13, 198, 70), Color8(110, 127, 151), false, 1.0)
	draw_rect(Rect2(222, 14, 196, 68), Color8(15, 20, 30), false, 1.0)
	_txt(291, 84, "REAR VIEW", 9, DIM)

func _draw_mirror_frame_sharp() -> void:
	var k := S()
	# Chunky bezel around the already-composited 3D mirror (drawn in the 3D post at 2x).
	var x := 221.0 * k
	var y := 13.0 * k
	var w := 198.0 * k
	var h := 70.0 * k
	# Bezel only — do not fill, the 3D rear-view is already in the upscaled 3D layer.
	draw_rect(Rect2(x - 5, y - 5, w + 10, h + 10), Color8(18, 20, 28), false, 5.0)
	draw_rect(Rect2(x - 3, y - 3, w + 6, h + 6), Color8(160, 175, 200), false, 3.0)
	draw_rect(Rect2(x - 1, y - 1, w + 2, h + 2), INK, false, 2.0)
	_txt(320, 84, "REAR VIEW", 10, DIM, "mt", true, false, true)

func _draw_timer() -> void:
	_panel(14, 12, 192, 57, EDGE, 6.0 if style == "sharp" else 5.0)
	_txt(23, 18, "LINE LOCK", 12 if style == "classic" else 13, WHITE, "lt", true, false, style == "sharp")
	_txt(183, 18, "04.8s", 19 if style == "classic" else 22, AMBER, "rt", true, false, style == "sharp")
	var lit_n := 10
	for j in 17:
		var x0 := 24.0 + j * 9.0
		var pts_s := [Vector2(x0, 43), Vector2(x0 + 6, 43), Vector2(x0 + 4, 50), Vector2(x0 - 2, 50)]
		var pts := PackedVector2Array()
		for p in pts_s:
			pts.append(p * S())
		var col := AMBER if j < lit_n else Color8(68, 52, 40)
		draw_colored_polygon(pts, col)
		if style == "sharp" and j < lit_n:
			draw_line(pts[0], pts[1], Color8(255, 230, 160), 1.5)

func _draw_corner_plate() -> void:
	_panel(476, 12, 628, 96, EDGE, 7.0 if style == "sharp" else 5.0)
	_txt(534, 18, "HAIRPIN R", 16 if style == "classic" else 18, WHITE, "lt", true, false, style == "sharp")
	_txt(534, 40, "VIEW", 9, DIM)
	_txt(560, 38, "ENTRY", 13, AMBER, "lt", true, false, style == "sharp")
	var k := S()
	var lw := 5.0 if style == "sharp" else 3.0
	draw_line(Vector2(492, 88) * k, Vector2(492, 46) * k, SOD, lw)
	# arc for the hairpin
	var cx := 506.0 * k
	var cy := 46.0 * k
	var r := 14.0 * k
	var pts := PackedVector2Array()
	for i in 17:
		var a := PI + PI * float(i) / 16.0
		pts.append(Vector2(cx + r * cos(a), cy + r * sin(a)))
	draw_polyline(pts, SOD, lw)
	draw_line(Vector2(520, 46) * k, Vector2(520, 80) * k, SOD, lw)
	var head := PackedVector2Array([Vector2(514, 78) * k, Vector2(526, 78) * k, Vector2(520, 88) * k])
	draw_colored_polygon(head, SOD)
	# stops: E active amber, A and X dim
	var stops := [Vector2(492, 70), Vector2(506, 33), Vector2(520, 64)]
	for i in 3:
		var sx: float = stops[i].x
		var sy: float = stops[i].y
		var cur := i == 0
		var dia := PackedVector2Array([
			Vector2(sx, sy - 5) * k, Vector2(sx + 5, sy) * k,
			Vector2(sx, sy + 5) * k, Vector2(sx - 5, sy) * k
		])
		draw_colored_polygon(dia, AMBER if cur else Color8(40, 46, 64))
		var q := dia.duplicate(); q.append(dia[0])
		draw_polyline(q, INK, 2.0 if style == "sharp" else 1.0)
	_txt(534, 58, "E", 10, AMBER)
	_txt(548, 58, "A", 10, DIMMER)
	_txt(562, 58, "X", 10, DIMMER)
	_txt(534, 74, "CAMERA STOP", 9, DIM)

func _draw_selector() -> void:
	var y := 154.0
	var slots: Array = []
	for i in 3:
		var h := 60.0 if i == 0 else 31.0
		slots.append([i, PICKS[i][0], PICKS[i][1], PICKS[i][2], y, h])
		y += h + 8.0
	var y_end := y - 8.0
	_panel(414, 107, 628, y_end + 24, EDGE, 8.0 if style == "sharp" else 5.0)
	_txt(422, 114, "PLAYER LINE LOCK", 15 if style == "classic" else 16, WHITE, "lt", true, false, style == "sharp")
	_txt(422, 133, "HAND", 10, DIM)
	var kchip := 0
	for st in ["ATK", "DEF", "NEU"]:
		_chip(473 + kchip * 50, 131, st, "%s x2" % st)
		kchip += 1
	for item in slots:
		var i: int = item[0]
		var ph: String = item[1]
		var lane: String = item[2]
		var st: String = item[3]
		var sy: float = item[4]
		var h: float = item[5]
		if i == 0:
			_panel(420, sy, 622, sy + h, AMBER, 6.0 if style == "sharp" else 5.0)
			var k := S()
			var tri := PackedVector2Array([Vector2(425, sy + 9) * k, Vector2(431, sy + 14) * k, Vector2(425, sy + 19) * k])
			draw_colored_polygon(tri, AMBER)
			_txt(438, sy + 5, ph, 12, AMBER)
			_txt(615, sy + 6, "CONFIRM", 9, AMBER, "rt")
			var slab_s := [Vector2(475, sy + 21), Vector2(613, sy + 21), Vector2(609, sy + 39), Vector2(471, sy + 39)]
			var slab := PackedVector2Array()
			for p in slab_s:
				slab.append(p * k)
			if style == "sharp":
				var sh := PackedVector2Array()
				for p in slab:
					sh.append(p + Vector2(2, 3))
				draw_colored_polygon(sh, AMBER_D)
			draw_colored_polygon(slab, AMBER)
			var q := slab.duplicate(); q.append(slab[0])
			draw_polyline(q, INK, 2.0 if style == "sharp" else 1.0)
			_txt(543, sy + 30, "< %s / %s >" % [lane, st], 15, INK, "mm", false, false, style == "sharp")
			_txt(428, sy + 44, "D-PAD LANE", 10, WHITE)
			var el := Rect2(Vector2(538, sy + 45) * k, Vector2(5, 5) * k)
			draw_rect(el, WHITE)
			_txt(549, sy + 44, "SET", 10, WHITE)
		else:
			_panel(420, sy, 622, sy + h, EDGE)
			_txt(428, sy + 9, ph, 12, DIM)
			_txt(510, sy + 7, "- - -", 15, DIMMER)
			_txt(614, sy + 11, "NOT SET", 9, DIMMER, "rt")
	_txt(422, y_end + 8, "[L1] / [R1] PHASE", 10, DIM)
	_txt(619, y_end + 8, "0/3 SET", 10, DIM, "rt")
