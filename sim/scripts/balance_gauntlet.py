"""
Balance Gauntlet — heat/load combat targets on the live engine (resources-v4b G2,
Austin approved 2026-11-13). Replaces the old HP/DP archetype gauntlet (card draw removed).

For every cell (15 official tracks x 10/20/30 turns x 3 boss styles) it races the G2
tuned split for that cell (config/heat_g2_tuned.json, from the G2 full runs) and the even
split through match.py / SimulationRunner, then checks the targets:

  perfect play (read 1.0, QTE 1.0, full pacing) at r 0.80, 20/30 turns : 10-25 %
  perfect play at r 1.00                                                : >= 85 %
  average play (read 0.6, average QTE profile, pacing 0.6) at the cap   : 60-75 % (all, 20, 30 turns)
  live vs G2 full runs, same splits                                     : within TOL pp (overall, per measure)

Constants come from velocity_shift/equations.py (MOD_CAP_FRACTION is the cap).

Usage:
  python3 scripts/balance_gauntlet.py            # N races per cell (default 24)
  python3 scripts/balance_gauntlet.py --n 100
Exit code 1 if a target or the G2 match fails.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from velocity_shift import equations as E                        # noqa: E402
from velocity_shift.combat import official_tracks                 # noqa: E402
from velocity_shift.models import CombatantStats, MatchConfig     # noqa: E402
from velocity_shift.simulation import SimulationRunner            # noqa: E402

TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "heat_g2_tuned.json")
OPP_TOTAL = 300.0
TOL = 4.0
# measure -> (r, q_read, q_time (None = average profile), pacing share)
MEASURES = {
    "perf_0.8": (0.80, 1.0, 1.0, 1.0),
    "perf_1.0": (1.00, 1.0, 1.0, 1.0),
    "avg_cap": (E.MOD_CAP_FRACTION, 0.6, None, 0.6),
}


def race_cell(measure: str, district: str, lap: list[str], length: int, style: str, tune, n: int, seed: int) -> float:
    r, q, qt, pace = MEASURES[measure]
    sp, sh, se = tune
    tot = OPP_TOTAL * r
    player = CombatantStats("Player", pow=tot * sp, en=tot * se, han=tot * sh)
    o = OPP_TOTAL / 3
    opp = CombatantStats("Boss", pow=o, en=o, han=o)
    w = 0.0
    for i in range(n):
        cfg = MatchConfig(player_stats=player, opponent_stats=opp, max_turns=length, seed=seed + i,
                          district=district, corners=lap, player_read=q, player_timing=qt,
                          player_qte_profile=None if qt is not None else "average",
                          player_pacing=pace, boss_style=style)
        m = SimulationRunner(cfg).run().match
        gp, go = m.player_total_progress, m.opponent_total_progress
        w += 1.0 if gp > go else 0.5 if gp == go else 0.0
    return 100.0 * w / n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24, help="races per cell")
    a = ap.parse_args()
    table = json.load(open(TABLE))
    tracks = {(d, name): lap for d, tr in official_tracks().items() for name, lap in tr.items()}
    live = defaultdict(list); g2 = defaultdict(list); even = defaultdict(list)
    for ci, c in enumerate(table["cells"]):
        if c["measure"] not in MEASURES:
            continue
        lap = tracks[(c["district"], c["track"])]
        seed = 20261113 * 7 + ci * 1000
        v = race_cell(c["measure"], c["district"], lap, c["length"], c["style"], c["tune"], a.n, seed)
        ve = race_cell(c["measure"], c["district"], lap, c["length"], c["style"], (1 / 3, 1 / 3, 1 / 3), a.n, seed)
        for key in ((c["measure"], "all"), (c["measure"], c["length"]), (c["measure"], c["district"])):
            live[key].append(v); g2[key].append(c["g2_win"]); even[key].append(ve)
    mean = lambda x: sum(x) / len(x)
    print(f"Heat/load gauntlet (G2), cap {E.MOD_CAP_FRACTION}, {a.n} races per cell; tuned = G2 split per cell, [even car]")
    print(f"{'measure':<10} {'slice':<8} {'live':>6} {'G2':>6} {'even':>6}")
    for key in sorted(live, key=lambda k: (k[0], str(k[1]))):
        print(f"{key[0]:<10} {str(key[1]):<8} {mean(live[key]):6.1f} {mean(g2[key]):6.1f} {mean(even[key]):6.1f}")
    fails = []
    for L in (20, 30):
        v = mean(live[("perf_0.8", L)])
        if not 10.0 <= v <= 25.0:
            fails.append(f"perfect at 0.80, {L} turns: {v:.1f} (target 10-25)")
    v = mean(live[("perf_1.0", "all")])
    if v < 85.0:
        fails.append(f"perfect at 1.00: {v:.1f} (target >= 85)")
    for key in ("all", 20, 30):
        v = mean(live[("avg_cap", key)])
        if not 60.0 <= v <= 75.0:
            fails.append(f"average at the cap, {key}: {v:.1f} (target 60-75)")
    for m in MEASURES:
        d = mean(live[(m, "all")]) - mean(g2[(m, "all")])
        if abs(d) > TOL:
            fails.append(f"{m}: live {mean(live[(m, 'all')]):.1f} vs G2 {mean(g2[(m, 'all')]):.1f} (tolerance {TOL})")
    print()
    if fails:
        print("FAIL:\n  " + "\n  ".join(fails))
        return 1
    print("PASS: all G2 targets hit on the live engine, and it matches the G2 full runs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
