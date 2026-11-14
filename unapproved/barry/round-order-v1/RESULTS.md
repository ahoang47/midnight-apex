# Round-order v1 — one district per round vs mixed free-choice rounds

Barry / 2026-11-13. Study only, under `unapproved/barry/round-order-v1/`. No `sim/` or `design/` edits. No commit.

Compares a campaign restructure **Round 1 = Street, Round 2 = Wangan, Round 3 = Touge** against the live free-choice mixed-district rounds (default example: R1 Touge / Wangan / Street, R2 Wangan / Street / Touge, R3 Street / Touge / Wangan; `OPTION_A_ROUND_STEP` = 1.30 on whichever crew opens R2 or R3).

## Source of numbers

Combat win rates, limp, and lock are **live G2_slant_m10** on the **touge-lines-v1 draft track set** (one fixed tune per district, gravity on, no line edits). Quoted from `unapproved/barry/touge-lines-v1/analysis.json` (`results_baseline.npz`, 9×1000, seeds 20261112–20261120, `r = 1.07` = live `MOD_CAP_FRACTION`). Tunes: Street 50/25/25, Wangan 25/30/45, Touge 40/30/30. Lengths map to official encounter caps in `cli.py`: wild/grind = 10, lieutenant = 20, crew boss = 30.

No new 9×1000 was required: at-cap target `r` does not change with campaign order (see §1.30 below). A full `LADDER_R` sweep (kids 1.13 through old head 1.06) was **not** rerun. 20-turn at `r = 1.07` is a slightly conservative stand-in for lieutenants at cap (it matches designed mature #2 exactly; kids/mature #1 are designed easier). 30-turn at `r = 1.07` is the right at-cap boss figure under live cap rules.

`progression.py` is **stale** (grind v8c, still `PROGRESSION_MOD_CAP_FRACTION = 1.05`, card-draw oracle). **Not refit.** Budget, level cap, never-grind `r_skip`, and grind-to-cap counts below are from that XP model only, and are **not** G2 combat win rates. Do not quote `progression.run()` win rates as shipping numbers.

## What “one district per round” means

Live campaign (canon 11/12, `design/01`, `pitch.md`): **one crew per district**, rematched each round, leveled up between rounds; within a round the player freely picks which of the three district crews to challenge; reputation for the next rematch is earned in the other districts. 9 crew-encounters, 63 story rungs, then Finale.

The restructure is ambiguous against that spine. This study uses two readings:

- **A — drop-in, 9 encounters (primary tables).** Still 3 crews per round, still 1.30 on the first crew of R2/R3, still the same unlock markers `(2,1)` / `(2,3)` / `(3,3)`. All three slots in a round are the same district: R1 Street×3, R2 Wangan×3, R3 Touge×3. Budgets and level caps are **identical** to the current season because they are keyed by play position, not district. This contradicts “one crew per district, rematch each round.”
- **B — story-literal, 3 crews (footnote only).** One Street crew, one Wangan crew, one Touge crew, no rematches. `check_order()` rejects this; unlocks `(2,3)` and `(3,3)` have no third crew; the Option A walk shrinks the season to R3 boss cap L78 / Finale caps L100–112 vs live L150 / L154–162. **Not a refit.** Combat per-round rates are the same as A (one district’s 10/20/30); only the XP ladder changes.

If the intent is a Street chapter, then a Wangan chapter, then a Touge chapter, Nathaniel has to pick A or B (or something else) before anyone wires it.

## 1.30 does not change at-cap combat `r`

`OPTION_A_ROUND_STEP = 1.30` and `CAP_ALLOC_ROUND_OPEN` raise the **budget and level cap** of whichever crew opens R2 or R3. At cap, lieutenant target `r` is still `LADDER_R` and the crew-boss at-cap ratio is still the live mod cap (`1.07` under G2; the stale model still writes `1.05`). The step is felt on **skip-grind**, not on a player who has ground to the cap.

Never-grind boss `r_skip` from the stale XP walk is the same in current default order and reading A, because the slots are the same:

| Slot | Opener? | Cap L | Story L (never grind) | `r_tgt` | `r_skip` | Races to cap |
|---|---|---:|---:|---:|---:|---:|
| R1 crew #1 boss | no | 12 | 4 | 1.050 | 1.001 | 34 |
| R1 crew #3 boss | no | 36 | 15 | 1.050 | 0.927 | 94 |
| R2 crew #1 boss | yes | 69 | 49 | 1.050 | 0.932 | 96 |
| R2 crew #3 boss | no | 93 | 63 | 1.050 | 0.880 | 151 |
| R3 crew #1 boss | yes | 126 | 101 | 1.050 | 0.906 | 131 |
| R3 crew #3 boss | no | 150 | 116 | 1.050 | 0.861 | 186 |

The opener is not uniquely the worst skip in its round — later crews in the same round sit further behind the climbing cap. Under the new order, the R3 opener is **Touge** at `r_skip = 0.906` if the player has not ground. That was not resimulated. At-cap Touge 30-turn is already 40.9% for 60/60; skip-grind on the R3 opener would be worse. Do not invent a win rate for `r = 0.906`.

Always-to-cap grind across the 9-crew season + Finale is 2650 races in the stale model (same in A and in the current order). That count is a v8c artifact, not a shipping target.

## At-cap difficulty curve (district-fixed tune, `r = 1.07`)

Win rates are percent. “Mix” for the current order is the equal-weight mean of the three districts in that round (same every round, because every round still contains all three). Free choice can deviate from the mix; the default example path is listed separately.

### Average player, 60/60

| Order | Round | Districts | Grind 10 | Lt 20 | Boss 30 |
|---|---:|---|---:|---:|---:|
| Current (mix) | 1 / 2 / 3 | all three, any order | 69.6 | 64.0 | 55.3 |
| Current (default path) | 1 first crew | Touge | 65.2 | 53.5 | 40.9 |
| Current (default path) | 1 mid / last | Wangan / Street | 68.8 / 74.7 | 70.6 / 67.8 | 67.6 / 57.4 |
| Current (default path) | 2 first / last | Wangan / Touge | 68.8 / 65.2 | 70.6 / 53.5 | 67.6 / 40.9 |
| Current (default path) | 3 first / last | Street / Wangan | 74.7 / 68.8 | 67.8 / 70.6 | 57.4 / 67.6 |
| **New** | **1** | **Street only** | **74.7** | **67.8** | **57.4** |
| **New** | **2** | **Wangan only** | **68.8** | **70.6** | **67.6** |
| **New** | **3** | **Touge only** | **65.2** | **53.5** | **40.9** |

Deltas, new minus current mix, 60/60:

| Round | Grind 10 | Lt 20 | Boss 30 |
|---:|---:|---:|---:|
| R1 Street | +5.1 | +3.8 | +2.1 |
| R2 Wangan | −0.8 | +6.6 | +12.3 |
| R3 Touge | −4.4 | −10.5 | −14.4 |

### Strong player, 80/80

| Order | Round | Grind 10 | Lt 20 | Boss 30 |
|---|---:|---:|---:|---:|
| Current (mix) | 1 / 2 / 3 | 97.3 | 96.5 | 96.1 |
| New R1 Street | | 98.8 | 98.3 | 98.4 |
| New R2 Wangan | | 95.6 | 97.0 | 97.6 |
| New R3 Touge | | 97.5 | 94.1 | 92.2 |

Perfect-read 1.0 is 100.0 at every district and length (same study). The wall below is a 60/60 pacing / heat problem, not a “can this course be won” problem.

### Per-track spikes inside the new rounds (60/60, district-fixed)

New R1 Street bosses are not uniform. S1 (Shibuya Grid) 30-turn is a first-round wall; S3 is not.

| Track | 10 | 20 | 30 |
|---|---:|---:|---:|
| S1_Shibuya_Grid_CW | 69.6 | 60.0 | **48.5** |
| S1_Shibuya_Grid_CCW | 76.0 | 64.0 | **50.5** |
| S3_Shinjuku_Underpass_CW | 74.2 | 73.5 | 65.7 |
| S3_Shinjuku_Underpass_CCW | 79.0 | 73.6 | 64.7 |
| W1_Bayshore_Run_CW | 73.2 | 76.8 | 73.4 |
| W1_Bayshore_Run_CCW | 72.7 | 73.1 | 73.9 |
| W3_C1_Outer_CW | 61.9 | 62.9 | 56.9 |
| W3_C1_Outer_CCW | 67.3 | 69.6 | 66.3 |
| T_Uphill | 61.9 | 50.7 | **37.4** |
| T_Downhill | 68.4 | 56.3 | 44.4 |

## Limp and lock (60/60, district-fixed, clash-share / corner-share)

| District | Lock 10/20/30 | Counter-lock 10/20/30 | Limp 10/20/30 |
|---|---|---|---|
| Street (new R1) | 59.3 / 70.5 / 74.8 | 23.4 / 35.4 / 40.2 | 3.6 / 12.8 / 16.9 |
| Wangan (new R2) | 57.5 / 67.7 / 72.0 | 19.5 / 29.4 / 34.3 | 6.5 / 14.7 / 19.2 |
| Touge (new R3) | 38.8 / 57.2 / 66.8 | 13.7 / 31.0 / 41.0 | 4.3 / 18.6 / **27.1** |
| Current mix (all rounds) | 51.9 / 65.1 / 71.2 | 18.9 / 31.9 / 38.5 | 4.8 / 15.4 / 21.1 |

Touge locks *fewer* corners than Street or Wangan, but limps harder late: 27.1% of 30-turn clashes are a three-bar lock, vs 19.2 Wangan and 16.9 Street. New R3 will feel like late-race resource collapse, not a lock lottery. Per-track limp at 30 is also ugly on some non-Touge layouts (W3 CCW 30.2, W1 CCW 24.1, both S1 variants ~22.6), but those are single-variant spikes inside an otherwise softer round. Under the new order the whole of R3 sits on Touge’s 18.6 / 27.1 at 20 / 30.

## Spikes and dips

- **New order, 60/60:** R1 is a slightly easier-than-mix start, except **S1 30-turn bosses at 48.5–50.5**, which can wall a first-round crew boss if S1 is the layout. R2 Wangan is the most comfortable round of the season (20/30 **above** the current mix by 6.6 / 12.3 pp; 10-turn dips 0.8 pp). R3 is a sharp crash: lieutenants 53.5, bosses 40.9, uphill bosses 37.4, 30-turn limp 27.1. That wall lasts the entire round (three crews under reading A, or the last chapter under B) and is immediately followed by Finale Myth #1, which is also Touge.
- **Current mix, 60/60:** the campaign-average curve is flat (69.6 / 64.0 / 55.3 every round). The Touge 40.9 boss and 53.5 lieutenant still appear **once per round**, but the other two crews in the same round are much softer. Free choice lets a player put Street or Wangan first and attempt Touge when ready.
- **Current default example path is already front-loaded:** R1 opens on Touge (same 53.5 / 40.9 wall as new R3, but as the first crew of the game). That order is an example for reports and tests, not a locked play order — but anyone following it hits the hardest long races first.
- **80/80:** almost flat in both structures. New R3 Touge 20/30 is 94.1 / 92.2 vs a 96.5 / 96.1 mix. Strong players will not feel this restructure as a difficulty story. The problem is the average-at-cap player.

## Recommendation

**Do not ship one-district-per-round as a pacing / smoothness change.** It does the opposite for a 60/60 player: a comfortable Street-then-Wangan midgame, then a full-round Touge wall (lieutenants below the mid-60s, bosses at 41%, limp 27% at 30 turns). The current mixed rounds already expose that same Touge cell once per round, but they average it with Wangan and Street and leave district order in the player’s hands.

If the goal is a narrative mountain climax (Street city chapter → Wangan highway chapter → Touge finale chapter), that is a story call, not a balance improvement. It should not lock until Touge 20/30 at cap is closer to the other districts — touge-lines-v1 already found that default-line edits are the wrong tool for that gap (one tune already covers uphill and downhill; 8/10 corners are signature). Concentrating Touge in R3 also stacks three Touge crew bosses against Finale Myth #1 Touge and Summit Touge.

A cheaper alternative that keeps canon 11/12: leave mixed free-choice rounds, and change only the **default / suggested** example order to Street → Wangan → Touge *within each round*. That gives a gentler recommended path without deleting rematches or concentrating the wall. The live default example (Touge first in R1) is itself a first-crew spike for anyone who follows it.

Reading B (three crews, no rematches) is a much larger design change than a reorder. Do not treat the Option A 3-crew walk as a plan: XP, caps, unlocks, and finale budgets would all need a real refit, which this study did not do.

## What would need to change in docs and code (not done)

- `design/01-system-overview.md` — crew-ladder paragraph (free order, rematch, play-position budgets, 216 legal orders); wholesale “end of Round 1” after a Street-only chapter; aero after the first R2 crew, now always a Wangan rematch (A) or the only Wangan crew (B). Still also says “3 tracks per district” (already flagged in touge-lines-v1; Austin 2026-11-12).
- `design/02-equations-reference.md` — `DISTRICTS` / `DEFAULT_CREW_ORDER` / free-order budget notes.
- `design/07-economy-and-mods.md` — season runner, “three district crews each round,” `campaign` tests that require a permutation of `DISTRICTS`.
- `design/08-skill-parity.md` — wholesale at end of Round 1.
- `sim/velocity_shift/equations.py` — `DEFAULT_CREW_ORDER`.
- `sim/velocity_shift/progression.py` — `check_order()` (rejects any round that is not a permutation of all three districts), `all_orders()` (216), docstring. Stale XP model must be refit separately, and **must not** be quietly pointed at G2; if reading B is chosen, the whole ladder, unlock flags, and Finale caps have to be redesigned.
- `sim/tests/test_progression.py` — asserts R2/R3 openers on the current default order.
- `story/canon.md` 11, 12, and beat 5; `plot.md` rematch-2 / rematch-3 beats; `pitch.md`; `dialogue_outline.md` (district sections “in whichever order the player picks”; Myth first sightings after each R1 district; “end of Round 1: all three Round 1 crew bosses”).
- Unlock flavor still maps under reading A, but `(2,3)` and `(3,3)` break under reading B and would need new rules (e.g. end of R2 / end of R3).

## Story / narrative (Nathaniel)

Primary work, and larger than a crew-order tweak.

- Canon 11/12 and the pitch spine (“one crew per district, rematched each round, reputation earned in the other districts”) do not survive a one-district-round structure without a rewrite. Reading A needs three Street crews, three Wangan, three Touge, or the same crew run three times in one chapter — neither is the current rematch story. Reading B drops rematches, rematch taunts (canon 27 into R2/R3), and “the boss leveled up the whole crew.”
- Myth Driver first sightings are written as **after the PC clears that district in Round 1** (#1 after R1 Touge, #2 after R1 Wangan, #3 after R1 Street). If R1 is Street-only, #1 and #2’s first sightings move or they appear in the wrong district; #3 lands at the end of R1, then you do not see Street again until Finale Myth #3.
- Finale order is locked Touge #1 → Wangan #2 → Street #3 → Summit Touge. After a Touge-only R3, the player goes straight from the last Touge crew boss into Myth #1 on the same mountain, leaves for Wangan and Street, then returns for Summit. That is a pacing / location problem, not just a line rewrite.
- “End of Round 1: wholesale” after a Street-only chapter; debt/aero after the first R2 crew (always Wangan under a locked order); betting at end of R2 (end of Wangan).
- Free-choice and locked-ladder dialogue (“the other crews won’t take you while you’re in a feud”; “go prove it in the other districts”) goes away or has to be rewritten around intra-district crews.

## Who needs to act

Austin’s read that Nathaniel is the only one is **close but not quite**. Combat numbers do not require a Gordon/Arthur pass to decide the structure, but shipping it does.

| Person | Need to act? | What |
|---|---|---|
| **Nathaniel** | **Yes, primary.** | Pick reading A vs B (or keep mixed rounds). Rewrite canon 11/12, plot rematches, district chapter arcs, Myth first-sighting beats, finale-after-Touge pacing, free-choice / feud dialogue. This is the blocker. |
| **Desmond** | **Yes, if the structure is approved.** | `design/01`, `02`, `07`, `08` (and any canon rewording he owns). Also the lingering “3 tracks per district” line, independent of this study. |
| **Gordon** | **Yes, if approved — wiring, not art.** | `DEFAULT_CREW_ORDER`, `check_order` / `all_orders` (216 permutations become illegal), progression tests, crew-select / overworld gating that currently offers all three districts each round. |
| **Arthur** | **No new track art.** Overworld / hub flow only if the map currently presents all three districts as simultaneously open each round; no district layout work in this study. |
| **Barry** | **Not this pass.** Progression stays stale; do not refit. Later: G2-aware progression (live 1.07 cap, drop the card-draw oracle), and a full ladder redesign only if reading B is chosen. The Touge 20/30 at-cap gap is a known combat issue from touge-lines-v1, not something an order change fixes. |

## Files

- This writeup: `unapproved/barry/round-order-v1/RESULTS.md`
- Supporting budget walk: `unapproved/barry/round-order-v1/comparison.json` (includes the unrefitted 3-crew walk as a footnote)
- Combat source: `unapproved/barry/touge-lines-v1/analysis.json` and `RESULTS.md`
