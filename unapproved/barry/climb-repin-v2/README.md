# climb-repin-v2: crew stats re-pinned for per-phase smoothed QTE + 2-turn lock cap (Barry PROPOSAL, 2026-11-20, UNAPPROVED)

> **Austin, direct:** "Maximum turns a state is locked should be 2." / (7:01 AM) "Lock cap: gauge stays hot after unlocking,
> so the next hard push relocks it. Re-pin the climb around that." / per-phase option 2 direction approved, w = 0.35.
> sim/ is untouched. Engine = live sim + `per_phase.patch` (branch copy). Floors, XP and the cap are unchanged; only crew
> stat totals move.

## Rules modelled
- **Lock cap (player):** a player lock ends at the 2nd turn end after it starts; the load is unchanged. The lock covers the
  rest of the turn it started in plus the next turn, and since the gauge is still hot, the next push relocks it
  (`HeatGauges.lock_cap`, `lock_cap_keep_load`).
- **AI: no cap (recommended).** The AI is not exempt for being moot: its locks average 1.85 turns, run up to 5, and 1,979
  of them ran longer than 2 turns in 2,000 MX-5 vs S2000 races. But the AI has no pacing logic. With the cap, it re-enters
  a still-hot gauge and overruns, so capping it made the AI *weaker*: player win 78.45 → 87.4 % (MX-5 vs S2000). Its
  softer rules (release at 80 %, no passive locks) already keep its locks short. Revisit if the AI gets a pacing rule.
- **Model:** Street and Wangan per-phase smoothed QTE (phase score = 0.35·press + 0.65·mean of earlier presses; the AI the
  same) + cap. Touge per-turn + cap (canon), plus a Touge per-phase what-if.

## Re-pinned crew stat totals (old → new; old = live `MS_CREW_BUDGET`)
| Rung | Street | Wangan | Touge |
|---|---|---|---|
| kid1 | 293.98 → 297.77 (+1.3 %) | 318.65 → 327.74 (+2.9 %) | 354.33 → 377.17 (+6.4 %) |
| kid2 | 306.16 → 307.95 (+0.6 %) | 340.56 → 342.82 (+0.7 %) | 383.85 → 391.80 (+2.1 %) |
| mat1 | 309.14 → 315.54 (+2.1 %) | 348.93 → 354.79 (+1.7 %) | 393.80 → 406.26 (+3.2 %) |
| mat2 | 317.38 → 322.22 (+1.5 %) | 362.05 → 364.45 (+0.7 %) | 404.82 → 417.00 (+3.0 %) |
| oh1 | 325.10 → 329.04 (+1.2 %) | 372.82 → 373.84 (+0.3 %) | 415.79 → 427.00 (+2.7 %) |
| oh2 | 331.98 → 335.74 (+1.1 %) | 383.00 → 383.45 (+0.1 %) | 426.72 → 436.89 (+2.4 %) |
| boss | 332.58 → 337.96 (+1.6 %) | 390.35 → 395.68 (+1.4 %) | 437.06 → 450.07 (+3.0 %) |

## Climb (rungs n = 2,000, bosses n = 6,000; seeds as the live climb)
| | Street | Wangan | Touge | Touge per-phase (what-if, same stats) |
|---|---|---|---|---|
| Strong 80/80 at floor | 95.95 / 90.44 / 84.68 / 81.43 / 76.68 / 72.07 / **66.22** | 96.1 / 90.64 / 85.34 / 81.03 / 77.23 / 72.17 / **66.57** | 96.15 / 90.54 / 85.44 / 80.18 / 76.98 / 73.12 / **66.8** | 95.55 / 87.79 / 79.68 / 71.22 / 66.92 / 63.21 / **55.62** |
| Smallest step | 3.25 (mat1 → mat2) | 3.80 (mat2 → oh1) | 3.20 (mat2 → oh1) | 3.71 |
| Weak 60/60 at max | 86.09 / 81.28 / 87.34 / 81.03 / 72.02 / 64.21 / **25.87** | 92.44 / 86.94 / 92.94 / 90.84 / 89.54 / 75.98 / **19.45** | 92.39 / 88.24 / 94.64 / 92.79 / 90.89 / 79.08 / **21.0** | 85.44 / 79.48 / 87.49 / 84.48 / 82.18 / 66.22 / **10.63** |
| Boss weak at floor | 0.35 | 0.18 | 0.02 | 0.03 |
| Boss strong at max | **98.08** | **95.03** | **96.27** | 95.85 |

| Criterion | Street | Wangan | Touge | Touge PP |
|---|---|---|---|---|
| Boss 66-68 | pass | pass | pass | fail (55.6) |
| Ladder strictly falling ≥ 3.0 | pass | pass | pass | pass |
| G2a weak at max ≥ 30 (every rung) | **fail at boss (25.87)** | **fail at boss (19.45)** | **fail at boss (21.0)** | fail |
| G3a (drop ≥ 30) | pass | pass | pass | pass |
| G3b (gap ≥ +10) | pass (40.4) | pass (47.1) | pass (45.8) | pass |
| G4a (lowest ≥ 40) | pass | pass | pass | pass |
| G4b (≤ 10) | pass | pass | pass | pass |
| G5 strong at max ≤ 95 | **fail (98.08)** | **fail (95.03)** | **fail (96.27)** | fail (95.85) |

## The conflict (no criterion relaxed)
Boss budget scan (`boss_scan.json`, n = 6,000) shows that with stats as the only lever, the boss band, G2a and G5 can't
hold together in any district:
- **Street:** strong at floor 69.38 / 60.85 at 337.39 / 339.08, while strong at max is 98.37 / 97.65. G5 needs about 342.3,
  where strong at floor is about 46.
- **Wangan:** 395.68 gives 66.57 / 95.03; 395.80 gives 65.97 / 95.02. The band and G5 miss each other by a hair.
- **Touge:** G5 needs about 452.3, where strong at floor is about 59.
- **G2a fails at the band everywhere:** at 66-68 strong, weak at max is 19-26. G2a needs the gap (strong at floor − weak at
  max) to be ≤ about 37 pp; under the lock cap and per-phase QTE it is 40-47.

**Why:** the lock cap helps a pacing 80/80 player far more than a 60/60 one, and per-phase QTE (even smoothed) hurts the weak
reader most. So the reading gap widens, and the max build's lift (floor → max) grows to about 29-32 pp. Crew stats move all
the boss cells together, so they can't close either gap.

**Closest fit:** the table above keeps the 66-68 band, the ladder and G3a/G3b/G4a/G4b. It misses G5 by 0.03 (Wangan), 1.27
(Touge) and 3.08 (Street), and G2a at the boss by 4.1 / 10.6 / 9.0.

**Levers outside crew stats that would close it (not run):** for G5, a smaller non-mandatory XP cap or lower round mod
ceilings (the max build lift). For G2a, more help for weak readers in per-phase districts (a wider QTE zone or a smaller
smoothing w), or a softer boss heat rule.

## Files
`per_phase.patch` (branch-copy engine: per-phase, smoothing, lock cap, AI cap option, tonics option) · `repin.py` (search
+ verify) · `search.json`, `verify.json` (first pass) · `search2.json`, `verify2.json` (final ladder) · `boss_scan.json`,
`boss_fine.json` · `repin_final.json` (final stats + climb) · `car_matchup.py/.json` (MX-5 vs S2000, WRX vs MX-5).

## MX-5 (player) vs S2000 (AI), playtest track, 2,000 races (`car_matchup.json`)
The S2000 draft block equals the MX-5's (1350/750/900, `globals.gd:143`), so this is a mirror match at r = 1.

| | Win % | Turns starting locked | Limp clashes | Mean lock (turns) | Locked share of turns P / H / E |
|---|---|---|---|---|---|
| MX-5 vs S2000, live | 72.15 | 34.6 % | 2.7 % | 3.31 | 4.9 / 29.8 / 20.9 % |
| MX-5 vs S2000, lock cap | 78.45 | 20.4 % | 0.1 % | 1.0 (max 1) | 0.8 / 15.9 / 9.3 % |
| WRX vs MX-5, live | 81.25 | 47.6 % | 13.1 % | 3.80 | 30.5 / 44.8 / 25.6 % |
| WRX vs MX-5, lock cap | 93.25 | 31.1 % | 1.4 % | 1.0 (max 1) | 11.7 / 20.7 / 9.6 % |

**Why it felt worse than WRX vs MX-5:** fewer locks overall, but the wrong ones. The MX-5's big gauge is POW (45 %), the
stance Touge corners load least (cost 0.8-1.0). Its HAN (25 %) and EN (30 %) gauges, the ones the corners load hardest,
are locked 29.8 % and 20.9 % of turns, and a lock lasts 3.3 turns. In a mirror match, the AI has the same shape on the
softer AI rules and the player has no build edge. So it wins 9 pp less than the WRX (72.15 vs 81.25), whose big EN gauge
matches Touge's demand. The lock cap fixes most of the feel: limp 2.7 → 0.1 %, turns starting locked 34.6 → 20.4 %.
