## TOUGE (Gordon, touge-race): the parked start. Both cars sit side by side on the start line; "Lead or chase first?".
## LEAD = mouse (pull away from the rival), CHASE = cat (close in on the rival). Turns 1-5 in that role, then the two swap at
## the turnout and run turns 6-10 the other way round. Buttons: touch_buttons.gd; keyboard Left / Right + Enter.
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var r = st.get("role_prompt")
	if r == null: return
	lpanel(150, 300, 490, 470, L_EDGE_L)
	t2(320, 307, "LEAD OR CHASE FIRST?", 16, L_AMBER, false, "m", true, false, true)
	t2(320, 328, "turns 1-%d in that role, swap at the turnout, turns %d-%d the other way" % [int(r.swap), int(r.swap) + 1, int(r.n)], 9, SUB, false, "m", true, false, false)
	t2(237, 424, "pull away from the rival", 9, L_DIM, false, "m", true, false, false)
	t2(403, 424, "close in on the rival", 9, L_DIM, false, "m", true, false, false)
	t2(320, 446, "%s  vs  %s" % [String(r.you), String(r.rival)], 10, L_EDGE_L, false, "m", true, false, true)
