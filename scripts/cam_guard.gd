## TOUGE camera clearance (Gordon, touge-race; Austin t114u: "no camera may clip into the track geometry").
## Course (Austin 2026-11-20, authored terrain): the geometry is Arthur's, so the test is too. touge_env.gd holds the *_col.glb
## proxies (terrain, cut / rock faces, gallery walls, decks) and the sections' rails and lamp posts as BVHs; clip() asks it, plus
## the two surfaces that stay code: every road leg near the camera (legs_at) and the turnout lot floor (no proxy covers them).
## The analytic kit model (lattice face, verge profile, rail box, gallery walls, up faces, sheets) is gone from the course: it
## had to be kept in step with the procedural terrain by hand and is wrong for the authored one.
## Scroll straight (the treadmill between corners, still the code-built roadside, no assets yet): the analytic model below
##   inside: road edge W, gravel to W + 0.7, the lattice slope face rising 7.2 m over 5.0 m, top 7.6 to W + 8.7, hill to 10 m;
##   outside: W-beam rail box (rail_box), verge falling from W + 0.55 (0 m) to W + 9 (-7.5 m) and on at the same slope.
## Lamps from the lamp list (the straight's code lamps, Arthur's lot posts): post r lamp_r_m up to 6.6 m, 1.6 m arm at 6.5 m.
## Cedar cards are not modelled: main.gd hides any card within 5.5 m of the camera (build_lsc.py:254, as before).
## clip(p) > 0 = the near-plane sphere (radius margin_m) around p intersects geometry (under ground: margin + depth, so the QTE
## line of sight reads metres of hill). fix(pos, look) pulls the camera in toward its target along the line of sight (spring
## arm) until it clears, then lifts it if the target itself is buried.
extends RefCounted
const TougeEnv = preload("res://scripts/touge_env.gd")

var course; var W := 3.0; var drop := 1.0; var margin := 0.3; var rail: Array = [0.33, 0.7, 0.85]; var lamp_r := 0.3
var lot: Dictionary = {}; var lot_ins := 0.0   # lot side (-course.drop_at at the lot: the inside of turn 5)
var lamps: Array = []        # [Vector3 base, Vector3 arm tip]
var _ss: PackedFloat32Array; var _px: PackedFloat32Array; var _pz: PackedFloat32Array; var _py: PackedFloat32Array
var hint := 0.0
var cut := PackedByteArray(); var cut_a0 := 0.0   # course: touge_dressing cut table (1 = lattice on the inside cut), set by main.gd

func setup(course_, W_: float, D: Dictionary, G: Dictionary, lot_: Dictionary, lamp_items: Array) -> void:
	course = course_; W = W_; drop = float(D.get("drop_side", 1.0)); lot = lot_
	lot_ins = 0.0 if lot.is_empty() or not course.has_method("drop_at") else -float(course.drop_at((float(lot.s0) + float(lot.s1)) * 0.5))
	margin = float(G.margin_m); rail = G.rail_box; lamp_r = float(G.lamp_r_m)
	_ss = PackedFloat32Array(); _px = PackedFloat32Array(); _pz = PackedFloat32Array(); _py = PackedFloat32Array()
	straight = course.segs.size() == 1 and String(course.segs[0].k) == "S"
	if straight: lamps = lamp_items; return
	var s := -80.0
	while s <= course.length + 140.0:
		var p: Dictionary = course.at(s); _ss.append(s); _px.append(p.x); _pz.append(p.z); _py.append(course.elev(s, 0.0)); s += 1.0
	lamps = lamp_items
	_grid = {}
	for i in _ss.size():
		var k := Vector2i(floori(_px[i] / GCELL), floori(_pz[i] / GCELL))
		if not _grid.has(k): _grid[k] = []   # a plain Array: Packed*Array is a value type, so appending to _grid[k] through a cast
		(_grid[k] as Array).append(i)        # (as before) appended to a copy and every cell stayed empty -> legs_at() found no leg
const GCELL := 16.0
var _grid := {}
## every leg near (x, z): [s, d] on each, one per stretch of course (samples > 60 m apart along it), refined on the segment
func legs_at(x: float, z: float, reach := 30.0) -> Array:
	var best := {}   # stretch key -> [dd, i]
	var k0 := Vector2i(floori(x / GCELL), floori(z / GCELL)); var rc := int(ceil(reach / GCELL))
	var cand := []
	for gx in range(-rc, rc + 1):
		for gz in range(-rc, rc + 1):
			for i in _grid.get(k0 + Vector2i(gx, gz), []):
				var dx := x - _px[i]; var dz := z - _pz[i]; var dd := dx * dx + dz * dz
				if dd <= reach * reach: cand.append([dd, i])
	cand.sort_custom(func(a, b): return a[0] < b[0])
	var picked := []
	for c in cand:
		var far := true
		for q in picked:
			if absf(_ss[c[1]] - _ss[q]) < 60.0: far = false; break
		if far: picked.append(c[1])
	var out := []
	for i in picked:
		var s: float = _ss[i]; var p: Dictionary = course.at(s)
		s += clampf((x - float(p.x)) * float(p.tx) + (z - float(p.z)) * float(p.tz), -1.0, 1.0); p = course.at(s)
		out.append([s, -(x - float(p.x)) * float(p.tz) + (z - float(p.z)) * float(p.tx)])
	return out

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
	var pen := -1e9
	if straight:
		var sd := sd_of(p.x, p.z)
		pen = _clip_leg(float(sd[0]), float(sd[1]), p.y - course.elev(float(sd[0]), float(sd[1])))
	else:
		pen = TougeEnv.clip(p, margin)   # authored terrain / walls / decks / rails / lamp posts
		for L in legs_at(p.x, p.z, 16.0):   # the code road of every leg here (+ the lot floor): buried under it or within margin above
			var s: float = L[0]; var d: float = L[1]
			if s < -60.0 or s > course.length + 60.0: continue   # the road is built on [-60, length + 60] only
			var y: float = p.y - course.elev(s, d)
			var lim := W + margin
			if not lot.is_empty() and signf(d) == lot_ins: lim += _lot_depth(s)
			if absf(d) < lim and y > -1.0: pen = maxf(pen, margin - y)
			# the streamed lattice modules (code-placed, touge_dressing) on the inside where the authored cut stands (cut table) and the
			# lot's back-wall modules: the same slope face as the scroll straight, standing on top of the authored cut
			if cut.size() > 0 and s >= cut_a0 and s < cut_a0 + float(cut.size() - 1):
				var ins: float = -float(course.drop_at(s))
				var ld := _lot_depth(s) if (not lot.is_empty() and ins == lot_ins) else 0.0
				var e := d * ins - W
				if e > -margin and (ld > 0.0 or cut[int(round(s - cut_a0))] == 1):
					var yi: float = p.y - course.elev(s, ins * W)
					pen = maxf(pen, _inside_h(maxf(e, 0.0) + margin, ld) + margin - yi)
	for L in lamps:
		var b: Vector3 = L[0]; var t: Vector3 = L[1]
		if p.y < b.y + 6.8:
			pen = maxf(pen, lamp_r + margin - Vector2(p.x - b.x, p.z - b.z).length())
		var top := b + Vector3(0, 6.5, 0)
		pen = maxf(pen, 0.15 + margin - _seg_dist(p, top, t))
	return pen

## the scroll straight's code roadside at (s, d), y above its road plane (one leg, no flips, no lot)
func _clip_leg(s: float, d: float, y: float) -> float:
	var pen := -1e9
	var dr: float = course.drop_at(s) if course.has_method("drop_at") else drop
	var e_in := -d * dr - W; var e_out := d * dr - W   # beyond the inside / outside edge
	if e_in > -margin:
		pen = maxf(pen, _inside_h(maxf(e_in, 0.0) + margin, 0.0) + margin - y)   # sphere vs slope face (conservative: + margin across)
	if e_out > -margin:
		var r0: float = rail[0]; var r1: float = rail[1]; var rh: float = rail[2]
		var dx := maxf(maxf(r0 - e_out, e_out - r1), 0.0); var dy := maxf(y - rh, 0.0)
		pen = maxf(pen, margin - Vector2(dx, dy).length())
		var g := 0.0 if e_out < 0.55 else -(e_out - 0.55) * 7.5 / 8.45
		pen = maxf(pen, g + margin - y)
	if absf(d) < W + margin: pen = maxf(pen, margin - y)   # the road itself
	return pen

static func _seg_dist(p: Vector3, a: Vector3, b: Vector3) -> float:
	var ab := b - a; var t := clampf((p - a).dot(ab) / maxf(ab.length_squared(), 1e-9), 0.0, 1.0)
	return (p - (a + ab * t)).length()

## spring arm: the farthest point on pivot -> pos that clears. The pivot is the clear point of the sight line nearest the look
## point: a look point is an AIM point and may sit inside the model (the select-cam stops aim tgt_y 0.8-1.2 m UNDER the road,
## build_lsc.py:249/252), so it is not itself the pivot (void sweep WALL t09_plan_X / t10_plan_X: clip(look) = 1.5 sent every
## clipping stop pose to the lift branch, which raised it 10 m and returned it still 0.5-1.1 m inside turn 9/10's gallery wall).
## Only when the whole sight line is buried is the camera lifted.
func fix(pos: Vector3, look: Vector3) -> Vector3:
	if clip(pos) <= 0.0: return pos
	var piv := look
	if clip(look) > 0.0:
		var n := maxi(1, int(ceil(pos.distance_to(look) / 0.25))); var found := false
		for k in range(1, n):
			var q := look.lerp(pos, float(k) / float(n))
			if clip(q) <= 0.0: piv = q; found = true; break
		if not found:
			var q := pos
			for k in 80:
				q.y += 0.25
				if clip(q) <= 0.0: return q
			return q
	var lo := 0.0; var hi := 1.0
	for k in 14:
		var m := (lo + hi) * 0.5
		if clip(piv.lerp(pos, m)) <= 0.0: lo = m
		else: hi = m
	return piv.lerp(pos, lo)
