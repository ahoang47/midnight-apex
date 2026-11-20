"""R1 journey with purchases for the oh2-70 variant (Barry 2026-11-19): journey_shop.py rules, M13r + boss floor 3392 (oh2 story
XP +46), Street oh2 budget 332.93 -> 331.98 (oh2_70.py). -> journey_oh2_70.json"""
import json, os
import journey as J, journey_shop as JS
HERE = os.path.dirname(os.path.abspath(__file__))
J.BUD["oh2"] = 331.98
if __name__ == "__main__":
    v = JS.variant("M13r+boss46+oh2_70", 46); out = []
    for who, rk in (("strong", 1), ("weak", 1), ("weak", 2)):
        o = JS.run(v, who, rk); out.append(o)
        print(who, rk, "att", o["att"], "nm", o["nm"], "lost", o["lost"], "spent", o["spent"], "mk3", o["mk3"], "stuck", o["stuck"])
        for r in o["rows"]:
            if r["race"] != "we":
                print("   %-4s q %.3f pts %6.1f p1 %5.1f att %4.2f nm %4.2f cash %6.0f debt %6.0f" % (r["race"], r["q"], r["pts"], 100 * r["p"], r["att"], r["nm"], r["cash"], r["debt"]))
    json.dump(out, open(os.path.join(HERE, "journey_oh2_70.json"), "w"), indent=1)
