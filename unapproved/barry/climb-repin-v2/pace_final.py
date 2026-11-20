"""Build pace_<model>_final.json from the verify file, re-running the boss cells (n = 6,000) for any boss moved by pace_boss_fix.
Usage: AI_PACE=1 [FALLOFF_T=t] python3 pace_final.py <tag> [mode:rnd:B ...]"""
import json, os, sys
os.environ.setdefault("SIM", "/tmp/pp/sim")
from multiprocessing import Pool
import repin as R
tag = sys.argv[1]; fix = [a.split(":") for a in sys.argv[2:]]
J = [(m, int(r), 6, float(B), q, w, 6000) for m, r, B in fix for q, w in ((0.8, "floor"), (0.6, "max"), (0.8, "max"), (0.6, "floor"))]
if __name__ == "__main__":
    d = json.load(open(os.path.join(R.HERE, f"pace_{tag}_verify.json")))
    with Pool(8) as p: res = p.map(R.verify_job, J, chunksize=1) if J else []
    for (m, r, j, B, q, w, n), v in res:
        for mm in ([m, "touge_pp"] if m == "touge" else [m]):
            c = d[mm]
            if mm != m: continue
            c["budgets"][6] = B
            if (q, w) == (0.8, "floor"): c["strong_floor"][6] = v
            elif (q, w) == (0.6, "max"): c["weak_max"][6] = v
            elif (q, w) == (0.8, "max"): c["boss_strong_max"] = v
            else: c["boss_weak_floor"] = v
    out = {"budgets": {m: d[m]["budgets"] for m in ("street", "wangan", "touge")}, "climb": {m: d[m] for m in ("street", "wangan", "touge")},
           "note": f"AI pacing on; heat {os.environ.get('FALLOFF_T') and 'falloff t=' + os.environ['FALLOFF_T'] or 'lock cap 2 (keep load)'}; rungs n=2000, bosses n=6000"
                   + ("; boss fixes " + str(fix) if fix else "")}
    json.dump(out, open(os.path.join(R.HERE, f"pace_{tag}_final.json"), "w"), indent=1)
    for m in ("street", "wangan", "touge"): print(m, out["climb"][m])
