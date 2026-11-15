## Combined PLAN THE LINE panel, lower right (Austin 2026-11-12, line-preview mockup only).
## Folds the old bottom-left ENTRY IN/MID/OUT strip into this panel. Every phase row
## (ENTRY, APEX, EXIT) labels choices OUT / MID / IN with a small stat chip
## (OUT · POW, MID · HAN, IN · EN). The pick itself is the stat. Austin 2026-11-12:
## "stance selection should say in/mid/out for all, with a chip explaining stat."
## Austin follow-up: "The stat should be framed under the position text."
## Position text (OUT / MID / IN) is unframed; the stat (POW / HAN / EN) sits in
## its own small framed box underneath, filled in the stat colour, with a
## pixel-hard plate-style border. No frame around the whole chip.
@tool
extends "res://scripts/hud/hud_panel.gd"

## Small framed stat box (POW / HAN / EN) in stance colour, plate-style bevel, pixel-hard.
func stat_box(cx: float, y: float, label: String, col: Color, selected: bool, dim: bool) -> void:
	var sz := 8
	# Fixed width so POW / HAN / EN frames line up as a row of equal chips.
	var w := maxf(sw("POW", sz, true, true) + 8.0, 24.0)
	var h := 11.0
	var x0 := cx - w / 2.0
	var pts := P([x0 + 2, y, x0 + w, y, x0 + w - 2, y + h, x0, y + h])
	var fill: Color = col if selected else dimc(col, 0.45 if dim else 0.7)
	solid(pts, fill)
	outline(pts, INK)
	var hi := Color8(255, 255, 255, 200) if selected else Color8(220, 230, 255, 110)
	var sh := Color8(0, 0, 0, 200 if selected else 140)
	draw_line(pts[0] + Vector2(1, 1), pts[1] + Vector2(-1, 1), hi, 1.0)
	draw_line(pts[0] + Vector2(1, 1), pts[3] + Vector2(1, -1), Color8(hi.r8, hi.g8, hi.b8, 160), 1.0)
	draw_line(pts[1] + Vector2(-1, 1), pts[2] + Vector2(-1, -1), sh, 1.0)
	draw_line(pts[2] + Vector2(-1, -1), pts[3] + Vector2(1, -1), Color8(0, 0, 0, 220 if selected else 150), 1.0)
	# HAN yellow needs dark text; green/red use white. Dimmed boxes keep the same ink so the letters stay sharp.
	var tc: Color = INK if col == STANCE.S else Color.WHITE
	if dim and not selected:
		tc = INK if col == STANCE.S else Color8(230, 230, 235)
	t2(cx, y + h / 2.0, label, sz, tc, true, "m", false, true)

func paint() -> void:
	var pl: Dictionary = st.plan
	# Pass 4: slimmer and further right/down so the chase MX5 is not covered.
	var x0 := 424.0
	var y0 := 372.0
	var x1 := 636.0
	var y1 := 479.0
	var body := cut_panel(x0, y0, x1, y1, 9)
	semi(body, PANEL)
	plate_finish(body, x0, y0, x1, y1)
	outline(body, EDGE)
	outline(cut_panel(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 8), EDGE_D)
	var tab := P([x0 + 22, y0 - 14, x0 + 118, y0 - 14, x0 + 128, y0, x0 + 22, y0])
	solid(tab, AMBER)
	outline(tab, INK)
	t2(x0 + 29, y0 - 14, "PLAN THE LINE", 12, INK, false, "l", false, false, true)
	var ph: int = int(pl.phase)
	var slots: Array = st.get("slots", [null, null, null])
	# On-screen lane order: left corner IN MID OUT, right corner OUT MID IN.
	var lanes: Array = ["D", "S", "A"] if String(st.get("dir", "R")) == "L" else ORDER
	for i in 3:
		var ry := y0 + 6 + i * 30
		var active: bool = (i == ph and ph < 3)
		var locked: bool = (i < ph) or (ph >= 3 and slots[i] != null)
		if active:
			var al := [200, 140, 90, 50]
			for j in 4:
				var bx := x0 + 4 + j * 50
				semi(P([bx, ry - 2, bx + 54, ry - 2, bx + 50, ry + 26, bx - 4, ry + 26]), AMBER, al[j] / 255.0)
			var tri := P([x0 + 8, ry + 8, x0 + 15, ry + 13, x0 + 8, ry + 18])
			solid(tri, Color.WHITE)
			outline(tri, INK)
		# Phase name
		var nx := x0 + (20 if active else 10)
		var ncol: Color = INK if active else (EDGE if locked else TODO)
		t2(nx, ry + 8, PH[i], 12, ncol, true, "l", not active, true, true)
		if locked:
			check(nx + sw(PH[i], 12, true, true) + 4, ry + 6, CHECK_GREEN)
		# All rows: unframed OUT / MID / IN over a small framed stat box.
		var chosen: String = ""
		if locked and slots[i] != null:
			chosen = String(slots[i])
		elif locked and i == 0 and String(pl.entry) != "":
			chosen = String(pl.entry)
		elif active:
			chosen = ORDER[int(pl.sel)] if int(pl.sel) >= 0 else ""
		if active or locked:
			var lx := x0 + 56
			var w := 44.0
			for k in lanes:
				var lab: String = LANE[k]
				var note: String = NAME[k]
				var off: bool = active and int(pl.avail[k]) <= 0
				var selected: bool = (k == chosen and not off)
				var dim: bool = locked or off
				var cx := lx + w / 2.0 - 1.0
				var hw := w - 2.0
				# Selection highlight behind the position text only — not a frame around the whole chip.
				if selected:
					solid(P([lx, ry + 1, lx + hw, ry + 1, lx + hw - 2, ry + 13, lx - 2, ry + 13]), AMBER if active else EDGE)
				t2(cx, ry + 7, lab, 10, INK if selected else (DIMT if dim else SUB), true, "m", not selected, true)
				if selected and locked:
					# Tick just after the position letters, still on the highlight and above the stat box.
					check(cx + sw(lab, 10, true, true) / 2.0 + 3.0, ry + 2, INK)
				stat_box(cx, ry + 13, note, STANCE[k], selected, dim and not selected)
				lx += w + 2.0
		else:
			t2(x0 + 70, ry + 9, "--  --  --", 12, TODO, false, "l", false, true)
	t2(x0 + 8, y1 - 12, "Line set. Enter to lock now" if ph >= 3 else "Line locks at turn-in", 9, SUB, true)
	t2(x1 - 8, y1 - 12, "Enter SET  Bksp BACK", 9, SUB, false, "r")
