# shots7: HUD text legibility (Austin 2026-11-11: "Text is really difficult to read")

## Finding 1 (implementation, FIXED): non-integer browser scaling
The web export filled the browser window with a **non-integer nearest** scale: 2.25x at 1920x1080 and 1.6x at 1366x768
(measured from the canvas bbox in `before_live/*/1_plan_entry.png`, where the row run-lengths are 2/3 px and 1/2 px).
The HUD text is 1-bit with 1-px stems, so those stems came out 2 or 3 (1 or 2) screen px wide and the letters broke up.
At 1280x960 the scale was exactly 2x and clean (0 % mismatch against a 2x block upscale).
`art_direction.md` A.5:115 asks for an "integer **nearest**" upscale, and :141 for a "nearest-upscale to the window".
**Fix:** `godot/scripts/main.gd` `_fit_scale()` uses whole-number scaling (`CONTENT_SCALE_STRETCH_INTEGER`) whenever the window fits 2x
or more, and stays fractional below 2x so a small window is not shrunk to 1x. 1920x1080 is now 2x (1280x960, centred) and every
pixel is the same width. Display settings (640x480, viewport stretch, keep aspect, `project.godot`) are unchanged.
Trade-off: at 1080p the frame is 11 % smaller than before (2x vs 2.25x), but it is crisp.

## Finding 2 (design-level, NOT changed): the approved text itself is small and thin
`composite_native_godot_vs_arthur.png`: at native 640x480 the build's HUD text matches Arthur's approved frames pixel for pixel
(the same NimbusSansNarrow-Bold stand-in at 9-13 px, rendered 1-bit with a 1-px INK shadow, `art/ui/line_select_cam/post_lsc.py:13,34-37`).
- Sizes in use (hud.gd t2 calls): 9 px x4, 10 px x11, 11 px x14, 12 px x9, 13 px x5, 26 px x1.
  Cap height: 9 px gives 7 px caps and 5 px x-height; 11 px gives 8 and 6; 13 px gives 10 and 7.
- A narrow vector font forced to 1-bit at these sizes merges letters, the same way in PIL and in Godot: "turn-in" reads "tum-in",
  "Enter SET" reads "EnterSET", and "ATK" reads "AT K" in Arthur's own chip. B.5 (`art_direction.md:253`) asks for a "Bitmap-style font".
  The build still uses the stand-in (`godot/fonts/README.md`).
- Contrast (WCAG, text against a PS1 50/50 PANEL over the scene, full table in `contrast.txt`) is fine over fog and road,
  but it fails where a panel crosses a bright guardrail or lamp pool:
  - SUB 2.07, L_DIM 1.88, TODO 1.20, L_DIMMER 1.03, DIMT 1.30 over the guardrail.
  - White on ATK green #2CB84A is 2.60, and the 'none drawn' red is 2.40.

## Files
- `before_live/<WxH>/`, `after_live/<WxH>/`: the live web build in headless Chrome at 1280x960, 1920x1080 and 1366x768 (`tools/live_shots7.mjs`).
- `before_native/`: native 640x480 frames from `tools/run_shots.sh`. The HUD drawing is unchanged, so after = before at native.
- `composite_before_after_1920x1080.png`: Plan the Line, the B.5a panel with the corner plate, and the timer, all at true screen pixels.
- `composite_fullwindow_1920x1080.png`, `composite_native_godot_vs_arthur.png`, `contrast.txt`, `parity.txt`.
