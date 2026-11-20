## Engine-agnostic race state machine for the 10-turn Touge race (Gordon [godot], touge-race). Port of sim match.py run_match
## under the G2 heat gauges (heat.gd). Phases: SELECT -> TIMING -> RESULT -> (next corner) ... -> FINISHED.
## SELECT: the player plans Entry / Apex / Exit; any stance whose gauge is not locked can be planned, repeats allowed
## (the plan is checked against a projected copy of the gauges, so a stance that would be locked by an earlier pick of the
## same turn is refused, and with all three locked the engine's limp stance is the only one offered, as match.py does).
## TIMING holds the three per-phase QTEs; submit_qte() resolves the turn exactly in match.py order:
##   per clash: rival plays boss_stance under its gauges, player plays its pick; end_turn both; resolve_turn with the mults.
##   AI raw QTE is drawn once per turn from its own RNG (seed + OPPONENT_QTE_SEED_OFFSET), never the race RNG:
##   round_qte_score(clamp(gauss(OPPONENT_QTE * opponent_qte_ratio, SD), MIN, MAX)); sd 0 = the fixed mean (match.py).
## Touge cat / mouse (Austin): role chosen first, swap after swap_after_turn. Purely presentational: progress keeps summing,
## turns 1..swap are BANKED at the swap and the on-screen gap restarts from 0; the winner is cum totals (same as every race).
extends RefCounted
signal event(type: String, data: Dictionary)

const C = preload("res://scripts/globals.gd")
const Combat = preload("res://scripts/combat.gd")
const Heat = preload("res://scripts/heat.gd")
const PyRandom = preload("res://scripts/py_random.gd")

## Godot-only / prototype UX constants (NOT sim numbers)
const STRAIGHT_DURATION := 12.0  # fallback only: main.gd reads display.json pick_timer_s (12.0, Austin 2026-11-19; design/02 8 vs 12 open with Barry)
## the planning list the PLAN THE LINE panel indexes into: each stance up to 3 times (a turn has 3 clashes). Not a deck.
const HAND := ["P", "H", "E", "P", "H", "E", "P", "H", "E"]

var cfg: Dictionary
var seed_value: int
var player: Dictionary
var opponent: Dictionary
var rng
var o_qte_rng                  # match.py o_qte_rng: Random(seed + OPPONENT_QTE_SEED_OFFSET), or null when sd == 0
var o_qte_mean := 0.0
var o_qte_sd := 0.0
var o_qte_lo := 0.0
var o_qte_hi := 0.0
var p_heat
var o_heat
var corner_index := -1
var phase := ""
var line := ""
var line_index := -1
var hand: Array = HAND.duplicate()
var picks: Array = []
var qte_in = null
var build := ""
var cum_p := 0.0
var cum_o := 0.0
var history: Array = []
var result = null
var autofilled := false
var role_first := "chase"        # "lead" (mouse) or "chase" (cat) for turns 1..swap_after_turn
var banked_p := 0.0; var banked_o := 0.0; var banked := false

## TODO(barry): pending parity block. globals.gd CAR_STAT_BLOCKS[car] is null for every car, so both sides use the even,
## equal stand-in PARITY_PLACEHOLDER_UNITS (only shares and r reach the maths: r = 1, shares 1/3). Car choice is visual only.
## use_draft = race_config use_draft_blocks: Barry's blocks.json @ fd59332 (globals.gd CAR_DRAFT_BLOCKS, still UNAPPROVED).
static func car_stats(car: String, use_draft := false) -> Dictionary:
	var b = C.CAR_STAT_BLOCKS.get(car, null)
	if b == null and use_draft: b = C.CAR_DRAFT_BLOCKS.get(car, null)
	if b == null: b = C.PARITY_PLACEHOLDER_UNITS
	return {"pow": float(b.pow), "en": float(b.en), "han": float(b.han)}

## parity cap (Austin: "within the 1.07 cap"): blocks.json parity_cap_r (globals.gd CAR_BLOCKS_PARITY_CAP_R) = equations K_STEP
static func in_parity(a: Dictionary, b: Dictionary) -> bool:
	var ta: float = a.pow + a.en + a.han; var tb: float = b.pow + b.en + b.han
	if tb <= 0.0: return false
	var r := ta / tb
	return r <= C.CAR_BLOCKS_PARITY_CAP_R + 1e-12 and r >= 1.0 / C.CAR_BLOCKS_PARITY_CAP_R - 1e-12

static func stats_from_config(c: Dictionary) -> Dictionary:
	var ud := bool(c.get("use_draft_blocks", false))
	var p := car_stats(String(c.player.car), ud); var o := car_stats(String(c.opponent.car), ud)
	p.name = c.player.name; o.name = c.opponent.name
	return {"player": p, "opponent": o}

## Crew-boss stats: budget × BOSS_STAT_SHARES[district] as POW / HAN / EN (equations.py; Street 0.25/0.25/0.50,
## every other boss even 1/3). The 10-turn playtest still uses car blocks, not this. Ladder boss r = BOSS_TARGET_R
## (also the last entry of LADDER_TARGET_R).
static func boss_stats(district: String, budget: float) -> Dictionary:
	var sh: Array = C.BOSS_STAT_SHARES[district.to_lower()]
	return {"pow": budget * float(sh[0]), "han": budget * float(sh[1]), "en": budget * float(sh[2])}

static func build_info() -> Dictionary:
	var f := "res://spec/build.json"
	if not FileAccess.file_exists(f): return {"build": "unstamped", "sim": C.PIN_COMMIT}
	return JSON.parse_string(FileAccess.get_file_as_string(f))

func race_r() -> float:
	var p_tot: float = player.pow + player.en + player.han
	var o_tot: float = opponent.pow + opponent.en + opponent.han
	return p_tot / o_tot if o_tot != 0.0 else 1.0
func zone_width() -> float:
	return Combat.qte_zone_width(race_r(), float(cfg.get("qte_window_mod", 0.0)))
func zone_ms() -> float:
	return zone_width() * C.QTE_ZONE_BASE_MS

func setup(c: Dictionary, s: int, first_role: String = "chase") -> void:
	cfg = c; seed_value = s; role_first = first_role
	var st := stats_from_config(c); player = st.player; opponent = st.opponent
	rng = PyRandom.new(s)
	# match.py opponent_qte_mean / opponent_qte_spread: ratio None = unscaled OPPONENT_QTE; sd/min/max None = live constants.
	var ratio = c.get("opponent_qte_ratio", null)
	o_qte_mean = C.OPPONENT_QTE if ratio == null else C.OPPONENT_QTE * float(ratio)
	var sd = c.get("opponent_qte_sd", null)
	var lo = c.get("opponent_qte_min", null)
	var hi = c.get("opponent_qte_max", null)
	o_qte_sd = C.OPPONENT_QTE_SD if sd == null else float(sd)
	o_qte_lo = C.OPPONENT_QTE_MIN if lo == null else float(lo)
	o_qte_hi = C.OPPONENT_QTE_MAX if hi == null else float(hi)
	if o_qte_sd > 0.0:
		o_qte_rng = PyRandom.new(s + C.OPPONENT_QTE_SEED_OFFSET)
	else:
		o_qte_rng = null
	var wear: Array = C.TRACK_WEAR   # heat.track_wear(district, lap), computed by the sim (globals.gd)
	p_heat = Heat.for_player(player.pow, player.en, player.han, race_r(), wear)
	o_heat = Heat.for_boss(opponent.pow, opponent.en, opponent.han, wear)
	cum_p = 0.0; cum_o = 0.0; history = []; banked_p = 0.0; banked_o = 0.0; banked = false
	_start_corner(0)

func corner() -> Dictionary:
	return cfg.corners[corner_index]

func swap_after() -> int: return int(cfg.get("swap_after_turn", 5))
## player's role this corner: "lead" (mouse) or "chase" (cat)
func role() -> String:
	if corner_index < swap_after(): return role_first
	return "chase" if role_first == "lead" else "lead"

func _start_corner(i: int) -> void:
	corner_index = i
	var c := corner()
	line = Combat.pick_line(c.district, c.corner, rng)            # match.py: line first (one rng draw)
	line_index = Combat.line_triples(c.district, c.corner).find(line)
	p_heat.begin_turn(); o_heat.begin_turn()
	picks = []; qte_in = null; result = null; autofilled = false
	phase = "SELECT"
	event.emit("deal", {"line": line})

func entry_tell() -> Dictionary:
	return {"stance": line[0]}

## gauges after the planned picks so far (the rival's plays do not touch the player's gauges)
func projected():
	var g = p_heat.copy()
	for i in picks: g.play(hand[i], corner().corner)
	return g

## stances the player may plan for the next clash: unlocked ones, or the limp stance when all three are locked
func allowed() -> Array:
	var g = projected()
	if g.all_locked(): return [g.least_loaded(false)]
	var out := []
	for s in ["P", "H", "E"]:
		if g.selectable(s): out.append(s)
	return out

func can_pick(i: int) -> bool:
	return phase == "SELECT" and i >= 0 and i < hand.size() and not picks.has(i) and picks.size() < 3 and allowed().has(hand[i])

func pick(i: int) -> bool:
	if not can_pick(i): return false
	picks.append(i); return true

func first_free(stance: String) -> int:
	for i in hand.size():
		if hand[i] == stance and not picks.has(i): return i
	return -1

func unpick() -> void:
	if phase == "SELECT" and not picks.is_empty(): picks.pop_back()

## timer expiry: GODOT UX RULE (not sim) - Austin 2026-11-19 (t121 item 8): fill the unpicked clashes RANDOMLY among the
## allowed stances, clash by clash. The draw comes from its own RNG seeded from race seed + turn, never the sim rng (rng.draws and
## parity are untouched); replays store the resulting pick indices (dump / load_state), so they reproduce exactly.
static func autofill_seed(race_seed: int, turn: int) -> int:
	return (race_seed * 1000003 + turn * 7919 + 17) & 0x7FFFFFFF

func autofill() -> void:
	var ux := RandomNumberGenerator.new(); ux.seed = autofill_seed(seed_value, corner_index)
	while picks.size() < 3:
		var cand := []
		for i in hand.size():
			if not picks.has(i) and allowed().has(hand[i]): cand.append(i)
		if cand.is_empty():   # no free card of an allowed stance: previous least-loaded rule
			var g = projected()
			picks.append(first_free(g.least_loaded(false) if g.all_locked() else g.least_loaded(true)))
		else:
			picks.append(cand[ux.randi_range(0, cand.size() - 1)])

func lock() -> bool:
	if phase != "SELECT": return false
	if picks.size() < 3:
		autofill(); autofilled = true
	phase = "TIMING"
	event.emit("lock", {"player_line": player_line(), "autofilled": autofilled})
	return true

func player_line() -> String:
	var s := ""
	for i in picks: s += hand[i]
	return s

## One AI QTE draw as match.py: if sd == 0, the mean with no RNG; else gauss + clamp + round_qte_score.
## Pass a clone of o_qte_rng to peek without advancing the race's stream.
func _draw_opponent_qte(r) -> float:
	if r == null:
		return o_qte_mean
	return Combat.round_qte_score(clampf(r.gauss(o_qte_mean, o_qte_sd), o_qte_lo, o_qte_hi))

## preview (pure, no RNG, no state change): the turn result these phase scores would give
func preview(phases: Array) -> Dictionary:
	var pg = p_heat.copy(); var og = o_heat.copy()
	var peek = null if o_qte_rng == null else o_qte_rng.clone()
	return _resolve(pg, og, phases, _draw_opponent_qte(peek))

func _resolve(pg, og, phases: Array, o_qte: float) -> Dictionary:
	var k: String = corner().corner
	var pl := []; var ol := []; var pm := []; var om := []; var plimp := []; var olimp := []
	for ci in 3:
		var o_s: String = Heat.boss_stance(og, line[ci])          # match.py: rival first, under the boss heat rule
		var r_o: Dictionary = og.play(o_s, k)
		var p_s: String = pg.least_loaded(false) if pg.all_locked() else hand[picks[ci]]
		var r_p: Dictionary = pg.play(p_s, k)
		pl.append(p_s); ol.append(o_s); pm.append(r_p.mult); om.append(r_o.mult); plimp.append(r_p.limp); olimp.append(r_o.limp)
	pg.end_turn(k); og.end_turn(k)
	var res := Combat.resolve_turn(pl, ol, player, opponent, Combat.mean_phase_qte(phases), o_qte, int(cfg.max_turns), phases, pm, om)
	res.p_line = "".join(pl); res.o_line = "".join(ol); res.p_mults = pm; res.o_mults = om; res.p_limp = plimp; res.o_limp = olimp
	res.opponent_qte = o_qte
	return res

func submit_qte(phases: Array):
	if phase != "TIMING": return null
	assert(phases.size() == 3, "three phase scores")
	qte_in = phases.duplicate()
	var o_qte: float = _draw_opponent_qte(o_qte_rng)
	var res := _resolve(p_heat, o_heat, phases, o_qte)
	cum_p += res.player_progress; cum_o += res.opponent_progress
	var c := corner()
	result = {"district": c.district, "corner": c.corner, "line": line, "line_index": line_index, "rival_played": res.o_line,
		"picks": picks.duplicate(), "player_line": res.p_line, "qte_in": qte_in.duplicate(), "qte_phases": res.player_qte_phases,
		"q_time": res.player_qte, "opponent_qte": res.opponent_qte, "zone_width": zone_width(), "p_mults": res.p_mults, "o_mults": res.o_mults, "p_limp": res.p_limp,
		"outcomes": res.outcomes, "player_clash": res.player_clash, "opponent_clash": res.opponent_clash,
		"player_progress": res.player_progress, "opponent_progress": res.opponent_progress,
		"cum_player": cum_p, "cum_opponent": cum_o, "rng_draws_after": rng.draws, "autofilled": autofilled, "role": role(),
		"p_fill": p_heat.fill(), "p_locked": p_heat.locked.duplicate(), "o_fill": o_heat.fill(), "o_locked": o_heat.locked.duplicate()}
	history.append(result)
	phase = "RESULT"
	event.emit("result", result)
	return result

## true between the swap corner's RESULT and the next corner (main.gd plays the turnout here)
func at_swap() -> bool: return phase == "RESULT" and corner_index + 1 == swap_after() and corner_index + 1 < cfg.corners.size()

func next() -> void:
	if phase != "RESULT": return
	if corner_index + 1 == swap_after() and not banked:   # turnout: bank turns 1..swap (heat carries on untouched)
		banked_p = cum_p; banked_o = cum_o; banked = true
	if corner_index + 1 < cfg.corners.size():
		_start_corner(corner_index + 1)
	else:
		phase = "FINISHED"
		event.emit("finish", {"winner": winner()})

## winner: banked + turns after the swap = the plain cum totals, decided exactly as match.py (higher total, exact tie = Tie)
func winner() -> String:
	return "Player" if cum_p > cum_o else ("Opponent" if cum_o > cum_p else "Tie")

func lead() -> float:  # whole race share lead
	var t := cum_p + cum_o
	return 0.0 if t == 0.0 else (cum_p - cum_o) / t

func gap() -> float:
	return cum_p - cum_o

## this half's progress (since the swap, or since the start): what the touge gap meter and the drawn gap show
func seg_p() -> float: return cum_p - banked_p
func seg_o() -> float: return cum_o - banked_o
func seg_lead() -> float:
	var t := seg_p() + seg_o()
	return 0.0 if t == 0.0 else (seg_p() - seg_o()) / t
func seg_gap() -> float: return seg_p() - seg_o()

static func fhex(x: float) -> String:
	var b := Combat._bits(x)
	return "0x%08x%08x" % [(b >> 32) & 0xffffffff, b & 0xffffffff]
static func fdec(v):
	if v == null: return null
	if v is String:
		var t := String(v); assert(t.begins_with("0x") and t.length() == 18, "bad hex float")
		return Combat._d((t.substr(2, 8).hex_to_int() << 32) | t.substr(10, 8).hex_to_int())
	return float(v)

func dump() -> Dictionary:
	var bi := build_info()
	var turns := []
	for h in history:
		var q := []
		for v in h.qte_in: q.append(null if v == null else fhex(float(v)))
		turns.append({"picks": h.picks.duplicate(), "auto": h.autofilled, "qte": q})
	return {"schema": "TC4", "sim": C.PIN_COMMIT.substr(0, 7), "build": String(bi.build), "seed": seed_value, "rng_draws": rng.draws,
		"role_first": role_first, "corner_index": corner_index, "phase": phase, "picks": picks.duplicate(), "auto": autofilled, "turns": turns,
		"cum_player": fhex(cum_p), "cum_opponent": fhex(cum_o)}

func load_state(c: Dictionary, d: Dictionary) -> void:
	assert(d.schema == "TC4", "outdated token" if str(d.get("schema", "")) in ["TC1", "TC2", "TC3"] else "unknown schema")
	assert(String(d.sim) == C.PIN_COMMIT.substr(0, 7), "token is from sim %s; this build is sim %s: replay it on its own build" % [d.sim, C.PIN_COMMIT.substr(0, 7)])
	if String(d.build) != String(build_info().build):
		push_warning("TC4 token from build %s, running build %s (same sim pin): results replay; visuals may differ" % [d.build, build_info().build])
	setup(c, int(d.seed), String(d.role_first))
	for t in d.turns:
		for i in t.picks: pick(int(i))
		lock(); autofilled = bool(t.auto)
		var q := []
		for v in t.qte: q.append(fdec(v))
		submit_qte(q); history[-1].autofilled = autofilled
		if corner_index < int(d.corner_index) or String(d.phase) == "FINISHED": next()
	if phase == "SELECT":
		for i in d.picks: pick(int(i))
		if String(d.phase) == "TIMING":
			lock(); autofilled = bool(d.auto)
	if phase != String(d.phase) or corner_index != int(d.corner_index) or rng.draws != int(d.rng_draws) \
			or fhex(cum_p) != String(d.cum_player) or fhex(cum_o) != String(d.cum_opponent):
		push_error("replay desync")
		assert(false, "replay desync")

## ── compact token TC4:<sim7>:<build10>:<base64url(json)>:<CRC16 hex4> (CRC over "TC4" + sim7 + build + payload bytes) ──
## TC1-TC3 (card-draw sims) are refused as outdated tokens; TC4 = G2 heat touge race.
static func crc16(bytes: PackedByteArray) -> int:
	var crc := 0xFFFF
	for b in bytes:
		crc ^= (b << 8)
		for i in 8:
			crc = (((crc << 1) ^ 0x1021) & 0xFFFF) if (crc & 0x8000) else ((crc << 1) & 0xFFFF)
	return crc

static func encode_token(d: Dictionary) -> String:
	var payload: PackedByteArray = JSON.stringify(d, "", false, true).to_utf8_buffer()
	var head: PackedByteArray = ("TC4" + String(d.sim) + String(d.build)).to_utf8_buffer()
	var crc: String = "%04X" % crc16(head + payload)
	var b64: String = Marshalls.raw_to_base64(payload).replace("+", "-").replace("/", "_").replace("=", "")
	return "TC4:%s:%s:%s:%s" % [d.sim, d.build, b64, crc]

static func decode_token(tok: String) -> Dictionary:
	var parts := tok.strip_edges().split(":")
	if parts[0] == "TC1" or parts[0] == "TC2" or parts[0] == "TC3":
		push_error("outdated token (%s): this build uses TC4 (G2 heat touge race). Replay that token on the build that made it." % parts[0])
		return {}
	assert(parts[0] == "TC4" and parts.size() == 5, "bad token")
	var s := parts[3].replace("-", "+").replace("_", "/")
	while s.length() % 4 != 0: s += "="
	var payload: PackedByteArray = Marshalls.base64_to_raw(s)
	var calc: String = "%04X" % crc16(("TC4" + parts[1] + parts[2]).to_utf8_buffer() + payload)
	assert(calc == parts[4], "CRC mismatch")
	return JSON.parse_string(payload.get_string_from_utf8())
