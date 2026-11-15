# xp-carry-v1 — Barry 2026-11-14 (fix C LIVE since 2026-11-14 on Austin's go; this folder is the study)

> **Go-live note:** fix C is now in `sim/velocity_shift/` (`story_xp` with `CATCHUP_XP_FRAC` / `CATCHUP_XP_SHARE`, `STORY_XP_MULT` R2 boss 1.5,
> `run_with_garage` no longer bumps to the previous cap). The scripts here patch the *pre-go-live* sim in memory; re-running `catchup.make`
> on the live sim would apply the catch-up twice. The live numbers match the fix C column below exactly.

Austin: leftover XP carries over between rounds. A player starts R2/R3 at the level and XP bag they actually finished on,
not at the previous cap with an empty bag. Run on live mods-v1 (Mk3 optional, not the mods-v2 draft). Patches are in memory only
(`carry.py`, `catchup.py`, `final.py` → `results.json`, `final.txt`). `sim/` is unchanged.

Only story-only (80/80) feels it: mixed and hard grind to every cap (bag 0 at the cap), so they enter at the cap anyway.

## Confirmed on live mods-v1 (carry, no fix)
Story-only 80/80 enters R2 at L7 (live L12) and R3 at L25 (live L29). Rows below 50% (min of district and hardest track):
| Race | live (reset) | carry | /tmp/carry scratch |
|---|---|---|---|
| R2 mat2 | L19 57.1 | L18 **49.2** | 49.0 |
| R2 oh1 | L21 54.4 | L20 **45.0** | 45.0 |
| R3 kid1 | L29 76.2 | L25 **43.3** | 43.4 |
| R3 mat2 | L36 51.0 | L35 **39.5** | 39.5 |
(small differences from the scratch come from the mods-v1 garage.) Bosses 53.0/57.7/55.8, at-cap, mixed/hard, arc and finale are all unchanged.
Why: story_xp pays STORY_FILL of XP(entry→cap). A lower entry pays more XP in total, so the story player is back on track by the boss,
but the mid-ladder rows land about 1 level low. Raising R1 boss XP doesn't help R2 (a higher entry just gets less XP back, so R2 mat2/oh1 stay at L18/L20).

## Fixes tried
| Lever | Result |
|---|---|
| Front-load R2/R3 story XP (kid1..mat2 x1.2–1.6) | fixes the rows, but the story boss rises to L24 (67.7) and the mixed R2 wall drops to 1–2 (below 3) |
| R1 boss XP ×1.35–2.25 | no effect on R2 mid rows (see above) |
| **B: R2 boss XP 1.0→1.5 + R2 mat2/oh1 opponent r +0.005 (1.080→1.085, 1.060→1.065)** | all rows ≥50 (R2 min 51.2), but changes the ladder for everyone (hard R2 grinds 15→16) |
| **C: catch-up story XP + R2 boss XP 1.0→1.5** (recommended) | all rows ≥50, minimums equal to live, story-only only |

**Fix C, exact rule:** a story race pays the live nominal XP (story_xp as if the round was entered at the previous cap) plus
0.75 × the XP the player is short of that cap, XP(entry→prev cap), split kid1 40 % / kid2 40 % / mat1 20 %. Entering at the cap
(mixed, hard, or story on the live reset rule) pays exactly the live XP. Plus `STORY_XP_MULT` R2 boss 1.0 → 1.5. That race comes after
the R2 boss, so only the carried level into R3 moves (L25 → L26), which fixes R3 kid1. Opponents and bosses are untouched.

## Before / after (story-only 80/80; min of district and hardest track)
| Rung | live R2 | carry R2 | fix C R2 | live R3 | carry R3 | fix C R3 |
|---|---|---|---|---|---|---|
| kid1 | L12 88.5 | L7 58.7 | L7 58.7 | L29 76.2 | L25 **43.3** | L26 54.1 |
| kid2 | L14 87.8 | L12 79.0 | L12 79.0 | L31 75.9 | L29 63.5 | L30 70.7 |
| mat1 | L17 69.8 | L15 53.1 | L16 60.7 | L34 68.1 | L32 50.9 | L34 68.1 |
| mat2 | L19 57.1 | L18 **49.2** | L19 57.1 | L36 51.0 | L35 **39.5** | L36 51.0 |
| oh1 | L21 54.4 | L20 **45.0** | L21 54.4 | L38 50.5 | L38 50.5 | L38 50.5 |
| oh2 | L23 66.0 | L22 57.3 | L22 57.3 | L40 60.3 | L40 60.3 | L40 60.3 |
| boss | L23 57.7 | L23 57.7 | L23 57.7 | L41 55.8 | L41 55.8 | L41 55.8 |
R1 is unchanged in all variants (53.0 minimum, the boss).

| Check | live | carry | fix C | fix B |
|---|---|---|---|---|
| Story minimum R1/R2/R3 (≥50) | 53.0/54.4/50.5 | 53.0/**45.0/39.5** | 53.0/54.4/50.5 | 53.0/51.2/50.5 |
| Story bosses | 53.0/57.7/55.8 | same | same | same |
| 60/60 at cap (≥30) | 31.6/40.1/30.2 | same | same | same |
| 80/80 at cap (90–95) | 94.9/91.6/92.9 | same | same | same |
| Mixed wall / total grinds | 3/3/4 · 13/13/12 | same | same | same |
| Hard grinds | 13/15/18 | same | same | 13/16/18 |
| Finale 80/80 F1–F4 / arc grinds 60/60 | 81.7/82.7/79.3/81.7 / 11/7/7/9 | same | same | same |
| Story cash end R1/R2/R3 | $5,900/$17,660/$30,420 | $5,900/$17,940/$30,700 | $5,900/$13,940/$26,700 | $5,900/$13,940/$26,700 |
| Story cash after finale | $16,995 | $17,275 | $13,275 | $13,275 |

## Flags
- Grind races are not easy for an under-leveled story player at the start of R2: with carry, a 10-turn grind at R2 kid1 (L7) is 58.7 % for
  80/80, against 85.6 % worst case on the live reset. Story-only players don't grind in the walk, so no target breaks, but "grinds stay easy" no longer holds at round start.
- R2 kid1 at L7 is 58.7 % (live 88.5 %); it passes but is the new thinnest early race.
- Fix C spends about $3,700 more on mods by end of R3 ($27,300 vs $23,580); the finale is unchanged.
