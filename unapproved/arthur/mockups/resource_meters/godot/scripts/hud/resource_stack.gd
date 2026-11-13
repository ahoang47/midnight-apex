## Unapproved concept: three stacked resource meters on the left of the race HUD.
## Fuel (POW) / Brakes (EN) / Suspension (HAN). Purely visual; costs and empty-state
## rules are not decided. Extends the line-preview HUD plate language (grain, bevel,
## pixel-hard type, slanted pips like LINE LOCK).
##
## Variants:
##   A — slim stack, icon + vertical segmented bar + label
##   B — horizontal segmented bars to the right of each icon (same pip language as LINE LOCK)
##   C — one combined plate with a segmented ring around each icon and a short pip track
##
## EN icon: a wheel (tyre + rim + spokes) with the brake rotor and caliper visible
## through the spoke gaps, so it reads as the wheel-and-brake package.
@tool
extends "res://scripts/hud/hud_panel.gd"

const COL := {
	"fuel": Color8(44, 184, 74),    # POW
	"brakes": Color8(232, 40, 44),  # EN
	"susp": Color8(240, 200, 40),   # HAN
}
const ITEMS := [
	{"key": "fuel", "label": "FUEL", "stat": "POW"},
	{"key": "brakes", "label": "BRAKES", "stat": "EN"},
	{"key": "susp", "label": "SUSP", "stat": "HAN"},
]
const TYRE := Color8(22, 20, 24)
const RIM := Color8(210, 216, 226)
const RIM_D := Color8(120, 128, 140)
const HUB := Color8(48, 50, 58)
const INK_I := Color8(6, 6, 10)

func paint() -> void:
	var rs: Dictionary = st.get("resources", {})
	if rs.is_empty():
		return
	var variant := String(rs.get("variant", "B"))
	match variant:
		"A":
			_paint_a(rs)
		"C":
			_paint_c(rs)
		_:
			_paint_b(rs)

func _item_state(rs: Dictionary, it: Dictionary) -> Dictionary:
	var key: String = it.key
	var pips: int = int(rs.get("pips", 8))
	var val: int = clampi(int(rs.get(key, pips)), 0, pips)
	var ghosts: Dictionary = rs.get("ghosts", {})
	var badges: Dictionary = rs.get("badge", {})
	var warn: Array = rs.get("warn", [])
	return {
		"key": key,
		"label": it.label,
		"stat": it.stat,
		"col": COL[key],
		"val": val,
		"pips": pips,
		"ghost": int(ghosts.get(key, 0)),
		"badge": String(badges.get(key, "")),
		"warn": warn.has(key),
		"spent": String(rs.get("spent", "")) == key,
		"flash": String(rs.get("flash", "")) == key,
		"blink": bool(rs.get("blink", false)) and warn.has(key),
		"empty": val <= 0,
	}

# ─────────────────────────────────────────────────────────────────────────────
# Variant A: slim vertical bars beside icons, each on its own small plate.
# ─────────────────────────────────────────────────────────────────────────────
func _paint_a(rs: Dictionary) -> void:
	var x0 := 14.0
	var y0 := 64.0
	for i in ITEMS.size():
		var s: Dictionary = _item_state(rs, ITEMS[i])
		var y := y0 + i * 48.0
		var x1 := 152.0
		var y1 := y + 44.0
		_plate(x0, y, x1, y1, s)
		_icon_at(x0 + 16, y + 22, s, 11.0)
		_pips_v(x0 + 32, y + 6, y1 - 6, s)
		var lx := x0 + 48
		t2(lx, y + 8, s.label, 10, _lab_col(s), true, "l", true, false, true)
		var tw := _stat_tag(lx, y + 22, s)
		_badge_at(lx + tw + 3, y + 22, s, "l")

# ─────────────────────────────────────────────────────────────────────────────
# Variant B: horizontal slanted pips to the right of each icon (LINE LOCK language).
# Three slim plates, same width as LINE LOCK so they read as a left-column family.
# ─────────────────────────────────────────────────────────────────────────────
func _paint_b(rs: Dictionary) -> void:
	var x0 := 14.0
	var y0 := 64.0
	var x1 := 192.0
	for i in ITEMS.size():
		var s: Dictionary = _item_state(rs, ITEMS[i])
		var y := y0 + i * 40.0
		var y1 := y + 36.0
		_plate(x0, y, x1, y1, s)
		_icon_at(x0 + 16, y + 18, s, 11.0)
		t2(x0 + 32, y + 6, s.label, 11, _lab_col(s), true, "l", true, false, true)
		var tw := _stat_tag(x0 + 32, y + 20, s)
		_badge_at(x0 + 32 + tw + 3, y + 20, s, "l")
		_pips_h(120.0, y + 12, 8, s)

# ─────────────────────────────────────────────────────────────────────────────
# Variant C: one combined plate, segmented ring around each icon, short pip track.
# Same left edge and width as LINE LOCK.
# ─────────────────────────────────────────────────────────────────────────────
func _paint_c(rs: Dictionary) -> void:
	var x0 := 14.0
	var y0 := 64.0
	var x1 := 192.0
	var y1 := 200.0
	# Outer plate, then the three rows inside.
	var body := cut_panel(x0, y0, x1, y1, 6.0)
	semi(body, PANEL)
	plate_finish(body, x0, y0, x1, y1)
	outline(body, EDGE)
	outline(cut_panel(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 5.0), EDGE_D)
	for i in ITEMS.size():
		var s: Dictionary = _item_state(rs, ITEMS[i])
		var y := y0 + 8.0 + i * 42.0
		if s.warn or s.blink or s.empty:
			var a := 0.16 if s.blink or s.empty else 0.10
			semi(P([x0 + 6, y - 1, x1 - 6, y - 1, x1 - 8, y + 39, x0 + 4, y + 39]), s.col, a)
		_ring(x0 + 26, y + 19, s, 16.0, 13.0)
		_icon_at(x0 + 26, y + 19, s, 8.0)
		t2(x0 + 48, y + 6, s.label, 11, _lab_col(s), true, "l", true, false, true)
		var tw := _stat_tag(x0 + 48, y + 20, s)
		_badge_at(x0 + 48 + tw + 3, y + 20, s, "l")
		_pips_h(136.0, y + 14, 6, s)

# ─────────────────────────────────────────────────────────────────────────────
# Shared chrome
# ─────────────────────────────────────────────────────────────────────────────
func _plate(x0: float, y0: float, x1: float, y1: float, s: Dictionary) -> void:
	var col: Color = EDGE
	if s.empty:
		col = Color8(232, 40, 44)
	elif s.blink or s.warn:
		col = L_AMBER
	elif s.flash or s.spent:
		col = s.col
	var body := cut_panel(x0, y0, x1, y1, 5.0)
	semi(body, PANEL)
	plate_finish(body, x0, y0, x1, y1)
	outline(body, col)
	outline(cut_panel(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 4.0), EDGE_D)
	if s.blink:
		# Bright warning flash on the outer edge (the still that stands in for a blink).
		outline(cut_panel(x0 - 1, y0 - 1, x1 + 1, y1 + 1, 6.0), Color(L_AMBER, 0.9))

func _lab_col(s: Dictionary) -> Color:
	if s.empty:
		return Color8(180, 70, 70)
	if s.blink or s.warn:
		return L_AMBER
	if s.flash:
		return Color.WHITE
	return L_WHITE

func _stat_tag(x: float, y: float, s: Dictionary) -> float:
	# Tiny framed stat note, same idea as the PLAN THE LINE stat box.
	var lab: String = s.stat
	var sz := 8
	var w := maxf(sw(lab, sz, true, true) + 8.0, 22.0)
	var h := 10.0
	var pts := P([x + 2, y, x + w, y, x + w - 2, y + h, x, y + h])
	var fill: Color = s.col if not s.empty else dimc(s.col, 0.35)
	if s.blink:
		fill = s.col
	solid(pts, fill)
	outline(pts, INK)
	var tc: Color = INK if s.key == "susp" else Color.WHITE
	if s.empty and not s.blink:
		tc = Color8(230, 230, 235)
	t2(x + w / 2.0, y + h / 2.0, lab, sz, tc, true, "m", false, true)
	return w

func _badge_at(x: float, y: float, s: Dictionary, anchor: String = "r") -> void:
	var b: String = s.badge
	if b == "":
		return
	var sz := 8
	var w := sw(b, sz, true, true) + 8.0
	var x0 := x - w if anchor == "r" else x
	var col: Color = L_AMBER if b == "LOW" else (s.col if b == "RECOVER" else Color8(232, 40, 44))
	var pts := P([x0 + 2, y, x0 + w, y, x0 + w - 2, y + 10, x0, y + 10])
	solid(pts, col)
	outline(pts, INK)
	var tc: Color = INK if b == "LOW" or b == "RECOVER" else Color.WHITE
	if b == "RECOVER":
		tc = INK  # yellow fill
	t2(x0 + w / 2.0, y + 5.0, b, sz, tc, true, "m", false, true)

func _pip_col(s: Dictionary, lit: bool, ghost: bool) -> Color:
	if lit:
		if s.flash:
			return Color(minf(s.col.r * 1.15 + 0.15, 1), minf(s.col.g * 1.15 + 0.15, 1), minf(s.col.b * 1.15 + 0.1, 1))
		if s.blink:
			return L_AMBER if s.key != "susp" else s.col
		return s.col
	if ghost:
		return dimc(s.col, 0.55)
	return L_SEG_OFF

func _pips_h(x: float, y: float, count: int, s: Dictionary) -> void:
	# Slanted parallelograms, same construction as LINE LOCK (6 wide, 8 tall, stride 9).
	# Scale the 8-pip value onto `count` lit pips.
	var on := int(round(float(s.val) / float(s.pips) * count)) if s.pips > 0 else 0
	var gh := int(round(float(s.ghost) / float(s.pips) * count)) if s.pips > 0 else 0
	for j in count:
		var px := x + j * 9.0
		var lit := j < on
		var ghost := (not lit) and j < on + gh
		var pts := P([px, y, px + 6, y, px + 4, y + 9, px - 2, y + 9])
		solid(pts, _pip_col(s, lit, ghost))
		if ghost:
			outline(pts, dimc(s.col, 0.7))
		elif lit and (s.flash or s.spent or s.blink):
			outline(pts, INK)

func _pips_v(x: float, y0: float, y1: float, s: Dictionary) -> void:
	# 8 pips stacked bottom-up, 3 px body + 1 px gap, same slant as LINE LOCK.
	var n: int = s.pips
	var body := 3.0
	var gap := 1.0
	var h := body + gap
	# centre the stack in [y0, y1]
	var total := h * n - gap
	var y_top := y0 + maxf((y1 - y0) - total, 0.0) * 0.5
	for j in n:
		# j = 0 is the bottom pip
		var y := y_top + total - (j + 1) * h + gap
		var lit := j < int(s.val)
		var ghost := (not lit) and j < int(s.val) + int(s.ghost)
		var pts := P([x, y, x + 10, y, x + 8, y + body, x - 2, y + body])
		solid(pts, _pip_col(s, lit, ghost))
		if ghost:
			outline(pts, dimc(s.col, 0.7))
		elif lit and (s.flash or s.spent or s.blink):
			outline(pts, INK)

func _ring(cx: float, cy: float, s: Dictionary, r_out: float, r_in: float) -> void:
	# Segmented ring, 12 ticks starting at 7-o'clock going clockwise (fuel-gauge direction).
	var n := 12
	var on := int(round(float(s.val) / float(s.pips) * n)) if s.pips > 0 else 0
	var gh := int(round(float(s.ghost) / float(s.pips) * n)) if s.pips > 0 else 0
	var a0 := deg_to_rad(130.0)  # 7-ish o'clock if 0 is 3 o'clock... Godot: 0 is east, clockwise is positive? atan2 style: 0 is east, CCW is positive.
	# We want start at lower-left (220°) going clockwise to lower-right (about 320°+wrap to 140°).
	# Clockwise in Godot 2D (Y down) is positive angle. Start at 130°? Let's start at 210° (lower left) and sweep 300° clockwise = +300°.
	var start := deg_to_rad(210.0)
	var sweep := deg_to_rad(300.0)
	# dark track first
	_ring_track(cx, cy, r_out, r_in, start, sweep, Color8(28, 30, 40))
	for j in n:
		var t0 := start + sweep * (j / float(n))
		var t1 := start + sweep * ((j + 1) / float(n)) - deg_to_rad(4.0)  # 4° gap
		var lit := j < on
		var ghost := (not lit) and j < on + gh
		_ring_seg(cx, cy, r_out, r_in, t0, t1, _pip_col(s, lit, ghost))
	# inner ink ring so the icon sits in a crisp well
	_ring_track(cx, cy, r_in, r_in - 1.5, 0.0, TAU, INK_I)

func _ring_track(cx: float, cy: float, r0: float, r1: float, a0: float, sweep: float, col: Color) -> void:
	var n := 24
	for i in n:
		var t0 := a0 + sweep * (i / float(n))
		var t1 := a0 + sweep * ((i + 1) / float(n))
		_ring_seg(cx, cy, r0, r1, t0, t1, col)

func _ring_seg(cx: float, cy: float, r0: float, r1: float, a0: float, a1: float, col: Color) -> void:
	var p0 := Vector2(cx + cos(a0) * r0, cy + sin(a0) * r0)
	var p1 := Vector2(cx + cos(a1) * r0, cy + sin(a1) * r0)
	var p2 := Vector2(cx + cos(a1) * r1, cy + sin(a1) * r1)
	var p3 := Vector2(cx + cos(a0) * r1, cy + sin(a0) * r1)
	solid(PackedVector2Array([p0, p1, p2, p3]), col)

# ─────────────────────────────────────────────────────────────────────────────
# Icons — chunky 1px silhouettes, drawn in the stat colour with an ink outline.
# Coordinates are relative to a box centred on (cx, cy).
# ─────────────────────────────────────────────────────────────────────────────
func _icon_at(cx: float, cy: float, s: Dictionary, r: float) -> void:
	var col: Color = s.col
	if s.empty:
		col = dimc(s.col, 0.45)
	match String(s.key):
		"fuel":
			_icon_pump(cx, cy, r, col)
		"brakes":
			_icon_wheel(cx, cy, r, col, s.empty)
		_:
			_icon_shock(cx, cy, r, col)
	if s.empty:
		# Slash through the icon.
		draw_line(Vector2(cx - r + 1, cy + r - 2), Vector2(cx + r - 1, cy - r + 2), Color8(232, 40, 44), 2.0)
		draw_line(Vector2(cx - r + 1, cy + r - 2), Vector2(cx + r - 1, cy - r + 2), INK_I, 1.0)

func _icon_pump(cx: float, cy: float, r: float, col: Color) -> void:
	# Classic chunky gas pump: body, window, base, hose and nozzle.
	var x := cx - 5.0
	var y := cy - 9.0
	# body
	var body := P([x, y + 3, x + 10, y + 3, x + 10, y + 16, x, y + 16])
	solid(body, col)
	outline(body, INK_I)
	# top cap
	var cap := P([x - 1, y, x + 11, y, x + 11, y + 3, x - 1, y + 3])
	solid(cap, col)
	outline(cap, INK_I)
	# window
	rect(x + 2, y + 5, 6, 4, INK_I)
	# a little highlight in the window
	rect(x + 3, y + 6, 2, 2, Color(col, 0.85))
	# base
	var base := P([x - 2, y + 16, x + 12, y + 16, x + 12, y + 19, x - 2, y + 19])
	solid(base, dimc(col, 0.75))
	outline(base, INK_I)
	# hose: out of the right side, down, then a nozzle
	var hx := x + 10
	var hy := y + 8
	draw_line(Vector2(hx, hy), Vector2(hx + 4, hy), INK_I, 3.0)
	draw_line(Vector2(hx, hy), Vector2(hx + 4, hy), col, 2.0)
	draw_line(Vector2(hx + 4, hy), Vector2(hx + 4, y + 17), INK_I, 3.0)
	draw_line(Vector2(hx + 4, hy), Vector2(hx + 4, y + 17), col, 2.0)
	# nozzle
	var noz := P([hx + 2, y + 16, hx + 7, y + 16, hx + 7, y + 19, hx + 1, y + 19])
	solid(noz, col)
	outline(noz, INK_I)

func _icon_wheel(cx: float, cy: float, r: float, col: Color, empty: bool) -> void:
	# Wheel package: tyre, a clearly visible steel rotor behind the spokes, caliper
	# in the 3-o'clock spoke gap, rim, 5 spokes, hub. Drawn back-to-front.
	var rt: float = r            # tyre outer
	var ri: float = r - 2.4      # tyre inner / rim outer
	var rr: float = r - 3.4      # rim inner / rotor outer
	var rh: float = 2.2          # hub
	# Steel rotor, slightly warm so it still belongs with the EN red, but light enough
	# to read through the spoke gaps (the earlier dim-red disc looked like a hole).
	var rotor := Color8(186, 168, 162)
	var rotor_d := Color8(132, 108, 106)
	# 1. Tyre
	_ring_track(cx, cy, rt, ri, 0.0, TAU, TYRE)
	_ring_track(cx, cy, rt, rt - 1.0, 0.0, TAU, dimc(col, 0.7 if not empty else 0.4))
	# 2. Rotor disc, plus two grooves and a few slots so it reads as a brake disc
	_disc(cx, cy, rr, rotor)
	_ring_track(cx, cy, rr - 0.8, rr - 1.6, 0.0, TAU, rotor_d)
	_ring_track(cx, cy, rr * 0.58, rr * 0.58 - 0.8, 0.0, TAU, rotor_d)
	for k in 6:
		var sa := deg_to_rad(18.0 + k * 60.0)  # slots sit in the spoke gaps, not under a spoke
		var p0 := Vector2(cx + cos(sa) * (rh + 1.4), cy + sin(sa) * (rh + 1.4))
		var p1 := Vector2(cx + cos(sa) * (rr - 1.8), cy + sin(sa) * (rr - 1.8))
		draw_line(p0, p1, rotor_d, 1.0)
	# a 1 px highlight on the upper-left of the rotor so the disc has a surface
	var ha := deg_to_rad(200.0)
	var hb := deg_to_rad(280.0)
	_ring_seg(cx, cy, rr - 0.2, rr - 1.0, ha, hb, Color8(220, 210, 205))
	# 3. Caliper at 3 o'clock, before the spokes, so it shows through the gap
	_caliper(cx, cy, ri, rt, col)
	# 4. Rim ring
	_ring_track(cx, cy, ri, rr, 0.0, TAU, RIM)
	# 5. Five slightly slimmer spokes, gap centred at 0° (over the caliper)
	for i in 5:
		var a := deg_to_rad(36.0 + i * 72.0)
		_spoke(cx, cy, a, rh + 0.4, ri - 0.3, 1.15, 1.7, RIM)
	# 6. Hub
	_disc(cx, cy, rh, HUB)
	_disc(cx, cy, rh - 1.0, RIM_D)
	_disc(cx, cy, 0.7, col)
	# 7. Tyre outline
	_ring_track(cx, cy, rt + 0.6, rt, 0.0, TAU, INK_I)

func _caliper(cx: float, cy: float, r_rim: float, r_tyre: float, col: Color) -> void:
	# Chunky 2-piston caliper at 3 o'clock. Body sits just outside the rotor, pads pinch onto it.
	var mid := Color(minf(col.r * 1.05, 1), minf(col.g * 0.85, 1), minf(col.b * 0.85, 1))
	var bright := Color(minf(col.r * 1.2, 1), minf(col.g * 0.95 + 0.05, 1), minf(col.b * 0.95 + 0.05, 1))
	var pad := P([
		cx + r_rim - 3.5, cy - 2.4,
		cx + r_rim + 0.4, cy - 2.4,
		cx + r_rim + 0.4, cy + 2.4,
		cx + r_rim - 3.5, cy + 2.4,
	])
	solid(pad, dimc(col, 0.7))
	var body := P([
		cx + r_rim - 0.2, cy - 4.0,
		cx + r_tyre + 1.4, cy - 4.0,
		cx + r_tyre + 2.2, cy - 2.2,
		cx + r_tyre + 2.2, cy + 2.2,
		cx + r_tyre + 1.4, cy + 4.0,
		cx + r_rim - 0.2, cy + 4.0,
	])
	solid(body, mid)
	outline(body, INK_I)
	_disc(cx + r_tyre - 0.4, cy - 1.7, 1.45, bright)
	_disc(cx + r_tyre - 0.4, cy + 1.7, 1.45, bright)
	rect(cx + r_tyre - 1.0, cy - 0.5, 2.0, 1.0, dimc(col, 0.55))

func _spoke(cx: float, cy: float, a: float, r0: float, r1: float, w0: float, w1: float, col: Color) -> void:
	var d := Vector2(cos(a), sin(a))
	var n := Vector2(-d.y, d.x)
	var p0 := Vector2(cx, cy) + d * r0 - n * w0
	var p1 := Vector2(cx, cy) + d * r0 + n * w0
	var p2 := Vector2(cx, cy) + d * r1 + n * w1
	var p3 := Vector2(cx, cy) + d * r1 - n * w1
	solid(PackedVector2Array([p0, p1, p2, p3]), col)
	outline(PackedVector2Array([p0, p1, p2, p3]), INK_I)

func _disc(cx: float, cy: float, r: float, col: Color, n := 16) -> void:
	if r <= 0.6:
		rect(roundf(cx - 0.5), roundf(cy - 0.5), 1, 1, col)
		return
	var pts := PackedVector2Array()
	for i in n:
		var a := TAU * i / n - PI / 2.0
		pts.append(Vector2(cx + cos(a) * r, cy + sin(a) * r))
	solid(pts, col)

func _icon_shock(cx: float, cy: float, r: float, col: Color) -> void:
	# Clean shock: upper eye, short body/can, visible shaft, three separated coil loops, lower eye.
	var dark := dimc(col, 0.7)
	# upper eye
	_ring_track(cx, cy - r + 1.8, 2.2, 1.0, 0.0, TAU, col)
	_ring_track(cx, cy - r + 1.8, 2.4, 2.2, 0.0, TAU, INK_I)
	# body / can
	var can_y0 := cy - r + 4.0
	var can_y1 := cy - 0.4
	var can := P([cx - 3.5, can_y0, cx + 3.5, can_y0, cx + 3.5, can_y1, cx - 3.5, can_y1])
	solid(can, col)
	outline(can, INK_I)
	rect(cx - 3.5, can_y1 - 2.0, 7, 1.2, dark)
	# shaft behind the coils
	var shaft_y1 := cy + r - 2.6
	rect(cx - 0.8, can_y1, 1.6, shaft_y1 - can_y1, RIM)
	# three clearly separated coil loops (diamond rings, not a filled scribble)
	var coil0 := can_y1 + 0.4
	for i in 3:
		var y := coil0 + i * 3.4
		var coil := P([cx, y, cx + 4.2, y + 1.6, cx, y + 3.2, cx - 4.2, y + 1.6])
		# fill faintly so the shaft peeks through, then a hard outline
		solid(coil, dimc(col, 0.85))
		outline(coil, INK_I)
		# inner diamond cut so it reads as a coil, not a solid blob
		var inner := P([cx, y + 0.8, cx + 2.2, y + 1.6, cx, y + 2.4, cx - 2.2, y + 1.6])
		solid(inner, Color8(18, 20, 28))
		# redraw the shaft through the hole
		rect(cx - 0.8, y + 0.8, 1.6, 1.6, RIM)
	# lower cap
	var cap_y := cy + r - 2.6
	var cap := P([cx - 3.0, cap_y, cx + 3.0, cap_y, cx + 3.0, cap_y + 1.4, cx - 3.0, cap_y + 1.4])
	solid(cap, dark)
	outline(cap, INK_I)
	# lower eye
	_ring_track(cx, cy + r - 0.6, 2.0, 0.9, 0.0, TAU, col)
	_ring_track(cx, cy + r - 0.6, 2.2, 2.0, 0.0, TAU, INK_I)
