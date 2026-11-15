# HUD fonts (B.5c, pixel-hard at 1280×960)

Copied into this folder for the two-corner Godot HUD. Runtime load in `scripts/hud.gd` `_font()` sets no antialiasing, hinting off, subpixel positioning disabled, oversampling 1, and the HUD layer uses nearest filtering.

## Nimbus Sans Narrow Bold / Bold Oblique, Nimbus Sans Bold
- Files: `NimbusSansNarrow-Bold.otf`, `NimbusSansNarrow-BoldOblique.otf`, `NimbusSans-Bold.otf`
- Source: URW++ base35 (identical to `/usr/share/fonts/opentype/urw-base35/` on this box). Nimbus Sans Bold is the heavier title face from Arthur's line-preview mockup (`unapproved/arthur/mockups/line_preview/godot/fonts/`).
- License: AGPL-3 with Font exception (embedding in documents/programs allowed). Full text: `LICENSE-URW-base35.txt` (Debian `fonts-urw-base35` copyright file).

## Archivo Black Regular
- File: `ArchivoBlack-Regular.ttf`
- Source: The Archivo Black Project Authors (Omnibus-Type); identical to the file in Arthur's mockup fonts folder and `/usr/share/fonts/truetype/sand-box/google/Archivo Black/`. Loaded as `hud.fa` for short labels, same as Arthur's `hud.gd` (paint currently uses Nimbus Sans Bold for heavy titles).
- License: SIL Open Font License 1.1. Full text: `OFL-ArchivoBlack.txt`.
