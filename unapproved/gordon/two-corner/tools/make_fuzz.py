"""Generate a batch of random scripted races: seeds, picks (fewer than 3 -> timer auto-fill), and per-phase QTE inputs
[entry, apex, exit]. Each phase is null (unplayed = 0), 0, 1, a short decimal, a k/1024 value, or an arbitrary double written
as "0x<16 hex>" IEEE-754 bits (exact on both sides; Godot's decimal parser is not correctly rounded).
Usage: python3 tools/make_fuzz.py [n=300] [out=spec/inputs/fuzz300.json]"""
import json, random, struct, sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
R = random.Random(7)
def hx(x): return "0x%016x" % struct.unpack("<Q", struct.pack("<d", x))[0]
def phase():
    k = R.random()
    if k < 0.15: return None
    if k < 0.22: return 0.0
    if k < 0.30: return 1.0
    if k < 0.50: return round(R.random(), 3)
    if k < 0.65: return R.randrange(0, 1025) / 1024
    return hx(R.random())
races = []
for k in range(n):
    corners = []
    for _ in range(2):
        m = R.choice([3, 3, 3, 2, 1, 0])
        corners.append({"pick": R.sample(range(6), m), "qte": [phase(), phase(), phase()]})
    races.append({"seed": R.randrange(0, 2**53) if k % 3 else R.randrange(0, 100000), "corners": corners})
json.dump({"races": races}, open(sys.argv[2] if len(sys.argv) > 2 else "spec/inputs/fuzz300.json", "w"))
