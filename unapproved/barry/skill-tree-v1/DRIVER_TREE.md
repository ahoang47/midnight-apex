# Driver tree: EXECUTION (Barry DRAFT 2026-11-18)

The driver never adds raw stats (those are the car's). Every node bends a lever that already exists in
`sim/velocity_shift/equations.py`, or the spirit meter (spirit-meter-v1). The node values are all [PH]. Bonuses are additive offsets
(design/05 §1).
- **Points:** 1 per driver level [PH], giving 12 / 29 / 46 by the R1 / R2 / R3 caps and 115 at L115 [sim levels].
- **Costs:** tier 1 nodes 1 point, tier 2 2, tier 3 3, capstones 5 [PH]. A full tree costs about 100, so a player at L115 can own most
  of it but not all by R3.
- **Gates:** a tier unlocks at driver level 0 / 12 / 29 / 46 (the round caps) [PH], so the tree grows with the story.

## A. Timing (QTE)
Levers [sim]:
- `qte_zone_width(r, window_mod)`: the window mod multiplies the width.
- QTE phases entry / apex / exit, averaged.
- An unplayed phase scores PHASE_QTE_UNPLAYED = 0.

| Tier | Node | Effect [PH] |
|---|---|---|
| 1 | Steady hands | window_mod +0.05 |
| 2 | Apex focus | apex phase window_mod +0.10 (needs per-phase width; open Q) |
| 2 | Recovery tap | an unplayed phase scores 0.2 instead of 0 |
| 3 | In the zone | window_mod +0.05 more |
| Cap | Clean line | the first QTE of each lap counts as the best phase score of that turn |

Note: spirit-meter-v1 found a QTE-width buff weak at 80/80 (timing is already near the top). These nodes help weak timers most,
which is the right audience.

## B. Reading
Levers [sim]:
- q_read: the sim player reads the boss's line with that probability.
- Bosses follow their line with LINE_ADHERENCE 0.65, else bluff.
- The scouted guess is the most likely line.
- A misread clash ties with probability q_read.

| Tier | Node | Effect [PH] |
|---|---|---|
| 1 | Scout | on the first corner of each lap, show which of the 3 lines is most likely (= the sim's guess) |
| 2 | Tell | once per lap, show the boss's Entry stance for this corner |
| 2 | Bluff sense | after a boss deviation, show "deviated" (sees the 1 − 0.65 case) |
| 3 | Second read | on a misread, the tie chance +0.1 |
| Cap | Rival file | a boss beaten before shows its style (balanced / hot_early / conserver [sim: BOSS_STYLES]) at the start |

## C. Heat craft
Levers [sim]:
- HEAT_RELEASE 0.3 (a locked gauge unlocks below 0.3 × capacity).
- OVERRUN_SLOPE 2.0 and OVERRUN_FLOOR 0.4.
- LIMP_MULT 0.4 (all three locked).

| Tier | Node | Effect [PH] |
|---|---|---|
| 1 | Cool down | HEAT_RELEASE +0.05 (unlock sooner) |
| 2 | Ride the edge | OVERRUN_FLOOR +0.05 |
| 2 | Limp home | LIMP_MULT +0.1 |
| 3 | Feather | OVERRUN_SLOPE −0.25 |
| Cap | Vent | once per race, empty one gauge (a 1-gauge version of the spirit "free heat" buff, which measured strong) |

## D. Pacing
Levers [sim]:
- PACE_LOOKAHEAD 3: corners the pacing rule looks ahead.
- PACE_RES_T 0.7: the soft ceiling.
- The sim player paces on a share of turns (player_pacing).

| Tier | Node | Effect [PH] |
|---|---|---|
| 1 | Track notes | the HUD shows the next 3 corners' expected load per gauge (the sim's exp_load) |
| 2 | Long view | notes extend to 5 corners |
| 3 | Rhythm | +5 % recovery on the gauge least used last turn |
| Cap | Race brain | a soft-ceiling marker (0.7 × capacity) on each gauge |

The pacing nodes are mostly information. Their win % value depends on the real player and needs a playtest, not the sim.

## E. Spirit (the meter)
Recommended baseline (spirit-meter-v1, A) [sim-measured, values PH]:
- Meter 100, fill 6 per won clash × match, tie 0.5, loss 0.25.
- Buff +25 % payoff × 3 turns, 1 activation per race.

| Tier | Node | Effect [PH] |
|---|---|---|
| 1 | Fired up | fill +1 per won clash |
| 2 | Hold it | buff +1 turn (stage-2 story walk, curve player: pay +20 % for 3 → 5 turns measured +4.8 → +7.4 pp) |
| 2 | Kindling | loss fill 0.25 → 0.4 (helps weak readers activate in 10-turn races) |
| 3 | Second wind | a 2nd activation in 20-30-turn races (measured about +1.2 pp on the curve story walk, B vs A) |
| Cap | Overdrive | the buff type follows the car (CAR_TREE §1). Mastered techniques from retired cars add extra buff options |

Measured guidance [sim, spirit-meter-v1]:
- One activation is about 5-6 pp in the mid range, 1 pp at 80/80 on capped bosses.
- Free heat widens the 60/60-80/80 gap (+10.3 pp story), so keep full free heat out of the driver tree.

## Mastery techniques (learned from retired cars; README §5)
| From | Technique | Effect [PH] |
|---|---|---|
| Starter hatch | Forgiving | HEAT_RELEASE +0.05 on every car |
| Street tuner | Overboost | POW overrun slope −0.25 on every car |
| AWD GT | Long legs | EN repeat surcharge −0.1 on every car |
| Light FR | Light on its feet | ES/CH HAN cost −0.05 on every car |

These are small on purpose (about a quarter of the car's own signature), so the next car still feels new.
