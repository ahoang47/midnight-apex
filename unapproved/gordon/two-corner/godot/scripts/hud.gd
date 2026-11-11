## Native-resolution HUD (640x480 under viewport stretch). Plan the Line layout from Arthur's /workspace/mockups/lane_chain/v5/post_v5.py (1-bit NimbusSansNarrow,
## PS1 50/50 semi panels); debug boxes, menu and gap meter keep the 6x9 bitmap font + 9-slice stand-ins from spec/gen_art.py.
extends Control
## Stance UI colours (Austin 2026-11-11; Arthur's mockups lane_chain/v5/post_v5.py:14): ATK red, DEF green, NEU yellow with dark text.
## Letter 'S' is the sim's internal code for Neutral (race_core.gd / combat.gd are unchanged).
const STANCE := {"A": Color8(232, 40, 44), "S": Color8(240, 200, 40), "D": Color8(44, 184, 74)}
const NAME := {"A": "ATK", "S": "NEU", "D": "DEF"}
const FULL := {"A": "Attack", "S": "Neutral", "D": "Defend"}   # option names: '<Stance> <phase>' (Austin's final call, 07:34)
const TAG := {"A": "POW", "S": "HAN", "D": "EN"}               # stat-tag chips (lane_chain/v5/post_v5.py:59)
const LANE := {"A": "OUT", "S": "MID", "D": "IN"}              # same lane rule as the entry tell (race_core.gd entry_tell)
const ORDER := ["A", "S", "D"]
const PH := ["ENTRY", "APEX", "EXIT"]
const PHL := ["entry", "apex", "exit"]
# lane_chain/v5/post_v5.py:15-17 + 76
const AMBER := Color8(255, 176, 40); const AMBER_D := Color8(150, 80, 14)
const EDGE := Color8(210, 230, 255); const EDGE_D := Color8(70, 90, 150); const INK := Color8(8, 8, 14); const PANEL := Color8(10, 14, 36)
const DIMT := Color8(88, 92, 110); const SUB := Color8(150, 165, 200); const TODO := Color8(110, 122, 155)
const SEG_OFF := Color8(69, 49, 38)   # pattern_read/compose_mockups.py:52
const OUTN := {1: "WIN", 0: "TIE", -1: "LOSS"}
const WHITE := Color("#e8e8e8")
var font_tex: Texture2D
var fm: Dictionary
var panel: StyleBoxTexture
var logo: Texture2D
var st: Dictionary = {}
var fn: FontFile   # NimbusSansNarrow-Bold, 1-bit
var fi: FontFile   # -BoldOblique

func setup(font_png: Texture2D, meta: Dictionary, panel_png: Texture2D, logo_png: Texture2D) -> void:
	font_tex = font_png; fm = meta; logo = logo_png
	panel = StyleBoxTexture.new(); panel.texture = panel_png
	for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]: panel.set_texture_margin(side, 4)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	size = Vector2(640, 480); mouse_filter = Control.MOUSE_FILTER_IGNORE
	fn = _font("res://fonts/NimbusSansNarrow-Bold.otf"); fi = _font("res://fonts/NimbusSansNarrow-BoldOblique.otf")

## mockup text is PIL fontmode '1' (1-bit, no AA); B.5 'drawn at native resolution'
func _font(p: String) -> FontFile:
	var f: FontFile = (load(p) as FontFile).duplicate()
	f.antialiasing = TextServer.FONT_ANTIALIASING_NONE; f.hinting = TextServer.HINTING_NORMAL
	f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED; f.oversampling = 1.0
	return f

func sw(s: String, sz: int, it := false) -> float: return (fi if it else fn).get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz).x
## anchor: 'l' left / 'm' centre / 'r' right on x; y = top of the line (PIL 'la'), or the vertical middle when mid = true
func t2(x: float, y: float, s: String, sz: int, col: Color, it := false, anchor := "l", shadow := true, mid := false) -> void:
	var f: FontFile = fi if it else fn
	var w := f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz).x
	if anchor == "m": x -= w / 2.0
	elif anchor == "r": x -= w
	var base := y + (f.get_ascent(sz) if not mid else (f.get_ascent(sz) - f.get_descent(sz)) / 2.0)
	x = roundf(x); base = roundf(base)
	if shadow: draw_string(f, Vector2(x + 1, base + 1), s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz, INK)
	draw_string(f, Vector2(x, base), s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz, col)

## PS1 50/50 semi-transparent poly (post_v5.py:149-153): alpha 255 -> 0.5, partial alpha -> a * 0.75
func semi(pts: PackedVector2Array, col: Color, a := 1.0) -> void:
	draw_colored_polygon(pts, Color(col, 0.5 if a >= 1.0 else a * 0.75))
func solid(pts: PackedVector2Array, col: Color) -> void: draw_colored_polygon(pts, col)
func outline(pts: PackedVector2Array, col: Color) -> void:
	var q := pts.duplicate(); q.append(pts[0]); draw_polyline(q, col, 1.0)
func cut_panel(x0: float, y0: float, x1: float, y1: float, c := 8.0) -> PackedVector2Array:
	return PackedVector2Array([Vector2(x0, y0), Vector2(x1 - c, y0), Vector2(x1, y0 + c), Vector2(x1, y1), Vector2(x0 + c, y1), Vector2(x0, y1 - c)])
func P(a: Array) -> PackedVector2Array:
	var o := PackedVector2Array()
	for i in range(0, a.size(), 2): o.append(Vector2(a[i], a[i + 1]))
	return o
func check(x: float, y: float, col: Color) -> void:
	draw_polyline(P([x, y + 3, x + 2, y + 5, x + 6, y]), col, 2.0)
func lock_x(x: float, y: float, r: float, col: Color) -> void:
	draw_line(Vector2(x - r, y - r), Vector2(x + r, y + r), col, 2.0); draw_line(Vector2(x - r, y + r), Vector2(x + r, y - r), col, 2.0)
func dimc(c: Color, k: float) -> Color: return Color(c.r * k, c.g * k, c.b * k)

## stat-tag chip, right-aligned at x1 (post_v5.py:45-57): dim = 'none drawn' outline; pending = planned, not played yet
func chip(x1: float, y: float, label: String, col: Color, dim := false, pending := false, sz := 11, h := 13.0) -> float:
	var w := sw(label, sz) + 12.0; var x0 := x1 - w
	var pts := P([x0 + 4, y, x1, y, x1 - 4, y + h, x0, y + h])
	if pending:
		solid(pts, dimc(col, 0.5)); outline(pts, INK); t2(x0 + w / 2, y + 1, label, sz, Color8(200, 205, 215), false, "m", false)
	elif dim:
		outline(pts, dimc(col, 0.55)); t2(x0 + w / 2, y + 1, label, sz, dimc(col, 0.7), false, "m", false)
	else:
		solid(pts, col); outline(pts, INK); t2(x0 + w / 2, y + 1, label, sz, INK if col == STANCE.S else Color.WHITE, false, "m", false)
	return w

func show_state(s: Dictionary) -> void:
	st = s; queue_redraw()

func tw(s: String) -> int: return s.length() * int(fm.cell[0])

func text(x: float, y: float, s: String, col: Color = WHITE) -> void:
	var cw: int = int(fm.cell[0]); var ch: int = int(fm.cell[1])
	for i in s.length():
		var k: int = s.unicode_at(i) - int(fm.first)
		if k <= 0 or k >= int(fm.count): continue
		var src := Rect2((k % int(fm.cols)) * cw, (k / int(fm.cols)) * ch, cw, ch)
		draw_texture_rect_region(font_tex, Rect2(x + i * cw + 1, y + 1, cw, ch), src, Color.BLACK)
		draw_texture_rect_region(font_tex, Rect2(x + i * cw, y, cw, ch), src, col)

func segs(x: float, y: float, parts: Array) -> void:
	for p in parts:
		text(x, y, p[0], p[1]); x += tw(p[0])

func center(cx: float, y: float, parts: Array) -> void:
	var w := 0
	for p in parts: w += tw(p[0])
	segs(roundf(cx - w / 2.0), y, parts)

func box(x: float, y: float, w: float, h: float) -> void: draw_style_box(panel, Rect2(x, y, w, h))
func rect(x: float, y: float, w: float, h: float, col: Color) -> void: draw_rect(Rect2(x, y, w, h), col)

## main menu: approved V3 logo (art/logo/final) + 9-slice list. Selection colour = car head glow #FFF2CC (B.2), never a stance colour.
func _draw_menu(m: Dictionary) -> void:
	draw_texture(logo, Vector2(roundi(320 - logo.get_width() / 2.0), 52))
	var items: Array = m.items
	var h: int = 16 + items.size() * 16
	box(200, 146, 240, h)
	for i in items.size():
		var sel: bool = i == int(m.sel); var y: int = 155 + i * 16
		if sel: rect(206, y - 3, 228, 14, Color("#30263F"))
		var label: String = items[i]
		if label == "SEED": label = "SEED  %s%s" % [m.seed_text if m.seed_text != "" else "RANDOM", "_" if sel and m.blink else ""]
		text(216, y, ("> " if sel else "  ") + label, Color("#FFF2CC") if sel else Color("#ADADC8"))
	center(320, 146 + h + 8, [["Up/Down select  Enter confirm", Color("#ADADC8")]])
	center(320, 146 + h + 19, [["on SEED: 0-9 type  Bksp delete  (empty = random)", Color("#ADADC8")]])
	box(4, 450, 196, 26); text(9, 454, "two-corner engine test"); text(9, 464, "pin " + String(m.commit))


func _draw() -> void:
	if st.is_empty(): return
	if st.has("menu"):
		_draw_menu(st.menu); return
	box(4, 4, 196, 26); text(9, 8, st.title); text(9, 18, st.sub)
	box(500, 4, 136, 26); text(505, 8, "640x480 RGB555"); text(505, 18, "F9 dump F10 load")
	_gap_meter(436, 34)
	if st.phase == "SELECT":
		_turn_in(); _lanes(); _entry_strip(); _plan_panel()
	elif st.phase == "TIMING":
		_timing_panel(); _replay_strip(-1)
	else:
		_replay_strip(mini(3, int(st.reveal)))
		if st.phase == "FINISHED": _finish_panel()
		else: _result_line()

## gap / lead meter, moved to the top right (the mirror owns top centre, the turn-in plate sits under it)
func _gap_meter(x: float, y: float) -> void:
	var lead: float = st.lead; var gap: float = st.gap
	var pos := "1st" if lead > 0 else ("2nd" if lead < 0 else "TIE")
	box(x, y, 200, 40); var cx := x + 100
	center(cx, y + 4, [["%s GAP %s%.3f lead %s%.3f" % [pos, "+" if gap >= 0 else "", gap, "+" if lead >= 0 else "", lead], WHITE]])
	rect(cx - 90, y + 15, 180, 6, Color("#9597AD")); rect(cx - 89, y + 16, 178, 4, Color("#161C2A"))
	var w: int = mini(89, roundi(absf(lead) * 89.0 * 2.5))
	if lead > 0: rect(cx, y + 16, w, 4, Color("#3CC8FF"))
	elif lead < 0: rect(cx - w, y + 16, w, 4, Color("#FF3C8C"))
	rect(cx, y + 13, 1, 10, Color.WHITE); text(cx - 90, y + 26, "RIVAL"); text(cx + 90 - tw("YOU"), y + 26, "YOU")

## corner-warning plate (post_v5.py:91-96), moved below the rear-view mirror; segmented line-lock timer (pattern_read 16 segments + 04.8s readout)
func _turn_in() -> void:
	var px := 296.0; var py := 56.0
	var pl := cut_panel(px, py, px + 48, py + 34, 7); semi(pl, PANEL); outline(pl, EDGE)
	var ar := [12, 29, 12, 13, 28, 13, 28, 7, 38, 16, 28, 25, 28, 19, 18, 19, 18, 29]
	if st.dir == "L":
		for i in range(0, ar.size(), 2): ar[i] = 48 - ar[i]
	var a := PackedVector2Array(); var sh := PackedVector2Array()
	for i in range(0, ar.size(), 2):
		a.append(Vector2(px + ar[i], py + ar[i + 1])); sh.append(Vector2(px + ar[i] + 1, py + ar[i + 1] + 2))
	solid(sh, AMBER_D); solid(a, AMBER); outline(a, INK)
	t2(px + 24, py + 38, "TURN-IN %dm" % roundi(float(st.turn_m)), 11, EDGE, true, "m")
	var n := 16; var on := ceili(16.0 * float(st.left) / float(st.total))
	var x0 := 320.0 - (n * 9) / 2.0 - 18.0; var y0 := py + 54
	for j in n:
		var x := x0 + j * 9
		solid(P([x + 2, y0, x + 8, y0, x + 6, y0 + 12, x, y0 + 12]), AMBER if j < on else SEG_OFF)
	t2(x0 + n * 9 + 40, y0 - 2, "%04.1fs" % float(st.left), 15, AMBER, false, "r")

## lane markers over the turn-in point (post_v5.py:66-88): chosen = amber chevron, available = faint tick, none drawn = dark tick crossed out
func _lanes() -> void:
	var pl: Dictionary = st.plan
	if not st.has("lanes") or st.lanes == null: return
	var chosen: String = pl.entry if pl.entry != "" else (ORDER[int(pl.sel)] if int(pl.phase) == 0 else "")
	for k in ORDER:
		var v = st.lanes.get(k)
		if v == null: continue
		var x := roundf((v as Vector2).x); var y := roundf((v as Vector2).y)
		if k == chosen:
			var w := 26.0; var h := 15.0; var t := 8.0
			var mk := func(dy: float) -> PackedVector2Array: return P([x - w / 2, y - h + dy, x - w / 2 + t, y - h + dy, x, y - 4 + dy, x + w / 2 - t, y - h + dy, x + w / 2, y - h + dy, x, y + dy])
			solid(mk.call(3.0), AMBER_D); solid(mk.call(0.0), AMBER); outline(mk.call(3.0), INK); outline(mk.call(0.0), INK)
			draw_line(Vector2(x - w / 2 + 2, y - h + 1), Vector2(x - w / 2 + t - 1, y - h + 1), Color8(255, 236, 170))
			t2(x, y - h - 9, LANE[k], 11, AMBER, false, "m", true, true)
		else:
			var w := 12.0; var h := 7.0; var t := 4.0
			var pts := P([x - w / 2, y - h, x - w / 2 + t, y - h, x, y - 3, x + w / 2 - t, y - h, x + w / 2, y - h, x, y])
			if int(pl.avail_entry[k]) <= 0:
				solid(pts, Color8(40, 42, 56)); outline(pts, Color8(70, 74, 92)); lock_x(x, y - 4, 4, dimc(STANCE.S, 0.7))
				t2(x, y - h - 8, LANE[k], 10, DIMT, false, "m", true, true)
			else:
				semi(pts, Color8(150, 170, 210)); t2(x, y - h - 8, LANE[k], 10, Color8(120, 135, 170), false, "m", true, true)

## entry strip, bottom left (post_v5.py:98-111)
func _entry_strip() -> void:
	var pl: Dictionary = st.plan
	var x0 := 14.0; var y0 := 430.0
	var poly := cut_panel(x0, y0, x0 + 188, y0 + 36, 6); semi(poly, PANEL); outline(poly, EDGE)
	t2(x0 + 8, y0 + 3, "ENTRY", 10, SUB, true)
	var chosen: String = pl.entry if pl.entry != "" else (ORDER[int(pl.sel)] if int(pl.phase) == 0 else "")
	for i in 3:
		var k: String = ORDER[i]; var cx := x0 + 36 + i * 58; var ry := y0 + 19
		if k == chosen:
			solid(P([cx - 21, ry - 6, cx + 19, ry - 6, cx + 17, ry + 6, cx - 23, ry + 6]), AMBER)
			t2(cx - 4 if pl.entry != "" else cx, ry, LANE[k], 12, INK, true, "m", false, true)
			if pl.entry != "": check(cx + 8, ry - 3, INK)
		elif int(pl.avail_entry[k]) <= 0:
			t2(cx - 2, ry - 2, LANE[k], 12, DIMT, true, "m", false, true)
			var lab: String = TAG[k] + " \u00b7 none drawn"; var w := sw(lab, 9) + 10.0
			var tp := P([cx - w / 2 + 3, ry + 4, cx + w / 2, ry + 4, cx + w / 2 - 3, ry + 14, cx - w / 2, ry + 14])
			outline(tp, dimc(STANCE[k], 0.55)); t2(cx, ry + 9, lab, 9, dimc(STANCE[k], 0.7), false, "m", false, true)
		else:
			t2(cx - 2, ry, LANE[k], 12, SUB, true, "m", true, true)

## PLAN THE LINE, lower right (post_v5.py:112-131). Options are '<Stance> <phase>'; the 6-card hand only decides availability.
func _plan_panel() -> void:
	var pl: Dictionary = st.plan
	var x0 := 404.0; var y0 := 328.0; var x1 := 628.0; var y1 := 468.0
	semi(cut_panel(x0, y0, x1, y1, 9), PANEL)
	outline(cut_panel(x0, y0, x1, y1, 9), EDGE); outline(cut_panel(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 8), EDGE_D)
	var tab := P([x0, y0 - 15, x0 + 108, y0 - 15, x0 + 119, y0, x0, y0]); solid(tab, AMBER); outline(tab, INK)
	t2(x0 + 7, y0 - 14, "PLAN THE LINE", 13, INK, true, "l", false)
	var ph: int = int(pl.phase)
	# breadcrumb ENTRY > APEX > EXIT: current in an amber slab, done = tick, pending = dim
	var x := x0 + 9; var y := y0 + 6
	for i in 3:
		var lab: String = PH[i]
		if i == 0 and pl.entry != "": lab = "ENTRY " + LANE[pl.entry]
		var w := sw(lab, 11, true)
		if i == ph:
			solid(P([x - 3, y - 1, x + w + 5, y - 1, x + w + 2, y + 12, x - 6, y + 12]), AMBER); t2(x, y, lab, 11, INK, true, "l", false); x += w + 6
		elif i < ph:
			t2(x, y, lab, 11, EDGE, true); check(x + w + 3, y + 3, STANCE.D); x += w + 12
		else:
			t2(x, y, lab, 11, TODO, true); x += w
		if i < 2: t2(x + 4, y, ">", 11, TODO, true); x += 15
	draw_line(Vector2(x0 + 6, y0 + 22), Vector2(x1 - 8, y0 + 22), EDGE_D)
	if ph < 3:
		for i in 3:
			var k: String = ORDER[i]; var ry := y0 + 29 + i * 22
			var off: bool = int(pl.avail[k]) <= 0
			if i == int(pl.sel) and not off:
				var al := [200, 150, 100, 55]
				for j in 4:
					var bx := x0 + 6 + j * 52
					semi(P([bx, ry - 2, bx + 56, ry - 2, bx + 52, ry + 16, bx - 4, ry + 16]), AMBER, al[j] / 255.0)
				var tri := P([x0 + 7, ry + 2, x0 + 14, ry + 7, x0 + 7, ry + 12]); solid(tri, Color.WHITE); outline(tri, INK)
			var lab: String = "%s %s" % [FULL[k], PHL[ph]]
			t2(x0 + 19, ry, lab, 13, DIMT if off else Color.WHITE, false, "l", not off)
			if ph == 0: t2(x0 + 23 + sw(lab, 13), ry + 2, LANE[k], 10, DIMT if off else SUB, true, "l", not off)   # lane hint
			chip(x1 - 8, ry + 1, TAG[k] + (" \u00b7 none drawn" if off else ""), STANCE[k], off)
	else:
		t2(x0 + 19, y0 + 40, "Line set. Enter to lock now", 13, Color.WHITE)
	t2(x0 + 9, y1 - 16, "Line locks at turn-in", 10, SUB, true)
	t2(x1 - 10, y1 - 16, "Enter SET  Bksp BACK", 10, SUB, false, "r")

## LINE LOCKED strip (post_v5.py:132-148). During playback the current phase is the amber band; in RESULT each clash fills in as it is revealed.
func _replay_strip(reveal: int) -> void:
	var line: String = st.line
	if line.length() < 3: return
	var r: Dictionary = st.result
	var x0 := 12.0; var y0 := 432.0; var x1 := 628.0; var y1 := 468.0
	semi(cut_panel(x0, y0, x1, y1, 8), PANEL); outline(cut_panel(x0, y0, x1, y1, 8), EDGE)
	var tab := P([x0, y0 - 14, x0 + 92, y0 - 14, x0 + 102, y0, x0, y0]); solid(tab, EDGE); outline(tab, INK)
	t2(x0 + 7, y0 - 13, "LINE LOCKED", 12, INK, true, "l", false)
	t2(x1 - 10, y0 - 12, "REPLAY" if reveal < 0 else "RESULT", 10, SUB, true, "r")
	var cur: int = int(st.play_phase) if reveal < 0 else -1
	var x := x0 + 4; var w := 200.0
	for i in 3:
		var k: String = line[i]
		var state := "cur" if i == cur else ("done" if (reveal < 0 and i < cur) or (reveal >= 0 and i < reveal) else "todo")
		if state == "cur":
			var band := P([x + 2, y0 + 4, x + w, y0 + 4, x + w - 5, y1 - 4, x - 3, y1 - 4]); semi(band, AMBER, 190 / 255.0); outline(band, AMBER)
		t2(x + 6, y0 + 5, PH[i], 10, INK if state == "cur" else SUB, true, "l", state != "cur")
		var call: String = "%s %s" % [FULL[k], PHL[i]]
		t2(x + 6, y0 + 16, call, 13, Color.WHITE if state == "cur" else (Color8(225, 232, 250) if state == "done" else Color8(125, 135, 165)), false)
		if reveal >= 0 and i < reveal and not r.is_empty():
			var o: int = int(r.outcomes[i]); var ok := {1: "WIN", 0: "TIE", -1: "LOSS"}[o] as String
			var ox := x + 6 + sw(PH[i], 10, true) + 8
			t2(ox, y0 + 5, "%s vs %s  +%.2f/+%.2f" % [ok, NAME[r.line[i]], float(r.player_clash[i]), float(r.opponent_clash[i])], 10, AMBER if o == 1 else (EDGE if o == 0 else Color8(150, 150, 170)), true)
			chip(x + w - 8, y0 + 18, TAG[r.line[i]], STANCE[r.line[i]], false, false, 9, 11.0)
			chip(x + w - 8 - sw(TAG[r.line[i]], 9) - 16, y0 + 18, TAG[k], STANCE[k], false, false, 9, 11.0)
		else:
			if state == "done" and reveal < 0: check(x + 6 + sw(call, 13) + 5, y0 + 20, STANCE.D)
			chip(x + w - 8, y0 + 12, TAG[k], STANCE[k], false, state == "todo")
		x += w + 2
		if i < 2: draw_line(Vector2(x - 1, y0 + 6), Vector2(x - 5, y1 - 6), EDGE_D)

## compact timing needle (SPACE), kept from the earlier build, above the strip
func _timing_panel() -> void:
	box(232, 372, 176, 40); center(320, 376, [["TIMING - SPACE", WHITE]])
	rect(240, 388, 160, 10, Color("#9597AD")); rect(241, 389, 158, 8, Color("#161C2A")); rect(316, 389, 8, 8, Color("#3CC8FF"))
	rect(320 + roundi(st.needle * 78.0) - 1, 386, 2, 14, Color.WHITE)

func _result_line() -> void:
	var r: Dictionary = st.result
	if r.is_empty(): return
	var tm := ("%d" % int(r.timing)) if float(r.timing) == floorf(float(r.timing)) else str(r.timing)
	var s := "timing %s (q %.2f)%s%s" % [tm, r.q_time, " [auto]" if r.autofilled else "", "  LEAD CHANGE" if st.leader_changed else ""]
	t2(120, 419, s, 10, SUB, true)
	if int(st.reveal) >= 3: t2(618, 404, "Enter: finish" if st.last_corner else "Enter: next corner", 11, EDGE, true, "r")

## finish: winner + options (keys 1-3, or arrows + Enter), centre panel above the strip
func _finish_panel() -> void:
	var wn: String = st.winner
	var pl := cut_panel(170, 300, 470, 398, 8); semi(pl, PANEL); outline(pl, EDGE)
	t2(320, 306, "%s  %.4f vs %.4f" % ["TIE" if wn == "Tie" else ("YOU WIN" if wn == "Player" else "RIVAL WINS"), st.cum_p, st.cum_o], 13, Color("#FFF2CC"), false, "m")
	if st.get("fin") != null:
		var fin: Dictionary = st.fin
		for i in (fin.items as Array).size():
			var sel: bool = i == int(fin.sel); var y := 328.0 + i * 18
			if sel: semi(P([182, y - 2, 458, y - 2, 454, y + 14, 178, y + 14]), AMBER, 200 / 255.0)
			t2(192, y, "%d  %s" % [i + 1, fin.items[i]], 12, INK if sel else EDGE, false, "l", not sel)
		t2(320, 384, "1-3 or Up/Down + Enter", 10, SUB, true, "m")
