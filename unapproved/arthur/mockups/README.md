# Unapproved mockups (Art)

Concept and UI mockups still awaiting approval. Anything approved moves out of `unapproved/arthur/` into `art/`. Exception: the `tones/` blend50 values are approved as art_direction B.2a. Build scripts are included. Blender scenes, raw passes, full-size CRT renders and logs are left out to keep the repo small.

On 2026-11-13 Austin approved deleting these superseded or experiment-only studies. They are gone from the tree and remain in git history: `lane_chain/`, `line_clash/` (option A already lives in `art/ui/line_vs_line/`; option B was not chosen), `psx_road_test/`, `crt/`, `race_state_study/`, and `pattern_read/`.

On 2026-11-19 Austin approved and promoted:
- Cel A study → `art/mockups/cel_shaded/`
- mountain districts pass 5 (every road 7.5 m) → `art/mockups/mountain_districts/`
- line preview → `art/ui/line_preview/`
- resource meters → `art/ui/resource_meters/`

He also asked to delete the two-corner tests (`experiments/cel_two_corner/`, `experiments/wangan_two_corner/`). Those are gone; git history keeps them.

Some older frames still in this folder (for example `tones/entry_*.png`) predate the POW / EN / HAN and IN / MID / OUT naming and were not re-rendered.

- `overworld/`: Harbor Flats overworld mockup
- `tones/`: colour tone study. `blend50` is the approved night palette (art_direction B.2a)
- `districts/`: earlier unlit PSX district frames (pre-Cel A comparison source)
- `tight_districts/`: cat-and-mouse stills; only Wangan is 7.5 m (touge 6.0 m, street 5.8 m), so this pass was not promoted with the 7.5 m set
- `mountain_districts/`: earlier passes (v1–v4) only; v5 is in `art/mockups/mountain_districts/`
