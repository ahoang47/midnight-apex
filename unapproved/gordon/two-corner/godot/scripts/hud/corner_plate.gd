## corner plate, top right (B.5b:261-262 / B.5a:269; post_lsc.py:60-73, post_clash.py:48-55): corner map + E / A / X stops
@tool
extends "res://scripts/hud/hud_panel.gd"
func paint() -> void:
	var pl: Dictionary = st.plate
	lpanel(476, 12, 628, 96); t2_fit(528, 16, String(pl.name), 16, L_WHITE, 622.0, false, true)
	var md: String = pl.mode; var k: int = int(pl.stop)
	var cur := -1; var ndone := 0
	match md:
		"VIEW": cur = k; ndone = k
		"LOCK": cur = 0; ndone = 3
		"QTE": cur = k; ndone = k
		"PLAY": cur = k; ndone = k
		_: cur = -1; ndone = 3
	var lab := "PLAY" if md in ["PLAY", "DONE"] else ("QTE" if md == "QTE" else "VIEW")
	t2(534, 40, lab, 9, L_DIM)
	t2(560, 38, "RESULT" if md == "DONE" else PHN[cur], 13, L_AMBER)
	if md in ["VIEW", "LOCK", "QTE"]:
		var lt := ["E", "A", "X"]
		for i in 3:
			var on_cur := i == cur; var dn := (md == "LOCK" and i > 0) or (md == "VIEW" and i < cur)
			t2(534 + i * 14, 58, lt[i], 10, L_AMBER if on_cur else (L_WHITE if dn else L_DIMMER))
	t2(534, 74, "PLAYBACK" if lab == "PLAY" else ("TIMING" if lab == "QTE" else "CAMERA STOP"), 9, L_DIM)   # 'QTE' / 'TIMING' labels: PLACEHOLDER
	# map: fit the path into x 486..526, y 28..90, forward = up
	var ic: Dictionary = pl.icon; var pts: Array = ic.pts
	var mn := Vector2(1e9, 1e9); var mx := Vector2(-1e9, -1e9)
	for v in pts: mn = Vector2(minf(mn.x, v.x), minf(mn.y, v.y)); mx = Vector2(maxf(mx.x, v.x), maxf(mx.y, v.y))
	var sc := minf(40.0 / maxf(mx.x - mn.x, 1.0), 58.0 / maxf(mx.y - mn.y, 1.0))
	var ctr := (mn + mx) / 2.0
	var f := func(v: Vector2) -> Vector2: return Vector2(506, 60) + (v - ctr) * sc
	var line := PackedVector2Array()
	for v in pts: line.append(f.call(v))
	draw_polyline(line, SOD, 3.0)
	var e: Vector2 = line[line.size() - 1]; var dvec: Vector2 = (e - line[line.size() - 2]).normalized(); var nv := Vector2(-dvec.y, dvec.x)
	solid(PackedVector2Array([e + dvec * 6, e - dvec * 4 + nv * 6, e - dvec * 4 - nv * 6]), SOD)
	for i in 3:
		var c: Vector2 = f.call(ic.stops[i])
		var dn := i < ndone and i != cur
		var dia := P([c.x, c.y - 5, c.x + 5, c.y, c.x, c.y + 5, c.x - 5, c.y])
		solid(dia, L_AMBER if i == cur else (L_WHITE if dn else L_TODO)); outline(dia, L_INK)
