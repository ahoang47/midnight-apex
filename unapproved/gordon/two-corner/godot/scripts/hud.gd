## Display-resolution HUD laid out in 640x480 design units (canvas_items stretch, Austin 2026-11-11). Plan the Line layout from Arthur's /workspace/mockups/lane_chain/v5/post_v5.py (NimbusSansNarrow,
## PS1 50/50 semi panels); debug boxes, menu and gap meter keep the 6x9 bitmap font + 9-slice stand-ins from spec/gen_art.py.
extends Control
## Stance UI colours (Austin 2026-11-11, swapped the same day): ATK/POW green #2CB84A, DEF/EN red #E8282C, NEU/HAN yellow #F0C828 with dark text.
## Letter 'S' is the sim's internal code for Neutral (race_core.gd / combat.gd are unchanged).
const STANCE := {"A": Color8(44, 184, 74), "S": Color8(240, 200, 40), "D": Color8(232, 40, 44)}
const CHECK_GREEN := Color8(44, 184, 74)  # breadcrumb tick; not a stance colour (stays green after the DEF/EN swap to red)
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

## Display-resolution HUD (Austin 2026-11-11 21:41, 'continue upressing'): the project stretch mode is canvas_items, so this
## Control is laid out in 640x480 design units (same positions, sizes and colours as Arthur's frames) and the canvas transform
## scales it to the window. Glyphs are rasterised at size x scale by the viewport's automatic font oversampling
## (oversampling 0 = follow the viewport), greyscale AA, light hinting. This departs from the mockups' 1-bit 640x480 text
## (post_lsc.py:34) and from art_direction.md:115/:141 integer-nearest upscale, for the UI only; the 3D world keeps it.
func _font(p: String) -> FontFile:
	var f: FontFile = (load(p) as FontFile).duplicate()
	f.antialiasing = TextServer.FONT_ANTIALIASING_GRAY; f.hinting = TextServer.HINTING_LIGHT
	f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_AUTO; f.oversampling = 0.0
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
	if st.mirror: _mirror_frame()
	_corner_plate()
	_gap_meter(203, 428)
	if st.phase == "SELECT":
		_timer_panel(false); _debug(14, 64)
		if int(st.plate.stop) == 0: _lanes()
		_entry_strip(); _plan_panel()
	elif st.phase == "TIMING" and st.locked_hold:
		_timer_panel(true); _debug(14, 64); _lock_banner()
	elif st.phase == "TIMING":
		_line_vs_line(int(st.play_phase)); _debug(14, 106); _timing_panel()
	else:
		_line_vs_line(-1); _debug(14, 106)
		if st.phase == "FINISHED": _finish_panel()
		else: _result_line()

# ── B.5a / B.5b frame palette (art/ui/line_select_cam/post_lsc.py:15-17, unapproved/arthur/mockups/line_clash/post_clash.py:15-17) ──
const L_WHITE := Color8(220, 230, 242); const L_DIM := Color8(140, 159, 180); const L_DIMMER := Color8(96, 108, 132)
const L_EDGE := Color8(71, 94, 127); const L_EDGE_L := Color8(150, 172, 205); const L_AMBER := Color8(255, 184, 56); const L_AMBER_D := Color8(150, 90, 20)
const L_INK := Color8(8, 10, 16); const SOD := Color8(240, 200, 148); const L_SEG_OFF := Color8(68, 52, 40); const L_TODO := Color8(40, 46, 64)
const PHN := ["ENTRY", "APEX", "EXIT"]

func lpanel(x0: float, y0: float, x1: float, y1: float, col: Color = L_EDGE, c := 5.0) -> void:
	var p := cut_panel(x0, y0, x1, y1, c); semi(p, PANEL); outline(p, col)
## stance chip (post_clash.py:39-42): 49 x 14 slanted, label = ATK / DEF / NEU
func lchip(x: float, y: float, k: String, w := 49.0) -> void:
	var p := P([x + 4, y, x + w, y, x + w - 4, y + 14, x, y + 14]); solid(p, STANCE[k]); outline(p, L_INK)
	t2(x + w / 2, y + 7, NAME[k], 11, L_INK if k == "S" else Color.WHITE, false, "m", false, true)
## RESULT chip (post_clash.py:43-47)
func lres(cx: float, y: float, o: int) -> void:
	var w := 49.0; var x := cx - floorf(w / 2); var p := P([x + 4, y, x + w, y, x + w - 4, y + 14, x, y + 14])
	if o == 1: solid(p, L_AMBER); t2(cx, y + 7, "WIN", 11, L_INK, false, "m", false, true)
	elif o == -1: solid(p, Color8(40, 44, 60)); outline(p, L_EDGE_L); t2(cx, y + 7, "LOSS", 11, L_WHITE, false, "m", false, true)
	else: solid(p, L_EDGE); t2(cx, y + 7, "TIE", 11, L_WHITE, false, "m", false, true)

## rear-view mirror frame (post_lsc.py:46-48); the image itself is composited by the post shader
func _mirror_frame() -> void:
	draw_rect(Rect2(221.5, 13.5, 197, 69), Color8(110, 127, 151), false, 1.0); draw_rect(Rect2(222.5, 14.5, 195, 67), Color8(15, 20, 30), false, 1.0)
	t2(291, 84, "REAR VIEW", 9, L_DIM)

## B.5b line-lock timer, top left (post_lsc.py:50-58): 17 segments; after the lock 'SET' with every segment lit pale
func _timer_panel(locked: bool) -> void:
	lpanel(14, 12, 192, 57); t2(23, 18, "LINE LOCK", 12, L_WHITE)
	var on := 17 if locked else ceili(17.0 * float(st.left) / float(st.total))
	if locked: t2(183, 18, "SET", 19, L_WHITE, false, "r")
	else: t2(183, 18, "%04.1fs" % float(st.left), 19, L_AMBER, false, "r")
	for j in 17:
		solid(P([24 + j * 9, 43, 30 + j * 9, 43, 28 + j * 9, 50, 22 + j * 9, 50]), L_EDGE_L if locked else (L_AMBER if j < on else L_SEG_OFF))

## corner plate, top right (B.5b:261-262 / B.5a:269; post_lsc.py:60-73, post_clash.py:48-55): corner map + E / A / X stops
func _corner_plate() -> void:
	var pl: Dictionary = st.plate
	lpanel(476, 12, 628, 96); t2(534, 18, String(pl.name), 16, L_WHITE)
	var md: String = pl.mode; var k: int = int(pl.stop)
	var cur := -1; var ndone := 0
	match md:
		"VIEW": cur = k; ndone = k
		"LOCK": cur = 0; ndone = 3
		"PLAY": cur = k; ndone = k
		_: cur = -1; ndone = 3
	var lab := "PLAY" if md in ["PLAY", "DONE"] else "VIEW"
	t2(534, 40, lab, 9, L_DIM)
	t2(560, 38, "RESULT" if md == "DONE" else PHN[cur], 13, L_AMBER)
	if md in ["VIEW", "LOCK"]:
		var lt := ["E", "A", "X"]
		for i in 3:
			var on_cur := i == cur; var dn := (md == "LOCK" and i > 0) or (md == "VIEW" and i < cur)
			t2(534 + i * 14, 58, lt[i], 10, L_AMBER if on_cur else (L_WHITE if dn else L_DIMMER))
	t2(534, 74, "PLAYBACK" if lab == "PLAY" else "CAMERA STOP", 9, L_DIM)
	# map: fit the path into x 486..526, y 28..90, forward = up
	var ic: Dictionary = pl.icon; var pts: Array = ic.pts
	var mn := Vector2(1e9, 1e9); var mx := Vector2(-1e9, -1e9)
	for v in pts: mn = Vector2(minf(mn.x, v.x), minf(mn.y, v.y)); mx = Vector2(maxf(mx.x, v.x), maxf(mx.y, v.y))
	var sc := minf(40.0 / maxf(mx.x - mn.x, 1.0), 58.0 / maxf(mx.y - mn.y, 1.0))
	var ctr := (mn + mx) / 2.0
	var f := func(v: Vector2) -> Vector2: return Vector2(506, 60) + (v - ctr) * sc
	var line := PackedVector2Array()
	for v in pts: line.append(f.call(v))
	draw_polyline(line, SOD, 3.0)
	var e: Vector2 = line[line.size() - 1]; var dvec: Vector2 = (e - line[line.size() - 2]).normalized(); var nv := Vector2(-dvec.y, dvec.x)
	solid(PackedVector2Array([e + dvec * 6, e - dvec * 4 + nv * 6, e - dvec * 4 - nv * 6]), SOD)
	for i in 3:
		var c: Vector2 = f.call(ic.stops[i])
		var dn := i < ndone and i != cur
		var dia := P([c.x, c.y - 5, c.x + 5, c.y, c.x, c.y + 5, c.x - 5, c.y])
		solid(dia, L_AMBER if i == cur else (L_WHITE if dn else L_TODO)); outline(dia, L_INK)

## debug readout (seed / pin / rig / keys), kept small and out of the approved panels
func _debug(x: float, y: float) -> void:
	box(x, y, 178, 36); text(x + 5, y + 4, st.title); text(x + 5, y + 14, st.sub); text(x + 5, y + 24, "F9 dump  F10 load", Color("#ADADC8"))

## B.5b frame 4 (post_lsc.py:120-130): LINE LOCKED banner over the Entry chase camera, then playback runs
func _lock_banner() -> void:
	var x0 := 176.0; var y0 := 112.0; var x1 := 404.0; var y1 := 150.0
	semi(cut_panel(x0 - 6, y0 - 4, x1 + 6, y1 + 22, 9), PANEL)
	var slab := P([x0 + 10, y0, x1, y0, x1 - 10, y1, x0, y1])
	var sh := PackedVector2Array()
	for v in slab: sh.append(v + Vector2(2, 3))
	solid(sh, L_AMBER_D); solid(slab, L_AMBER); outline(slab, L_INK)
	draw_line(Vector2(x0 + 12, y0 + 3), Vector2(x1 - 4, y0 + 3), Color8(255, 236, 170), 1.0)
	t2((x0 + x1) / 2.0, (y0 + y1) / 2.0 + 1, "LINE LOCKED", 26, L_INK, true, "m", false, true)
	var ln: String = st.line if String(st.line).length() == 3 else ""
	for k in ln.length():
		var cx := x0 + 22 + k * 70; lchip(cx, y1 + 5, ln[k])
		if k < 2: t2(cx + 57, y1 + 5, ">", 12, L_DIM)

## B.5a LINE LOCKED panel (post_clash.py:62-85): YOU and RIVAL rows face up from the start, amber outline on the column
## being played, RESULT fills in as each phase plays. k = phase being played (-1 = playback over: every result shown).
func _line_vs_line(k: int) -> void:
	var you: String = st.line; var riv: String = st.rline; var outs: Array = st.outs
	if you.length() < 3 or riv.length() < 3: return
	var x0 := 120.0; var y0 := 12.0; var x1 := 466.0; var y1 := 100.0
	lpanel(x0, y0, x1, y1, L_EDGE_L, 8)
	t2(x0 + 8, y0 + 6, "LINE LOCKED", 12, L_AMBER, true)
	var cols := [241.0, 331.0, 421.0]
	for i in 3:
		var cx: float = cols[i]; var cur := i == k
		if cur:
			outline(cut_panel(cx - 42, y0 + 3, cx + 42, y1 - 3, 5), L_AMBER)
			solid(P([cx - 30, y0 + 9, cx - 25, y0 + 13, cx - 30, y0 + 17]), L_AMBER)
		t2(cx, y0 + 13, PHN[i], 11, L_AMBER if cur else (L_WHITE if (k < 0 or i < k) else L_DIM), false, "m", true, true)
	var rows := [["YOU", you, 30.0], ["RIVAL", riv, 50.0]]
	for rw in rows:
		var dy: float = rw[2]
		t2(x0 + 8, y0 + dy + 1, rw[0], 11, L_WHITE if rw[0] == "YOU" else L_DIM)
		for i in 3: lchip(cols[i] - 24, y0 + dy, String(rw[1])[i])
		for i in 2: t2(cols[i] + 45, y0 + dy + 7, ">", 10, L_DIMMER, false, "m", true, true)
	t2(x0 + 8, y0 + 71, "RESULT", 11, L_DIM)
	for i in 3:
		if (k < 0 or i <= k) and outs.size() == 3: lres(cols[i], y0 + 70, int(outs[i]))
		else: t2(cols[i], y0 + 77, "- -", 11, L_DIMMER, false, "m", true, true)
	draw_line(Vector2(x0 + 6, y0 + 25), Vector2(x1 - 8, y0 + 25), L_EDGE, 1.0)

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
			draw_line(Vector2(x - w / 2 + 2, y - h + 1), Vector2(x - w / 2 + t - 1, y - h + 1), Color8(255, 236, 170), 1.0)
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
			t2(x, y, lab, 11, EDGE, true); check(x + w + 3, y + 3, CHECK_GREEN); x += w + 12
		else:
			t2(x, y, lab, 11, TODO, true); x += w
		if i < 2: t2(x + 4, y, ">", 11, TODO, true); x += 15
	draw_line(Vector2(x0 + 6, y0 + 22), Vector2(x1 - 8, y0 + 22), EDGE_D, 1.0)
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
	t2(200, 104, s, 10, SUB, true)
	if int(st.reveal) >= 3: t2(200, 117, "Enter: finish" if st.last_corner else "Enter: next corner", 11, EDGE, true)

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
