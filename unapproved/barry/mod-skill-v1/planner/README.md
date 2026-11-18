# mod_skill campaign planner (draft, unapproved)

Live Page, rewritten in place: https://cursor.com/canvas/store-4599c40d-e855-4fb8-bc90-b1743052ccec/786f1da3-54a2-42a2-b4c6-331eb5da9579
(canvas 786f1da3-54a2-42a2-b4c6-331eb5da9579). The old planner's source is kept untouched in `planner-v1/`;
`live_canvas_before.tsx` is the canvas as it was before this rewrite (identical to planner-v1/page_source.tsx).

## Files
- `gen_constants.py` -> `constants.ts` / `constants.json` (C, KNOTS, WIN; win tables from the live sim, x100 ints)
- `engine.ts` - the Page engine (between `// ENGINE-START` and `// ENGINE-END`)
- `py_reference.py` - Python model of the same rules; writes `script.json`, `script_errors.json`, `py_reference.json`
- `verify.mjs` - runs both plans through the TS engine and compares with Python; with a page source it also
  deep-compares the Page's C / KNOTS / WIN against constants.ts. Log: `verify_log.txt`
- `page_source.tsx` - the published Page source (ReadCanvas)

## Regenerate and verify
    python3 gen_constants.py && python3 py_reference.py
    node verify.mjs                   # constants.ts + engine.ts
    node verify.mjs page_source.tsx   # the published Page
Last result: 543 numbers over 42 rows (scripted playthrough + error plan), 543 exact, worst win diff 0.000 pp,
0 mismatches; C, KNOTS, WIN identical.

## Player decisions (nothing is automatic)
Base setup of the 3,000 stock points per district (750-1,500 per stat), each mod's POW/HAN/EN split per district
(own stat >= 60%, sums to 100), every grind (+/-), every buy (before grinds or after the win), and the mod that gets
each race's grind XP and win XP. Invalid or missing choices are flagged, never auto-fixed; win % shows "—".

## Standard reading curve (PLACEHOLDER)
Read skill and QTE timing are one value s. In each district s = 0.6 + 0.2 * ran / N, where N = 6 + grinds in that
district and `ran` counts story races and grinds already run (this race's grinds included). The boss is always 0.8.
Win % blends the c6060 / c6080 / c8060 / c8080 tables with a = (s - 0.6) / 0.2:
(1-a)^2, (1-a)a, a(1-a), a^2. Replace once real player-skill data exists.

## Per-race order
1. buys marked "before grinds"  2. grinds (0.55 x wild purse each, 65% to debt while open; grind XP to the grind pick)
3. the race (win % from the car at this point)  4. story purse  5. buys marked "after the win"
6. win XP = story XP + catch-up (0.75 x shortfall below the last cap, split 40/40/20 over Kid 1, Kid 2, Mature 1).

## Spill rule
XP goes to the picked mod up to its tier ceiling (133 / 261 / 407), then spills to the district kit's other owned
mods in slot order; anything left is lost. Unassigned XP is lost and flagged.

Kits: Street P1 P2 H1 E1; Wangan P1 H1 E1 E2; Touge P1 H1 E1 E2 (PHEE). Prices Mk1 list $150 / $700 / $1,200,
-20% wholesale in R2-R3. Debt $16,000 and purses as live. Not committed or pushed.
