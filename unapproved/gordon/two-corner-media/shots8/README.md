# shots8: HUD text at display resolution (Austin 2026-11-11 21:41: "I think you have to continue upressing")

## What changed
- `godot/project.godot`: `window/stretch/mode` changes from `viewport` to `canvas_items`, still 640x480 base and keep aspect.
  `_fit_scale()` from shots7 still picks a whole-number scale at 2x or more and a fractional one below that.
- **World (unchanged look):** the 3D world was already rendered into a 640x480 `SubViewport`. It is shown through the post `TextureRect`,
  which samples nearest (`post.gdshader` `filter_nearest`, `px = floor(uv * 640x480)`). The RGB555 + 4x4 Bayer dither and the bloom still work on
  640x480 pixels, and the screen upscale is still nearest at whole numbers (2x at 1920x1080, 3x at 2560x1440).
- **HUD:** the HUD is still laid out in 640x480 design units, so positions, sizes, colours and the font face match Arthur's frames.
  The canvas transform scales it to the window, and glyphs are drawn at size x scale through the viewport's automatic font oversampling
  (`hud.gd _font`: oversampling 0 = follow the viewport, greyscale antialiasing, light hinting, automatic subpixel positioning).
  - The 1-unit INK text shadow and the 1-unit outlines and rules scale with the display: 2 px at 2x, 3 px at 3x.
    The four `draw_line` calls that used the default -1 width (always 1 physical px) now pass 1.0.
- **Departure from the art direction (UI only, Austin's direct request; flag for Arthur):**
  - `design/art/art_direction.md:115/:141` call for an integer nearest upscale of the whole frame, and `:242` locks "viewport stretch".
  - The mockups draw text 1-bit at 640x480 (`art/ui/line_select_cam/post_lsc.py:34`).
  - The HUD text is now smooth and drawn at window resolution. The world is unchanged.

## Not changed (still pixel-scaled)
The Godot stand-in **6x9 bitmap font** (`art/font_6x9.png`, from `spec/gen_art.py`) is still a texture scaled nearest. It is used by the main menu,
the debug box (CORNER / seed / F9 F10), the gap meter and TIMING - SPACE. It is crisp at 2x and 3x, but it renders unevenly at fractional scales
below 2x (see `after_live/1366x768/menu.png`). Moving those to the HUD font would be a face change, so that is a proposal and is not done here.

## Files
- `before_live/<WxH>/`, `after_live/<WxH>/`: the live web build in headless Chrome at 1920x1080, 1366x768, 2560x1440 and 1280x960
  (`tools/live_shots7.mjs`, PLAY_WAIT=4500). The screens are menu, Plan the Line at entry/apex/exit (B.5b stops, plate, timer), LINE LOCKED, B.5a playback and result.
  Each run uses a random seed, so the hands differ between before and after.
- `after_native/`: `tools/run_shots.sh` frames. These are now captured at the 1280x960 window (2x), not at 640x480.
- `composite_before_after_1920x1080_full.png`: the full window.
- `composite_before_after_1920x1080_zoom2x.png`: text areas at 2x zoom (Plan, B.5a with plate, timer with debug HUD and LINE LOCKED, result line).
- `composite_sizes_2_plan_apex.png`, `composite_sizes_6_playback_b.png`: before and after at every window size, in true screen pixels.
- `parity.txt`: `tools/run_parity.sh`, all PASS, max diff 0.0.
