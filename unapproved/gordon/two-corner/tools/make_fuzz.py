"""Generate a batch of random scripted races (seeds, picks incl. partial -> autofill, timings 1..10)."""
import json, random, sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
R = random.Random(7)
races = []
for k in range(n):
    corners = []
    for _ in range(2):
        m = R.choice([3, 3, 3, 2, 1, 0])
        corners.append({"pick": R.sample(range(6), m), "timing": R.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 5.5, 9.9])})
    races.append({"seed": R.randrange(0, 2**53) if k % 3 else R.randrange(0, 100000), "corners": corners})
json.dump({"races": races}, open(sys.argv[2] if len(sys.argv) > 2 else "spec/inputs/fuzz.json", "w"))
