## TOUGE (Gordon, touge-race): on-screen touch buttons (Austin t109u: every input by tap, phone-sized). main.gd builds the list
## each frame (_touch_buttons) and hit-tests taps against the same rects, so what is drawn is what is tappable.
## Item: {id, r: [x, y, w, h] design px, label, sub?, col?, on (enabled), sel (highlight)}. Minimum height 36 design px.
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	for b in st.get("buttons", []):
		var r: Array = b.r; var x: float = r[0]; var y: float = r[1]; var w: float = r[2]; var h: float = r[3]
		var on: bool = b.get("on", true); var sel: bool = b.get("sel", false)
		var col: Color = b.get("col", L_EDGE_L)
		var p := cut_panel(x, y, x + w, y + h, 5.0)
		semi(p, PANEL)
		if b.has("col") and on: solid(cut_panel(x + 2, y + 2, x + w - 2, y + h - 2, 4.0), dimc(col, 0.85 if sel else 0.55))
		outline(p, L_AMBER if sel else (col if on else L_EDGE))
		var lc: Color = (L_INK if (b.has("col") and col == STANCE["H"]) else L_WHITE) if on else L_DIMMER
		var sz: int = int(b.get("sz", 13))
		if b.has("sub"):
			t2(x + w / 2, y + h / 2 - 6, String(b.label), sz, lc, false, "m", true, true, true)
			t2(x + w / 2, y + h / 2 + 7, String(b.sub), 9, lc if on else L_DIMMER, false, "m", true, true, false)
		else:
			t2(x + w / 2, y + h / 2, String(b.label), sz, lc, false, "m", true, true, true)
		if not on: draw_line(Vector2(x + 4, y + h - 4), Vector2(x + w - 4, y + 4), Color8(150, 150, 160), 1.0)
