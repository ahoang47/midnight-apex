## G2 heat / load gauges: 1:1 port of sim/velocity_shift/heat.py HeatGauges (+ equations.heat_share_mult, heat_capacity,
## overrun_mult) at globals.gd PIN_COMMIT. Gordon [godot], touge-race. POW = engine heat, HAN = suspension load,
## EN = brake / tyre heat. Arrays are in HEAT_ORDER (POW, HAN, EN). A full gauge locks; it unlocks once load < release x cap
## (HEAT_RELEASE for the player, BOSS_HEAT_RELEASE for the rival). All three locked = limp (LIMP_MULT, least-loaded gauge).
## Calibration (avg_heat_demand, track_wear) is computed by the sim and generated into globals.gd, never re-derived here.
extends RefCounted
const C = preload("res://scripts/globals.gd")
const IDX := {"P": 0, "H": 1, "E": 2}   # equations._STANCE_INDEX
const ORDER := ["P", "H", "E"]          # equations._INDEX_STANCE
const EPS := 1e-9                       # heat.py _EPS

var cap: Array = [0.0, 0.0, 0.0]
var rec: Array = [0.0, 0.0, 0.0]
var release: float
var lock_on_passive: bool
var wear: Array
var load: Array = [0.0, 0.0, 0.0]
var locked: Array = [false, false, false]
var uses: Array = [0, 0, 0]

## heat.py build_shares (POW, HAN, EN)
static func build_shares(p: float, e: float, h: float) -> Array:
	var tot := p + e + h
	if tot <= 0: return [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]
	return [p / tot, h / tot, e / tot]

## equations.py heat_share_mult: 3 s**e / sum(s**e)
static func heat_share_mult(shares: Array) -> Array:
	var se := []
	for x in shares: se.append(pow(maxf(0.0, float(x)), C.HEAT_SHARE_EXP))
	var tot := _py_sum(se)   # sum(se) in CPython 3.12+ is compensated (Neumaier)
	if tot <= 0: return [1.0, 1.0, 1.0]
	return [3.0 * se[0] / tot, 3.0 * se[1] / tot, 3.0 * se[2] / tot]

static func _py_sum(xs: Array) -> float:   # CPython 3.12+ sum() (Neumaier), same as combat.gd py_sum
	var f: float = 0.0 + float(xs[0]); var c := 0.0
	for i in range(1, xs.size()):
		var x: float = xs[i]; var t := f + x
		if absf(f) >= absf(x): c += (f - t) + x
		else: c += (x - t) + f
		f = t
	if c != 0.0 and is_finite(c): f += c
	return f

## equations.py overrun_mult
static func overrun_mult(x: float) -> float:
	if x <= 0.0: return 1.0
	return maxf(C.OVERRUN_FLOOR, 1.0 - C.OVERRUN_SLOPE * x)

func _init(shares: Array, r: float, wear_: Array, cap_turns: float, recovery: float, release_: float, lock_on_passive_: bool) -> void:
	var k := heat_share_mult(shares); var rr := pow(r, C.HEAT_R_EXP)
	for i in 3:   # equations.heat_capacity
		var a: float = C.AVG_HEAT_DEMAND[i]
		cap[i] = maxf(cap_turns * a * k[i] * rr, EPS)
		rec[i] = recovery * a * k[i] * rr
	release = release_; lock_on_passive = lock_on_passive_; wear = wear_.duplicate()

static func for_player(p: float, e: float, h: float, r: float, wear_: Array):
	return load("res://scripts/heat.gd").new(build_shares(p, e, h), r, wear_, C.HEAT_CAP_TURNS, C.HEAT_RECOVERY, C.HEAT_RELEASE, true)

static func for_boss(p: float, e: float, h: float, wear_: Array):
	return load("res://scripts/heat.gd").new(build_shares(p, e, h), 1.0, wear_, C.BOSS_HEAT_CAP_TURNS, C.BOSS_HEAT_RECOVERY, C.BOSS_HEAT_RELEASE, C.BOSS_HEAT_LOCK_ON_PASSIVE)

func copy():
	var g = load("res://scripts/heat.gd").new([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0], 1.0, wear, 1.0, 1.0, release, lock_on_passive)
	g.cap = cap.duplicate(); g.rec = rec.duplicate(); g.load = load.duplicate(); g.locked = locked.duplicate(); g.uses = uses.duplicate()
	return g

func begin_turn() -> void: uses = [0, 0, 0]

func cost(stance: String, corner: String) -> float:
	var i: int = IDX[stance]
	return C.HEAT_BASE_COST * float(C.CORNER_HEAT_COST[corner][i]) * float(wear[i]) * (1.0 + C.HEAT_REPEAT_SURCHARGE * uses[i])

func selectable(stance: String) -> bool: return not locked[IDX[stance]]
func all_locked() -> bool: return locked[0] and locked[1] and locked[2]

func overrun_if(stance: String, corner: String) -> float:
	var i: int = IDX[stance]
	return maxf(0.0, load[i] + cost(stance, corner) - cap[i]) / cap[i]

func mult_if(stance: String, corner: String) -> float:
	if all_locked(): return C.LIMP_MULT
	return overrun_mult(overrun_if(stance, corner))

## load / capacity per gauge, HEAT_ORDER
func fill() -> Array: return [load[0] / cap[0], load[1] / cap[1], load[2] / cap[2]]

func least_loaded(only_unlocked: bool) -> String:
	var best = null; var bi := -1
	for i in 3:
		if only_unlocked and locked[i]: continue
		var f: float = load[i] / cap[i]
		if best == null or f < best: best = f; bi = i
	return ORDER[bi]

func _lock_new() -> void:
	for i in 3:
		if load[i] >= cap[i] - EPS: locked[i] = true

## heat.py play: returns {mult, x, limp}
func play(stance: String, corner: String) -> Dictionary:
	var limp := all_locked()
	var i: int = IDX[stance]
	assert(limp or not locked[i], "%s is locked (gauge full)" % stance)
	var x := overrun_if(stance, corner)
	load[i] += cost(stance, corner)
	uses[i] += 1
	_lock_new()
	return {"mult": C.LIMP_MULT if limp else overrun_mult(x), "x": 0.0 if limp else x, "limp": limp}

## heat.py end_turn: passive load (can lock unless lock_on_passive is false), recovery, then release
func end_turn(corner: String) -> void:
	for i in 3: load[i] += float(C.CORNER_HEAT_PASSIVE[corner][i]) * float(wear[i])
	if lock_on_passive: _lock_new()
	for i in 3:
		load[i] = maxf(0.0, load[i] - rec[i])
		if locked[i] and load[i] < release * cap[i] - EPS: locked[i] = false

## heat.py boss_stance: the line's stance; if locked, the least-loaded unlocked one; all locked -> limp on the least loaded
static func boss_stance(g, wanted: String) -> String:
	if g.all_locked(): return g.least_loaded(false)
	if g.selectable(wanted): return wanted
	return g.least_loaded(true)
