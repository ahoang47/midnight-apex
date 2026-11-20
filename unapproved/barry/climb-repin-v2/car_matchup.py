"""Playtest car matchups on the playtest track (spec/race_config.json, 10 Touge corners, per-turn), 80/80 sim player,
r = 1, 2,000 seeded races. live vs lock cap (Austin 7:01 AM: "gauge stays hot after unlocking": a player lock ends after
2 turn ends, load unchanged). Uses the patched sim copy (per_phase.patch). Per-gauge lock shares and AI lock lengths too.
Usage: python3 car_matchup.py [sim_copy=/tmp/pp/sim]"""
import json, sys
from multiprocessing import Pool
SIM = sys.argv[1] if len(sys.argv) > 1 else "/tmp/pp/sim"; sys.path.insert(0, SIM)
from velocity_shift.models import MatchConfig, CombatantStats
from velocity_shift.simulation import SimulationRunner

CORNERS = [c["corner"] for c in json.load(open("../../../spec/race_config.json"))["corners"]]
CARS = {"mx5": (1350, 750, 900), "s2000": (1350, 750, 900), "wrx_sti": (750, 750, 1500)}   # globals.gd:143 POW/HAN/EN
MATCH = {"MX-5 vs S2000": ("mx5", "s2000"), "WRX vs MX-5": ("wrx_sti", "mx5")}
VAR = {"live": {}, "lockcap2": dict(lock_cap=2, lock_cap_keep_load=True), "lockcap2_both": dict(lock_cap=2, lock_cap_keep_load=True, opponent_lock_cap=2),
       "falloff0.5": dict(falloff_t=0.5), "falloff0.7": dict(falloff_t=0.7)}


def job(a):
    mname, v, k0, n = a; p, o = (CARS[c] for c in MATCH[mname])
    g = dict(deg=0, mult=0.0, longest=[], win=0.0, races=0, turns=0, clashes=0, limp=0, overrun=0, start_locked=0, runs=[], gauge_locked_turns=[0, 0, 0], ai_runs=[], ai_start_locked=0)
    for k in range(k0, k0 + n):
        cfg = MatchConfig(player_stats=CombatantStats(name="P", pow=p[0] / 10, han=p[1] / 10, en=p[2] / 10, level=50),
                          opponent_stats=CombatantStats(name="O", pow=o[0] / 10, han=o[1] / 10, en=o[2] / 10, level=50),
                          max_turns=10, district="touge", encounter_type="boss", corners=list(CORNERS), seed=98_000_000 + k,
                          player_read=0.8, player_timing=0.8, player_pacing=0.8, **VAR[v])
        m = SimulationRunner(cfg).run().match; g["races"] += 1
        g["win"] += 1.0 if m.player_total_progress > m.opponent_total_progress else 0.5 if m.player_total_progress == m.opponent_total_progress else 0.0
        pd = m.pref_degraded; g["deg"] += sum(pd); rr = bb = 0
        for x in pd:
            rr = rr + 1 if x else 0; bb = max(bb, rr)
        g["longest"].append(bb); g["mult"] += sum(sum(tr.player_heat_mults) for tr in m.turn_results)
        run = [0] * 3; arun = [0] * 3; prev = [False] * 3; aprev = [False] * 3
        for tr in m.turn_results:
            g["turns"] += 1; g["start_locked"] += any(prev); g["ai_start_locked"] += any(aprev)
            for x, l in zip(tr.player_heat_mults, tr.player_limp):
                g["clashes"] += 1; g["limp"] += l; g["overrun"] += (x < 1 and not l)
            for i in range(3):
                if tr.player_locked[i]: run[i] += 1; g["gauge_locked_turns"][i] += 1
                elif run[i]: g["runs"].append(run[i]); run[i] = 0
                if tr.opponent_locked[i]: arun[i] += 1
                elif arun[i]: g["ai_runs"].append(arun[i]); arun[i] = 0
            prev = list(tr.player_locked); aprev = list(tr.opponent_locked)
        g["runs"] += [x for x in run if x]; g["ai_runs"] += [x for x in arun if x]
    return mname, v, g


if __name__ == "__main__":
    J = [(m, v, k0, 250) for m in MATCH for v in VAR for k0 in range(0, 2000, 250)]
    with Pool(8) as pool: R = pool.map(job, J)
    agg = {}
    for m, v, g in R:
        a = agg.setdefault((m, v), None)
        if a is None: agg[(m, v)] = g
        else:
            for k in g:
                if k == "gauge_locked_turns": a[k] = [x + y for x, y in zip(a[k], g[k])]
                else: a[k] += g[k]
    out = {}
    for (m, v), g in agg.items():
        r = g["runs"]; ar = g["ai_runs"]
        out.setdefault(m, {})[v] = dict(win=round(100 * g["win"] / g["races"], 2), turns_starting_locked_pct=round(100 * g["start_locked"] / g["turns"], 1),
            limp_pct=round(100 * g["limp"] / g["clashes"], 1), overrun_pct=round(100 * g["overrun"] / g["clashes"], 1),
            locks_per_race=round(len(r) / g["races"], 2), mean_lock_turns=round(sum(r) / max(1, len(r)), 2), max_lock_turns=max(r or [0]),
            locked_turn_share_POW_HAN_EN=[round(100 * x / g["turns"], 1) for x in g["gauge_locked_turns"]],
            ai_turns_starting_locked_pct=round(100 * g["ai_start_locked"] / g["turns"], 1), ai_mean_lock_turns=round(sum(ar) / max(1, len(ar)), 2),
            ai_max_lock_turns=max(ar or [0]), ai_lock_runs_over_2=sum(1 for x in ar if x > 2), pref_degraded_pct=round(100 * g['deg'] / g['turns'], 1),
            avg_mult=round(g['mult'] / g['clashes'], 3), longest_degraded_mean=round(sum(g['longest']) / g['races'], 2), longest_degraded_max=max(g['longest']))
        print(m, v, out[m][v])
    json.dump(dict(n=2000, seeds="98,000,000 + k", out=out), open("car_matchup.json", "w"), indent=1)
