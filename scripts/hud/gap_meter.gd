## gap / lead meter (the node's position is the meter's top-left). TOUGE (Gordon, touge-race): no visible passing, so the meter
## carries the result. It shows THIS half (turns 1-5, or 6-10 after the turnout swap; race_core seg_*): chasing = how close you
## are to the rival ahead, leading = how far the rival is behind. Bar: right (blue) = you are winning this half.
## Two-corner layout kept when st.role is absent.
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var x: float = origin().x; var y: float = origin().y
	var lead: float = st.lead; var gap: float = st.gap
	box(x, y, 200, 40); var cx := x + 100
	var role: String = String(st.get("role", ""))
	if role == "":
		var pos := "1st" if lead > 0 else ("2nd" if lead < 0 else "TIE")
		center(cx, y + 4, [["%s GAP %s%.3f lead %s%.3f" % [pos, "+" if gap >= 0 else "", gap, "+" if lead >= 0 else "", lead], WHITE]])
	else:
		var tag := "CHASING" if role == "chase" else "LEADING"
		var tc := Color("#FF9C3C") if role == "chase" else Color("#3CC8FF")
		center(cx, y + 4, [[tag, tc], ["  gap %s%.3f" % ["+" if gap >= 0 else "", gap], WHITE]])
	rect(cx - 90, y + 15, 180, 6, Color("#9597AD")); rect(cx - 89, y + 16, 178, 4, Color("#161C2A"))
	var w: int = mini(89, roundi(absf(lead) * 89.0 * 2.5))
	if lead > 0: rect(cx, y + 16, w, 4, Color("#3CC8FF"))
	elif lead < 0: rect(cx - w, y + 16, w, 4, Color("#FF3C8C"))
	rect(cx, y + 13, 1, 10, Color.WHITE)
	if role == "chase": text(cx - 90, y + 26, "DROPPING"); text(cx + 90 - tw("CLOSING"), y + 26, "CLOSING")
	elif role == "lead": text(cx - 90, y + 26, "CAUGHT"); text(cx + 90 - tw("PULLING AWAY"), y + 26, "PULLING AWAY")
	else: text(cx - 90, y + 26, "RIVAL"); text(cx + 90 - tw("YOU"), y + 26, "YOU")
