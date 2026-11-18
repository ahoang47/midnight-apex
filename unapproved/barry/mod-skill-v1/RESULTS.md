# mod-skill-v1 RESULTS (Barry DRAFT, 2026-11-18, touge-race @ bbdda07)

Every number below comes from the scripts in this folder (results.json, sweep_x.json, sweep_fine.json, debt_check.json,
baseline_live.json). The live comparison column was rerun today from sim/velocity_shift (baseline_live.py), not copied.

## 0. Headline
- **mod_skill reproduces today's curve.** The recommended config is: X = 0.60, a free base setup, overflow spills to the
  next mod, and Touge runs the Wangan PHEE kit. It matches today's live campaign within 0.1-1.0 point on every
  headline number (table 2). The hard-player grind counts were not fitted and still land at 13/14/18 against live 13/15/18.
- **Recommended own-stat share: X = 60 %.** X = 0.52 is the first value where no single kit works in both Street and
  Wangan, and X = 0.60 is the first where a wrong mono-kit drops the Wangan boss's 60/60 below the 30 % floor (29.1 %).
- **Austin's strict rule ("one race's XP into ONE mod", overflow lost) has a cost.** It leaves the story-only player's
  lows at 34.6 % (R2) and 20.3 % (R3), against live 54.4 / 50.5. A boss's XP lump can't fit in one mod, and the
  Street→Wangan kit swap strands 133 points.
- **At list Mk1 prices cash never gates power; XP does.** Prices up to 2x Mk1 are safe. At 3x, the Sabine debt makes the
  R1 boss unwinnable for story-only (4.3 %).

## 1. Recommended config and why
| Piece | Choice | Why (numbers in the tables below) |
|---|---|---|
| Base 3000 points | Fixed total, free setup per race inside 25-50 % of 3000 | Locked street base: Wangan is 14.3-18.6 share points off tune, and its boss 80/80 falls from 90.6 to 72.5-80.4. Locked even base: Street is 9.2-14.2 points off. |
| Ceiling per mod (earned points over stock) | R1 133 / R2 261 / R3 407 | 3000 + 4 x ceiling = 3532 / 4044 / 4628 points. Live cap power is 353.1 / 404.19 / 462.51; the walk caps power at those values. |
| Own-stat share X | **0.60** | See section 3 |
| XP assignment | One picked mod; overflow spills to the next greedy pick | The strict rule loses up to 111 story points at a boss and drops story lows to 34.6 / 20.3 |
| Kits | Free pick of mod types (4 slots). Street PPHE, Wangan PHEE, Touge **PHEE** | PHEE is on tune in Touge at X = 0.60. Keeping it avoids stranding the Wangan E2 points (Touge story low 42.3 with PPHE vs 50.5 with PHEE). |
| Prices | Keep Mk1 list as the per-tier price ($150 / $700 / $1,200); never above 2x in R1 while the debt is open | Price sweep and debt check |
| Retune (20 %) | Not needed | Pattern-kit tune distance stays 0.0 in every walk, and round-entry distance is 0.0 for X ≤ 0.74 |

## 2. Side by side with live (verified by rerunning the live code)
The rerun reproduced every number in the brief except one: R3 60/60 at cap is 30.2 in boss_check_at_cap and 30.3 in the walk.

| Metric | Live (rerun) | mod_skill recommended | strict |
|---|---|---|---|
| Story-only 80/80 low | 53.0 / 54.4 / 50.5 | 52.9 / 54.2 / 50.5 | 52.9 / 34.6 / 20.3 |
| Story-only boss 80/80 | 53.0 / 57.7 / 55.8 | 52.9 / 57.7 / 55.9 | 52.9 / 57.7 / 55.9 |
| 60/60 boss at cap | 31.6 / 40.1 / 30.2 | 31.6 / 39.5 / 30.3 | same |
| 80/80 boss at cap | 94.9 / 91.6 / 92.9 | 94.9 / 90.6 / 92.9 | same |
| Mixed grinds | 13 / 13 / 12 | 13 / 13 / 12 (fitted) | 13 / 14 / 12 |
| Hard grinds | 13 / 15 / 18 | 13 / 14 / 18 (not fitted) | 14 / 14 / 18 |
| Story-only cash / debt at round end | $5,900 / $13,940 / $26,700; debt $3,000 after R1 | $6,400 / $24,160 / $47,320; debt $3,000 after R1 | same as recommended |

The R2 cap gap (40.1 → 39.5 and 91.6 → 90.6) comes from the build. Live is limited by the retune to a 26.2 % POW share
at the R2 cap. mod_skill reaches the exact Wangan tune of 25 %.

## 3. Own-stat share X: the sweep
"Works" means the round's kit reaches its district tune exactly inside the 25-50 % band, mod type still matters, and no
retune is needed. With the setup base, every X up to 1.00 reaches the tune with the pattern kit at the cap. What X
changes is how much the mod TYPE matters, plus round entry:

| X | Kits on tune S / W / T (of 15) | Kits on tune in both Street and Wangan | Wangan boss 60/60 / 80/80, right kit vs PPPP | Round entry off tune R2 / R3 |
|---|---|---|---|---|
| 0.34 | 9 / 9 / 14 | – | 39.5 / 90.6 vs 40.6 / 92.5 | 0 / 0 |
| 0.50 | 9 / 9 / 11 | **6** (one kit fits everything) | 39.5 / 90.6 vs 37.3 / 92.2 | 0 / 0 |
| 0.52 | 5 / 4 / 11 | 0 | – | 0 / 0 |
| **0.60** | **4 / 4 / 6** | **0** | 39.5 / 90.6 vs **29.1 / 87.8** | **0 / 0** |
| 0.70 | 4 / 4 / 6 | 0 | 39.5 / 90.6 vs 23.5 / 84.0 | 0 / 0 |
| 0.76 | 4 / 4 / 6 | 0 | 39.5 / 90.6 vs 21.1 / 81.9 | 0.08 / 0.07 |
| 0.80 | 4 / 4 / 4 | 0 | 39.5 / 90.6 vs 19.5 / 80.5 | 0.39 / 0.34 |
| 1.00 | 4 / 4 / 3 | 0 | 39.5 / 90.6 vs 10.7 / 70.9 | 1.96 / 1.72 |

Why X = 0.60 and not its neighbours:
- **0.50 and below:** 6 kits (PPHE, PPEE, PHHE, PHEE, HHEE, PPHH) are on tune in both Street and Wangan, so one kit
  does everything and the mod type barely matters. A wrong kit costs at most 2.2 points of 60/60. At 0.34-0.40 a POW-heavy
  wrong kit even scores *higher* on the Wangan 80/80 cell (92.5-93.8 vs 90.6).
- **0.52-0.56:** the kit sets are already split, but a wrong kit still costs only 3.8-7.1 points of 60/60. Its 60/60 stays
  above the 30 % floor (35.7 at 0.52, 32.4 at 0.56).
- **0.60:** at the cap, Street and Wangan each have 4 kits on tune, with no kit in common, and Touge has 6. A wrong
  mono-kit drops the Wangan boss to 29.1 / 87.8, below the 60/60 floor, so the mod type matters. Each mod keeps a 40 % free
  pool, and round entry stays exactly on tune.
- **0.70:** the same kit sets as 0.60 but harsher. A wrong kit costs 16 points of 60/60, and only 30 % of each mod is free,
  which leaves less room for varied mods.
- **≥ 0.76:** carrying the old kit into the next round no longer reaches the tune. That would need retune-style slack again,
  and at 0.80 Touge also drops from 6 kits to 4.
- **Base option:** with any locked base, no X works (Wangan is 14-19 points off with the street base, Street 9-14 with the even base).

Valid kits at X = 0.60 (at the cap):
- Street: PPPP, PPPH, PPPE, PPHE
- Wangan: PHEE, PEEE, HEEE, EEEE
- Touge: PPPP, PPPH, PPPE, PPHE, PPEE, PHEE

## 4. Ceilings, XP table, prices
**Ceilings** (earned points per mod above the 150 stock part): **R1 133, R2 261, R3 407.** A full kit is 3532 / 4044 /
4628 points, which is the live cap power. The derivation for the pre-finale arc and finale, if carried on (not walked), gives:
- F1: 579.8 per mod
- F2: 747.9 per mod
- F3: 941.8 per mod
- F4: 1243.9 per mod

The stock 3000 shrinks from 56 % of the car at F1 to 38 % at F4, so the setup base matters less and less there.

**Story XP table (points into mods, recommended config)**, rungs kid1 / kid2 / mat1 / mat2 / oh1 / oh2 / boss:

| Round | kid1 | kid2 | mat1 | mat2 | oh1 | oh2 | boss | Grind win |
|---|---|---|---|---|---|---|---|---|
| R1 | 145.0 | 115.8 | 26.9 | 25.1 | 27.0 | 26.8 | 154.3 | 13 |
| R2 | 96.6 | 72.1 | 67.9 | 60.1 | 29.5 | 30.6 | 92.2 | 15 |
| R3 | 99.6 | 102.3 | 52.2 | 69.5 | 69.6 | 35.0 | 70.5 | 14 |

On top of the table, a player entering a round below the previous cap gets the live catch-up: 0.75 x shortfall, split 40/40/20 over kid1/kid2/mat1.
Kid rungs pay big because the live level curve front-loads power: early levels are cheap. A grind win is worth 9-16 % of that round's kid1 story win.

Strict-rule table (for reference):
- R1: 133.0 / 127.8 / 26.9 / 25.1 / 27.0 / 26.8 / 80.9
- R2: 147.9 / 50.2 / 56.8 / 60.1 / 29.5 / 30.7 / 64.2
- R3: 177.6 / 68.9 / 35.4 / 69.6 / 69.6 / 35.0 / 53.4
- Grind: 15 / 19 / 22

Even with these tables it falls short of the live story curve at R1 kid1 (12 points), R1 boss (73.4), R2 boss (111.4) and R3 boss (16.7).

**Prices:** the live Mk1 list is kept as the per-tier price: $150 / $700 / $1,200 per mod, with wholesale -20 % in R2-R3.
A kit costs $600 / $2,840 / $6,680 in total, all bought on time. Cash ends R3 at $47,320 (story) and $71,602 (mixed),
which is a surplus. Going up to 2x keeps every boss number (story R1 boss 47.9 vs 52.9). 3x breaks R1:
- story R1 boss 4.3 %
- mixed R1 grinds 24
Mk3 or spend-matched prices ($1,000-$11,075 per tier) leave story-only at 0.2-3.0 % on bosses.

## 5. Risks
- **Cash as the only gate:** under these rules cash is NOT the gate; XP is. Cash only unlocks the tier ceiling, and at
  ≤2x Mk1 the player can always afford it. Above that, R1 becomes a cash wall:
  - at 3x Mk1, the story-only R1 boss is 4.3 % and mixed needs 24 R1 grinds (13 today)
  - at Mk3 list prices, 27 grinds
  To make cash matter without walls, it needs things to buy beyond the tier: more mods per tier with different ceilings,
  and aero (section 6).
- **The debt slows early power:** with the debt on, the highest R1 price that costs nothing is 2x Mk1. With the debt
  off, it is 3x (debt_check.json: story R1 boss 52.9 at 3x with no debt vs 4.3 with it). The 65 % share bites in R1,
  where tier-1 purchases happen.
- **Betting as a power shortcut:** betting (after R2) can't buy power here. Story-only already has $24,160 entering R3,
  the R3 tier kit costs $3,840 after wholesale, and the ceiling is fixed per tier. Betting would only matter if prices rise
  past the cash wall or the catalog adds mods above the round ceiling. Keep the ceilings tied to the round, so money can
  never buy past the cap.
- **The Pokémon "XP-limited grinding" feel:** it is kept. Grinding still fills toward a hard cap (the tier ceiling, which
  is today's level cap), XP past it is lost (83-158 points per round for mixed), and grind counts match live. What changes:
  - power is per mod, so the player chooses which mod grows
  - a district change can strand points: Street→Wangan strands 133 points with the pattern kits, so the mixed player
    grinds 7 at R2 kid1
  - the strict one-mod rule wastes boss XP
- **Off-tune pricing caveat:** only the POW share is modelled. HAN-heavy wrong kits look free in the table, which they are not.

## 6. Growing the catalog (not simulated)
Mod type is now a real choice: 4 or 6 valid kits per district, with no Street/Wangan overlap. The catalog can widen without
breaking the curve, as long as every mod's tier ceiling stays at or under the round ceiling (133 / 261 / 407). Ways to vary mods:
- **Own-stat floors:** a "specialist" at X = 0.80 vs a "flex" mod at X = 0.60. Keep the minimum at 0.60.
- **Ceiling vs price:** a cheap mod with a lower ceiling, such as 80 % of the tier ceiling.
- **Fill rate:** a mod that takes 1.25x XP per point but has a perk.
- **District affinity:** a mod with a bonus own-stat share in one district.
Each of these needs one walk to confirm before it is adopted.

---
## Full tables (generated by make_tables.py)

#### story (80/80 criterion, never grinds)

| Round | Rung | Grinds before | Car points | r | 60/60 | 60/80 | 80/60 | 80/80 | Cash before | Debt before | Tiers (kit) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 street | kid1 | 0 | 3000 | 1.020 | 24.3 | 64.3 | 59.0 | 92.0 | $0 | $16,000 | P0P0H0E0 |
| R1 street | kid2 | 0 | 3145 | 1.032 | 40.2 | 74.7 | 76.2 | 95.5 | $50 | $15,350 | P1P1H0E0 |
| R1 street | mat1 | 0 | 3261 | 1.011 | 5.7 | 46.9 | 30.2 | 83.3 | $100 | $14,700 | P1P1H1E1 |
| R1 street | mat2 | 0 | 3288 | 0.997 | 0.6 | 28.7 | 10.0 | 72.2 | $975 | $13,075 | P1P1H1E1 |
| R1 street | oh1 | 0 | 3313 | 0.999 | 0.8 | 30.9 | 11.8 | 74.4 | $1,850 | $11,450 | P1P1H1E1 |
| R1 street | oh2 | 0 | 3340 | 1.001 | 1.1 | 32.7 | 13.6 | 75.8 | $2,725 | $9,825 | P1P1H1E1 |
| R1 street | boss | 0 | 3367 | 0.995 | 0.2 | 12.0 | 3.0 | 52.9 | $3,600 | $8,200 | P1P1H1E1 |
| R2 wangan | kid1 | 0 | 3393 | 0.990 | 2.4 | 27.9 | 10.3 | 59.1 | $4,160 | $3,000 | P2H2E2E2 |
| R2 wangan | kid2 | 0 | 3531 | 1.013 | 13.7 | 47.4 | 38.1 | 78.7 | $4,562 | $2,252 | P2H2E2E2 |
| R2 wangan | mat1 | 0 | 3645 | 1.001 | 3.6 | 23.8 | 12.1 | 60.1 | $4,965 | $1,505 | P2H2E2E2 |
| R2 wangan | mat2 | 0 | 3733 | 0.997 | 2.9 | 21.1 | 9.5 | 56.8 | $6,335 | $0 | P2H2E2E2 |
| R2 wangan | oh1 | 0 | 3793 | 0.995 | 2.4 | 19.1 | 7.8 | 54.2 | $9,210 | $0 | P2H2E2E2 |
| R2 wangan | oh2 | 0 | 3823 | 0.998 | 2.9 | 21.3 | 9.7 | 57.1 | $12,085 | $0 | P2H2E2E2 |
| R2 wangan | boss | 0 | 3853 | 1.006 | 0.7 | 13.8 | 7.3 | 57.7 | $14,960 | $0 | P2H2E2E2 |
| R3 touge | kid1 | 0 | 3946 | 1.008 | 1.4 | 23.8 | 7.9 | 54.0 | $20,320 | $0 | P3H3E3E3 |
| R3 touge | kid2 | 0 | 4074 | 1.024 | 7.6 | 37.4 | 24.5 | 70.7 | $21,670 | $0 | P3H3E3E3 |
| R3 touge | mat1 | 0 | 4205 | 1.028 | 4.0 | 32.4 | 16.9 | 68.2 | $23,020 | $0 | P3H3E3E3 |
| R3 touge | mat2 | 0 | 4272 | 1.012 | 0.4 | 17.3 | 3.1 | 51.0 | $26,395 | $0 | P3H3E3E3 |
| R3 touge | oh1 | 0 | 4341 | 1.012 | 0.3 | 16.9 | 2.8 | 50.5 | $29,770 | $0 | P3H3E3E3 |
| R3 touge | oh2 | 0 | 4411 | 1.021 | 1.4 | 24.8 | 8.4 | 60.3 | $33,145 | $0 | P3H3E3E3 |
| R3 touge | boss | 0 | 4446 | 1.029 | 1.5 | 17.7 | 9.1 | 55.9 | $36,520 | $0 | P3H3E3E3 |

| Round | Grinds | End points | End cash | Debt left | Spent on mods | XP lost past ceilings |
|---|---|---|---|---|---|---|
| R1 | 0 | 3521 | $6,400 | $3,000 | $600 | 0.0 |
| R2 | 0 | 3946 | $24,160 | $0 | $2,840 | 0.0 |
| R3 | 0 | 4517 | $47,320 | $0 | $6,680 | 0.0 |

#### mixed (grinds when 60/80 or 80/60 < 50 %, then to cap before the boss)

| Round | Rung | Grinds before | Car points | r | 60/60 | 60/80 | 80/60 | 80/80 | Cash before | Debt before | Tiers (kit) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 street | kid1 | 0 | 3000 | 1.020 | 24.3 | 64.3 | 59.0 | 92.0 | $0 | $16,000 | P0P0H0E0 |
| R1 street | kid2 | 0 | 3145 | 1.032 | 40.2 | 74.7 | 76.2 | 95.5 | $50 | $15,350 | P1P1H0E0 |
| R1 street | mat1 | 3 | 3300 | 1.023 | 18.0 | 62.1 | 53.5 | 89.6 | $678 | $13,628 | P1P1H1E1 |
| R1 street | mat2 | 0 | 3327 | 1.009 | 4.3 | 44.0 | 26.4 | 81.9 | $1,552 | $12,002 | P1P1H1E1 |
| R1 street | oh1 | 0 | 3352 | 1.011 | 5.5 | 46.5 | 29.7 | 83.1 | $2,428 | $10,378 | P1P1H1E1 |
| R1 street | oh2 | 0 | 3379 | 1.012 | 6.8 | 48.4 | 32.6 | 83.9 | $3,302 | $8,752 | P1P1H1E1 |
| R1 street | boss | 10 | 3532 | 1.044 | 31.6 | 72.4 | 71.0 | 94.9 | $6,102 | $3,552 | P1P1H1E1 |
| R2 wangan | kid1 | 7 | 3504 | 1.023 | 22.7 | 55.6 | 52.4 | 83.7 | $12,738 | $0 | P2H2E2E2 |
| R2 wangan | kid2 | 0 | 3640 | 1.044 | 49.1 | 72.3 | 79.8 | 91.7 | $13,888 | $0 | P2H2E2E2 |
| R2 wangan | mat1 | 0 | 3752 | 1.030 | 25.5 | 56.5 | 61.3 | 86.7 | $15,038 | $0 | P2H2E2E2 |
| R2 wangan | mat2 | 0 | 3840 | 1.026 | 20.9 | 51.2 | 52.9 | 83.5 | $17,912 | $0 | P2H2E2E2 |
| R2 wangan | oh1 | 0 | 3900 | 1.022 | 17.7 | 47.2 | 46.6 | 81.1 | $20,788 | $0 | P2H2E2E2 |
| R2 wangan | oh2 | 0 | 3929 | 1.025 | 20.6 | 50.7 | 52.2 | 83.2 | $23,662 | $0 | P2H2E2E2 |
| R2 wangan | boss | 6 | 4044 | 1.055 | 39.5 | 62.8 | 80.6 | 90.6 | $30,332 | $0 | P2H2E2E2 |
| R3 touge | kid1 | 0 | 4044 | 1.033 | 13.6 | 45.4 | 35.5 | 76.5 | $35,692 | $0 | P3H3E3E3 |
| R3 touge | kid2 | 0 | 4144 | 1.041 | 19.8 | 53.0 | 46.7 | 81.5 | $37,042 | $0 | P3H3E3E3 |
| R3 touge | mat1 | 5 | 4316 | 1.056 | 25.1 | 57.4 | 52.0 | 86.5 | $42,105 | $0 | P3H3E3E3 |
| R3 touge | mat2 | 0 | 4368 | 1.035 | 8.4 | 39.3 | 26.7 | 74.0 | $45,480 | $0 | P3H3E3E3 |
| R3 touge | oh1 | 0 | 4438 | 1.034 | 7.9 | 38.5 | 25.5 | 73.3 | $48,855 | $0 | P3H3E3E3 |
| R3 touge | oh2 | 0 | 4507 | 1.043 | 14.8 | 46.9 | 37.9 | 79.8 | $52,230 | $0 | P3H3E3E3 |
| R3 touge | boss | 7 | 4628 | 1.070 | 30.3 | 67.6 | 70.1 | 92.9 | $60,802 | $0 | P3H3E3E3 |

| Round | Grinds | End points | End cash | Debt left | Spent on mods | XP lost past ceilings |
|---|---|---|---|---|---|---|
| R1 | 13 | 3532 | $10,550 | $0 | $600 | 157.9 |
| R2 | 13 | 4044 | $39,532 | $0 | $2,840 | 98.0 |
| R3 | 12 | 4628 | $71,602 | $0 | $6,680 | 82.7 |

#### hard (grinds when 60/60 < 50 %, then to cap before the boss)

| Round | Rung | Grinds before | Car points | r | 60/60 | 60/80 | 80/60 | 80/80 | Cash before | Debt before | Tiers (kit) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 street | kid1 | 5 | 3065 | 1.042 | 51.2 | 81.1 | 85.4 | 97.4 | $362 | $14,212 | P1P1H1E1 |
| R1 street | kid2 | 0 | 3210 | 1.054 | 63.7 | 86.6 | 91.7 | 98.6 | $712 | $13,562 | P1P1H1E1 |
| R1 street | mat1 | 3 | 3365 | 1.044 | 51.5 | 81.4 | 81.4 | 95.9 | $1,640 | $11,840 | P1P1H1E1 |
| R1 street | mat2 | 4 | 3444 | 1.044 | 53.3 | 82.1 | 82.4 | 96.1 | $3,285 | $8,785 | P1P1H1E1 |
| R1 street | oh1 | 0 | 3469 | 1.046 | 56.3 | 83.4 | 84.0 | 96.4 | $4,160 | $7,160 | P1P1H1E1 |
| R1 street | oh2 | 0 | 3496 | 1.048 | 58.4 | 84.3 | 85.2 | 96.7 | $5,035 | $5,535 | P1P1H1E1 |
| R1 street | boss | 1 | 3532 | 1.044 | 31.6 | 72.4 | 71.0 | 94.9 | $6,102 | $3,552 | P1P1H1E1 |
| R2 wangan | kid1 | 13 | 3594 | 1.049 | 54.1 | 75.2 | 83.9 | 92.6 | $16,532 | $0 | P2H2E2E2 |
| R2 wangan | kid2 | 0 | 3730 | 1.070 | 67.3 | 83.8 | 91.0 | 95.8 | $17,682 | $0 | P2H2E2E2 |
| R2 wangan | mat1 | 0 | 3842 | 1.055 | 59.0 | 78.8 | 87.5 | 95.1 | $18,832 | $0 | P2H2E2E2 |
| R2 wangan | mat2 | 0 | 3930 | 1.050 | 54.7 | 75.4 | 85.0 | 94.3 | $21,708 | $0 | P2H2E2E2 |
| R2 wangan | oh1 | 1 | 4005 | 1.050 | 55.0 | 75.6 | 85.2 | 94.4 | $25,215 | $0 | P2H2E2E2 |
| R2 wangan | oh2 | 0 | 4034 | 1.053 | 57.3 | 77.4 | 86.5 | 94.8 | $28,090 | $0 | P2H2E2E2 |
| R2 wangan | boss | 0 | 4044 | 1.055 | 39.5 | 62.8 | 80.6 | 90.6 | $30,965 | $0 | P2H2E2E2 |
| R3 touge | kid1 | 8 | 4156 | 1.061 | 35.1 | 66.2 | 63.5 | 88.2 | $42,265 | $0 | P3H3E3E3 |
| R3 touge | kid2 | 0 | 4256 | 1.069 | 44.8 | 74.5 | 78.1 | 94.2 | $43,615 | $0 | P3H3E3E3 |
| R3 touge | mat1 | 3 | 4400 | 1.076 | 50.1 | 78.5 | 81.0 | 95.9 | $47,192 | $0 | P3H3E3E3 |
| R3 touge | mat2 | 7 | 4550 | 1.078 | 52.1 | 79.9 | 82.2 | 96.2 | $55,765 | $0 | P3H3E3E3 |
| R3 touge | oh1 | 0 | 4620 | 1.077 | 50.8 | 79.0 | 81.4 | 96.0 | $59,140 | $0 | P3H3E3E3 |
| R3 touge | oh2 | 0 | 4628 | 1.070 | 44.8 | 74.8 | 78.0 | 95.2 | $62,515 | $0 | P3H3E3E3 |
| R3 touge | boss | 0 | 4628 | 1.070 | 30.3 | 67.6 | 70.1 | 92.9 | $65,890 | $0 | P3H3E3E3 |

| Round | Grinds | End points | End cash | Debt left | Spent on mods | XP lost past ceilings |
|---|---|---|---|---|---|---|
| R1 | 13 | 3532 | $10,550 | $0 | $600 | 157.9 |
| R2 | 14 | 4044 | $40,165 | $0 | $2,840 | 113.0 |
| R3 | 18 | 4628 | $76,690 | $0 | $6,680 | 166.7 |

#### Side by side with live

| Metric | Live (rerun today) | mod_skill recommended | strict (1 mod, pattern kits) |
|---|---|---|---|
| Story-only 80/80 low | 53.0 / 54.4 / 50.5 | 52.9 / 54.2 / 50.5 | 52.9 / 34.6 / 20.3 |
| Story-only boss 80/80 | 53.0 / 57.7 / 55.8 | 52.9 / 57.7 / 55.9 | 52.9 / 57.7 / 55.9 |
| 60/60 boss at cap | 31.6 / 40.1 / 30.2 | 31.6 / 39.5 / 30.3 | 31.6 / 39.5 / 30.3 |
| 80/80 boss at cap | 94.9 / 91.6 / 92.9 | 94.9 / 90.6 / 92.9 | 94.9 / 90.6 / 92.9 |
| Mixed grinds | 13 / 13 / 12 | 13 / 13 / 12 | 13 / 14 / 12 |
| Hard grinds | 13 / 15 / 18 | 13 / 14 / 18 | 14 / 14 / 18 |
| Story-only cash at round end | $5,900 / $13,940 / $26,700 | $6,400 / $24,160 / $47,320 | $6,400 / $24,160 / $47,320 |
| Story-only debt at round end | $3,000 / $0 / $0 | $3,000 / $0 / $0 | $3,000 / $0 / $0 |

#### Variant configs (story low / story boss 80/80; mixed and hard grinds)

| Config | Story 80/80 low | Story boss 80/80 | Mixed grinds | Hard grinds | Mixed XP lost |
|---|---|---|---|---|---|
| strict | 52.9 / 34.6 / 20.3 | 52.9 / 57.7 / 55.9 | 13 / 14 / 12 | 14 / 14 / 18 | 110.5 / 159.4 / 155.9 |
| spill | 52.9 / 54.2 / 42.3 | 52.9 / 57.7 / 55.9 | 13 / 13 / 12 | 13 / 14 / 18 | 157.9 / 196.4 / 81.8 |
| touge_phee | 52.9 / 34.6 / 44.2 | 52.9 / 57.7 / 55.9 | 13 / 14 / 12 | 14 / 14 / 20 | 110.5 / 159.4 / 84.7 |
| recommended | 52.9 / 54.2 / 50.5 | 52.9 / 57.7 / 55.9 | 13 / 13 / 12 | 13 / 14 / 18 | 157.9 / 98.0 / 82.7 |

#### X sweep (at each round's cap, all 4 mods at the tier ceiling)

| Base | X | Street pattern off-tune (pts) | Wangan pattern off-tune | Touge pattern off-tune | Kits on tune S/W/T (of 15) | Round-entry off-tune R2/R3 | Wangan boss 60/60 / 80/80, pattern vs PPPP |
|---|---|---|---|---|---|---|---|
| B1_locked_street | 0.34 | 0.0 | 14.29 (outside 25-50 band) | 0.0 | 9/0/14 | 20.46 / 0.0 | 19.4 / 80.4 vs 8.9 / 68.3 |
| B1_locked_street | 0.40 | 0.0 | 14.67 (outside 25-50 band) | 0.0 | 9/0/10 | 20.7 / 0.0 | 18.8 / 79.8 vs 7.7 / 65.9 |
| B1_locked_street | 0.50 | 0.0 | 15.32 (outside 25-50 band) | 0.0 | 9/0/8 | 21.09 / 0.0 | 17.7 / 78.8 vs 5.8 / 62.0 |
| B1_locked_street | 0.60 | 0.0 | 15.96 (outside 25-50 band) | 0.0 | 3/0/3 | 21.48 / 0.0 | 16.6 / 77.5 vs 5.8 / 62.0 |
| B1_locked_street | 0.70 | 0.0 | 16.61 (outside 25-50 band) | 0.0 | 1/0/3 | 21.87 / 0.0 | 15.5 / 76.2 vs 5.8 / 62.0 |
| B1_locked_street | 0.80 | 0.0 | 17.26 (outside 25-50 band) | 1.48 | 1/0/0 | 22.46 / 0.52 | 14.3 / 75.0 vs 5.8 / 62.0 |
| B1_locked_street | 1.00 | 0.0 | 18.55 | 5.0 | 1/0/0 | 24.02 / 3.28 | 12.1 / 72.5 vs 5.8 / 62.0 |
| B2_locked_even | 0.34 | 9.19 | 3.84 | 0.0 | 0/1/6 | 11.5 / 3.78 | 40.4 / 92.2 vs 30.8 / 88.7 |
| B2_locked_even | 0.40 | 9.64 | 4.62 | 0.13 | 0/1/6 | 11.97 / 4.19 | 40.6 / 92.5 vs 26.0 / 86.1 |
| B2_locked_even | 0.50 | 10.39 | 5.91 | 1.0 | 0/1/2 | 12.75 / 4.88 | 41.0 / 93.1 vs 21.9 / 82.6 |
| B2_locked_even | 0.60 | 11.14 | 7.2 | 1.88 | 0/1/2 | 13.54 / 6.15 | 41.3 / 93.6 vs 17.9 / 79.0 |
| B2_locked_even | 0.70 | 11.9 | 8.49 | 2.76 | 0/1/1 | 14.32 / 7.53 | 41.6 / 94.1 vs 13.4 / 73.9 |
| B2_locked_even | 0.80 | 12.65 | 9.78 | 3.64 | 0/1/1 | 15.1 / 8.91 | 41.9 / 94.7 vs 9.3 / 69.0 |
| B2_locked_even | 1.00 | 14.16 | 12.36 | 5.8 | 0/0/0 | 16.67 / 11.67 | 38.2 / 92.7 vs 5.8 / 62.0 |
| B3_setup | 0.34 | 0.0 | 0.0 | 0.0 | 9/9/14 | 0.0 / 0.0 | 39.5 / 90.6 vs 40.6 / 92.5 |
| B3_setup | 0.40 | 0.0 | 0.0 | 0.0 | 9/9/11 | 0.0 / 0.0 | 39.5 / 90.6 vs 41.4 / 93.8 |
| B3_setup | 0.50 | 0.0 | 0.0 | 0.0 | 9/9/11 | 0.0 / 0.0 | 39.5 / 90.6 vs 37.3 / 92.2 |
| B3_setup | 0.60 | 0.0 | 0.0 | 0.0 | 4/4/6 | 0.0 / 0.0 | 39.5 / 90.6 vs 29.1 / 87.8 |
| B3_setup | 0.70 | 0.0 | 0.0 | 0.0 | 4/4/6 | 0.0 / 0.0 | 39.5 / 90.6 vs 23.5 / 84.0 |
| B3_setup | 0.80 | 0.0 | 0.0 | 0.0 | 4/4/4 | 0.39 / 0.34 | 39.5 / 90.6 vs 19.5 / 80.5 |
| B3_setup | 1.00 | 0.0 | 0.0 | 0.0 | 4/4/3 | 1.96 / 1.72 | 39.5 / 90.6 vs 10.7 / 70.9 |

#### Fine sweep, B3 setup base

| X | Kits on tune Street | Wangan | Touge | Kits on tune in BOTH Street and Wangan |
|---|---|---|---|---|
| 0.50 | 9 | 9 | 11 | 6 |
| 0.52 | 5 | 4 | 11 | 0 |
| 0.54 | 4 | 4 | 6 | 0 |
| 0.56 | 4 | 4 | 6 | 0 |
| 0.58 | 4 | 4 | 6 | 0 |
| 0.60 | 4 | 4 | 6 | 0 |
| 0.62 | 4 | 4 | 6 | 0 |
| 0.64 | 4 | 4 | 6 | 0 |
| 0.66 | 4 | 4 | 6 | 0 |
| 0.68 | 4 | 4 | 6 | 0 |
| 0.70 | 4 | 4 | 6 | 0 |
| 0.72 | 4 | 4 | 6 | 0 |
| 0.74 | 4 | 4 | 6 | 0 |
| 0.76 | 4 | 4 | 6 | 0 |
| 0.78 | 4 | 4 | 6 | 0 |
| 0.80 | 4 | 4 | 4 | 0 |

#### Price sweep (recommended config, XP fixed; story-only 80/80 low/boss and rungs raced on a lagging tier)

| Prices R1/R2/R3 per tier | Story R1 low/boss | Story R2 low/boss | Story R3 low/boss | Story rungs on old tier R1/R2/R3 | Mixed grinds | Hard grinds |
|---|---|---|---|---|---|---|
| mk1_x1 ($150 / $700 / $1,200) | 52.9 / 52.9 | 54.2 / 57.7 | 50.5 / 55.9 | 2 / 0 / 0 | 13 / 13 / 12 | 13 / 14 / 18 |
| mk1_x2 ($300 / $1,400 / $2,400) | 47.9 / 47.9 | 54.2 / 57.7 | 50.5 / 55.9 | 3 / 0 / 0 | 14 / 13 / 12 | 14 / 14 / 18 |
| mk1_x3 ($450 / $2,100 / $3,600) | 4.3 / 4.3 | 28.0 / 48.6 | 45.9 / 54.1 | 4 / 3 / 0 | 24 / 13 / 12 | 15 / 14 / 18 |
| mk1_x4 ($600 / $2,800 / $4,800) | 4.3 / 4.3 | 11.2 / 44.3 | 41.6 / 53.1 | 4 / 4 / 0 | 25 / 13 / 12 | 16 / 14 / 18 |
| mk1_x6 ($900 / $4,200 / $7,200) | 0.4 / 0.4 | 1.9 / 1.9 | 3.0 / 40.9 | 6 / 6 / 6 | 26 / 13 / 12 | 23 / 14 / 18 |
| mk1_x8 ($1,200 / $5,600 / $9,600) | 0.4 / 0.4 | 0.8 / 0.8 | 0.2 / 15.1 | 7 / 7 / 7 | 28 / 13 / 12 | 28 / 14 / 18 |
| mk3_list ($1,000 / $5,000 / $8,000) | 0.4 / 0.4 | 1.9 / 1.9 | 3.0 / 40.9 | 6 / 7 / 7 | 27 / 13 / 12 | 24 / 14 / 18 |
| spend_matched ($1,525 / $6,450 / $11,075) | 0.4 / 0.4 | 0.8 / 0.8 | 0.2 / 2.1 | 7 / 7 / 7 | 30 / 13 / 12 | 33 / 14 / 18 |
