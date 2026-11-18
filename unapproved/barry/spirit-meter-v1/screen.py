"""Stage 1 screen: one-at-a-time sweep around a centre setting, bosses at the mod_skill cap (hardest track, 30 turns,
r = mod_skill cap r, build on district tune), c6060 and c8080, 3 boss styles x N races, paired seeds. -> screen.json"""
import json, os, sys, time
from dataclasses import asdict, replace
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import core
from spirit_match import Spirit

N = int(os.environ.get("N", 200))
CAP = {"street": 1.044, "wangan": 1.0548, "touge": 1.0702}   # mod-skill-v1 results.json live_boss_at_cap r (= mod_skill cap)
HARD = {"street": "S1_Shibuya_Grid", "wangan": "W3_C1_Outer", "touge": "T3_Usui_Esses"}
PROF = {"c6060": (0.6, 0.6, 0.6), "c8080": (0.8, 0.8, 0.8)}
C0 = Spirit(base=8, size=100, match_k=1.0, loss_frac=0.25, tie_frac=0.5, buff="pay", amount=0.25, dur=3, max_acts=1)
SP = [("centre", C0)]
for a in (0.1, 0.2, 0.3, 0.5):
    for du in (2, 3, 5):
        SP.append((f"pay {a} x{du}", replace(C0, amount=a, dur=du)))
for a in (0.25, 0.5, 1.0):
    for du in (2, 3, 5):
        SP.append((f"qte {a} x{du}", replace(C0, buff="qte", amount=a, dur=du)))
for du in (1, 2, 3):
    SP.append((f"heat x{du}", replace(C0, buff="heat", dur=du)))
for b in (4, 6, 12, 16):
    SP.append((f"base {b}", replace(C0, base=b)))
for k in (0.0, 2.0, 3.0):
    SP.append((f"match_k {k}", replace(C0, match_k=k)))
for lf in (0.0, 0.5, 1.0):
    SP.append((f"loss {lf}", replace(C0, loss_frac=lf)))
for m in (2, 3, 99):
    SP.append((f"acts {m}", replace(C0, max_acts=m)))
CHUNK = 6


def job(args):
    d, pr, lo = args
    names = SP[lo:lo + CHUNK]
    res = core.paired(d, [HARD[d]], 30, PROF[pr], CAP[d], N, [s for _, s in names])
    return d, pr, lo, res


if __name__ == "__main__":
    t = time.time()
    jobs = [(d, pr, lo) for d in CAP for pr in PROF for lo in range(0, len(SP), CHUNK)]
    with Pool(8) as p:
        out = p.map(job, jobs)
    cells = {}
    for d, pr, lo, res in out:
        c = cells.setdefault(f"{d} {pr}", dict(base=res["base"], se_base=res["se_base"], n=res["n"], sp={}))
        for (nm, _), x in zip(SP[lo:lo + CHUNK], res["sp"]):
            c["sp"][nm] = {k: round(v, 3) for k, v in x.items()}
    json.dump(dict(N_per_style=N, cap_r=CAP, spirits={nm: asdict(s) for nm, s in SP}, cells=cells), open(os.path.join(HERE, "screen.json"), "w"), indent=1)
    print("done", round(time.time() - t), "s")
