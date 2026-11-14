"""Story XP / level / money progression report (econ-v1 3-round ladder, Barry; Austin go-ahead 2026-11-13).

Usage (from sim/):  python scripts/run_progression.py [--rows] [--arc]
Prints the at-cap boss and finale win rates (Variant C), the story / mixed / hard walks (grind, levels, USD cash and
debt per round), and with --arc the pre-finale arc table. --rows adds every rung of every walk.
All constants: velocity_shift/equations.py. Win rates: config/winrate_g2_live_tracks_v1.json (live stand-in tracks; hard cell = hardest track).
"""
import sys
sys.path.insert(0, ".")
from velocity_shift import equations as E, progression as P


def fmt(pack):
    s = f"{pack['district']:5.1f}"
    if "hard" in pack:
        s += f" (hardest {pack['hard']:.1f})"
    return s


def main(argv):
    print("At cap, bosses and finale (60/60 | 60/80 | 80/60 | 80/80; district mean (hardest track)):")
    for x in P.at_cap_table():
        if x["rung"] == "boss" or x["rnd"] == "F":
            print(f"  R{x['rnd']} {x['district']:6s} {x['rung']:26s} r={x['r']:.3f} | " + " | ".join(fmt(x["wr"][p]) for p in P.PROFILES))
    for mode in ("story", "mixed", "hard"):
        print(f"\nwalk: {mode}")
        for w in P.run(mode):
            r0 = w["rows"][0]
            print(f"  R{r0['rnd']} {r0['district']:6s} cap L{w['cap']} reached={w['reached_cap']} end L{w['L']} grind {w['total_grind']}"
                  f" (wall {w['wall']} {w['wall_grind']} + to cap {w['post_wall_to_cap']}) cash ${w['money']:,.0f} debt ${w['debt']:,.0f}")
            if "--rows" in argv:
                for r in w["rows"]:
                    print(f"      {r['rung']:5s} {r['turns']}t B={r['B']:.1f} L{r['arrive_L']:3d} r={r['arrive_r']:.4f} grind {r['grind_here']}+{r['pre_boss_grind']}"
                          f" | " + " | ".join(fmt(r["wr"][p]) for p in P.PROFILES) + f" | ${r['money']:,.0f} debt ${r['debt']:,.0f} {' '.join(r['unlocks'])}")
    print(f"\nfinale caps (C, L): {[(round(c, 1), l) for c, l in P.finale_caps()]} | T4 package ${P.t4_package_price():,.0f}"
          f" (T4 regular ${E.MOD_PRICE['T4']:,.0f} stand-in)")
    if "--arc" in argv:
        print("\npre-finale arc + finale:")
        for a in P.finale_arc():
            print(f"  {a['id']:4s} {a['place']:6s} {a['district']:6s} {a['turns']}t r*={a['r_design']:.3f} B={a['B']:.2f} purse ${a['purse']:,.0f}"
                  f" xp {a['xp']:,.1f}" + (" grants T4" if a["unlock_t4"] else "") + (f" {a['name']} vs {a['opponent']} cap L{a['cap']}" if a["billed"] else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
