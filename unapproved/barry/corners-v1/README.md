# corners-v1: signature corners — PROPOSAL, NOT APPROVED

> **Status:** proposal only. Austin paused the signature-corner sim on 2026-11-12; nothing was run, committed or changed in `sim/`. No picks below are approved. Approved track facts are in the canon block of `design/01-system-overview.md` (Tracks, 2026-11-12).

## Rule (Austin, relayed by Nathaniel)
- Each district has signature corners. On them, **every** racer in the district (wild racers, lieutenants, crew bosses) runs the same standard line and bluff.
- On every other corner, all **wild racers** share one line and bluff, and **each named character** has their own style.

## Track facts (Austin, 2026-11-12)
- 3 tracks per district, 9 in total.
- Every track is exactly 10 turns per lap.
- 20- and 30-turn races are 2 and 3 laps of the same track, so signature corners repeat each lap.

## Candidate picks (none chosen)
Corner codes are the keys of `LINE_SET_C` in `sim/velocity_shift/equations.py` (HP hairpin, ES esses, DR decreasing radius, SW sweeper, IR increasing radius, CR constant radius, N90 90-degree, CH chicane).

| District | Nathaniel's first pass (keeps the district's current main line) | Barry's earlier candidates (from shared lines in `LINE_SET_C`) |
|---|---|---|
| Touge | HP, ES, DR | CR, IR, SW (a guess) |
| Wangan | SW, IR, CR | IR, SW |
| Street | N90, CH, HP | SW, ES, CH |

Nathaniel writes the in-world reasons only after picks are approved.

## Austin's concern (2026-11-12)
With only a few signature corners, and one shared wild line on every other corner, wild races can feel flat or like a guessing game: the player can read the entry, and nothing after it.

## Options (systems only, none approved)
1. **More signature corners**, maybe about half of each 10-turn track, so wild races get a learnable district rhythm and named characters stand out on the rest.
2. **A learnable wild pattern on normal corners**, e.g. the corner type's main line plus a tell, instead of a fixed guess.
3. **Correlate apex and exit with the entry** on normal corners, so a read of the entry carries through the rest of the corner.

## Proposed sim (paused; do not run without Austin's go)
- Sweep 3 to 7 signature corners out of 10 per track, each with and without option 3, on the live sim (0.67 knot, 10 % aero cap, mod tier floor at 29f8431).
- Placeholder track layouts per district, clearly labelled, unless real layouts exist. Named-character styles would be documented variations of the district table and shown to Desmond and Nathaniel.
- **Metrics:**
  1. **Distinctness edge:** how much more often a player who has learned a named character's style picks a better line against them than against a wild racer; report the most signature corners that keep it clearly above zero.
  2. **Wild-race read rate:** how often a player who knows the district guesses right against wild racers.
  3. **Balance:** boss and lieutenant win rates within the usual bar of today's numbers (≥ 5 pp in the same direction in all 9 batches counts as a move); grind stays 141 / 153 / 100 (weak / average / strong); every play order keeps its wall layout.
  4. **Signature corners are measurably more predictable** than normal corners.
- If nothing passes, report the closest option rather than forcing a pick.

## Needs from the build (Gordon)
- Corner IDs with a `signature` flag per track.
- A wild-or-named tag on each racer, so the line lookup can choose the district, wild or personal table.
