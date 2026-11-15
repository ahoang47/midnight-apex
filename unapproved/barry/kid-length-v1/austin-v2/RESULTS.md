# kid-length-v1 / austin-v2 (draft, not live) — Barry 2026-11-14

> Committed 2026-11-14 as a draft (not live). Run on the sim as it was before xp-carry-v1 fix C went live, with fix C patched in memory; on today's live sim, drop the in-memory fix C patch or the catch-up XP is applied twice.

Austin's decisions:
- Kid races are 20 turns, without fix K. Kid races dipping below target is fine; it means more forced grinding.
- No finite grind pool. Grinds are unlimited and limited only by XP: they pay good XP all the way to the stage's level cap, then nothing.

Setup:
- Base: live mods-v1 + xp-carry fix C.
- `LADDER_TURNS = (20, 20, 20, 20, 20, 20, 30)`. Grinds stay 10 turns, against today's kid1 opponent (no fix K, so nothing to separate).
- Grind falloff removed: `GRIND_TAPER_FLOOR` 0.20 → **1.0**, so every grind pays a flat 0.70 × xp_to_next(L). `GRIND_FRAC` stays 0.70. XP past the cap is still lost.
- The pre-finale arc walker gets the same floor.

Everything is patched in memory (`run.py` → `results.json`, `run.txt`). `sim/` is unchanged. Grind purse is unchanged ($550 / $632.50 / $742.50).

Levels per grind:

| Levels below cap | 10 | 6 | 3 | 2 | 1 | at cap |
|---|---|---|---|---|---|---|
| today (floor 0.20) | 0.67 | 0.59 | 0.46 | 0.38 | 0.28 | 0 |
| austin-v2 (flat) | 0.70 | 0.70 | 0.70 | 0.70 | 0.70 | 0 |
| soft option (floor 0.60) | 0.68 | 0.65 | 0.58 | 0.54 | 0.49 | 0 |

## Kid races
Lower of the district average and the hardest track. Levels are the story-only arrival levels; 20/20 arrival levels are the same as 10/10 for story-only.

| Race (story-only) | today 10/10, L · 80/80 | austin-v2 80/80 | 60/80 | 80/60 |
|---|---|---|---|---|
| R1 kid1 | L0 · 92.0 | 88.0 | 57.7 | 46.7 |
| R1 kid2 | L1 · 95.5 | 93.1 | 72.0 | 68.5 |
| R2 kid1 | L7 · 58.7 | 50.8 | 18.2 | 5.0 |
| R2 kid2 | L12 · 79.0 | 73.7 | 38.2 | 29.3 |
| R3 kid1 | L26 · 54.1 | **44.3** | 13.3 | 1.2 |
| R3 kid2 | L30 · 70.7 | 63.3 | 27.7 | 11.7 |

At the level cap, kid races are 96–100 % for every profile.

| Grinds forced by kid races | today | austin-v2 |
|---|---|---|
| Mixed (R1 / R2 / R3) | 0 / 0 / 0 | **1 / 0 / 5** (all at kid1) |
| 60/60 (R1 / R2 / R3) | 1 / 3 / 6 | **2 / 5 / 9** (all at kid1) |

After those grinds, the mixed player meets the kid races at 79–89 % (R1), 55–61 % (R2) and 53–59 % (R3). The 60/60 player meets them at 76 / 56 / 55 %.

## Campaign
| Check | today (10/10, floor 0.20) | kid 20/20, floor 0.20 | **austin-v2** (20/20, flat) |
|---|---|---|---|
| Mixed total grinds | 13 / 13 / 12 | 13 / 13 / 14 | **9 / 9 / 10** |
| Mixed first grind stretch (target 3–6) | 3 mat1 / 3 mat1 / 4 mat1 | 1 kid1 / 3 mat1 / 5 kid1 | **1 kid1** / 3 mat1 / 5 kid1 |
| Mixed grinds to the cap before the boss | 10 / 10 / 8 | 12 / 10 / 9 | 8 / 6 / 5 |
| 60/60 total grinds | 13 / 15 / 18 | 13 / 16 / 19 | **11 / 14 / 16** |
| 60/60 grinds by rung | — | — | R1 kid1 2, mat1 4, mat2 3, oh1 1, boss 1 · R2 kid1 5, mat1 4, mat2 4, oh1 1 · R3 kid1 9, mat1 2, mat2 4, oh1 1 |
| 60/60 reaches every cap | yes | yes | **yes** (L12 / 29 / 46) |
| 60/60 at cap, full mod fill (≥30) | 31.6 / 40.1 / 30.2 | same | same |
| 80/80 at cap (90–95) | 94.9 / 91.6 / 92.9 | same | same |
| 60/60 boss in the walk (own cash) | 31.6 / 40.1 / 30.3 | 31.6 / 40.1 / 30.3 | **29.7** / 40.1 / 30.3 |
| Mod fill at the boss: mixed · 60/60 | 100 · 100 | 100 · 100 | 99.6 / 100 / 99.7 · 99.6 / 100 / 100 |
| Mixed cash at round end | $5,050 / $15,632 / $16,102 | $5,050 / $15,632 / $17,588 | $2,850 / $10,902 / $9,888 |
| 60/60 cash at round end | $4,550 / $13,998 / $16,922 | $4,550 / $14,630 / $18,298 | $3,450 / $12,265 / $13,705 |
| Story-only lowest race (80/80) | 53.0 / 54.4 / 50.5 | 53.0 / 50.8 / **44.3** | 53.0 / 50.8 / **44.3** |
| Story-only bosses | 53.0 / 57.7 / 55.8 | same | same |
| Story-only cash at round end · mods spent | $5,900 / $13,940 / $26,700 · $27,300 | same | same |

What the story-only player can afford at each boss (all versions): R1 4 × Mk1; R2 1 Mk2 + 3 Mk1; R3 1 Mk2 + 3 Mk1. Mod fill is 100 % every time.

Mixed and 60/60 players still end up with mostly Mk3 sets ($62,180 / $67,080 spent, same as today). The exception is that they now arrive one mod short at two bosses, covered in the next section.

## Flatter XP: earlier cap, less cash
Players reach the cap in fewer grinds, so they carry less grind cash. At three bosses, the player is one mod short of full fill:

| Walk | Round | Cash before the boss | Missing mod | Fix |
|---|---|---|---|---|
| 60/60 | R1 | $717.50 | R1 EN Mk3 ($1,000) | 1 cash-only grind at the cap ($550) |
| Mixed | R1 | $832.50 | R1 EN Mk3 ($1,000) | 1 cash-only grind at the cap ($550) |
| Mixed | R3 | $5,487.50 | R3 EN Mk3 ($6,400 at wholesale) | 2 cash-only grinds at the cap ($742.50 each) |

- The 60/60 R1 boss drops from 31.6 to 29.7, just under the 30 floor. The full-fill check stays at 31.6.
- With grind prize money as it is, the R1 60/60 boss gate now depends on one grind at the cap that pays cash but no XP.
- Mixed bosses move by at most 1.4 points (60/80 71.0 / 64.1 / 67.3 against 72.4 / 64.1 / 67.6 today). They stay well above 50.

## Pre-finale arc and finale
| Profile | arc grinds, today | austin-v2 | finale F1–F4 | arc end cash, today → v2 |
|---|---|---|---|---|
| 60/60 | 11 / 7 / 7 / 9 | 9 / 7 / 7 / 8 | 34.7 / 41.7 / 31.6 / 34.7 (same) | $35,243 → $29,798 |
| 60/80 | 7 / 6 / 6 / 7 | 5 / 5 / 4 / 6 | 72.6 / 64.2 / 72.4 / 72.6 (same) | $28,483 → $17,813 |
| 80/60 | 6 / 6 / 6 / 7 | 5 / 5 / 4 / 6 | 74.1 / 84.2 / 71.0 / 74.1 (same) | $27,740 → $17,813 |
| 80/80 | 0 | 0 | 81.7 / 82.7 / 79.3 / 81.7 (same) | $13,275 (same) |

The arc's lowest story race is unchanged: 52.1 / 53.1 / 54.1 / 55.9. Finale odds don't move. Only cash goes down.

## Cash farming at the cap
- It is already possible today: a grind at the cap pays the full purse and 0 XP, with no limit.
- With flat XP it becomes the normal way to close the last-mod gap: 1–2 races per affected boss, as in the table above.
- It's bounded. Mods stop at 107 % fill, so farming only buys the fill a capped player gets anyway, a bit earlier.
- Spare cash past full fill has nowhere useful to go: betting is fair odds, and the Myth mods are locked by arc wins.
- The full R3 Mk3 set ($25,600 at wholesale) is about 34 cap grinds. That's tedious but not an exploit.
- Options, not done here:
  - leave it as is;
  - pay no purse past the cap. This breaks the 60/60 R1 gate (29.7) unless R1 EN Mk3 drops to about $700 or the R1 grind purse rises;
  - halve the purse at the cap.

## Soft option (floor 0.60) for comparison
- Mixed: 10 / 11 / 11 grinds, first stretch 1 kid1 / 3 mat1 / 5 kid1.
- 60/60: 11 / 15 / 17 grinds; R1 boss still 29.7.
- Arc grinds slightly higher; finale the same.

## Planner page (not updated)
Regenerate `planner-v1` constants with:
- `TURNS` [20, 20, 20, 20, 20, 20, 30]
- `FLOOR` 1.0
- `CATCHUP` as before

Then re-verify. Kid opponent strengths and the grind opponent are unchanged.
