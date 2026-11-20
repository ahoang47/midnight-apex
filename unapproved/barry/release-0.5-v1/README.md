# release-0.5-v1: player lock release 30 % → 50 %, crew stats re-pinned (Barry PROPOSAL, 2026-11-20, UNAPPROVED)

> Austin (direct, 9:40 AM): "No, I think an earlier unlock is what preserves gameplay mechanics." One change only: the player's
> gauge unlocks below **50 %** of capacity (was 30 %, `HEAT_RELEASE`). Everything else is live: per-turn QTE, no lock cap, no falloff,
> no AI pacing, no lap reset, no tonics; AI rules unchanged (release 80 %, corner load never locks). sim/ untouched (patched in memory
> by `repin.py`). Harness = climb-repin-v2 `repin.py` on the live sim; seeds as the live climb; rungs n = 2,000, bosses n = 6,000.

## New crew stats (MS_CREW_BUDGET, live → release 0.5), kid1 → boss
| District | live | release 0.5 |
|---|---|---|
| Street | 293.98, 306.16, 309.14, 317.38, 325.10, 331.98, 332.58 | 295.24, 308.67, 311.92, 320.73, 328.02, 335.48, **336.50** |
| Wangan | 318.65, 340.56, 348.93, 362.05, 372.82, 383.00, 390.35 | 314.54, 340.16, 352.61, 364.74, 375.30, 385.24, **395.20** |
| Touge | 354.33, 383.85, 393.80, 404.82, 415.79, 426.72, 437.06 | 370.52, 389.10, 400.41, 411.94, 423.42, 434.22, **444.00** |
Bosses +1.2 / +1.2 / +1.6 %. Ladder: search to 97.5 / 92 / 86.5 / 81 / 76 / 71.5 / 67 (`r0.5_search/verify.json`), bosses fine-tuned
(`boss_scan.json`), final in `r0.5_final.json`.

## Criteria (live → release 0.5; `criteria.py` → `criteria.json`)
| Criterion | Street | Wangan | Touge |
|---|---|---|---|
| G1a strong boss at floor 66-68 | 66.87 → 66.25 pass | 66.07 → 67.07 pass | 67.65 → 66.35 pass |
| G3c smallest step ≥ 3.0 | 4.15 → 3.81 pass | 3.96 → 3.95 pass | 3.20 → 3.67 pass |
| G2a weak at max ≥ 30 (boss is the min) | 32.63 → 32.72 pass | 35.90 → **26.83 FAIL** | 38.57 → 33.98 pass |
| G3a kid1 → boss ≥ 30 | 30.96 → 31.25 pass | 31.33 → 30.53 pass | 30.70 → 30.75 pass |
| G3b reading gap ≥ 10 | 34.24 → 33.53 pass | 30.17 → 40.24 pass | 29.08 → 32.37 pass |
| G4a lowest ≥ 40 | pass (66.25) | pass (67.07) | pass (66.35) |
| G4b weak at boss floor ≤ 10 | 2.28 → 0.73 pass | 1.55 → 0.47 pass | 2.88 → 0.52 pass |
| G5 strong at max ≤ 95 | 94.50 → **95.67 FAIL** | 89.60 → 90.03 pass | 94.77 → 92.15 pass |

## Feel (600 races per cell; `feel_live.json` vs `feel_r0.5.json`): turns starting locked % / limp % / mean lock turns / races all-locked %
| Cell | Street live → 0.5 | Wangan live → 0.5 | Touge live → 0.5 |
|---|---|---|---|
| kid1 strong floor | 30.2/1.9/2.84/9.0 → 29.9/0.9/2.06/4.5 | 34.7/1.5/3.70/4.8 → 30.4/1.4/3.05/4.8 | 28.3/0.6/3.21/4.3 → 27.4/0.5/2.55/3.8 |
| kid1 weak max | 47.5/2.1/2.78/11.5 → 41.8/0.3/2.18/1.7 | 50.4/4.9/3.55/12.3 → 45.3/0.9/2.50/4.0 | 38.9/0.1/2.90/2.5 → 38.1/0.1/2.31/0.3 |
| oh1 strong floor | 52.0/13.4/4.45/49.2 → 48.2/8.8/2.97/35.3 | 49.9/9.6/5.13/31.0 → 45.1/6.2/3.83/23.7 | 50.2/12.0/4.66/44.8 → 41.4/5.5/2.86/26.8 |
| oh1 weak max | 71.1/16.0/4.12/60.8 → 64.7/8.8/2.80/41.2 | 63.7/9.9/4.56/34.7 → 61.2/8.0/3.39/34.2 | 55.6/8.5/3.86/39.5 → 51.5/4.2/2.71/21.2 |
| boss strong floor | 54.6/14.3/4.66/58.8 → 51.2/10.0/3.13/40.7 | 56.6/16.6/6.25/51.5 → 53.1/12.3/4.62/41.3 | 56.8/16.8/5.15/68.3 → 49.4/10.4/3.29/44.7 |
| boss weak max | 73.0/17.2/4.33/74.3 → 70.7/12.4/3.00/59.8 | 75.5/29.1/6.62/78.0 → 72.3/21.1/4.41/69.7 | 71.3/22.5/4.93/88.0 → 68.1/14.8/3.25/69.7 |
Locks are 0.6-2 turns shorter everywhere and limp drops by about a third at the boss, at the same win rates. Locks still happen
(the mechanic stays); the climb still gets harsher going up (race length), just less so.

## Playtest matchups at equal stats (2,000 races; `../experience-rootcause-v1/exp_levers_live.json`, `exp_levers_release0.5.json`,
same live sim, same rule, same seeds, so not rerun): win % / turns starting locked / limp / lock turns / races all-locked
- MX-5 vs S2000: 72.15 / 34.6 / 2.7 / 3.31 / 12.9 → **76.5 / 31.8 / 1.0 / 2.67 / 5.6**
- WRX vs MX-5: 81.25 / 47.6 / 13.1 / 3.80 / 52.9 → **87.5 / 43.4 / 6.3 / 2.62 / 31.3**

## Remaining failures and the cheapest fix (NOT applied)
- **Wangan G2a 26.83 (−3.17).** Why: the Wangan max build is cap-bound (round cap 4044 at both oh2 and boss), so the weak player
  gains nothing for the boss, while release 0.5 helps the strong pacer more, so the boss rose +1.2 % and the weak-at-max cell fell.
- **Street G5 95.67 (+0.67).** Why: the strong player at max locks less too, and the Street boss can't go higher without leaving
  66-68 (boss 337.0 → strong at floor 64.78).
- Boss alternatives tried (`boss_scan.json`): Street 336.09 → 67.32 / G5 96.05; Wangan 394.77 → 68.12 (out of band, G2a 28.45).
- **Cheapest non-crew fix: move the round max-build caps (`MS_ROUND_CAP_POINTS`; `cap_fix.json`, boss cells n = 6,000):**
  - Wangan 4044 → **4060**: weak at max 33.77, strong at max 91.8, both pass (4054: 29.95 / 90.68; 4084: 41.7 / 94.02).
  - Street 3532 → 3522-3525: 3522 gives G5 94.92 but G2a 29.30; 3525 gives G2a 30.35 but G5 95.17. Street has no clean cap
    value at n = 6,000 (both misses are ≤ 0.7, within noise of about ±0.6). Street could stay at a 0.2 G5 miss, or take the cap
    plus a small Street boss nudge (needs one more scan).
  - Side effect: caps chain into the next round's max builds (Street's into Wangan kid1-oh1, Wangan's into Touge kid1-oh1); Touge's
    boss max is capped at 4628 so its G5 is unaffected. Not re-verified.
- Release 0.6 not tried: 0.5 meets all goals except these two small misses, and 0.6 would raise the strong player's edge further
  (G5) without fixing Wangan's cap-bound G2a.

Files: `repin.py`, `run.sh`, `boss_scan.py`, `cap_fix.py`, `feel.py`, `criteria.py`, their JSON outputs and logs.
