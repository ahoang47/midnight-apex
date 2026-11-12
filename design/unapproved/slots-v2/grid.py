"""Generate official-style clash-count banks on a share grid (POW, HAN, EN shares), for deck weights of skewed builds.
Grid: shares = 1/3 + k * 0.025, every share in [0.15, 0.65]. Each point: 3 districts x 3 seeds x 10/20/30 turns, N=4000,
q_read 0.6, same seed formula as the official banks (so the balanced point reproduces them bit-for-bit)."""
import os, sys, itertools, time
import numpy as np
from multiprocessing import Pool
import gen

STEP = 0.025
OUT = "/workspace/barry-drafts/slots-v2/counts"
N = 4000


def points():
    pts = []
    for kp in range(-7, 13):
        for kh in range(-7, 13):
            ke = -kp - kh
            s = [1 / 3 + kp * STEP, 1 / 3 + kh * STEP, 1 / 3 + ke * STEP]
            if all(0.15 - 1e-9 <= x <= 0.65 + 1e-9 for x in s):
                pts.append((kp, kh))
    return pts


def path(kp, kh):
    return os.path.join(OUT, f"p{kp:+d}_h{kh:+d}.npz")


def one(pt):
    kp, kh = pt
    if os.path.exists(path(kp, kh)):
        return pt
    ke = -kp - kh
    stats = (100 * 3 * (1 / 3 + kp * STEP), 100 * 3 * (1 / 3 + kh * STEP), 100 * 3 * (1 / 3 + ke * STEP))
    pack = {}
    for d in gen.DISTRICTS:
        for sd in gen.SEEDS:
            for L in gen.LENGTHS:
                pack[f"{d}_{sd}_{L}"] = gen.counts(N, L, 0.6, sd, d, stats).astype(np.int8)
    tmp = path(kp, kh) + ".tmp.npz"
    np.savez_compressed(tmp, **pack); os.replace(tmp, path(kp, kh))
    return pt


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pts = points()
    # center-out order so the most-used points finish first
    pts.sort(key=lambda p: abs(p[0]) + abs(p[1]) + abs(p[0] + p[1]))
    print("grid points:", len(pts), flush=True)
    t = time.time()
    with Pool(8) as pool:
        for i, pt in enumerate(pool.imap_unordered(one, pts)):
            if i % 10 == 0:
                print(i, pt, round(time.time() - t), "s", flush=True)
    print("done", round(time.time() - t), "s")
