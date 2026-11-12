## Base for every HUD panel in hud.tscn (scene refactor 2026-11-12). Holds the drawing helpers and palette that were in hud.gd.
## Panels are real Control nodes placed in the editor at their design rect (640x480 design units; hud.tscn is drawn into the
## 1280x960 HUD SubViewport at scale 2, Austin 2026-11-11 22:21 + art_direction.md B.5c). Each panel draws in the same absolute
## design coordinates as before: _o() cancels the node offset, so moving a node in the editor only moves its selection box;
## the drawn positions stay those of the approved frames (post_lsc.py / post_clash.py / post_v5.py) unless the code changes.
@tool
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
# ── B.5a / B.5b frame palette (art/ui/line_select_cam/post_lsc.py:15-17, unapproved/arthur/mockups/line_clash/post_clash.py:15-17) ──
const L_WHITE := Color8(220, 230, 242); const L_DIM := Color8(140, 159, 180); const L_DIMMER := Color8(96, 108, 132)
const L_EDGE := Color8(71, 94, 127); const L_EDGE_L := Color8(150, 172, 205); const L_AMBER := Color8(255, 184, 56); const L_AMBER_D := Color8(150, 90, 20)
const L_INK := Color8(8, 10, 16); const SOD := Color8(240, 200, 148); const L_SEG_OFF := Color8(68, 52, 40); const L_TODO := Color8(40, 46, 64)
const PHN := ["ENTRY", "APEX", "EXIT"]
## text raster scale (2x grid): text is rasterised at size x 2, 1-bit, so glyph edges sit on the 1280x960 grid (see hud.gd)
const TS := 2

var hud   # the hud.gd root: fonts, 9-slice panel, logo, state
var st: Dictionary:
	get: return hud.st if hud != null else {}

## offset that cancels this node's position (summed up to the HUD root), so drawing stays in absolute design units
func _o() -> Vector2:
	var p := Vector2.ZERO; var n: Node = self
	while n != hud and n is Control:
		p += (n as Control).position; n = n.get_parent()
	return -p
## design-unit origin of this node (for panels whose layout is relative to their own position)
func origin() -> Vector2: return -_o()

func _draw() -> void:
	if hud == null or st.is_empty(): return
	draw_set_transform(_o(), 0.0, Vector2.ONE)
	paint()
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

## override: draw the panel (absolute design units)
func paint() -> void: pass

## widths and ascents are measured at the raster size (size x 2) and given back in design units
func sw(s: String, sz: int, it := false) -> float: return (hud.fi if it else hud.fn).get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz * TS).x / TS
## anchor: 'l' left / 'm' centre / 'r' right on x; y = top of the line (PIL 'la'), or the vertical middle when mid = true
func t2(x: float, y: float, s: String, sz: int, col: Color, it := false, anchor := "l", shadow := true, mid := false) -> void:
	var f: FontFile = hud.fi if it else hud.fn; var z := sz * TS
	var w := f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, z).x
	var X := x * TS; var B := y * TS + (f.get_ascent(z) if not mid else (f.get_ascent(z) - f.get_descent(z)) / 2.0)
	if anchor == "m": X -= w / 2.0
	elif anchor == "r": X -= w
	X = roundf(X); B = roundf(B)
	draw_set_transform(_o(), 0.0, Vector2(1.0 / TS, 1.0 / TS))   # undo the HUD's x2 so glyphs land 1:1 on the 1280x960 grid
	if shadow: draw_string(f, Vector2(X + TS, B + TS), s, HORIZONTAL_ALIGNMENT_LEFT, -1, z, INK)
	draw_string(f, Vector2(X, B), s, HORIZONTAL_ALIGNMENT_LEFT, -1, z, col)
	draw_set_transform(_o(), 0.0, Vector2.ONE)

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

## 6x9 bitmap font (debug boxes, menu, gap meter)
func tw(s: String) -> int: return s.length() * int(hud.fm.cell[0])
func text(x: float, y: float, s: String, col: Color = WHITE) -> void:
	var fm: Dictionary = hud.fm
	var cw: int = int(fm.cell[0]); var ch: int = int(fm.cell[1])
	for i in s.length():
		var k: int = s.unicode_at(i) - int(fm.first)
		if k <= 0 or k >= int(fm.count): continue
		var src := Rect2((k % int(fm.cols)) * cw, (k / int(fm.cols)) * ch, cw, ch)
		draw_texture_rect_region(hud.font_tex, Rect2(x + i * cw + 1, y + 1, cw, ch), src, Color.BLACK)
		draw_texture_rect_region(hud.font_tex, Rect2(x + i * cw, y, cw, ch), src, col)
func segs(x: float, y: float, parts: Array) -> void:
	for p in parts:
		text(x, y, p[0], p[1]); x += tw(p[0])
func center(cx: float, y: float, parts: Array) -> void:
	var w := 0
	for p in parts: w += tw(p[0])
	segs(roundf(cx - w / 2.0), y, parts)
func box(x: float, y: float, w: float, h: float) -> void: draw_style_box(hud.panel, Rect2(x, y, w, h))
func rect(x: float, y: float, w: float, h: float, col: Color) -> void: draw_rect(Rect2(x, y, w, h), col)

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
