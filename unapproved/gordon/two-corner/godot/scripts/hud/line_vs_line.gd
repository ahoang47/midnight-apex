## B.5a LINE LOCKED panel (post_clash.py:62-85): YOU and RIVAL rows face up from the start, amber outline on the column
## being played, RESULT fills in as each phase plays. k = phase being played (-1 = playback over: every result shown).
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var k: int = int(st.play_phase) if st.phase == "TIMING" else -1
	var you: String = st.line; var riv: String = st.rline; var outs: Array = st.outs
	if you.length() < 3 or riv.length() < 3: return
	var x0 := 120.0; var y0 := 12.0; var x1 := 466.0; var y1 := 100.0
	lpanel(x0, y0, x1, y1, L_EDGE_L, 8)
	t2(x0 + 8, y0 + 6, "LINE LOCKED", 12, L_AMBER, true)
	var cols := [241.0, 331.0, 421.0]
	for i in 3:
		var cx: float = cols[i]; var cur := i == k
		if cur:
			outline(cut_panel(cx - 42, y0 + 3, cx + 42, y1 - 3, 5), L_AMBER)
			solid(P([cx - 30, y0 + 9, cx - 25, y0 + 13, cx - 30, y0 + 17]), L_AMBER)
		t2(cx, y0 + 13, PHN[i], 11, L_AMBER if cur else (L_WHITE if (k < 0 or i < k) else L_DIM), false, "m", true, true)
	var rows := [["YOU", you, 30.0], ["RIVAL", riv, 50.0]]
	for rw in rows:
		var dy: float = rw[2]
		t2(x0 + 8, y0 + dy + 1, rw[0], 11, L_WHITE if rw[0] == "YOU" else L_DIM)
		for i in 3: lchip(cols[i] - 24, y0 + dy, String(rw[1])[i])
		for i in 2: t2(cols[i] + 45, y0 + dy + 7, ">", 10, L_DIMMER, false, "m", true, true)
	t2(x0 + 8, y0 + 71, "RESULT", 11, L_DIM)
	for i in 3:
		if (k < 0 or i <= k) and outs.size() == 3: lres(cols[i], y0 + 70, int(outs[i]))
		else: t2(cols[i], y0 + 77, "- -", 11, L_DIMMER, false, "m", true, true)
	draw_line(Vector2(x0 + 6, y0 + 25), Vector2(x1 - 8, y0 + 25), L_EDGE, 1.0)
