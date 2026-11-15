"""Lever A (story XP), targeted: R2 mat1+mat2 XP x a2 (paid after the mixed wall at mat1), R2 oh2 set to o2, R2 boss XP x b2
(after the boss: lifts the carried level into R3 kid1), R3 kid1..mat1 XP x a3, R3 oh2 set to o3. Opponents unchanged."""
import itertools, json, carry as C
from velocity_shift import equations as E
L = E.STORY_XP_MULT; out = []
LIVE = C.summary(True)
for a2, o2, b2, a3, o3 in itertools.product((1.0, 1.15, 1.3, 1.45), (0.2, 0.4, 0.6), (1.0, 1.5, 2.0, 2.5), (1.0, 1.15, 1.3), (0.4, 0.6, 0.8)):
    m = [list(r) for r in L]
    m[1][2] = m[1][3] = a2; m[1][5] = o2; m[1][6] = b2
    m[2][0] = m[2][1] = m[2][2] = a3; m[2][5] = o3
    with C.patched(STORY_XP_MULT=tuple(tuple(r) for r in m)):
        o = C.summary(True)
    s = o["story"]
    out.append(dict(a2=a2, o2=o2, b2=b2, a3=a3, o3=o3, min80=s["min80"], boss80=s["boss80"], enter=s["enter"], endL=s["endL"], rows=s["rows"],
                    mixed_wall=o["mixed"]["wall"], mixed_g=o["mixed"]["grinds"], hard_g=o["hard"]["grinds"], cap=(o["mixed"]["boss80"], o["hard"]["boss6060"]),
                    cash=s["cash"]))
json.dump(out, open(__file__.replace(".py", ".json"), "w"))
ok = [x for x in out if min(x["min80"]) >= 50 and all(3 <= w <= 6 for w in x["mixed_wall"]) and abs(x["boss80"][1] - 57.7) <= 4 and abs(x["boss80"][2] - 55.8) <= 4]
ok.sort(key=lambda x: (abs(x["a2"] - 1) + abs(x["o2"] - .6) + abs(x["b2"] - 1) + abs(x["a3"] - 1) + abs(x["o3"] - .8)))
print(len(ok))
for x in ok[:8]: print({k: x[k] for k in ("a2", "o2", "b2", "a3", "o3", "min80", "boss80", "enter", "endL", "mixed_wall", "hard_g", "cap")})
