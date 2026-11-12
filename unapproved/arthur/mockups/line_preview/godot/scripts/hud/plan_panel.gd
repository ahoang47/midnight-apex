## Combined PLAN THE LINE panel, lower right (Austin 2026-11-12, line-preview mockup only).
## Folds the old bottom-left ENTRY IN/MID/OUT strip into this panel: each phase row carries the
## lane and stance pick; the active row is highlighted and is where you choose lane (Entry) or stance.
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var pl: Dictionary = st.plan
	var x0 := 360.0
	var y0 := 316.0
	var x1 := 628.0
	var y1 := 468.0
	var body := cut_panel(x0, y0, x1, y1, 9)
	semi(body, PANEL)
	plate_finish(body, x0, y0, x1, y1)
	outline(body, EDGE)
	outline(cut_panel(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 8), EDGE_D)
	var tab := P([x0, y0 - 15, x0 + 108, y0 - 15, x0 + 119, y0, x0, y0])
	solid(tab, AMBER)
	outline(tab, INK)
	t2(x0 + 7, y0 - 14, "PLAN THE LINE", 12, INK, false, "l", false, false, true)
	var ph: int = int(pl.phase)
	var slots: Array = st.get("slots", [null, null, null])
	# On-screen lane order: left corner IN MID OUT, right corner OUT MID IN.
	var lanes: Array = ["D", "S", "A"] if String(st.get("dir", "R")) == "L" else ORDER
	for i in 3:
		var ry := y0 + 10 + i * 38
		var active: bool = (i == ph and ph < 3)
		var locked: bool = (i < ph) or (ph >= 3 and slots[i] != null)
		if active:
			var al := [200, 150, 100, 55]
			for j in 4:
				var bx := x0 + 6 + j * 62
				semi(P([bx, ry - 4, bx + 66, ry - 4, bx + 62, ry + 30, bx - 4, ry + 30]), AMBER, al[j] / 255.0)
			var tri := P([x0 + 8, ry + 8, x0 + 15, ry + 13, x0 + 8, ry + 18])
			solid(tri, Color.WHITE)
			outline(tri, INK)
		# Phase name
		var nx := x0 + (20 if active else 10)
		var ncol: Color = INK if active else (EDGE if locked else TODO)
		t2(nx, ry + 8, PH[i], 12, ncol, true, "l", not active, true, true)
		if locked:
			check(nx + sw(PH[i], 12, true, true) + 4, ry + 6, CHECK_GREEN)
		if i == 0:
			# Entry row always shows the three lanes; chosen/hovered slab is amber.
			var chosen_lane: String = ""
			if locked and String(pl.entry) != "":
				chosen_lane = String(pl.entry)
			elif active:
				chosen_lane = ORDER[int(pl.sel)] if int(pl.sel) >= 0 else ""
			var lx := x0 + 78
			for k in lanes:
				var lab: String = LANE[k]
				var w := 32.0
				if k == chosen_lane:
					solid(P([lx, ry + 2, lx + w - 2, ry + 2, lx + w - 4, ry + 16, lx - 2, ry + 16]), AMBER if active else EDGE)
					t2(lx + w / 2 - 2, ry + 9, lab, 11, INK, true, "m", false, true)
					if locked:
						check(lx + w - 2, ry + 5, INK)
				else:
					t2(lx + w / 2 - 2, ry + 9, lab, 11, DIMT if locked else SUB, true, "m", true, true)
				lx += w
		# Stance picks (every row). Active = the three options, with the hovered one marked.
		# Locked = the confirmed stance + chip. Pending = dashes.
		if active:
			var sx := x0 + 178
			for j in 3:
				var k: String = ORDER[j]
				var off: bool = int(pl.avail[k]) <= 0
				var picked: bool = (j == int(pl.sel) and not off)
				var lab: String = NAME[k]
				var w := 30.0
				if picked:
					solid(P([sx, ry + 2, sx + w - 2, ry + 2, sx + w - 4, ry + 16, sx - 2, ry + 16]), AMBER)
					t2(sx + w / 2 - 1, ry + 9, lab, 11, INK, true, "m", false, true)
				else:
					t2(sx + w / 2 - 1, ry + 9, lab, 11, DIMT if off else Color.WHITE, true, "m", not off, true)
				sx += w
			# No stat chip on the active row: the three stance labels already fill the width.
		elif locked:
			var k: String = String(slots[i]) if slots[i] != null else ""
			if k != "":
				t2(x0 + 178, ry + 9, NAME[k], 12, Color.WHITE, true, "l", true, true)
				chip(x1 - 8, ry + 8, TAG[k], STANCE[k], false)
		else:
			t2(x0 + 178, ry + 9, "--  --  --", 12, TODO, false, "l", false, true)
	t2(x0 + 9, y1 - 16, "Line set. Enter to lock now" if ph >= 3 else "Line locks at turn-in", 10, SUB, true)
	t2(x1 - 10, y1 - 16, "Enter SET  Bksp BACK", 10, SUB, false, "r")
