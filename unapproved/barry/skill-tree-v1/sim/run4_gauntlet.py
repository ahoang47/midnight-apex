"""Run 4: Myth finale gauntlet. One Myth car, 3 Myth drivers back to back, no stop: F1 touge T3_Usui_Esses r 1.075,
F2 wangan W3_C1_Outer r 1.058, F3 street S1_Shibuya_Grid r 1.044 (live FINALE_TARGET_R), 30 turns each.
Spirit A + driver build 4 (L64) [PH] on throughout. Boss style drawn per race (uniform over the 3 styles).
carry: heat fill/locks and spirit meter carry from the previous race's end state; no carry: each race starts fresh.
Tunes: 'on' = each race at its district tune (reference); 'one' = one compromise car tune (0.40, 0.25, 0.35) [PH] for all 3.
Profiles: c6060, c8080, curve s = 0.7 [PH; the per-rung curve ends at 0.8 = 80/80 at the boss, so a mid value is shown].
Clear = product of the 3 race values (tie = 0.5). Also sweeps a common multiplier f on all 3 r (curve, one tune, carry)
to find the per-race win % that gives about 50% clear. -> run4.json"""
import json, os, time
from random import Random
from multiprocessing import Pool
import st_match as M, races as R
from velocity_shift import equations as E

LEGS = [("touge", "T3_Usui_Esses", 1.075), ("wangan", "W3_C1_Outer", 1.058), ("street", "S1_Shibuya_Grid", 1.044)]
ONE = (0.40, 0.25, 0.35)
SK = {"c6060": (0.6,) * 3, "c8080": (0.8,) * 3, "curve": (0.7,) * 3}
N = 600


def gaunt(a):
    prof, tune, carry, f, n, seed0 = a
    drv = M.BUILDS[4][1]; w = [0.0, 0.0, 0.0]; clr = 0.0
    for k in range(n):
        rng = Random(seed0 + k); st = None; v = 1.0
        for i, (d, tr, r) in enumerate(LEGS):
            tn = R.TUNE[d] if tune == "on" else ONE
            c = R.cfg_of(d, tr, 30, rng.choice(E.BOSS_STYLES), SK[prof], r * f, tn, seed0 * 7 + k * 3 + i)
            out = {}
            x = R.wv(M.Runner(c, M.SPIRIT_A, drv, carry=st if carry else None, out=out).run())
            st = out["end"]; w[i] += x; v *= x
        clr += v
    return dict(prof=prof, tune=tune, carry=carry, f=f, n=n, win=[round(100 * x / n, 1) for x in w], clear=round(100 * clr / n, 1))


if __name__ == "__main__":
    t = time.time()
    jobs = [(p, tu, ca, 1.0, N, 91_000_000) for p in SK for tu in ("on", "one") for ca in (False, True)]
    jobs += [("curve", "one", True, f, 300, 92_000_000) for f in (1.02, 1.04, 1.06, 1.08, 1.10)]
    with Pool(8) as p:
        rows = p.map(gaunt, jobs, chunksize=1)
    json.dump(rows, open(os.path.join(R.HERE, "run4.json"), "w"), indent=1)
    for x in rows:
        print(x)
    print("done", round(time.time() - t))
