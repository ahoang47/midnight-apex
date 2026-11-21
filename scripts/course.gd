@tool
## Continuous display track (Austin 2026-11-11 ~10 PM PT: "the two corners should be in the same district as part of a
## continuous 2-turn track"): straight, corner, straight, corner, straight as ONE road. Display only, never read by the sim.
## Same conventions as track.gd: forward of the first straight is -Z, lateral d > 0 = right of travel (tangent x up).
## Corner radius / angle stay the display PLACEHOLDERS of spec/display.json road.by_code.
extends RefCounted
var segs: Array = []   # {k: "S"/"A", s0, len, x, z, tx, tz, R, sgn}
var length := 0.0
var x0 := 0.0; var z0 := 0.0; var tx0 := 0.0; var tz0 := -1.0
## TOUGE (Gordon, touge-race): elevation, all downhill. y(s, d) = y0 + grade * s + bank(s) * d * sgn (outside high in arcs).
## grade / bank / bank_ramp_m are display values from display.json districts.touge (Arthur's districts README Pass 2:
## "falls at 5 %", "banks up to 6 %, with the outside high"); 0 = flat (Street / Wangan).
var grade := 0.0; var bank := 0.0; var bank_ramp_m := 8.0; var y0 := 0.0
## TOUGE (Austin t121 item 11): the guardrail + drop follow each corner on its OUTSIDE, the cut slope / lattice on the inside.
## drop_runs = [[s_from, side]] sorted by s (side +1 = drop on the right of travel, -1 = left); drop_const for a plain straight.
var drop_runs: Array = []; var drop_const := 1.0
## TOUGE: how far the roadside may reach on each side before it runs into another part of the road (the other leg of a hairpin,
## the centre of a tight arc): the 2D Voronoi boundary of the centre line along each normal, sampled every cap_step m.
## Dressing clamps its bands / props to cap_at(s, side) - road half - margin so hairpin interiors never overlap or fold.
## Austin pt137u (dressing missing / clipped, voids past the dressing): two root causes, fixed here.
## 1. The boundary was 2D only, so any part of the course that passes over or under this spot in plan (turn 10 crosses
##    s = 462 25.7 m higher) counted as "the other leg" and cut the room on BOTH sides to < 1 m. A sample j now only limits
##    the room on its side when this side's terrain profile (terrain_profile: verge / slope / cut / hill, out to the camera
##    reach) passes within cap_prof.clear m of j's road height at j's distance, i.e. when the two roadsides could touch. A
##    profile that dives well under j, or passes well over it (the pass crosses itself: turn 5 runs 25.7 m over turn 10),
##    does not limit it; the dressing skirts are shorter than clear, so they never reach a road they were not limited by.
## 2. The samples ran from -80 m to length + 140 m, but the road and its dressing only exist on [-60, length + 60]: the
##    phantom run-out past the finish (~46 m under turn 2) clipped turn 2's roadside. build_caps(s_from, s_end) now takes the
##    dressed range.
## 3. (pt137u round 2, void sweep) Rule 1 let a leg's FAR terrain (the profile out to reach_m) hang over a lower leg: the
##    start run-in's inside hill (y ~ +10) ran 25 m out over turn 2's drop side (y ~ -20), a floating sheet with sky under it
##    (void_check t02_qte*). Terrain is one surface, so the far bands get their own room, tcap: j limits it unless this side's
##    terrain passes >= clear UNDER j's road (j is then on a bridge / fill above it; e.g. turn 10's slope under turn 5). A
##    hill over a lower leg is cut at the Voronoi boundary, and tstep (the drop from this terrain to j's terrain at that
##    boundary) sizes the skirt that closes the cliff. The kit (rails, lattice, cards) keeps cap (rule 1): a rail at the
##    edge of a road over a crossing stays.
##    A skirt never hangs into another road's clear space: where the boundary lies over j's road (turn 5 runs ~24 m right
##    above turn 10 for ~80 m, s 458-536 over s 906-979) its bottom stops road_clear_m above j's road (tskmax), so turn 10
##    drives under turn 5's edge like a gallery instead of into a wall (pt137u round 2, void sweep t10 views).
var tcap_l := PackedFloat32Array(); var tcap_r := PackedFloat32Array(); var tstep_l := PackedFloat32Array(); var tstep_r := PackedFloat32Array()
var tskmax_l := PackedFloat32Array(); var tskmax_r := PackedFloat32Array()
## tup: where the neighbour's terrain at the boundary is ABOVE this band's cut edge (this leg runs under it: turn 10's cut is
## capped 2-3 m past its edge where turn 5 diverges overhead, s 890-900), the cut face continues UP to it, so the step between
## the two levels is closed from below as tstep closes it from above (void sweep t09_qte1_chase / lot_overview).
var tup_l := PackedFloat32Array(); var tup_r := PackedFloat32Array()
var groof_l := PackedFloat32Array(); var groof_r := PackedFloat32Array()
var gwall_l := PackedFloat32Array(); var gwall_r := PackedFloat32Array()   # gallery wall line, metres past the edge
func gwall_at(s: float, side: float) -> float:   # min of the two samples (the wall never stands past a band end)
	var a := gwall_r if side > 0.0 else gwall_l
	if a.is_empty(): return float(cap_prof.get("gallery_wall", 3.5))
	var f := clampf((s - cap_s0) / cap_step, 0.0, a.size() - 1.001); var i := int(f)
	return minf(a[i], a[i + 1])   # gallery: height of the leg overhead at the wall line (0 = none)
## Band ends at a step (void sweep t05_lot_top_down): both legs' bands used to stop BAND_MARGIN short of their shared boundary
## (and at the shorter of two 2 m samples), so where two levels meet across an oblique crossing (turn 5 over turn 10, s 534-540)
## the higher band's skirt and the lower band's up face stood 0.8-1.6 m apart in plan and the slot between them was open to the
## sky from above. The HIGHER band (tstep > 0) now runs past the boundary over the lower one (tlap: to the longer sample +
## BAND_MARGIN + step_lap_m), so its skirt hangs over the lower terrain and its deck covers the lower band's up face, whose top is
## the higher leg's surface AT that face (not at the boundary + 0.5 m, which left a lip poking through the deck).
const BAND_MARGIN := 0.4   # every terrain band / kit stops this far inside its room (touge_dressing CAP_MARGIN)
var tlap_l := PackedFloat32Array(); var tlap_r := PackedFloat32Array()
var cap_prof: Dictionary = {}   # {W, out: profile, in: profile, clear}; empty = plan-only boundary (Street / Wangan)
## The turnout lot (Austin pt155u: terrain slabs over the lot). The lot is cut into the inside hill: its floor runs out to
## Ld * u(s) past the edge and the cut / hill start that much further out. Every terrain rule here (tcap, tstep, tup, tskmax,
## groof) used the plain inside profile there, i.e. a 7.6-10 m hill where the lot floor is: turn 10's band under turn 5 got an
## up face (tup) to that phantom hill, a 7 m slab standing on the lot floor, and no skirt kept the lot's clear space. Set
## before build_caps: {s0, s1, taper, w}; the side is the inside at the lot. lot_w_at() / side_prof() are the lot-aware profile.
var lot_cut: Dictionary = {}
var _inprof: Array = []
func lot_w_at(s: float, side: float) -> float:
	if lot_cut.is_empty() or s <= float(lot_cut.s0) or s >= float(lot_cut.s1): return 0.0
	if side != -drop_at((float(lot_cut.s0) + float(lot_cut.s1)) * 0.5): return 0.0
	return clampf(minf(s - float(lot_cut.s0), float(lot_cut.s1) - s) / maxf(float(lot_cut.taper), 1e-3), 0.0, 1.0) * float(lot_cut.w)
## the inside profile pushed out by the lot: floor (0.02) to w, the gravel, then the cut / hill as before, w further out
func lot_prof(w: float) -> Array:
	var p: Array = cap_prof["in"]
	if w <= 0.0: return p
	var q := [[0.0, float(p[0][1])], [w, float(p[0][1])]]
	for k in range(1, p.size()): q.append([float(p[k][0]) + w, float(p[k][1])])
	return q
## the terrain profile on side at s (outside of the corner = out, inside = in, pushed out by the lot)
func side_prof(s: float, side: float) -> Array:
	return cap_prof.out if side == float(drop_at(s)) else lot_prof(lot_w_at(s, side))
func _pr(k: int, side: float, dr: Array) -> Array:
	return cap_prof.out if side == float(dr[k]) else _inprof[k][0 if side < 0.0 else 1]
var cap_step := 2.0; var cap_s0 := -60.0; var cap_l := PackedFloat32Array(); var cap_r := PackedFloat32Array()
func build_caps(s_from: float, s_end: float) -> void:
	cap_s0 = s_from
	var cs := []; var ys := []; var dr := []; var s := cap_s0
	while s <= s_end + 1e-6: cs.append(at(s)); ys.append(elev(s, 0.0)); dr.append(drop_at(s)); s += cap_step
	var n := cs.size(); var cell := 20.0; var grid := {}
	_inprof = []
	for i in n:
		var si: float = cap_s0 + i * cap_step
		_inprof.append([lot_prof(lot_w_at(si, -1.0)) if not cap_prof.is_empty() else [], lot_prof(lot_w_at(si, 1.0)) if not cap_prof.is_empty() else []])
	for i in n:
		var k := Vector2i(floori(float(cs[i].x) / cell), floori(float(cs[i].z) / cell))
		if not grid.has(k): grid[k] = []
		grid[k].append(i)
	var W: float = float(cap_prof.get("W", 0.0)); var clear: float = float(cap_prof.get("clear", 12.0))
	var reach: float = 40.0
	if not cap_prof.is_empty(): reach = float((cap_prof.out as Array)[-1][0]) + W
	var rc := int(ceil(2.0 * reach / cell)) + 1
	cap_l.resize(n); cap_r.resize(n); tcap_l.resize(n); tcap_r.resize(n); tstep_l.resize(n); tstep_r.resize(n); tskmax_l.resize(n); tskmax_r.resize(n); tup_l.resize(n); tup_r.resize(n)
	var road_clear: float = float(cap_prof.get("road_clear", 8.0))
	var lap: float = float(cap_prof.get("lap", 0.0))
	var lj_l := PackedInt32Array(); var lj_r := PackedInt32Array(); lj_l.resize(n); lj_r.resize(n)   # the leg sample that sets tcap
	for i in n:
		var c: Dictionary = cs[i]; var cx: float = c.x; var cz: float = c.z
		var nx: float = -float(c.tz); var nz: float = float(c.tx)   # +d (right) normal: point() = x - tz d, z + tx d
		var kl := 1e3; var kr := 1e3; var tl := 1e3; var tr := 1e3; var jl := -1; var jr := -1
		var k0 := Vector2i(floori(cx / cell), floori(cz / cell))
		for gx in range(-rc, rc + 1):
			for gz in range(-rc, rc + 1):
				for j in grid.get(k0 + Vector2i(gx, gz), []):
					if j == i: continue
					var vx: float = float(cs[j].x) - cx; var vz: float = float(cs[j].z) - cz
					var dn := vx * nx + vz * nz; var dd := vx * vx + vz * vz
					if absf(dn) <= 1e-3: continue
					var side := 1.0 if dn > 0.0 else -1.0
					var dd0 := dd
					# a lot widens its leg's ground (lot_cut): the boundary is the bisector between the two legs' drivable
					# EDGES on the facing sides, not their centre lines (pt155u: turn 9's band ended inside turn 5's lot)
					var wi: float = lot_w_at(cap_s0 + i * cap_step, side)
					var sjf := 1.0 if (cx - float(cs[j].x)) * -float(cs[j].tz) + (cz - float(cs[j].z)) * float(cs[j].tx) > 0.0 else -1.0
					var wj: float = lot_w_at(cap_s0 + j * cap_step, sjf)
					var b_off := 0.0
					if wi > 0.0 or wj > 0.0:
						vx += -float(cs[j].tz) * sjf * wj - nx * side * wi; vz += float(cs[j].tx) * sjf * wj - nz * side * wi
						dn = vx * nx + vz * nz; dd = vx * vx + vz * vz; b_off = wi
						if dn * side <= 1e-3: continue   # the two lots' edges overlap in plan: no boundary from this pair
					if cap_prof.is_empty():
						if absf(float(ys[j]) - float(ys[i])) > 18.0: continue
					else:
						var pr: Array = _pr(i, side, dr)
						var yb := prof_y(pr, maxf(0.0, sqrt(dd0) - W))
						var dyb := yb - (float(ys[j]) - float(ys[i]))
						if dyb <= -clear: continue   # dives well under j's road (j bridges over it): limits neither
						var b := dd / (2.0 * absf(dn)) + b_off
						if dn > 0.0 and b < tr: tr = b; jr = j
						elif dn < 0.0 and b < tl: tl = b; jl = j
						if dyb >= clear: continue   # passes well over j's road: the kit is not limited, the terrain is (tcap)
					if dn > 0.0: kr = minf(kr, dd / (2.0 * dn) + b_off)
					else: kl = minf(kl, dd / (-2.0 * dn) + b_off)
		cap_l[i] = kl; cap_r[i] = kr
		if cap_prof.is_empty():
			tcap_l[i] = kl; tcap_r[i] = kr; tstep_l[i] = 0.0; tstep_r[i] = 0.0; tskmax_l[i] = 1e3; tskmax_r[i] = 1e3; tup_l[i] = 0.0; tup_r[i] = 0.0; continue
		tcap_l[i] = tl; tcap_r[i] = tr
		for sd in [-1.0, 1.0]:
			var jj: int = jl if sd < 0.0 else jr; var bb: float = tl if sd < 0.0 else tr
			var stp := 0.0; var skm := 1e3; var upv := 0.0
			if jj >= 0:
				var my: Array = _pr(i, sd, dr)
				var bx: float = cx + nx * sd * bb; var bz: float = cz + nz * sd * bb
				var cj: Dictionary = cs[jj]
				var vx2: float = bx - float(cj.x); var vz2: float = bz - float(cj.z)
				var sj := 1.0 if vx2 * -float(cj.tz) + vz2 * float(cj.tx) > 0.0 else -1.0
				var pj: Array = _pr(jj, sj, dr)
				var yj: float = float(ys[jj]) + prof_y(pj, maxf(0.0, sqrt(vx2 * vx2 + vz2 * vz2) - W))
				var ytop: float = float(ys[i]) + prof_y(my, maxf(0.0, bb - W))
				stp = maxf(0.0, ytop - yj)
				# j's terrain is ABOVE this band's cut edge: the cliff goes up (tup), to j's surface at the face itself
				# (the band ends BAND_MARGIN inside the boundary; j's lapped deck covers that line from above)
				var bf: float = maxf(W, bb - BAND_MARGIN)
				var fx: float = cx + nx * sd * bf - float(cj.x); var fz: float = cz + nz * sd * bf - float(cj.z)
				var sf := 1.0 if fx * -float(cj.tz) + fz * float(cj.tx) > 0.0 else -1.0
				# real heights at the face (pt155u TERRAIN_CHECK: centre-line sample heights put turn 9's up face 0.4-1.0 m up
				# through turn 5's lot floor): j's surface at the face's own s / d on j (grade, bank, the lot's floor there) and
				# this band's edge as pp() builds it; the face stops UP_GAP under j's surface, which covers it from above
				var dfj: float = fx * -float(cj.tz) + fz * float(cj.tx); var sqj: float = cap_s0 + jj * cap_step + (fx * float(cj.tx) + fz * float(cj.tz))
				var pjf: Array = cap_prof.out if sf == float(drop_at(sqj)) else lot_prof(lot_w_at(sqj, sf))
				var yjf: float = elev(sqj, clampf(dfj, -W, W)) + prof_y(pjf, maxf(0.0, absf(dfj) - W))
				upv = maxf(0.0, yjf - UP_GAP - (elev(cap_s0 + i * cap_step, sd * bf) + prof_y(my, maxf(0.0, bf - W)))) if yj > ytop else 0.0
				if sqrt(vx2 * vx2 + vz2 * vz2) - W - lot_w_at(cap_s0 + jj * cap_step, sj) < float(cap_prof.get("gallery_wall", 3.5)):   # over j's road / lot / gravel / rail line: keep its clear space
					skm = maxf(0.0, ytop - (float(ys[jj]) + road_clear))
			# any road under the skirt line (not only the limiting j): its clear space caps the skirt
			var my2: Array = _pr(i, sd, dr)
			var eb: float = minf(bb + BAND_MARGIN + lap, float((my2 as Array)[-1][0]) + W)   # where the (lapped) skirt hangs
			var ytop2: float = float(ys[i]) + prof_y(my2, maxf(0.0, eb - W))
			var bx2: float = cx + nx * sd * eb; var bz2: float = cz + nz * sd * eb
			var kb := Vector2i(floori(bx2 / cell), floori(bz2 / cell))
			for gx in range(-1, 2):
				for gz in range(-1, 2):
					for j in grid.get(kb + Vector2i(gx, gz), []):
						if absi(j - i) * cap_step < 30.0: continue
						var wx: float = float(cs[j].x) - bx2; var wz: float = float(cs[j].z) - bz2
						var lwj: float = maxf(lot_w_at(cap_s0 + j * cap_step, -1.0), lot_w_at(cap_s0 + j * cap_step, 1.0))   # its lot is drivable too
						if wx * wx + wz * wz < pow(W + lwj + float(cap_prof.get("gallery_wall", 3.5)), 2.0) and float(ys[j]) < ytop2:
							skm = minf(skm, maxf(0.0, ytop2 - (float(ys[j]) + road_clear)))
			if sd < 0.0: tstep_l[i] = stp; tskmax_l[i] = skm; tup_l[i] = upv
			else: tstep_r[i] = stp; tskmax_r[i] = skm; tup_r[i] = upv
			if sd < 0.0: lj_l[i] = jj
			else: lj_r[i] = jj
	# The ground under a boundary is the LOWEST terrain that covers it, not only j's: a third leg whose slope dives under
	# both (rule 3 leaves it uncapped) shows through the cut, e.g. turn 7's drop side under turn 6's hill at s 606-612
	# (void sweep t07_qte0_outside). Second pass, once every tcap is known: deepen tstep to that terrain.
	for i in n:
		var c: Dictionary = cs[i]; var cx: float = c.x; var cz: float = c.z
		var nx: float = -float(c.tz); var nz: float = float(c.tx)
		for sd in [-1.0, 1.0]:
			var bb: float = tcap_l[i] if sd < 0.0 else tcap_r[i]
			if bb >= reach: continue
			var my: Array = _pr(i, sd, dr)
			var ytop: float = float(ys[i]) + prof_y(my, maxf(0.0, bb - W))
			var bx: float = cx + nx * sd * bb; var bz: float = cz + nz * sd * bb
			var low: float = ytop - (tstep_l[i] if sd < 0.0 else tstep_r[i])
			var kb := Vector2i(floori(bx / cell), floori(bz / cell))
			for gx in range(-rc, rc + 1):
				for gz in range(-rc, rc + 1):
					for k in grid.get(kb + Vector2i(gx, gz), []):
						if k == i: continue
						var ck: Dictionary = cs[k]
						var wx: float = bx - float(ck.x); var wz: float = bz - float(ck.z)
						if absf(wx * float(ck.tx) + wz * float(ck.tz)) > 0.5 * cap_step + 0.05: continue   # B on k's normal line
						var dk: float = wx * -float(ck.tz) + wz * float(ck.tx); var sk := 1.0 if dk > 0.0 else -1.0
						var ad := absf(dk)
						if ad < W or ad > (tcap_l[k] if sk < 0.0 else tcap_r[k]) + 0.5 or ad > reach: continue
						var pk: Array = _pr(k, sk, dr)
						low = minf(low, float(ys[k]) + prof_y(pk, ad - W))
			var stp2: float = maxf(0.0, ytop - low)
			if sd < 0.0: tstep_l[i] = stp2
			else: tstep_r[i] = stp2
	# Lap: a band standing ABOVE the terrain past its boundary (tstep > 0) runs on over it, wherever that cannot cover the lower
	# leg's road: it stands >= road_clear over it, or the room is wide enough that the lap ends on the lower leg's terrain (the
	# lower leg's clear space under the skirt is kept by tskmax at the lapped skirt line). Only against ANOTHER leg (>= 40 m along
	# the course): inside a hairpin the boundary is the bend's own centre, where the fan of band rows converges; lapping past it
	# folds the fan back over itself (void replay t07_plan_A, the drop-side flip at s 729 inside turn 7).
	tlap_l.resize(n); tlap_r.resize(n)
	for i in n:
		for sd in [-1.0, 1.0]:
			var bb: float = tcap_l[i] if sd < 0.0 else tcap_r[i]; var st_: float = tstep_l[i] if sd < 0.0 else tstep_r[i]
			var jx: int = lj_l[i] if sd < 0.0 else lj_r[i]
			var lv: float = BAND_MARGIN + lap if lap > 0.0 and st_ > 0.0 and (st_ >= road_clear or bb - W >= 2.0 * (BAND_MARGIN + lap) + 1.0) and bb < reach and jx >= 0 and absi(jx - i) * cap_step >= 40.0 else 0.0
			if sd < 0.0: tlap_l[i] = lv
			else: tlap_r[i] = lv
	# Gallery (pt137u round 2, void sweep t09/t10 + lot): turn 5 (s 458-540) runs 18-25 m right over turn 10 (s 900-980),
	# only 4.4 m to one side, so its deck covers turn 10's lane and roadside. The cavity under it beside turn 10 was open: turn
	# 10's cameras saw sky out under turn 5, and the lot (on turn 5) saw down past its edge, through the cavity, to sky. A road
	# under another leg runs in a gallery: at gallery_wall_m past each edge, wherever another leg's road or terrain lies above
	# by >= road_clear_m, a wall rises from this road's ground to that surface (groof = its height over this road).
	var gwe: float = float(cap_prof.get("gallery_wall", 3.5))
	groof_l.resize(n); groof_r.resize(n); gwall_l.resize(n); gwall_r.resize(n)
	for i in n:
		var c: Dictionary = cs[i]; var nx: float = -float(c.tz); var nz: float = float(c.tx)
		for sd in [-1.0, 1.0]:
			# the wall stands at gallery_wall_m, or just past this road's band end where the band is shorter (pt155u: a lot-aware
			# boundary ends turn 10's band 1.6 m out under turn 5; a wall at 3.5 m left a floorless slot between the two)
			var ew: float = clampf(minf(gwe, tband_at(cap_s0 + i * cap_step, sd) - W + 0.03), 0.3, gwe)
			if sd < 0.0: gwall_l[i] = ew
			else: gwall_r[i] = ew
			var qx: float = float(c.x) + nx * sd * (W + ew); var qz: float = float(c.z) + nz * sd * (W + ew)
			var roof := 0.0
			var kq := Vector2i(floori(qx / cell), floori(qz / cell))
			for gx in range(-rc, rc + 1):
				for gz in range(-rc, rc + 1):
					for k in grid.get(kq + Vector2i(gx, gz), []):
						if absi(k - i) * cap_step < 30.0: continue
						var ck: Dictionary = cs[k]
						var wx: float = qx - float(ck.x); var wz: float = qz - float(ck.z)
						if absf(wx * float(ck.tx) + wz * float(ck.tz)) > 0.5 * cap_step + 0.05: continue
						var dk: float = wx * -float(ck.tz) + wz * float(ck.tx); var sk := 1.0 if dk > 0.0 else -1.0
						var ad := absf(dk)
						# the surface's real height there (banked road at its own s / d, not the centre-line sample height):
						# the gallery wall stops just under it (pt155u: it stood 0.1-0.2 m up through turn 5's road)
						var sq: float = cap_s0 + k * cap_step + (wx * float(ck.tx) + wz * float(ck.tz))
						var yk: float = elev(sq, clampf(dk, -W, W))
						if ad > W:
							if ad > (tcap_l[k] if sk < 0.0 else tcap_r[k]) or ad > reach: continue
							yk += prof_y(_pr(k, sk, dr), ad - W)
						var h: float = yk - elev(cap_s0 + i * cap_step, sd * (W + ew))   # over THIS road's plane at the wall line (pp() adds the bank there)
						if h >= road_clear and (roof == 0.0 or h < roof): roof = h
			if sd < 0.0: groof_l[i] = roof
			else: groof_r[i] = roof

## TOUGE terrain profile on one side: [[metres beyond the road edge, height above the road], ...]. The near part is the approved
## kit (outside: verge 0..0.55, slope to -7.5 at 9 m; inside: gravel, lattice cut to 7.6 at 8.7 m, hill band to 10 at 18 m);
## display.json districts.touge.terrain continues both out to reach_m (fog_far + the furthest camera offset from the road),
## so every camera pose sees ground wherever the fog has not already hidden it (Austin pt137u pic 5).
static func terrain_profile(D: Dictionary, outside: bool) -> Array:
	var T: Dictionary = D.get("terrain", {})
	var R: float = float(T.get("reach_m", 18.0))
	if outside:
		var p := [[0.0, 0.0], [0.55, 0.0], [9.0, -7.5]]
		if R > 9.0: p.append([R, -7.5 - float(T.get("out_slope", 0.888)) * (R - 9.0)])
		return p
	var gw: float = float(D.get("gravel_w_m", 0.7))
	var q := [[0.0, 0.02], [gw, 0.02], [8.7, 7.6], [18.0, 10.0]]
	if R > 18.0: q.append([R, 10.0 + float(T.get("in_slope", 0.35)) * (R - 18.0)])
	return q

static func prof_y(prof: Array, e: float) -> float:
	if e <= float(prof[0][0]): return float(prof[0][1])
	for k in range(1, prof.size()):
		var a: Array = prof[k - 1]; var b: Array = prof[k]
		if e <= float(b[0]): return lerpf(float(a[1]), float(b[1]), (e - float(a[0])) / maxf(1e-6, float(b[0]) - float(a[0])))
	return float(prof[-1][1])

## centre-line distance available on side (+1 right / -1 left) at s (1e3 = unlimited)
func cap_at(s: float, side: float) -> float:
	var a := cap_r if side > 0.0 else cap_l
	if a.is_empty(): return 1e3
	var f := clampf((s - cap_s0) / cap_step, 0.0, a.size() - 1.001); var i := int(f)
	return minf(a[i], a[i + 1])   # conservative between samples

## the far terrain's room on side (rule 3); the cliff drop to the neighbour terrain at that boundary (skirt depth)
func tcap_at(s: float, side: float) -> float:
	var a := tcap_r if side > 0.0 else tcap_l
	if a.is_empty(): return cap_at(s, side)
	var f := clampf((s - cap_s0) / cap_step, 0.0, a.size() - 1.001); var i := int(f)
	return minf(a[i], a[i + 1])
## centre-line distance where the terrain band on side ends: BAND_MARGIN inside tcap, or past it by tlap where it laps over a lower level
func tband_at(s: float, side: float) -> float:
	var a := tcap_r if side > 0.0 else tcap_l
	if a.is_empty(): return cap_at(s, side) - BAND_MARGIN
	var l := tlap_r if side > 0.0 else tlap_l
	var f := clampf((s - cap_s0) / cap_step, 0.0, a.size() - 1.001); var i := int(f)
	if not l.is_empty() and l[i] > 0.0 and l[i + 1] > 0.0: return maxf(a[i], a[i + 1]) + minf(l[i], l[i + 1])
	return minf(a[i], a[i + 1]) - BAND_MARGIN
func tup_lerp(s: float, side: float) -> float:   # the samples interpolated along s: an up face's top follows the surface above it
	var a := tup_r if side > 0.0 else tup_l
	if a.is_empty(): return 0.0
	var f := clampf((s - cap_s0) / cap_step, 0.0, a.size() - 1.001); var i := int(f)
	return lerpf(a[i], a[i + 1], f - i)
const UP_GAP := 0.05   # an up face stops this far under the surface it meets (that surface covers its top edge)
func tup_at(s: float, side: float) -> float:   # min of the two samples: the face must not stand up through the surface above
	var a := tup_r if side > 0.0 else tup_l
	if a.is_empty(): return 0.0
	var f := clampf((s - cap_s0) / cap_step, 0.0, a.size() - 1.001); var i := int(f)
	return minf(a[i], a[i + 1]) if a[i] > 0.0 and a[i + 1] > 0.0 else maxf(a[i], a[i + 1])
func groof_at(s: float, side: float, lo := false) -> float:   # max of the two samples (lo: min, a wall top that must stay UNDER the surface)
	var a := groof_r if side > 0.0 else groof_l
	if a.is_empty(): return 0.0
	var f := clampf((s - cap_s0) / cap_step, 0.0, a.size() - 1.001); var i := int(f)
	if not (a[i] > 0.0 and a[i + 1] > 0.0): return 0.0
	return minf(a[i], a[i + 1]) if lo else maxf(a[i], a[i + 1])
func tskmax_at(s: float, side: float) -> float:
	var a := tskmax_r if side > 0.0 else tskmax_l
	if a.is_empty(): return 1e3
	var f := clampf((s - cap_s0) / cap_step, 0.0, a.size() - 1.001); var i := int(f)
	return minf(a[i], a[i + 1])
func tstep_at(s: float, side: float) -> float:
	var a := tstep_r if side > 0.0 else tstep_l
	if a.is_empty(): return 0.0
	var f := clampf((s - cap_s0) / cap_step, 0.0, a.size() - 1.001); var i := int(f)
	return maxf(a[i], a[i + 1])

## TOUGE (Austin pt137u item 15, pic 1: lattice on BOTH sides past turn 1): which side is the drop must follow the ground, not
## only the corner. The corner rule (t121 item 11: outside of each corner = guardrail + drop, flip halfway along the straight)
## put turn 1's exit-straight drop on the LEFT from s 113 on, toward the approach leg 28 m away and 5-11 m HIGHER (a guardrail
## and a drop facing up a hill), and the lattice on the right; the hairpin's own inside lattice was still in view on the left.
## The same rule hung turn 10's drop under turn 5 (24 m above) and put turn 5's cut toward turn 10 30 m below. Rule now: where
## another leg runs alongside (|dl| <= lat_m, >= 40 m along the course, height difference >= dy_m) the drop side is the LOWER
## neighbour's side (the higher one is uphill = cut / lattice); with no neighbour the corner rule (default) stands. Each turn's
## approach [off, off + S] is one run (it overlaps that turn's scroll straight, whose drop_const must match), the turnout lot
## span keeps one side, and runs shorter than min_run_m merge into the one before. Returns {"runs", "spans": [side per span]}.
func terrain_drop_runs(s_from: float, s_end: float, W: float, spans: Array, lat_m := 60.0, dy_m := 1.5, min_run_m := 24.0) -> Dictionary:
	var step := 2.0
	var cs := []; var ys := []; var s := s_from
	while s <= s_end + 1e-6: cs.append(at(s)); ys.append(elev(s, 0.0)); s += step
	var n := cs.size(); var cell := 20.0; var grid := {}
	for i in n:
		var k := Vector2i(floori(float(cs[i].x) / cell), floori(float(cs[i].z) / cell))
		if not grid.has(k): grid[k] = []
		grid[k].append(i)
	var rc := int(ceil(lat_m / cell)) + 1
	var want := PackedFloat32Array(); want.resize(n)
	for i in n:
		var c: Dictionary = cs[i]; var nx: float = -float(c.tz); var nz: float = float(c.tx)
		var best := {-1.0: [1e9, 0.0], 1.0: [1e9, 0.0]}   # side -> [|dl|, dy] of the nearest leg alongside
		var k0 := Vector2i(floori(float(c.x) / cell), floori(float(c.z) / cell))
		for gx in range(-rc, rc + 1):
			for gz in range(-rc, rc + 1):
				for j in grid.get(k0 + Vector2i(gx, gz), []):
					if absi(j - i) * step < 40.0: continue
					var vx: float = float(cs[j].x) - float(c.x); var vz: float = float(cs[j].z) - float(c.z)
					if absf(vx * float(c.tx) + vz * float(c.tz)) > 0.5 * step + 0.05: continue
					var dl: float = vx * nx + vz * nz
					if absf(dl) > lat_m: continue
					var sd := 1.0 if dl > 0.0 else -1.0
					if absf(dl) < float(best[sd][0]): best[sd] = [absf(dl), float(ys[j]) - float(ys[i])]
		var w := 0.0; var lo := 1e9
		for sd in [-1.0, 1.0]:
			if float(best[sd][0]) > lat_m: continue
			var dy: float = best[sd][1]
			if dy <= -dy_m and dy < lo: lo = dy; w = sd           # a lower leg on this side: the drop faces it
			elif dy >= dy_m and w == 0.0: w = -sd                  # a higher leg on this side: uphill, the drop is opposite
		want[i] = w
	var side := PackedFloat32Array(); side.resize(n)
	for i in n: side[i] = want[i] if want[i] != 0.0 else drop_at(s_from + i * step)
	var span_side := []
	for sp in spans:   # one side per span: the majority of the decided samples in it, else the corner rule at its middle
		var i0 := clampi(int(ceil((float(sp[0]) - s_from) / step)), 0, n - 1); var i1 := clampi(int(floor((float(sp[1]) - s_from) / step)), 0, n - 1)
		var v := 0.0
		for i in range(i0, i1 + 1): v += want[i]
		var sv: float = signf(v) if v != 0.0 else drop_at((float(sp[0]) + float(sp[1])) * 0.5)
		for i in range(i0, i1 + 1): side[i] = sv
		span_side.append(sv)
	var runs := [[-1e9, side[0]]]
	for i in range(1, n):
		if side[i] != side[i - 1]: runs.append([s_from + i * step - 1.0, side[i]])
	var fixed := func(a: float, b: float) -> bool:
		for sp in spans:
			if a < float(sp[1]) and b > float(sp[0]): return true
		return false
	var merged := true
	while merged:   # a run shorter than min_run_m (and not a fixed span) takes the side of the run before it
		merged = false
		for r in range(1, runs.size() - 1):
			var a0: float = runs[r][0]; var a1: float = runs[r + 1][0]
			if a1 - a0 < min_run_m and not fixed.call(a0 + 0.5, a1 - 0.5):
				runs.remove_at(r); merged = true; break
		var k := 1
		while k < runs.size():
			if float(runs[k][1]) == float(runs[k - 1][1]): runs.remove_at(k)
			else: k += 1
	return {"runs": runs, "spans": span_side}

func drop_at(s: float) -> float:
	var side := drop_const
	for r in drop_runs:
		if s >= float(r[0]): side = float(r[1])
		else: break
	return side

func _init(x := 0.0, z := 0.0, tx := 0.0, tz := -1.0) -> void:
	x0 = x; z0 = z; tx0 = tx; tz0 = tz

func _end() -> Dictionary:
	return {"x": x0, "z": z0, "tx": tx0, "tz": tz0} if segs.is_empty() else at(length)

func add_straight(l: float):
	var e := _end(); segs.append({"k": "S", "s0": length, "len": l, "x": e.x, "z": e.z, "tx": e.tx, "tz": e.tz}); length += l
	return self

## sgn +1 = left turn, -1 = right turn (track.gd convention)
func add_arc(r: float, a: float, sgn: float):
	var e := _end(); segs.append({"k": "A", "s0": length, "len": r * a, "x": e.x, "z": e.z, "tx": e.tx, "tz": e.tz, "R": r, "sgn": sgn}); length += r * a
	return self

static func _rot(vx: float, vz: float, tx: float, tz: float) -> Vector2:   # rotate a local (forward = -Z) vector into the frame whose forward is (tx, tz)
	var al := atan2(tx, -tz); var c := cos(al); var s := sin(al)
	return Vector2(vx * c - vz * s, vx * s + vz * c)

func at(s: float) -> Dictionary:
	if segs.is_empty() or s <= 0.0:
		return {"x": x0 + tx0 * s, "z": z0 + tz0 * s, "tx": tx0, "tz": tz0}
	var g: Dictionary = segs[-1]
	for q in segs:
		if s <= float(q.s0) + float(q.len): g = q; break
	var u: float = s - float(g.s0)
	if g.k == "S" or u > float(g.len):   # straight, or past the end of the last arc
		if g.k == "A":
			var e := _arc(g, float(g.len)); return {"x": e.x + e.tx * (u - g.len), "z": e.z + e.tz * (u - g.len), "tx": e.tx, "tz": e.tz}
		return {"x": g.x + g.tx * u, "z": g.z + g.tz * u, "tx": g.tx, "tz": g.tz}
	return _arc(g, u)

func _arc(g: Dictionary, u: float) -> Dictionary:
	var th: float = u / float(g.R); var R: float = g.R; var sg: float = g.sgn
	var p := _rot(sg * (-R + R * cos(th)), -R * sin(th), g.tx, g.tz)
	var t := _rot(-sg * sin(th), -cos(th), g.tx, g.tz)
	return {"x": g.x + p.x, "z": g.z + p.y, "tx": t.x, "tz": t.y}

func elev(s: float, d: float) -> float:
	var y := y0 + grade * s
	if bank != 0.0:
		for q in segs:
			if q.k != "A": continue
			var a: float = q.s0; var b: float = float(q.s0) + float(q.len)
			if s > a - bank_ramp_m and s < b + bank_ramp_m:
				var k := clampf(minf(s - (a - bank_ramp_m), (b + bank_ramp_m) - s) / bank_ramp_m, 0.0, 1.0)
				y += bank * k * k * (3.0 - 2.0 * k) * d * float(q.sgn)
				break
	return y

func point(s: float, d: float) -> Dictionary:
	var p := at(s)
	return {"x": p.x - p.tz * d, "z": p.z + p.tx * d, "tx": p.tx, "tz": p.tz, "y": elev(s, d)}

## one corner of the course seen in that corner's local s (local 0 = 45 m before its turn-in, like the old per-corner Track),
## so stop poses, the corner plate, the authored corner cameras and playback keep their Phase 5 numbers.
class View:
	extends RefCounted
	var course; var off: float; var S: float; var R: float; var A: float; var E: float; var sgn: float; var length: float
	func _init(c, o: float, s_: float, r_: float, a_: float, e_: float, sg: float) -> void:
		course = c; off = o; S = s_; R = r_; A = a_; E = e_; sgn = sg; length = S + R * A + E
	func at(s: float) -> Dictionary: return course.at(off + s)
	func point(s: float, d: float) -> Dictionary: return course.point(off + s, d)
	func corner_cam_points(dir: String, cc: Dictionary) -> Array:
		var out := []
		var ins := -1.0 if dir == "L" else 1.0
		var wk: float = float(cc.get("d_scale", 1.0))   # TOUGE: two-corner keys were authored for a 5.95 m half road
		for k in cc.points:
			var p := point(S + R * A * float(k.a), float(k.d_in) * ins * wk)
			out.append(Vector3(p.x, float(k.h) + float(p.get("y", 0.0)), p.z))   # TOUGE: h above the road (downhill grade)
		return out
