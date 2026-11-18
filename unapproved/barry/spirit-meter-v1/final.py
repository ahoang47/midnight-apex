"""Stage 3: final candidates, bigger N. Same races and cells as stage2.py, plus bosses at the mod_skill cap.
max_acts = -1 means one activation per 10 turns of race (1 / 2 / 3). -> final.json"""
import json, os, sys, time
from dataclasses import asdict, replace
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import core, stage2
from spirit_match import Spirit
from velocity_shift import combat as C

M = Spirit(base=6, size=100, match_k=1.0, loss_frac=0.25, tie_frac=0.5, buff="pay", amount=0.25, dur=3, max_acts=1)
SP = [("A pay.25x3 1act", M), ("B pay.25x3 1per10t", replace(M, max_acts=-1)),
      ("C pay.20x3 1per10t", replace(M, amount=0.2, max_acts=-1)), ("D pay.15x3 1act", replace(M, amount=0.15)),
      ("E heat x1 1act", replace(M, buff="heat", dur=1))]
NH, ND, NB = 300, 60, 800
CAP = {"street": 1.044, "wangan": 1.0548, "touge": 1.0702}
TUNE = {"street": (0.5, 0.25, 0.25), "wangan": (0.25, 0.25, 0.5), "touge": (0.45, 0.25, 0.3)}


def sps(T):
    return [replace(x, max_acts=T // 10) if x.max_acts == -1 else x for _, x in SP]


def job(a):
    rc, prof = a
    s = 0.6 + 0.2 * rc["j"] / 6
    sk = {"c6060": (0.6, 0.6, 0.6), "c8080": (0.8, 0.8, 0.8), "curve": (s, s, s)}[prof]
    if rc["mode"] == "cap":
        res = core.paired(rc["d"], [stage2.HARD[rc["d"]]], 30, sk, rc["r"], NB, sps(30), seed0=31_000_000, tune=TUNE[rc["d"]])
    else:
        tracks = [stage2.HARD[rc["d"]]] if rc["hard"] else list(C.official_tracks()[rc["d"]])
        tune = (rc["ps"], 0.25, 1 - rc["ps"] - 0.25)
        res = core.paired(rc["d"], tracks, rc["T"], sk, rc["r"], NH if rc["hard"] else ND, sps(rc["T"]), seed0=41_000_000, tune=tune)
    return rc, prof, s, res


if __name__ == "__main__":
    t = time.time()
    rcs = stage2.races() + [dict(mode="cap", rnd=i + 1, d=d, rung="boss", j=6, T=30, r=CAP[d], ps=TUNE[d][0], hard=True, walk_wr=None)
                            for i, d in enumerate(CAP)]
    jobs = [(rc, p) for rc in rcs for p in ("c6060", "c8080", "curve") if not (rc["mode"] == "cap" and p == "curve")]
    jobs.sort(key=lambda a: -(a[0]["T"] * (3 if a[0]["mode"] == "cap" else 1)))
    with Pool(8) as p:
        out = p.map(job, jobs, chunksize=1)
    rows = [dict(rc, prof=prof, skill=s if prof == "curve" else None, base=round(res["base"], 2), se_base=round(res["se_base"], 2),
                 n=res["n"], sp={nm: {k: round(v, 3) for k, v in x.items()} for (nm, _), x in zip(SP, res["sp"])})
            for rc, prof, s, res in out]
    json.dump(dict(NH=NH, ND=ND, NB=NB, spirits={nm: asdict(x) for nm, x in SP}, rows=rows), open(os.path.join(HERE, "final.json"), "w"), indent=1)
    print("done", round(time.time() - t), "s")
