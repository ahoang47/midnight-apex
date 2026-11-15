# mods-v1 — mod catalog (final draft for Austin's pick, Barry, 2026-11-14)

Not approved for live, not committed. Live `sim/` untouched. Mods have IDs only (no display names yet):
`MOD_<R1|R2|R3|ARC>_<POW|HAN|EN>_<MK1..MK3|MYTH1..MYTH4>`, aero versions `<ID>_AERO`.

**Configuration (Austin 2026-11-14):** 4 slots · canon staging (all Mk1 at round open, Mk2 after mat1, Mk3 after mat2;
arc Myth tiers after P1 / F1 / F2 / F3) · aspire Mk3 prices (R2 $5,000, R3 $8,000). Full record: `DECISION.md`.
Go-live plan: `GO_LIVE.md`.

Files: `catalog_final.json` (the 39 mods), `catalog.py` (catalog + garage/buyer), `catalog_walk.py` (R1–R3),
`catalog_arc.py` (arc + finale via the draft econ-v1 walker), `catalog_report.py` → `catalog.json` /
`catalog_results.json` / `catalog_results.txt` (all explored variants; the pick is key `final_4`), `final_tables.py` →
`final_tables.md` (per-rung money and gear for every walk).
Run from `sim/`: `PYTHONPATH=.:../unapproved/barry/skill-points-v1:../unapproved/barry/mods-v1 python3 ../unapproved/barry/mods-v1/catalog_report.py && python3 ../unapproved/barry/mods-v1/final_tables.py > ../unapproved/barry/mods-v1/final_tables.md`

## Rules
- Each mod boosts one fixed stat by fixed points and never changes or levels. Rebalancing = buy and equip new mods + the 20 % retune. At most one aero (`_AERO`, 1.75× price, unlocks after the R1 boss).
- Car points = SP + slot points, capped at min(round / finale-step ceiling, 1.3375 × SP) (= live 1.07 × P). An empty slot holds a stock part worth 150 points (600 / 4), so SP + 600 = the live stock car at L0.
- Points per Mk = ceil(live mod gap at the "fills through" level / 4). Wholesale −20 % on R1–R3 mods during R2–R3 (live rule; never ARC).
- 39 regular mods (27 round + 12 arc) + 39 aero versions; level floors are replaced by rung unlocks.

### Unlock and price table

| Unlocks | Mod IDs | Points | List price | Fills gap through |
|---|---|---|---|---|
| R1 open (Prologue race 3 win) | `MOD_R1_POW_MK1`, `MOD_R1_HAN_MK1`, `MOD_R1_EN_MK1` | 213 | $150 | L6 |
| after R1 mat1 | `MOD_R1_POW_MK2`, `MOD_R1_HAN_MK2`, `MOD_R1_EN_MK2` | 218 | $500 | L9 |
| after R1 mat2 | `MOD_R1_POW_MK3`, `MOD_R1_HAN_MK3`, `MOD_R1_EN_MK3` | 223 | $1,000 | L12 |
| R2 open | `MOD_R2_POW_MK1`, `MOD_R2_HAN_MK1`, `MOD_R2_EN_MK1` | 242 | $700 | L22 |
| after R2 mat1 | `MOD_R2_POW_MK2`, `MOD_R2_HAN_MK2`, `MOD_R2_EN_MK2` | 249 | $1,500 | L26 |
| after R2 mat2 | `MOD_R2_POW_MK3`, `MOD_R2_HAN_MK3`, `MOD_R2_EN_MK3` | 255 | $5,000 | L29 |
| R3 open | `MOD_R3_POW_MK1`, `MOD_R3_HAN_MK1`, `MOD_R3_EN_MK1` | 279 | $1,200 | L40 |
| after R3 mat1 | `MOD_R3_POW_MK2`, `MOD_R3_HAN_MK2`, `MOD_R3_EN_MK2` | 288 | $2,500 | L44 |
| after R3 mat2 | `MOD_R3_POW_MK3`, `MOD_R3_HAN_MK3`, `MOD_R3_EN_MK3` | 292 | $8,000 | L46 |
| arc: P1 win | `MOD_ARC_POW_MYTH1`, `MOD_ARC_HAN_MYTH1`, `MOD_ARC_EN_MYTH1` | 333 | $2,500 | L64 |
| arc: F1 win | `MOD_ARC_POW_MYTH2`, `MOD_ARC_HAN_MYTH2`, `MOD_ARC_EN_MYTH2` | 375 | $4,000 | L79 |
| arc: F2 win | `MOD_ARC_POW_MYTH3`, `MOD_ARC_HAN_MYTH3`, `MOD_ARC_EN_MYTH3` | 426 | $6,000 | L94 |
| arc: F3 win | `MOD_ARC_POW_MYTH4`, `MOD_ARC_HAN_MYTH4`, `MOD_ARC_EN_MYTH4` | 501 | $8,000 | L114 |


All Mk2/Mk3 cards are visible from round open with their lock (after mat1 / after mat2).

## Buyer used in the walks
Before every race, after every grind and at each round end: while under full fill, buy the unlocked affordable mod with the
largest usable gain (ties → cheaper); duplicates allowed. Equip by district pattern (Street PPHE, Wangan PHEE, Touge PPHE);
owned mods stay in the garage. Live purses / 65 % debt cut / wholesale / grind pay and live grind rules. No aero bought.

## Results (sim numbers, `final_4`) vs live c877a19
| Target | Result | Live | OK |
|---|---|---|---|
| 60/60 boss at cap ≥ 30 % (hard track) | 31.6 / 40.1 / 30.2 | 31.6 / 40.1 / 30.2 | yes |
| 80/80 boss at cap 90–95 % | 94.9 / 91.6 / 92.9 | same | yes |
| 80/80 story-only minimum per round ≥ 50 % | 53.0 / 54.4 / 50.5 (R3 oh1) | same | yes (R3 thin, as live) |
| 80/80 story-only bosses | 53.0 / 57.7 / 55.8 | same | yes |
| Mixed wall grinds 3–6 (+ to cap) | 3+10 / 3+10 / 4+8 | same | yes |
| 60/60 grinds per round | 13 / 15 / 18 | same | — |
| Finale 80/80 F1–F4 (hard) | 81.7 / 82.7 / 79.3 / 81.7 | 81.7 / 82.7 / 78.6 / 81.7 | — |
| Finale 60/60 F1–F4 | 34.7 / 41.7 / 31.6 / 34.7 | 34.7 / 41.7 / 30.3 / 34.7 | — |
| Finale grinds per step ≤ 10 | 60/60 **11** / 7 / 7 / 9; 60/80 7/6/6/7; 80/60 6/6/6/7; 80/80 0 | identical (60/60 step 1 = 11 in live too) | **no, step 1 for 60/60 (pre-existing, not a catalog effect)** |
| Easy grind races (10-turn) | min 50.3 (60/60 hard walk, R1 kid1, 1 Mk1 equipped); 80/80 min 85.6 | 52.1 / 85.6 | yes, 60/60 floor 1.8 pts lower |
| Arc fill | 100 % at every billed finale race for all four profiles | — | yes |

Differences from live are confined to R1 kid1–kid2, where live assumes full mods the player can't yet afford:
80/80 kid2 95.5 (live 98.9); 60/60 hard kid1 50.3 after 1 grind (live 85.6 after 2), hard R1 wall 1+12 (live 2+11).
F3 finale differs because this walk is on tune (live includes the SP split).

**Spend and money:** story-only spends $23,580 in R1–R3 and ends R3 with $30,420 (live banks $54,000); mixed $62,180 → $16,102;
hard $67,080 → $16,922. Arc end money: 80/80 $16,995, 60/80 $28,482, 80/60 $27,740, 60/60 $35,242 (80/80 has $6,195 before F4).

**Aspirational check (story-only first sight):** R1 shop opens with $0 → kid1 runs stock; `MOD_R2_*_MK3` set 4 × $5,000 = $20,000
vs $8,470 when it unlocks; `MOD_R3_*_MK3` set 4 × $8,000 = $32,000 vs $24,230. Story-only never needs Mk3 (bosses at L6 / L23 / L41
sit inside Mk2 fill), so it doesn't move story targets; it still buys single Mk3s late (`MOD_R2_HAN_MK3` at R2 end, `MOD_R3_POW_MK3` at R3 end).

**Price limits found:** R1 Mk3 must stay ≤ $1,000 (at $1,600 the grinders miss the 4th piece and 60/60 at R1 cap is 27.7 %);
ARC MYTH4 must stay $8,000 (at $12,000 F4 breaks: 60/80 59.2, 80/60 52.9, 80/80 78.2). Mk sizes differ only ~5 % within a
round because the mod gap grows slowly and the win curve is steep.

The stale econ-v1 evaluator line "80/80 only 0 T4 regulars at F2" reads the old `n_t4_reg` counter, which this catalog doesn't use.

## Prologue race-3 mismatch → resolution
design/07 (§ Progression) says regular mods unlock when the PC **wins** scripted race 3; the sim has no such constant and its
walk gives full mods from R1 kid2 ($350 cash). Resolution: add `MOD_UNLOCK_RACE = 3`; the shop opens on that win with the R1 Mk1 set;
the sim starts R1 with $0, so kid1 is stock in practice (matches the sim's stock car at R1 L0). design/07 line ~301 ("no parts
in scripted races 1–3") already agrees. See `GO_LIVE.md`.

## Assumptions / flags
Stock part 150 per slot (draft). On-tune win table (the 4-slot patterns land on the district tune per RESULTS.md). Arc via the
draft econ-v1 walker with `core.LIVE_ARC` caps 46/64/79/94/115 and step patterns touge / wangan / street / touge. Aero not
exercised. Variants explored (base / aspire / canon × 4 / 6 slots) are in `catalog_results.txt`; all met the same targets.
