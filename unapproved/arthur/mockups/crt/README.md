# CRT filter pass on blend50 mockups

Runner: `librashader-cli` 0.12.1 (SnowflakePowered/librashader), OpenGL 3 runtime via GLFW + Mesa llvmpipe.
Shaders: shallow clone of https://github.com/libretro/slang-shaders.git (authentic RetroArch `.slangp` multi-pass presets).

## Input
- `entry_blend50.png` / `overworld_blend50.png` are 1280×960 = 2× nearest of native 640×480 RGB555+Bayer.
- Recovered lossless 640×480 with `[::2,::2]` / NEAREST downscale, verified round-trip.
- Primary CRT input: **640×480** (matches our HUD pixel grid). Output: **1920×1440** (3× integer).
- Bonus: Royale Kurozumi + Guest-Adv NTSC also at **2560×1920** (4×).
- Bonus 240p test: vertical nearest to 640×240 then CRT → 1920×1440 (see `crt_entry_240p_vs_480p_hud.png`).

## Featured presets (both scenes)
| file suffix | preset |
|---|---|
| `__raw` | 3× nearest baseline (no CRT) |
| `__royale_kurozumi` | `presets/crt-royale-kurozumi.slangp` (Sony BVM/PVM aperture-grille look) |
| `__guest_adv_ntsc` | `crt/crt-guest-advanced-ntsc.slangp` |
| `__lottes` | `crt/crt-lottes.slangp` |
| `__geom` | `crt/crt-geom.slangp` |
| `__easymode` | `crt/crt-easymode.slangp` |

Extras also rendered: `__zfast`, `__hyllian`, `__guest_advanced` (RGB, no NTSC).

## Sheets
- `crt_entry_zoom_sheet.png` / `crt_overworld_zoom_sheet.png` — **1:1 unscaled crops** side-by-side (no thumbnail downsample of the CRT mask).
- `crt_entry_240p_vs_480p_hud.png` — HUD legibility: 480p vs 240p input into easymode.
- `crt_royale_3x_vs_4x_zoom.png` — Royale mask resolution at 3× vs 4×.
