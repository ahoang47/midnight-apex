## Combined PLAN THE LINE panel, lower right (Arthur line-preview pass 4 / 9a83828, Austin approved as build reference).
## Adapted from unapproved/arthur/mockups/line_preview/godot/scripts/hud/plan_panel.gd into Gordon's tree.
## Narrower and further right/down so it clears the chase-camera MX5. Lane chips read "OUT · POW".
## Entry still has a single cursor (lane and stance are 1:1); both chip groups highlight the same pick.
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var pl: Dictionary = st.plan
	# Pass 4 coords (640 design units): slimmer and further right/down so the chase MX5 is not covered.
	var box: Array = [424.0, 372.0, 636.0, 479.0]
	if st.has("preview_panel") and (st.preview_panel as Array).size() >= 4:
		box = st.preview_panel
	var x0 := float(box[0]); var y0 := float(box[1]); var x1 := float(box[2]); var y1 := float(box[3])
	var body := cut_panel(x0, y0, x1, y1, 9)
	semi(body, PANEL)
	outline(body, EDGE)
	outline(cut_panel(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 8), EDGE_D)
	var tab := P([x0 + 22, y0 - 14, x0 + 118, y0 - 14, x0 + 128, y0, x0 + 22, y0])
	solid(tab, AMBER)
	outline(tab, INK)
	t2(x0 + 29, y0 - 14, "PLAN THE LINE", 12, INK, false, "l", false, false)
	var ph: int = int(pl.phase)
	var slots: Array = st.get("slots", [null, null, null])
	# On-screen lane order: left corner IN MID OUT, right corner OUT MID IN.
	var lanes: Array = ["E", "H", "P"] if String(st.get("dir", "R")) == "L" else ORDER
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
		var nx := x0 + (20 if active else 10)
		var ncol: Color = INK if active else (EDGE if locked else TODO)
		t2(nx, ry + 8, PH[i], 11, ncol, true, "l", not active, true)
		if locked:
			check(nx + sw(PH[i], 11, true) + 4, ry + 6, CHECK_GREEN)
		if i == 0:
			# Entry row: three lane chips "IN · EN" / "MID · HAN" / "OUT · POW"
			var chosen_lane: String = ""
			if locked and String(pl.entry) != "":
				chosen_lane = String(pl.entry)
			elif active:
				chosen_lane = ORDER[int(pl.sel)] if int(pl.sel) >= 0 else ""
			var lx := x0 + 54
			for k in lanes:
				var lab: String = lane_stat(k)
				var cw := 38.0
				if k == chosen_lane:
					solid(P([lx, ry + 1, lx + cw - 2, ry + 1, lx + cw - 4, ry + 24, lx - 2, ry + 24]), AMBER if active else EDGE)
					t2(lx + cw / 2 - 2, ry + 12, lab, 8, INK, true, "m", false, true)
					if locked:
						check(lx + cw - 2, ry + 3, INK)
				else:
					t2(lx + cw / 2 - 2, ry + 12, lab, 8, DIMT if locked else SUB, true, "m", true, true)
				lx += cw
		# Apex / Exit: stance chips POW / HAN / EN. Entry also shows them, synced to the same cursor.
		if active:
			var sx := x0 + (170.0 if i == 0 else 66.0)
			# The slim panel can't fit stance chips next to three "OUT · POW" labels on Entry;
			# Entry shows only the lane chips. Apex / Exit show POW / HAN / EN.
			if i > 0:
				for j in 3:
					var k: String = ORDER[j]
					var off: bool = int(pl.avail[k]) <= 0
					var picked: bool = (j == int(pl.sel) and not off)
					var lab: String = NAME[k]
					var w := 26.0
					if picked:
						solid(P([sx, ry + 2, sx + w - 2, ry + 2, sx + w - 4, ry + 16, sx - 2, ry + 16]), AMBER)
						t2(sx + w / 2 - 1, ry + 9, lab, 11, INK, true, "m", false, true)
					else:
						t2(sx + w / 2 - 1, ry + 9, lab, 11, DIMT if off else Color.WHITE, true, "m", not off, true)
					sx += w
		elif locked:
			var k: String = String(slots[i]) if slots[i] != null else ""
			if k != "":
				if i == 0:
					pass  # Entry locked state is the chosen lane chip above
				else:
					chip(x1 - 8, ry + 8, NAME[k], STANCE[k], false)
		else:
			t2(x0 + 70, ry + 9, "--  --  --", 12, TODO, false, "l", false, true)
	t2(x0 + 8, y1 - 12, "Line set. Enter to lock now" if ph >= 3 else "Line locks at turn-in", 9, SUB, true)
	t2(x1 - 8, y1 - 12, "Enter SET  Bksp BACK", 9, SUB, false, "r")
