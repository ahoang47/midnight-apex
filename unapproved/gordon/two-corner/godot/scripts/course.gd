@tool
## Continuous display track (Austin 2026-11-11 ~10 PM PT: "the two corners should be in the same district as part of a
## continuous 2-turn track"): straight, corner, straight, corner, straight as ONE road. Display only, never read by the sim.
## Same conventions as track.gd: forward of the first straight is -Z, lateral d > 0 = right of travel (tangent x up).
## Corner radius / angle stay the display PLACEHOLDERS of spec/display.json road.by_code.
extends RefCounted
var segs: Array = []   # {k: "S"/"A", s0, len, x, z, tx, tz, R, sgn}
var length := 0.0
var x0 := 0.0; var z0 := 0.0; var tx0 := 0.0; var tz0 := -1.0

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

func point(s: float, d: float) -> Dictionary:
	var p := at(s)
	return {"x": p.x - p.tz * d, "z": p.z + p.tx * d, "tx": p.tx, "tz": p.tz}

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
		for k in cc.points:
			var p := point(S + R * A * float(k.a), float(k.d_in) * ins)
			out.append(Vector3(p.x, k.h, p.z))
		return out
