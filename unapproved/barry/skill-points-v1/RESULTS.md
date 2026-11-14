# skill-points-v1: whole, player-distributable skill points per level (draft, Barry, 2026-11-14)

Austin's ask (2026-11-14): leveling should grant whole skill points, more than one per level, that the player spreads over the stats, so builds are a real choice.
Also: does the sim assume free retuning (for example 33/33/33 → 0/0/100)?
Draft only. Nothing in `sim/` changed and nothing was committed. Base: proto-build `65a070c`.

## 1. How the live sim turns levels into stats today

- **XP to levels.** `xp_to_next(L) = 100 × 1.08^L` (`equations.py`). Story and grind wins pay XP. XP past a round cap is lost, and the walk resets leftover XP to 0 at each round.
- **Levels to skill points (SP).** `sp_at_level(L) = 240 × 1.10^(L/12)` is a smooth curve, not whole numbers.
  - The gain per level is 1.91 SP at L0, 2.76 at L46 and 4.73 at L114.
  - SP at the caps L12 / 29 / 46 / 64 / 79 / 94 / 115 is 264 / 302.16 / 345.85 / 399.0 / 449.48 / 506.35 / 598.26.
- **SP to stat total.** `stats_at_level(L) = SP / SP_CAP_FRACTION (0.80)`, so SP is 80% of the stat total P.
  - The sim never says what the other 20% is (stock car? base stats?). It is only a scale factor. Flagged.
- **Stat total to combat.** `progression.combat_power(L, rnd) = min(C_ROUND[rnd], MOD_CAP_FRACTION 1.07 × P)`.
  - Mods are assumed to fill up to 1.07 × P, capped at the round ceiling `C_ROUND` (353.1 / 404.26 / 462.84). R1 at L0 is the stock car (1.00 × P).
  - Finale caps L64 / 79 / 94 / 115 come from `finale_caps()`: the finale ceilings `B × FINALE_TARGET_R` turned back into levels with `level_for_sp`. T4 mods fill the gap above 1.07 × P in the finale.
- **Combat to win %.** `r = combat power ÷ opponent budget B`, and win % is read from `config/winrate_g2_live_tracks_v1.json` (linear in r).
- **Profiles are skill, not stats.** 60/60, 60/80, 80/60 and 80/80 are (read, timing, pacing) skill. Every profile has the same stat total at the same level.
- **Aero.** At most one equipped. Its free pool (assigned at the wind tunnel) is at most 10% of the part's own stat total (`AERO_FREE_POOL_MAX_FRACTION`) and counts inside the 1.07 cap.
- **Stat split.** Nothing in progression tracks POW / HAN / EN per level; the walk only uses the total.

## 2. What the live sim assumes about stat allocation (Austin's respec question)

- **One fixed tune per district.** Every win % in the live table was run with one fixed POW / HAN / EN tune per district, the same for every profile, level, track, race length, boss and finale race.
  - Street 50/25/25, Wangan 25/25/50, Touge 45/25/30 (POW/HAN/EN).
  - Sources: `winrate_g2_live_tracks_v1.json` key `tunes`, `unapproved/barry/econ-v1-live-tracks/run_sweep.py` `TUNES`.
  - The tunes came from `run_tune_screen.py`, which picked the best split per district (60/60 at r 1.07) from a grid with each share at 25-50%.
- **So the sim assumes a free respec whenever the district changes.** That is R1 → R2 → R3, and in the training arc Touge → Wangan → Street → Touge.
  - Within a district the build is fixed and is not re-optimised per track or per race.
- **All-in builds.**
  - `equations.py` lines 296-297 define `BUILD_STAT_MIN_SHARE 0.25` / `BUILD_STAT_MAX_SHARE 0.50` ("each of POW/HAN/EN is 25-50% of the total"). Nothing in `sim/` enforces it; it is only defined.
  - The engine (`CombatantStats`) accepts any split. An exact 0 in a stat crashes the engine: `heat.py:182` `overrun_if` divides by that stat's heat capacity (ZeroDivisionError). So a literal 0/0/100 can't run. I tested 98/1/1 as "all-in".
  - All the tables stayed inside 25-50%, so no all-in build was ever simulated before this study.

### All-in and skewed builds on the live engine (`builds.py`, `builds_edge.py`, `builds_fixed.py`)

Setup: the district's boss r (Street 1.044, Wangan 1.055, Touge 1.071), all 5 tracks, 3 boss styles, N = 200 per cell.
Each cell reads: Street / Wangan / Touge win % for 30-turn races on the district average, then the hardest track in brackets.

| Build (POW/HAN/EN) | 80/80 | 60/60 |
|---|---|---|
| live district tune | 96.0 (94.2) / 95.2 (89.0) / 94.9 (94.3) | 43.9 (33.5) / 53.0 (37.3) / 41.4 (30.2) |
| even 33/33/33 | 93.2 (93.0) / 88.3 (89.7) / 89.0 (81.0) | 31.2 (28.5) / 38.7 (36.0) / 31.6 (16.3) |
| 60/20/20 POW | 90.1 (84.5) / 16.7 (7.0) / 74.7 (65.2) | 46.6 (19.2) / 1.1 (0.3) / 35.6 (17.7) |
| 70/15/15 POW | 77.8 (47.5) / 5.8 (1.8) / 46.7 (33.0) | 60.4 (3.5) / 0.6 (0.2) / 26.2 (3.0) |
| 80/10/10 POW | 88.1 (94.2) / – / 66.7 (75.2) | 62.2 (11.0) / – / 28.3 (4.5) |
| 90/5/5 POW | 100.0 (100.0) / – / 93.7 (100.0) | 81.9 (99.8) / – / 70.6 (100.0) |
| all-in 98/1/1 POW | 100.0 (100.0) / 15.4 (11.3) / 100.0 (100.0) | 95.4 (100.0) / 3.0 (0.2) / 82.7 (100.0) |
| all-in 1/1/98 EN ("0/0/100") | 5.2 (0.5) / 100.0 (100.0) / 99.7 (100.0) | 0.1 (0.0) / 100.0 (100.0) / 93.5 (94.2) |
| all-in 1/98/1 HAN | 3.0 (10.3) / 100.0 (100.0) / 11.6 (1.7) | 0.0 (0.0) / 99.9 (100.0) / 2.0 (0.0) |
| Wangan EN 80% / 90% / 95% | – / 93.0 (68.3) / 98.4 (92.2) / 100.0 (100.0) | – / 77.4 (23.3) / 88.8 (48.7) / 99.3 (97.8) |

The full 10/20/30-turn grid is in `builds.txt`.

**What the numbers show:**
- Win % is not monotonic. Skews of 60-70% lose badly. From about 80-90% in the matching stat the engine breaks: the right all-in build wins about 100% even for 60/60 (Austin's 0/0/100 = all EN wins Wangan and Touge outright).
- With free respec and no cap, a 60/60 player would go all-POW on Street and Touge and all-EN on Wangan, and win nearly everything. Every grind count and boss band would stop meaning anything.
- This is an engine exploit (likely in heat capacity or share payoff at extreme shares). It needs a hard per-stat cap; nerfing the boss won't fix it.
- Inside the 25-50% band, the live district tunes are the best builds tested.
- **No respec at all is too punishing.** Carrying the Touge tune into Wangan gives 80/80 68.4 (68.8) and 60/60 12.0 (12.2). Carrying the Street tune into Wangan gives 80/80 58.0 (55.8).
- Street and Touge both favour POW, but Wangan wants EN, so a locked build breaks the R2 boss band.

### Proposed allocation rules

1. **Hard per-stat floor and cap, enforced always:** each of POW / HAN / EN stays at 25-50% of the car's total, including mods and the aero free pool.
   - With whole points: each stat ≥ ceil(0.25 × total) and ≤ floor(0.50 × total).
   - This blocks every degenerate build above (all-in and 60%+) and keeps the balance tables valid.
   - It needs a sim check, because today it is only a constant. Aero has to respect it after its free pool is placed.
2. **Points lock when spent, plus a free retune at the garage when the district changes.**
   - That is between rounds, and before each arc step: P1 (Touge), M11 (Wangan), M21 (Street), M31 (Touge).
   - This is exactly what the balance already assumes, so no number moves.
   - Within a district a retune is locked, or costs a fee (amount TBD by Desmond; not simulated).
3. **Alternatives, not recommended:**
   - Paid respec only: a fee adds a money sink the economy hasn't been tested against.
   - No respec: it needs the bosses re-tuned for one fixed build. R2 Wangan fails by about 25-40 points as shown.

## 3. Whole-number schemes

`grant[L]` is the number of whole points granted on reaching level L. SP_int(L) = 240 + the sum of grants up to L (`schemes.py`, `schemes.txt`).

| Scheme | Points per level | SP at caps L12/29/46/64/79/94/115 | Worst error at a cap | Worst error at any level |
|---|---|---|---|---|
| live | 1.91-4.73 (continuous) | 264 / 302.16 / 345.85 / 399.0 / 449.48 / 506.35 / 598.26 | – | – |
| **S1 curve** (round the live curve) | 2-5 (34 levels at 2, 42 at 3, 31 at 4, 8 at 5) | 264 / 302 / 346 / 399 / 449 / 506 / 598 | −0.107% (L79) | 0.48 SP |
| **S2 band + milestone** (flat per band, remainder at the cap) | 2 / 2 / 2 / 2 / 3 / 3 / 4 per band, cap bonus 0 / 4 / 10 / 17 / 5 / 12 / 8 | same as S1 | −0.107% | 15.8 SP (before L64) |
| **S3 ×10** (S1 at 10× resolution; 1 point = 0.1 SP) | 19-48 | 264 / 302.2 / 345.8 / 399.0 / 449.5 / 506.4 / 598.3 | +0.012% | 0.05 SP |
| rejected: flat 2→3→4→5 steps at L34/75/111 | 2-5 | 264 / 298 / 345 / 399 / 449 / 509 / 598 | −1.38% (L29) | 5.9 SP |

The ×10 points are meant as a display scale. Under S3 the stat total P = SP/0.8 stays exactly as live.
Other ways to reach the same result: show points as stat points ×10, or change `SP_CAP_FRACTION`. Either is a presentation choice to make.

## 4. Balance with each scheme

Setup: the live progression walk with SP(L) swapped in memory for integer levels, plus the draft arc walker on the live table (`balance.py`, `balance.json`, `balance.txt`).
80/80 is story-only. Arc entry uses the live end-of-R3 level and leftover XP.

| | live | S1 curve | S2 band | S3 ×10 |
|---|---|---|---|---|
| 80/80 story boss R1/R2/R3 (hardest) | 53.0 / 57.7 / 55.7 | 54.6 / 57.2 / 54.2 | 54.6 / 47.1 / 31.7 | 52.9 / 57.7 / 55.8 |
| 80/80 lowest story race R1/R2/R3 | 53.0 / 54.1 / 50.4 | 54.6 / 55.5 / **49.5** | 54.6 / 47.1 / 29.1 | 52.9 / 54.2 / 50.5 |
| Mixed grind (wall + to-cap) | 3+10 / 3+10 / 4+8 | 3+10 / **5+9** / 4+8 | 3+10 / 5+9 / 1+11 | 3+10 / 3+10 / 4+8 |
| 60/60 grind | 13 / 15 / 18 | 13 / 16 / 18 | 13 / 19 / 22 | 13 / 15 / 18 |
| At-cap boss 60/60 / 80/80, R1 / R2 / R3 | 31.6/94.9, 39.3/90.6, 30.7/93.0 | 31.6/94.9, 38.6/90.3, 31.5/93.4 | as S1 | 31.6/94.9, 39.4/90.6, 30.2/92.9 |
| 80/80 finale F1-F4 (hardest) | 81.7 / 82.7 / 79.3 / 81.7 | 81.9 / 82.8 / 78.3 / 81.6 | 40.3 / 78.2 / 59.9 / 71.2 | 81.7 / 82.7 / 79.3 / 81.7 |
| 60/60 finale F1-F4 | 34.7 / 41.7 / 31.6 / 34.7 | same | same | same |
| Arc grind per step 60/80, 80/60, 60/60 | 7/6/6/7, 6/6/6/7, 11/7/7/9 | 7/6/6/7, 6/6/6/7, **9**/7/7/9 | 13/6/6/7, 15/6/6/7, 19/9/12/11 | same as live |
| 80/80 lowest arc race | 56.0 (P3) | 57.2 (P3) | 34.1 (P3) | 55.9 (P3) |
| Arc / finale checks failed | none | none | 4 | none |
| End cash 60/80, 80/60, 60/60, 80/80 | $77,790 / $77,047.50 / $91,732.50 / $31,075 | $78,422.50 / $77,680 / $90,880 / $31,075 | – | same as live |

- **S3 ×10:** every number is within 0.5 points of live and every grind count is identical. Recommended.
- **S1 curve (2-5 points per level):** within 1.6 points of live, but it breaks two things:
  - R3 oh1 for 80/80 drops to 49.5, under the 50% story floor.
  - The R2 mixed wall goes from 3 to 5 grinds.
  - It's also 1 point outside the ~1 point target on R1 (54.6 vs 53.0), R3 (54.2 vs 55.7) and F3 (78.3 vs 79.3).
  - These come from rounding at single levels, because one level is worth about 10 points near a boss. A one-level tweak at the affected levels (L20, L38) might fix it but wasn't tested.
- **S2 band + milestone:** rejected. Back-loading the remainder at each cap leaves mid-band levels up to 15.8 SP short. 80/80 falls to 31.7% at the R3 boss and 40.3% at F1, and mixed players grind 13-15 before F1.

## 5. Open question, no change made

Should leftover XP carry between rounds?
- The live walk resets it to 0 (`progression.run`: `L, bag = E.CAP_LEVEL[rnd - 1], 0.0`), and it also starts each round at the previous round's cap.
- Today's carry-over check: with true carry-over a story-only 80/80 player still ends R2 at L25 and R3 at L43, because story XP is sized from the actual entry level. But four early races drop below 50%: R2 mat2 49.0, R2 oh1 45.0, R3 kid1 43.4 and R3 mat2 39.5 on the hardest Touge track.
- Mixed and 60/60 players are unaffected because they grind to each cap.

## Assumptions and limits
- Skill points are counted in today's SP units. The 20% gap between SP and the stat total (P = SP/0.8) isn't defined in the sim.
- Under every scheme the whole stat total feeds combat exactly as live. The split is assumed to be the district tune via free respec; the walk does not model a per-level split.
- The build tests ran at one r per district with N = 200 per cell (about ±1.5 points of noise per cell). The tune row reproduces the live table within that noise (for example Street 80/80 hardest 94.2 vs 94.9 in the table).
- The arc and finale come from the draft econ-v1 arc walker run on the live table and constants; live `progression.py` has no arc walk. T4 slot sizing is unchanged.
- Integer SP replaces SP(L) only at whole levels. Level caps derived from SP (`finale_caps`) use the continuous inverse as live.
