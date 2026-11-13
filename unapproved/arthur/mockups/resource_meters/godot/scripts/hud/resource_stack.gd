## Unapproved concept: three stacked resource meters on the left of the race HUD.
## Fuel (POW) / Brakes (EN) / Suspension (HAN). Purely visual; costs and empty-state
## rules are not decided. Extends the line-preview HUD plate language (grain, bevel,
## pixel-hard type, slanted pips like LINE LOCK).
##
## Variants:
##   A — slim stack, icon + vertical segmented bar + label (top left)
##   B — horizontal segmented bars to the right of each icon (same pip language as LINE LOCK)
##   C — one combined plate with a segmented ring around each icon and a short pip track
##   D — one wide plate at the BOTTOM LEFT (mirrors PLAN THE LINE). Icons in a left
##       column; long thin continuous fill bars in framed troughs, no pips. Austin
##       2026-11-13: "the bars are more 'freeform' when depleting vs discrete ticks"
##       and "it should be in the bottom left."
##   E — International Rally-style bottom HUD band (Austin 2026-11-13: that GBC
##       shot "shows a better HUD design"). HEAT / BRAKES / SUSP compact on the
##       left (continuous troughs, not segments), LINE LOCK + corner map in the
##       middle, PLAN THE LINE chips on the right. Top stays minimal: rear view,
##       a tighter tie-gap, and a floating turn sign (first reference). POW fuel
##       row becomes HEAT with a coolant-temperature icon (headroom left; OVERHEAT
##       / LIMP tags). E1 = everything in the bottom band. E2 = bottom band + a
##       slim top strip for LINE LOCK and the corner name if the band is tight.
##   E3 — from E1 (Austin 2026-11-13: "if the turn indicator exists, why does
##       the one exist in the middle of the bottom hud?"). No corner map in the
##       band. HAIRPIN L sits under the floating turn sign (hairpin-left U-turn
##       arrow). E/A/X camera stops sit next to the PLAN THE LINE rows. Middle
##       of the band is LINE LOCK only, with room and bigger timer digits.
##       Chunky Archivo Black / Nimbus Sans Bold type at readable sizes. Flat.
##   E3B — same layout as E3, with heat / load meters that fill as load builds
##       and drain as they recover (Austin, 2026-11-13). POW = engine heat,
##       EN = brake and tyre heat, HAN = suspension load. LIMIT tick at ~80%,
##       RELEASE notch at ~55% (placeholder numbers, not approved). Between
##       LIMIT and full is OVERRUN (still selectable, hits less). Full is
##       LOCKED until the fill cools past RELEASE (hysteresis). Concept only;
##       not in the sim. EN and HAN band icons were reverted at Austin's
##       request (2026-11-13) to the E3 wheel+caliper and shock from 7c69bf6.
##       POW coolant is unchanged.
##
## EN icon: a wheel (tyre + rim + spokes) with the brake rotor and caliper
## visible through the spoke gaps (restored from E3). HAN icon: the E3 shock
## absorber (upper eye, can, coils, lower eye).
@tool
extends "res://scripts/hud/hud_panel.gd"

## Optional standalone icon render (icon_export.gd). When set, _draw skips the HUD.
var icon_job: Dictionary = {}

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
const ITEMS_E := [
	{"key": "fuel", "label": "HEAT", "stat": "POW"},
	{"key": "brakes", "label": "BRAKES", "stat": "EN"},
	{"key": "susp", "label": "SUSP", "stat": "HAN"},
]
# Hot tint used only on a warning HEAT bar (overheat). The POW chip stays green.
const COL_HOT := Color8(255, 112, 28)

func _draw() -> void:
	if not icon_job.is_empty():
		_paint_icon_job()
		return
	super._draw()


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
		"D":
			_paint_d(rs)
		"E", "E1":
			_paint_e(rs, false)
		"E2":
			_paint_e(rs, true)
		"E3":
			_paint_e3(rs)
		"E3B":
			_paint_e3b(rs)
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
# Variant D: one wide framed plate at the BOTTOM LEFT, mirroring PLAN THE LINE.
# Icons in a column on the left; long thin continuous bars in framed troughs
# (no pips). The fill length is freeform — it can sit at any width, and the
# depleting edge is a slight slant rather than a tick-aligned cut.
# ─────────────────────────────────────────────────────────────────────────────
func _paint_d(rs: Dictionary) -> void:
	# Mirror PLAN THE LINE (424, 372, 636, 479). Left margin matches LINE LOCK.
	# Right edge stops short of the chase MX5 (left of the car is about x=342).
	var x0 := 14.0
	var y0 := 372.0
	var x1 := 316.0
	var y1 := 479.0
	var body := cut_panel(x0, y0, x1, y1, 8.0)
	semi(body, PANEL)
	plate_finish(body, x0, y0, x1, y1)
	outline(body, EDGE)
	outline(cut_panel(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 7.0), EDGE_D)
	for i in ITEMS.size():
		var s: Dictionary = _item_state(rs, ITEMS[i])
		var y := y0 + 8.0 + i * 33.0
		if s.warn or s.blink or s.empty or s.flash or s.spent:
			var a := 0.14 if (s.blink or s.empty or s.flash) else 0.08
			var wash: Color = L_AMBER if (s.blink or s.warn) else (Color8(232, 40, 44) if s.empty else s.col)
			semi(P([x0 + 5, y - 1, x1 - 5, y - 1, x1 - 7, y + 31, x0 + 3, y + 31]), wash, a)
		# Icon column, slightly larger than A/B/C; shock is drawn bolder at this size.
		var icx := x0 + 18.0
		var icy := y + 16.0
		_icon_at(icx, icy, s, 14.0 if s.key == "susp" else 12.0)
		# Label + stat + badge sit above the trough, so the bar can span the rest of the plate.
		var lx := x0 + 34.0
		t2(lx, y + 1, s.label, 11, _lab_col(s), true, "l", true, false, true)
		var tw := _stat_tag(lx + sw(s.label, 11, true, true) + 5, y + 1, s)
		_badge_at(lx + sw(s.label, 11, true, true) + 5 + tw + 4, y + 1, s, "l")
		# Long thin trough: from just after the icon to the right inner edge.
		_trough(x0 + 34.0, y + 16.0, (x1 - 10.0) - (x0 + 34.0), 9.0, s)


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
	if b == "OVERHEAT":
		col = COL_HOT
	var pts := P([x0 + 2, y, x0 + w, y, x0 + w - 2, y + 10, x0, y + 10])
	solid(pts, col)
	outline(pts, INK)
	var tc: Color = INK if b == "LOW" or b == "RECOVER" or b == "OVERHEAT" else Color.WHITE
	t2(x0 + w / 2.0, y + 5.0, b, sz, tc, true, "m", false, true)

func _pip_col(s: Dictionary, lit: bool, ghost: bool) -> Color:
	if lit:
		if s.flash:
			return Color(minf(s.col.r * 1.15 + 0.15, 1), minf(s.col.g * 1.15 + 0.15, 1), minf(s.col.b * 1.15 + 0.1, 1))
		if s.blink:
			if bool(s.get("hot", false)):
				return COL_HOT
			return L_AMBER if s.key != "susp" else s.col
		return s.col
	if ghost:
		return dimc(s.col, 0.55)
	return L_SEG_OFF

func _trough(x: float, y: float, w: float, h: float, s: Dictionary) -> void:
	# Framed well. Pixel-hard, no AA, no soft gradient. The fill length is continuous
	# (any width, not snapped to ticks). A slanted leading edge reads as freeform
	# depletion rather than a chopped rectangle or a pip. A full bar sits flush.
	var well := P([x, y, x + w, y, x + w, y + h, x, y + h])
	solid(well, Color8(10, 12, 20))
	draw_line(Vector2(x, y), Vector2(x + w, y), Color8(0, 0, 0, 200), 1.0)
	draw_line(Vector2(x, y), Vector2(x, y + h), Color8(0, 0, 0, 180), 1.0)
	draw_line(Vector2(x, y + h), Vector2(x + w, y + h), Color8(70, 82, 110, 140), 1.0)
	draw_line(Vector2(x + w, y), Vector2(x + w, y + h), Color8(70, 82, 110, 120), 1.0)
	outline(well, INK)
	var pips: float = maxf(float(s.pips), 1.0)
	var inner := w - 2.0
	var fill_w := inner * (float(s.val) / pips)
	var ghost_w := inner * (float(s.val + s.ghost) / pips)
	var x0 := x + 1.0
	var y0 := y + 1.0
	var y1 := y + h - 1.0
	# Draw the spent (ghost) wash first, full height, so the bright fill can sit on top
	# with no gap under a slanted nose.
	if ghost_w > fill_w + 0.5:
		_trough_fill(x0, y0, y1, ghost_w, inner, dimc(s.col, 0.45), false)
	if fill_w >= 1.0:
		var col := _pip_col(s, true, false)
		var is_full := fill_w >= inner - 0.51
		_trough_fill(x0, y0, y1, fill_w, inner, col, not is_full)
		# Hard 1 px highlight on the top of the fill, no soft shine.
		var hx1 := x0 + (inner if is_full else fill_w) - 1.0
		draw_line(Vector2(x0 + 1, y0 + 1), Vector2(maxf(hx1, x0 + 2), y0 + 1), Color(1, 1, 1, 0.22), 1.0)
		if not is_full and (s.flash or s.spent or s.blink):
			pass  # outline is already on the fill polygon inside _trough_fill when wanted
		if s.flash or s.spent or s.blink:
			# re-stroke the leading edge so a spent/flash bar stays sharp
			var nose := 0.0 if is_full else (3.0 if fill_w > 6.0 else maxf(fill_w * 0.4, 1.0))
			draw_line(Vector2(x0 + fill_w, y0), Vector2(x0 + fill_w - nose, y1), INK, 1.0)
	elif s.empty:
		draw_line(Vector2(x0 + 2, y + h / 2.0), Vector2(x + w - 3, y + h / 2.0), Color8(232, 40, 44, 120), 1.0)


func _trough_fill(x0: float, y0: float, y1: float, fill_w: float, inner: float, col: Color, slant: bool) -> void:
	var fx1 := x0 + minf(fill_w, inner)
	var pts: PackedVector2Array
	if slant and fill_w > 2.0:
		var nose := 3.0 if fill_w > 6.0 else maxf(fill_w * 0.4, 1.0)
		pts = P([x0, y0, fx1, y0, fx1 - nose, y1, x0, y1])
	else:
		pts = P([x0, y0, fx1, y0, fx1, y1, x0, y1])
	solid(pts, col)


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
			if bool(s.get("heat", false)):
				_icon_coolant(cx, cy, r, col)
			else:
				_icon_pump(cx, cy, r, col)
		"brakes":
			_icon_wheel(cx, cy, r, col, s.empty)
		_:
			_icon_shock(cx, cy, r, col)
	if s.empty and not bool(s.get("no_slash", false)):
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
	# Thin 5-spoke alloy (Austin Enkei-style ref): five slim straight spokes,
	# thin rim, small hub with 5 lug holes and a dark centre cap, big open
	# windows. Steel rotor behind the spokes. Caliper inside the rim, visible
	# through the 3-o'clock window. No logos. Drawn back-to-front.
	var rt: float = r            # tyre outer
	var tyre_w := 2.2
	var rim_w := 0.75
	var ri: float = r - tyre_w   # tyre inner / rim outer
	var rr: float = ri - rim_w   # rim inner / rotor outer
	var rh: float = maxf(2.5, r * 0.26)  # small hub, room for 5 lugs + cap
	# Steel rotor, slightly warm so it still belongs with the EN red, but light
	# enough to read through the open windows.
	var rotor := Color8(186, 168, 162)
	var rotor_d := Color8(132, 108, 106)
	# 1. Tyre
	_ring_track(cx, cy, rt, ri, 0.0, TAU, TYRE)
	_ring_track(cx, cy, rt, rt - 1.0, 0.0, TAU, dimc(col, 0.7 if not empty else 0.4))
	# 2. Rotor disc, grooves and a few slots so it reads as a brake disc
	_disc(cx, cy, rr, rotor)
	_ring_track(cx, cy, rr - 0.8, rr - 1.6, 0.0, TAU, rotor_d)
	_ring_track(cx, cy, rr * 0.58, rr * 0.58 - 0.8, 0.0, TAU, rotor_d)
	for k in 6:
		var sa := deg_to_rad(18.0 + k * 60.0)
		var p0 := Vector2(cx + cos(sa) * (rh + 1.4), cy + sin(sa) * (rh + 1.4))
		var p1 := Vector2(cx + cos(sa) * (rr - 1.8), cy + sin(sa) * (rr - 1.8))
		draw_line(p0, p1, rotor_d, 1.0)
	var ha := deg_to_rad(200.0)
	var hb := deg_to_rad(280.0)
	_ring_seg(cx, cy, rr - 0.2, rr - 1.0, ha, hb, Color8(220, 210, 205))
	# 3. Caliper in the window nearest 3 o'clock, entirely inside the rim.
	# One spoke points straight up, so no spoke sits on the horizontal;
	# that puts a window centre at 18° (just below 3 o'clock).
	var win0 := deg_to_rad(18.0)
	_caliper(cx, cy, rr, rh, col, win0)
	# 4. Thin rim ring
	_ring_track(cx, cy, ri, rr, 0.0, TAU, RIM)
	# 5. Five slim straight spokes in the rim's light tone, so the star reads
	# against the darker rotor at in-band size. Roots start under the hub.
	# One spoke at -90° (12 o'clock); no spoke is exactly horizontal.
	for i in 5:
		var a := deg_to_rad(-90.0 + float(i) * 72.0)
		_spoke(cx, cy, a, maxf(0.4, rh - 0.6), ri - 0.15, 0.70, 0.55, RIM)
	# 6. Light hub face (same tone as the rim/spokes) covers the spoke roots
	# so the centre stays clean. Dark centre cap and 5 dark lug holes. No logo.
	_disc(cx, cy, rh, RIM)
	var cap_r := maxf(1.0, rh * 0.40)
	var lug_r := (cap_r + rh) * 0.55
	_disc(cx, cy, cap_r, HUB)
	_disc(cx, cy, maxf(0.55, cap_r - 0.35), Color8(22, 20, 24))
	for i in 5:
		var la := win0 + deg_to_rad(float(i) * 72.0)  # sit in the windows, around the cap
		var lx := cx + cos(la) * lug_r
		var ly := cy + sin(la) * lug_r
		if r < 12.0:
			rect(roundf(lx - 0.5), roundf(ly - 0.5), 1, 1, INK_I)
		else:
			_disc(lx, ly, 0.7, INK_I, 8)
	# 7. Tyre outline
	_ring_track(cx, cy, rt + 0.6, rt, 0.0, TAU, INK_I)

func _rot_pts(pts: PackedVector2Array, origin: Vector2, ang: float) -> PackedVector2Array:
	if ang == 0.0:
		return pts
	var out := PackedVector2Array()
	for p in pts:
		out.append(origin + (p - origin).rotated(ang))
	return out

func _caliper(cx: float, cy: float, r_rotor: float, r_hub: float, col: Color, ang: float = 0.0) -> void:
	# Chunky 2-piston caliper, entirely inside the rim. Pads pinch the rotor;
	# the body stays in the wheel opening, visible in a spoke window. `ang`
	# rotates the caliper about the hub so it can sit in a window near 3 o'clock.
	var mid := Color(minf(col.r * 1.05, 1), minf(col.g * 0.85, 1), minf(col.b * 0.85, 1))
	var bright := Color(minf(col.r * 1.2, 1), minf(col.g * 0.95 + 0.05, 1), minf(col.b * 0.95 + 0.05, 1))
	var x_out := cx + r_rotor - 0.2  # just inside the rim inner / rotor outer
	var x_in := cx + r_hub + 0.7
	if x_out - x_in < 3.6:
		x_in = x_out - 3.6
	# A little larger than the previous in-rim caliper — the 5-spoke windows
	# are wide enough for it to read at in-band size, still inside the rim.
	var y_out := maxf(4.8, (x_out - cx) * 0.70)
	var y_in := y_out * 0.68
	var origin := Vector2(cx, cy)
	var pad := _rot_pts(P([
		x_out - 3.0, cy - 2.4,
		x_out - 0.1, cy - 2.4,
		x_out - 0.1, cy + 2.4,
		x_out - 3.0, cy + 2.4,
	]), origin, ang)
	solid(pad, dimc(col, 0.7))
	var body := _rot_pts(P([
		x_out, cy - y_out,
		x_out, cy + y_out,
		x_in, cy + y_in,
		x_in, cy - y_in,
	]), origin, ang)
	solid(body, mid)
	outline(body, INK_I)
	# Two pistons stacked inside the body, not past the rim.
	var pr := 1.25 if (x_out - x_in) >= 3.8 else 1.1
	var px := x_out - pr - 0.35
	if px - pr < x_in + 0.2:
		px = x_in + pr + 0.2
	var py := 1.55
	var p_up := origin + (Vector2(px, cy - py) - origin).rotated(ang)
	var p_dn := origin + (Vector2(px, cy + py) - origin).rotated(ang)
	_disc(p_up.x, p_up.y, pr, bright)
	_disc(p_dn.x, p_dn.y, pr, bright)
	var bar := _rot_pts(P([
		px - 0.7, cy - 0.4,
		px + 0.7, cy - 0.4,
		px + 0.7, cy + 0.4,
		px - 0.7, cy + 0.4,
	]), origin, ang)
	solid(bar, dimc(col, 0.55))

func _ring_n(cx: float, cy: float, r0: float, r1: float, a0: float, sweep: float, col: Color, n: int) -> void:
	var segs := maxi(n, 8)
	for i in segs:
		var t0 := a0 + sweep * (float(i) / float(segs))
		var t1 := a0 + sweep * (float(i + 1) / float(segs))
		_ring_seg(cx, cy, r0, r1, t0, t1, col)


func _spoke(cx: float, cy: float, a: float, r0: float, r1: float, w0: float, w1: float, col: Color) -> void:
	# Outline first, then the light fill, so a thin spoke keeps a light body at
	# in-band size instead of being swallowed by the 1 px ink stroke.
	var d := Vector2(cos(a), sin(a))
	var n := Vector2(-d.y, d.x)
	var p0 := Vector2(cx, cy) + d * r0 - n * w0
	var p1 := Vector2(cx, cy) + d * r0 + n * w0
	var p2 := Vector2(cx, cy) + d * r1 + n * w1
	var p3 := Vector2(cx, cy) + d * r1 - n * w1
	var pts := PackedVector2Array([p0, p1, p2, p3])
	outline(pts, INK_I)
	solid(pts, col)

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
	# Shock / coilover. Variant D (r >= 13) keeps the taller three-coil can.
	# The compact path (E3 / E3B band, r ~ 10–11) is squatter — fewer coil
	# turns, compact eyelets — so it stays inside its row and does not crowd
	# the meter, chip, or the rows above and below.
	var bold := r >= 13.0
	var dark := dimc(col, 0.7)
	if bold:
		_icon_shock_tall(cx, cy, r, col, dark)
		return
	# Total height capped to sit inside an E3B row (~20.3 design units) with
	# a little air under the EN wheel and above the panel edge.
	var h: float = minf(16.0, r * 1.45)
	var half := h * 0.5
	var eye_r := 1.5
	var eye_in := 0.7
	var can_w := 3.4
	var coil_w := 4.2
	var coil_step := 2.5
	var coil_n := 2
	var cap_h := 1.15
	var cap_w := 2.8
	var shw := 1.5
	var uy := cy - half + eye_r + 0.2
	var ly := cy + half - eye_r - 0.2
	# upper eye
	_ring_track(cx, uy, eye_r, eye_in, 0.0, TAU, col)
	_ring_track(cx, uy, eye_r + 0.25, eye_r, 0.0, TAU, INK_I)
	# short body / can — leave room for two distinct coils above the lower cap
	var can_y0 := uy + eye_r + 0.25
	var can_y1 := can_y0 + 3.8
	var can := P([cx - can_w, can_y0, cx + can_w, can_y0, cx + can_w, can_y1, cx - can_w, can_y1])
	solid(can, col)
	outline(can, INK_I)
	rect(cx - can_w, can_y0 + 1.2, can_w * 2.0, 0.85, dark)
	rect(cx - can_w, can_y1 - 1.3, can_w * 2.0, 0.9, dark)
	# shaft behind the coils, down to the lower cap (cap sits on the lower eye)
	var shaft_y1 := ly - eye_r - 0.15
	rect(cx - shw / 2.0, can_y1, shw, maxf(shaft_y1 - can_y1, 1.0), RIM)
	outline(P([cx - shw / 2.0, can_y1, cx + shw / 2.0, can_y1, cx + shw / 2.0, shaft_y1, cx - shw / 2.0, shaft_y1]), INK_I)
	# two compact coil loops, shaft visible through the hole, clear of the cap
	var coil0 := can_y1 + 0.2
	for i in coil_n:
		var y := coil0 + i * coil_step
		var coil := P([cx, y, cx + coil_w, y + coil_step * 0.5, cx, y + coil_step * 0.90, cx - coil_w, y + coil_step * 0.5])
		solid(coil, col)
		outline(coil, INK_I)
		var iw := coil_w * 0.40
		var inner := P([cx, y + coil_step * 0.30, cx + iw, y + coil_step * 0.5, cx, y + coil_step * 0.68, cx - iw, y + coil_step * 0.5])
		solid(inner, Color8(18, 20, 28))
		rect(cx - shw / 2.0, y + coil_step * 0.30, shw, coil_step * 0.38, RIM)
	# lower cap
	var cap := P([cx - cap_w, shaft_y1, cx + cap_w, shaft_y1, cx + cap_w, shaft_y1 + cap_h, cx - cap_w, shaft_y1 + cap_h])
	solid(cap, dark)
	outline(cap, INK_I)
	# lower eye
	_ring_track(cx, ly, eye_r - 0.1, eye_in - 0.05, 0.0, TAU, col)
	_ring_track(cx, ly, eye_r + 0.2, eye_r - 0.1, 0.0, TAU, INK_I)


func _icon_shock_tall(cx: float, cy: float, r: float, col: Color, dark: Color) -> void:
	# Original taller three-coil can, used at r >= 13 (variant D).
	var eye_r := 2.6
	var eye_in := 1.2
	var can_w := 5.5
	var coil_w := 6.0
	var coil_step := 3.6
	var coil_n := 3
	var uy := cy - r + eye_r
	_ring_track(cx, uy, eye_r, eye_in, 0.0, TAU, col)
	_ring_track(cx, uy, eye_r + 0.3, eye_r, 0.0, TAU, INK_I)
	var can_y0 := uy + eye_r + 0.4
	var can_h := 7.0
	var can_y1 := can_y0 + can_h
	var can := P([cx - can_w, can_y0, cx + can_w, can_y0, cx + can_w, can_y1, cx - can_w, can_y1])
	solid(can, col)
	outline(can, INK_I)
	rect(cx - can_w, can_y0 + 2.2, can_w * 2.0, 1.4, dark)
	rect(cx - can_w, can_y1 - 2.2, can_w * 2.0, 1.4, dark)
	draw_line(Vector2(cx - can_w + 1, can_y0 + 1), Vector2(cx - can_w + 1, can_y1 - 1), Color(1, 1, 1, 0.25), 1.0)
	var ly := cy + r - eye_r
	var cap_h := 1.8
	var shaft_y1 := ly - eye_r - 0.2
	var shw := 2.2
	rect(cx - shw / 2.0, can_y1, shw, maxf(shaft_y1 - can_y1, 1.0), RIM)
	outline(P([cx - shw / 2.0, can_y1, cx + shw / 2.0, can_y1, cx + shw / 2.0, shaft_y1, cx - shw / 2.0, shaft_y1]), INK_I)
	var coil0 := can_y1 + 0.3
	for i in coil_n:
		var y := coil0 + i * coil_step
		var coil := P([cx, y, cx + coil_w, y + coil_step * 0.5, cx, y + coil_step * 0.92, cx - coil_w, y + coil_step * 0.5])
		solid(coil, col)
		outline(coil, INK_I)
		var iw := coil_w * 0.42
		var inner := P([cx, y + coil_step * 0.28, cx + iw, y + coil_step * 0.5, cx, y + coil_step * 0.70, cx - iw, y + coil_step * 0.5])
		solid(inner, Color8(18, 20, 28))
		rect(cx - shw / 2.0, y + coil_step * 0.28, shw, coil_step * 0.42, RIM)
	var cap_w := 4.2
	var cap := P([cx - cap_w, shaft_y1, cx + cap_w, shaft_y1, cx + cap_w, shaft_y1 + cap_h, cx - cap_w, shaft_y1 + cap_h])
	solid(cap, dark)
	outline(cap, INK_I)
	_ring_track(cx, ly, eye_r - 0.15, eye_in - 0.1, 0.0, TAU, col)
	_ring_track(cx, ly, eye_r + 0.15, eye_r - 0.15, 0.0, TAU, INK_I)


func _item_state_e(rs: Dictionary, it: Dictionary) -> Dictionary:
	var s: Dictionary = _item_state(rs, it)
	if String(it.key) == "fuel":
		s["heat"] = true
		s["no_slash"] = true
		s["hot"] = bool(s.warn) or bool(s.blink) or String(s.badge) == "OVERHEAT"
	return s


func _flat_panel(x0: float, y0: float, x1: float, y1: float, border: Color = EDGE) -> void:
	# Hard rectangle. Solid fill, 2 px border (ink outside, edge inside). No grain, no bevel, no banding.
	var r := Rect2(x0, y0, x1 - x0, y1 - y0)
	draw_rect(r, PANEL, true)
	draw_rect(r, INK, false, 1.0)
	if x1 - x0 > 4.0 and y1 - y0 > 4.0:
		draw_rect(Rect2(x0 + 1.0, y0 + 1.0, x1 - x0 - 2.0, y1 - y0 - 2.0), border, false, 1.0)


func _vdiv(x: float, y0: float, y1: float) -> void:
	draw_line(Vector2(x, y0 + 5.0), Vector2(x, y1 - 5.0), EDGE_D, 1.0)


func _e_trough(x: float, y: float, w: float, h: float, s: Dictionary) -> void:
	# Flat well + flat fill. Same freeform slanted nose as D, but no highlight sheen and no well bevel.
	var well := Rect2(x, y, w, h)
	draw_rect(well, Color8(8, 10, 16), true)
	draw_rect(well, INK, false, 1.0)
	var pips: float = maxf(float(s.pips), 1.0)
	var inner := w - 2.0
	var fill_w := inner * (float(s.val) / pips)
	var ghost_w := inner * (float(s.val + int(s.get("ghost", 0))) / pips)
	var x0 := x + 1.0
	var y0 := y + 1.0
	var y1 := y + h - 1.0
	if ghost_w > fill_w + 0.5:
		_trough_fill(x0, y0, y1, ghost_w, inner, dimc(s.col, 0.45), false)
	if fill_w >= 1.0:
		var col := _pip_col(s, true, false)
		var is_full := fill_w >= inner - 0.51
		_trough_fill(x0, y0, y1, fill_w, inner, col, not is_full)
	# Empty HEAT is a dark trough + LIMP tag; no slash and no red midline.


func _paint_e(rs: Dictionary, e2: bool) -> void:
	_paint_e_gap()
	_paint_e_sign()
	var x0 := 8.0
	var y0 := 408.0
	var x1 := 632.0
	var y1 := 479.0
	_flat_panel(x0, y0, x1, y1)
	if e2:
		_paint_e_lock_strip()
		_paint_e_corner_strip()
		_paint_e_meters(rs, 12.0, y0, 248.0, y1)
		_vdiv(254.0, y0, y1)
		_paint_e_map(258.0, y0, 356.0, y1)
		_vdiv(362.0, y0, y1)
		_paint_e_plan(366.0, y0, x1 - 4.0, y1)
	else:
		_paint_e_meters(rs, 12.0, y0, 204.0, y1)
		_vdiv(209.0, y0, y1)
		_paint_e_lock(214.0, y0, 368.0, y1)
		_vdiv(373.0, y0, y1)
		_paint_e_plan(378.0, y0, x1 - 4.0, y1)


func _paint_e_meters(rs: Dictionary, x0: float, y0: float, x1: float, y1: float) -> void:
	var pad := 5.0
	var rh: float = ((y1 - y0) - pad * 2.0) / 3.0
	for i in ITEMS_E.size():
		var s: Dictionary = _item_state_e(rs, ITEMS_E[i])
		var y: float = y0 + pad + float(i) * rh
		var icy: float = y + rh * 0.5
		var r: float = 10.0 if String(s.key) == "susp" else 9.0
		_icon_at(x0 + 11.0, icy, s, r)
		var cx := x0 + 24.0
		var tw: float = _e_stat_tag(cx, icy - 5.0, s)
		var bx := cx + tw + 4.0
		var badge: String = String(s.badge)
		var badge_w := 0.0
		if badge != "":
			badge_w = sw(badge, 8, true, true) + 10.0
		var bx1: float = x1 - 3.0 - (badge_w + 2.0 if badge_w > 0.0 else 0.0)
		_e_trough(bx, icy - 4.0, maxf(bx1 - bx, 16.0), 8.0, s)
		if badge_w > 0.0:
			_e_badge_at(x1 - 3.0, icy - 5.0, s)


func _lock_state() -> Dictionary:
	var left := float(st.get("left", 4.8))
	var total := maxf(float(st.get("total", 12.0)), 0.001)
	var locked := String(st.get("phase", "")) == "TIMING"
	var frac := 1.0 if locked else clampf(left / total, 0.0, 1.0)
	return {
		"key": "lock",
		"col": L_AMBER,
		"val": int(round(frac * 120.0)),
		"pips": 120,
		"ghost": 0,
		"flash": false,
		"spent": false,
		"blink": false,
		"empty": false,
		"hot": false,
		"badge": "",
		"warn": false,
		"left": left,
		"locked": locked,
	}


func _paint_e_lock(x0: float, y0: float, x1: float, y1: float) -> void:
	var ls: Dictionary = _lock_state()
	t2(x0 + 4.0, y0 + 6.0, "LINE LOCK", 9, L_WHITE, true, "l", false, true)
	if bool(ls.locked):
		t2(x1 - 4.0, y0 + 6.0, "SET", 11, L_WHITE, true, "r", false, true)
	else:
		t2(x1 - 4.0, y0 + 5.0, "%04.1fs" % float(ls.left), 11, L_AMBER, true, "r", false, true)
	_e_trough(x0 + 4.0, y0 + 16.0, (x1 - 4.0) - (x0 + 4.0), 7.0, ls)
	# Map on the left, corner name + stacked stops on the right, under the timer bar.
	_paint_e_map_path(x0 + 4.0, y0 + 26.0, x0 + 68.0, y1 - 4.0)
	var lx := x0 + 72.0
	t2(lx, y0 + 30.0, String(st.plate.get("name", "HAIRPIN L")) if st.has("plate") else "HAIRPIN L", 9, L_WHITE, true, "l", false, true)
	if st.has("plate"):
		_paint_e_stops(lx, y0 + 42.0, st.plate, x1 - 4.0)


func _paint_e_lock_strip() -> void:
	# E2: slim top-left strip, clear of the rear view (221.5–418.5).
	var x0 := 12.0
	var y0 := 12.0
	var x1 := 208.0
	var y1 := 46.0
	_flat_panel(x0, y0, x1, y1)
	var ls: Dictionary = _lock_state()
	t2(x0 + 5.0, y0 + 5.0, "LINE LOCK", 9, L_WHITE, true, "l", false, true)
	if bool(ls.locked):
		t2(x1 - 5.0, y0 + 5.0, "SET", 11, L_WHITE, true, "r", false, true)
	else:
		t2(x1 - 5.0, y0 + 4.0, "%04.1fs" % float(ls.left), 11, L_AMBER, true, "r", false, true)
	_e_trough(x0 + 5.0, y0 + 18.0, (x1 - 5.0) - (x0 + 5.0), 8.0, ls)


func _paint_e_corner_strip() -> void:
	# E2: slim top-right strip with the corner name and E / A / X stops.
	var x0 := 430.0
	var y0 := 12.0
	var x1 := 632.0
	var y1 := 46.0
	_flat_panel(x0, y0, x1, y1)
	if not st.has("plate"):
		return
	var pl: Dictionary = st.plate
	t2(x0 + 6.0, y0 + 6.0, String(pl.get("name", "HAIRPIN L")), 11, L_WHITE, true, "l", false, true)
	_paint_e_stops(x0 + 6.0, y0 + 22.0, pl, x1 - 6.0)


func _paint_e_stops(x: float, y: float, pl: Dictionary, x_right: float = -1.0) -> void:
	var md: String = String(pl.get("mode", "VIEW"))
	var k: int = int(pl.get("stop", 0))
	var cur := -1
	var ndone := 0
	match md:
		"VIEW":
			cur = k
			ndone = k
		"LOCK":
			cur = 0
			ndone = 3
		"QTE", "PLAY":
			cur = k
			ndone = k
		_:
			cur = -1
			ndone = 3
	var lab := "PLAY" if md in ["PLAY", "DONE"] else ("QTE" if md == "QTE" else "VIEW")
	t2(x, y, lab, 8, L_DIM, true, "l", false, true)
	var phn: String = "RESULT" if md == "DONE" else (PHN[cur] if cur >= 0 and cur < PHN.size() else "")
	var px := x + 28.0
	t2(px, y - 1.0, phn, 9, L_AMBER, true, "l", false, true)
	if not (md in ["VIEW", "LOCK", "QTE"]):
		return
	# E / A / X sit after the phase name when there is room; otherwise they wrap to the next line.
	var ex := px + sw(phn, 9, true, true) + 10.0
	var letters_w := 14.0 * 3.0
	var ey := y
	if x_right > 0.0 and ex + letters_w > x_right:
		ex = x
		ey = y + 11.0
	var lt := ["E", "A", "X"]
	for i in 3:
		var on_cur := i == cur
		var dn := (md == "LOCK" and i > 0) or (md == "VIEW" and i < cur)
		t2(ex + float(i) * 14.0, ey, lt[i], 9, L_AMBER if on_cur else (L_WHITE if dn else L_DIMMER), true, "l", false, true)


func _paint_e_map(x0: float, y0: float, x1: float, y1: float) -> void:
	if not st.has("plate"):
		return
	var pl: Dictionary = st.plate
	t2(x0 + 4.0, y0 + 6.0, String(pl.get("name", "HAIRPIN L")), 9, L_WHITE, true, "l", false, true)
	_paint_e_stops(x0 + 4.0, y0 + 16.0, pl, x1 - 3.0)
	_paint_e_map_path(x0 + 4.0, y0 + 38.0, x1 - 3.0, y1 - 4.0)


func _paint_e_map_path(box_x0: float, box_y0: float, box_x1: float, box_y1: float) -> void:
	if not st.has("plate"):
		return
	if box_y1 - box_y0 < 16.0 or box_x1 - box_x0 < 16.0:
		return
	var pl: Dictionary = st.plate
	var ic: Dictionary = pl.get("icon", {})
	var pts: Array = ic.get("pts", [])
	if pts.is_empty():
		return
	var mn := Vector2(1e9, 1e9)
	var mx := Vector2(-1e9, -1e9)
	for v in pts:
		var p: Vector2 = v
		mn = Vector2(minf(mn.x, p.x), minf(mn.y, p.y))
		mx = Vector2(maxf(mx.x, p.x), maxf(mx.y, p.y))
	var sc := minf((box_x1 - box_x0) / maxf(mx.x - mn.x, 1.0), (box_y1 - box_y0) / maxf(mx.y - mn.y, 1.0))
	var ctr := (mn + mx) / 2.0
	var mid := Vector2((box_x0 + box_x1) * 0.5, (box_y0 + box_y1) * 0.5)
	var line := PackedVector2Array()
	for v in pts:
		var p: Vector2 = v
		line.append(mid + (p - ctr) * sc)
	if line.size() >= 2:
		draw_polyline(line, SOD, 2.0)
		var e: Vector2 = line[line.size() - 1]
		var dvec: Vector2 = (e - line[line.size() - 2]).normalized()
		var nv := Vector2(-dvec.y, dvec.x)
		solid(PackedVector2Array([e + dvec * 5.0, e - dvec * 3.0 + nv * 4.0, e - dvec * 3.0 - nv * 4.0]), SOD)
	var md: String = String(pl.get("mode", "VIEW"))
	var k: int = int(pl.get("stop", 0))
	var cur := -1
	var ndone := 0
	match md:
		"VIEW":
			cur = k
			ndone = k
		"LOCK":
			cur = 0
			ndone = 3
		"QTE", "PLAY":
			cur = k
			ndone = k
		_:
			cur = -1
			ndone = 3
	var stops: Array = ic.get("stops", [])
	for i in mini(3, stops.size()):
		var sp: Vector2 = stops[i]
		var c: Vector2 = mid + (sp - ctr) * sc
		var dn := i < ndone and i != cur
		var dia := P([c.x, c.y - 4, c.x + 4, c.y, c.x, c.y + 4, c.x - 4, c.y])
		solid(dia, L_AMBER if i == cur else (L_WHITE if dn else L_TODO))
		outline(dia, INK)


func _paint_e_plan(x0: float, y0: float, x1: float, y1: float) -> void:
	if not st.has("plan"):
		return
	var pl: Dictionary = st.plan
	t2(x0 + 4.0, y0 + 5.0, "PLAN THE LINE", 8, L_WHITE, true, "l", false, true)
	var ph: int = int(pl.get("phase", 0))
	var slots: Array = st.get("slots", [null, null, null])
	var lanes: Array = ["D", "S", "A"] if String(st.get("dir", "R")) == "L" else ORDER
	var row0 := y0 + 13.0
	var rh: float = maxf(((y1 - 2.0) - row0) / 3.0, 16.0)
	for i in 3:
		var ry: float = row0 + float(i) * rh
		var active: bool = (i == ph and ph < 3)
		var locked: bool = (i < ph) or (ph >= 3 and slots[i] != null)
		if active:
			# Flat active cue: a solid 2 px amber tick, no fade wash.
			draw_rect(Rect2(x0 + 3.0, ry + 1.0, 2.0, rh - 2.0), L_AMBER, true)
		var nx := x0 + (8.0 if active else 5.0)
		var ncol: Color = INK if active else (EDGE if locked else TODO)
		if active:
			# Name sits on a flat amber slab so it stays readable without a glow.
			var nw: float = sw(PH[i], 8, true, true) + 6.0
			draw_rect(Rect2(nx - 2.0, ry + 2.0, nw, 9.0), L_AMBER, true)
		t2(nx, ry + 6.0, PH[i], 8, ncol, true, "l", not active, true)
		if locked:
			check(nx + sw(PH[i], 8, true, true) + 3.0, ry + 3.0, CHECK_GREEN)
		var chosen := ""
		if locked and slots[i] != null:
			chosen = String(slots[i])
		elif locked and i == 0 and String(pl.get("entry", "")) != "":
			chosen = String(pl.entry)
		elif active:
			chosen = ORDER[int(pl.get("sel", 0))] if int(pl.get("sel", 0)) >= 0 else ""
		if active or locked:
			var lx := x0 + 52.0
			var w := 42.0
			if x1 - lx < w * 3.0 + 4.0:
				w = maxf(((x1 - 2.0) - lx) / 3.0, 32.0)
			for k in lanes:
				var lab: String = LANE[k]
				var note: String = NAME[k]
				var avail: Dictionary = pl.get("avail", {})
				var off: bool = active and int(avail.get(k, 1)) <= 0
				var selected: bool = (k == chosen and not off)
				var dim: bool = locked or off
				var cx := lx + w * 0.5
				if selected:
					draw_rect(Rect2(lx, ry + 1.0, w - 3.0, 8.0), AMBER if active else EDGE, true)
				t2(cx, ry + 5.0, lab, 8, INK if selected else (DIMT if dim else SUB), true, "m", not selected, true)
				if selected and locked:
					check(cx + sw(lab, 8, true, true) * 0.5 + 2.0, ry + 1.0, INK)
				_e_stat_box(cx, ry + 9.0, note, STANCE[k], selected, dim and not selected)
				lx += w
		else:
			t2(x0 + 54.0, ry + 8.0, "--  --  --", 10, TODO, false, "l", false, true)


func _e_stat_box(cx: float, y: float, label: String, col: Color, selected: bool, dim: bool) -> void:
	# Flat chip: hard rect, solid fill, 1 px ink border. No bevel, no slant, no sheen.
	var sz := 8
	var w := maxf(sw("POW", sz, true, true) + 6.0, 22.0)
	var h := 8.0
	var x0 := cx - w * 0.5
	var r := Rect2(x0, y, w, h)
	var fill: Color = col if selected else dimc(col, 0.45 if dim else 0.7)
	draw_rect(r, fill, true)
	draw_rect(r, INK, false, 1.0)
	var tc: Color = INK if col == STANCE.S else Color.WHITE
	if dim and not selected:
		tc = INK if col == STANCE.S else Color8(230, 230, 235)
	t2(cx, y + h * 0.5, label, sz, tc, true, "m", false, true)


func _paint_e_gap() -> void:
	# Compact flat tie-gap under REAR VIEW. Starts low enough that it does not
	# clip the REAR VIEW label (label at y=84, size 9).
	var lead := float(st.get("lead", 0.0))
	var x := 236.0
	var y := 98.0
	var w := 168.0
	var h := 24.0
	_flat_panel(x, y, x + w, y + h)
	var pos := "1st" if lead > 0.0 else ("2nd" if lead < 0.0 else "TIE")
	t2(x + 5.0, y + 4.0, "%s GAP" % pos, 8, L_WHITE, true, "l", false, true)
	var by := y + 14.0
	var bx0 := x + 36.0
	var bx1 := x + w - 28.0
	draw_rect(Rect2(bx0, by, bx1 - bx0, 5.0), Color8(8, 10, 16), true)
	draw_rect(Rect2(bx0, by, bx1 - bx0, 5.0), INK, false, 1.0)
	var mid := (bx0 + bx1) * 0.5
	var maxw := (bx1 - bx0) * 0.5 - 1.0
	var bw: float = minf(maxw, absf(lead) * maxw * 2.5)
	if lead > 0.0:
		draw_rect(Rect2(mid, by + 1.0, bw, 3.0), Color8(60, 200, 255), true)
	elif lead < 0.0:
		draw_rect(Rect2(mid - bw, by + 1.0, bw, 3.0), Color8(255, 60, 140), true)
	draw_rect(Rect2(mid, by, 1.0, 5.0), Color.WHITE, true)
	t2(x + 5.0, y + 16.0, "RIVAL", 7, SUB, true, "l", false, true)
	t2(x + w - 5.0, y + 16.0, "YOU", 7, SUB, true, "r", false, true)


func _paint_e_sign() -> void:
	# Floating upcoming-turn sign, first-reference language, drawn flat:
	# hard amber plate, 2 px ink border, flat black left arrow. No bevel, no gloss.
	var cx := 320.0
	var cy := 150.0
	var w := 34.0
	var h := 36.0
	var x0 := cx - w * 0.5
	var y0 := cy - h * 0.5
	var x1 := cx + w * 0.5
	var y1 := cy + h * 0.5
	draw_rect(Rect2(x0, y0, w, h), Color8(255, 184, 56), true)
	draw_rect(Rect2(x0, y0, w, h), INK, false, 1.0)
	draw_rect(Rect2(x0 + 1.0, y0 + 1.0, w - 2.0, h - 2.0), INK, false, 1.0)
	# 90-degree left arrow, chunky and flat.
	var shaft := P([cx - 2, cy - 4, cx + 6, cy - 4, cx + 6, cy + 13, cx - 2, cy + 13])
	solid(shaft, INK)
	var bar := P([cx - 10, cy - 4, cx + 6, cy - 4, cx + 6, cy + 3, cx - 10, cy + 3])
	solid(bar, INK)
	var head := P([cx - 16, cy - 0.5, cx - 5, cy - 11, cx - 5, cy + 10])
	solid(head, INK)


func _e_stat_tag(x: float, y: float, s: Dictionary) -> float:
	# Flat POW / EN / HAN chip: hard rect, solid fill, 1 px ink border. No slant, no bevel.
	var lab: String = s.stat
	var sz := 8
	var w := maxf(sw(lab, sz, true, true) + 8.0, 22.0)
	var h := 10.0
	var fill: Color = s.col if not s.empty else dimc(s.col, 0.35)
	if s.blink:
		fill = s.col
	draw_rect(Rect2(x, y, w, h), fill, true)
	draw_rect(Rect2(x, y, w, h), INK, false, 1.0)
	var tc: Color = INK if s.key == "susp" else Color.WHITE
	if s.empty and not s.blink:
		tc = Color8(230, 230, 235)
	t2(x + w / 2.0, y + h / 2.0, lab, sz, tc, true, "m", false, true)
	return w


func _e_badge_at(x: float, y: float, s: Dictionary) -> void:
	var b: String = s.badge
	if b == "":
		return
	var sz := 8
	var w := sw(b, sz, true, true) + 8.0
	var x0 := x - w
	var col: Color = L_AMBER if b == "LOW" else (s.col if b == "RECOVER" else Color8(232, 40, 44))
	if b == "OVERHEAT":
		col = COL_HOT
	draw_rect(Rect2(x0, y, w, 10.0), col, true)
	draw_rect(Rect2(x0, y, w, 10.0), INK, false, 1.0)
	var tc: Color = INK if b == "LOW" or b == "RECOVER" or b == "OVERHEAT" else Color.WHITE
	t2(x0 + w / 2.0, y + 5.0, b, sz, tc, true, "m", false, true)


func _icon_coolant(cx: float, cy: float, r: float, col: Color) -> void:
	# Standard dashboard coolant-temperature symbol: thermometer dipping into
	# wavy coolant lines. Chunky, pixel-hard, flat (no glass sheen).
	var stem_w := 3.0 if r < 12.0 else 4.0
	var stem_x := cx - stem_w * 0.5
	var stem_top := cy - r * 0.95
	var bulb_r := maxf(3.5, r * 0.40)
	var bulb_cy := cy + r * 0.42
	var stem_bot := bulb_cy - bulb_r * 0.25
	# Two short wavy coolant lines through the bulb (ISO dashboard language).
	# Kept narrow so they read as water, not a star around the stem.
	for i in 2:
		var wy: float = bulb_cy - 1.5 + float(i) * 4.0
		var pts := PackedVector2Array([
			Vector2(cx - r * 0.95, wy),
			Vector2(cx - r * 0.55, wy - 1.5),
			Vector2(cx - r * 0.15, wy + 1.5),
			Vector2(cx + r * 0.25, wy - 1.5),
			Vector2(cx + r * 0.65, wy + 1.5),
			Vector2(cx + r * 1.00, wy),
		])
		draw_polyline(pts, col, 2.0)
	# Stem body
	draw_rect(Rect2(stem_x, stem_top, stem_w, stem_bot - stem_top), Color8(18, 18, 24), true)
	draw_rect(Rect2(stem_x, stem_top, stem_w, stem_bot - stem_top), INK_I, false, 1.0)
	# Mercury in the stem
	var mer_top := stem_top + (stem_bot - stem_top) * 0.28
	draw_rect(Rect2(stem_x + 1.0, mer_top, stem_w - 2.0, stem_bot - mer_top + 1.0), col, true)
	# Ticks on the right of the stem
	for i in 3:
		var ty: float = stem_top + 2.0 + float(i) * ((mer_top - stem_top - 1.0) / 2.0 + 2.5)
		draw_line(Vector2(stem_x + stem_w, ty), Vector2(stem_x + stem_w + 3.0, ty), INK_I, 1.0)
	# Bulb — one flat fill + ink outline, no inner shading that would read as gloss.
	_disc(cx, bulb_cy, bulb_r, INK_I)
	_disc(cx, bulb_cy, bulb_r - 1.0, col)


# ─────────────────────────────────────────────────────────────────────────────
# Variant E3: E1 layout minus the redundant corner map. Chunkier type.
# ─────────────────────────────────────────────────────────────────────────────
func _fa() -> FontFile:
	if hud != null and hud.fa != null:
		return hud.fa
	return _fb()


func _fb() -> FontFile:
	if hud != null and hud.fb != null:
		return hud.fb
	return hud.fn


func _swf(f: FontFile, s: String, sz: int) -> float:
	return f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, sz * TS).x / TS


func _tf(f: FontFile, x: float, y: float, s: String, sz: int, col: Color, anchor := "l", shadow := true, mid := false) -> void:
	# Same pixel-hard raster path as t2, but with an explicit font (Archivo Black or Nimbus Bold).
	var z := sz * TS
	var w := f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, z).x
	var X := x * TS
	var B := y * TS + (f.get_ascent(z) if not mid else (f.get_ascent(z) - f.get_descent(z)) / 2.0)
	if anchor == "m":
		X -= w / 2.0
	elif anchor == "r":
		X -= w
	X = roundf(X)
	B = roundf(B)
	draw_set_transform(_o(), 0.0, Vector2(1.0 / TS, 1.0 / TS))
	if shadow:
		draw_string(f, Vector2(X + TS, B + TS), s, HORIZONTAL_ALIGNMENT_LEFT, -1, z, INK)
	draw_string(f, Vector2(X, B), s, HORIZONTAL_ALIGNMENT_LEFT, -1, z, col)
	draw_set_transform(_o(), 0.0, Vector2.ONE)


func _ta(x: float, y: float, s: String, sz: int, col: Color, anchor := "l", shadow := true, mid := false) -> void:
	_tf(_fa(), x, y, s, sz, col, anchor, shadow, mid)


func _tb(x: float, y: float, s: String, sz: int, col: Color, anchor := "l", shadow := true, mid := false) -> void:
	_tf(_fb(), x, y, s, sz, col, anchor, shadow, mid)


func _e_cam(pl: Dictionary) -> Dictionary:
	var md: String = String(pl.get("mode", "VIEW"))
	var k: int = int(pl.get("stop", 0))
	var cur := -1
	var ndone := 0
	match md:
		"VIEW":
			cur = k
			ndone = k
		"LOCK":
			cur = 0
			ndone = 3
		"QTE", "PLAY":
			cur = k
			ndone = k
		_:
			cur = -1
			ndone = 3
	return {"md": md, "cur": cur, "ndone": ndone}


func _paint_e3(rs: Dictionary) -> void:
	_paint_e_gap()
	_paint_e3_sign()
	var x0 := 8.0
	var y0 := 408.0
	var x1 := 632.0
	var y1 := 479.0
	_flat_panel(x0, y0, x1, y1)
	# Left: compact meters. Middle: LINE LOCK with room. Right: E/A/X + plan rows.
	_paint_e3_meters(rs, 12.0, y0, 210.0, y1)
	_vdiv(216.0, y0, y1)
	_paint_e3_lock(222.0, y0, 400.0, y1)
	_vdiv(406.0, y0, y1)
	_paint_e3_plan(412.0, y0, x1 - 4.0, y1)


func _paint_e3_meters(rs: Dictionary, x0: float, y0: float, x1: float, y1: float) -> void:
	var pad := 5.0
	var rh: float = ((y1 - y0) - pad * 2.0) / 3.0
	for i in ITEMS_E.size():
		var s: Dictionary = _item_state_e(rs, ITEMS_E[i])
		var y: float = y0 + pad + float(i) * rh
		var icy: float = y + rh * 0.5
		var r: float = 11.0 if String(s.key) == "susp" else 10.0
		_icon_at(x0 + 12.0, icy, s, r)
		var cx := x0 + 26.0
		var tw: float = _e3_stat_tag(cx, icy - 6.0, s)
		var bx := cx + tw + 4.0
		var badge: String = String(s.badge)
		var badge_w := 0.0
		if badge != "":
			badge_w = _swf(_fb(), badge, 10) + 10.0
		var bx1: float = x1 - 3.0 - (badge_w + 2.0 if badge_w > 0.0 else 0.0)
		_e_trough(bx, icy - 5.0, maxf(bx1 - bx, 16.0), 10.0, s)
		if badge_w > 0.0:
			_e3_badge_at(x1 - 3.0, icy - 6.0, s)


func _e3_stat_tag(x: float, y: float, s: Dictionary) -> float:
	var lab: String = s.stat
	var sz := 9
	var w := maxf(_swf(_fb(), lab, sz) + 8.0, 24.0)
	var h := 12.0
	var fill: Color = s.col if not s.empty else dimc(s.col, 0.35)
	if s.blink:
		fill = s.col
	draw_rect(Rect2(x, y, w, h), fill, true)
	draw_rect(Rect2(x, y, w, h), INK, false, 1.0)
	var tc: Color = INK if s.key == "susp" else Color.WHITE
	if s.empty and not s.blink:
		tc = Color8(230, 230, 235)
	_tb(x + w / 2.0, y + h / 2.0, lab, sz, tc, "m", false, true)
	return w


func _e3_badge_at(x: float, y: float, s: Dictionary) -> void:
	var b: String = s.badge
	if b == "":
		return
	var sz := 10
	var w := _swf(_fb(), b, sz) + 8.0
	var x0 := x - w
	var col: Color = L_AMBER if b == "LOW" else (s.col if b == "RECOVER" else Color8(232, 40, 44))
	if b == "OVERHEAT":
		col = COL_HOT
	draw_rect(Rect2(x0, y, w, 12.0), col, true)
	draw_rect(Rect2(x0, y, w, 12.0), INK, false, 1.0)
	var tc: Color = INK if b == "LOW" or b == "RECOVER" or b == "OVERHEAT" else Color.WHITE
	_tb(x0 + w / 2.0, y + 6.0, b, sz, tc, "m", false, true)


func _paint_e3_lock(x0: float, y0: float, x1: float, y1: float) -> void:
	# Middle of the band is LINE LOCK only — no map. Bigger digits, a longer bar, some air.
	var ls: Dictionary = _lock_state()
	_ta(x0 + 6.0, y0 + 7.0, "LINE LOCK", 12, L_WHITE, "l", true, false)
	if bool(ls.locked):
		_ta(x1 - 6.0, y0 + 5.0, "SET", 20, L_WHITE, "r", true, false)
	else:
		_ta(x1 - 6.0, y0 + 5.0, "%04.1fs" % float(ls.left), 20, L_AMBER, "r", true, false)
	# Thick continuous trough, full column width, under the digits with some air.
	_e_trough(x0 + 6.0, y0 + 36.0, (x1 - 6.0) - (x0 + 6.0), 14.0, ls)


func _paint_e3_plan(x0: float, y0: float, x1: float, y1: float) -> void:
	if not st.has("plan"):
		return
	var pl: Dictionary = st.plan
	_ta(x0 + 22.0, y0 + 2.0, "PLAN THE LINE", 10, L_WHITE, "l", true, false)
	var cam: Dictionary = _e_cam(st.plate) if st.has("plate") else {"cur": -1, "ndone": 0, "md": "VIEW"}
	var ph: int = int(pl.get("phase", 0))
	var slots: Array = st.get("slots", [null, null, null])
	var lanes: Array = ["D", "S", "A"] if String(st.get("dir", "R")) == "L" else ORDER
	var row0 := y0 + 13.0
	var rh: float = maxf(((y1 - 2.0) - row0) / 3.0, 16.0)
	var letters := ["E", "A", "X"]
	for i in 3:
		var ry: float = row0 + float(i) * rh
		var active: bool = (i == ph and ph < 3)
		var locked: bool = (i < ph) or (ph >= 3 and slots[i] != null)
		# Camera-stop letter, aligned to this plan row (E=ENTRY, A=APEX, X=EXIT).
		var on_cam: bool = int(cam.cur) == i
		var cam_done: bool = i < int(cam.ndone) and not on_cam
		var lcol: Color = L_AMBER if on_cam else (L_WHITE if cam_done else L_DIMMER)
		if on_cam:
			draw_rect(Rect2(x0 + 3.0, ry + 2.0, 16.0, rh - 4.0), L_AMBER, true)
			lcol = INK
		_ta(x0 + 11.0, ry + rh * 0.5, letters[i], 11, lcol, "m", not on_cam, true)
		if active:
			draw_rect(Rect2(x0 + 21.0, ry + 1.0, 2.0, rh - 2.0), L_AMBER, true)
		var nx := x0 + 26.0
		var ncol: Color = INK if active else (EDGE if locked else TODO)
		if active:
			var nw: float = _swf(_fb(), PH[i], 10) + 6.0
			draw_rect(Rect2(nx - 2.0, ry + 1.0, nw, 10.0), L_AMBER, true)
		_tb(nx, ry + 1.0, PH[i], 10, ncol, "l", not active, false)
		if locked:
			check(nx + _swf(_fb(), PH[i], 10) + 3.0, ry + 2.0, CHECK_GREEN)
		var chosen := ""
		if locked and slots[i] != null:
			chosen = String(slots[i])
		elif locked and i == 0 and String(pl.get("entry", "")) != "":
			chosen = String(pl.entry)
		elif active:
			chosen = ORDER[int(pl.get("sel", 0))] if int(pl.get("sel", 0)) >= 0 else ""
		var lx := x0 + 78.0
		if active or locked:
			var w := 42.0
			if x1 - lx < w * 3.0 + 4.0:
				w = maxf(((x1 - 2.0) - lx) / 3.0, 34.0)
			for k in lanes:
				var lab: String = LANE[k]
				var note: String = NAME[k]
				var avail: Dictionary = pl.get("avail", {})
				var off: bool = active and int(avail.get(k, 1)) <= 0
				var selected: bool = (k == chosen and not off)
				var dim: bool = locked or off
				var cx := lx + w * 0.5
				if selected:
					draw_rect(Rect2(lx, ry + 1.0, w - 3.0, 9.0), AMBER if active else EDGE, true)
				_tb(cx, ry + 1.0, lab, 9, INK if selected else (DIMT if dim else SUB), "m", not selected, false)
				if selected and locked:
					check(cx + _swf(_fb(), lab, 9) * 0.5 + 2.0, ry + 1.0, INK)
				_e3_stat_box(cx, ry + 11.0, note, STANCE[k], selected, dim and not selected)
				lx += w
		else:
			_tb(lx, ry + rh * 0.5, "--  --  --", 11, TODO, "l", false, true)


func _e3_stat_box(cx: float, y: float, label: String, col: Color, selected: bool, dim: bool) -> void:
	var sz := 8
	var w := maxf(_swf(_fb(), "POW", sz) + 6.0, 22.0)
	var h := 7.0
	var x0 := cx - w * 0.5
	var r := Rect2(x0, y, w, h)
	var fill: Color = col if selected else dimc(col, 0.45 if dim else 0.7)
	draw_rect(r, fill, true)
	draw_rect(r, INK, false, 1.0)
	var tc: Color = INK if col == STANCE.S else Color.WHITE
	if dim and not selected:
		tc = INK if col == STANCE.S else Color8(230, 230, 235)
	_tb(cx, y + h * 0.5, label, sz, tc, "m", false, true)


func _paint_e3_sign() -> void:
	# Floating upcoming-turn sign: flat amber plate, hairpin-left (U-turn) arrow,
	# corner name under the sign. Kept short so the name sits above the OUT tell.
	# Gap box ends at y=122; lane labels start around y=180.
	var cx := 320.0
	var w := 34.0
	var h := 32.0
	var x0 := cx - w * 0.5
	var y0 := 125.0
	var cy := y0 + h * 0.5
	draw_rect(Rect2(x0, y0, w, h), Color8(255, 184, 56), true)
	draw_rect(Rect2(x0, y0, w, h), INK, false, 1.0)
	draw_rect(Rect2(x0 + 1.0, y0 + 1.0, w - 2.0, h - 2.0), INK, false, 1.0)
	# Chunky hairpin-left / U-turn: enter up the right, hook over the top, come
	# back down the left, arrow head pointing down. A short left vertical before
	# the head makes the loop read as a 180, not a 90-degree left.
	var t := 5.0
	var rx := cx + 5.0
	var lx := cx - 9.0
	var top := y0 + 5.0
	var bot := y0 + h - 5.0
	var hook := y0 + 16.0
	draw_rect(Rect2(rx, top, t, bot - top), INK, true)
	draw_rect(Rect2(lx, top, (rx + t) - lx, t), INK, true)
	draw_rect(Rect2(lx, top, t, hook - top), INK, true)
	# Arrowhead on the left leg, pointing down.
	var ah := P([lx - 5.0, hook, lx + t + 5.0, hook, lx + t * 0.5, hook + 9.0])
	solid(ah, INK)
	# Corner name under the sign, Archivo Black.
	var name := "HAIRPIN L"
	if st.has("plate"):
		name = String(st.plate.get("name", "HAIRPIN L"))
	_ta(cx, y0 + h + 2.0, name, 11, L_WHITE, "m", true, false)

# ─────────────────────────────────────────────────────────────────────────────
# Variant E3B: E3 layout, heat/load meters that fill as load builds and drain
# as they recover. LIMIT (~80%) and RELEASE (~55%) marks. OVERRUN between
# LIMIT and full; LOCKED at full until the fill cools past RELEASE.
# Placeholder thresholds, not approved. Concept only; not in the sim.
# ─────────────────────────────────────────────────────────────────────────────
const LIMIT_T := 0.80
const RELEASE_T := 0.55
const COL_OVERRUN := Color8(255, 112, 28)  # #FF701C
const COL_LIM_MARK := Color8(255, 184, 56)  # amber T-cap on the top edge
const COL_REL_MARK := Color8(140, 200, 255)  # cool triangle on the bottom edge
const KEY_STANCE := {"fuel": "A", "brakes": "D", "susp": "S"}


func _paint_e3b(rs: Dictionary) -> void:
	_paint_e_gap()
	_paint_e3_sign()
	var x0 := 8.0
	var y0 := 408.0
	var x1 := 632.0
	var y1 := 479.0
	_flat_panel(x0, y0, x1, y1)
	_paint_e3b_meters(rs, 12.0, y0, 210.0, y1)
	_vdiv(216.0, y0, y1)
	# Steal a little width from LINE LOCK so PLAN THE LINE can sit on a clean
	# three-column grid. The lock title, timer and trough stay readable.
	_paint_e3_lock(222.0, y0, 372.0, y1)
	_vdiv(378.0, y0, y1)
	_paint_e3b_plan(rs, 384.0, y0, x1 - 4.0, y1)


func _item_state_e3b(rs: Dictionary, it: Dictionary) -> Dictionary:
	var s: Dictionary = _item_state(rs, it)
	if String(it.key) == "fuel":
		s["heat"] = true
	s["no_slash"] = true
	var loads: Dictionary = rs.get("load", {})
	var f: float
	if loads.has(it.key):
		f = clampf(float(loads[it.key]), 0.0, 1.0)
	else:
		f = clampf(float(s.val) / maxf(float(s.pips), 1.0), 0.0, 1.0)
	s["load"] = f
	var locked_keys: Array = rs.get("locked", [])
	var is_locked: bool = locked_keys.has(it.key) or f >= 0.999
	if is_locked and f < RELEASE_T:
		is_locked = false
	s["meter_locked"] = is_locked
	s["cooling"] = is_locked and f < 0.999
	s["overrun"] = (not is_locked) and f >= LIMIT_T
	if is_locked:
		s["badge"] = "LOCKED"
	elif bool(s.overrun):
		s["badge"] = "OVERRUN"
	else:
		s["badge"] = ""
	return s


func _paint_e3b_meters(rs: Dictionary, x0: float, y0: float, x1: float, y1: float) -> void:
	var pad := 5.0
	var rh: float = ((y1 - y0) - pad * 2.0) / 3.0
	for i in ITEMS_E.size():
		var s: Dictionary = _item_state_e3b(rs, ITEMS_E[i])
		var y: float = y0 + pad + float(i) * rh
		var icy: float = y + rh * 0.5
		var r: float = 11.0 if String(s.key) == "susp" else 10.0
		_icon_at(x0 + 12.0, icy, s, r)
		var cx := x0 + 26.0
		var tw: float = _e3b_stat_tag(cx, icy - 6.0, s)
		var bx := cx + tw + 4.0
		var badge: String = String(s.badge)
		var badge_w := 0.0
		if badge != "":
			badge_w = _swf(_fb(), badge, 9) + (16.0 if badge == "LOCKED" else 10.0)
		var bx1: float = x1 - 3.0 - (badge_w + 2.0 if badge_w > 0.0 else 0.0)
		_e3b_trough(bx, icy - 5.0, maxf(bx1 - bx, 16.0), 10.0, s)
		if badge_w > 0.0:
			_e3b_badge_at(x1 - 3.0, icy - 6.0, s)


func _e3b_stat_tag(x: float, y: float, s: Dictionary) -> float:
	var lab: String = s.stat
	var sz := 9
	var w := maxf(_swf(_fb(), lab, sz) + 8.0, 24.0)
	var h := 12.0
	var fill: Color = s.col
	var tc: Color = INK if s.key == "susp" else Color.WHITE
	if bool(s.get("meter_locked", false)):
		fill = Color8(72, 76, 86)
		tc = Color8(200, 200, 206)
	draw_rect(Rect2(x, y, w, h), fill, true)
	draw_rect(Rect2(x, y, w, h), INK, false, 1.0)
	_tb(x + w / 2.0, y + h / 2.0, lab, sz, tc, "m", false, true)
	if bool(s.get("meter_locked", false)):
		# Hard strike through the chip.
		draw_line(Vector2(x + 1.0, y + h - 2.0), Vector2(x + w - 1.0, y + 2.0), INK, 2.0)
		draw_line(Vector2(x + 1.0, y + h - 2.0), Vector2(x + w - 1.0, y + 2.0), Color8(220, 220, 224), 1.0)
	return w


func _e3b_badge_at(x: float, y: float, s: Dictionary) -> void:
	var b: String = String(s.badge)
	if b == "":
		return
	var sz := 9
	var lock := b == "LOCKED"
	var tw := _swf(_fb(), b, sz)
	var w := tw + (16.0 if lock else 8.0)
	var x0 := x - w
	var col: Color = Color8(48, 50, 60) if lock else COL_OVERRUN
	draw_rect(Rect2(x0, y, w, 12.0), col, true)
	draw_rect(Rect2(x0, y, w, 12.0), INK, false, 1.0)
	var tx := x0 + w / 2.0
	if lock:
		_padlock(x0 + 5.0, y + 6.0, 4.4, COL_OVERRUN)
		tx += 5.0
		_tb(tx, y + 6.0, b, sz, Color.WHITE, "m", false, true)
	else:
		_tb(x0 + w / 2.0, y + 6.0, b, sz, INK, "m", false, true)


func _padlock(cx: float, cy: float, s: float, col: Color) -> void:
	# Tiny flat padlock, stroke-built so the shackle reads at badge size.
	var bw := s * 1.05
	var bh := s * 0.90
	var by := cy + s * 0.10
	# Shackle (top half-ring) sits above the body.
	var sr := s * 0.80
	_ring_n(cx, by, sr, maxf(sr - 1.4, sr * 0.55), PI, PI, col, 10)
	# Body + keyhole.
	draw_rect(Rect2(cx - bw, by, bw * 2.0, bh), col, true)
	draw_rect(Rect2(cx - bw, by, bw * 2.0, bh), INK, false, 1.0)
	_disc(cx, by + bh * 0.48, maxf(0.6, s * 0.18), INK, 6)


func _e3b_trough(x: float, y: float, w: float, h: float, s: Dictionary) -> void:
	var well := Rect2(x, y, w, h)
	draw_rect(well, Color8(8, 10, 16), true)
	draw_rect(well, INK, false, 1.0)
	var inner := w - 2.0
	var x0 := x + 1.0
	var y0 := y + 1.0
	var y1 := y + h - 1.0
	# Flat OVERRUN zone in the last 20% of the well (LIMIT to full).
	var zone_x := x0 + inner * LIMIT_T
	var zone_w := maxf((x0 + inner) - zone_x, 1.0)
	draw_rect(Rect2(zone_x, y0, zone_w, y1 - y0), Color8(72, 32, 16), true)
	var f: float = clampf(float(s.get("load", 0.0)), 0.0, 1.0)
	var fill_w := inner * f
	var col: Color = s.col
	if bool(s.get("overrun", false)) or (bool(s.get("meter_locked", false)) and not bool(s.get("cooling", false))):
		col = COL_OVERRUN
	elif bool(s.get("cooling", false)):
		col = dimc(s.col, 0.50)
	if fill_w >= 1.0:
		var slant := fill_w < inner - 0.51 and not bool(s.get("meter_locked", false))
		_trough_fill(x0, y0, y1, fill_w, inner, col, slant)
		if bool(s.get("cooling", false)):
			_flat_hatch(x0, y0, y1, fill_w, Color8(10, 12, 18, 200))
	# LIMIT: small amber block on the top edge, plus a short tick into the well.
	# A block, not a letter-T, so it stays distinct from the RELEASE triangle.
	var lx := x0 + inner * LIMIT_T
	draw_rect(Rect2(lx - 3.0, y - 2.0, 7.0, 3.0), COL_LIM_MARK, true)
	draw_rect(Rect2(lx - 3.0, y - 2.0, 7.0, 3.0), INK, false, 1.0)
	draw_line(Vector2(lx, y + 1.0), Vector2(lx, y + 4.0), COL_LIM_MARK, 2.0)
	# RELEASE: cool filled triangle on the bottom border, pointing up.
	var rx := x0 + inner * RELEASE_T
	var tri := P([rx, y + h - 5.0, rx - 3.5, y + h - 1.0, rx + 3.5, y + h - 1.0])
	solid(tri, COL_REL_MARK)
	outline(tri, INK)


func _flat_hatch(x0: float, y0: float, y1: float, fill_w: float, col: Color) -> void:
	# Flat 1 px diagonal hatch, clipped to the fill. No grain, no sheen.
	var x1 := x0 + fill_w
	var step := 4.0
	var c := x0 + y0
	var end := x1 + y1
	while c <= end + 0.1:
		var xa := x0
		var ya := c - x0
		var xb := x1
		var yb := c - x1
		if ya < y0:
			xa = c - y0
			ya = y0
		elif ya > y1:
			xa = c - y1
			ya = y1
		if yb < y0:
			xb = c - y0
			yb = y0
		elif yb > y1:
			xb = c - y1
			yb = y1
		if xa >= x0 - 0.2 and xa <= x1 + 0.2 and xb >= x0 - 0.2 and xb <= x1 + 0.2 and absf(xa - xb) + absf(ya - yb) > 0.6:
			draw_line(Vector2(xa, ya), Vector2(xb, yb), col, 1.0)
		c += step


func _paint_e3b_plan(rs: Dictionary, x0: float, y0: float, x1: float, y1: float) -> void:
	if not st.has("plan"):
		return
	var pl: Dictionary = st.plan
	# Clean grid. Nothing touches the panel border. Title gets its own header
	# row with a gap below. E/A/X in a fixed left column, row labels in a
	# fixed second column, then three equal-width OUT/MID/IN columns with
	# even gutters. Position text is unframed and centred in the column;
	# the framed stat box sits centred directly under it, same width in every
	# column.
	var pad := 4.0
	var ix0 := x0 + pad
	var ix1 := x1 - pad
	_ta(ix0, y0 + 9.0, "PLAN THE LINE", 10, L_WHITE, "l", true, true)
	var cam: Dictionary = _e_cam(st.plate) if st.has("plate") else {"cur": -1, "ndone": 0, "md": "VIEW"}
	var ph: int = int(pl.get("phase", 0))
	var slots: Array = st.get("slots", [null, null, null])
	var lanes: Array = ["D", "S", "A"] if String(st.get("dir", "R")) == "L" else ORDER
	var row0 := y0 + 16.0
	var rh: float = maxf(((y1 - 3.0) - row0) / 3.0, 16.0)
	var letters := ["E", "A", "X"]
	var letter_w := 16.0
	var label_x := ix0 + letter_w + 4.0
	var label_w := 38.0
	var grid_x := label_x + label_w + 5.0
	var n_col := 3
	var gutter := 6.0
	var col_w: float = maxf(((ix1 - grid_x) - gutter * float(n_col - 1)) / float(n_col), 36.0)
	# Stance keys that are locked (unavailable) or in OVERRUN (selectable, penalty).
	var locked_stance := {}
	var overrun_stance := {}
	for it in ITEMS_E:
		var s: Dictionary = _item_state_e3b(rs, it)
		var stn: String = String(KEY_STANCE.get(it.key, ""))
		if bool(s.get("meter_locked", false)):
			locked_stance[stn] = true
		elif bool(s.get("overrun", false)):
			overrun_stance[stn] = true
	for i in 3:
		var ry: float = row0 + float(i) * rh
		var mid_y: float = ry + rh * 0.5
		var active: bool = (i == ph and ph < 3)
		var locked_row: bool = (i < ph) or (ph >= 3 and slots[i] != null)
		var on_cam: bool = int(cam.cur) == i
		var cam_done: bool = i < int(cam.ndone) and not on_cam
		var lcol: Color = L_AMBER if on_cam else (L_WHITE if cam_done else L_DIMMER)
		# E/A/X sit in their own column. The camera highlight stays inside it
		# and never runs into the row label.
		if on_cam:
			draw_rect(Rect2(ix0, ry + 2.0, letter_w, rh - 4.0), L_AMBER, true)
			lcol = INK
		_ta(ix0 + letter_w * 0.5, mid_y, letters[i], 11, lcol, "m", not on_cam, true)
		# Active row: no fill behind the label. A short amber tick in the
		# gutter plus amber type marks the row; the selected cell is framed.
		if active:
			draw_rect(Rect2(label_x - 3.0, ry + 2.0, 2.0, rh - 4.0), L_AMBER, true)
		var ncol: Color = L_AMBER if active else (EDGE if locked_row else TODO)
		_tb(label_x + 1.0, mid_y, PH[i], 10, ncol, "l", not active, true)
		if locked_row:
			check(label_x + 1.0 + _swf(_fb(), PH[i], 10) + 3.0, mid_y - 4.0, CHECK_GREEN)
		var chosen := ""
		if locked_row and slots[i] != null:
			chosen = String(slots[i])
		elif locked_row and i == 0 and String(pl.get("entry", "")) != "":
			chosen = String(pl.entry)
		elif active:
			chosen = ORDER[int(pl.get("sel", 0))] if int(pl.get("sel", 0)) >= 0 else ""
		if locked_stance.has(chosen):
			if active:
				chosen = ""
		if active or locked_row:
			for k_i in n_col:
				var k: String = String(lanes[k_i])
				var lab: String = LANE[k]
				var note: String = NAME[k]
				var avail: Dictionary = pl.get("avail", {})
				var stance_lock: bool = locked_stance.has(k)
				var off: bool = (active and int(avail.get(k, 1)) <= 0) or stance_lock
				var selected: bool = (k == chosen and not off)
				var dim: bool = locked_row or off
				var cx: float = grid_x + (col_w + gutter) * float(k_i) + col_w * 0.5
				var cell_x: float = grid_x + (col_w + gutter) * float(k_i)
				# Selected choice: a 1 px amber (or edge) frame hugging the
				# position + stat stack. No filled bar over the position text.
				if selected:
					var stack_w := maxf(maxf(_swf(_fb(), "POW", 8) + 6.0, 22.0), _swf(_fb(), lab, 9)) + 8.0
					var fr := Rect2(cx - stack_w * 0.5, ry + 1.0, stack_w, rh - 2.0)
					draw_rect(fr, L_AMBER if active else EDGE, false, 1.0)
				_tb(cx, ry + 4.0, lab, 9, (L_AMBER if active else L_WHITE) if selected else (DIMT if dim else SUB), "m", not selected, true)
				if selected and locked_row:
					check(cx + _swf(_fb(), lab, 9) * 0.5 + 2.0, ry + 1.0, INK)
				_e3_stat_box(cx, ry + rh - 8.0, note, STANCE[k], selected, dim and not selected)
				if stance_lock:
					# Hard strike across the lane + stat chip so the stance reads unavailable.
					var x_a := cell_x + 3.0
					var x_b := cell_x + col_w - 3.0
					draw_line(Vector2(x_a, ry + rh - 3.0), Vector2(x_b, ry + 3.0), INK, 2.0)
					draw_line(Vector2(x_a, ry + rh - 3.0), Vector2(x_b, ry + 3.0), Color8(220, 220, 224), 1.0)
				elif overrun_stance.has(k):
					# Penalty badge: the stat box itself fills hot orange, label stays
					# POW / EN / HAN in ink. No extra tab — the cell is too tight.
					var box_w := maxf(_swf(_fb(), "POW", 8) + 6.0, 22.0)
					var by0 := ry + rh - 8.0
					var bx0 := cx - box_w * 0.5
					draw_rect(Rect2(bx0, by0, box_w, 7.0), COL_OVERRUN, true)
					draw_rect(Rect2(bx0, by0, box_w, 7.0), INK, false, 1.0)
					_tb(cx, by0 + 3.5, note, 8, INK, "m", false, true)
		else:
			# Empty pending rows: a neat dash centred in each column.
			for k_i in n_col:
				var cx2: float = grid_x + (col_w + gutter) * float(k_i) + col_w * 0.5
				_tb(cx2, mid_y, "--", 11, TODO, "m", false, true)



func _paint_icon_job() -> void:
	# Standalone icon render for review sheets. Drawn in the node's local pixels.
	var kind := String(icon_job.get("kind", "brakes"))
	var cx := float(icon_job.get("cx", 8.0))
	var cy := float(icon_job.get("cy", 8.0))
	var r := float(icon_job.get("r", 7.0))
	var col: Color = icon_job.get("col", COL.brakes)
	if not bool(icon_job.get("transparent", false)):
		var bg: Color = icon_job.get("bg", Color8(10, 14, 36))
		draw_rect(Rect2(0, 0, size.x, size.y), bg, true)
	match kind:
		"fuel", "coolant", "pow":
			_icon_coolant(cx, cy, r, col)
		"brakes", "en", "brake":
			_icon_wheel(cx, cy, r, col, false)
		_:
			_icon_shock(cx, cy, r, col)
