"""slots-v2 follow-up (small): under the proposed KNOT_WINDOW_105 r=1.00 knot 0.68 -> 0.67 (in-process only), which walls
does aero (with window) still clear for the average profile? parity_after.json only kept totals. Writes results_aero_knot.json."""
import json
from multiprocessing import Pool
import model as M, prog
import parity_after as PA


def job(a):
    sp, pol = a
    PA.patch()
    rows, t = prog.run(sp, pol, "average")
    base, tb = prog.run(sp, "balanced", "average")
    return dict(split=sp, policy=pol, grind=t["grind_races"], base_grind=tb["grind_races"],
                changed=[(r["crew"], r["rung"], b["grind"], r["grind"], r["mid"], r["pick"]) for b, r in zip(base, rows) if b["grind"] != r["grind"]])


if __name__ == "__main__":
    jobs = [(s, p) for s in ("100/0/0",) for p in ("aero10", "aero20", "aero30")]
    with Pool(3) as pool:
        res = pool.map(job, jobs)
    for r in res:
        print(r, flush=True)
    json.dump(res, open("results_aero_knot.json", "w"), indent=0)
