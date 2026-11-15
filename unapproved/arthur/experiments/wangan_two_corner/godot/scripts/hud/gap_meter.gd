## gap / lead meter, bottom centre (the node's position is the meter's top-left; was _gap_meter(203, 428))
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var x: float = origin().x; var y: float = origin().y
	var lead: float = st.lead; var gap: float = st.gap
	var pos := "1st" if lead > 0 else ("2nd" if lead < 0 else "TIE")
	box(x, y, 200, 40); var cx := x + 100
	center(cx, y + 4, [["%s GAP %s%.3f lead %s%.3f" % [pos, "+" if gap >= 0 else "", gap, "+" if lead >= 0 else "", lead], WHITE]])
	rect(cx - 90, y + 15, 180, 6, Color("#9597AD")); rect(cx - 89, y + 16, 178, 4, Color("#161C2A"))
	var w: int = mini(89, roundi(absf(lead) * 89.0 * 2.5))
	if lead > 0: rect(cx, y + 16, w, 4, Color("#3CC8FF"))
	elif lead < 0: rect(cx - w, y + 16, w, 4, Color("#FF3C8C"))
	rect(cx, y + 13, 1, 10, Color.WHITE); text(cx - 90, y + 26, "RIVAL"); text(cx + 90 - tw("YOU"), y + 26, "YOU")
