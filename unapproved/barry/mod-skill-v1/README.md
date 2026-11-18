# mod-skill-v1: Austin's "mod_skill" progression, simulated (Barry DRAFT, 2026-11-18)

Status: draft study. Nothing here is live and nothing is committed. sim/velocity_shift/ is imported read-only. The one
in-memory patch, DEBT_AMOUNT in debt_check.py, is never written back.
Branch: touge-race @ bbdda07.

## The proposal (Austin, 2026-11-18)
- The player never levels. The car starts as today's L0 stock car: 2400 SP plus 4 stock parts x 150 = 3000 points = 300.0 stat units.
- Grinding pays cash. Cash buys mods.
- Race XP from story and grind races goes straight into mods. After each race the player puts that race's XP into ONE mod.
- Each mod's points are split freely across POW/HAN/EN, but at least X go to the mod's own stat.

## Decisions this study had to make (all documented in RESULTS.md, with the numbers behind them)
1. **Base 3000 points:** the total is fixed and never grows. Its *allocation* is a free "setup" at Reiko's, inside
   25-50 % of the 3000 (option B3). Locking it fails: locked at today's street tune (B1), Wangan sits 14-19 share points
   off tune. Locked even (B2), Street sits 9-14 points off. See the X sweep.
2. **Mod model:** a mod's earned points start at 0, on top of the stock part it replaces. They fill with XP up to the
   ceiling of the tier the player has bought. Tier n = round n, unlocked at round open, one tier per stat per round
   (minimal catalog). Buying the next tier raises the ceiling, and earned points carry over.
   Ceiling per mod = (today's cap power x 10 - 3000) / 4, so a full kit equals today's cap power exactly.
3. **Pool split:** freely re-assignable at Reiko's (like the aero wind tunnel). Because of this and the base setup,
   the 20 % district retune is not needed.
4. **XP pick policy:** XP goes to the owned kit mod that leaves the build closest to DISTRICT_TUNE, ties to the mod furthest
   below its ceiling. "strict" = overflow past that mod's ceiling is lost (Austin's rule as written).
   "spill" = overflow goes to the next pick (recommended amendment).
5. **XP retune:** a per-rung story XP table, fitted so the story-only player reaches every rung at today's live
   story-only r, plus the live catch-up rule (CATCHUP_XP_FRAC / CATCHUP_XP_SHARE). Grind XP is a flat amount per round,
   fitted so the mixed player grinds as often as today (13/13/12). The hard-player grind counts are NOT fitted; they are a check.
6. **Walk policies (story / mixed / hard):** copied from live progression._walk_round. "Cap" = every kit mod at the round's ceiling.

## Files
- `mod_skill.py`: the model. Stock car, ceilings, base options, and `alloc()` (the best stat split toward the tune under X).
- `sweep_x.py` -> `sweep_x.json`: X x base sweep. Covers tune reach, kits on tune, round-entry distance, and the boss cost of a wrong kit.
- `sweep_fine.py` -> `sweep_fine.json`: fine X sweep (0.50-0.80) on the setup base.
- `walk.py`: the campaign walk R1-R3 (cash, debt, shop, XP assignment, grinding policies).
- `calibrate.py` -> `calib_*.json`: XP retune per config (`python3 calibrate.py mk1_list [spill] [touge_phee]`).
- `baseline_live.py` -> `baseline_live.json`: today's live progression rerun (the comparison column).
- `run_all.py` -> `results.json`: all configs plus the price sweep. `debt_check.py` -> `debt_check.json`.
- `make_tables.py` -> `tables.md`: every table in RESULTS.md.

Rerun order: `python3 baseline_live.py && python3 sweep_x.py && python3 sweep_fine.py && python3 calibrate.py mk1_list &&
python3 calibrate.py mk1_list spill && python3 calibrate.py mk1_list touge_phee && python3 calibrate.py mk1_list spill touge_phee &&
python3 run_all.py && python3 debt_check.py && python3 make_tables.py` (a few seconds in total).

## Limits
- Win rates come from the live interpolation tables (progression.win_pack, G2 heat, 15 live tracks, hard cells). The match
  engine was not rerun.
- The off-tune table varies only the POW share (HAN fixed at 25 %). A HAN-heavy wrong kit is therefore not priced, and the
  "wrong kit" costs below use POW-share kits (PPPP in Wangan, EEEE in Street).
- Pre-finale arc and finale: only the ceilings were derived (results.json `finale_ceil`). The arc was not walked.
