## TOUGE (Gordon, touge-race): turnout after turn 5. The cars roll into the small parking area (they slow, never stop), swap
## lead and chase, and roll out. Turns 1-5 are banked; the gap meter starts again at even for turns 6-10.
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var t = st.get("turnout")
	if t == null: return
	lpanel(170, 150, 470, 214, L_AMBER)
	t2(320, 156, "TURNOUT  ·  SWAP", 16, L_AMBER, false, "m", true, false, true)
	t2(320, 178, "you %s turns %d-%d" % ["LEAD" if t.new_role == "lead" else "CHASE", int(t.from), int(t.n)], 11, L_WHITE, false, "m", true, false, true)
	var b: float = float(t.banked)
	t2(320, 194, "turns 1-%d banked: %s%.3f  (heat carries over)" % [int(t.from) - 1, "+" if b >= 0.0 else "", b], 10, SUB, false, "m", true, false, false)
