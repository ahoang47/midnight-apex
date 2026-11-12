"""slots-v2: finer window-fix sweep (cap and size) + aero alone (no window) grind, all profiles, 100/0/0 and 70/20/10."""
import json
from multiprocessing import Pool
import model as M, prog, breaks


def job(a):
    kind, prof, split, policy, knob = a
    M.ZONE_CAP, M.WINDOW = 1.15, 0.75
    if kind == "cap":
        M.ZONE_CAP = knob
    elif kind == "size":
        M.WINDOW = knob
    rows, t = prog.run(split, policy, prof); base, tb = prog.run(split, "balanced", prof)
    return dict(kind=kind, profile=prof, split=split, policy=policy, knob=knob, grind=t["grind_races"], base_grind=tb["grind_races"],
                walls_cleared_by_mods=breaks.walls_cleared(base, rows),
                changed=[(r["crew"], r["rung"], b["grind"], r["grind"], r["mid"], r["pick"]) for b, r in zip(base, rows) if b["grind"] != r["grind"]])


if __name__ == "__main__":
    jobs = [("cap", p, "100/0/0", "window", c) for p in M.PROFILES for c in (1.04, 1.03, 1.02, 1.01)]
    jobs += [("size", p, "100/0/0", "window", s) for p in M.PROFILES for s in (0.70, 0.65, 0.60, 0.55)]
    with Pool(8) as pool:
        res = pool.map(job, jobs, chunksize=1)
    for r in res:
        print(r["kind"], r["profile"], r["split"], r["policy"], r["knob"], r["grind"], r["base_grind"], r["walls_cleared_by_mods"])
    json.dump(res, open("results_breaks2.json", "w"), indent=0)
