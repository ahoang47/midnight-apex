# mods-v2-mk3-boss (draft, not live) — Barry 2026-11-14

> Committed 2026-11-14 as a draft (not live). Run on the sim as it was before xp-carry-v1 fix C went live (no carry-over); not re-run since. Story-only cash differs under the live carry-over (end R2 $13,940 vs $17,660), so re-run before relying on story-only figures. Austin reviewed it and chose no changes ("Ok no changes then"), so it is kept for reference only.

Goal (Austin): story-only players must play a grind race or two per round, and Mk3 must be REQUIRED to win the boss
(a Mk2-capped car fails the boss, the same car with Mk3 clears it). All numbers are from the live sim (mods-v1) run
in memory with the patches below (`mk3boss.py`, `configs.py`, `final_report.py`, `results.json`). `sim/` is not changed.

## Why the levers had to combine
Mods make up only about 25 % of a car's points (gap = 1.07P − SP). One level of Mk2 shortfall is worth ~2.5 win points
at the boss, while one full level is worth ~10. So a Mk2-capped car only drops ~13–16 points below the Mk3 car when Mk2
stops filling **~5–6 levels below the story boss level**. On its own (no XP change), a 1–2 grind gate just raises the
boss level: R2 boss 57.7 → 67.8 (1 grind) / 74.5 (2 grinds), so the no-Mk3 car still wins.
What works: (1) a grind gate **after the mat1 win, before mat2** (where Mk2 unlocks), (2) taking the same XP back
out of oh1/oh2 so the story player still meets each boss at L6/L23/L41, (3) Mk1/Mk2 shrunk to fill through lower levels.
**Boss r is unchanged.** (Lowering boss r would make the needed level gap bigger; raising it breaks 80/80 at cap, R2 = 91.6.)
Grinds placed before oh1, before oh2 or before the boss scored worse in the grid (`grid3.json`).

## The two candidates
| | G1: 1 mandatory grind | G2: 2 mandatory grinds |
|---|---|---|
| Gate | 1 grind win after mat1, before mat2 (R1–R3) | 2 grind wins after mat1, before mat2 (R1–R3) |
| Story XP (`STORY_XP_MULT` oh1 / oh2), live R1 .90/.90, R2 1.0/.60, R3 1.0/.80 | R1 .63/.90 · R2 1.0/.30 · R3 1.0/.60 | R1 .63/.27 · R2 .40/.30 · R3 1.0/.30 |
| Mk1 / Mk2 fill through (live 6/9, 22/26, 40/44) | R1 0/2 · R2 15/17 · R3 34/36 | R1 0/2 · R2 14/16 · R3 34/36 |
| Mk3 fills through | cap (12/29/46), unchanged | same |

## Catalog (points per mod, same for POW/HAN/EN; list price, R2–R3 still 20 % wholesale)
| ID | live mods-v1 | G1 | G2 |
|---|---|---|---|
| R1 Mk1 / Mk2 / Mk3 | 213/218/223 · $150/$500/$1,000 | 203/206/223 · $150/$500/**$1,000** | same as G1 |
| R2 Mk1 / Mk2 / Mk3 | 242/249/255 · $700/$1,500/$5,000 | 229/232/255 · $400/$900/**$2,000** | 227/230/255 · $400/$900/**$3,000** |
| R3 Mk1 / Mk2 / Mk3 | 279/288/292 · $1,200/$2,500/$8,000 | 266/270/292 · $700/$1,500/**$4,000** | 266/270/292 · $700/$1,500/**$4,000** |
| ARC MYTH1–4 | unchanged | unchanged | unchanged |
Unlocks unchanged (Mk1 at round open, Mk2 after mat1, Mk3 after mat2). The aspirational $5k/$8k Mk3 had to go: with mods-v1 Mk1/Mk2 prices and R2 Mk3 $5,000 the story boss drops to 48.8 (G1) / 56.8 with oh1 50.6 (G2), and R3 $6,000+ leaves story short of a MYTH4 at
F4 (finale 81.7 → 65.1). Mk1/Mk2 in R2–R3 had to drop to 0.6× (they fill fewer levels now) or the story finale F4 falls to 78.2.
Highest Mk3 prices that keep every target with R3 Mk3 $4,000: G1 R2 $2,000 (R2 $2,500 still passes with story oh1 52.9 only if R3 is $3,000), G2 R2 $3,000 (R2 $3,500 passes only with R3 $3,000). Price grid: `arc_price2.json`.

## Boss win with / without Mk3 (without = all 4 slots at that round's Mk2)
| Profile @ boss | live (with = without) | G1 with / without | G2 with / without |
|---|---|---|---|
| Story 80/80 R1 (L6) | 53.0 / 53.0 | 53.0 / **41.8** | 53.0 / **41.8** |
| Story 80/80 R2 (L23) | 57.7 / 57.7 | 57.8 / **42.0** | 57.8 / **39.6** |
| Story 80/80 R3 (L41) | 55.8 / 55.8 | 55.8 / **43.4** | 55.8 / **43.4** |
| Mixed 80/80 at cap R1/R2/R3 | 94.9/91.6/92.9 (no-Mk3 92.7/90.0/87.9) | 94.9/91.6/92.9 / 81.6/81.4/81.0 | 94.9/91.6/92.9 / 81.6/80.2/81.0 |
| Mixed 60/80 at cap | 72.4/64.1/67.6 | same / 45.9/38.3/42.4 | same / 45.9/35.7/42.4 |
| Mixed 80/60 at cap | 71.0/81.4/70.1 | same / 33.1/53.5/35.8 | same / 33.1/48.5/35.8 |
| Hard 60/60 at cap | 31.6/40.1/30.3 | same / 7.6/10.4/11.4 | same / 7.6/8.2/11.4 |

## Targets
| Target | live | G1 | G2 |
|---|---|---|---|
| Story min win per round (≥50) | 53.0/54.4/50.5 | 53.0/54.5/55.8 | 53.0/**57.1**/55.8 |
| Mk2-capped story car, worst non-boss rung (≥50 means Mk3 is needed only at the boss) | — | 76.1/**45.7**/51.6 (R2 oh1 also needs Mk3) | 76.1/50.6/53.0 |
| Story grinds per round | 0/0/0 | 1/1/1 | 2/2/2 |
| 60/60 at cap (≥30) | 31.6/40.1/30.3 | 31.6/40.1/30.3 | 31.6/40.1/30.3 |
| 80/80 at cap (90–95) | 94.9/91.6/92.9 | same | same |
| Mixed wall (3–6; the mixed player's wall covers the gate) / total grinds | 3/3/4 · 13/13/12 | 5/6/6 · 14/15/13 | 5/6/6 · 15/16/14 |
| Hard grinds per round | 13/15/18 | 15/18/22 | 15/22/22 |
| Grind races easy, min 10-turn grind win (80/80; 60/60) | 85.6; 50.3 | 85.6; 52.1 | 85.6; 52.1 |
| Finale billed races 80/80 (F1–F4) | 81.7/82.7/79.3/81.7 | same | same |
| Finale grinds per step 60/60 · 60/80 · 80/60 · 80/80 | 11/7/7/9 · 7/6/6/7 · 6/6/6/7 · 0 | same | same |
| Story arc min | 55.9 | 59.4 | 59.4 |

## Money (cash at end of R1/R2/R3; total mod spend over the campaign)
| | live | G1 | G2 |
|---|---|---|---|
| Story | $5,900 (debt $3,000) / $17,660 / $30,420; $23,580 | $2,092 (debt $2,642) / $14,122 / $25,225; $30,700 | $2,785 (debt $2,285) / $13,405 / $25,250; $32,600 |
| Mixed | $5,050 / $15,632 / $16,102; $62,180 | $5,600 / $27,528 / $44,340; $36,500 | $6,150 / $25,510 / $43,065; $39,700 |
| Hard | $4,550 / $13,998 / $16,922; $67,080 | $5,650 / $29,475 / $52,970; $37,000 | $5,650 / $28,805 / $52,300; $40,200 |
Story cash before the boss: G1 $1,292 / $6,522 / $17,625, G2 $985 / $4,205 / $17,650. Story owns 2 R1 Mk3, 2 (G1) or 3 (G2) R2 Mk3,
and 2 R3 Mk3 at each boss. The just-in-time buyer actually buys its first Mk3 at oh1 in every round (largest gain once it unlocks).

## Recommendation: G2 (2 mandatory grinds, after mat1, before mat2)
- Only G2 makes Mk3 the boss key and nothing earlier: a Mk2-capped story car still clears every non-boss rung (worst 50.6),
  then drops to 41.8/39.6/43.4 at the boss. In G1 the R2 oh1 already fails without Mk3 (45.7).
- Higher story minimums (57.1 in R2) and a higher Mk3 price ($3,000 R2) for the same targets.
- Cost: mixed/hard grind a bit more (hard R2 22 vs 15 live), and grinders end R3 with much more cash ($43k–$52k vs $16k–$17k)
  because Mk1/Mk2 got cheaper and smaller. That cash isn't needed for the finale (arc unchanged); flag for the money pass.

## Open issues to flag
- R1: the story boss sits at L6, so R1 Mk2 has to stop at L2. R1 Mk1/Mk2 end up 203/206 points (stock part 150), so they are nearly the same
  mod. Options: drop R1 Mk2 (Mk1 → Mk3), or let R1 be the one round where Mk3 is only "nice to have".
- Mixed walls move to the top of the 3–6 band (5/6/6).
- STORY_XP_MULT oh1/oh2 cuts are deep in G2 (R2 oh1 0.40, R1 oh2 0.27, R3 oh2 0.30); the 2 grinds hand that XP back earlier.
- Mk1/Mk2 R2–R3 prices drop to 0.6× mods-v1; Desmond's USD wording pass still pending.
