## 1:1 port of sim/velocity_shift/equations.py + combat.py playable engine (pinned commit, see sim_constants.gd PIN_COMMIT). Stances are letters A/S/D.
## Pin f0efecf (Austin approved the re-pin 2026-11-11 10:56 PM PT): qte-v1 visible zone, no knot_window factor in clash_progress,
## Entry / Apex / Exit phase scores averaged into the turn's raw_qte. The old PROVISIONAL W=1 hook is gone (its hidden window no longer exists).
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

## LEGACY hidden window (equations.py:264). Not in clash math any more; only the generator of qte_zone_width.
static func knot_window(r: float) -> float:
	var K: Array = C.KNOT_WINDOW_105
	if r <= K[0][0]:
		return K[0][1]
	for i in K.size() - 1:
		var x0: float = K[i][0]; var y0: float = K[i][1]; var x1: float = K[i + 1][0]; var y1: float = K[i + 1][1]
		if r <= x1:
			return minf(1.0, y0 + (y1 - y0) * (r - x0) / (x1 - x0))
	return minf(1.0, K[K.size() - 1][1])

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

## equations.py:447-475 clash_progress: g = V * Phi(o, q_eff) * M,
## q_eff = clip(q_time * (1 + ETA * (han_share - 1/3)), 0, 1) (equations.py:465-466). No knot_window factor.
static func clash_progress(outcome: int, q_time: float, p: float, e: float, h: float, boss_total: float, kappa: float) -> float:
	var sh := stat_shares(p, e, h)
	var r: float = sh[0] / boss_total if boss_total != 0.0 else 1.0
	var V := pow(r, kappa)
	var qe: float = q_time * (1.0 + C.ETA * (sh[3] - 1.0 / 3.0))
	qe = 0.0 if qe < 0.0 else (1.0 if qe > 1.0 else qe)
	var M: float
	if outcome == WIN:
		M = 1.0 + C.MU * (sh[1] - 1.0 / 3.0)
	else:
		M = 1.0 + C.MU * (sh[2] - 1.0 / 3.0)
	return V * clash_payoff(outcome, qe) * M

# ── qte-v1 visible zone (equations.py:279-387) and per-phase QTE (equations.py:390-408) ──
## erf: line-for-line port of glibc 2.41 sysdeps/ieee754/dbl-64/s_erf.c __erf, which CPython's math.erf calls on this box
## (Python 3.13 / glibc 2.41: 300k random inputs, 0 mismatches). Coefficients are given as IEEE-754 bit patterns because
## Godot's decimal parser is not correctly rounded.
const _PP_BITS := [4593793367243283304, -4623844978884560621, -4639505510052718257, -4650069345988876060, -4685737207133104468]
const _QQ_BITS := [0, 4600839859364092937, 4589349767556288186, 4572508369437551375, 4549020217062988304, -4697082598652747488]
const _PA_BITS := [-4655778939758217928, 4601145003363971917, -4622995315929594895, 4599406442792952036, -4630716811330049812, 4585273783536293355, -4656230292307704001]
const _QA_BITS := [0, 4592332853260247843, 4603042691266866995, 4589840220683233703, 4593713817558660383, 4579014865432206620, 4578062215578719517]
const _RA_BITS := [-4646531662013963211, -4618947094890515616, -4601238440658278618, -4589396671920888947, -4583454195446177178, -4582672806012212302, -4587951525163904270, -4601657442552855972]
const _SA_BITS := [0, 4626224558917056135, 4639047418206938913, 4646352579956710001, 4648888102296496232, 4646254807205544724, 4637344925850578476, 4619083462031723155, -4634503139855918494]
const _RB_BITS := [-4646531662653919414, -4617997513926736418, -4597680399225743014, -4583516129954763368, -4574552727292087768, -4571148805341292142, -4576158261088339905]
const _SB_BITS := [0, 4629232622623347088, 4644439018692124426, 4654473423640940824, 4659254977712890986, 4657832632290065382, 4647055610571908963, -4596362252605379230]
const _ERX_BITS := 4605786869572042752
const _EFX_BITS := 4593793367243283305
static func _d(b: int) -> float:
	var a := PackedByteArray(); a.resize(8); a.encode_s64(0, b); return a.decode_double(0)
static func _bits(x: float) -> int:
	var a := PackedByteArray(); a.resize(8); a.encode_double(0, x); return a.decode_s64(0)
static var _c := {}
static func _cf(n: String) -> Array:
	if _c.is_empty():
		for k in ["PP", "QQ", "PA", "QA", "RA", "SA", "RB", "SB"]:
			var arr := []
			for b in _coef_bits(k): arr.append(_d(b))
			_c[k] = arr
	return _c[n]
static func _coef_bits(k: String) -> Array:
	match k:
		"PP": return _PP_BITS
		"QQ": return _QQ_BITS
		"PA": return _PA_BITS
		"QA": return _QA_BITS
		"RA": return _RA_BITS
		"SA": return _SA_BITS
		"RB": return _RB_BITS
	return _SB_BITS

static func erf(x: float) -> float:
	var hx: int = _bits(x) >> 32
	var ix: int = hx & 0x7fffffff
	if ix >= 0x7ff00000:
		return x if is_nan(x) else (1.0 if x > 0.0 else -1.0)
	var efx := _d(_EFX_BITS); var erx := _d(_ERX_BITS)
	if ix < 0x3feb0000:
		if ix < 0x3e300000:
			if ix < 0x00800000: return 0.0625 * (16.0 * x + (16.0 * efx) * x)
			return x + efx * x
		var pp := _cf("PP"); var qq := _cf("QQ")
		var z := x * x
		var r1: float = pp[0] + z * pp[1]; var z2 := z * z
		var r2: float = pp[2] + z * pp[3]; var z4 := z2 * z2
		var s1: float = 1.0 + z * qq[1]
		var s2: float = qq[2] + z * qq[3]
		var s3: float = qq[4] + z * qq[5]
		var r: float = r1 + z2 * r2 + z4 * pp[4]
		var s: float = s1 + z2 * s2 + z4 * s3
		var y: float = r / s
		return x + x * y
	if ix < 0x3ff40000:
		var pa := _cf("PA"); var qa := _cf("QA")
		var s := absf(x) - 1.0
		var P1: float = pa[0] + s * pa[1]; var s2 := s * s
		var Q1: float = 1.0 + s * qa[1]; var s4 := s2 * s2
		var P2: float = pa[2] + s * pa[3]; var s6 := s4 * s2
		var Q2: float = qa[2] + s * qa[3]
		var P3: float = pa[4] + s * pa[5]
		var Q3: float = qa[4] + s * qa[5]
		var Pv: float = P1 + s2 * P2 + s4 * P3 + s6 * pa[6]
		var Qv: float = Q1 + s2 * Q2 + s4 * Q3 + s6 * qa[6]
		return erx + Pv / Qv if hx >= 0 else -erx - Pv / Qv
	if ix >= 0x40180000:
		return 1.0 if hx >= 0 else -1.0   # one - tiny / tiny - one round to +-1 in double
	x = absf(x)
	var s := 1.0 / (x * x)
	var R: float; var S: float
	if ix < 0x4006DB6E:
		var ra := _cf("RA"); var sa := _cf("SA")
		var R1: float = ra[0] + s * ra[1]; var s2 := s * s
		var S1: float = 1.0 + s * sa[1]; var s4 := s2 * s2
		var R2: float = ra[2] + s * ra[3]; var s6 := s4 * s2
		var S2: float = sa[2] + s * sa[3]; var s8 := s4 * s4
		var R3: float = ra[4] + s * ra[5]
		var S3: float = sa[4] + s * sa[5]
		var R4: float = ra[6] + s * ra[7]
		var S4: float = sa[6] + s * sa[7]
		R = R1 + s2 * R2 + s4 * R3 + s6 * R4
		S = S1 + s2 * S2 + s4 * S3 + s6 * S4 + s8 * sa[8]
	else:
		var rb := _cf("RB"); var sb := _cf("SB")
		var R1: float = rb[0] + s * rb[1]; var s2 := s * s
		var S1: float = 1.0 + s * sb[1]; var s4 := s2 * s2
		var R2: float = rb[2] + s * rb[3]; var s6 := s4 * s2
		var S2: float = sb[2] + s * sb[3]
		var R3: float = rb[4] + s * rb[5]
		var S3: float = sb[4] + s * sb[5]
		var S4: float = sb[6] + s * sb[7]
		R = R1 + s2 * R2 + s4 * R3 + s6 * rb[6]
		S = S1 + s2 * S2 + s4 * S3 + s6 * S4
	var zz := _d(_bits(x) & ~0xffffffff)   # SET_LOW_WORD(z, 0)
	var rr: float = exp(-zz * zz - 0.5625) * exp((zz - x) * (zz + x) + R / S)
	return 1.0 - rr / x if hx >= 0 else rr / x - 1.0

## equations.py:279 expected_hit_quality: E[s] for one press, s = max(0, 1 - |e| / (w/2)), e ~ Normal(0, sigma)
static func expected_hit_quality(sigma_over_a0: float, width_over_w0: float) -> float:
	var a := width_over_w0; var s := sigma_over_a0
	if a <= 0.0: return 0.0
	if s <= 0.0: return 1.0
	var z := a / s
	return erf(z / sqrt(2.0)) - (s / a) * sqrt(2.0 / PI) * (1.0 - exp(-0.5 * z * z))

## equations.py:298 _qte_sigma_for_target (bisection, 80 steps)
static func _qte_sigma_for_target(target: float) -> float:
	assert(target > 0.0 and target < 1.0, "target must be in (0, 1)")
	var lo := 1e-8; var hi := 50.0
	for _i in 80:
		var mid := 0.5 * (lo + hi)
		if expected_hit_quality(mid, 1.0) > target: lo = mid
		else: hi = mid
	return 0.5 * (lo + hi)

## equations.py:312 _qte_width_for_target (bisection, 80 steps)
static func _qte_width_for_target(target: float, sigma_over_a0: float) -> float:
	if target <= 0.0: return 0.0
	if target >= 1.0 - 1e-15: return INF
	var lo := 1e-10; var hi := 50.0 * maxf(sigma_over_a0, 1e-8)
	for _i in 80:
		var mid := 0.5 * (lo + hi)
		if expected_hit_quality(sigma_over_a0, mid) < target: lo = mid
		else: hi = mid
	return 0.5 * (lo + hi)

## equations.py:328 qte_sigma_over_a0 (profile = "" means none)
static func qte_sigma_over_a0(profile: String = "", q_time = null) -> float:
	if profile != "":
		assert(C.QTE_SKILL_SIGMA_OVER_A0.has(profile), "unknown QTE skill profile")
		return C.QTE_SKILL_SIGMA_OVER_A0[profile]
	assert(q_time != null, "need a skill profile or a q_time")
	var q: float = q_time
	if q <= 0.0: return INF
	if q >= 1.0: return 0.0
	for name in C.QTE_SKILL_TARGET_E:
		if absf(q - float(C.QTE_SKILL_TARGET_E[name])) < 1e-12: return C.QTE_SKILL_SIGMA_OVER_A0[name]
	return _qte_sigma_for_target(q)

## equations.py:346 qte_zone_width: visible zone width / QTE_ZONE_BASE_MS at the race's fixed r. Same width for Entry, Apex
## and Exit; an unplayed phase times out after this visible sweep (Barry's proposal; Austin: unplayed = 0).
static func qte_zone_width(r: float, window_mod: float = 0.0) -> float:
	var target: float = C.AVERAGE_PLAY_Q * knot_window(r)
	var width: float
	if r >= float(C.KNOT_WINDOW_105[C.KNOT_WINDOW_105.size() - 1][0]) or absf(target - C.AVERAGE_PLAY_Q) < 1e-15:
		width = 1.0
	else:
		width = _qte_width_for_target(target, C.QTE_SKILL_SIGMA_OVER_A0["average"])
	width = width * (1.0 + window_mod)
	return 0.0 if width < 0.0 else width

## equations.py:372 raw_qte_score: expected raw score at the race's fixed r (no HAN, no knot_window)
static func raw_qte_score(r: float, profile: String = "", q_time = null, window_mod: float = 0.0) -> float:
	if profile == "" and q_time == null: profile = "average"
	var sig := qte_sigma_over_a0(profile, q_time)
	return expected_hit_quality(sig, qte_zone_width(r, window_mod))

## equations.py:390 phase_raw_qte: None / unplayed = PHASE_QTE_UNPLAYED (0, Austin)
static func phase_raw_qte(score) -> float:
	if score == null: return C.PHASE_QTE_UNPLAYED
	return float(score)

## equations.py:397 mean_phase_qte: a 3-list is averaged, a scalar is returned as-is. The sim's sum() is CPython 3.12+ sum(),
## which adds floats with Neumaier compensation (Objects/bltinmodule.c builtin_sum_impl): start 0 + x0, then t = f + x with
## c += (f - t) + x or (x - t) + f, and f + c at the end. Ported step for step so the mean is bit-identical.
static func py_sum(xs: Array) -> float:
	var f: float = 0.0 + float(xs[0]); var c := 0.0
	for i in range(1, xs.size()):
		var x: float = xs[i]; var t := f + x
		if absf(f) >= absf(x): c += (f - t) + x
		else: c += (x - t) + f
		f = t
	if c != 0.0 and is_finite(c): f += c
	return f
static func mean_phase_qte(value) -> float:
	if value is Array and value.size() == 3:
		var xs := []
		for v in value: xs.append(phase_raw_qte(v))
		return py_sum(xs) / 3.0
	if value == null: return C.PHASE_QTE_UNPLAYED
	return float(value)

## one press in the visible zone, from the score definition in expected_hit_quality's docstring (equations.py:280):
## s = max(0, 1 - |e| / (w/2)), e = press time - zone centre, w = zone width in ms. GAME-SIDE (the sim never sees a press).
static func hit_quality(err_ms: float, zone_ms: float) -> float:
	if zone_ms <= 0.0: return 0.0
	return maxf(0.0, 1.0 - absf(err_ms) / (zone_ms / 2.0))

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

## combat.py:62 resolve_turn. phases: TurnState.player_qte_phases (models.py:68). When it has 3 entries the turn's player_qte
## is mean_phase_qte(phases) and TurnResult.player_qte_phases = [phase_raw_qte(v)...] (combat.py:86-88); else p_q is used.
static func resolve_turn(p_cards: Array, o_cards: Array, player: Dictionary, opponent: Dictionary, p_q: float, o_q: float, race_length: int, phases: Array = []) -> Dictionary:
	var ph_out := []
	if not phases.is_empty():
		for v in phases: ph_out.append(phase_raw_qte(v))
		p_q = mean_phase_qte(phases)
	var outcomes := []
	for i in p_cards.size():
		outcomes.append(resolve_stance(p_cards[i], o_cards[i]))
	var boss_total: float = opponent.pow + opponent.en + opponent.han
	var kappa := kappa_for_length(race_length)
	var pc := []; var oc := []
	var pp := 0.0; var op := 0.0
	for o in outcomes:
		var pg := clash_progress(o, p_q, player.pow, player.en, player.han, boss_total, kappa)
		var og := clash_progress(-o, o_q, opponent.pow, opponent.en, opponent.han, boss_total, kappa)
		pp += pg; op += og; pc.append(pg); oc.append(og)
	var sum := 0
	for o in outcomes: sum += o
	return {"outcomes": outcomes, "battle_winner": "Player" if sum > 0 else ("Opponent" if sum < 0 else "Tie"),
		"player_clash": pc, "opponent_clash": oc, "player_progress": pp, "opponent_progress": op, "kappa": kappa,
		"player_qte": p_q, "player_qte_phases": ph_out}
