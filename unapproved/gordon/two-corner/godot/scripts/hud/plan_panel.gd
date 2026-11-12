## Combined PLAN THE LINE panel, lower right (Arthur line-preview pass 4 / 9a83828, Austin approved as build reference).
## Adapted from unapproved/arthur/mockups/line_preview/godot/scripts/hud/plan_panel.gd into Gordon's tree.
## Narrower and further right/down so it clears the chase-camera MX5.
## Every stance-selection row (Entry, Apex, Exit) uses corner-relative lane chips
## "IN · EN" / "MID · HAN" / "OUT · POW" (Austin via Arthur, 2026-11-12).
@tool
extends "res://scripts/hud/hud_panel.gd"

## Slanted lane+stat chip with a hard plate-style frame (Arthur c838466; Austin: "The chips should be framed.").
## Highlight fill stays inside the frame. Pixel-hard, no AA.
func frame_lane_chip(lx: float, ry: float, w: float, selected: bool, active: bool, dim: bool) -> PackedVector2Array:
	var pts := P([lx, ry + 1, lx + w - 2, ry + 1, lx + w - 4, ry + 24, lx - 2, ry + 24])
	if selected:
		solid(pts, AMBER if active else EDGE)
	else:
		solid(pts, Color8(14, 16, 36) if dim else Color8(20, 24, 52))
	# Bold 2 px frame: outer ink, inner edge, then a hard bevel.
	outline(pts, INK)
	var inner := P([lx + 1, ry + 2, lx + w - 3, ry + 2, lx + w - 5, ry + 23, lx - 1, ry + 23])
	outline(inner, EDGE if not dim else EDGE_D)
	var hi := Color8(160, 180, 230, 220) if selected else Color8(120, 140, 190, 200)
	var sh := Color8(0, 0, 0, 200)
	draw_line(pts[0] + Vector2(1, 1), pts[1] + Vector2(-1, 1), hi, 1.0)
	draw_line(pts[0] + Vector2(1, 1), pts[3] + Vector2(1, -1), Color8(hi.r8, hi.g8, hi.b8, 180), 1.0)
	draw_line(pts[1] + Vector2(-1, 1), pts[2] + Vector2(-1, -1), sh, 1.0)
	draw_line(pts[2] + Vector2(-1, -1), pts[3] + Vector2(1, -1), Color8(0, 0, 0, 220), 1.0)
	return pts

func paint() -> void:
	var pl: Dictionary = st.plan
	# Pass 4 coords (640 design units): slimmer and further right/down so the chase MX5 is not covered.
	var box: Array = [424.0, 372.0, 636.0, 479.0]
	if st.has("preview_panel") and (st.preview_panel as Array).size() >= 4:
		box = st.preview_panel
	var x0 := float(box[0]); var y0 := float(box[1]); var x1 := float(box[2]); var y1 := float(box[3])
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
	# On-screen lane order: left corner IN MID OUT, right corner OUT MID IN. Same mapping on every row.
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
		t2(nx, ry + 8, PH[i], 12, ncol, true, "l", not active, true, true)
		if locked:
			check(nx + sw(PH[i], 12, true, true) + 4, ry + 6, CHECK_GREEN)
		if active or locked:
			var chosen_lane: String = ""
			if locked:
				if i == 0 and String(pl.get("entry", "")) != "":
					chosen_lane = String(pl.entry)
				elif slots[i] != null:
					chosen_lane = String(slots[i])
			elif active:
				chosen_lane = ORDER[int(pl.sel)] if int(pl.sel) >= 0 else ""
			var lx := x0 + 54
			var cw := 38.0
			for k in lanes:
				var lab: String = lane_stat(k)
				var off: bool = active and int(pl.avail[k]) <= 0
				var selected: bool = (k == chosen_lane and not off)
				var dim: bool = locked or off
				frame_lane_chip(lx, ry, cw, selected, active, dim and not selected)
				if selected:
					t2(lx + cw / 2 - 2, ry + 12, lab, 8, INK, true, "m", false, true)
					if locked:
						check(lx + cw - 7, ry + 3, INK)
				else:
					t2(lx + cw / 2 - 2, ry + 12, lab, 8, DIMT if dim else SUB, true, "m", true, true)
				lx += cw + 2.0
		else:
			t2(x0 + 70, ry + 9, "--  --  --", 12, TODO, false, "l", false, true)
	t2(x0 + 8, y1 - 12, "Line set. Enter to lock now" if ph >= 3 else "Line locks at turn-in", 9, SUB, true)
	t2(x1 - 8, y1 - 12, "Enter SET  Bksp BACK", 9, SUB, false, "r")
