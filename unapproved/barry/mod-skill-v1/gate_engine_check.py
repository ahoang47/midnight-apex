"""GATE draft engine check (Barry, 2026-11-19): live SimulationRunner (0.80 random AI QTE, boss shares) at the exact boss r
a gated player arrives with (cap power / boss budget from gate.json), on-tune build, same seeds/setup as
ai-heat-qte-v1/verify_boss_live.py. -> gate_engine_check.json"""
import json, math, os, sys
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "sim"))
from velocity_shift import combat as C, equations as E
from velocity_shift.models import CombatantStats, MatchConfig
from velocity_shift.simulation import SimulationRunner
G = json.load(open(os.path.join(HERE, "gate.json")))["walks"]["gate"]
R = {d: G[i]["boss_r"] for i, d in enumerate(("street", "wangan", "touge"))}


def cell(a):
    d, prof = a; q = 0.6 if prof == "60/60" else 0.8; r = R[d]
    sp, sh, se = E.DISTRICT_TUNE[d]; bp, bh, be = E.BOSS_STAT_SHARES[d]; tot = 300.0 * r; w = n = 0
    for si, st in enumerate(E.BOSS_STYLES):
        for k in range(2000):
            cfg = MatchConfig(player_stats=CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50),
                              opponent_stats=CombatantStats(name="Opponent", pow=300 * bp, en=300 * be, han=300 * bh, level=50),
                              max_turns=30, seed=77_000_000 + si * 100_000 + k, district=d,
                              corners=list(C.official_tracks()[d][E.BOSS_HARD_TRACK[d]]), player_read=q, player_timing=q,
                              player_pacing=q, boss_style=st, encounter_type="boss")
            m = SimulationRunner(cfg).run().match; a_, b_ = m.player_total_progress, m.opponent_total_progress
            w += 1.0 if a_ > b_ else 0.5 if a_ == b_ else 0.0; n += 1
    p = w / n
    return dict(d=d, r=r, prof=prof, n=n, win=round(100 * p, 2), se=round(100 * math.sqrt(p * (1 - p) / n), 2))


if __name__ == "__main__":
    with Pool(6) as pool:
        rows = pool.map(cell, [(d, p) for d in ("street", "wangan", "touge") for p in ("60/60", "80/80")])
    json.dump(rows, open(os.path.join(HERE, "gate_engine_check.json"), "w"), indent=1)
    for x in rows: print(x)
