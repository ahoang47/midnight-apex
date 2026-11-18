"""Calibrate the additive clash_stakes bonus b: match the progress the x1.25 buff adds, b = 0.25 (W + T + L) / (W - L),
from un-buffed player progress by outcome on buff turns (curve player, story + mixed walks, driver builds by round). -> calib.json"""
import json, os
from multiprocessing import Pool
import st_match as M, races as R

def job(rc):
    acc = [0.0, 0.0, 0.0]
    sk = R.PROF("curve", rc["j"]); tune = (rc["ps"], 0.25, 1 - rc["ps"] - 0.25)
    for si, st in enumerate(R.E.BOSS_STYLES):
        for k in range(40):
            o = {}
            M.Runner(R.cfg_of(rc["d"], R.HARD[rc["d"]], rc["T"], st, sk, rc["r"], tune, 9_000_000 + si * 1000 + k), M.SPIRIT_A,
                     M.BUILDS[rc["rnd"]][1], out=o).run()
            acc = [x + y for x, y in zip(acc, o["acc"])]
    return acc

if __name__ == "__main__":
    rcs = [rc for rc in R.races() if rc["mode"] in ("story", "mixed")]
    with Pool(8) as p:
        accs = p.map(job, rcs)
    L, T, W = [sum(a[i] for a in accs) for i in range(3)]
    b = 0.25 * (W + T + L) / (W - L)
    json.dump(dict(loss=L, tie=T, win=W, b=b), open(os.path.join(R.HERE, "calib.json"), "w"), indent=1)
    print(dict(loss=round(L, 2), tie=round(T, 2), win=round(W, 2), b=round(b, 4)))
