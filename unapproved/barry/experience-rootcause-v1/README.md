# experience-rootcause-v1: Austin's playtests vs the experience goals (Barry ANALYSIS, 2026-11-20, UNAPPROVED, nothing live)

> Austin (direct, 8:48 AM): "I want you to look at the experience goals. Then I want you to look at my gameplay and understand
> what my experience was. I then need you to root cause it, and determine what levers we can pull while keeping gameplay
> experience intact." Live sim only (sim/ at go-live 83b98d8, unchanged). No tonics. All numbers come from the runs in this folder.

## 1. The goals, as the experience they protect (design/07 top, E.MS_TARGETS)
- **G1, the story bites a good player:** a strong 80/80 player at the floor should feel the boss as a real fight (65-70 %, Austin 66-68) and lose a few story races per round (1.5-4), not cruise.
- **G2, grinding always pays:** a weak 60/60 player who maxes their build gets a fair shot everywhere (≥ 30 %) and clears a round within 60 attempts. Nobody is stuck.
- **G3, a climb you learn:** every rung is noticeably harder than the one before (≥ 3.0 pp per step, ≥ 30 pp kid1 → boss), and at the boss *reading the lines* is worth more than grinding (strong at floor beats weak at max by ≥ 10 pp).
- **G4, a challenge from the start, brutal at the top, no handouts:** the easiest cell is still a race (≥ 40 %), the boss crushes an unskilled, ungrinded player (≤ 10 %), and there is no underdog bonus.
- **G5, a ceiling:** even a maxed strong player can still lose the boss (≤ 95 %).
- **None of the goals asks for lock-outs.** Heat exists to make the player spread picks across stances. The goals are about win rates and skill paying off.

## 2. What Austin experienced
**(a) WRX (player) vs MX-5 (AI), TC4: his actual race** (`../cooldown-v1/replay_tc4.py`, bit-identical 18.019 vs 12.978):
| Turn | Corner | Start-of-turn locks | What he could do |
|---|---|---|---|
| 1 | HP | none | Auto-filled EHH. The 2nd HAN overran (×0.40) and locked HAN. |
| 2-3 | ES, HP | HAN | Only POW/EN. Touge lines ask for HAN, so he couldn't answer them. |
| 4-5 | DR, ES | HAN (+POW from t4) | t5: only EN, so EEE. HAN had now been locked 5 turns. |
| 6 | HP | none (HAN finally < 30 %) | EEE overran EN (repeat surcharge) and locked it. |
| 7 | N90 | EN | HPH: the 2nd HAN locked HAN again. |
| 8 | HP | HAN, EN | Only POW, so PPP overran and locked POW. **All three locked.** |
| 9-10 | DR, CH | all | No choices: limp ×0.40 on all six clashes. |
9 of 10 turns started with a lock, and 6 of 30 clashes were limp. Meanwhile the AI MX-5 locked HAN or EN almost every other turn but always unlocked the next turn. He won anyway.

**(b) MX-5 vs S2000, "the cooldown was even worse":** no state string exists in the repo, so these are **representative sims, not his race**. Live rules (player releases at 30 %, AI at 80 %, the AI's corner load never locks), 2,000 seeded races, playtest track. The S2000 block equals the MX-5's (1350/750/900).
- Planning sim player (pacing 0.8): win 72.15 %, 34.6 % of turns start locked, lock length 3.31 turns, 2.7 % limp, 12.9 % of races hit all-locked. HAN is locked at the start of 42 % of turn-6 starts, and EN at 38 % of turn-9/10 starts (`exp_mx5.json`).
- Counter-picking player with no heat planning (pacing 0, closest to a first playtest): win 65.8 %, **45.2 % of turns start locked, 6.9 % limp, 32.2 % of races hit all-locked**. The WRX under the same play hits all-locked in 98.6 % of races, as TC4 did (`exp_levers_greedy(pacing0).json`).
- Median counter-pick race (`rep_greedy.json`, seed 98,000,004, won 17.54-15.63):
  - t4: EN overran (×0.77) and locked. EN stays locked t4-t5, so EN isn't available in t5.
  - t5: POW was the safe pick. With 7.26 capacity it never locks, but it's the stance Touge corners pay least for.
  - t8: HAN locked through t10.
  - t10: EE overran (×0.40) and locked EN, so it ended with HAN and EN both locked.
- **Why it felt worse than the WRX:** the MX-5's spare capacity is POW, so when HAN or EN lock it is left with the weakest Touge answer. The WRX's spare is EN, which Touge pays for. Win 72 % vs 81 %.

**(c) "It would be even more frustrating as we go up":** he's right. Live climb, Touge, 500 races per cell (`exp_climb.json`):
| Cell | Race length | Turns starting locked | Limp clashes | Mean lock length | Races with all three locked |
|---|---|---|---|---|---|
| kid1 strong at floor | 10 | 29.1 % | 1.0 % | 3.23 | 3.8 % |
| oh1 strong at floor | 20 | 51.8 % | 12.4 % | 4.65 | 49.4 % |
| boss strong at floor | 30 | 57.5 % | 18.2 % | 5.44 | 67.0 % |
| boss weak at floor | 30 | 76.8 % | 31.0 % | 5.80 | 94.0 % |

## 3. Root causes → goals
| # | Mechanical cause (number) | Experience | Coded? | Intent? | Goal touched |
|---|---|---|---|---|---|
| 1 | **Slow release asymmetry:** player unlocks below 30 % of capacity, AI below 80 %. Locked from full at the track-average load: player 3-4 turns, AI 1 (`exp_mech.json`). | "Doesn't cool off". The AI visibly recovers next turn. | as coded (approved, resources-v4b) | **conflicts** (Austin) | none directly. Undercuts G3: a read you can't play is worthless. |
| 2 | **HAN is undersized for Touge:** the Touge tune is HAN 25 %, but Touge corners cost HAN most (ES 1.4, HP 1.2, CH 1.3). MX-5 HAN capacity 2.53 = 2.16 average picks from empty. One HAN pick per turn (1.17) plus passive (0.27) beats recovery (0.84), so HAN locks within about 4 turns. A 2nd HAN in a turn costs ×2 (repeat surcharge), so two HANs in one turn always lock. | The stance Touge lines ask for is the one you lose | as coded | conflicts with "learn the lines" | G3 (reading) |
| 3 | **Gauges carry across the whole race; length rises 10 → 20 → 30 turns;** capacity ∝ r, and r falls from 1.10 (kid1) to 1.02 (boss). Capacity is sized for "3 turns of average demand" whatever the race length. | Lock-outs and limp triple going up (table 2c) | as coded | conflicts (Austin) | G3c/G1a are partly met *through* lock-outs (see 4) |
| 4 | **Difficulty is carried by heat:** at live crew stats, removing most locks moves the boss strong-at-floor from 69 % to 81-100 % (§4). The boss reaches 66-68 % partly because the player limps. | Hard *and* frustrating | as coded | conflicts: G1 wants a hard race, not a locked one | G1a, G3c, G4b depend on it today |
| 5 | **Picks have no warning:** auto-fill (TC4 t1 EHH) and repeat picks (EEE, PPP) overran with no warning shown. | Locks feel random | Godot UI | conflicts | none (UI) |
| 6 | **Car drafts:** the WRX is Wangan-shaped on a Touge track. MX-5 and S2000 are mirrors, so the AI also suffers, but recovers in 1 turn. | Car-dependent harshness | unapproved blocks | as intended (specialization) | none (playtest only), but the Touge tune is also the live climb's player shape |
| 7 | **The "kid" opponent isn't a kid for heat:** the playtest is r = 1.00 (3000 vs 3000). The climb's kid1 floor is r = 1.10, with strong win 99 %. | The playtest is harsher than kid1, closer to oh1/boss heat | as coded | n/a | none |
| 8 | Passive load can lock the player | small effect (removing it: 34.6 → 34.0 % turns locked) | as coded | neutral | none |

**Goals vs numbers:** the experience doesn't conflict with any goal. It conflicts with the *numbers and rules* that currently deliver G1a/G3c. The goals are reachable with less heat, but every lock-reducing lever needs a crew re-pin, and the past re-pins (lock cap, falloff) broke G2a/G5. That is the real constraint.

## 4. Levers (measured)
Playtest matchups: 2,000 races, live rules unless noted (`exp_levers_*.json`); win % / turns starting locked / limp / mean lock length / races all-locked.
Climb: Touge at **live crew stats** (no re-pin), 900 races per cell, 3 boss styles (`exp_goals_*.json`). Boss strong-at-floor / boss weak-at-max / boss strong-at-max win %, and boss strong-at-floor limp / lock length / all-locked.

| Lever | MX-5 vs S2000 | WRX vs MX-5 | Touge boss wins (sf / wm / sm) | Boss feel (limp / lock length / all-locked) | Goals risk |
|---|---|---|---|---|---|
| live | 72.15 / 34.6 / 2.7 / 3.31 / 12.9 | 81.25 / 47.6 / 13.1 / 3.80 / 52.9 | 69.22 / 41.22 / 95.0 | 17.2 / 5.20 / 67.7 | baseline (all pass) |
| **UI telegraph** (proxy: perfect pacing 1.0) | 77.1 / 32.7 / 1.7 / 3.37 / 7.7 | 91.15 / 31.4 / 5.3 / 3.42 / 27.4 | 82.44 / 41.22 / 97.22 | 9.7 / 4.88 / 41.4 | none to the rules. A skilled player wins more (skill reward, G3). Goal cells stay pinned at pacing 0.8. |
| **Lap reset** (player gauges reset between 10-corner laps) | unchanged (10-turn race) | unchanged | 94.56 / 68.0 / 99.56 | 4.2 / 3.41 / 35.1 | kid feel untouched (kid1 29.5 % locked). Needs a re-pin of the 20/30-turn rungs. |
| **Player release 0.3 → 0.5** | 76.5 / 31.8 / 1.0 / 2.67 / 5.6 | 87.5 / 43.4 / 6.3 / 2.62 / 31.3 | 81.11 / 55.67 / 97.0 | 8.2 / 3.23 / 38.7 | needs a re-pin (+11.9 pp at the boss; my cooldown-v1 "+0.7-1 % stats" guess was too low) |
| release 0.6 | 77.35 / 29.5 / 0.5 / 2.16 / 3.1 | 88.0 / 39.4 / 5.2 / 2.23 / 20.8 | 88.67 / 67.33 / 98.44 | 4.3 / 2.51 / 21.3 | bigger re-pin |
| lap reset + release 0.5 | 76.5 (release only) | 87.5 | 98.22 / 82.22 / 99.89 | 1.3 / 2.50 / 12.8 | big re-pin; heat nearly gone at the boss |
| recovery ×1.33 | 81.7 / 25.1 / 0.0 / 2.39 / 0.0 | 92.45 / 29.0 / 1.6 / 2.34 / 7.7 | 99.78 / 90.67 / 100 | 0.0 / 2.65 / 0.1 | heat stops mattering; huge re-pin; G5 likely |
| capacity 4 + recovery ×1.33 | 85.8 / 21.2 / 0.0 / 2.81 / 0.0 | 92.15 / 28.9 / 0.5 / 2.87 / 5.0 | 99.78 / 91.56 / 100 | 0.0 / 2.89 / 0.0 | same |
| capacity 4 turns | 79.8 / 29.7 / 1.0 / 3.88 / 5.6 | 88.75 / 40.3 / 6.6 / 4.14 / 26.3 | (not run) | | locks get *longer* |
| no passive lock | 72.05 / 34.0 / 2.6 / 3.40 / 12.7 | 82.15 / 46.9 / 12.2 / 3.92 / 44.5 | (not run) | | barely helps |
| share exp 1.0 (both sides) | 76.25 / 32.1 / 4.2 / 3.21 / 16.8 | 71.0 / 38.3 / 9.6 / 3.66 / 34.3 | (not run) | | nerfs specialization; MX-5 limp worse |
| lock cap 2, hot gauge (re-pinned, `../climb-repin-v2`) | 78.45, degraded 11.0 % | 93.25, 19.9 % | re-pinned boss 66-67 | Touge boss degraded 18.5 % | **fails G2a (19-26), G5, G3a** |
| falloff 0.5 + AI pacing (re-pinned) | 52.85, 17.9 % | 67.1, 27.8 % | re-pinned boss 66-67 | Touge boss degraded 25.8 % | **fails G2a (0.6-13), G3a**; reading harder |
| car drafts (`../cooldown-v1`, player split vs the MX-5) | even 33/33/33: 74.5 / 26.1 / 2.1 / 2.49 | WRX shape 81.25 / 47.6 / 13.1 | n/a | | playtest only, unless the Touge tune changes |

Counter-picking (pacing 0) with the same levers: MX-5 vs S2000 limp live 6.9 → release 0.5 3.8 → cap 4 + recovery ×1.33 0.0, all-locked 32.2 → 14.2 → 0.0. WRX limp 39.4 → 36.2 → 2.1.

## 5. Ranking and recommendation (keeps the goals)
1. **UI telegraph (Gordon): no numbers change.** Show "unlocks in N turns" and warn when a pick will overrun or lock, including auto-fill. A careful player's limp halves (MX-5 2.7 → 1.7 %, WRX 13.1 → 5.3 %, boss 17.2 → 9.7 %). Risk: a better-informed player wins more, so confirm in playtest before re-pinning.
2. **Lap reset between laps (player only), then re-pin Touge/Street/Wangan oh/boss.** It goes straight at "worse going up": boss limp 17.2 → 4.2 %, all-locked 68 → 35 %, with the kid and the playtest untouched. It's a clean rule for Godot (zero the gauges at the lap line).
3. **Player release 0.3 → 0.5 + re-pin.** It fixes "doesn't cool off" at every rung (lock length −0.6 to −2 turns), but moves the boss +12 pp, so the re-pin is large.
4. Touge car/tune: not a climb fix unless DISTRICT_TUNE changes. Use even-ish playtest blocks for Touge.
5. Not recommended: recovery or capacity boosts (heat stops mattering), share exp (wrong target), no passive lock (no effect). Lock cap and falloff + pacing fail G2a after their re-pins.

**Next step (needs Austin's go):** re-pin levers 2 and 3 with the climb harness and check G2a/G5. Those are the goals the past re-pins broke. Until then, 2 and 3 are "feel fixed, goals unverified".
