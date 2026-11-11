## 1:1 port of sim/velocity_shift/equations.py + combat.py playable engine (pinned commit). Stances are letters A/S/D.
extends RefCounted
const C = preload("res://scripts/sim_constants.gd")
const LETTERS := ["A", "S", "D"]  # _INDEX_STANCE order: Attack, Neutral (letter S = Stance.NEUTRAL; player-facing NEU, Q6 2026-11-11), Defend
const WIN := 1
const NEUTRAL := 0
const LOSS := -1

static func resolve_stance(a: String, b: String) -> int:
	if a == b:
		return NEUTRAL
	if (a == "A" and b == "S") or (a == "S" and b == "D") or (a == "D" and b == "A"):
		return WIN
	return LOSS

static func knot_window(r: float) -> float:
	var K: Array = C.KNOT_WINDOW_105
	if r <= K[0][0]:
		return K[0][1]
	for i in K.size() - 1:
		var x0: float = K[i][0]; var y0: float = K[i][1]; var x1: float = K[i + 1][0]; var y1: float = K[i + 1][1]
		if r <= x1:
			return minf(1.0, y0 + (y1 - y0) * (r - x0) / (x1 - x0))
	return minf(1.0, K[K.size() - 1][1])

## ── PROVISIONAL HOOK (Austin via Desmond, 2026-11-10) ───────────────────────
## Player timing window W(r) = 1.0 (window off) for the two-corner test.
## Barry's visible-QTE difficulty curve drops in HERE later (e.g. return knot_window(r)).
## No window-widening mods.
static func provisional_player_window(_r: float) -> float:
	return 1.0

static func kappa_for_length(L: int) -> float:
	if C.KAPPA_BY_LENGTH.has(L):
		return C.KAPPA_BY_LENGTH[L]
	var best: int = C.KAPPA_BY_LENGTH.keys()[0]
	for k in C.KAPPA_BY_LENGTH.keys():
		if absi(k - L) < absi(best - L):
			best = k
	return C.KAPPA_BY_LENGTH[best]

static func timing_value(q: float) -> float:
	q = 0.0 if q < 0.0 else (1.0 if q > 1.0 else q)
	var body: float = (1.0 - pow(1.0 - q, 2.0)) if C.TAU_GAMMA <= 0 else pow(q, C.TAU_GAMMA)
	return (1.0 - C.TAU_BETA) * body + C.TAU_BETA * pow(q, C.TAU_P_TOP)

static func clash_payoff(outcome: int, q: float) -> float:
	var t := timing_value(q)
	if outcome == WIN:
		return C.W0 + (1.0 - C.W0) * t
	if outcome == NEUTRAL:
		return C.T_MAX * t
	return C.L_MAX * t

static func stat_shares(p: float, e: float, h: float) -> Array:
	var tot := p + e + h
	if tot <= 0:
		return [0.0, 1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]
	return [tot, p / tot, e / tot, h / tot]

static func clash_progress(outcome: int, q_time: float, p: float, e: float, h: float, boss_total: float, kappa: float, scale_window: bool) -> float:
	var sh := stat_shares(p, e, h)
	var r: float = sh[0] / boss_total if boss_total != 0.0 else 1.0
	var V := pow(r, kappa)
	var w: float = provisional_player_window(r) if scale_window else 1.0
	var qe: float = q_time * w * (1.0 + C.ETA * (sh[3] - 1.0 / 3.0))
	qe = 0.0 if qe < 0.0 else (1.0 if qe > 1.0 else qe)
	var M: float
	if outcome == WIN:
		M = 1.0 + C.MU * (sh[1] - 1.0 / 3.0)
	else:
		M = 1.0 + C.MU * (sh[2] - 1.0 / 3.0)
	return V * clash_payoff(outcome, qe) * M

static func deck_weights(p: float, e: float, h: float) -> Array:
	var sh := stat_shares(p, e, h)
	var raw := [sh[1] * C.DECK_ALPHA + (1.0 - C.DECK_ALPHA) / 3.0, sh[3] * C.DECK_ALPHA + (1.0 - C.DECK_ALPHA) / 3.0, sh[2] * C.DECK_ALPHA + (1.0 - C.DECK_ALPHA) / 3.0]
	var s: float = 0.0 + raw[0] + raw[1] + raw[2]
	return [raw[0] / s, raw[1] / s, raw[2] / s]

static func line_probs() -> Array:
	var a: float = C.LINE_ADHERENCE
	return [a, (1.0 - a) * C.LINE_ALT_WEIGHTS["alt1"], (1.0 - a) * C.LINE_ALT_WEIGHTS["alt2"]]

static func line_triples(district: String, corner: String) -> Array:
	return C.LINE_SET_C[district.strip_edges().to_lower()][corner].duplicate()

static func pick_line(district: String, corner: String, rng) -> String:
	return rng.choices(line_triples(district, corner), line_probs(), 1)[0]

static func draw_weighted_hand(p: float, e: float, h: float, rng) -> Array:
	return rng.choices(LETTERS, deck_weights(p, e, h), C.HAND_SIZE)

static func resolve_turn(p_cards: Array, o_cards: Array, player: Dictionary, opponent: Dictionary, p_q: float, o_q: float, race_length: int) -> Dictionary:
	var outcomes := []
	for i in p_cards.size():
		outcomes.append(resolve_stance(p_cards[i], o_cards[i]))
	var boss_total: float = opponent.pow + opponent.en + opponent.han
	var kappa := kappa_for_length(race_length)
	var pc := []; var oc := []
	var pp := 0.0; var op := 0.0
	for o in outcomes:
		var pg := clash_progress(o, p_q, player.pow, player.en, player.han, boss_total, kappa, true)
		var og := clash_progress(-o, o_q, opponent.pow, opponent.en, opponent.han, boss_total, kappa, false)
		pp += pg; op += og; pc.append(pg); oc.append(og)
	var sum := 0
	for o in outcomes: sum += o
	return {"outcomes": outcomes, "battle_winner": "Player" if sum > 0 else ("Opponent" if sum < 0 else "Tie"),
		"player_clash": pc, "opponent_clash": oc, "player_progress": pp, "opponent_progress": op, "kappa": kappa}
