# climb-repin-v2: crew stats re-pinned for per-phase smoothed QTE + 2-turn lock cap (Barry PROPOSAL, 2026-11-20, UNAPPROVED)

> **2026-11-20 AI PACING variant (Austin direct, 8:11 AM: "Let's ignore tonics right now. Test falloff with AI pacing.").**
> Proposal only; sim/ untouched (`per_phase.patch`: `MatchConfig.ai_pace`, `heat.ai_paced_stance`). No tonics anywhere.
>
> **Rule (1 param, x):** before each clash the AI checks its line's stance. It keeps it unless the push would leave that gauge
> above x·capacity (falloff) or would lock it (lock cap: x = 1.0). Then it plays the selectable stance that doesn't trigger, with
> the best output multiplier; ties go to the lowest fill after the push. x = the AI curve start (t + 0.2: 0.7 / 0.9), so falloff
> adds no new number. Deterministic (no RNG), about 6 lines for Godot to mirror (`boss_stance` + `ai_paced_stance`).
> **Interaction with the AI's softer rules:** it sits on top of release 80 % and no passive lock. Those still decide how fast its
> gauges cool. Pacing only changes which stance it plays when hot, so it now leaves its planned line in 24-41 % of clashes at the
> boss (8-40 % at oh1/oh2). Without pacing it was 35-51 % under the lock cap (forced by locks) and 0 % under falloff. **That makes
> the line harder to read.** Same model and cells as before: Street/Wangan per-phase w 0.35, Touge per-turn; rungs n = 2,000,
> bosses n = 6,000, seeded. Files: `pace_*_search/verify/final.json`, `pace_boss_fix.py/.json`, `pace_final.py`, `pace_criteria.py/.json`,
> `pace_feel.json` (paced), `pace_feel_nopace.json` (same metrics, no pacing), `car_matchup.json` (+pace variants), `run_pace.sh`.
>
> **Boss crew stats (live → no pacing → with pacing):**
>
> | Model | Street | Wangan | Touge |
> |---|---|---|---|
> | lock cap | 332.58 → 337.96 → 337.13 | 390.35 → 395.68 → 396.30 | 437.06 → 450.07 → 450.21 |
> | falloff t 0.5 | 332.58 → 355.06 → 326.80 | 390.35 → 424.96 → 391.42 | 437.06 → 470.01 → 441.70 |
> | falloff t 0.7 | 332.58 → 356.35 → 330.60 | 390.35 → 428.32 → 392.64 | 437.06 → 475.13 → 446.45 |
>
> With pacing, falloff stats fall back to about live (−8 to −9 % from the no-pacing falloff re-pin). Lock-cap stats barely move.
> Full ladders are in `pace_*_final.json`.
>
> **Criteria with pacing (Street / Wangan / Touge):**
>
> | | lock cap + pace | falloff 0.5 + pace | falloff 0.7 + pace |
> |---|---|---|---|
> | Strong boss at floor (66-68) | 68.0 / 67.75 / 67.35 pass | 67.12 / 66.37 / 67.22 pass | **65.83** / 66.93 / 67.12 (Street fails) |
> | Smallest step (≥ 3.0) | 3.25 / 4.0 / 3.9 pass | 3.4 / 3.71 / 3.9 pass | 3.65 / 4.0 / 4.05 pass |
> | G2a weak at max, boss (≥ 30) | 10.77 / 7.02 / 15.87 fail | 0.55 / 6.37 / 12.97 fail | 1.77 / 4.87 / 8.02 fail |
> | G2a weak at max, oh2 | 63.36 / 64.91 / 73.97 | 51.0 / 45.4 / 49.45 | 39.74 / 43.84 / 50.0 |
> | G5 strong at max (≤ 95) | **98.7** / 92.87 / **95.18** | 90.28 / 94.15 / **96.83** | **95.68** / **95.05** / **96.55** |
> | Reading gap (G3b ≥ 10) | 57.2 / 60.7 / 51.5 | 66.6 / 60.0 / 54.3 | 64.1 / 62.1 / 59.1 |
> | G3a drop kid1 → boss (≥ 30) | 27.8 / 27.8 / 28.9 fail | 28.98 / 29.53 / 28.78 fail | 29.72 / 29.02 / 28.93 fail |
> | G4a / G4b | pass | pass | pass |
>
> Without pacing, for comparison: lock cap G2a boss 25.87 / 19.45 / 21.0, G5 98.08 / 95.03 / 96.27, gap 40-47. Falloff 0.5: G2a
> 7.43 / 1.55 / 9.18, Wangan oh2 18.32, G5 96.72 / 87.88 / 97.53. Falloff 0.7: G2a 6.95 / 1.08 / 5.0, G5 97.3 / 86.63 / 96.27.
> **Correction:** G3a was marked "pass" in the lock-cap and falloff sections below. Against the live target (MS_TARGETS
> G3a_drop_kid1_boss 30, test_mod_skill) it fails in every model by 0.1-2.2 pp, because kid1 ≈ 96 and the boss band is 66-68.
> So it can only pass with the boss at about 66 or kid1 above 96. **Street falloff 0.7 + pace:** there is a stat cliff at boss
> 330.55 → 330.6 (strong at floor 76.3 → 65.8, n = 6,000), so 66-68 can't be reached. The closest is 65.83.
>
> **Feel with pacing (strong 80/80 at floor; player turns degraded % / average output / mean longest degraded stretch; AI planned stance
> degraded % / AI average output / AI off-line %). No pacing in brackets:**
>
> | Model | District | oh1 | oh2 | boss |
> |---|---|---|---|---|
> | lock cap | street | 12.3/0.947/1.2; AI 0/1.0/7.9 (AI 6.8/0.958) | 12.5/0.946/1.23 | 12.1/0.948/1.42; AI 0/1.0/23.7 (12.7/0.944/1.46; AI 34.5/0.85) |
> | lock cap | wangan | 9.9/0.953/1.24; AI 0/1.0/35.8 (AI 45.7/0.855) | 9.9/0.952/1.24 | 13.8/0.934/1.89; AI 0/1.0/36.5 (13.9/0.935/1.89; AI 48.2/0.831) |
> | lock cap | touge | 13.7/0.962/1.21; AI 0/1.0/24.7 (AI 34.3/0.942) | 14.7/0.959/1.24 | 18.7/0.939/1.64; AI 0/1.0/24.5 (18.5/0.94/1.64; AI 35.5/0.931) |
> | falloff 0.5 | street | 22.3/0.836/1.77 (24.7/0.814/2.0) | 22.7/0.832/1.81 | **19.6/0.87/1.81** (33.6/0.756/3.93; AI 46.7/0.65) |
> | falloff 0.5 | wangan | 14.8/0.878/1.55 (20.0/0.826/2.36) | 14.9/0.876/1.57 | **19.5/0.848/2.59** (30.2/0.766/5.15; AI 68.4/0.607) |
> | falloff 0.5 | touge | 22.6/0.843/1.35 (25.0/0.793/1.92) | 23.0/0.84/1.42 | **25.8/0.818/2.08** (32.1/0.754/3.88; AI 70.6/0.632) |
> | falloff 0.7 | street | 19.6/0.881/1.51 (22.5/0.865/1.73) | 19.9/0.878/1.55 | **18.6/0.881/1.86** (29.4/0.807/3.12; AI 45.4/0.674) |
> | falloff 0.7 | wangan | 13.3/0.902/1.4 (17.9/0.86/2.06) | 13.6/0.9/1.43 | **17.8/0.877/2.3** (27.1/0.8/4.57; AI 68.4/0.616) |
> | falloff 0.7 | touge | 19.8/0.892/1.2 (22.7/0.848/1.57) | 19.8/0.891/1.21 | **23.0/0.869/1.77** (30.0/0.8/3.3; AI 69.7/0.642) |
>
> The paced AI never plays a degraded stance (AI output 1.0 in every falloff cell; 3.9-4 % planned-degraded only in Wangan
> t 0.7, and it switches away from those). Without pacing the falloff AI played degraded stances 28-71 % of turns, at output
> 0.61-0.79. The player's degraded share at the boss under falloff drops from 27-34 % to 18-26 %, and the longest stretch
> halves (3.1-5.2 → 1.8-2.6 turns), because crew stats drop back to about live. The weak 60/60 player is worse off at the
> boss in every paced model (see G2a).
>
> **Cars at equal stats (2,000 races; player win % / player turns degraded % / player average output; AI off-line %):**
>
> | Matchup | live | live + pace | lock cap + pace | falloff 0.5 + pace | falloff 0.7 + pace |
> |---|---|---|---|---|---|
> | MX-5 vs S2000 | 72.15 / 16.5 / 0.961 | 71.7; AI 36.4 | 78.0 / 11.0 / 0.974; AI 36.4 | **52.85** / 17.9 / 0.895; AI 42.6 | 68.4 / 15.8 / 0.934; AI 37.5 |
> | WRX vs MX-5 | 81.25 / 34.1 / 0.886 | 73.8; AI 36.4 | 90.3 / 19.9 / 0.949; AI 36.4 | **67.1** / 27.8 / 0.845; AI 42.6 | 76.75 / 25.1 / 0.88; AI 37.5 |
>
> Without pacing, falloff was 99.9 / 98.75-98.9 % player win, so pacing removes the AI collapse. Lock cap without pacing was
> 78.45 / 93.25. Live + pace gives the same player numbers as live (pacing only changes the AI). WRX vs MX-5 under falloff 0.7 +
> pace (76.75) is closest to live (81.25).
>
> **Reading:** pacing fixes falloff's AI collapse and brings stats back to about live. Falloff 0.5 + pace passes the band,
> the ladder, G3b and G4 in all three districts, and G5 in Street and Wangan. It still fails G2a (weak at max at the boss is 0.6-13)
> and G3a by about 1. Pacing also widens the reading gap under the lock cap (40-47 → 51-61), because a paced AI punishes the
> weak build harder. **Closest fit: falloff 0.5 + pace** (best G5, smallest player degraded share). G2a still needs a lever
> outside crew stats.


> **2026-11-20 HEAT FALLOFF variant (Austin direct, 7:04-7:08 AM: "instead of locking out a stance, could we just make
> damage hit less?" / "on paper math the lock makes sense but playing it is really frustrating to get a lock out and it
> doesn't cool off... even more frustrating as we go up.").** Proposal only; sim/ untouched (`per_phase.patch`, `falloff_t`).
>
> **Definition (1 param):** gauges never lock, for the player or the AI. Output multiplier m = 1.0 while load after the push
> ≤ t·capacity, then falls linearly to 0.4 (the old limp value) at capacity, and stays at 0.4 above it. This replaces the
> overrun multiplier. Cooling is unchanged. **AI mapping:** its softer rules (release at 80 %, no passive locks) become a
> curve that starts 0.2 later (t_AI = t + 0.2: 0.7 / 0.9). Tried t = 0.5 and t = 0.7. Same model as the lock-cap re-pin
> (Street/Wangan per-phase smoothed w 0.35, Touge per-turn, Touge per-phase what-if). Rungs n = 2,000, bosses n = 6,000.
>
> **Re-pinned crew stats (live → falloff t 0.5 / t 0.7; lock cap for comparison):**
>
> | Rung | Street | Wangan | Touge |
> |---|---|---|---|
> | kid1 | 293.98 → 296.39 / 297.08 (cap 297.77) | 318.65 → 349.89 / 351.14 (cap 327.74) | 354.33 → 395.99 / 398.76 (cap 377.17) |
> | kid2 | 306.16 → 307.00 / 307.71 (cap 307.95) | 340.56 → 364.64 / 364.90 (cap 342.82) | 383.85 → 412.19 / 414.59 (cap 391.80) |
> | mat1 | 309.14 → 317.71 / 318.20 (cap 315.54) | 348.93 → 377.14 / 379.33 (cap 354.79) | 393.80 → 424.72 / 427.18 (cap 406.26) |
> | mat2 | 317.38 → 324.69 / 325.44 (cap 322.22) | 362.05 → 389.91 / 391.89 (cap 364.45) | 404.82 → 435.34 / 437.87 (cap 417.00) |
> | oh1 | 325.10 → 331.32 / 332.34 (cap 329.04) | 372.82 → 402.09 / 404.71 (cap 373.84) | 415.79 → 445.84 / 448.76 (cap 427.00) |
> | oh2 | 331.98 → 338.33 / 339.11 (cap 335.74) | 383.00 → 414.57 / 417.26 (cap 383.45) | 426.72 → 456.22 / 460.22 (cap 436.89) |
> | boss | 332.58 → 355.06 / 356.35 (cap 337.96) | 390.35 → 424.96 / 428.32 (cap 395.68) | 437.06 → 470.01 / 475.13 (cap 450.07) |
>
> **Climb (strong 80/80 at floor kid1 → boss; weak 60/60 at max kid1 → boss; boss weak at floor / strong at max):**
>
> | Model | District | Strong at floor | Weak at max | Boss wf / sm |
> |---|---|---|---|---|
> | falloff t 0.5 | street | 96.2 / 90.79 / 85.99 / 81.28 / 77.88 / 72.87 / 66.35 | 81.98 / 71.77 / 67.67 / 59.66 / 52.45 / 43.79 / 7.43 | 0.17 / 96.72 |
> | falloff t 0.5 | wangan | 95.95 / 90.09 / 85.54 / 80.78 / 76.43 / 71.42 / 67.3 | 93.69 / 87.64 / 87.19 / 72.57 / 56.26 / 18.32 / 1.55 | 0.23 / 87.88 |
> | falloff t 0.5 | touge | 96.85 / 91.54 / 85.54 / 81.53 / 77.83 / 73.27 / 67.6 | 94.04 / 90.54 / 92.59 / 90.24 / 85.09 / 62.21 / 9.18 | 0.07 / 97.53 |
> | falloff t 0.5 | touge_pp | 94.19 / 83.18 / 73.92 / 69.57 / 63.91 / 58.66 / 51.12 | 90.19 / 85.59 / 86.54 / 80.83 / 75.23 / 46.35 / 4.05 | 0.03 / 96.18 |
> | falloff t 0.7 | street | 96.4 / 90.74 / 86.49 / 81.98 / 77.73 / 72.92 / 67.13 | 81.18 / 70.47 / 66.37 / 57.21 / 47.75 / 40.29 / 6.95 | 0.15 / 97.3 |
> | falloff t 0.7 | wangan | 95.8 / 90.14 / 85.39 / 80.33 / 76.63 / 71.87 / 66.98 | 93.39 / 87.29 / 82.73 / 67.77 / 48.9 / 14.11 / 1.08 | 0.23 / 86.63 |
> | falloff t 0.7 | touge | 96.55 / 91.29 / 84.98 / 81.78 / 77.93 / 73.42 / 67.22 | 93.89 / 90.34 / 91.54 / 88.54 / 82.98 / 54.1 / 5.0 | 0.08 / 96.27 |
> | falloff t 0.7 | touge_pp | 93.74 / 82.43 / 72.42 / 67.97 / 62.16 / 57.31 / 51.07 | 89.79 / 85.69 / 84.03 / 78.43 / 72.32 / 37.84 / 2.32 | 0.02 / 93.43 |
> | lock cap | street | 95.95 / 90.44 / 84.68 / 81.43 / 76.68 / 72.07 / 66.22 | 86.09 / 81.28 / 87.34 / 81.03 / 72.02 / 64.21 / 25.87 | 0.35 / 98.08 |
> | lock cap | wangan | 96.1 / 90.64 / 85.34 / 81.03 / 77.23 / 72.17 / 66.57 | 92.44 / 86.94 / 92.94 / 90.84 / 89.54 / 75.98 / 19.45 | 0.18 / 95.03 |
> | lock cap | touge | 96.15 / 90.54 / 85.44 / 80.18 / 76.98 / 73.12 / 66.8 | 92.39 / 88.24 / 94.64 / 92.79 / 90.89 / 79.08 / 21.0 | 0.02 / 96.27 |
> | lock cap | touge_pp | 95.55 / 87.79 / 79.68 / 71.22 / 66.92 / 63.21 / 55.62 | 85.44 / 79.48 / 87.49 / 84.48 / 82.18 / 66.22 / 10.63 | 0.03 / 95.85 |
>
> **Criteria (falloff t 0.5 | t 0.7):**
> - **Boss 66-68:** pass in all three (66.35 / 67.3 / 67.6 | 67.13 / 66.98 / 67.22).
> - **Ladder ≥ 3.0:** pass in all three (smallest step 3.40 / 4.12 / 3.70 | 4.25 / 3.70 / 3.20).
> - **G3a, G3b, G4a, G4b:** pass. *(STALE 2026-11-20: G3a actually fails, drop 28.65-29.85 < 30; see AI pacing correction above.)*
> - **G2a: FAILS badly.** Weak at max at the boss is 7.43 / 1.55 / 9.18 | 6.95 / 1.08 / 5.0, and Wangan oh2 also fails (18.32 | 14.11).
> - **G5: fails in Street and Touge** (96.72 / 97.53 | 97.3 / 96.27). Wangan passes (87.88 | 86.63).
> - **Touge per-phase what-if:** boss 51.1 (fails the band).
>
> So falloff widens the reading gap far more than the lock cap: boss strong at floor − weak at max is 59-66 pp, against
> 40-47 for the cap. The stats needed jump a lot (boss +6.8 / +8.9 / +7.5 % at t 0.5), because the AI keeps pushing hot
> stances at reduced output while the pacing player doesn't. **Closest fit: t 0.5** (better G2a, similar G5). Same conflict
> as the cap: crew stats can't fix G2a/G5. That needs levers outside stats, plus an AI pacing rule.
>
> **Feel (n = 999 per cell; `feel.py` → `feel.json`; degraded = the counter stance is locked, or pays m < 0.7, at turn start):**
>
> | Cell | Lock cap: degraded % / avg mult / longest (mean, max) | Falloff 0.5 | Falloff 0.7 |
> |---|---|---|---|
> | street oh1 strong | 12.3 / 0.947 / 1.2, 9 | 24.7 / 0.814 / 2.0, 11 | 22.5 / 0.865 / 1.73, 9 |
> | street oh1 weak | 15.9 / 0.934 / 1.26, 6 | 31.5 / 0.758 / 1.93, 9 | 28.4 / 0.788 / 1.77, 7 |
> | street oh2 strong | 12.6 / 0.945 / 1.24, 9 | 25.2 / 0.811 / 2.06, 13 | 22.6 / 0.863 / 1.76, 9 |
> | street oh2 weak | 16.4 / 0.932 / 1.3, 6 | 32.3 / 0.755 / 2.02, 9 | 29.5 / 0.787 / 1.79, 7 |
> | street boss strong | 12.7 / 0.944 / 1.46, 9 | 33.6 / 0.756 / 3.93, 23 | 29.4 / 0.807 / 3.12, 19 |
> | street boss weak | 17.3 / 0.928 / 1.54, 6 | 40.0 / 0.706 / 3.32, 14 | 36.9 / 0.739 / 2.75, 13 |
> | wangan oh1 strong | 9.5 / 0.955 / 1.2, 6 | 20.0 / 0.826 / 2.36, 15 | 17.9 / 0.86 / 2.06, 15 |
> | wangan oh1 weak | 13.1 / 0.937 / 1.59, 5 | 22.0 / 0.773 / 1.92, 15 | 20.5 / 0.796 / 1.78, 15 |
> | wangan oh2 strong | 9.6 / 0.954 / 1.22, 6 | 21.3 / 0.818 / 2.54, 15 | 18.7 / 0.853 / 2.2, 15 |
> | wangan oh2 weak | 14.7 / 0.929 / 1.67, 6 | 23.7 / 0.759 / 2.1, 15 | 21.7 / 0.784 / 1.92, 15 |
> | wangan boss strong | 13.9 / 0.935 / 1.89, 16 | 30.2 / 0.766 / 5.15, 25 | 27.1 / 0.8 / 4.57, 25 |
> | wangan boss weak | 21.4 / 0.897 / 2.53, 7 | 32.0 / 0.708 / 4.05, 25 | 29.9 / 0.733 / 3.69, 25 |
> | touge oh1 strong | 13.3 / 0.963 / 1.19, 3 | 25.0 / 0.793 / 1.92, 15 | 22.7 / 0.848 / 1.57, 14 |
> | touge oh1 weak | 14.0 / 0.957 / 1.09, 3 | 27.9 / 0.783 / 1.49, 11 | 25.1 / 0.824 / 1.3, 11 |
> | touge oh2 strong | 13.7 / 0.962 / 1.21, 3 | 25.3 / 0.79 / 1.99, 15 | 23.3 / 0.843 / 1.63, 14 |
> | touge oh2 weak | 16.3 / 0.951 / 1.26, 3 | 28.9 / 0.77 / 1.63, 11 | 27.3 / 0.81 / 1.48, 11 |
> | touge boss strong | 18.5 / 0.94 / 1.64, 5 | 32.1 / 0.754 / 3.88, 25 | 30.0 / 0.8 / 3.3, 24 |
> | touge boss weak | 22.1 / 0.925 / 1.71, 3 | 36.5 / 0.716 / 3.54, 21 | 33.8 / 0.751 / 3.09, 21 |
>
> **On these metrics, falloff feels worse than the lock cap.** The counter stance is degraded on 18-40 % of turns (cap
> 9.5-22 %), average output is 0.71-0.87 (cap 0.90-0.96), and boss stretches run 3-5 turns on average, up to 25 (cap
> 1.5-2.5, max 16). With falloff the stance is never closed, so the player keeps paying the penalty instead of switching.
> t 0.7 is milder than 0.5 on every feel metric.
>
> **Playtest cars under falloff** (r = 1, 2,000 races; `car_matchup.json`):
>
> | | Win % | Degraded % | Avg mult | Longest degraded (mean, max) |
> |---|---|---|---|---|
> | MX-5 vs S2000: live / cap / falloff 0.5 / 0.7 | 72.15 / 78.45 / 99.9 / 99.9 | 16.5 / 11.0 / 17.9 / 15.8 | 0.961 / 0.974 / 0.895 / 0.934 | 1.46, 5 / 0.91, 4 / 1.57, 5 / 1.38, 5 |
> | WRX vs MX-5: live / cap / falloff 0.5 / 0.7 | 81.25 / 93.25 / 98.75 / 98.9 | 34.1 / 19.9 / 27.8 / 25.1 | 0.886 / 0.949 / 0.845 / 0.88 | 2.99, 8 / 1.46, 6 / 2.35, 8 / 1.98, 8 |
>
> At parity the AI collapses under falloff (player wins 99 %), because it has no pacing rule and keeps playing its line
> into hot gauges. **Falloff needs an AI pacing rule** before it can be judged fairly. Re-pinned crew stats cover the
> climb, but not the 10-turn car playtest.

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
| G3a (drop ≥ 30) | pass *(STALE: fails, 29.73; see correction above)* | pass *(STALE: 29.53)* | pass *(STALE: 29.35)* | pass |
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
