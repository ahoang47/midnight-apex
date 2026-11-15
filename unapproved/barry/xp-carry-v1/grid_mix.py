"""Fix lever B: R2 boss-race story XP x b2 (after the boss; only story is below the cap, so only story-only feels it) plus
small early-rung opponent r lifts (LADDER_TARGET_R) on R2 mat2 / R2 oh1 / R3 mat2. Bosses, kid1 (= grind budget) unchanged."""
import itertools, json, carry as C
from velocity_shift import equations as E
L = E.STORY_XP_MULT; T = E.LADDER_TARGET_R; out = []
for b2, dm2, do1, dm3 in itertools.product((1.0, 1.5, 2.0), (0, .005, .01, .015), (0, .005, .01, .015, .02), (0, .005, .01, .015, .02, .03)):
    m = [list(r) for r in L]; m[1][6] = b2
    t = {k: list(v) for k, v in T.items()}
    t["wangan"][3] = round(T["wangan"][3] + dm2, 4); t["wangan"][4] = round(T["wangan"][4] + do1, 4); t["touge"][3] = round(T["touge"][3] + dm3, 4)
    with C.patched(STORY_XP_MULT=tuple(tuple(r) for r in m), LADDER_TARGET_R={k: tuple(v) for k, v in t.items()}):
        o = C.summary(True)
    s = o["story"]
    out.append(dict(b2=b2, dm2=dm2, do1=do1, dm3=dm3, min80=s["min80"], boss80=s["boss80"], enter=s["enter"], endL=s["endL"], rows=s["rows"],
                    mixed_wall=o["mixed"]["wall"], mixed_g=o["mixed"]["grinds"], hard_g=o["hard"]["grinds"], cap=(o["mixed"]["boss80"], o["hard"]["boss6060"]), cash=s["cash"]))
json.dump(out, open(__file__.replace(".py", ".json"), "w"))
ok = [x for x in out if min(x["min80"]) >= 50 and all(3 <= w <= 6 for w in x["mixed_wall"])]
ok.sort(key=lambda x: (x["dm2"] + x["do1"] + x["dm3"], x["b2"]))
print(len(ok))
for x in ok[:8]: print({k: x[k] for k in ("b2", "dm2", "do1", "dm3", "min80", "boss80", "enter", "endL", "mixed_wall", "mixed_g", "hard_g", "cap")})
