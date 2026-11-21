## TOUGE check (Austin pt137u item 15, pic 1): the lattice (cut) side must be the uphill side and the guardrail / drop side the
## downhill side wherever the ground is known, i.e. where another leg of the course runs alongside (within drop_lat_m, >= 40 m
## along the course) higher or lower by >= drop_dy_m. For every 2 m course sample over the dressed range: FAIL if the drop side
## faces a HIGHER leg or the lattice side faces a LOWER one ("lattice on both sides" = a cut facing down the hill), unless the
## ground really rises (or falls) on both sides. Also: each turn's scroll straight has the course's side over its approach.
## Authored ground (Austin 2026-11-20, Arthur's terrain): at every 2 m sample the ground the assets put 3 m past each road edge
## (touge_env.ground_y on the *_col proxies) must agree with the side: the drop / guardrail side at or below the road (+0.3 m;
## a deck lip with no ground under it also counts), the lattice side's cut above it (+0.5 m). Skipped: 4 m round each drop-side
## flip (the cut runs 2 m past it onto a wing wall), the turnout lot's inside (its floor).
## Usage: godot --headless --path . -s tools/touge_race/drop_side_check.gd [-- --config CFG.json] [--display DISPLAY.json]
extends SceneTree
const TrackRoad = preload("res://scripts/track_road.gd")
const TougeEnv = preload("res://scripts/touge_env.gd")
func _initialize() -> void:
	var ua := OS.get_cmdline_user_args()
	var dpath := "res://spec/display.json"
	if ua.has("--display"): dpath = ua[ua.find("--display") + 1]
	var disp: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(dpath))
	var cfgp := "res://spec/race_config.json"
	if ua.has("--config"): cfgp = ua[ua.find("--config") + 1]
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(cfgp))
	var tr: Dictionary = TrackRoad.build_course(disp, cfg)
	var c = tr.course; var T: Dictionary = disp.districts.touge.terrain
	var lat: float = maxf(float(T.get("drop_lat_m", 60.0)), 60.0); var dym: float = float(T.get("drop_dy_m", 1.5))   # the ground test itself does not switch off with the rule
	var step := 2.0; var cs := []; var ys := []; var s := -60.0
	while s <= c.length + 60.0: cs.append(c.at(s)); ys.append(c.elev(s, 0.0)); s += step
	var bad := []; var checked := 0
	for i in cs.size():
		var p: Dictionary = cs[i]; var nx: float = -float(p.tz); var nz: float = float(p.tx)
		var near := {-1.0: [1e9, 0.0, 0.0], 1.0: [1e9, 0.0, 0.0]}
		for j in cs.size():
			if absi(j - i) * step < 40.0: continue
			var vx: float = float(cs[j].x) - float(p.x); var vz: float = float(cs[j].z) - float(p.z)
			if absf(vx * float(p.tx) + vz * float(p.tz)) > 0.5 * step + 0.05: continue
			var dl: float = vx * nx + vz * nz
			if absf(dl) > lat: continue
			var sd := 1.0 if dl > 0.0 else -1.0
			if absf(dl) < float(near[sd][0]): near[sd] = [absf(dl), float(ys[j]) - float(ys[i]), -60.0 + j * step]
		var si: float = -60.0 + i * step; var drop: float = c.drop_at(si)
		var dyd: float = near[drop][1] if float(near[drop][0]) <= lat else 0.0       # neighbour on the drop side
		var dyl: float = near[-drop][1] if float(near[-drop][0]) <= lat else 0.0     # neighbour on the lattice side
		if float(near[drop][0]) <= lat or float(near[-drop][0]) <= lat: checked += 1
		var both_up := dyd >= dym and dyl >= dym; var both_down := dyd <= -dym and dyl <= -dym
		if (dyd >= dym and not both_up) or (dyl <= -dym and not both_down):
			bad.append("s=%.0f drop=%d drop-side leg dy=%.1f (s %.0f) lattice-side leg dy=%.1f (s %.0f)" % [si, drop, dyd, near[drop][2], dyl, near[-drop][2]])
	var sbad := 0
	for i in tr.views.size():
		var v = tr.views[i]; var sm: float = float(v.off) + float(v.S) * 0.5
		if float(tr.straights[i].drop_const) != c.drop_at(float(v.off) + 1.0) or c.drop_at(float(v.off) + 1.0) != c.drop_at(float(v.off) + float(v.S) - 1.0):
			sbad += 1; print("DROP_SIDE straight %d drop_const %d != course %d..%d" % [i + 1, tr.straights[i].drop_const, c.drop_at(float(v.off) + 1.0), c.drop_at(float(v.off) + float(v.S) - 1.0)])
	var abad := []; var achk := 0; var nocut := []
	var Wr: float = float(disp.road_half_m) if disp.has("road_half_m") else float(disp.lane_width_m) * 1.5 + 1.0
	var lot: Dictionary = tr.get("turnout", {})
	s = -60.0
	while s <= c.length + 60.0:
		var near_flip := false
		for k in range(1, c.drop_runs.size()): near_flip = near_flip or absf(s - float(c.drop_runs[k][0])) < 4.0
		if not near_flip:
			var dr: float = c.drop_at(s)
			var g := {}
			for sd in [dr, -dr]:
				var q: Dictionary = c.point(s, sd * (Wr + 3.0)); var ry: float = c.elev(s, sd * Wr)
				var gy: float = TougeEnv.ground_y(float(q.x), float(q.z), ry + 12.0, 40.0)
				g[sd] = NAN if is_nan(gy) else gy - ry
			var up_d: bool = not is_nan(g[dr]) and g[dr] > 0.3; var up_l: bool = not is_nan(g[-dr]) and g[-dr] >= 0.5
			achk += 1
			# a cut on BOTH sides (the turn-4 underpass canyon, s 1036-1104) is a valley-floor road, not a wrong side
			if up_d and not up_l: abad.append("s=%.0f drop side (%s) ground %.2f m ABOVE the road edge" % [s, "R" if dr > 0 else "L", g[dr]])
			var lot_in: bool = not lot.is_empty() and s > float(lot.s0) - 2.0 and s < float(lot.s1) + 2.0
			if not up_l and not lot_in: nocut.append(s)   # no cut on the lattice side: a bridge / deck (no lattice there: touge_dressing _cut_table)
			if not up_l and not lot_in and not is_nan(g[-dr]) and g[-dr] > 0.3: abad.append("s=%.0f lattice side (%s) ground %.2f m: a low cut" % [s, "R" if -dr > 0 else "L", g[-dr]])
		s += step
	for b in abad: print("DROP_SIDE authored bad ", b)
	var nr := []   # no-cut stretches as ranges
	for v in nocut:
		if nr.is_empty() or float(v) - float(nr[-1][1]) > step + 0.01: nr.append([v, v])
		else: nr[-1][1] = v
	print("DROP_SIDE_AUTHORED no cut on the lattice side (bridges / decks; no lattice placed): ", ", ".join(nr.map(func(r): return "%.0f-%.0f" % [r[0], r[1]])))
	print("DROP_SIDE_AUTHORED samples=%d bad=%d %s" % [achk, abad.size(), "PASS" if abad.is_empty() else "FAIL"])
	var runs := []
	for r in c.drop_runs: runs.append("%.0f:%s" % [maxf(float(r[0]), -60.0), "R" if float(r[1]) > 0.0 else "L"])
	print("DROP_SIDE runs ", " ".join(runs))
	for b in bad.slice(0, 12): print("DROP_SIDE bad ", b)
	print("DROP_SIDE_CHECK samples=%d with_neighbour=%d bad=%d straight_mismatch=%d %s" % [cs.size(), checked, bad.size(), sbad, "PASS" if bad.is_empty() and sbad == 0 and abad.is_empty() else "FAIL"])
	quit(0 if bad.is_empty() and sbad == 0 and abad.is_empty() else 1)
