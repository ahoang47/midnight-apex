"""Cooldown check: 80/80 sim player (live SimulationRunner: read 0.8, timing 0.8, pacing 0.8) on the playtest track
(spec/race_config.json, 10 Touge corners) vs the MX-5 draft block (POW/HAN/EN 45/25/30) under the live AI heat rules,
r = 1, 2000 seeded races per player split. Optional heat overrides (proposal what-ifs) patch equations/heat constants.
Usage: python3 matchup_mc.py [n=2000] [variant=live]"""
import json, sys
from multiprocessing import Pool
sys.path.insert(0, "../../../sim")
from velocity_shift import equations as E, heat as H
from velocity_shift.models import MatchConfig, CombatantStats
from velocity_shift.simulation import SimulationRunner

CORNERS = [c["corner"] for c in json.load(open("../../../spec/race_config.json"))["corners"]]
SPLITS = {"WRX (25/25/50)": (0.25, 0.25, 0.50), "MX-5 / Touge tune (45/25/30)": (0.45, 0.25, 0.30),
          "even (33/33/33)": (1 / 3, 1 / 3, 1 / 3), "HAN-heavy (30/45/25)": (0.30, 0.45, 0.25)}
VARIANTS = {"live": {}, "release50": {"HEAT_RELEASE": 0.5}, "shareexp1": {"HEAT_SHARE_EXP": 1.0},
            "nopassivelock": {"lock_on_passive": False}}


def apply(v):
    for k, val in VARIANTS[v].items():
        if k == "lock_on_passive":
            init = H.HeatGauges.__init__
            def patched(self, shares, r, wear, cap_turns=E.HEAT_CAP_TURNS, recovery=E.HEAT_RECOVERY, release=None, lock_on_passive=True, _i=init):
                _i(self, shares, r, wear, cap_turns, recovery, H.HEAT_RELEASE if release is None else release, False)
            H.HeatGauges.__init__ = patched
        else:
            setattr(E, k, val)
            if hasattr(H, k): setattr(H, k, val)
            if k == "HEAT_RELEASE":   # default arg is bound at def time: rebind the player constructor
                H.HeatGauges.for_player = classmethod(lambda cls, p, e, h, r, w: cls(H.build_shares(p, e, h), r, w, release=val))


def job(a):
    name, v, k0, n = a; apply(v); sp = SPLITS[name]
    agg = dict(win=0.0, clashes=0, overrun=0, limp=0, lock_turn_starts=0, turns=0, lock_runs=[], forced_turns=0)
    for k in range(k0, k0 + n):
        cfg = MatchConfig(player_stats=CombatantStats(name="P", pow=300 * sp[0], han=300 * sp[1], en=300 * sp[2], level=50),
                          opponent_stats=CombatantStats(name="O", pow=135, han=75, en=90, level=50), max_turns=10,
                          district="touge", encounter_type="boss", corners=list(CORNERS), seed=98_000_000 + k,
                          player_read=0.8, player_timing=0.8, player_pacing=0.8)
        m = SimulationRunner(cfg).run().match
        agg["win"] += 1.0 if m.player_total_progress > m.opponent_total_progress else 0.5 if m.player_total_progress == m.opponent_total_progress else 0.0
        run = [0, 0, 0]; prev = [False] * 3
        for tr in m.turn_results:
            agg["turns"] += 1; agg["lock_turn_starts"] += sum(prev); agg["forced_turns"] += any(prev)
            for x, l in zip(tr.player_heat_mults, tr.player_limp):
                agg["clashes"] += 1; agg["overrun"] += (x < 1 and not l); agg["limp"] += l
            for i, lk in enumerate(tr.player_locked):
                if lk: run[i] += 1
                elif run[i]: agg["lock_runs"].append(run[i]); run[i] = 0
            prev = list(tr.player_locked)
        agg["lock_runs"] += [x for x in run if x]
    return name, v, agg


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000; vs = sys.argv[2].split(",") if len(sys.argv) > 2 else ["live"]
    J = [(s, v, k0, 250) for v in vs for s in SPLITS for k0 in range(0, n, 250)]
    with Pool(8) as p: R = p.map(job, J)
    out = {}
    for name, v, a in R:
        o = out.setdefault(v, {}).setdefault(name, dict(win=0.0, clashes=0, overrun=0, limp=0, lock_turn_starts=0, turns=0, lock_runs=[], forced_turns=0))
        for k in a: o[k] += a[k]
    res = {}
    for v in out:
        for name, o in out[v].items():
            lr = o["lock_runs"]; races = o["turns"] / 10
            res.setdefault(v, {})[name] = dict(win=round(100 * o["win"] / races, 2), overrun_pct=round(100 * o["overrun"] / o["clashes"], 1),
                limp_pct=round(100 * o["limp"] / o["clashes"], 1), turns_starting_locked_pct=round(100 * o["forced_turns"] / o["turns"], 1),
                locked_gauges_per_turn=round(o["lock_turn_starts"] / o["turns"], 2), locks_per_race=round(len(lr) / races, 2),
                mean_lock_turns=round(sum(lr) / max(1, len(lr)), 2))
            print(v, name, res[v][name])
    json.dump(dict(n=n, seeds="98,000,000 + k", out=res), open("matchup_mc_%s.json" % "_".join(vs), "w"), indent=1)
