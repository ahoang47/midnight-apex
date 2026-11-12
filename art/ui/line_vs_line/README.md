# Corner playback: line vs line (approved, art_direction B.5a)

These are the reference frames for the corner-playback HUD. It shows the LINE LOCKED panel with a YOU row and a RIVAL row.
- Both full lines are face up from the start.
- The column being played gets the amber outline.
- The RESULT row fills in as each phase plays.
- The corner plate shows the current phase.

The scene is the Touge hairpin from `art/ui/line_select_cam`.

The sample lines are:
- Player: NEU > DEF > ATK
- Rival: ATK > ATK > DEF

That gives a LOSS at Entry, a WIN at the Apex and a LOSS at Exit.

## Frames (1280x960 = 640x480 native, 2x nearest)
- `a1_entry_line_vs_line.png`: Entry, from the chase camera. The rival leads on the outside.
- `a2_apex_line_vs_line.png`: Apex, from the raised outside view. The player is ahead on the inside.
- `a3_exit_line_vs_line.png`: Exit, from the closer rear-quarter camera (`pb_exit`, 2026-11-11). Both cars read clearly and the rival pulls away on the inside.
- `line_vs_line_sheet.png`: A1 to A3 at full size. The tiles are pixel-identical to the frames.

The lines, gaps and camera numbers are illustrative. Rival Apex and Exit lanes reuse the Entry lane = stance placeholder.

## Pipeline
- Scene: `build_clash.py`. It is the line_select_cam scene with both cars placed per phase.
- HUD: `post_clash.py` writes option A, which is approved. It also writes option B (clash beats), which is not approved, and only its own working copy under `unapproved/arthur/mockups/line_clash/` uses it.
- Aliasing follows B.5c:
  - Overlays are drawn at native 640x480 with no AA and binary alpha.
  - RGB555 + 4x4 Bayer is applied once, then there is a single 2x nearest upscale.
  - The contact sheet is built at full size.
- Check: `../line_select_cam/verify_b5c.py`.
- To rebuild, run `run.sh`. It needs the box working copies under `/workspace/mockups/`.
