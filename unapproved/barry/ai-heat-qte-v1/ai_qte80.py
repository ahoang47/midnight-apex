"""ai-heat-qte-v1 v2 (Barry DRAFT 2026-11-19): AI QTE = seeded random per turn, mean 0.80 (Austin via Gordon).

Runs on a THROWAWAY copy of sim/ with opponent_qte.patch applied (the live sim has no spread fields):
  rm -rf /tmp/aiqte_b && cp -r ../../../sim /tmp/aiqte_b && (cd /tmp/aiqte_b && patch -p2 < $PWD/opponent_qte.patch)
  AIQTE_SIM=/tmp/aiqte_b python3 ai_qte80.py JOBS.json OUT.json
JOBS.json: list of cells {"mode": "boss"|"touge", "d", "r", "prof": "60/60"|"80/80", "mean", "sd", "lo", "hi",
  optional "kappa_mult" (x kappa_for_length, in-process, Street lever test) and "boss_shape" [pow, han, en] shares (boss tune lever)}.
AI heat rules are the live (boss) rules; nothing about heat is patched.
"""
import json, math, os, sys
from multiprocessing import Pool
SIM = os.environ.get("AIQTE_SIM", "/tmp/aiqte_b")
sys.path.insert(0, SIM)
from velocity_shift import combat as C, equations as E, simulation as S
from velocity_shift.models import CombatantStats, MatchConfig
from velocity_shift.simulation import SimulationRunner
assert hasattr(MatchConfig(player_stats=None, opponent_stats=None), "opponent_qte_sd"), "AIQTE_SIM must be the patched copy"

HERE = os.path.dirname(os.path.abspath(__file__))
HARD = {"street": "S1_Shibuya_Grid", "wangan": "W3_C1_Outer", "touge": "T3_Usui_Esses"}
BLOCKS = json.load(open(os.path.join(HERE, "..", "touge-race-parity", "blocks.json")))["cars"]
_k0 = E.kappa_for_length


def cell(c):
    km = c.get("kappa_mult", 1.0)
    kf = (lambda L: _k0(L) * km)
    C.kappa_for_length = kf; S.kappa_for_length = kf            # in-process only (lever test)
    q = 0.6 if c["prof"] == "60/60" else 0.8
    qte = dict(opponent_qte_ratio=c["mean"] / E.OPPONENT_QTE, opponent_qte_sd=c["sd"], opponent_qte_min=c["lo"], opponent_qte_max=c["hi"])
    w = 0.0; n = 0
    if c["mode"] == "boss":
        d, r = c["d"], c["r"]; sp, sh, se = E.DISTRICT_TUNE[d]; tot = 300.0 * r
        bp, bh, be = c.get("boss_shape", (1 / 3, 1 / 3, 1 / 3))
        runs = [(CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50),
                 CombatantStats(name="Opponent", pow=300 * bp, en=300 * be, han=300 * bh, level=50),
                 30, 77_000_000 + si * 100_000 + k, d, list(C.official_tracks()[d][HARD[d]]), st)
                for si, st in enumerate(E.BOSS_STYLES) for k in range(c.get("N", 2000))]
    else:                                                        # 10-turn Touge test race, parity mirror (brz vs mx5)
        P, O = BLOCKS["brz"], BLOCKS["mx5"]; tr = C.official_tracks()["touge"]
        runs = [(CombatantStats(name="Player", pow=P["pow"] / 10, en=P["en"] / 10, han=P["han"] / 10, level=50),
                 CombatantStats(name="Opponent", pow=O["pow"] / 10, en=O["en"] / 10, han=O["han"] / 10, level=50),
                 10, 88_000_000 + ti * 1_000_000 + si * 100_000 + k, "touge", list(tr[t]), st)
                for ti, t in enumerate(sorted(tr)) for si, st in enumerate(E.BOSS_STYLES) for k in range(c.get("N", 400))]
    for ps, os_, T, seed, d, lap, st in runs:
        cfg = MatchConfig(player_stats=ps, opponent_stats=os_, max_turns=T, seed=seed, district=d, corners=lap,
                          player_read=q, player_timing=q, player_pacing=q, boss_style=st, encounter_type="boss", **qte)
        m = SimulationRunner(cfg).run().match
        a, b = m.player_total_progress, m.opponent_total_progress
        w += 1.0 if a > b else 0.5 if a == b else 0.0; n += 1
    p = w / n
    return dict(c, n=n, win=round(100 * p, 2), se=round(100 * math.sqrt(p * (1 - p) / n), 2))


if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    with Pool(8) as pool:
        rows = pool.map(cell, jobs, chunksize=1)
    old = json.load(open(sys.argv[2])) if os.path.exists(sys.argv[2]) else []
    json.dump(old + rows, open(sys.argv[2], "w"), indent=1)
    for x in rows:
        print({k: x[k] for k in x if k not in ("lo", "hi", "N")})
