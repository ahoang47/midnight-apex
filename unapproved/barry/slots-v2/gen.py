"""Clash-count generator for a given player stat split (deck weights from shares).

Identical to lines-v1 lib.generate_counts except the player's (POW, HAN, EN) stats are a parameter instead of (100,100,100).
Counts depend on the player's deck weights only (DECK_ALPHA mix of stat shares); timing, HAN-QTE and the POW/EN payoff
multipliers are applied analytically in the oracle. Lines = repo LINE_SET_C (lines-v1 S-A + W-A).
"""
import sys, os, time
import numpy as np
sys.path.insert(0, "/workspace/barry-drafts/lines-v1")
cwd = os.getcwd()
import lib  # noqa: E402  (chdirs to final-v1)
os.chdir(cwd)

LINES = lib.apply_edits(lib.apply_edits(lib.LINES0, "street", {"N90": "SSA"}), "wangan", {"SW": "AAD", "IR": "AAD"})
SEEDS = (20261113, 20261114, 20261115)
LENGTHS = (10, 20, 30)
DISTRICTS = ("touge", "wangan", "street")


def counts(n, L, q_read, seed, district, stats_phe):
    corners, dist = lib.layout_district(district, n, L)
    s = seed + L * 1000 + int(q_read * 100) * 10 + int(round(lib.A * 100))
    ps, os_ = lib.E4.generate_clashes(n, corners, dist, LINES, lib.ALT_W, q_read, lib.A, tuple(stats_phe), s)
    o = lib.E2.outcome(ps, os_).reshape(n, -1)
    return np.stack([(o == 1).sum(1), (o == 0).sum(1), (o == -1).sum(1)], 1).astype(float)


if __name__ == "__main__":
    t = time.time()
    ref = dict(np.load("/workspace/barry-drafts/lines-v1/counts_S_N90=SSA.npz"))
    c = counts(4000, 20, 0.6, 20261113, "street", (100, 100, 100))
    print("street 20t balanced identical to official bank:", np.array_equal(c, ref["20261113_0.6_20"]), round(time.time() - t, 1), "s")
    ref = dict(np.load("/workspace/barry-drafts/lines-v1/counts_W_SW=IR=AAD.npz"))
    c = counts(4000, 10, 0.6, 20261114, "wangan", (100, 100, 100))
    print("wangan 10t identical:", np.array_equal(c, ref["20261114_0.6_10"]), round(time.time() - t, 1), "s")
