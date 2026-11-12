"""slots-v2: search CAP_ALLOC variants with no zero entries (no dead wins) for the smallest grind change (balanced 2/2/2, 100/0/0)."""
import json, itertools
from multiprocessing import Pool
import model as M, prog, breaks

E = M.E
CREWS = [(2, 2, 3, 3, 1, 0, 1), (2, 2, 3, 2, 1, 1, 1), (2, 2, 2, 3, 1, 1, 1), (2, 2, 2, 2, 1, 1, 2), (1, 2, 3, 3, 1, 1, 1), (2, 1, 3, 3, 1, 1, 1), (2, 2, 3, 3, 0.5, 0.5, 0.5)]
ROS = [(12, 3, 3, 3, 1, 0, 0.5), (18, 4, 4, 4, 1, 1, 1), (17, 4, 4, 4, 2, 1, 1), (18, 4, 4, 3, 2, 1, 1), (18, 3, 4, 4, 2, 1, 1), (12, 3, 3, 3, 0.5, 0.5, 0.5)]


def job(a):
    crew, ro, prof = a
    E.CAP_ALLOC_CREW, E.CAP_ALLOC_ROUND_OPEN = crew, ro
    rows, t = prog.run("100/0/0", "balanced", prof)
    dead = sum(1 for s in M.S1.schedule("C") if s["buy"] is None)
    return dict(crew=crew, ro=ro, profile=prof, grind=t["grind_races"], dead_wins=dead,
                walls=[(r["crew"], r["rung"], r["grind"], r["mid"]) for r in rows if r["grind"] and r["crew"] != "Finale"],
                finale=sum(r["grind"] for r in rows if r["crew"] == "Finale"))


if __name__ == "__main__":
    jobs = [(c, r, p) for c in CREWS for r in ROS for p in M.PROFILES]
    with Pool(8) as pool:
        res = pool.map(job, jobs, chunksize=1)
    json.dump(res, open("results_alloc.json", "w"), indent=0)
    for c in CREWS:
        for r in ROS:
            g = [x for x in res if x["crew"] == c and x["ro"] == r]
            print(c, r, "dead", g[0]["dead_wins"], "grind w/a/s", [x["grind"] for x in g])
