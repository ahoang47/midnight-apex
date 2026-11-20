## B.5b line-lock timer, top left (post_lsc.py:50-58): 17 segments; after the lock 'SET' with every segment lit pale
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var locked: bool = st.phase == "TIMING"
	lpanel(14, 12, 192, 57); t2(23, 16, "LINE LOCK", 13, L_WHITE, false, "l", true, false, true)
	var off: bool = bool(st.get("no_timer", false)) and not locked   # TOUGE debug (Austin t119u): timer disabled
	var on := 17 if (locked or off) else ceili(17.0 * float(st.left) / float(st.total))
	if locked: t2(183, 18, "SET", 19, L_WHITE, false, "r")
	elif off: t2(183, 18, "OFF", 19, L_DIM, false, "r")
	else: t2(183, 18, "%04.1fs" % float(st.left), 19, L_AMBER, false, "r")
	for j in 17:
		solid(P([24 + j * 9, 43, 30 + j * 9, 43, 28 + j * 9, 50, 22 + j * 9, 50]), L_EDGE_L if locked else (L_AMBER if j < on else L_SEG_OFF))
