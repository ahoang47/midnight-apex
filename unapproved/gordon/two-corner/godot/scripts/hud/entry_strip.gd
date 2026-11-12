## entry strip, bottom left (post_v5.py:98-111)
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var pl: Dictionary = st.plan
	var x0 := 14.0; var y0 := 430.0
	var poly := cut_panel(x0, y0, x0 + 188, y0 + 36, 6); semi(poly, PANEL); outline(poly, EDGE)
	t2(x0 + 8, y0 + 3, "ENTRY", 10, SUB, true)
	var chosen: String = pl.entry if pl.entry != "" else (ORDER[int(pl.sel)] if int(pl.phase) == 0 else "")
	# lanes in on-screen order (Austin 2026-11-11: Left / Right move the Entry lane the way the road shows it):
	# right corner OUT MID IN as post_v5.py:98, left corner mirrored to IN MID OUT
	var order: Array = ["D", "S", "A"] if String(st.get("dir", "R")) == "L" else ORDER
	for i in 3:
		var k: String = order[i]; var cx := x0 + 36 + i * 58; var ry := y0 + 19
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
