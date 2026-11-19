## after-turn result line + "Press Enter to continue  N" with its countdown (display.json playback_flow.continue_s, PLACEHOLDER;
## the game auto-continues at 0)
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var r: Dictionary = st.result
	if r.is_empty(): return
	var ph := []
	for j in 3:
		var v = (r.qte_in as Array)[j]
		ph.append("%s %s" % [["E", "A", "X"][j], "--" if v == null else "%.2f" % float(v)])
	var s := "QTE %s  avg %.3f%s%s" % ["  ".join(ph), r.q_time, " [auto]" if r.autofilled else "", "  LEAD CHANGE" if st.leader_changed else ""]
	# Under the tie-gap bar (220,98 200x40), which moved under the mirror in the B.5d pass.
	t2(220, 144, s, 10, SUB, true)
	if int(st.reveal) >= 3:
		var n := int(ceilf(float(st.get("cont_left", 0.0))))
		t2(220, 157, "Press Enter to %s  %d" % ["finish" if st.last_corner else "continue", n], 11, EDGE, true)
