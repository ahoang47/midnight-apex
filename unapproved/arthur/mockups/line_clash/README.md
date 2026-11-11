# Corner playback: line vs line (A) and clash beats (B) (UNAPPROVED PROPOSAL)

> Option A (line vs line) was approved 2026-11-11; see `design/art/art_direction.md` B.5a and `art/ui/line_vs_line/`. Option B stays unapproved.

This is a proposal only. Austin has not approved it. It shows two options for the corner playback after the line is locked, so they can be compared. It uses the same Touge hairpin scene and pipeline as `../line_select_cam/`.

The sample lines are:
- Player: NEU > DEF > ATK
- Rival: ATK > ATK > DEF

The result of each phase follows the stance rules (ATK beats NEU, NEU beats DEF, DEF beats ATK):
- Entry: the player loses (ATK beats NEU).
- Apex: the player wins (DEF beats ATK).
- Exit: the player loses (DEF beats ATK).

The cars are placed to match each result:
- Entry: the rival leads on the outside.
- Apex: the player gets ahead on the inside.
- Exit: the rival pulls away on the inside.

## A: Line vs line (Austin's version)
This is the LINE LOCKED panel from line_select_cam frame 4 with a rival row added.
- Both full lines are face up from the start of playback. There are no face-down cards and no flips.
- Only the current phase is highlighted, and the RESULT row fills in as each phase plays.
- The cameras are the chase camera at Entry, the raised outside view at the apex, and the exit view.

Files:
- `a1_entry_line_vs_line.png`
- `a2_apex_line_vs_line.png`
- `a3_exit_line_vs_line.png`

## B: Clash beats (Arthur's version)
Playback holds briefly at each phase.
- Flat letterbox bars appear. The top bar shows "<PHASE> CLASH" and who won.
- The two stance cards slam in from opposite sides of the screen, with flat speed bars trailing behind them.
- The winning card stays whole. The losing card splits along a hard jagged crack into two halves, with three angular chips and a flat impact star. There is no glow and there are no particles.
- The winner's car is about 2.5 m further ahead than in A.
- The bottom bar tracks the results so far.
- The rival's card is shown as it slams in.

Files:
- `b1_entry_clash.png`
- `b2_apex_clash.png`
- `b3_exit_clash.png`

## Comparison sheet
`line_clash_comparison_sheet.png` has row A, labelled "A  LINE VS LINE", on top and row B, labelled "B  CLASH BEATS", below.

## Not specs
- The lines, results, timings and car gaps are illustrative.
- The rival's Apex and Exit lanes reuse the Entry lane-to-stance rule (ATK = outside, DEF = inside). That rule has not been approved for Apex or Exit.

## Art and pipeline
The pipeline is the same as line_select_cam:
- blend50 tone with hard 3-step pale-sodium pools and bloom (.22, 0)
- EEVEE at 640x480, 1 sample, filter 0
- the HUD is drawn at native resolution with 1-bit text and PS1 50/50 panels
- RGB555 + 4x4 Bayer, then a 2x nearest upscale

Stance chips are ATK #2CB84A, DEF #E8282C and NEU #F0C828.

To rebuild, run `./run.sh`. The .blend file and raw passes stay on the box only.
