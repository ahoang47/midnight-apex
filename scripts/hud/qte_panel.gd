## per-phase timing QTE during playback (shots10, moved into playback in shots11; no Arthur frame exists for it, so layout, labels and sizes are PLACEHOLDERS on the B.5a/B.5b
## palette and the 2x grid). Bar = the sweep in ms (display.json qte_sweep): lead-in, then the zone (amber; width from the sim's
## qte_zone_width at the race's fixed r), cursor = white. Score = round_qte_score(max(0, 1 - |e| / (zone/2))) (3 decimals, pin c3ffc41); past the far edge = unplayed (0).
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var q: Dictionary = st.qte; var i: int = int(q.i)
	var x0 := 150.0; var y0 := 344.0; var x1 := 490.0; var y1 := 420.0
	lpanel(x0, y0, x1, y1, L_EDGE_L, 7)
	t2(x0 + 8, y0 + 5, "%s QTE" % PHN[i], 12, L_AMBER, true)
	t2(x1 - 8, y0 + 6, "%s at the zone" % String(q.key), 10, SUB, false, "r")
	# the phase timer (shots11): the cars hold at this phase's point until it runs out (PLACEHOLDER layout)
	t2(320, y0 + 5, "%.1fs" % float(q.get("t_left", 0.0)), 12, L_WHITE, false, "m")
	# phase row: ENTRY / APEX / EXIT with the locked stance and the score so far
	var line: String = q.line
	for j in 3:
		var cx := x0 + 60 + j * 110.0; var y := y0 + 22
		if j == i: outline(cut_panel(cx - 46, y - 3, cx + 46, y + 15, 4), L_AMBER)
		if line.length() == 3: lchip(cx - 44, y - 1, line[j], 40)
		var r = q.res[j]
		var txt := "- -"; var col := L_DIMMER
		if j < i or (j == i and q.seg == "show"):
			if r == null: txt = "0 unplayed"; col = L_DIM
			else: txt = "%.3f" % float(r); col = L_WHITE
		t2(cx + 2, y + 6, txt, 11, col, false, "l", true, true)
	# the sweep bar
	var bx0 := x0 + 12.0; var bx1 := x1 - 12.0; var by := y0 + 46.0; var bw := bx1 - bx0
	var k: float = bw / float(q.bar_ms)
	rect(bx0, by, bw, 8, L_SEG_OFF); outline(P([bx0, by, bx1, by, bx1, by + 8, bx0, by + 8]), L_EDGE)
	var zx0 := roundf(bx0 + float(q.zone[0]) * k); var zx1 := roundf(bx0 + float(q.zone[1]) * k)
	rect(zx0, by, maxf(1.0, zx1 - zx0), 8, L_AMBER); outline(P([zx0, by, zx1, by, zx1, by + 8, zx0, by + 8]), L_INK)
	rect(roundf((zx0 + zx1) / 2.0), by - 2, 1, 12, L_INK)
	var cur = null
	if q.seg == "sweep": cur = float(q.ms)
	elif q.seg == "show" and q.press[i] != null: cur = float(q.press[i])
	if cur != null:
		var cx := roundf(bx0 + float(cur) * k)
		rect(cx - 2, by - 5, 4, 18, L_INK); rect(cx - 1, by - 4, 2, 16, L_WHITE)
	if q.seg == "show":
		var r = q.res[i]
		if r == null: t2(320, y0 + 60, "UNPLAYED  0", 12, L_DIM, true, "m")
		else: t2(320, y0 + 60, ("HIT %.3f" if float(r) > 0.0 else "MISS %.3f") % float(r), 12, L_AMBER if float(r) > 0.0 else L_DIM, true, "m")
	else:
		t2(320, y0 + 60, "zone %d ms" % roundi(float(q.zone[1]) - float(q.zone[0])), 10, SUB, false, "m")
