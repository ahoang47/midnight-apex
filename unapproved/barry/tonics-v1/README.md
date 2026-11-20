# tonics-v1: tonics as their own study (Barry DRAFT, 2026-11-20, UNAPPROVED)

> **Austin, direct, 7:08 AM:** "also sim the tonics as a separate thing." Tonics on top of each heat model, 0-3 per race,
> kid1 / oh2 / boss, strong and weak players. sim/ untouched (branch copy + `per_phase.patch`, `MatchConfig.tonics`).

**Definitions (mine; no tonic or heat-falloff spec exists in the repo or reached me):**
- **Tonic:** a consumable. At the start of a turn, if any player gauge is locked, one tonic cools the hottest locked gauge
  to 0 and unlocks it. Max 1 per turn; used automatically.
- **Heat models run:**
  - **live:** live locks with live crew stats, per-turn.
  - **lock cap:** the climb-repin-v2 proposal (2-turn cap with load kept; Street/Wangan per-phase smoothed w 0.35, Touge
    per-turn) with its re-pinned stats.
- **Falloff: not run**, because no falloff model was defined to me. Add it as a third column once it's specified.
- **Cells:** strong = 80/80 at the floor, weak = 60/60 at max build. Common seeds (97,000,000+), so the columns are paired.
  n = 1,500 for kid1/oh2 and 3,000 for the boss. `tonics.py` → `tonics.json`.

## Win % by tonics per race (0 / 1 / 2 / 3)
| Cell | Live: Street | Live: Wangan | Live: Touge | Lock cap: Street | Lock cap: Wangan | Lock cap: Touge |
|---|---|---|---|---|---|---|
| kid1 strong | 97.47 / 99.0 / 99.27 / 99.2 | 96.67 / 98.33 / 99.6 / 100 | 98.73 / 99.87 / 99.87 / 99.93 | 95.67 / 96.0 / 96.47 / 96.53 | 96.73 / 97.87 / 99.33 / 99.47 | 97.07 / 97.13 / 97.47 / 97.53 |
| kid1 weak | 93.47 / 93.93 / 94.4 / 93.6 | 92.93 / 95.47 / 98.87 / 99.53 | 99.33 / 99.2 / 99.07 / 98.87 | 86.27 / 85.6 / 84.6 / 84.0 | 91.8 / 93.33 / 94.8 / 95.4 | 92.6 / 92.6 / 92.47 / 92.4 |
| oh2 strong | 68.53 / 85.67 / 92.67 / 96.07 | 70.4 / 81.6 / 87.67 / 94.0 | 70.0 / 86.2 / 94.6 / 98.07 | 72.2 / 79.2 / 83.67 / 86.2 | 73.6 / 80.47 / 84.87 / 87.93 | 73.87 / 82.0 / 85.33 / 87.53 |
| oh2 weak | 72.13 / 76.07 / 82.07 / 86.8 | 67.0 / 77.53 / 86.27 / 91.2 | 75.93 / 83.93 / 91.13 / 92.93 | 61.27 / 61.93 / 63.2 / 65.07 | 75.47 / 82.13 / 84.67 / 86.27 | 79.67 / 81.73 / 82.27 / 84.33 |
| **boss strong** | 67.33 / 79.73 / 86.93 / 92.43 | 66.97 / 77.97 / 86.7 / 93.53 | 66.33 / 80.9 / 90.7 / 96.1 | 67.27 / 75.8 / 79.83 / 84.5 | 67.17 / 75.27 / 80.37 / 85.7 | 67.9 / 77.5 / 83.47 / 88.2 |
| **boss weak** | 32.7 / 38.3 / 44.93 / 51.83 | 33.87 / 44.2 / 55.5 / 63.5 | 40.3 / 48.77 / 60.13 / 68.77 | 26.67 / 29.73 / 32.07 / 35.87 | 17.6 / 22.43 / 26.03 / 29.47 | 22.9 / 27.1 / 28.77 / 33.2 |

Tonics used per race (boss, 3 allowed): 2.67-3.0, so nearly all get used. At kid1 only 0.7-1.5 get used (few locks).

## What a tonic is worth
- **Boss, 1st tonic:** strong +11.0 to +14.6 pp under live locks, +8.1 to +9.6 under the lock cap. Weak +5.6 to +10.3 live,
  +3.1 to +4.8 lock cap. Each extra tonic is worth a bit less: 2nd +4 to +11, 3rd +4 to +9.
- **oh2, 1st tonic:** strong +11 to +17 live, +7 to +8 lock cap.
- **kid1:** ≤ +2.6 in every model, because the rung is already near the ceiling.
- **Swing from 0 to 3 tonics at the boss:** strong +25 to +30 live (66-67 → 92-96), +17 to +20 lock cap. Weak +19 to +30
  live, +9 to +12 lock cap.
- **Buying power replaces reading under live locks:** a weak player with the max build and 3 tonics beats the strong
  player at the floor with none in Touge (68.77 vs 66.33) and nearly does in Wangan (63.5 vs 66.97). Under the lock cap it
  doesn't (≤ 35.9 vs ~67): the cap already removes most of what a tonic fixes, so tonics are worth about 40 % less.
- **Even 1 tonic breaks the 66-68 boss band** for a strong player (75-81). If tonics ship, the boss pin has to assume the
  allowed tonics are used.

## Suggested cap and price (judgment from these numbers; the price is not simmed)
- **Cap: 1 tonic per race**, and only together with the lock cap. That keeps a weak max-build player's boss gain to +3 to +5
  pp (still 22-30 %, so reading still decides it). A strong player gains about +8 to +10, so the boss stats would need about
  +0.5 % (boss scan slope ~8.5 pp per 0.5 %) to keep 66-68 with the tonic. Under live locks, cap 1 is still +11 to +15 for
  strong players: too strong.
- **Consider a weaker tonic:** cool to half load instead of 0. Not run yet; one cheap follow-up.
- **Price:** about the cost of one mod step, so a tonic competes with permanent upgrades instead of replacing them. R1 is
  **$500-$1,000** (Mk2 $500 to Mk3 $1,000 per slot). While the debt is open, a $550 non-mandatory win nets about $190, so
  one tonic is about 3-5 grinds. Scale with the round's purse in R2/R3. No discount stacking on tonics (Reiko's wholesale
  applies to mods only).

## Tonics on HEAT FALLOFF (Austin 7:04-7:08 AM falloff variant; appended 2026-11-20)
Falloff has no locks, so here a tonic cools the **hottest** gauge to 0 at turn start (max 1 per turn). Crew stats are the
falloff re-pins (`../climb-repin-v2/fo0.5_final.json`, `fo0.7_final.json`); the model and cells are as above
(`ONLY=fo0.5,fo0.7 OUT=tonics_falloff.json`, `tonics_falloff.json`).

| Cell (0 / 1 / 2 / 3 tonics) | Falloff 0.5: Street | Wangan | Touge | Falloff 0.7: Street | Wangan | Touge |
|---|---|---|---|---|---|---|
| kid1 strong | 95.47 / 96.87 / 97.93 / 98.87 | 96.8 / 98.0 / 98.2 / 98.47 | 96.53 / 97.4 / 97.8 / 98.33 | 95.93 / 96.67 / 97.6 / 98.53 | 96.0 / 97.27 / 97.47 / 97.87 | 96.67 / 97.53 / 97.53 / 98.0 |
| kid1 weak | 82.0 / 84.93 / 86.87 / 89.13 | 93.73 / 94.6 / 95.33 / 96.33 | 94.27 / 95.53 / 96.2 / 96.93 | 82.2 / 85.13 / 86.53 / 88.73 | 93.27 / 94.0 / 95.0 / 96.07 | 94.2 / 95.47 / 96.2 / 96.4 |
| oh2 strong | 71.07 / 75.6 / 78.73 / 83.13 | 70.8 / 75.47 / 77.87 / 80.4 | 75.53 / 82.67 / 86.6 / 89.2 | 71.8 / 75.8 / 78.13 / 81.73 | 71.07 / 75.53 / 77.33 / 80.27 | 76.6 / 82.67 / 86.0 / 87.27 |
| oh2 weak | 41.67 / 47.0 / 51.47 / 55.8 | 18.2 / 20.47 / 21.87 / 23.67 | 61.93 / 65.6 / 69.27 / 72.67 | 39.27 / 43.13 / 46.53 / 50.33 | 14.07 / 15.4 / 16.67 / 17.87 | 54.8 / 58.27 / 60.73 / 63.87 |
| boss strong | 66.1 / 70.9 / 74.5 / 77.47 | 66.53 / 70.73 / 74.03 / 76.17 | 68.43 / 76.93 / 82.07 / 84.07 | 67.53 / 71.0 / 73.97 / 76.5 | 65.93 / 70.1 / 72.97 / 75.13 | 67.7 / 76.1 / 80.77 / 82.0 |
| boss weak | 7.77 / 9.27 / 10.33 / 11.6 | 1.5 / 1.73 / 1.83 / 2.17 | 10.0 / 11.7 / 13.67 / 15.77 | 7.33 / 8.2 / 9.23 / 10.4 | 1.17 / 1.3 / 1.33 / 1.53 | 5.13 / 6.63 / 7.83 / 8.83 |

- **Worth:** under falloff a tonic is worth much less than under locks. At the boss, the 1st tonic is strong +3.5 to +8.5 pp
  (live locks +11 to +15, cap +8 to +10) and weak +0.1 to +1.7. Over 0 → 3 the swing is strong +9 to +16 and weak +0.4 to
  +5.8.
- **Reading still decides it:** tonics widen the gap. A weak max-build player with 3 tonics is at most 15.8 % at the boss,
  against about 67 for a strong player with none.
- **Suggested cap:** 1 per race. One tonic still lifts a strong boss win out of the 66-68 band (70-77), so the boss pin
  should assume it gets used (about +0.3-0.5 % boss stats). Up to 2 would be safe for reading skill but makes the band
  harder to pin. **Price:** as above, about one mod step ($500-$1,000 in R1).
