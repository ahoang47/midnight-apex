## Line-preview mockup overlay (Arthur). IN / MID / OUT markers only; Gordon's file is not edited.
## lane markers over the turn-in point (post_v5.py:66-88): chosen = amber chevron, available = faint tick, none drawn = dark tick
## crossed out. Full-screen node: the markers follow the road (main.gd unprojects the lane points).
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var pl: Dictionary = st.plan
	if not st.has("lanes") or st.lanes == null: return
	var chosen: String = pl.entry if pl.entry != "" else (ORDER[int(pl.sel)] if int(pl.phase) == 0 else "")
	for k in ORDER:
		var v = st.lanes.get(k)
		if v == null: continue
		var x := roundf((v as Vector2).x); var y := roundf((v as Vector2).y)
		if k == chosen:
			var w := 26.0; var h := 15.0; var t := 8.0
			var mk := func(dy: float) -> PackedVector2Array: return P([x - w / 2, y - h + dy, x - w / 2 + t, y - h + dy, x, y - 4 + dy, x + w / 2 - t, y - h + dy, x + w / 2, y - h + dy, x, y + dy])
			solid(mk.call(3.0), AMBER_D); solid(mk.call(0.0), AMBER); outline(mk.call(3.0), INK); outline(mk.call(0.0), INK)
			draw_line(Vector2(x - w / 2 + 2, y - h + 1), Vector2(x - w / 2 + t - 1, y - h + 1), Color8(255, 236, 170), 1.0)
			t2(x, y - h - 9, LANE[k], 11, AMBER, false, "m", true, true)
		else:
			var w := 12.0; var h := 7.0; var t := 4.0
			var pts := P([x - w / 2, y - h, x - w / 2 + t, y - h, x, y - 3, x + w / 2 - t, y - h, x + w / 2, y - h, x, y])
			if int(pl.avail_entry[k]) <= 0:
				solid(pts, Color8(40, 42, 56)); outline(pts, Color8(70, 74, 92)); lock_x(x, y - 4, 4, dimc(STANCE.S, 0.7))
				t2(x, y - h - 8, LANE[k], 10, DIMT, false, "m", true, true)
			else:
				semi(pts, Color8(150, 170, 210)); t2(x, y - h - 8, LANE[k], 10, Color8(120, 135, 170), false, "m", true, true)
