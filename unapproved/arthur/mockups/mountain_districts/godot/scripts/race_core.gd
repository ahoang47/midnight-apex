## Engine-agnostic race state machine for the two-corner test (mirror of threejs/src/core/raceCore.js).
## Phases: SELECT -> TIMING -> RESULT -> (next corner) ... -> FINISHED
## TIMING holds the three per-phase QTEs (Entry, Apex, Exit) and the playback; submit_qte() takes the three raw scores
## (null = unplayed = 0, Austin) and resolves the turn with the pinned sim's averaging (combat.gd resolve_turn).
extends RefCounted
signal event(type: String, data: Dictionary)

const C = preload("res://scripts/sim_constants.gd")
const Combat = preload("res://scripts/combat.gd")
const PyRandom = preload("res://scripts/py_random.gd")

## Godot-only / prototype UX constants (NOT sim numbers)
const STRAIGHT_DURATION := 12.0  # guide §1.2; 8/10/12 s is an OPEN decision (design/02 item 5)

var cfg: Dictionary
var seed_value: int
var player: Dictionary
var opponent: Dictionary
var rng
var corner_index := -1
var phase := ""
var line := ""
var line_index := -1
var hand: Array = []
var picks: Array = []
var qte_in = null          # this turn's three phase inputs as given (null = unplayed)
var build := ""
var cum_p := 0.0
var cum_o := 0.0
var history: Array = []
var result = null
var autofilled := false

static func stats_from_config(c: Dictionary) -> Dictionary:
	var opp_total: float = C.ALL[c.stats.opp_total_const]
	var r: float = C.LADDER_R[int(c.stats.ladder_rung)]
	var p := opp_total * r / 3.0
	var o := opp_total / 3.0
	return {"player": {"name": c.player.name, "pow": p, "en": p, "han": p}, "opponent": {"name": c.opponent.name, "pow": o, "en": o, "han": o}}

## the build id + sim pin this game was built from (godot/spec/build.json, tools/stamp_build.py)
static func build_info() -> Dictionary:
	var f := "res://spec/build.json"
	if not FileAccess.file_exists(f): return {"build": "unstamped", "sim": C.PIN_COMMIT}
	return JSON.parse_string(FileAccess.get_file_as_string(f))

## the race's fixed r (match.py:190-192) and the visible zone width (equations.py:346), same for Entry / Apex / Exit
func race_r() -> float:
	var p_tot: float = player.pow + player.en + player.han
	var o_tot: float = opponent.pow + opponent.en + opponent.han
	return p_tot / o_tot if o_tot != 0.0 else 1.0
func zone_width() -> float:
	return Combat.qte_zone_width(race_r(), float(cfg.get("qte_window_mod", 0.0)))
func zone_ms() -> float:
	return zone_width() * C.QTE_ZONE_BASE_MS

static func autofill(h: Array, pk: Array) -> Array:
	var out := pk.duplicate()
	while out.size() < 3:
		var rem := []
		for i in h.size():
			if not out.has(i): rem.append(i)
		var best := ""; var best_n := -1
		for s in ["P", "H", "E"]:
			var n := 0
			for i in rem:
				if h[i] == s: n += 1
			if n > best_n:
				best = s; best_n = n
		for i in rem:
			if h[i] == best:
				out.append(i); break
	return out

func setup(c: Dictionary, s: int) -> void:
	cfg = c; seed_value = s
	var st := stats_from_config(c); player = st.player; opponent = st.opponent
	rng = PyRandom.new(s)
	cum_p = 0.0; cum_o = 0.0; history = []
	_start_corner(0)

func corner() -> Dictionary:
	return cfg.corners[corner_index]

func _start_corner(i: int) -> void:
	corner_index = i
	var c := corner()
	line = Combat.pick_line(c.district, c.corner, rng)            # 1) match.py: line first
	line_index = Combat.line_triples(c.district, c.corner).find(line)
	hand = Combat.draw_weighted_hand(player.pow, player.en, player.han, rng)  # 2) then hand
	picks = []; qte_in = null; result = null; autofilled = false
	phase = "SELECT"
	event.emit("deal", {"line": line, "hand": "".join(hand)})

## Entry tell: the opponent's Entry stance (P/E/H). Sim has no lane bluff (alt lines share Entry), so this is always the true Entry.
## The on-screen lane is Track.lane_for(stance): OUT = POW, MID = HAN, IN = EN.
func entry_tell() -> Dictionary:
	return {"stance": line[0]}

func can_pick(i: int) -> bool:
	return phase == "SELECT" and i >= 0 and i < hand.size() and not picks.has(i) and picks.size() < 3

func pick(i: int) -> bool:
	if not can_pick(i): return false
	picks.append(i); return true

func unpick() -> void:
	if phase == "SELECT" and not picks.is_empty(): picks.pop_back()

func lock() -> bool:
	if phase != "SELECT": return false
	if picks.size() < 3:
		picks = autofill(hand, picks); autofilled = true
	phase = "TIMING"
	event.emit("lock", {"player_line": player_line(), "autofilled": autofilled})
	return true

func player_line() -> String:
	var s := ""
	for i in picks: s += hand[i]
	return s

## the turn's three phase scores, Entry / Apex / Exit: a float in [0, 1] or null (unplayed / timed out = PHASE_QTE_UNPLAYED).
## Same path as match.py:201-215 for a 3-tuple callback: TurnState.player_qte_phases = phase_raw_qte each, player_qte = mean.
func submit_qte(phases: Array):
	if phase != "TIMING": return null
	assert(phases.size() == 3, "three phase scores")
	qte_in = phases.duplicate()
	var ph := []
	for v in phases: ph.append(Combat.phase_raw_qte(v))
	var p_cards := []
	for i in picks: p_cards.append(hand[i])
	var o_cards := []
	for ch in line: o_cards.append(ch)
	var res := Combat.resolve_turn(p_cards, o_cards, player, opponent, Combat.mean_phase_qte(phases), C.OPPONENT_QTE, int(cfg.max_turns), ph)
	cum_p += res.player_progress; cum_o += res.opponent_progress
	var c := corner()
	result = {"district": c.district, "corner": c.corner, "line": line, "line_index": line_index, "hand": "".join(hand),
		"picks": picks.duplicate(), "player_line": player_line(), "qte_in": qte_in.duplicate(), "qte_phases": res.player_qte_phases,
		"q_time": res.player_qte, "zone_width": zone_width(),
		"outcomes": res.outcomes, "player_clash": res.player_clash, "opponent_clash": res.opponent_clash,
		"cum_player": cum_p, "cum_opponent": cum_o, "rng_draws_after": rng.draws, "autofilled": autofilled}
	history.append(result)
	phase = "RESULT"
	event.emit("result", result)
	return result

func next() -> void:
	if phase != "RESULT": return
	if corner_index + 1 < cfg.corners.size():
		_start_corner(corner_index + 1)
	else:
		phase = "FINISHED"
		event.emit("finish", {"winner": winner()})

func winner() -> String:
	return "Player" if cum_p > cum_o else ("Opponent" if cum_o > cum_p else "Tie")

func lead() -> float:  # guide §0.1 / §10.1 display shares
	var t := cum_p + cum_o
	return 0.0 if t == 0.0 else (cum_p - cum_o) / t

func gap() -> float:
	return cum_p - cum_o

## ── state dump/load (TC3): seed + every completed turn's picks and exact phase scores; load REPLAYS them through this core,
## so totals are bit-exact (no decimal floats are parsed back). capture never touches the RNG. Records sim pin + build id.
static func fhex(x: float) -> String:
	var b := Combat._bits(x)
	return "0x%08x%08x" % [(b >> 32) & 0xffffffff, b & 0xffffffff]
static func fdec(v):   # input/token phase score: null, a JSON number, or "0x<16 hex>" IEEE-754 bits (exact)
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
	return {"schema": "TC3", "sim": C.PIN_COMMIT.substr(0, 7), "build": String(bi.build), "seed": seed_value, "rng_draws": rng.draws,
		"corner_index": corner_index, "phase": phase, "picks": picks.duplicate(), "auto": autofilled, "turns": turns,
		"cum_player": fhex(cum_p), "cum_opponent": fhex(cum_o)}

func load_state(c: Dictionary, d: Dictionary) -> void:
	assert(d.schema == "TC3", "outdated token" if str(d.get("schema", "")) in ["TC1", "TC2"] else "unknown schema")
	assert(String(d.sim) == C.PIN_COMMIT.substr(0, 7), "token is from sim %s; this build is sim %s: replay it on its own build" % [d.sim, C.PIN_COMMIT.substr(0, 7)])
	if String(d.build) != String(build_info().build):
		push_warning("TC3 token from build %s, running build %s (same sim pin): results replay; visuals may differ" % [d.build, build_info().build])
	setup(c, int(d.seed))
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

## ── compact token TC3:<sim7>:<build10>:<base64url(json)>:<CRC16 hex4> (CRC over "TC3" + sim7 + build + payload bytes) ──
## TC2 (pre-POW/EN/HAN rename, pin c3ffc41 and earlier) and TC1 (sim 212eaab) are refused as outdated tokens.
static func crc16(bytes: PackedByteArray) -> int:
	var crc := 0xFFFF
	for b in bytes:
		crc ^= (b << 8)
		for i in 8:
			crc = (((crc << 1) ^ 0x1021) & 0xFFFF) if (crc & 0x8000) else ((crc << 1) & 0xFFFF)
	return crc

static func encode_token(d: Dictionary) -> String:
	var payload: PackedByteArray = JSON.stringify(d, "", false, true).to_utf8_buffer()
	var head: PackedByteArray = ("TC3" + String(d.sim) + String(d.build)).to_utf8_buffer()
	var crc: String = "%04X" % crc16(head + payload)
	var b64: String = Marshalls.raw_to_base64(payload).replace("+", "-").replace("/", "_").replace("=", "")
	return "TC3:%s:%s:%s:%s" % [d.sim, d.build, b64, crc]

static func decode_token(tok: String) -> Dictionary:
	var parts := tok.strip_edges().split(":")
	if parts[0] == "TC1" or parts[0] == "TC2":
		push_error("outdated token (%s): this build uses TC3 (POW/EN/HAN stance letters). Replay that token on the build that made it." % parts[0])
		return {}
	assert(parts[0] == "TC3" and parts.size() == 5, "bad token")
	var s := parts[3].replace("-", "+").replace("_", "/")
	while s.length() % 4 != 0: s += "="
	var payload: PackedByteArray = Marshalls.base64_to_raw(s)
	var calc: String = "%04X" % crc16(("TC3" + parts[1] + parts[2]).to_utf8_buffer() + payload)
	assert(calc == parts[4], "CRC mismatch")
	return JSON.parse_string(payload.get_string_from_utf8())
