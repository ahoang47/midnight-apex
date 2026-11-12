"""slots-v2 equation-break checks (draft only; live sim constants untouched, patched in-process).
(i) walls cleared by mods alone: window cap / size sweep; aero pools.  (ii) dead wins: CAP_ALLOC without zeros."""
import json
from multiprocessing import Pool
import numpy as np
import model as M, prog

E = M.E


def walls_cleared(base_rows, rows):
    return [(b["crew"], b["rung"]) for b, r in zip(base_rows, rows) if b["grind"] and not r["grind"] and b["crew"] != "Finale"]


def job(a):
    kind, prof, split, policy, knob = a
    M.ZONE_CAP, M.WINDOW = 1.15, 0.75                      # reset per job (pool workers are reused)
    E.CAP_ALLOC_CREW, E.CAP_ALLOC_ROUND_OPEN = ALLOCS["official"]
    if kind == "cap":
        M.ZONE_CAP = knob
    elif kind == "size":
        M.WINDOW = knob
    elif kind == "alloc":
        E.CAP_ALLOC_CREW, E.CAP_ALLOC_ROUND_OPEN = knob
    rows, t = prog.run(split, policy, prof)
    base, _ = prog.run(split, "balanced", prof)
    dead = sum(1 for s in M.S1.schedule("C") if s["buy"] is None)
    return dict(kind=kind, profile=prof, split=split, policy=policy, knob=knob, grind=t["grind_races"], base_grind=_["grind_races"],
                walls_cleared_by_mods=walls_cleared(base, rows), dead_wins=dead,
                walls=[(r["crew"], r["rung"], r["grind"], r["mid"]) for r in rows if r["grind"] and r["crew"] != "Finale"])


ALLOCS = {"official": ((2, 2, 3, 3, 1, 0, 1), (12, 3, 3, 3, 1, 0, 0.5)),
          "A: CREW (2,2,3,2,1,1,1), RO (18,4,4,4,1,1,1)": ((2, 2, 3, 2, 1, 1, 1), (18, 4, 4, 4, 1, 1, 1)),
          "B: CREW (2,2,2,3,1,1,1), RO (18,4,4,4,1,1,1)": ((2, 2, 2, 3, 1, 1, 1), (18, 4, 4, 4, 1, 1, 1)),
          "C: CREW (2,2,3,3,1,1,0), RO (18,4,4,4,2,1,0)": ((2, 2, 3, 3, 1, 1, 0), (18, 4, 4, 4, 2, 1, 0))}


def main():
    jobs = []
    for prof in M.PROFILES:
        for cap in (1.15, 1.10, 1.05, 1.00):
            jobs.append(("cap", prof, "100/0/0", "window", cap))
        for size in (0.50, 0.25):
            jobs.append(("size", prof, "100/0/0", "window", size))
        for nm, al in ALLOCS.items():
            jobs.append(("alloc", prof, "100/0/0", "balanced", al))
            jobs.append(("alloc", prof, "100/0/0", "window", al))
    with Pool(8) as p:
        res = p.map(job, jobs, chunksize=1)
    names = {v: k for k, v in ALLOCS.items()}
    for r in res:
        if r["kind"] == "alloc":
            r["knob"] = names[r["knob"]]
        print(r["kind"], r["profile"], r["policy"], r["knob"], r["grind"], r["base_grind"], r["dead_wins"], r["walls_cleared_by_mods"], flush=True)
    json.dump(res, open("results_breaks.json", "w"), indent=0, default=str)


if __name__ == "__main__":
    main()
