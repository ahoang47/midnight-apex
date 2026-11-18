"""Boss checks, spirit OFF, live SimulationRunner (no spirit code), fixed layout at the round cap (full build on tune,
shares = DISTRICT_TUNE, from fixed_layout.py). Hardest track per district, 30 turns, 3 boss styles, ties = half.
N per style per cell below. Also a Street r scan. -> boss_engine_check.json"""
import json, math, os, sys
from multiprocessing import Pool
import mod_skill  # sets sys.path to live sim (read-only)
from velocity_shift import combat as C, equations as E
from velocity_shift.models import CombatantStats, MatchConfig
from velocity_shift.simulation import SimulationRunner

HERE = os.path.dirname(os.path.abspath(__file__))
HARD = {"street": "S1_Shibuya_Grid", "wangan": "W3_C1_Outer", "touge": "T3_Usui_Esses"}
N = 3000


def cell(a):
    d, r, prof, seed0 = a
    q = 0.6 if prof == "c6060" else 0.8; sp, sh, se = E.DISTRICT_TUNE[d]; tot = 300.0 * r; w = 0.0; n = 0
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(N):
            cfg = MatchConfig(player_stats=CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50),
                              opponent_stats=CombatantStats(name="Opponent", pow=100.0, en=100.0, han=100.0, level=50),
                              max_turns=30, seed=seed0 + si * 100_000 + k, district=d, corners=list(C.official_tracks()[d][HARD[d]]),
                              player_read=q, player_timing=q, player_pacing=q, boss_style=st, encounter_type="boss")
            m = SimulationRunner(cfg).run().match; a_, b_ = m.player_total_progress, m.opponent_total_progress
            w += 1.0 if a_ > b_ else 0.5 if a_ == b_ else 0.0; n += 1
    p = w / n
    return dict(d=d, r=r, prof=prof, n=n, win=round(100 * p, 2), se=round(100 * math.sqrt(p * (1 - p) / n), 2))


if __name__ == "__main__":
    jobs = [(d, r, p, 77_000_000) for d, r in (("street", 1.044), ("wangan", 1.0548), ("touge", 1.0702)) for p in ("c6060", "c8080")]
    jobs += [("street", r, p, 77_000_000) for r in (1.036, 1.040, 1.042) for p in ("c6060", "c8080")]
    with Pool(8) as pool:
        rows = pool.map(cell, jobs, chunksize=1)
    json.dump(rows, open(os.path.join(HERE, "boss_engine_check.json"), "w"), indent=1)
    for x in rows:
        print(x)
