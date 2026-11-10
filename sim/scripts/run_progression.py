"""Story XP / level progression report (grind v8c model, Barry 2026-11-09).

Usage (from sim/):  python scripts/run_progression.py [--never] [--rows] [--all-orders]
--all-orders runs all 216 legal play orders (free crew choice per round) and prints the per-slot worst cases.
Prints walls (mature #2 / boss grind races) in game order, the skip-grind pattern, totals,
and the per-district split (each crew scored on its own district's tracks).
All constants: velocity_shift/equations.py. Win rates: config/winrate_n4000.json.
"""
import sys
sys.path.insert(0, ".")
from velocity_shift import progression as P

F = lambda t: f"{t[0]:.0f}-{t[1]:.0f}"


def all_orders_report():
    import json
    totals = set(); walls = set(); slots = {}
    for order in P.all_orders():
        rows, tot = P.run("forced", order)
        w, fin = P.walls(rows)
        totals.add((tot["grind_races"], tot["levels"], tot["story_xp"], tot["grind_xp"], tot["lost_xp"]))
        walls.add(tuple((m, b) for _, m, b in w) + (tuple(fin),))
        for rnd in (1, 2, 3):
            for pos, d in enumerate(order[rnd]):
                ds = [r for r in rows if r["crew"] == f"R{rnd} {d}"]
                cl = [r for r in ds if not r["grind_races"]]
                weak = min(cl, key=lambda r: P.mid(r["district_rates"]["avg_skip"]))
                rec = (ds[3]["grind_races"], ds[6]["grind_races"], tuple(ds[3]["district_rates"]["avg_skip"]), tuple(ds[6]["district_rates"]["avg_skip"]),
                       tuple(ds[6]["district_rates"]["avg_target"]), weak["rung"], tuple(weak["district_rates"]["avg_skip"]),
                       "".join("W" if r["grind_races"] else "c" for r in ds))
                slots.setdefault((d, rnd, pos), set()).add(rec)
    print("orders: 216 | distinct totals:", sorted(totals), "| distinct wall layouts by position:", len(walls))
    print("slot           | m2 races skip | boss races skip | boss target | weakest cleared skip | pattern")
    for d in ("Touge", "Wangan", "Street"):
        for rnd in (1, 2, 3):
            for pos in range(3):
                recs = slots[(d, rnd, pos)]
                for m, b, ms, bs, bt, wr, ws, pat in sorted(recs):
                    print(f"{d:6s} R{rnd} pos{pos + 1} | {m:2d} {F(ms)} | {b:2d} {F(bs)} | {F(bt)} | {wr} {F(ws)} | {pat}" + ("" if len(recs) == 1 else "  (varies by order)"))


def main(argv):
    if "--all-orders" in argv:
        all_orders_report(); return
    policy = "never" if "--never" in argv else "forced"
    rows, tot = P.run(policy)
    w, fin = P.walls(rows)
    print(f"policy: {policy}")
    print("pattern:", P.pattern(rows))
    print("walls (mature #2 / boss):", ", ".join(f"{c} {m}/{b}" for c, m, b in w), "| finale", "/".join(map(str, fin)))
    print("totals:", {k: v for k, v in tot.items() if k != "budgets"})
    print("budgets (crew, Option A, level-following):", tot["budgets"])
    if "--rows" in argv or policy == "never":
        print("\nk  crew       rung       | cap story grind | pooled avg tgt/skip good tgt/skip | own district avg tgt/skip good tgt/skip")
        for r in rows:
            s = f"{r['k']:2d} {r['crew']:10s} {r['rung']:10s} | {r['level_cap']:3d} {r['story_level']:3d} {r['grind_races']:2d} | {F(r['avg_target'])} {F(r['avg_skip'])} {F(r['good_target'])} {F(r['good_skip'])}"
            if "district_rates" in r:
                d = r["district_rates"]; s += f" | {F(d['avg_target'])} {F(d['avg_skip'])} {F(d['good_target'])} {F(d['good_skip'])}"
            print(s)
    if policy == "forced":
        print("\nper district (own tracks, average play):")
        for dn in ("Touge", "Wangan", "Street"):
            ds = [r for r in rows if r["district"] == dn]
            tg = [r["district_rates"]["avg_target"] for r in ds]
            wl = [r["district_rates"]["avg_skip"] for r in ds if r["grind_races"]]
            cl = [r for r in ds if not r["grind_races"] and r["crew"] != "Finale"]
            weak = min(cl, key=lambda r: P.mid(r["district_rates"]["avg_skip"]))
            print(f"  {dn:6s} at target {min(t[0] for t in tg):.0f}-{max(t[1] for t in tg):.0f} | walls skipped {min(t[0] for t in wl):.0f}-{max(t[1] for t in wl):.0f}"
                  f" | weakest cleared rung {P.mid(weak['district_rates']['avg_skip']):.0f} ({weak['crew']} {weak['rung']} {F(weak['district_rates']['avg_skip'])})")


if __name__ == "__main__":
    main(sys.argv[1:])
