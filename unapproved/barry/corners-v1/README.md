# corners-v1: signature corners — PROPOSAL, NOT APPROVED

> **Status:** proposal only. Austin paused the signature-corner sim on 2026-11-12; nothing was run, committed or changed in `sim/`. No picks below are approved. Approved track facts are in the canon block of `design/01-system-overview.md` (Tracks, 2026-11-12).

## Three-layer line model: PROPOSAL, NOT APPROVED (draft per Austin 2026-11-12)

> **Status:** draft only. Austin asked for it on 2026-11-12 ("all districts should have a distinct default line for all corner types. Where this default line deviates is for select corners, this is where bluff lines come in to play. Where it deviates even more is for story characters, where they get their own line + bluff." Then: "Draft it."). **No sim was run.** `sim/` and `LINE_SET_C` are unchanged. Nothing below is approved.

Notation: lines are Entry-Apex-Exit by stat. In tables, **P** = POW, **E** = EN, **H** = HAN (the sim's `LINE_SET_C` letters since 53267c5), so `EHP` = EN-HAN-POW. Visual note (the only one here): on screen, Entry shows as a lane, OUT = POW, MID = HAN, IN = EN relative to the corner (design/06).

### The three layers

| Layer | Applies to | What the opponent plays | Bluff |
|---|---|---|---|
| 1. District default | Every racer in the district, on **normal** corners | One fixed line per (district, corner type). For every corner type the three districts' lines differ | None. Always played, so a player who has learned the district reads it fully |
| 2. Signature corners | Every racer in the district, on a few **select** corners per track | The district default as main line, plus 2 bluff alts in today's structure (alts share main's Entry; alt1 switches Apex + Exit; alt2 switches Exit only) | Yes. Today's structure is `LINE_ADHERENCE` / `LINE_ALT_WEIGHTS`; the rate for this layer is open |
| 3. Story characters | Named racers only (lieutenants, crew bosses, Myth Drivers, Sabine), on **some** corners only: a subset of normal corners and a subset of signature corners (Austin, 2026-11-12) | On a swapped normal corner, their own line instead of the district default; on a swapped signature corner, their own line + bluff instead of the district's. Every other corner follows layers 1 and 2 | Own bluff on swapped signature corners; on swapped normal corners still open. Schema slot only; Nathaniel and Desmond supply the inputs |

### Layer 1: district defaults, current vs proposed (8 x 3)

Rule for the proposal: minimal change. Keep CR, CH and SW (already distinct in all three districts). For each collision, change exactly one district: the one whose change best fits its documented habit (`story/corner_lines.md`: Touge preserves momentum, mostly HAN with POW only on exits; Wangan commits where the road opens and shuts the door, EN, before the straights; Street fights for position, EN-heavy with POW as a lunge, and waits out intersections on HAN). No line Austin approved in lines-v1 (Street N90 `HHP`, Wangan IR and SW `PPE`) is touched, and none of Nathaniel's first-pass signature candidates (Touge HP/ES/DR, Wangan SW/IR/CR, Street N90/CH/HP) changes. Every change is a single letter.

Bold = changed cell, shown as current -> proposed.

| Corner | Touge | Wangan | Street | Collision today |
|---|---|---|---|---|
| HP hairpin | EHP | **EHP -> EHE** | EEP | Touge = Wangan |
| CR constant radius | HHP | HPP | EHE | none |
| DR decreasing radius | HEH | **EEH -> EEE** | EEH | Wangan = Street |
| IR increasing radius | HHP | PPE (lines-v1, approved) | **HHP -> EHP** | Touge = Street |
| N90 90-degree | EHP | **EHP -> EPP** | HHP (lines-v1, approved) | Touge = Wangan |
| CH chicane | HEP | EHP | EPP | none |
| ES esses | HHH | **HHH -> HHE** | PHP | Touge = Wangan |
| SW sweeper | HHP | PPE (lines-v1, approved) | EEE | none |

Systems reason per change:
- **Wangan HP EN-HAN-POW -> EN-HAN-EN:** Wangan leans on EN at Exit to shut the door before the straight; Touge keeps its momentum hairpin (a Touge signature candidate).
- **Wangan N90 EN-HAN-POW -> EN-POW-POW:** Wangan commits on POW where the road opens; Touge keeps its square-off, and Touge can't take HAN-HAN-POW because Street's approved N90 already has it.
- **Wangan ES HAN-HAN-HAN -> HAN-HAN-EN:** one-letter change; keeps the HAN rhythm and adds Wangan's EN door-shut on the exit; Touge's all-HAN esses are its momentum identity (a Touge signature candidate).
- **Wangan DR EN-EN-HAN -> EN-EN-EN:** Wangan doesn't commit on a closing corner, so it goes all-EN and shuts the door; Street keeps EN-EN-HAN, its "door shut until it opens."
- **Street IR HAN-HAN-POW -> EN-HAN-POW:** Street leans on EN at Entry to fight for position, then still lets the opening corner run; Touge keeps its patient momentum line.

Within-district duplicates (info only, not required to fix):

| District | Current | Proposed |
|---|---|---|
| Touge | HP = N90 (EHP); CR = IR = SW (HHP) | same (Touge unchanged) |
| Wangan | HP = N90 = CH (EHP); IR = SW (PPE) | IR = SW (PPE) only |
| Street | IR = N90 (HHP) | none |

Alts for the changed cells are not drafted. They only matter if that corner type becomes a signature corner; they would follow the structure rule above and need Nathaniel's in-world read.

### Layer 3: story-character schema (slot only)

**Ruling (Austin, 2026-11-12, corrected):** "Story characters swap some defaults, and some signature corners." A story character overrides only **some** corners: on a subset of normal corners their own line replaces the district default, and on a subset of signature corners their own line + bluff replaces the district line + bluff. All other corners follow the district layers. This replaces the earlier same-day "every corner" wording (aa1f141). Which corners each character swaps, and their lines and bluff rates, come from Nathaniel and Desmond; none are invented here.

No character lines or rates are invented here. Proposed fields per named racer: a list of swapped normal corners and a list of swapped signature corners; then, per swapped corner, `main` line (3 letters), `alt1` and `alt2` (same structure rule, or a different one if Desmond wants), and a personal adherence and alt split. Any corner not in either list falls back to the district layers. **Nathaniel and Desmond supply every character-level input.**

### Open parameters (none set)

| Parameter | Current value (for reference only) | Status |
|---|---|---|
| Signature corners per 10-turn track, per district | none in the sim today (every corner draws a bluff) | open |
| Which corners are signature | Nathaniel's and Barry's candidates above | open |
| Signature-corner adherence and alt split (layer 2) | `LINE_ADHERENCE` 0.65, `LINE_ALT_WEIGHTS` 0.6 / 0.4 = 0.65 / 0.21 / 0.14 | open |
| Story-character adherence and alt split (layer 3) | same 0.65 / 0.21 / 0.14 today | open |
| Which corners each story character swaps (normal and signature) | none | open, Nathaniel / Desmond |
| Does a character's swapped **normal** corner stay fixed, or also bluff? | Austin earlier said characters get "their own line + bluff" | open, needs Austin |
| Story-character lines | Nathaniel's rung-level first pass in `story/corner_lines.md` (not mechanical yet) | open, Nathaniel / Desmond |
| Alts for the 5 changed cells | none drafted | open, only if signature |
| Entry lane-placement bluff rate (design/06) | not set | separate layer, open |

### Flags for Desmond / Nathaniel
- **Default line changes alter `story/corner_lines.md`.** The 5 changed cells (Wangan HP, N90, ES, DR; Street IR) would need new in-world reasons. Wangan HP and N90 currently read "the same textbook hairpin" / "same", which stop being true. Nathaniel's approved 2026-11-10 lines are otherwise untouched.
- **Character layer needs their inputs.** Per-character lines, bluffs and rates come from Nathaniel and Desmond; Barry only provides the slot and runs the sim.
- **Signature vs character precedence: settled.** Austin, 2026-11-12 (corrected): story characters swap some defaults and some signature corners; every other corner follows the district layers. Nathaniel and Desmond pick which corners each character swaps.
- **Normal corners become fully readable** for wild racers. That is the feel point Austin raised; the sim plan below measures it.

## Sim plan v2: NOT STARTED (runs only when Austin approves a sim)

**Starting conditions**
- Live sim at proto-build HEAD, including the 0.67 knot, the 10% aero cap, the b3 mod-tier level floor (29f8431), the QTE 3-decimal rounding (c3ffc41) and the stat rename (53267c5).
- Grind 141 / 153 / 100 races (weak / average / strong). Boss win rates about 63–67%.
- The three layers above, with the proposed defaults, as a sim-side draft table (not `LINE_SET_C` until approved).

**Assumptions**
- 3 tracks per district, each exactly 10 turns.
- 20- and 30-turn races are 2 and 3 laps of the same track, so each corner repeats once per lap.
- No real track layouts exist in the repo, so placeholder layouts are built from each district's corner types and clearly labelled as placeholders.
- The opponent draws its line fresh each time it reaches a corner (once per corner per lap).
- Normal corners are deterministic for wild racers, so a player who has learned the district reads them perfectly.
- Wild racers follow the district layers on every corner. A story character follows them too, except on its swapped corners: a subset of normal corners (own line) and a subset of signature corners (own line + bluff) (Austin, 2026-11-12, corrected). The old rule that every racer reads the same on signature corners is superseded. Swap lists, lines and rates come from Nathaniel / Desmond; until they exist, criterion 1 is not run.
- Two player models per story character: one who has learned the character's swaps, and one who plays them on the district defaults (and district signature read).
- Signature-corner count, bluff rates and character inputs are swept or taken from Nathaniel / Desmond, never invented as final values.

**Success criteria**
1. Learning a story character pays off: a player who has learned the character's swaps does clearly better against them than one playing them on district defaults, and the character's bluffs don't wipe out that payoff. Reported per character once their inputs exist. (Replaces the old "read edge vs wild racers" criterion, 2026-11-12.)
2. Balance holds: boss and lieutenant win rates within the usual margin, grind stays 141 / 153 / 100, walls unchanged; otherwise report the shift.
3. Signature corners are measurably less predictable than normal corners.
4. Austin's feel concern: report, per district, how much of a wild race is fully readable vs bluff.

"Clear" = a gap of at least 5 pp with the same sign in all 9 batches (N = 4000, seeds 20261113–15, race lengths 10 / 20 / 30).

**Needs from the build (Gordon):** corner IDs with a `signature` flag per track; a wild-or-named tag per racer so the line lookup picks district default, signature or personal table.

> The earlier "Proposed sim (paused)" below is superseded by Sim plan v2.

## Rule (Austin, relayed by Nathaniel)
- Each district has signature corners. On them, **every** racer in the district (wild racers, lieutenants, crew bosses) runs the same standard line and bluff. *(Superseded 2026-11-12: story characters swap some normal and some signature corners; see the three-layer section.)*
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
