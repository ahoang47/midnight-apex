"""Smallest kid1/kid2 opponent-r lift (weaker kid opponents) per district that restores the targets with 20-turn kid races.
Kid1 budget is also the grind reporting budget (grind10 column); grind XP / count logic does not read win rates."""
import json, itertools
import kidlen as KL
from velocity_shift import equations as E
base = E.LADDER_TARGET_R
out = []
steps = [round(0.005 * i, 3) for i in range(0, 13)]
for di, d in enumerate(("street", "wangan", "touge")):
    for a, b in itertools.product(steps, steps):
        k = {d: (round(base[d][0] + a, 4), round(base[d][1] + b, 4))}
        r = KL.evaluate(dict(KL.FIXC, LADDER_TURNS=KL.turns(20, 20), LADDER_TARGET_R=KL.tr(**k)), arc=False)
        rows = r["story_rows"][di]
        x = dict(d=d, da=a, db=b, r=k[d], story_kid=[rows[0]["c8080"], rows[1]["c8080"]], story_min=r["story_min"]["c8080"][di],
                 mixed_wall=r["mixed"]["wall"][di], mixed_wall_at=r["mixed"]["wall_at"][di], mixed_g=r["mixed"]["grinds"][di],
                 hard_g=r["hard"]["grinds"][di], hard_wall=r["hard"]["wall"][di], g10=r["g10_min_story8080"])
        out.append(x)
json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=0)
for d in ("street", "wangan", "touge"):
    ok = [x for x in out if x["d"] == d and x["story_min"] >= 50 and x["mixed_wall_at"] not in ("kid1", "kid2") and 3 <= x["mixed_wall"] <= 6]
    ok.sort(key=lambda x: (x["da"] + x["db"], x["da"]))
    print(d, "n ok", len(ok)); [print("  ", x) for x in ok[:4]]
    z = [x for x in out if x["d"] == d and x["da"] == x["db"]]; [print("   diag", x) for x in z]
