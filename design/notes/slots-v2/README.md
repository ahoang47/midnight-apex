# slots-v2: approved parts (Austin, 2026-11-11 10:58 PM PT)

Austin's words: "Approve both". Both parts are now live in `sim/velocity_shift/equations.py`, the single source:

1. **Parity-window knot:** the r = 1.00 knot of `KNOT_WINDOW_105` goes from 0.68 to **0.67**.
   - `qte_zone_width` is generated from it. In units of w0, verified from code: r 1.00 0.5802 → **0.5698**, r 1.0004 0.5829 → 0.5725, r 1.02 0.7243 → **0.7170**, r 1.0355 0.8548 → 0.8507, r 1.037 0.8687 → 0.8649. r ≤ 0.95 and r ≥ 1.05 are unchanged.
   - `QTE_ZONE_WIDTH_105`'s r = 1.00 row is now 0.5698111340658429.
   - `sim/config/winrate_n4000.json` was rebuilt with the new knots (`rebuild_winrate_table.py`). The same method run on the old knots reproduces the old table exactly. 395 rows changed, all at r 0.9525–1.045.
   - Official forced progression is still **153 grind / 162 levels in all 216 play orders**.
2. **Aero free-pool cap:** `AERO_FREE_POOL_MAX_FRACTION = 0.10`, with helper `aero_free_pool_max()`.
   - `AERO_MAX_EQUIPPED = 1` and `AERO_COUNTS_IN_MOD_CAP = True`.
   - Aero goes in any slot and its full total counts inside the 105% cap.
   - Per-tier `AERO_FREE_POINTS` are still TBD.

## Playable spot-check (`spotcheck.py`)

Same method as `sim/tests/test_playable_oracle.py`: 1,000 races per (seed, length), 9 batches.

| Cell | Before: playable min–max (mean) / oracle band | After: playable min–max (mean) / oracle band |
|---|---|---|
| Street boss at target (r 1.05) | 63.2–65.1 (64.39) / 61.4–65.1 | 63.2–65.1 (64.39) / 61.4–65.1 |
| Street mature #2 skipped (r 1.0355) | 43.5–49.4 (46.82) / 42.8–49.6 | **43.0–49.4 (46.22) / 42.3–49.6** |
| Touge boss at target (r 1.05) | 65.5–67.1 (66.42) / 63.4–67.8 | 65.5–67.1 (66.42) / 63.4–67.8 |
| Wangan boss at target (r 1.05) | 63.7–67.1 (65.79) / 62.0–66.8 | 63.7–67.1 (65.79) / 62.0–66.8 |

The r = 1.05 cells can't move, because the zone there is 1.0 either way.

## Fix b3: crew-local level floor on the mature #2 mod tier (Austin, 2026-11-12 6:55 AM PT)

Austin's words: "Oh, neat. Yes approved." This is live in `sim/velocity_shift/equations.py` (`MOD_TIER_LEVEL_FLOOR`, `MOD_TIER_FLOOR_RUNG`, `MOD_TIER_FLOOR_MARGIN`) and `sim/velocity_shift/progression.py` (`derive_mod_tier_floors`, `mod_tier_floor`, `mod_tier_available`, gating in `run`). Rules: design/07 §6.4.

- **Floors:** the code generates them, nothing is copied by hand. `derive_mod_tier_floors()` uses the study's derivation (`fixes.py` `LOCAL_L` + 1, capped at the rung's cap). Its output equals the constant table in all 216 play orders, and it matches the study's `results_floor_cost.json` crew by crew.
- **`b3_check.py`:** reruns the study's oracle check with the floor read from the live sim, across all 216 orders. `b3_check_before.json` uses `--no-floor`; `b3_check_after.json` uses the live floor.

| Profile | Grind before (bal / window / aero10) | Grind after | Newest-mod-decisive rungs before | After |
|---|---|---|---|---|
| weak | 141 / 141 / 141 | 141 / 141 / 141 | none | none |
| average | 153 / 153 / 153 | 153 / 153 / 153 | none | none |
| strong | 121 / 121 / 121 | **100 / 100 / 100** | R1 pos 2 mature #2 (47.86 → 52.49), R2 pos 3 mature #2 (47.84 → 52.67; aero10 48.03 → 52.67) | **none** |

Every value is identical in all 216 orders, so the check depends on play position only.

- **Live progression** (`scripts/run_progression.py --all-orders`, average play): still **153 grind / 162 levels / 0 lost XP in all 216 orders**, with one wall layout.
  - The only change is the skipped mature #2 rate of the crew played first in R1, where the tier is locked (story level 3 < floor 4). Touge 42–51 → 33–44, Wangan 43–52 → 34–44, Street 42–50 → 32–42. Those rungs were already walls (7 grind) and stay walls.
- **`floor_cost.py` / `results_floor_cost.json`:** grind races from the skip state to the floor. These were moved here from the study and rerun byte-identical.
- **Playable spot-check (`spotcheck_b3.json`):** identical to `spotcheck_after.json`. The engine cells are r-based, and the floor doesn't touch combat.
- **Test:** `sim/tests/test_mod_floor.py`. Its oracle test needs numpy and the banks outside the repo, and it skips when they aren't present.

Everything else in `unapproved/barry/slots-v2/RESULTS.md` is still **NOT approved**: window +75% / 1.15 cap, the P1/P2 prices, and the dead-win fill. In `unapproved/barry/slots-v2/RESULTS_v1v2.md`, fixes a, a0, b, b2 and c were **not chosen**.
