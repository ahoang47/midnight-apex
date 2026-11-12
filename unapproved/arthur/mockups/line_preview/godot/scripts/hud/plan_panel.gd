## PLAN THE LINE, lower right (post_v5.py:112-131). Options are '<Stance> <phase>'; the 6-card hand only decides availability.
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var pl: Dictionary = st.plan
	var x0 := 404.0; var y0 := 328.0; var x1 := 628.0; var y1 := 468.0
	var body := cut_panel(x0, y0, x1, y1, 9)
	semi(body, PANEL); plate_finish(body, x0, y0, x1, y1)
	outline(body, EDGE); outline(cut_panel(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 8), EDGE_D)
	var tab := P([x0, y0 - 15, x0 + 108, y0 - 15, x0 + 119, y0, x0, y0]); solid(tab, AMBER); outline(tab, INK)
	t2(x0 + 7, y0 - 14, "PLAN THE LINE", 12, INK, false, "l", false, false, true)
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
