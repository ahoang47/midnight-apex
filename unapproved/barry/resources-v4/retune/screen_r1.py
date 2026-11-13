"""v4b retune screen 1, from F2_gentle at cap 1.10. Levers: share-curve exponent for capacity and recovery, DEMAND_SLANT,
DIST_SIG, STAT_M_W. All 15 laps x 20/30 turns x 3 styles, N 300, seed 7. Players at the cap: average (mix 0.6), greedy,
best pacing (read 0.6). Tuned = best split per cell; wrong = best split over the other two districts (same length/style).
Appends one JSON line per config to screen_r1.jsonl. Screen only."""
import sys, os, json, itertools, numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resources_v4b as R
E = R.E
TUNES = np.vstack([R.tune_grid(), [[1 / 3] * 3]]); NT = 21
TR = sorted(R.tracks().items()); DIST = np.array([d for (d, _), _ in TR])
N, SEED, CAP = 300, 7, float(os.environ.get("R_CAP", 1.10))
F2 = {k: v for k, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "candidates.json")))["F2_gentle"].items() if not k.startswith("_")}
LENS = (20, 30)
PL = {"avg": ("mix", 0.6), "greedy": ("greedy", 1.0), "best": ("reserve", 1.0)}


def job(a):
    cfg, pl, ti, T, st = a
    pac, pq = PL[pl]
    (d, _), lap = TR[ti]
    o = R.run_new(TUNES, CAP, d, lap, T, st, 0.6, E.raw_qte_score(CAP, profile="average"), N, SEED,
                  cfg=dict(F2, **cfg, PACE_Q=pq), pacing=pac)
    return a[1:], o["win"].mean(1), o["lock_turns"].mean(1) / T


def summarize(res):
    out = {}
    for pl in PL:
        W = np.array([[[res[(pl, ti, T, st)][0] for st in R.STYLES] for T in LENS] for ti in range(len(TR))])  # (15,2,3,22)
        LK = np.array([[[res[(pl, ti, T, st)][1] for st in R.STYLES] for T in LENS] for ti in range(len(TR))])
        b = W[..., :NT].argmax(-1); tw = np.take_along_axis(W, b[..., None], -1)[..., 0]; ev = W[..., NT]
        wr = np.zeros_like(tw)
        for ti in range(len(TR)):
            j = W[DIST != DIST[ti], ..., :NT].mean(0).argmax(-1)
            wr[ti] = np.take_along_axis(W[ti], j[..., None], -1)[..., 0]
        out[pl] = dict(tuned=tw.mean(), even=ev.mean(), wrong=wr.mean(), gap_even=(tw - ev).mean(), gap_wrong=(tw - wr).mean(),
                       lock_tuned=np.take_along_axis(LK, b[..., None], -1)[..., 0].mean(), lock_even=LK[..., NT].mean(),
                       **{f"gap_even_{d}": (tw - ev)[DIST == d].mean() for d in ("street", "touge", "wangan")},
                       **{f"gap_wrong_{d}": (tw - wr)[DIST == d].mean() for d in ("street", "touge", "wangan")},
                       cells_gap_even_5=((tw - ev) >= 0.05).mean(), cells_gap_wrong_5=((tw - wr) >= 0.05).mean(),
                       **{f"tuned_{T}": tw[:, k].mean() for k, T in enumerate(LENS)})
        out[pl] = {k: round(100 * float(v), 1) for k, v in out[pl].items()}
    out["pacing_gap"] = round(out["best"]["tuned"] - out["greedy"]["tuned"], 1)
    return out


def configs():
    g = dict(EXP=[1.5, 2.5, 3.5], DEMAND_SLANT=[1.0, 2.0], DIST_SIG=[0.0, 0.5], STAT_M_W=[0.0, 0.5, 1.0])
    for e, sl, ds, mw in itertools.product(*g.values()):
        yield dict(CAP_SHARE_EXP=e, REC_SHARE_EXP=e, DEMAND_SLANT=sl, DIST_SIG=ds, STAT_M_W=mw)


if __name__ == "__main__":
    outf = os.environ.get("R_OUT", "screen_r1.jsonl")
    done = set()
    if os.path.exists(outf):
        done = {json.dumps(json.loads(l)["cfg"], sort_keys=True) for l in open(outf)}
    with Pool(8) as p:
        for cfg in configs():
            key = json.dumps(cfg, sort_keys=True)
            if key in done:
                continue
            jobs = [(cfg, pl, ti, T, st) for pl in PL for ti in range(len(TR)) for T in LENS for st in R.STYLES]
            res = {}
            for k, w, lk in p.imap_unordered(job, jobs, chunksize=4):
                res[k] = (w, lk)
            s = summarize(res)
            with open(outf, "a") as f:
                f.write(json.dumps(dict(cfg=cfg, cap=CAP, **s)) + "\n")
            print(key, s["avg"]["gap_even"], s["avg"]["gap_wrong"], s["avg"]["gap_even_street"], s["pacing_gap"], flush=True)
