"""slots-v2: parity-window alternative fix. Lower the r=1.00 knot of KNOT_WINDOW_105 (which generates qte_zone_width; live
value 0.68) in-process only, and rerun balanced and window (+75%, any slot, cap 1.15) progression for all profiles."""
import json
from multiprocessing import Pool
import model as M, prog

E = M.E
K0 = E.KNOT_WINDOW_105


def job(a):
    k, prof, pol = a
    E.KNOT_WINDOW_105 = tuple((r, (k if abs(r - 1.0) < 1e-9 else w)) for r, w in K0)
    rows, t = prog.run("100/0/0", pol, prof)
    return dict(knot_100=k, profile=prof, policy=pol, grind=t["grind_races"],
                opener_boss=[(r["crew"], r["grind"], r["mid"], r["pick"]) for r in rows if r["crew"] in ("R2 Wangan", "R3 Street") and r["j"] == 6])


if __name__ == "__main__":
    jobs = [(k, p, pol) for k in (0.68, 0.67, 0.66, 0.65) for p in M.PROFILES for pol in ("balanced", "window")]
    with Pool(8) as pool:
        res = pool.map(job, jobs, chunksize=1)
    for r in res:
        print(r)
    json.dump(res, open("results_parity.json", "w"), indent=0)
