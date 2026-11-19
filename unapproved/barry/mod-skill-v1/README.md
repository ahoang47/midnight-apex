# mod-skill-v1: Austin's "mod_skill" progression, simulated (Barry DRAFT, 2026-11-18)

> **DECISION (Austin, direct, 2026-11-19): Gate A, see [GATE.md](GATE.md).** Each round's crew boss stays locked until all
> four mods are full (car points 3,532 / 4,044 / 4,628). For a story-only player that is 13 / 13 / 12 wild-encounter wins.
> Austin accepted about 20 races per round at 80/80. Gate B (the mat2 lock) is **rejected**. mod_skill itself is still an
> unapproved draft; nothing in `sim/` changed.
> - **Still open:** whether to replace the story-only criterion with "80/80 ≥ 50 on every non-boss race", and the finale r
>   retune.
> - **Terms (Austin approved 2026-11-19; design/01 canon, "Race terms"):** a **mandatory race** is a wild encounter or a story
>   race; a **non-mandatory race** is a substory or a race the player picks a fight in. "Grind race" is retired: older lines in
>   this README that say "grind" mean wild encounters. Code names (`grind_xp` etc.) are unchanged.

> ~~**2026-11-19 DRAFT (Austin direct, unapproved): required grinding ("gym gate")**~~ (superseded by the decision above; numbers unchanged), see [GATE.md](GATE.md). The skill_tree
> "Pokemon-style" design (shelved in e5b8a14) was a win gate on mandatory races, with no XP threshold. For mod_skill I proposed:
> the **round boss stays locked until all four mods are full** (car points 3,532 / 4,044 / 4,628), which is the build the
> boss targets assume. Live sim results:
> - A story-only player needs **13 / 13 / 12 wild-encounter wins**. Boss win at the gate is 31.2 / 93.9, 40.5 / 92.4 and 31.2 / 91.4
>   (table); the engine gives 32.0 / 93.8, 40.7 / 92.2 and 30.8 / 91.8.
> - Mixed and hard players are unaffected. The story-only boss criterion disappears. The finale out-of-band issue remains.
> - ~~Option B adds a mat2 lock at 3,327 / 3,793 / 4,382.~~ Rejected (Austin 2026-11-19).
> - `walk.py` now has a `gate` mode and the boss-cell fix (`../ai-heat-qte-v1/econ_rewalk/walk_boss_flag.patch`).

Status: draft study. Nothing here is live and nothing is committed. sim/velocity_shift/ is imported read-only. The one
in-memory patch, DEBT_AMOUNT in debt_check.py, is never written back.
Branch: touge-race @ bbdda07.

## The proposal (Austin, 2026-11-18)
- The player never levels. The car starts as today's L0 stock car: 2400 SP plus 4 stock parts x 150 = 3000 points = 300.0 stat units.
- Wild encounters pay cash ("grinding" in the original wording). Cash buys mods.
- Race XP from story races and wild encounters goes straight into mods. After each race the player puts that race's XP into ONE mod.
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
   story-only r, plus the live catch-up rule (CATCHUP_XP_FRAC / CATCHUP_XP_SHARE). Wild-encounter XP (code `grind_xp`) is a flat amount per
   round, fitted so the mixed player races as many wild encounters as today (13/13/12). The hard player's wild-encounter counts are NOT fitted; they are a check.
6. **Walk policies (story / mixed / hard):** copied from live progression._walk_round. "Cap" = every kit mod at the round's ceiling.

## Files
- `mod_skill.py`: the model. Stock car, ceilings, base options, and `alloc()` (the best stat split toward the tune under X).
- `sweep_x.py` -> `sweep_x.json`: X x base sweep. Covers tune reach, kits on tune, round-entry distance, and the boss cost of a wrong kit.
- `sweep_fine.py` -> `sweep_fine.json`: fine X sweep (0.50-0.80) on the setup base.
- `walk.py`: the campaign walk R1-R3 (cash, debt, shop, XP assignment, wild-encounter policies).
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

## Decision (Austin 2026-11-18)
- Mod slots must NOT change per district: one fixed kit layout across all rounds. Layout: POW, HAN, EN + 1 flex slot (any stat), every round. Ceilings re-derived in FIXED_LAYOUT.md: unchanged at 133 / 261 / 407; grind XP 13 / 12 / 14; R1 boss story XP 26.5; spirit off.
