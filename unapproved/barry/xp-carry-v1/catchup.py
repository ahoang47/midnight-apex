"""Fix lever C (story_xp entry-level scaling): story races pay the live nominal XP (as if entered at the previous cap)
plus a catch-up share of the XP the player is short of that cap: k x [X(prev cap) - X(entry)], paid on kid1/kid2/mat1
(shares SHARE). A player entering at the cap (mixed / hard) gets exactly the live XP. Optionally R2 boss XP x b2."""
import itertools, json, carry as C
from velocity_shift import equations as E
LIVE_XP = E.story_xp
SHARE = (0.4, 0.4, 0.2, 0, 0, 0, 0)
def make(k, share=SHARE):
    def story_xp(rnd, rung, enter_level, cap):
        nominal = 0 if rnd == 0 else E.CAP_LEVEL[rnd - 1]
        base = LIVE_XP(rnd, rung, nominal, cap) if enter_level < nominal else LIVE_XP(rnd, rung, enter_level, cap)
        short = sum(E.xp_to_next(L) for L in range(enter_level, nominal))
        return base + k * share[rung] * short
    return story_xp
if __name__ == "__main__":
    out = []
    for k, b2, sh in itertools.product((0.0, 0.25, 0.5, 0.75, 1.0), (1.0, 1.5), ("kid", "early")):
        share = SHARE if sh == "kid" else (0.25, 0.25, 0.25, 0.25, 0, 0, 0)
        m = [list(r) for r in E.STORY_XP_MULT]; m[1][6] = b2
        with C.patched(story_xp=make(k, share), STORY_XP_MULT=tuple(tuple(r) for r in m)):
            o = C.summary(True)
        s = o["story"]
        x = dict(k=k, b2=b2, share=sh, min80=s["min80"], boss80=s["boss80"], enter=s["enter"], endL=s["endL"], rows=s["rows"], mixed_wall=o["mixed"]["wall"],
                 mixed_g=o["mixed"]["grinds"], hard_g=o["hard"]["grinds"], cap=(o["mixed"]["boss80"], o["hard"]["boss6060"]), cash=s["cash"])
        out.append(x); print({kk: x[kk] for kk in ("k", "b2", "share", "min80", "boss80", "enter", "endL", "mixed_wall", "hard_g")})
    json.dump(out, open(__file__.replace(".py", ".json"), "w"))
