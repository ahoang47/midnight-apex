"""When does the meter fill? First-activation turn and share of races that activate, by fill setting, profile and race.
-> fill_turn.json"""
import json, os, sys
from dataclasses import replace
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import core
from spirit_match import Spirit, SpiritRunner
from velocity_shift import equations as E

C0 = Spirit(base=8, size=100, match_k=1.0, loss_frac=0.25, tie_frac=0.5, buff="pay", amount=0.25, dur=3, max_acts=1)
RACES = {"Street kid1 story (10t, r 1.0195)": ("street", "S1_Shibuya_Grid", 10, 1.0195, (0.5, 0.25, 0.25)),
         "Wangan mat1 mixed (20t, r 1.0302)": ("wangan", "W3_C1_Outer", 20, 1.0302, (0.25, 0.25, 0.5)),
         "Wangan boss cap (30t, r 1.0548)": ("wangan", "W3_C1_Outer", 30, 1.0548, (0.25, 0.25, 0.5))}
SETS = [(b, k, lf) for b in (3, 4, 5, 6, 8) for k in (0.0, 1.0, 2.0) for lf in (0.0, 0.25)]
OFF = {"on tune": None, "off tune (Street build in Wangan)": (0.5, 0.25, 0.25)}
N = 60


def job(a):
    rn, prof, off = a
    d, tr, T, r, tune = RACES[rn]
    if off and OFF[off]:
        tune = OFF[off]
    sk = {"c6060": (0.6, 0.6, 0.6), "c8080": (0.8, 0.8, 0.8)}[prof]
    out = {}
    for b, k, lf in SETS:
        sp = replace(C0, base=b, match_k=k, loss_frac=lf)
        firsts = []
        for si, st in enumerate(E.BOSS_STYLES):
            for i in range(N):
                mo = []
                SpiritRunner(core.cfg_of(d, tr, T, st, *sk, r, tune, 5_000_000 + si * 10_000 + i), sp, mo).run()
                firsts.append(mo[0][2])
        got = [x for x in firsts if x is not None]
        out[f"base {b} k {k} loss {lf}"] = dict(activated=round(100 * len(got) / len(firsts), 1),
                                                 mean_turn=round(sum(got) / len(got), 2) if got else None)
    return rn, prof, off, out


if __name__ == "__main__":
    jobs = [(rn, p, "on tune") for rn in RACES for p in ("c6060", "c8080")]
    jobs += [("Wangan boss cap (30t, r 1.0548)", p, "off tune (Street build in Wangan)") for p in ("c6060", "c8080")]
    with Pool(8) as pool:
        res = pool.map(job, jobs)
    J = {f"{rn} | {p} | {o}": out for rn, p, o, out in res}
    json.dump(dict(N=N * 3, races=RACES, results=J), open(os.path.join(HERE, "fill_turn.json"), "w"), indent=1)
    for k, v in J.items():
        print(k)
        for s, x in v.items():
            if s.endswith("loss 0.25") or s.startswith("base 8"):
                print("   ", s, x)
