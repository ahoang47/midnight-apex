"""Bit-identity check for opponent_qte.patch (ai-heat-qte-v1 v2). Usage: python3 patch_identity_test.py LIVE_SIM PATCHED_SIM
Runs the same seeded races (3 districts x 3 boss styles x 60/60 + 80/80 x 30 turns, plus 10-turn Touge parity races) through
the live sim and the patched sim with default MatchConfig (opponent_qte_ratio None, sd 0), and compares a SHA-256 of
every turn's stances, QTE scores, heat mults/fills and progress (repr of floats, so bit-exact)."""
import hashlib, subprocess, sys, json
CODE = r'''
import sys, hashlib
sys.path.insert(0, sys.argv[1])
from velocity_shift import combat as C, equations as E
from velocity_shift.models import CombatantStats, MatchConfig
from velocity_shift.simulation import SimulationRunner
h = hashlib.sha256(); n = 0
for d, r in (("street", 1.044), ("wangan", 1.0548), ("touge", 1.0702)):
    for st in E.BOSS_STYLES:
        for q in (0.6, 0.8):
            for k in range(60):
                sp, sh, se = E.DISTRICT_TUNE[d]; tot = 300 * r; lap = list(C.official_tracks()[d].values())[k % 5]
                for T, ps, os_ in ((30, (tot*sp, tot*se, tot*sh), (100, 100, 100)), (10, (135, 90, 75), (75, 150, 75))):
                    cfg = MatchConfig(player_stats=CombatantStats(name="P", pow=ps[0], en=ps[1], han=ps[2], level=50),
                                      opponent_stats=CombatantStats(name="O", pow=os_[0], en=os_[1], han=os_[2], level=50),
                                      max_turns=T, seed=5_000_000 + k, district=d, corners=list(lap),
                                      player_read=q, player_timing=q, player_pacing=q, boss_style=st)
                    m = SimulationRunner(cfg).run().match
                    for t in m.turn_results:
                        h.update(repr((t.player_stances, t.opponent_stances, t.player_qte, t.opponent_qte, t.player_heat_mults,
                                       t.opponent_heat_mults, t.player_heat_fill, t.opponent_heat_fill, t.player_progress,
                                       t.opponent_progress)).encode())
                    h.update(repr((m.player_total_progress, m.opponent_total_progress, m.winner)).encode()); n += 1
print(n, h.hexdigest())
'''
out = {}
for tag, path in (("live", sys.argv[1]), ("patched", sys.argv[2])):
    out[tag] = subprocess.run([sys.executable, "-c", CODE, path], capture_output=True, text=True, check=True).stdout.split()
print(json.dumps(out)); print("BIT-IDENTICAL" if out["live"] == out["patched"] else "DIFFERENT")
