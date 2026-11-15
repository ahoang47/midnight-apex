"""Fix lever A: story XP only (STORY_XP_MULT). b1/b2 = R1/R2 boss-race XP mult (lifts the carried level for the next
kid1), e2/e3 = R2/R3 kid1..mat2 mult (front-load). Opponents unchanged."""
import itertools, json, carry as C
from velocity_shift import equations as E
L = E.STORY_XP_MULT; out = []
for b1, b2, e2, e3 in itertools.product((0.9, 1.35, 1.8, 2.25), (1.0, 1.5, 2.0, 2.5, 3.0), (1.0, 1.2, 1.4, 1.6), (1.0, 1.2, 1.4)):
    m = [list(r) for r in L]; m[0][6] = b1; m[1][6] = b2
    for k in range(4): m[1][k] = round(L[1][k] * e2, 3); m[2][k] = round(L[2][k] * e3, 3)
    with C.patched(STORY_XP_MULT=tuple(tuple(r) for r in m)):
        o = C.summary(True)
    s = o["story"]
    out.append(dict(b1=b1, b2=b2, e2=e2, e3=e3, min80=s["min80"], boss80=s["boss80"], enter=s["enter"], endL=s["endL"],
                    rows=s["rows"], mixed_wall=o["mixed"]["wall"], mixed_g=o["mixed"]["grinds"], hard_g=o["hard"]["grinds"],
                    cap=(o["mixed"]["boss80"], o["hard"]["boss6060"])))
json.dump(out, open(__file__.replace(".py", ".json"), "w"))
ok = [x for x in out if min(x["min80"]) >= 50 and all(3 <= w <= 6 for w in x["mixed_wall"])]
ok.sort(key=lambda x: (x["b1"] + x["b2"] + x["e2"] + x["e3"]))
print(len(ok))
for x in ok[:8]: print({k: x[k] for k in ("b1", "b2", "e2", "e3", "min80", "boss80", "enter", "endL", "mixed_wall", "hard_g", "cap")})
