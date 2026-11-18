"""Fine X sweep on B3 (setup base): kits on tune per district at cap, kits shared by Street and Wangan (a kit that is on
tune in both = mod type does not matter), and the highest X at which the pattern kit still reaches each tune."""
import json, os
from mod_skill import *

def on_tune(X, rnd, d, earned=None):
    e = CEIL[rnd] if earned is None else earned
    return {k for k in KITS if (lambda r: r[1] < 0.5 and r[2])(alloc(BASES["B3_setup"], [(SI[c], e) for c in k], X, d))}

rows = []
for i in range(50, 81, 2):
    X = i / 100
    s = [on_tune(X, n, d) for n, d in enumerate(DIST)]
    rows.append(dict(X=X, street=len(s[0]), wangan=len(s[1]), touge=len(s[2]), shared_sw=len(s[0] & s[1]),
                     all3=len(s[0] & s[1] & s[2]), pattern_ok=all(E.MOD_SLOT_PATTERN[d] in [ "".join(sorted(k, key="PHE".index)) for k in s[n]] or "".join(sorted(E.MOD_SLOT_PATTERN[d], key="PHE".index)) in s[n] for n, d in enumerate(DIST))))
xmax = {}
for n, d in enumerate(DIST):
    pat = "".join(sorted(E.MOD_SLOT_PATTERN[d], key="PHE".index)); X = 0.34
    while X <= 1.0001 and alloc(BASES["B3_setup"], [(SI[c], CEIL[n]) for c in pat], X, d)[1] < 0.05:
        X += 0.01
    xmax[d] = round(X - 0.01, 2)
json.dump(dict(rows=rows, pattern_xmax=xmax), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sweep_fine.json"), "w"), indent=1)
for r in rows: print(r)
print("pattern kit reaches the tune at cap up to X =", xmax)
