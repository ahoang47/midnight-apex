# Unapproved mockups (Art)

Concept and UI mockups for review. Not approved by Austin. Proposals only; anything approved moves out of `unapproved/arthur/` into the docs or assets. Exception: the `tones/` blend50 values are approved as art_direction B.2a. Build scripts are included. Blender scenes, raw passes, full-size CRT renders and logs are left out to keep the repo small.

**Naming (2026-11-12):** older mockups in this folder predate the canon that choices, stances and colours are always POW / EN / HAN, and that IN / MID / OUT is visual only — road lane markers, lane-chip text, and where chevrons sit (`design/01-system-overview.md`, 4cdd1bc). Embedded HUD labels, and some filenames, still use Attack / Defend / Neutral, ATK / DEF / NEU, or outside / center / inside. Those frames were not re-rendered. `line_preview/` is being re-rendered separately and is not covered here.

Filenames that still use the old visual-lane words (outside / center / inside = OUT / MID / IN):
- `race_state_study/entry_matrix/*_{outside,center,inside}.png`
- `race_state_study/resolution_test/comparisons/` and `native/`: the same suffixes on the 640 vs 960 frames

HUD frames whose on-screen chips or captions may still show the old stance names include `lane_chain/`, `line_clash/`, `pattern_read/`, `psx_road_test/`, and `race_state_study/`.

- `lane_chain/`: race HUD mockups (v4, v5 entry plan and apex replay)
- `overworld/`: Harbor Flats overworld mockup
- `tones/`: colour tone study. `blend50` is the approved night palette (art_direction B.2a)
- `crt/`: CRT shader comparison sheets (librashader)
- `pattern_read/`: A/B layouts for showing a locked line
- `race_state_study/`: fixed-chase race-state study, rival Entry matrix with the proposed player **Line Lock** selector, and the 640 vs 960 resolution test (experiment only)
- `psx_road_test/`: unapproved Godot before/after of the line-select Entry frame with pack-based PSX roads, plus sharp-UI variants (new B.5c)
- `line_preview/`: unapproved Godot B.5d line-preview frames (flat stance-coloured chevrons on a pack road, copy of Gordon's two-corner scenes)
