# kid-length-v1 (draft, not live) — Barry 2026-11-14

> Committed 2026-11-14 as a draft (not live). Run on the sim as it was before xp-carry-v1 fix C went live, with fix C patched in memory; on today's live sim, drop the in-memory fix C patch or the catch-up XP is applied twice.

Austin: kid story races (kid1, kid2 in R1–R3) are 20+ turns; only grind races are 10 turns. Base = live mods-v1 +
xp-carry-v1 fix C (carry, catch-up XP 0.75 on kid1/kid2/mat1, R2 boss XP ×1.5). All patches are in memory
(`kidlen.py`, `grid_r.py`, `final.py`); `sim/` is unchanged. Run from `sim/`:
`PYTHONPATH=.:../unapproved/barry/kid-length-v1:../unapproved/barry/xp-carry-v1:../unapproved/barry/mods-v1:../unapproved/barry/skill-points-v1 python3 ../unapproved/barry/kid-length-v1/final.py`

## 1. Where length is set
`equations.py:347 LADDER_TURNS = (10, 10, 20, 20, 20, 20, 30)` (kid1..boss). Read by `progression._walk_round`, `ladder()`,
`at_cap_table()` and the planner (`constants.ts TURNS`). `GRIND_TURNS = 10` is separate and stays 10.
Draft: `LADDER_TURNS = (20, 20, 20, 20, 20, 20, 30)`.
**30 turns:** not recommended anywhere. Kid 20/30 drops story-only R3 kid2 to 49.2; 30/30 drops R2/R3 kid1 to 37.5/29.9
(80/80 story-only). Kids are the easiest rung; at 20 they already match the mature length.
Side effect of 20 turns: the 50 % clear test now also reads the Touge hard track (T3) on kid races (it is only read on
20/30-turn races), so the Touge kid rungs get harder for the walk as well as longer.

## 2. Before / after (story-only, min of district and hardest track, % win)
| Race | 10/10 (base) L · 80/80 | 20/20 no fix | 20/20 + fix K |
|---|---|---|---|
| R1 kid1 | L0 92.0 | 88.0 | 89.9 |
| R1 kid2 | L1 95.5 | 93.1 | 93.1 |
| R2 kid1 | L7 58.7 | **50.8** | 54.9 |
| R2 kid2 | L12 79.0 | 73.7 | 77.1 |
| R3 kid1 | L26 54.1 | **44.3** | 68.6 |
| R3 kid2 | L30 70.7 | 63.3 | 81.7 |

| Check | 10/10 base | 20/20 no fix | 20/20 + fix K |
|---|---|---|---|
| Story 80/80 round min (≥50) | 53.0 / 54.4 / 50.5 | 53.0 / 50.8 / **44.3** | 53.0 / 54.4 / 50.5 |
| Story bosses 80/80 | 53.0 / 57.7 / 55.8 | same | same |
| Story-only other profiles, round min (6080 / 8060 / 6060) | 12.0/14.0/16.9 · 2.8/7.3/2.8 · 0.1/0.7/0.3 | 12.0/14.0/13.3 · 2.8/5.0/1.2 · 0.1/0.7/0.1 | same as base |
| Mixed total grinds | 13 / 13 / 12 | 13 / 13 / 14 | 13 / 13 / 12 |
| Mixed wall (target 3–6) and where | 3 / 3 / 4 at mat1 | **1** / 3 / 5 at kid1 / mat1 / kid1 | 3 / 3 / 4 at mat1 |
| Hard (60/60) total grinds | 13 / 15 / 18 | 13 / 16 / 19 | 13 / 15 / 18 |
| 60/60 at cap (≥30) | 31.6 / 40.1 / 30.2 | same | same |
| 80/80 at cap (90–95) | 94.9 / 91.6 / 92.9 | same | same |
| Kid races at cap, any profile | 88.7–100 | 96.0–100 | ≥96 |
| Arc grinds 60/60 · finale 80/80 F1–F4 | 11/7/7/9 · 81.7/82.7/79.3/81.7 | same | same |
| Story cash end R1/R2/R3 | $5,900 / $13,940 / $26,700 | same | same |
Bosses stay on the hardest track (S1 / W3 / T3) and their r is untouched.

## 3. Fix K (smallest that restores every target)
Lift the kid opponents' target r (weaker kid opponents) only; grids in `grid_r.json`:
| District | live kid1 / kid2 r | fix K | why this size |
|---|---|---|---|
| Street (R1) | 1.200 / 1.159 | **1.205** / 1.159 | +0.005 kid1 puts the mixed wall back at mat1 (3); 0 leaves it at kid1 (1 grind) |
| Wangan (R2) | 1.180 / 1.160 | **1.185 / 1.165** | +0.005 both: story kid1 50.8 → 54.9 and hard grinds back to 15 (16 with kid1 only) |
| Touge (R3) | 1.182 / 1.163 | **1.207 / 1.188** | +0.005 is enough for story-only (50.3); +0.025 is needed to move the mixed wall off kid1 back to mat1 |
Fix K reproduces the base on every target (table above). Alternative **K-lite** (Touge +0.010 only): story R3 kid1 55.1,
mixed 13/13/13 with R3 wall 3 grinds at kid1, hard 13/15/19 — passes 3–6 but changes where the R3 wall sits.
**Grind opponents:** grinds use the kid1 budget. With fix K I held grinds at the live kid1 budget (draft constant:
grind budget = C_ROUND / live kid1 r) so grind odds don't move: worst grind 80/80 story 58.6, mixed 85.6, hard 93.4
(base 58.6 / 85.5 / 93.7). If grinds instead follow the new kid1 budget they get slightly easier (R2 story 58.7 → 63.4).
Story XP change is not needed.
Flag: kid races now run 2 laps but still pay the wild purse ($1,000 × round mult). Unchanged here; money wording is Desmond's.

## 4. Planner page
Canvas 786f1da3… would need `planner-v1/gen_constants.py` re-run: `TURNS` kid 20/20, `TARGET_R` kid values, and
`engine.ts:227` grind odds should use a separate grind budget (live kid1 r) instead of `budget(rnd, 0)`; then
`verify.mjs` against new `py_reference.json`. Not done (another fix is in progress on the page).

---

# Pokémon-style progression (Austin's direction; draft study, `pool.py`, `pool_grid2.py`, `pool_final.py`)
All on the kid-length base above (20/20 + fix K + fix C).

## What the sim already does
- **XP falloff:** a grind pays 0.70 × xp_to_next(L) × taper(levels below cap). In levels per grind: 0.67 at 10 below,
  0.59 at 6, 0.46 at 3, 0.38 at 2, 0.28 at 1, **0 at the cap** (XP past the cap is lost). Same in every round.
  The taper floor (0.20) barely matters because the cap cuts first.
- **Round caps:** hard caps L12 / L29 / L46. Going from cap−6 to the cap costs 14 grinds.
- **Availability:** none. Grinds are unlimited and repeatable; after the boss the cap rises and grinds pay full XP again.
  Nothing makes the player "run out". Grind purse does not taper, so cash farming at the cap is possible in the game rules
  (the walk stops at the cap).
- **Why mixed totals are 13/13/12:** the live mixed walk is scripted to grind to the cap before every boss. The wall is 3/3/4.
  The fewest grinds that keep 60/80 or 80/60 ≥50 % on every race is 10/10/9 and 10/8/11 (joint 10/10/11).
  So 3–6 total per round is not reachable with live grind XP; each grind has to pay more.

## Finite pool tested
One-time grind races open before rung j (pool[j]), closed after the boss. Leftovers are lost. Pool races pay PX × the live grind XP (same
falloff, 0 at the cap) and PAYX × the grind purse. Fallback = repeatable race, FB_XP × grind XP, FB_PAY × grind purse.
"Natural" players: mixed clears every open pool race and uses fallback only if their own next race is under 50 %;
60/60 does the same and also fallback-grinds to the cap before the boss. Story-only plays no grinds.
Pass rule: 6080 and 8060 total 3–6 every round, own win ≥50 % on every race, 60/60 reaches every cap and has ≥30 % on the boss.
128 grid points (pool 4–7 per round, even or front-loaded, PX 1.75–2.5, PAYX 1–2, floor 0.2/0.05): **one passes**,
refined below. The 60/60 boss floor is the binding check: fewer grinds = less cash = fewer mods by the boss (R1 drops to 29.7 at purse ×1).

## Recommended: Pool A
- **6 pool races per round:** 1 at round open, 1 after each of kid1, kid2, mat1, mat2, oh1 wins. Pool XP ×2.5, purse ×2.
- **Fallback:** XP ×0.5, purse ×0.5. Taper floor 0.20 → 0.05.

| Check | live (unlimited) | Pool A |
|---|---|---|
| 60/80 grinds per round | 13 / 13 / 12 (mixed walk) | **6 / 6 / 6** (0 fallback) |
| 80/60 grinds per round | same | **6 / 6 / 6** (0 fallback) |
| 60/80 / 80/60 level at boss | cap | L12 / 29 / 46 (cap) |
| 60/80 boss | 72.4 / 63.0 / 69.2 at cap | 71.0 / 64.1 / 67.6 |
| 80/60 boss | 71.0 / 80.7 / 70.2 at cap | 69.8 / 81.4 / 70.1 |
| Mixed lowest race (60/80 and 80/60) | — | 69.8 / 61.1 / 50.4 |
| 60/60 grinds (pool + fallback) | 13 / 15 / 18 | 7 / 14 / 21 (1 / 8 / 15 fallback) |
| 60/60 reaches cap · boss | yes · 31.6 / 40.1 / 30.2 | yes · 31.6 / 40.1 / 30.3 |
| Story-only 80/80 min | 53.0 / 54.4 / 50.5 | same (no grinds) |
| XP per race near the cap (levels; at 4 / 2 / 1 below) | 0.48 / 0.38 / 0.28 | pool 1.20 / 0.80 / 0.49; fallback 0.24 / 0.16 / **0.10**; 0 at cap |
| 60/60 cash end R1/R2/R3 | $4,550 / $13,998 / $16,922 | $4,275 / $14,355 / $18,394 |
Live "at cap" boss figures for 60/80 and 80/60 are the hardest-track at-cap cells in equations.py.

What it feels like: the pool lands a mixed player at the cap right at the gym. After that the pool is gone and only
fallback races are left, at ½ XP and ½ purse. One level below the cap a fallback race gives 0.10 level, and at the cap it gives 0.
Close variants: fallback 0.25 XP sends 60/60 to 8 / 21 / 36 grinds; 5 pool races per round drop the 60/60 R1 boss to
29.7; front-loading (2 at open, XP ×2.25) leaves 60/80 and 80/60 at L28 for the R2 boss (60/80 56.0).

Caveats:
- The arc and finale still use unlimited live grinds; the pool is not applied there.
- 80/60 R3 thinnest race is 50.4 (same as base).
- The pool keeps grind cash about level with live only because of the ×2 purse.
- If story-only players also clear the pool, they reach the cap like mixed players. "Story-only" would then mean skipping the pool.

## Files
`kidlen.py/.txt/results.json` (10/20/30 length variants), `grid_r.py/.json/.txt` (kid r grid), `final.py/.json/.txt`
(base / no fix / fix K / K-lite + arc + grind odds at live budget), `pool.py` (pool walk; `pool_grid.json` = first grid at
PX 1), `pool_grid2.py/.json/.txt`, `pool_final.py/.json/.txt`.
