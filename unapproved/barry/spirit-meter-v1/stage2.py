"""Stage 2: candidate spirit settings on the mod_skill campaign races (mod-skill-v1 results.json, recommended config):
story-only and mixed (grind-to-target) runs, 21 races each, r and POW share from the walk, HAN 25 %.
Profiles c6060, c8080 and the standard reading curve (q_read = q_time = pacing = s, s = 0.6 + 0.2 j/6 by rung).
Cell = the walk's shown cell: hardest track for bosses and every Touge race, else the mean of the 5 district tracks.
-> stage2.json"""
import json, os, sys, time
from dataclasses import asdict, replace
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import core
from spirit_match import Spirit
from velocity_shift import combat as C

HARD = {"street": "S1_Shibuya_Grid", "wangan": "W3_C1_Outer", "touge": "T3_Usui_Esses"}
NH = int(os.environ.get("NH", 200)); ND = int(os.environ.get("ND", 40))   # per boss style: hard track / each district track
C0 = Spirit(base=8, size=100, match_k=1.0, loss_frac=0.25, tie_frac=0.5, buff="pay", amount=0.25, dur=3, max_acts=1)
SP = [("centre pay.25x3", C0), ("pay.2x3", replace(C0, amount=0.2)), ("pay.3x3", replace(C0, amount=0.3)),
      ("pay.2x5", replace(C0, amount=0.2, dur=5)), ("pay.3x3 a2", replace(C0, amount=0.3, max_acts=2)),
      ("heat x1", replace(C0, buff="heat", dur=1)), ("qte1.0x5", replace(C0, buff="qte", amount=1.0, dur=5)),
      ("centre base4", replace(C0, base=4)), ("centre base16", replace(C0, base=16)),
      ("centre k0", replace(C0, match_k=0.0)), ("centre k3", replace(C0, match_k=3.0)),
      ("centre loss0", replace(C0, loss_frac=0.0)), ("centre loss1", replace(C0, loss_frac=1.0))]
RES = json.load(open(os.path.join(HERE, "..", "mod-skill-v1", "results.json")))["configs"]["recommended"]["runs"]


def races():
    out = []
    for mode in ("story", "mixed"):
        for rd in RES[mode]:
            d = rd["district"]
            for j, x in enumerate(rd["rows"]):
                hard = x["rung"] == "boss" or d == "touge"
                ps = x["pow_share"] / 100
                out.append(dict(mode=mode, rnd=rd["rnd"], d=d, rung=x["rung"], j=j, T=x["turns"], r=x["r"], ps=ps,
                                hard=hard, walk_wr=x["wr"]))
    return out


def job(a):
    rc, prof = a
    s = 0.6 + 0.2 * rc["j"] / 6
    sk = {"c6060": (0.6, 0.6, 0.6), "c8080": (0.8, 0.8, 0.8), "curve": (s, s, s)}[prof]
    tracks = [HARD[rc["d"]]] if rc["hard"] else list(C.official_tracks()[rc["d"]])
    tune = (rc["ps"], 0.25, 1 - rc["ps"] - 0.25)
    res = core.paired(rc["d"], tracks, rc["T"], sk, rc["r"], NH if rc["hard"] else ND, [x for _, x in SP], tune=tune)
    return rc, prof, s, res


if __name__ == "__main__":
    t = time.time()
    jobs = [(rc, p) for rc in races() for p in ("c6060", "c8080", "curve")]
    jobs.sort(key=lambda a: -a[0]["T"])
    with Pool(8) as p:
        out = p.map(job, jobs, chunksize=1)
    rows = []
    for rc, prof, s, res in out:
        rows.append(dict(rc, prof=prof, skill=s if prof == "curve" else None, base=round(res["base"], 2),
                         se_base=round(res["se_base"], 2), n=res["n"],
                         sp={nm: {k: round(v, 3) for k, v in x.items()} for (nm, _), x in zip(SP, res["sp"])}))
    json.dump(dict(NH=NH, ND=ND, spirits={nm: asdict(x) for nm, x in SP}, rows=rows), open(os.path.join(HERE, "stage2.json"), "w"), indent=1)
    print("done", round(time.time() - t), "s")
