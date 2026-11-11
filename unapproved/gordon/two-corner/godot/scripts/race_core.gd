## Engine-agnostic race state machine for the two-corner test (mirror of threejs/src/core/raceCore.js).
## Phases: SELECT -> TIMING -> RESULT -> (next corner) ... -> FINISHED
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
var timing = null
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

static func autofill(h: Array, pk: Array) -> Array:
	var out := pk.duplicate()
	while out.size() < 3:
		var rem := []
		for i in h.size():
			if not out.has(i): rem.append(i)
		var best := ""; var best_n := -1
		for s in ["A", "S", "D"]:
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
	picks = []; timing = null; result = null; autofilled = false
	phase = "SELECT"
	event.emit("deal", {"line": line, "hand": "".join(hand)})

## Entry tell (lane). Sim has no lane bluff (alt lines share Entry), so the lane always shows the true Entry.
func entry_tell() -> Dictionary:
	var e := line[0]
	return {"stance": e, "lane": "outside" if e == "A" else ("center" if e == "S" else "inside")}

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

func submit_timing(score: float):
	if phase != "TIMING": return null
	score = clampf(score, C.PLAYER_QTE_MIN, C.PLAYER_QTE_MAX)
	timing = score
	var q := score / C.QTE_NORMALIZER  # qte_factor()
	var p_cards := []
	for i in picks: p_cards.append(hand[i])
	var o_cards := []
	for ch in line: o_cards.append(ch)
	var res := Combat.resolve_turn(p_cards, o_cards, player, opponent, q, C.OPPONENT_QTE, int(cfg.max_turns))
	cum_p += res.player_progress; cum_o += res.opponent_progress
	var c := corner()
	result = {"district": c.district, "corner": c.corner, "line": line, "line_index": line_index, "hand": "".join(hand),
		"picks": picks.duplicate(), "player_line": player_line(), "timing": score, "q_time": q,
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

## ── state dump/load: seed + replay counter (rng_draws); capture never touches the RNG ──
func dump() -> Dictionary:
	return {"schema": "TC1", "commit": C.PIN_COMMIT.substr(0, 7), "seed": seed_value, "rng_draws": rng.draws,
		"corner_index": corner_index, "phase": phase, "line": line, "hand": "".join(hand), "picks": picks.duplicate(),
		"timing": timing, "cum_player": cum_p, "cum_opponent": cum_o, "history": history.duplicate(true)}

func load_state(c: Dictionary, d: Dictionary) -> void:
	assert(d.schema == "TC1", "unknown schema")
	cfg = c; seed_value = int(d.seed)
	var st := stats_from_config(c); player = st.player; opponent = st.opponent
	rng = PyRandom.restore(seed_value, int(d.rng_draws))
	corner_index = int(d.corner_index); phase = d.phase; line = d.line
	hand = []
	for ch in String(d.hand): hand.append(ch)
	line_index = Combat.line_triples(corner().district, corner().corner).find(line)
	picks = []
	for x in d.picks: picks.append(int(x))
	timing = d.timing; cum_p = float(d.cum_player); cum_o = float(d.cum_opponent)
	history = []
	for h in d.history:
		var hh: Dictionary = h.duplicate(true)
		for k in ["picks", "outcomes"]:
			var a := []
			for x in hh[k]: a.append(int(x))
			hh[k] = a
		hh.rng_draws_after = int(hh.rng_draws_after); hh.line_index = int(hh.line_index)
		history.append(hh)
	result = history[-1] if phase == "RESULT" else null
	# replay desync check: re-derive this corner's line + hand from the seed
	var chk = PyRandom.new(seed_value)
	var l := ""; var h2 := ""
	for i in corner_index + 1:
		var cc: Dictionary = c.corners[i]
		l = Combat.pick_line(cc.district, cc.corner, chk)
		h2 = "".join(Combat.draw_weighted_hand(player.pow, player.en, player.han, chk))
	if l != line or h2 != d.hand or chk.draws != int(d.rng_draws):
		push_error("replay desync")
		assert(false, "replay desync")

## ── compact token TC1:<git7>:<base64url(json)>:<CRC16 hex4> ──
static func crc16(bytes: PackedByteArray) -> int:
	var crc := 0xFFFF
	for b in bytes:
		crc ^= (b << 8)
		for i in 8:
			crc = (((crc << 1) ^ 0x1021) & 0xFFFF) if (crc & 0x8000) else ((crc << 1) & 0xFFFF)
	return crc

static func encode_token(d: Dictionary) -> String:
	var payload: PackedByteArray = JSON.stringify(d, "", false, true).to_utf8_buffer()
	var head: PackedByteArray = ("TC1" + String(d.commit)).to_utf8_buffer()
	var crc: String = "%04X" % crc16(head + payload)
	var b64: String = Marshalls.raw_to_base64(payload).replace("+", "-").replace("/", "_").replace("=", "")
	return "TC1:%s:%s:%s" % [d.commit, b64, crc]

static func decode_token(tok: String) -> Dictionary:
	var parts := tok.strip_edges().split(":")
	assert(parts[0] == "TC1", "bad version")
	var s := parts[2].replace("-", "+").replace("_", "/")
	while s.length() % 4 != 0: s += "="
	var payload: PackedByteArray = Marshalls.base64_to_raw(s)
	var calc: String = "%04X" % crc16(("TC1" + parts[1]).to_utf8_buffer() + payload)
	assert(calc == parts[3], "CRC mismatch")
	return JSON.parse_string(payload.get_string_from_utf8())
