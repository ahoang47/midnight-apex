# Campaign planner v2: live mod_skill rules (draft tool, unapproved/barry)

Live Page, rewritten in place: https://cursor.com/canvas/store-4599c40d-e855-4fb8-bc90-b1743052ccec/786f1da3-54a2-42a2-b4c6-331eb5da9579
(canvas 786f1da3-54a2-42a2-b4c6-331eb5da9579, title kept: "Campaign planner: mod_skill"). Tracks the live sim at commit
c8d1200 (release 0.5, player HEAT_RELEASE 0.5). The old version (draft mod_skill study rules, 13f6917) stays in
`../mod-skill-v1/planner/` and is STALE.

Approval: Austin 2026-11-20 ("Yes." to regenerating the planner from the live sim; then approved the real rebuild, keeping
the reading slider / standard reading curve rather than strong/weak players).

## Files
- `build_tables.py` -> `win_tables.json`: Monte Carlo win tables through the live sim (`mod_skill.crew_config`, live crew
  stats, live HEAT_RELEASE, hardest live track, player on the district tune, 3 boss styles). Grid per district x rung:
  reading q in 0.60 / 0.65 / 0.70 / 0.75 / 0.80 (player_read = player_timing = player_pacing = q) x car points at the 7 rung
  floors, the midpoint boss floor -> round cap, and the round cap. n = 2,400 races per cell (SE <= 1.0 pp), seeds
  96,000,000 + style x 100,000 + k (the experience gauntlet's seeds, so each cell is a subset of its races). ~11.5 min on 8 cores.
- `gen_constants.py` -> `constants.ts` / `constants.json`: every rule value read from sim/velocity_shift (equations.py,
  mod_skill.py): tiers, prices and wholesale, Mk unlocks (mod_skill.unlocked_mk), story / wild XP, required wilds, NM cap,
  floors, crew stats, purses, debt. Refuses tables built at another HEAT_RELEASE.
- `engine.ts` - the Page engine (between `// ENGINE-START` and `// ENGINE-END`).
- `py_reference.py` - Python model of the same rules; writes `script.json`, `script_errors.json`, `py_reference.json`.
- `verify.mjs` - runs both plans through the TS engine and compares with Python; with a page source it also checks that the
  Page carries constants.ts and engine.ts verbatim. Log: `verify_log.txt`.
- `page_source.tsx` - the published Page source (ReadCanvas). `before_after.txt` - old page vs new page on the same builds.

## Regenerate and verify
    python3 build_tables.py --n 2400      # only when the sim changes
    python3 gen_constants.py && python3 py_reference.py
    node verify.mjs                       # constants.ts + engine.ts
    node verify.mjs page_source.tsx       # the published Page
Last result (c8d1200): 844 numbers over 42 rows (scripted playthrough + error plan), 844 exact, worst win diff 0.000 pp,
0 mismatches; Page constants and engine blocks identical.
Sanity vs the experience gauntlet: strong (0.8) at the boss floor = 65.8 / 66.8 / 66.9 (Street / Wangan / Touge), inside
the 66-68 band within the table's ~1 pp noise.

## Player decisions (nothing is automatic)
Per crew race: the required wild encounter wins before it (one before every rung after Kid 1), any non-mandatory wins, and
every buy at Reiko's (slot 1-4, before the extra races or after the win). A buy is one live shop step: an empty slot or one
holding an older round's mod takes this round's Mk1, otherwise the next Mk; Mk2 after the Mature 1 win, Mk3 after the
Mature 2 win; earned points carry. XP placement is the live Garage.assign (most room first, spilling; the rest is lost from
the car but stays in the earned-XP ledger the floors check). Missing wilds, floor locks, unaffordable or not-on-sale buys
are flagged; a locked race shows win "—".

## Standard reading curve (PLACEHOLDER, kept from v1)
s = 0.6 + 0.2 x ran / N per district, N = 6 + all wilds and non-mandatory wins entered in that district, `ran` = races run
so far (this stop's extra races included); the boss is 0.8. Win % is bilinear in (s, car points) on the table, rounded to
0.1; points outside the grid use its edge.

## Per-stop order
1. buys "before the extra races"  2. required wilds, then non-mandatory wins (each pays the wild purse, 65 % to the debt
while open; XP per MS_WILD_XP, NM XP only for the first MS_NM_XP_CAP per round)  3. the crew race (floor and wild checks,
win %)  4. story purse  5. buys "after the win"  6. story XP. Every planned race is assumed won.

## Not modelled
Pre-finale arc and finale; off-tune stat splits (the sim measures the district tune; points re-assign freely at Reiko's).
