## Pause menu (Austin pt137u, desktop Escape only; no touch button). Same plate style as the finish panel: dimmed screen,
## cut panel, amber bar on the selected row. State: hud.pause_st = {"items": [...], "sel": i} (main.gd _pause_*).
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var ps = hud.get("pause_st")
	if ps == null or (ps as Dictionary).is_empty(): return
	draw_rect(Rect2(0, 0, 640, 480), Color(0, 0, 0, 0.45))
	var items: Array = ps.items
	var y1 := 196.0 + 30.0 + items.size() * 18.0 + 22.0
	var pl := cut_panel(200, 196, 440, y1, 8); semi(pl, PANEL); outline(pl, EDGE)
	t2(320, 204, "PAUSED", 16, Color("#FFF2CC"), false, "m", true, false, true)
	for i in items.size():
		var sel: bool = i == int(ps.sel); var y := 230.0 + i * 18
		if sel: semi(P([212, y - 2, 428, y - 2, 424, y + 14, 208, y + 14]), AMBER, 200 / 255.0)
		t2(222, y, String(items[i]), 12, INK if sel else EDGE, false, "l", not sel)
	t2(320, y1 - 18, "Up/Down + Enter  ·  Esc resume", 10, SUB, true, "m")
