## main menu: approved V3 logo (art/logo/final) + 9-slice list. Selection colour = car head glow #FFF2CC (B.2), never a stance colour.
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var m: Dictionary = st.menu
	var logo: Texture2D = hud.logo
	draw_texture(logo, Vector2(roundi(320 - logo.get_width() / 2.0), 52))
	var items: Array = m.items
	var h: int = 16 + items.size() * 16
	box(200, 146, 240, h)
	for i in items.size():
		var sel: bool = i == int(m.sel); var y: int = 155 + i * 16
		if sel: rect(206, y - 3, 228, 14, Color("#30263F"))
		var label: String = items[i]
		if label == "SEED": label = "SEED  %s%s" % [m.seed_text if m.seed_text != "" else "RANDOM", "_" if sel and m.blink else ""]
		text(216, y, ("> " if sel else "  ") + label, Color("#FFF2CC") if sel else Color("#ADADC8"))
	center(320, 146 + h + 8, [["Up/Down select  Enter confirm", Color("#ADADC8")]])
	center(320, 146 + h + 19, [["on SEED: 0-9 type  Bksp delete  (empty = random)", Color("#ADADC8")]])
	box(4, 450, 196, 26); text(9, 454, "two-corner engine test"); text(9, 464, "pin " + String(m.commit))
