# Cel-shaded pass (experiment, unapproved)

Austin, 2026-11-14: "As an experiment, could you do a pass as a cel-shaded style?"

This is a test look only. It is not a direction. The approved look is still the unlit PSX frames in `../../mockups/districts/`, and none of those files were changed.

`cel_compare_sheet.png` puts each district in a row: the current frame, then cel A, then cel B.

| File | What |
|---|---|
| `touge_cel.png`, `street_cel.png`, `wangan_cel.png` | **A:** cel pass with the existing RGB555 + 4×4 Bayer PSX pass kept |
| `*_cel_clean.png` | **B:** the same cel pass with no dither (clamped 8-bit) |
| `cel_compare_sheet.png` | current / A / B for the three districts |

Each frame keeps the E3B Entry chase frame from `../../mockups/districts/`. That means the same camera, cars, road widths, touge grade, chevrons, dressing and palette (TXR navy fog, Mercury teal, every lamp #F0C894). It's rendered in Godot 4.6.3 (GL Compatibility), with the 3D at 640×480 and a 2× nearest upscale. The E3B HUD is drawn on top at 1280×960 after the post pass, so no cel or ink code touches it. The HUD panel pixels match the originals exactly.

## How it's done
- **Toon ramp (3 bands).** Everything stays `unshaded`. The light is computed in the fragment shader against one fixed key direction (the car key, 0.4/0.8/0.3), then stepped into lit 1.0 / mid / shadow bands. The shadow band leans to navy and is never warm. Props and road strips have no usable normals, so they use faceted normals from screen derivatives. Cars use their smooth normals. Emit_ surfaces (signs, windows, lamp heads) and the #F0C894 lamp heads skip the ramp and stay full-bright.
- **Cars.** The painted albedo is posterised in sqrt-luma steps so baked gradients become flat blocks. The spec becomes one hard highlight, and the painted env reflection is stepped into 3 levels.
- **Flatter textures.** Every environment texture goes through an edge-preserving flatten in the shader: a ring of 8 taps with outlier rejection gives a base colour, the base is posterised (10 sqrt-luma steps), and strong painted marks are added back on top. Grain and noise go flat, while lane lines, kerb paint, window frames, sign text and rock cracks stay. The sodium pools painted into the road come out as 3–4 hard rings. The road uses a wider radius (6 texels) than props (4). The rejection step is there so thin lane lines don't halo or double.
- **Ink (screen-space, not inverted hull).** Each frame is rendered two more times with the global `cel_gbuf` = 1 (view normals) and 2 (log-packed linear depth). Every shader draws those passes through its own vertex code, so the PSX snap lines up pixel for pixel. Decals are hidden for those passes, and glows and chevrons write nothing. In `shaders/post.gdshader`:
  - A pixel is inked when a 4-neighbour is clearly farther (silhouette). Only the near side gets the line, so lines are never doubled.
  - It's also inked when the normal turns hard against its right or down neighbour (crease).
  - Lines are always 1 px at 640×480 (2 px in the frame) and dark navy #040810, not black. They fade into the district fog. The rear-view inset gets its own G-buffer, flipped the same way as its colour.
  - The chevrons are kept off the G-buffer, so they stay flat paint with no ink.
- The G-buffer values sit in the 0.25–1.0 range because the Compatibility colour buffer doesn't read back linearly in the darks (0.04 comes back as 4/255).

## Files
- `godot/`: real files are copies of the districts scene and script plus the cel shaders (`shaders/cel.gdshaderinc`, `scroll`, `env`, `car`, `car_lit`, `sky`, `glow`, `fx`, `chevron`, `post`) and `project.godot` (with the `cel_gbuf` shader global). Everything else (art, assets, HUD, Gordon's scripts) is symlinked at stage time from `../../mockups/districts/godot` by `stage.py`.
- `godot/scripts/district_preview.gd`: the districts script with only three changes: the three standard frames only, cel_k/flatten off on Emit_ surfaces, and `_capture` doing the G-buffer passes and writing both flavours.

## Rebuild
`./run.sh` (or `ONLY=touge ./run.sh`). Debug switches: `CEL_NOINK=1` (ramp only), `CEL_DEBUG=1` (dumps the G-buffers to /tmp), `CEL_ALL=1` (the cat/mouse frames too, not reviewed).

## Honest read
- **What works:** The ink gives the cars, guardrail, jersey barriers, poles and shop edges a clear, hand-drawn read without any glow. The banded sodium pools and the flattened rock and asphalt feel painted rather than filtered. A (dithered) holds together better with the rest of the PSX art.
- **What doesn't:** At night most surfaces sit in the dark end, so the 3 bands barely show on the environment, and the "cel" read comes mostly from the ink and flat textures. A day or dusk scene would show the ramp far more. Some asphalt still breaks into small speckles where the base sits on a posterise step, and B (clean) shows the 8-bit steps harder. The ink also goes busy on distant cedar cards before the fog takes it.
