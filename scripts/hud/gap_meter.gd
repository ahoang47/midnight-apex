## gap / lead meter (the node's position is the meter's top-left). TOUGE passing (sim 5c79dea, Austin 2026-11-20): no roles, so
## the meter shows the whole race: the order on screen (st.order = who is ahead after the phases shown, the same order the cars
## are drawn in) and the running gap / share lead after those phases (st.gap / st.lead). Bar: right (blue) = you are ahead.
## Two-corner layout kept when st.order is absent.
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var x: float = origin().x; var y: float = origin().y
	var lead: float = st.lead; var gap: float = st.gap
	box(x, y, 200, 40); var cx := x + 100
	var order: String = String(st.get("order", ""))
	if order == "":
		var pos := "1st" if lead > 0 else ("2nd" if lead < 0 else "TIE")
		center(cx, y + 4, [["%s GAP %s%.3f lead %s%.3f" % [pos, "+" if gap >= 0 else "", gap, "+" if lead >= 0 else "", lead], WHITE]])
	else:
		var ahead := order == "player"
		center(cx, y + 4, [["1ST" if ahead else "2ND", Color("#3CC8FF") if ahead else Color("#FF9C3C")], ["  gap %s%.3f" % ["+" if gap >= 0 else "", gap], WHITE]])
	rect(cx - 90, y + 15, 180, 6, Color("#9597AD")); rect(cx - 89, y + 16, 178, 4, Color("#161C2A"))
	var w: int = mini(89, roundi(absf(lead) * 89.0 * 2.5))
	if lead > 0: rect(cx, y + 16, w, 4, Color("#3CC8FF"))
	elif lead < 0: rect(cx - w, y + 16, w, 4, Color("#FF3C8C"))
	rect(cx, y + 13, 1, 10, Color.WHITE)
	text(cx - 90, y + 26, "RIVAL"); text(cx + 90 - tw("YOU"), y + 26, "YOU")
