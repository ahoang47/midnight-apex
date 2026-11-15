# mods-v1 go-live plan (prepared, NOT applied; Barry, 2026-11-14)

This applies the DECISION.md pick (4 slots, canon staging, aspire Mk3, IDs only) to live `sim/` at c877a19. Nothing here has been applied yet. It needs Austin's go-ahead, then commit and push, with one CHANGELOG entry per commit.

## 1. `sim/velocity_shift/equations.py`
| Constant | Now | After |
|---|---|---|
| `MOD_SLOTS` | 6 | **4** |
| `MOD_UNLOCK_RACE` | (missing) | **3**: the shop opens on the Prologue race-3 *win* |
| `MOD_STOCK_PART_POINTS` | (missing) | **150** per slot (600 / `MOD_SLOTS`, so SP + stock = live stock P at L0) |
| `MOD_CATALOG` | (missing) | the 39 entries from `catalog_final.json`: `{id: (stat, points, price, unlock)}`, IDs `MOD_R1_POW_MK1` … `MOD_ARC_EN_MYTH4` |
| `MOD_UNLOCK` | (missing) | the unlock token per Mk: `("open", r)` / `(r, "mat1")` / `(r, "mat2")` / `("arc", "P1" \| "F1" \| "F2" \| "F3")` |
| `MOD_PRICE` (per tier) | T1 1600 / T2 2800 / T3 4000 / T4 8000 | **replaced** by per-ID prices in `MOD_CATALOG`. Keep `MOD_PRICE_STANDIN = ("MOD_ARC_*_MYTH4",)` |
| `MOD_TIER_LEVEL_FLOOR` | T1 0 / T2 13 / T3 30 / T4 47 | **removed**; rung unlocks replace it (story-only reaches R2 kid1 at L12) |
| `T4_UNLOCK_RACE` | "P1" | kept as the MYTH1 unlock (`MOD_UNLOCK` arc P1) |
| `T4_PACKAGE` | 5 regular + 1 aero | **4 slots: 3 regular + 1 aero**, or retired with `t4_package_price` |
| `WHOLESALE_TIERS` | ("T1", "T2", "T3") | R1–R3 IDs (by prefix `MOD_R`) |
| `AERO_PRICE_MULT` 1.75, `AERO_MAX_EQUIPPED` 1, `AERO_UNLOCK_AFTER` 1, `MOD_CAP_FRACTION` 1.07, `MOD_BUDGET_AT_CAP` 0.27 | unchanged | aero IDs are `<ID>_AERO` |
| `MOD_SLOT_PATTERN` | (missing) | Street PPHE / Wangan PHEE / Touge PPHE (the buyer's equip order) |

`mod_price(tier, aero, wholesale)` becomes `mod_price(mod_id, aero=False, wholesale=False)`.

## 2. `sim/velocity_shift/progression.py`
- **`combat_power(level, rnd)`:** add an optional `garage` argument, so the power becomes min(C, 1.3375·SP, SP + slot points)/10 with stock parts in empty slots. With no `garage`, it keeps today's full-fill path, which is still used by `cap_builds` / `boss_check_at_cap`.
- **`Garage` class** (port of `catalog.Garage`):
  - owned list and `equipped(district)`;
  - `shop(wallet, L, stage, district, unlocked, wholesale)`, the just-in-time buyer;
  - `fill()`.
- **`_walk_round`:**
  - carry the garage and cash, and shop before every race, after every grind and at round end;
  - add the unlock tokens `("open", r)` and `(r, rung)`;
  - rows gain `fill`, `equipped`, `owned` and `cash_pre`;
  - grinds stay one at a time, with a shop after each (`grind_until` / pre-boss to-cap).
- **`run()`:** create the garage at R1 with $0. The shop is open from R1 kid1 (`MOD_UNLOCK_RACE` met by the Prologue).
- **`mod_tier_floor`, `mod_tier_available`:** replace with `mod_unlocked(mod_id, done_tokens)`.
- **Arc walk** (`LIVE_ARC` races, line ~452): unlock MYTH tiers on the P1 / F1 / F2 / F3 wins, and shop with the same garage.
- **`sim/scripts/run_progression.py`:** print the per-rung fill, owned mods and cash. Replace the "T4 package" line with the MYTH4 stand-in price.

## 3. Tests (`sim/tests/`)
- **`test_mod_floor.py`:** replace the floor tests with:
  - the unlock schedule (Mk1 at round open, Mk2 after mat1, Mk3 after mat2, MYTH1–4 after P1/F1/F2/F3);
  - the ID format;
  - `MOD_UNLOCK_RACE == 3`;
  - a check that 4 × the Mk points cover the gap at `fills_to_L`.

  Replace `test_shop_funds_the_cap_on_the_mixed_walk` with "buyer reaches 100 % fill at every rung from mat1 on, for all three walks".
- **`test_progression.py`:**
  - update the `mod_price` pins (lines ~79–82) to the per-ID prices, e.g. `mod_price("MOD_R3_POW_MK3") == 8000`, aero 14000, wholesale R2 Mk3 4000, ARC MYTH4 no wholesale;
  - re-pin R1 kid2 80/80 at 95.5 (was 98.9) and the hard R1 split 1+12 (was 2+11);
  - every other pin is unchanged (bosses, minimums, grinds, at cap).
- **New `test_mod_catalog.py`:**
  - 39 IDs, one stat each, and points never change;
  - at most one aero;
  - the price guards (R1 Mk3 ≤ $1,000, MYTH4 = $8,000);
  - the story-only Mk3 sets are unaffordable at unlock: R2 4 × $5,000 > $8,470 and R3 4 × $8,000 > $24,230.
- **Run only:** `test_mod_floor.py`, `test_progression.py`, `test_mod_catalog.py`, `test_skill_points.py`. CI covers the rest.

## 4. Docs
- **design/02 (equations reference):**
  - row 191, "Mod tier level floor": becomes "Mod unlocks", listing `MOD_UNLOCK_RACE = 3`, `MOD_UNLOCK` and the rung staging;
  - row 190: add `MOD_SLOTS` 4 and `MOD_STOCK_PART_POINTS` 150;
  - row 215, "Mod prices": the per-ID price table;
  - lines 49 and 260: note that the race-3 unlock is now in the sim.
- **design/07, Progression bullet (~line 394):**
  - "Regular mods unlock when the PC wins race 3 (`MOD_UNLOCK_RACE = 3`). Reiko's stock then grows by rung: each round's Mk1 set at round open, Mk2 after the mat1 win, Mk3 after the mat2 win (visible, locked, from open). MYTH1–4 unlock after P1 / F1 / F2 / F3."
  - Also the §6.4 floor paragraph (~223) and the table rows 216–217 (`MOD_TIER_LEVEL_FLOOR`, `MOD_PRICE`).
  - Line ~301 ("no parts in scripted races 1–3") already agrees.
  - Answer Q19's race-3 gate only if Austin gives a rule; this plan doesn't.
- **Money wording:** the price figures in 02 and 07 belong to Desmond's USD pass. Change only the numbers and the IDs, and ask Desmond to review the wording.
- **design/01 canon block (line 17)** still names `MOD_TIER_LEVEL_FLOOR`. Barry doesn't edit the canon block, so Austin should update it if the floors are retired.
- **Deck Page:** add a "Mod catalog" section with the unlock and price table, no track codenames.

## 5. Verification after applying
Re-run `catalog_report.py` against live, or the ported walk, and check:
- 60/60 at cap 31.6 / 40.1 / 30.2;
- 80/80 at cap 94.9 / 91.6 / 92.9;
- story-only minimums 53.0 / 54.4 / 50.5;
- mixed grinds 3+10 / 3+10 / 4+8;
- 60/60 grinds 13 / 15 / 18;
- finale 80/80 81.7 / 82.7 / 79.3 (on tune; 78.6 with the SP split) / 81.7.
