## TOUGE (Gordon, touge-race): E3B-style heat gauges (Arthur, unapproved/arthur/mockups/resource_meters/e3b_states.png and
## README:28) driven by the sim's G2 gauges (scripts/heat.gd = sim heat.py). Rows POW / EN / HAN as in E3B.
## Fill = load / capacity, clamped to the bar. RELEASE = the blue triangle at HEAT_RELEASE (globals.gd, sim equations.py, 30 %).
## No LIMIT cap: under G2 a gauge locks only when full (E3B's ~80 % LIMIT was a concept number, not the sim's).
## LOCKED: padlock + LOCKED tag, chip greyed and struck; locked and cooling (fill below full): dim hatched fill until RELEASE.
## OVERRUN: the planned / hovered stance's next play would pass full (heat.overrun_if > 0): hot-orange fill + OVERRUN tag.
## No LIMP tag (Austin). Display only; every value comes from main.gd's heat state (projected gauges during planning).
@tool
extends "res://scripts/hud/hud_panel.gd"
const ROWS := ["P", "E", "H"]
const HOT := Color8(255, 112, 28)
const REL := Color8(120, 190, 255)
const GREY := Color8(70, 74, 90)

var drawn := {}   # TOUGE (Austin t119u): bar fraction actually drawn per gauge this paint (main.gd heat check)
var drawn_frame := -1

const PANEL_W := 206.0   # main.gd lays the touch stance row out against this (Austin pt137u)
const PANEL_H := 64.0
func paint() -> void:
	var h = st.get("heat")
	if h == null: return
	drawn_frame = Engine.get_process_frames()
	var o := origin(); var x := o.x; var y := o.y
	var W := PANEL_W; var H := PANEL_H
	lpanel(x, y, x + W, y + H)
	t2(x + 6, y + 3, "HEAT", 9, L_DIM, false, "l", true, false, true)
	if String(h.get("who", "")) != "": t2(x + W - 6, y + 3, String(h.who), 9, L_DIMMER, false, "r", true, false, true)
	for r in 3:
		var k: String = ROWS[r]
		var f: float = float(h.fill[k]); var lk: bool = bool(h.locked[k]); var ov: bool = bool(h.over.get(k, false))
		var ry := y + 15.0 + r * 16.0
		# stance chip (E3B: coloured label; greyed + struck when locked)
		var cp := P([x + 8, ry, x + 44, ry, x + 40, ry + 12, x + 4, ry + 12])
		if lk:
			solid(cp, GREY); t2(x + 24, ry + 6, NAME[k], 10, Color8(150, 150, 160), false, "m", false, true, true)
			draw_line(Vector2(x + 6, ry + 11), Vector2(x + 42, ry + 1), Color8(220, 220, 230), 1.0)
		else:
			solid(cp, HOT if ov else STANCE[k]); outline(cp, L_INK)
			t2(x + 24, ry + 6, NAME[k], 10, L_INK if (k == "H" and not ov) else Color.WHITE, false, "m", false, true, true)
		# trough
		var bx := x + 50.0; var bw := 88.0; var by := ry + 2.0; var bh := 8.0
		rect(bx - 1, by - 1, bw + 2, bh + 2, L_INK); rect(bx, by, bw, bh, Color8(20, 24, 40))
		var fw := clampf(f, 0.0, 1.0) * bw
		drawn[k] = fw / bw
		if lk and f < 1.0:   # locked, cooling: dim hatched fill
			rect(bx, by, fw, bh, dimc(STANCE[k], 0.35))
			var hx := bx
			while hx < bx + fw - 1.0:
				draw_line(Vector2(hx, by + bh), Vector2(minf(hx + bh, bx + fw), by + maxf(0.0, bh - (bx + fw - hx))), dimc(STANCE[k], 0.75), 1.0)
				hx += 4.0
		else:
			rect(bx, by, fw, bh, HOT if (lk or ov) else STANCE[k])
		# RELEASE triangle (sim HEAT_RELEASE)
		var rx := bx + float(h.release) * bw
		solid(P([rx, by + bh - 3, rx + 3, by + bh + 2, rx - 3, by + bh + 2]), REL)
		# tag column
		var tx := bx + bw + 6.0
		if lk:
			_padlock(tx + 4, ry + 1)
			t2(tx + 12, ry + 6, "LOCKED", 9, L_WHITE, false, "l", true, true, true)
		elif ov:
			var tp := P([tx, ry, tx + 50, ry, tx + 50, ry + 12, tx, ry + 12]); solid(tp, HOT); outline(tp, L_INK)
			t2(tx + 25, ry + 6, "OVERRUN", 9, L_INK, false, "m", false, true, true)
		else:
			t2(tx + 2, ry + 6, "%d%%" % roundi(clampf(f, 0.0, 9.99) * 100.0), 9, L_DIM, false, "l", true, true, true)

func _padlock(x: float, y: float) -> void:
	draw_arc(Vector2(x + 3, y + 4), 2.5, PI, TAU, 8, HOT, 1.0)
	rect(x, y + 4, 7, 6, HOT)
