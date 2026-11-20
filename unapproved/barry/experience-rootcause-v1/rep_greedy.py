"""Representative MX-5 vs S2000 race for a player who counter-picks without heat planning (sim player_pacing 0 = greedy every
turn, read/timing 0.8), live rules, playtest track. Picks the race closest to the medians of turns-starting-locked and limp
clashes over seeds 98,000,000-98,001,999 (lowest seed on ties). REPRESENTATIVE, not Austin's race (no state string exists)."""
import json, statistics as st
import exp as X
from velocity_shift.simulation import SimulationRunner
rows = []
for k in range(2000):
    m = SimulationRunner(X.cfg_match("mx5", "s2000", 98_000_000 + k, 0.0)).run().match; f = X.feel(m); f["seed"] = 98_000_000 + k
    f["win"] = m.player_total_progress > m.opponent_total_progress; rows.append(f)
ms, ml = st.median(r["start_locked"] for r in rows), st.median(r["limp"] for r in rows)
rep = min(rows, key=lambda r: (abs(r["start_locked"] - ms) + abs(r["limp"] - ml), r["seed"]))
m = SimulationRunner(X.cfg_match("mx5", "s2000", rep["seed"], 0.0)).run().match
T = []
for i, t in enumerate(m.turn_results):
    T.append(dict(turn=i + 1, corner=X.CORNERS[i], ai_line="".join(s.value[0] for s in t.opponent_line), played="".join(s.value[0] for s in t.player_stances),
                  p_mults=[round(x, 2) for x in t.player_heat_mults], p_limp=t.player_limp, p_fill_end=[round(x, 2) for x in t.player_heat_fill],
                  p_locked_end="".join("PHE"[k] if x else "-" for k, x in enumerate(t.player_locked)),
                  ai_played="".join(s.value[0] for s in t.opponent_stances), ai_mults=[round(x, 2) for x in t.opponent_heat_mults],
                  ai_locked_end="".join("PHE"[k] if x else "-" for k, x in enumerate(t.opponent_locked))))
out = dict(median_start_locked=ms, median_limp=ml, win_pct=round(100 * sum(r["win"] for r in rows) / 2000, 2), seed=rep["seed"],
           final=[round(m.player_total_progress, 3), round(m.opponent_total_progress, 3)], turns=T)
json.dump(out, open("rep_greedy.json", "w"), indent=1)
print({k: v for k, v in out.items() if k != "turns"})
for t in T: print(t)
