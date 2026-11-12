"""slots-v2: proposed parity fix KNOT_WINDOW_105 r=1.00 knot 0.68 -> 0.67 (in-process only): zone widths before/after and
progression under window / aero policies for every split/profile."""
import json
from multiprocessing import Pool
import model as M, prog

E = M.E; K0 = E.KNOT_WINDOW_105
RS = (0.95, 1.0, 1.0004, 1.02, 1.037, 1.05)


def patch():
    E.KNOT_WINDOW_105 = tuple((r, (0.67 if abs(r - 1) < 1e-9 else w)) for r, w in K0)


def job(a):
    patch(); sp, pol, prof = a
    rows, t = prog.run(sp, pol, prof)
    return (sp, pol, prof, t["grind_races"])


if __name__ == "__main__":
    zb = {r: E.qte_zone_width(r) for r in RS}; patch(); za = {r: E.qte_zone_width(r) for r in RS}; E.KNOT_WINDOW_105 = K0
    jobs = [(sp, pol, prof) for sp in M.SPLITS for pol in ("balanced", "window", "aero30nw", "aero30") for prof in M.PROFILES]
    with Pool(8) as pool:
        runs = pool.map(job, jobs, chunksize=1)
    for r in runs:
        print(r, flush=True)
    json.dump(dict(zone_before=zb, zone_after=za, runs=runs), open("results_parity_after.json", "w"), indent=0)
    print({r: (round(zb[r], 4), round(za[r], 4)) for r in RS})
