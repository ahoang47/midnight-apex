"""Run 2: spirit multiplicative (x1.25 payoff, 3 turns) vs additive clash_stakes (win x (1+b), loss x (1-b), b from calib.json),
on the mod_skill races (story-only + mixed walks, bosses at the cap), driver builds by round [PH] on in every variant.
Variants (paired seeds): none (no driver, no spirit) | driver only | driver + spirit mult | driver + spirit stakes. -> run2.json"""
import json, os, time
from dataclasses import replace
from multiprocessing import Pool
import st_match as M, races as R

B = json.load(open(os.path.join(R.HERE, "calib.json")))["b"]
NH, ND, NB = 200, 40, 600

def job(a):
    rc, prof = a
    drv = M.BUILDS[rc["rnd"]][1]
    v = [(None, M.Driver()), (None, drv), (M.SPIRIT_A, drv), (replace(M.SPIRIT_A, buff="stakes", amount=B), drv)]
    n = NB if rc["mode"] == "cap" else (NH if rc["hard"] else ND)
    N, out = R.batch(rc, prof, v, n, 81_000_000)
    return dict(rc, prof=prof, n=N, none=round(out[0]["win"], 2), **{k: dict(win=round(o["win"], 2), d=round(o["delta"], 2), se=round(o["se"], 2))
                for k, o in zip(("driver", "mult", "stakes"), out[1:])})

if __name__ == "__main__":
    t = time.time()
    jobs = [(rc, p) for rc in R.races() for p in ("c6060", "c8080", "curve") if not (rc["mode"] == "cap" and p == "curve")]
    jobs.sort(key=lambda a: -(a[0]["T"] * (3 if a[0]["mode"] == "cap" else 1)))
    with Pool(8) as p:
        rows = p.map(job, jobs, chunksize=1)
    json.dump(dict(b=B, rows=rows), open(os.path.join(R.HERE, "run2.json"), "w"), indent=1)
    print("done", round(time.time() - t))
