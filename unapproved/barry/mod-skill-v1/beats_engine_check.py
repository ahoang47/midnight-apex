"""STORY-BEAT draft engine check (Barry, 2026-11-19): live SimulationRunner (0.80 random AI QTE, boss shares), on-tune builds,
same seeds/setup as ai-heat-qte-v1/verify_boss_live.py, at the r each player meets the retuned boss with (N = 5, beats.json):
min path (exactly 5 required wins), K3 (3 extra XP-paying optional wins), full build (all mods maxed). -> beats_engine_check.json"""
import json, math, os, sys
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "sim"))
from velocity_shift import combat as C, equations as E
from velocity_shift.models import CombatantStats, MatchConfig
from velocity_shift.simulation import SimulationRunner
B = json.load(open(os.path.join(HERE, "beats.json")))
DIST = ("street", "wangan", "touge")
RT = B["retune"]["5"]; K3 = next(r for r in B["optional_xp_cap"]["5"]["rows"] if r["K"] == 3)["rounds"]
CASES = [(who, d, r) for i, d in enumerate(DIST) for who, r in (("min_path", RT[i]["boss_r_new"]), ("K3", K3[i]["r"]), ("full_build", RT[i]["full_r"]))]


def cell(a):
    who, d, r, prof = a; q = 0.6 if prof == "60/60" else 0.8
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
    return dict(who=who, d=d, r=r, prof=prof, n=n, win=round(100 * p, 2), se=round(100 * math.sqrt(p * (1 - p) / n), 2))


if __name__ == "__main__":
    with Pool(8) as pool:
        rows = pool.map(cell, [c + (p,) for c in CASES for p in ("60/60", "80/80")])
    json.dump(rows, open(os.path.join(HERE, "beats_engine_check.json"), "w"), indent=1)
    for x in rows: print(x)
