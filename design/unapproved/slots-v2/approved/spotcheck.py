"""Playable-engine spot-check (same cells/method as sim/tests/test_playable_oracle.py: N_PER_TRACK=200 -> 1000 races per
(seed, length), seeds 20261113-15 x 10/20/30 turns = 9 batches) plus the official oracle band and the official progression totals.
Usage: python3 spotcheck.py OUT.json"""
import sys, json
sys.path.insert(0, "/workspace/midnight-apex/sim")
from velocity_shift.progression import win_rate
from velocity_shift import progression as P, equations as E
from velocity_shift.simulation import simulate_win_rate

CELLS = [("street", 1.05, "Street boss at target"), ("street", 1.0355, "Street mature #2 skipped"),
         ("touge", 1.05, "Touge boss at target"), ("wangan", 1.05, "Wangan boss at target")]
out = {"knot": E.KNOT_WINDOW_105, "zone": {r: E.qte_zone_width(r) for r in (0.95, 1.0, 1.0004, 1.02, 1.0355, 1.037, 1.05)}, "cells": []}
for d, r, lab in CELLS:
    rates = [simulate_win_rate(d, r, E.AVERAGE_PLAY_Q, L, sd, n_per_track=200) for L in E.RACE_LENGTHS for sd in E.SIM_SEEDS]
    lo, hi = win_rate(r, E.AVERAGE_PLAY_Q, d)
    out["cells"].append(dict(cell=lab, r=r, playable_min=round(min(rates), 1), playable_max=round(max(rates), 1),
                             playable_mean=round(sum(rates) / len(rates), 2), oracle_band=(lo, hi)))
    print(out["cells"][-1], flush=True)
rows, t = P.run("forced")
out["progression_forced_default_order"] = t
print(t, out["zone"])
json.dump(out, open(sys.argv[1], "w"), indent=1)
