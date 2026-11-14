# story-xp-v1: cut story XP so 80/80 story-only meets bosses at about 55% (draft, Barry, 2026-11-14)

Austin's ask (2026-11-14): cut story-race XP so an 80/80 story-only player (no grind) wins bosses on the hardest track
about 55% of the time (live: R1 61.6, R2 67.2, R3 64.6; finale billed 81.7 / 82.7 / 79.3 / 81.7), while keeping the
other econ-v1 criteria. Draft only: no `sim/` edits, no commits.

Base: live `6d3641f` (`sim/velocity_shift/progression.py` walk, `sim/config/winrate_g2_live_tracks_v1.json`).
Campaign = live `progression.run()` with `equations.story_xp` scaled per round and rung in memory (`camp.py`).
Arc and finale = the econ-v1 draft arc walker with live arc budgets, live caps and the live table (`arc.py`).
It reproduces the live numbers exactly at multiplier 1.0 (grind 7/6/6/7, 6/6/6/7, 11/7/7/9; billed 81.7 / 82.7 / 79.3 / 81.7).

## Why a flat cut doesn't work

80/80's boss odds move about 9-11 points per level near the boss (hardest track):
R1 L7 61.6 → L6 53.0; R2 L24 67.2 → L23 57.7; R3 L42 64.6 → L41 55.7. One level less per round is the target.
A flat cut of the round's story XP also lowers the mid-ladder rungs.
R2 ×0.925 drops oh1 to 45.0, below the 50% floor (R3 is already at 50.4 on oh1). So the cut goes on the late rungs, which only move the boss arrival.

## Recommended campaign set (`C_rec`)

| Round | Lever | Plateau that gives the same result | 80/80 levels kid1..boss | Boss (hardest) | Lowest story race |
|---|---|---|---|---|---|
| R1 | all rungs ×0.90 (`STORY_FILL` 0.62 → 0.558) | 0.83-0.92 | 0,1,2,3,4,5,6 (was 0,1,2,3,5,6,7) | 53.0 (was 61.6) | 53.0 boss |
| R2 | oh2 rung ×0.60 | 0.18-0.62 | 12,14,17,19,21,23,23 (was ..,23,24) | 57.7 (was 67.2) | 54.1 oh1 (unchanged) |
| R3 | oh2 rung ×0.80 | 0.33-0.95 | 29,31,34,36,38,40,41 (was ..,40,42) | 55.7 (was 64.6) | 50.4 oh1 (unchanged) |

Alternative `C_even`: R2 oh1+oh2 ×0.70 (plateau 0.58-0.80). It gives even R2 levels (..21,22,23), so every race levels up, at +1 grind for mixed and 60/60 in R2.
With `C_rec`, R2's oh2 win doesn't reach a new level before the boss.

80/80 story-only still ends R3 at L43 (the boss win pays as before), so it enters the arc at the same level.

### Grind (wall + to-cap) before → after

| Round | 60/80 & 80/60 (mixed) | 60/60 | Mixed cash | 60/60 cash |
|---|---|---|---|---|
| R1 | 3+9=12 → 3+10=13 | 2+10=12 → 2+11=13 | $10,600 → $11,150 | $10,600 → $11,150 |
| R2 | 3+9=12 → 3+10=13 (`C_even` 3+11=14) | 3+12=15 → 3+12=15 (`C_even` 16) | $41,190 → $42,372.50 | $43,087.50 → $43,637.50 |
| R3 | 4+8=12 → 4+8=12 | 6+12=18 → 6+12=18 | $77,100 → $78,282.50 | $83,452.50 → $84,002.50 |

The walls stay at mat1 (mixed) and kid1 (60/60), and every profile still reaches every cap.
Bosses at the cap are unchanged (60/60 31.6 / 39.3 / 30.6; 80/80 94.9 / 90.6 / 93.0).
The 10-turn grind races are unchanged. 80/80 story-only cash is unchanged ($7,000 + $3,000 debt left after R1, then $27,000 and $54,000).
Criterion 2 (mixed wall 3-6 plus to-cap 8-10) holds: to-cap is 10 / 10 / 8.

## Finale billed fights (optional)

A flat cut of the arc's story XP (`ARC_STORY_FILL` per step) breaks 80/80: M12 falls to 20% and P3, M22 and M32 fall under 50%.
So the lever shifts XP instead. The story race just before each billed fight pays less (P4, M12, M22, M32).
The first race after the fight pays more (M11, M21, M31), so 80/80 is back at its live level by the next wall race.
Multipliers apply on top of `ARC_STORY_FILL` 0.80.

| Option | P4 | M11 | M12 | M21 | M22 | M31 | M32 | 80/80 at F1-F4 (L) | 80/80 billed (hardest) |
|---|---|---|---|---|---|---|---|---|---|
| live | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 61 / 76 / 91 / 112 | 81.7 / 82.7 / 79.3 / 81.7 |
| t62 | 0.46 | 1.18 | 0.53 | 1.26 | 0.68 | 1.08 | 0.75 | 59 / 73 / 89 / 110 | 64.1 / 66.1 / 62.1 / 64.2 |
| t55 | 0.18 | 1.26 | 0.37 | 1.34 | 0.52 | 1.12 | 0.62 | 58 / 72 / 88 / 109 | 55.3 / 55.5 / 54.1 / 55.3 |

A level step near 60 doesn't exist: one level is 9-11 points, so "about 60" lands on 62-66 (t62) or 54-56 (t55).
In both options the 80/80 arc story races are unchanged: the lowest is 59.3 (M12), and P3 64.6, M22 75.3, M32 59.6.
Billed fights for grinders are unchanged at the cap (60/60 34.7 / 41.7 / 31.6 / 34.7).

### Arc grind per step (wall + to-cap), on top of `C_rec`

| Profile | live arc | t62 | t55 |
|---|---|---|---|
| 60/80 | 4+3, 4+2, 1+5, 4+3 = 7/6/6/7 | 4+7, 2+8, 0+8, 3+7 = 11/10/8/10 | 4+9, 2+10, 0+9, 3+9 = 13/12/9/12 |
| 80/60 | 5+1, 4+2, 2+4, 6+1 = 6/6/6/7 | 5+6, 2+8, 0+8, 5+5 = 11/10/8/10 | 5+8, 2+10, 0+9, 4+8 = 13/12/9/12 |
| 60/60 | 11/7/7/9 | 11/10/7/9 | 11/11/9/11 |
| 80/80 story | 0 | 0 | 0 |

End of finale, after buying mods: 80/80 L109-112, $31,075 in every option (full T4 set).
Mixed $78,972.50 / $78,230 (live arc), $88,625 (t62), $93,822.50 (t55).
60/60 $92,282.50 (live arc), $94,510 (t62), $98,222.50 (t55).

**What breaks:** in the arc, the econ-v1 check "mixed ≤10 grinds per step" fails. t62 is 11 before F1. t55 is 12-13 on three steps.
The cause is structural: XP is the only lever that separates story-only players from grinders. Any XP taken away from 80/80 before a billed fight also has to be ground back by mixed players, about one grind per level, to reach the cap.
Everything else holds: 80/80 ≥50% on every story race, 60/60 at cap, bosses ≥30%, finale reachable, T4 bought by every profile.

## Options for Austin
1. Campaign `C_rec` (or `C_even`) and leave the arc alone. R1-R3 bosses are 53.0 / 57.7 / 55.7, finale billed 81.7 / 82.7 / 79.3 / 81.7, and mixed grind +1 per round.
2. `C_rec` + arc t62. Billed fights 62-66; mixed arc grind 11/10/8/10 (one step over 10).
3. `C_rec` + arc t55. Billed fights 54-56; mixed arc grind 13/12/9/12 (three steps over 10).

## Caveats
- The live walk enters each round at the previous round's cap, even for story-only. Story-only's R1/R2 end level (L7, L25) is not carried forward; this is the live model's assumption and is unchanged here.
- Each choice sits inside a plateau of multipliers that gives the same levels (table above). Rounding into a different level moves 80/80 by about 9-11 points.
- The hardest Touge track is the most stat-sensitive (see econ-v1-live-tracks RESULTS.md). R3's 50.4 oh1 floor is unchanged but still thin.

Files: `camp.py`, `arc.py`, `sweep.py`/`sweep.json` (per-round sweep), `cands.py`/`cands_campaign.json`,
`arc_fit.py`/`arc_fit_B_mixed.json` (flat arc cut, rejected), `arc_fit2.py`/`arc_fit2_C_rec.json`, `arc_grind_split_C_rec.json`.
