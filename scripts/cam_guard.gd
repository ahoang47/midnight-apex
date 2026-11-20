## TOUGE camera clearance (Gordon, touge-race; Austin t114u: "no camera may clip into the track geometry"). An analytic model
## of the touge kit around the course, in course coordinates (s along, d lateral, height above the road plane):
##   inside (cut side, -course.drop_at(s)): road edge W, gravel to W + 0.7, then Arthur's lattice slope face rising 7.2 m over 5.0 m
##     (mtn_lattice_slope_g.glb bounds: x 0..5.04 at y 0..7.23, top 7.6 to x 8), the hill band W + 8.7 (7.6 m) -> W + 18 (10 m);
##     over the turnout lot the floor runs out to W + Ld and the same face starts at W + Ld + 0.7 (tapers interpolate).
##   outside (course.drop_at(s), follows each corner): W-beam guardrail box (rail_box: 0.33-0.70 m beyond the edge, 0.85 m high), verge falling from
##     W + 0.55 (0 m) to W + 9 (-7.5 m) and on at the same slope.
##   lamps (fixed, Austin t116u): post r lamp_r_m up to 6.6 m and the 1.6 m arm toward the road at 6.5 m.
## Cedar cards are not modelled: main.gd hides any card within 5.5 m of the camera (build_lsc.py:254, as before).
## clip(p) > 0 = the near-plane sphere (radius margin_m) around p intersects geometry. fix(pos, look) pulls the camera in toward
## its target along the line of sight (spring arm) until it clears, then lifts it if the target itself is buried.
extends RefCounted

var course; var W := 3.0; var drop := 1.0; var margin := 0.3; var rail: Array = [0.33, 0.7, 0.85]; var lamp_r := 0.3
var lot: Dictionary = {}
var lamps: Array = []        # [Vector3 base, Vector3 arm tip]
var _ss: PackedFloat32Array; var _px: PackedFloat32Array; var _pz: PackedFloat32Array; var _py: PackedFloat32Array
var hint := 0.0

func setup(course_, W_: float, D: Dictionary, G: Dictionary, lot_: Dictionary, lamp_items: Array) -> void:
	course = course_; W = W_; drop = float(D.get("drop_side", 1.0)); lot = lot_
	margin = float(G.margin_m); rail = G.rail_box; lamp_r = float(G.lamp_r_m)
	_ss = PackedFloat32Array(); _px = PackedFloat32Array(); _pz = PackedFloat32Array(); _py = PackedFloat32Array()
	straight = course.segs.size() == 1 and String(course.segs[0].k) == "S"
	if straight: lamps = lamp_items; return
	var s := -80.0
	while s <= course.length + 140.0:
		var p: Dictionary = course.at(s); _ss.append(s); _px.append(p.x); _pz.append(p.z); _py.append(course.elev(s, 0.0)); s += 1.0
	lamps = lamp_items

## course s nearest to p over the WHOLE course (3D, so the two legs of a hairpin at different heights are told apart); use it as
## the hint for a camera pose: stop / corner cameras can sit far from the player's own s
func locate(p: Vector3) -> float:
	if straight: return sd_of(p.x, p.z)[0]
	var best := 1e20; var bi := 0
	for i in _ss.size():
		var dx := p.x - _px[i]; var dz := p.z - _pz[i]; var dy := (p.y - _py[i]) * 2.0
		var dd := dx * dx + dz * dz + dy * dy
		if dd < best: best = dd; bi = i
	hint = _ss[bi]
	return hint

## nearest course sample to (x, z) within +-90 m of the hint, refined on the segment; returns [s, d]
var straight := false
func sd_of(x: float, z: float) -> Array:
	if straight:   # the per-corner scroll straight: one 100 km segment, solved directly
		var g: Dictionary = course.segs[0]
		var dx0 := x - float(g.x); var dz0 := z - float(g.z)
		return [dx0 * float(g.tx) + dz0 * float(g.tz), -dx0 * float(g.tz) + dz0 * float(g.tx)]
	var i0 := clampi(int(hint + 80.0) - 90, 0, _ss.size() - 1); var i1 := clampi(int(hint + 80.0) + 90, 0, _ss.size() - 1)
	var best := 1e20; var bi := i0
	for i in range(i0, i1 + 1):
		var dx := x - _px[i]; var dz := z - _pz[i]; var dd := dx * dx + dz * dz
		if dd < best: best = dd; bi = i
	var s: float = _ss[bi]
	var p: Dictionary = course.at(s)
	var u := (x - float(p.x)) * float(p.tx) + (z - float(p.z)) * float(p.tz)   # along the tangent
	s += clampf(u, -1.0, 1.0); p = course.at(s)
	var d := -(x - float(p.x)) * float(p.tz) + (z - float(p.z)) * float(p.tx)   # point(): x - tz*d, z + tx*d
	return [s, d]

## lot depth at course s (0 outside the lot, Ld between the tapers)
func _lot_depth(s: float) -> float:
	if lot.is_empty(): return 0.0
	var a: float = lot.s0; var b: float = lot.s1; var tp: float = lot.taper
	return clampf(minf((s - a) / tp, (b - s) / tp), 0.0, 1.0) * float(lot.w)

## ground / wall height above the road plane at e metres beyond the road edge on the inside
func _inside_h(e: float, ld: float) -> float:
	var f0 := 0.7 + ld
	if e < f0: return 0.15 if (ld > 0.0 and e > ld - 0.9) else 0.02   # gravel / lot floor (back curb, wheel stops)
	var x := e - f0
	if x <= 5.0: return x * 7.2 / 5.0
	if e < 8.7 + ld: return 7.6
	return lerpf(7.6, 10.0, clampf((e - (8.7 + ld)) / 9.3, 0.0, 1.0))

func clip(p: Vector3) -> float:
	var sd := sd_of(p.x, p.z); var s: float = sd[0]; var d: float = sd[1]
	var y: float = p.y - course.elev(s, d)
	var pen := -1e9
	var dr: float = course.drop_at(s) if course.has_method("drop_at") else drop   # outside of the corner at s (Austin t121 item 11)
	var e_in := -d * dr - W; var e_out := d * dr - W   # beyond the inside / outside edge
	if e_in > -margin:
		pen = maxf(pen, _inside_h(maxf(e_in, 0.0) + margin, _lot_depth(s)) + margin - y)   # sphere vs slope face (conservative: + margin across)
	if e_out > -margin:
		var r0: float = rail[0]; var r1: float = rail[1]; var rh: float = rail[2]
		if true:
			var dx := maxf(maxf(r0 - e_out, e_out - r1), 0.0); var dy := maxf(y - rh, 0.0)
			pen = maxf(pen, margin - Vector2(dx, dy).length())
		var g := 0.0 if e_out < 0.55 else -(e_out - 0.55) * 7.5 / 8.45
		pen = maxf(pen, g + margin - y)
	if absf(d) < W + margin: pen = maxf(pen, margin - y)   # the road itself
	for L in lamps:
		var b: Vector3 = L[0]; var t: Vector3 = L[1]
		if p.y < b.y + 6.8:
			pen = maxf(pen, lamp_r + margin - Vector2(p.x - b.x, p.z - b.z).length())
		var top := b + Vector3(0, 6.5, 0)
		pen = maxf(pen, 0.15 + margin - _seg_dist(p, top, t))
	return pen

static func _seg_dist(p: Vector3, a: Vector3, b: Vector3) -> float:
	var ab := b - a; var t := clampf((p - a).dot(ab) / maxf(ab.length_squared(), 1e-9), 0.0, 1.0)
	return (p - (a + ab * t)).length()

## spring arm: the farthest point on look -> pos that clears; if even the look point is buried, lift the camera
func fix(pos: Vector3, look: Vector3) -> Vector3:
	if clip(pos) <= 0.0: return pos
	var lo := 0.0; var hi := 1.0
	if clip(look) > 0.0:
		var q := pos
		for k in 40:
			q.y += 0.25
			if clip(q) <= 0.0: return q
		return q
	for k in 14:
		var m := (lo + hi) * 0.5
		if clip(look.lerp(pos, m)) <= 0.0: lo = m
		else: hi = m
	return look.lerp(pos, lo)
