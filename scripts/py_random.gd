## Exact port of CPython's random.Random: MT19937, random(), choices(weights). Ints are int64; every
## 32-bit product goes through _mul32 so nothing overflows.
extends RefCounted

const N := 624
const M := 397
var mt := PackedInt64Array()
var mti := N + 1
var draws := 0
var seed_value := 0

func _init(s: int = 0) -> void:
	seed_py(s)

static func _mul32(a: int, b: int) -> int:
	return (((((a >> 16) * b) & 0xFFFF) << 16) + (a & 0xFFFF) * b) & 0xFFFFFFFF

func seed_py(s: int) -> void:
	seed_value = s
	draws = 0
	var n: int = absi(s)
	var key: Array[int] = []
	while n > 0:
		key.append(n & 0xFFFFFFFF)
		n = n >> 32
	if key.is_empty():
		key.append(0)
	_init_by_array(key)

func _init_genrand(s: int) -> void:
	mt.resize(N)
	mt[0] = s & 0xFFFFFFFF
	for i in range(1, N):
		var p: int = mt[i - 1] ^ (mt[i - 1] >> 30)
		mt[i] = (_mul32(1812433253, p) + i) & 0xFFFFFFFF
	mti = N

func _init_by_array(key: Array[int]) -> void:
	_init_genrand(19650218)
	var i := 1
	var j := 0
	var k: int = maxi(N, key.size())
	while k > 0:
		var p: int = mt[i - 1] ^ (mt[i - 1] >> 30)
		mt[i] = ((mt[i] ^ _mul32(p, 1664525)) + key[j] + j) & 0xFFFFFFFF
		i += 1
		j += 1
		if i >= N:
			mt[0] = mt[N - 1]
			i = 1
		if j >= key.size():
			j = 0
		k -= 1
	k = N - 1
	while k > 0:
		var p: int = mt[i - 1] ^ (mt[i - 1] >> 30)
		mt[i] = ((mt[i] ^ _mul32(p, 1566083941)) - i) & 0xFFFFFFFF
		i += 1
		if i >= N:
			mt[0] = mt[N - 1]
			i = 1
		k -= 1
	mt[0] = 0x80000000

func _genrand() -> int:
	var y: int
	if mti >= N:
		var kk := 0
		while kk < N - M:
			y = (mt[kk] & 0x80000000) | (mt[kk + 1] & 0x7FFFFFFF)
			mt[kk] = mt[kk + M] ^ (y >> 1) ^ (0x9908B0DF if (y & 1) else 0)
			kk += 1
		while kk < N - 1:
			y = (mt[kk] & 0x80000000) | (mt[kk + 1] & 0x7FFFFFFF)
			mt[kk] = mt[kk + (M - N)] ^ (y >> 1) ^ (0x9908B0DF if (y & 1) else 0)
			kk += 1
		y = (mt[N - 1] & 0x80000000) | (mt[0] & 0x7FFFFFFF)
		mt[N - 1] = mt[M - 1] ^ (y >> 1) ^ (0x9908B0DF if (y & 1) else 0)
		mti = 0
	y = mt[mti]
	mti += 1
	y ^= (y >> 11)
	y ^= (y << 7) & 0x9D2C5680
	y ^= (y << 15) & 0xEFC60000
	y ^= (y >> 18)
	return y & 0xFFFFFFFF

func random() -> float:
	draws += 1
	var a: int = _genrand() >> 5
	var b: int = _genrand() >> 6
	return (float(a) * 67108864.0 + float(b)) * (1.0 / 9007199254740992.0)

## random.choices(pop, weights=w, k): bisect_right over cumulative weights with hi = n - 1
func choices(pop: Array, weights: Array, k: int = 1) -> Array:
	var cum: Array[float] = []
	var acc := 0.0
	for i in weights.size():
		acc = weights[0] if i == 0 else acc + weights[i]
		cum.append(acc)
	var total: float = cum[cum.size() - 1] + 0.0
	var hi: int = pop.size() - 1
	var out := []
	for t in k:
		var x: float = random() * total
		var lo := 0
		var h := hi
		while lo < h:
			var mid: int = (lo + h) >> 1
			if x < cum[mid]:
				h = mid
			else:
				lo = mid + 1
		out.append(pop[lo])
	return out

static func restore(s: int, n_draws: int):
	var r = load("res://scripts/py_random.gd").new(s)
	for i in n_draws:
		r.random()
	return r
