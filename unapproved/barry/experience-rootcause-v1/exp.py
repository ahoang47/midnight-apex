"""Experience root cause (Austin 8:48 AM): live sim (sim/ at go-live 83b98d8, unchanged), playtest track spec/race_config.json.
Parts: mech (gauge numbers), mx5 (MX-5 vs S2000 representative races + per-turn lock profile), climb (live mod_skill Touge, kid1 -> boss),
levers (player-feel what-ifs on both playtest matchups). Usage: python3 exp.py <part> [variant]. Writes exp_<part>[_variant].json."""
import json, statistics as st, sys
from multiprocessing import Pool
sys.path.insert(0, "../../../sim")
from velocity_shift import equations as E, heat as H, mod_skill as M
from velocity_shift.models import MatchConfig, CombatantStats, Stance
from velocity_shift.simulation import SimulationRunner

CORNERS = [c["corner"] for c in json.load(open("../../../spec/race_config.json"))["corners"]]
CARS = {"mx5": (1350, 750, 900), "s2000": (1350, 750, 900), "wrx": (750, 750, 1500)}   # POW/HAN/EN, globals.gd CAR_DRAFT_BLOCKS
MATCH = {"MX-5 vs S2000": ("mx5", "s2000"), "WRX vs MX-5": ("wrx", "mx5")}
# player-only heat what-ifs (boss rules untouched unless noted): cap_turns, recovery, release, lock_on_passive, share_exp, pacing
BASE = dict(cap=E.HEAT_CAP_TURNS, rec=E.HEAT_RECOVERY, rel=E.HEAT_RELEASE, lop=True, sexp=E.HEAT_SHARE_EXP, pace=0.8, lap=0)
_END = H.HeatGauges.end_turn


def _end_lap(self, corner, _lap=[0]):
    """What-if: the player's gauges reset (load 0, unlocked) at the end of every lap of 10 corners (between laps)."""
    _END(self, corner); self._t = getattr(self, "_t", 0) + 1
    if self.release != E.BOSS_HEAT_RELEASE and self._t % 10 == 0:
        self.load = [0.0, 0.0, 0.0]; self.locked = [False, False, False]
VAR = {"live": {}, "release0.5": dict(rel=0.5), "release0.6": dict(rel=0.6), "cap4": dict(cap=4.0), "rec1.33": dict(rec=4 / 3),
       "cap4_rec1.33": dict(cap=4.0, rec=4 / 3), "nopassivelock": dict(lop=False), "shareexp1(both)": dict(sexp=1.0),
       "telegraph(pacing1.0)": dict(pace=1.0), "greedy(pacing0)": dict(pace=0.0), "greedy_release0.5": dict(pace=0.0, rel=0.5),
       "greedy_cap4_rec1.33": dict(pace=0.0, cap=4.0, rec=4 / 3), "lapreset": dict(lap=1), "lapreset_release0.5": dict(lap=1, rel=0.5)}


def setv(v):
    c = dict(BASE, **VAR[v])
    H.HeatGauges.__init__.__defaults__ = (c["cap"], c["rec"], c["rel"], c["lop"])
    E.HEAT_SHARE_EXP = c["sexp"]
    H.HeatGauges.end_turn = _end_lap if c["lap"] else _END
    return c


def cfg_match(p, o, seed, pace):
    P, O = CARS[p], CARS[o]
    return MatchConfig(player_stats=CombatantStats(name="P", pow=P[0] / 10, han=P[1] / 10, en=P[2] / 10, level=50),
                       opponent_stats=CombatantStats(name="O", pow=O[0] / 10, han=O[1] / 10, en=O[2] / 10, level=50), max_turns=10,
                       district="touge", encounter_type="boss", corners=list(CORNERS), seed=seed,
                       player_read=0.8, player_timing=0.8, player_pacing=pace)


def feel(m, side="player"):
    tr = m.turn_results; L = [getattr(t, side + "_locked") for t in tr]; mult = [x for t in tr for x in getattr(t, side + "_heat_mults")]
    limp = sum(x for t in tr for x in getattr(t, side + "_limp"))
    start_locked = [any(L[i - 1]) if i else False for i in range(len(tr))]
    runs, run = [], [0, 0, 0]
    for lk in L:
        for i in range(3):
            if lk[i]: run[i] += 1
            elif run[i]: runs.append(run[i]); run[i] = 0
    runs += [x for x in run if x]
    allk = sum(all(x) for x in L)
    return dict(start_locked=sum(start_locked), limp=limp, overrun=sum(1 for x in mult if x < 1) - limp, runs=runs,
                avg_mult=sum(mult) / len(mult), all_locked_turns=allk, turns=len(tr), clashes=len(mult))


def agg(rows):
    T = sum(r["turns"] for r in rows); C = sum(r["clashes"] for r in rows); runs = [x for r in rows for x in r["runs"]]
    return dict(turns_starting_locked_pct=round(100 * sum(r["start_locked"] for r in rows) / T, 1),
                limp_pct=round(100 * sum(r["limp"] for r in rows) / C, 1), overrun_pct=round(100 * sum(r["overrun"] for r in rows) / C, 1),
                avg_mult=round(sum(r["avg_mult"] * r["clashes"] for r in rows) / C, 3), locks_per_race=round(len(runs) / len(rows), 2),
                mean_lock_turns=round(sum(runs) / max(1, len(runs)), 2), max_lock_turns=max(runs or [0]),
                races_with_all_locked_pct=round(100 * sum(r["all_locked_turns"] > 0 for r in rows) / len(rows), 1))


def job_match(a):
    name, v, k0, n = a; c = setv(v); p, o = MATCH[name]; out = []
    for k in range(k0, k0 + n):
        m = SimulationRunner(cfg_match(p, o, 98_000_000 + k, c["pace"])).run().match
        f = feel(m); f["ai"] = feel(m, "opponent"); f["win"] = 1.0 if m.player_total_progress > m.opponent_total_progress else 0.0
        f["seed"] = 98_000_000 + k; f["prof"] = [t.player_locked for t in m.turn_results]; out.append(f)
    return name, v, out


def summarize(rows):
    s = agg(rows); s["win"] = round(100 * sum(r["win"] for r in rows) / len(rows), 2); s["ai"] = agg([r["ai"] for r in rows])
    s["locked_at_turn_start_by_turn_PHE_pct"] = [[round(100 * sum(r["prof"][t - 1][i] for r in rows) / len(rows), 1) for i in range(3)] if t else [0, 0, 0]
                                                 for t in range(10)]
    return s


def mech():
    w = H.track_wear("touge", CORNERS); out = {}
    for car in ("mx5", "wrx"):
        P = CARS[car]
        for rules in ("player", "ai"):
            g = H.HeatGauges.for_player(P[0], P[2], P[1], 1.0, w) if rules == "player" else H.HeatGauges.for_boss(P[0], P[2], P[1], w)
            pas = [sum(E.CORNER_HEAT_PASSIVE[c][i] * w[i] for c in CORNERS) / len(CORNERS) for i in range(3)]
            first = [round(H.HEAT_BASE_COST * sum(E.CORNER_HEAT_COST[c][i] for c in CORNERS) / len(CORNERS) * w[i], 3) for i in range(3)]
            # turns from just-locked (load = cap) to release, at the track-average passive load
            unl = []
            for i in range(3):
                L, t = g.cap[i], 0
                while t < 50:
                    t += 1; L = max(0.0, L + pas[i] - g.rec[i])
                    if L < g.release * g.cap[i] - 1e-9: break
                unl.append(t)
            out[f"{car} {rules}"] = dict(cap=[round(x, 2) for x in g.cap], rec=[round(x, 2) for x in g.rec], release=g.release,
                                         avg_first_pick_cost=first, avg_passive=[round(x, 3) for x in pas],
                                         picks_to_fill_from_empty=[round(g.cap[i] / first[i], 2) for i in range(3)],
                                         turns_locked_from_full=unl, lock_on_passive=g.lock_on_passive)
    return out


def job_climb(a):
    rnd, j, q, which, k0, n = a; setv("live"); d = M.DISTRICTS[rnd]
    pts = E.MS_FLOOR_POINTS[d][j] if which == "floor" else M.max_build_points(rnd, j) if hasattr(M, "max_build_points") else None
    out = []
    for k in range(k0, k0 + n):
        cfg = M.crew_config(rnd, j, pts, seed=97_000_000 + k, player_read=q, player_timing=q, player_pacing=q)
        sim = SimulationRunner(cfg); m = sim.run().match
        f = feel(m); f["win"] = 1.0 if m.player_total_progress > m.opponent_total_progress else 0.0; out.append(f)
    tot_p = cfg.player_stats.pow + cfg.player_stats.han + cfg.player_stats.en; tot_o = cfg.opponent_stats.pow + cfg.opponent_stats.han + cfg.opponent_stats.en
    return (rnd, j, q, which, round(tot_p / tot_o, 3)), out


if __name__ == "__main__":
    part = sys.argv[1]
    if part == "mech":
        r = mech(); print(json.dumps(r, indent=1)); json.dump(r, open("exp_mech.json", "w"), indent=1)
    elif part in ("mx5", "levers"):
        vs = ["live"] if part == "mx5" else [sys.argv[2]]; names = ["MX-5 vs S2000"] if part == "mx5" else list(MATCH)
        J = [(nm, v, k0, 250) for nm in names for v in vs for k0 in range(0, 2000, 250)]
        with Pool(8) as p: R = p.map(job_match, J)
        res = {}
        for nm, v, rows in R: res.setdefault(nm, {}).setdefault(v, []).extend(rows)
        out = {nm: {v: summarize(rows) for v, rows in d.items()} for nm, d in res.items()}
        if part == "mx5":   # representative race: start-locked turns and limp closest to the medians, lowest seed on ties
            rows = res["MX-5 vs S2000"]["live"]; ms, ml = st.median(r["start_locked"] for r in rows), st.median(r["limp"] for r in rows)
            rep = min(rows, key=lambda r: (abs(r["start_locked"] - ms) + abs(r["limp"] - ml), abs(r["avg_mult"] - out["MX-5 vs S2000"]["live"]["avg_mult"]), r["seed"]))
            out["median_start_locked"] = ms; out["median_limp"] = ml; out["rep_seed"] = rep["seed"]
            m = SimulationRunner(cfg_match("mx5", "s2000", rep["seed"], 0.8)).run().match
            out["rep_race"] = [dict(turn=i + 1, corner=CORNERS[i], ai_line="".join(s.value[0] for s in t.opponent_line),
                                    played="".join(s.value[0] for s in t.player_stances), ai_played="".join(s.value[0] for s in t.opponent_stances),
                                    p_mults=[round(x, 2) for x in t.player_heat_mults], p_fill=[round(x, 2) for x in t.player_heat_fill],
                                    p_locked_end="".join("PHE"[k] if x else "-" for k, x in enumerate(t.player_locked)),
                                    ai_locked_end="".join("PHE"[k] if x else "-" for k, x in enumerate(t.opponent_locked)),
                                    ai_fill=[round(x, 2) for x in t.opponent_heat_fill], cum=[round(m.player_total_progress if i == 9 else 0, 2)])
                              for i, t in enumerate(m.turn_results)]
            out["rep_final"] = [round(m.player_total_progress, 3), round(m.opponent_total_progress, 3)]
        for nm in out:
            if isinstance(out[nm], dict) and nm in MATCH:
                for v, s in out[nm].items(): print(nm, v, {k: s[k] for k in s if k not in ("locked_at_turn_start_by_turn_PHE_pct", "ai")}, "AI", s["ai"])
        if part == "mx5":
            print(out["MX-5 vs S2000"]["live"]["locked_at_turn_start_by_turn_PHE_pct"]); print(out["rep_seed"], out["rep_final"])
            for r in out["rep_race"]: print(r)
        json.dump(out, open(f"exp_{part}{'_' + vs[0] if part == 'levers' else ''}.json", "w"), indent=1)
    elif part == "climb":
        J = [(2, j, q, "floor", k0, 250) for j in (0, 4, 6) for q in (0.8, 0.6) for k0 in range(0, 500, 250)]
        with Pool(8) as p: R = p.map(job_climb, J)
        res = {}
        for key, rows in R: res.setdefault(key, []).extend(rows)
        out = {}
        for (rnd, j, q, which, r), rows in res.items():
            s = agg(rows); s["win"] = round(100 * sum(x["win"] for x in rows) / len(rows), 1); s["r"] = r
            out[f"touge {M.RUNGS[j]} {'strong' if q == 0.8 else 'weak'} {which}"] = s; print(M.RUNGS[j], q, which, s)
        json.dump(out, open("exp_climb.json", "w"), indent=1)


# -- goals part: Touge cells at LIVE crew stats under a player-heat variant (the win shift a lever causes = the re-pin it would
# need, plus the boss feel). 3 boss styles x n seeds like scripts/mod_skill_climb.py. Usage: exp.py goals <variant>
def max_build():
    out, e = {}, E.MS_STOCK_POINTS
    for rnd, d in enumerate(M.DISTRICTS):
        fl = E.MS_FLOOR_POINTS[d]
        row = tuple(min(E.MS_ROUND_CAP_POINTS[rnd], e + (f - fl[0]) + E.MS_NM_XP_CAP * E.MS_WILD_XP[rnd]) for f in fl)
        out[d] = row; e = row[-1]
    return out


def job_goal(a):
    v, j, q, which, si, n = a; c = setv(v); d = "touge"; pts = E.MS_FLOOR_POINTS[d][j] if which == "floor" else max_build()[d][j]
    rows = []
    for k in range(n):
        cfg = M.crew_config(2, j, pts, seed=96_000_000 + si * 100_000 + k, player_read=q, player_timing=q,
                            player_pacing=c["pace"] if q == 0.8 else q, boss_style=E.BOSS_STYLES[si])
        m = SimulationRunner(cfg).run().match; f = feel(m)
        x, y = m.player_total_progress, m.opponent_total_progress; f["win"] = 1.0 if x > y else 0.5 if x == y else 0.0; rows.append(f)
    return (j, q, which), rows


if __name__ == "__main__" and sys.argv[1] == "goals":
    v = sys.argv[2]; n = 300
    J = [(v, j, q, w, si, n) for j, q, w in ((0, 0.8, "floor"), (5, 0.6, "max"), (6, 0.8, "floor"), (6, 0.6, "max"), (6, 0.8, "max"))
         for si in range(len(E.BOSS_STYLES))]
    with Pool(8) as p: R = p.map(job_goal, J)
    res = {}
    for key, rows in R: res.setdefault(key, []).extend(rows)
    out = {}
    for (j, q, w), rows in res.items():
        s = agg(rows); s["win"] = round(100 * sum(x["win"] for x in rows) / len(rows), 2)
        out[f"{M.RUNGS[j]} {'strong' if q == 0.8 else 'weak'} {w}"] = s
    print(v, {k: (s["win"], s["turns_starting_locked_pct"], s["limp_pct"], s["mean_lock_turns"], s["races_with_all_locked_pct"]) for k, s in out.items()}, flush=True)
    json.dump(dict(variant=v, n_per_cell=n * len(E.BOSS_STYLES), out=out), open(f"exp_goals_{v}.json", "w"), indent=1)
