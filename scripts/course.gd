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
var cap_step := 2.0; var cap_s0 := -80.0; var cap_l := PackedFloat32Array(); var cap_r := PackedFloat32Array()
func build_caps(s_end: float) -> void:
	var cs := []; var s := cap_s0
	while s <= s_end: cs.append(at(s)); s += cap_step
	var n := cs.size(); var cell := 20.0; var grid := {}
	for i in n:
		var k := Vector2i(floori(float(cs[i].x) / cell), floori(float(cs[i].z) / cell))
		if not grid.has(k): grid[k] = []
		grid[k].append(i)
	cap_l.resize(n); cap_r.resize(n)
	for i in n:
		var c: Dictionary = cs[i]; var cx: float = c.x; var cz: float = c.z
		var nx: float = -float(c.tz); var nz: float = float(c.tx)   # +d (right) normal: point() = x - tz d, z + tx d
		var kl := 1e3; var kr := 1e3
		var k0 := Vector2i(floori(cx / cell), floori(cz / cell))
		for gx in range(-2, 3):
			for gz in range(-2, 3):
				for j in grid.get(k0 + Vector2i(gx, gz), []):
					if j == i: continue
					var vx: float = float(cs[j].x) - cx; var vz: float = float(cs[j].z) - cz
					var dn := vx * nx + vz * nz; var dd := vx * vx + vz * vz
					if dn > 1e-3: kr = minf(kr, dd / (2.0 * dn))
					elif dn < -1e-3: kl = minf(kl, dd / (-2.0 * dn))
		cap_l[i] = kl; cap_r[i] = kr

## centre-line distance available on side (+1 right / -1 left) at s (1e3 = unlimited)
func cap_at(s: float, side: float) -> float:
	var a := cap_r if side > 0.0 else cap_l
	if a.is_empty(): return 1e3
	var f := clampf((s - cap_s0) / cap_step, 0.0, a.size() - 1.001); var i := int(f)
	return minf(a[i], a[i + 1])   # conservative between samples

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
