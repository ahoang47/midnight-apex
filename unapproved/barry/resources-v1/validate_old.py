"""Check that resources_v1.run_old reproduces the live engine (velocity_shift.match.run_match) win rates."""
import sys, os, json
import numpy as np
import resources_v1 as R
from velocity_shift.match import run_match
from velocity_shift.models import MatchConfig, CombatantStats

def live(shares, r, d, lap, T, qr, qt, n, seed0):
    B = 300.0; tot = B * r
    p, h, e = shares
    wins = 0.0
    for k in range(n):
        cfg = MatchConfig(player_stats=CombatantStats("P", pow=tot*p, en=tot*e, han=tot*h),
                          opponent_stats=CombatantStats("O", pow=100, en=100, han=100),
                          max_turns=T, seed=seed0 + k, district=d, corners=lap,
                          player_read=qr, player_timing=qt)
        res = run_match(cfg, None, None, None, None)
        wins += 1.0 if res.winner == "P" else 0.5 if res.winner == "Tie" else 0.0
    return 100 * wins / n

out = []
tr = R.tracks()
cases = [((1/3,1/3,1/3), 1.0, "touge", 10, 0.6, 0.6), ((0.5,0.25,0.25), 1.0, "street", 10, 0.6, 0.6),
         ((0.25,0.25,0.5), 0.9, "wangan", 20, 1.0, 1.0), ((1/3,1/3,1/3), 0.8, "touge", 10, 1.0, 1.0)]
for sh, r, d, T, qr, qt in cases:
    lap = R.C.track_corners(d, 0)
    # q_time in live run_match is evaluated at the visible zone: raw_qte_score(r, q_time=qt)
    raw = R.E.raw_qte_score(r, q_time=qt)
    a = live(sh, r, d, lap, T, qr, qt, 3000, 777000)
    b = 100 * R.run_old([sh], r, d, lap, T, qr, raw, 20000, 4242)[0][0]
    out.append(dict(shares=sh, r=r, district=d, T=T, q_read=qr, q_time=qt, raw_qte=raw, live_n3000=a, vec_n20000=b, diff=b - a))
    print(out[-1], flush=True)
json.dump(out, open("validate_old.json", "w"), indent=1)
