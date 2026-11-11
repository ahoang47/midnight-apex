# Phase 4 (2026-11-11): Godot only. Arthur's palette, all-docs pass, Plan the Line
Palette source: design/art/art_direction.md **B.2a** at origin/proto-build **55b9063** (55b90630ce777fa8f9fffac7c243dd341d158725).
Sim pin is unchanged at 212eaab. Display, art and UI only. Scoring, RNG and parity are untouched.

## Source table (value | used for | source file:line | conflict / note)
| Value | Used for | Source | Note |
|---|---|---|---|
| fog #0B172B | Street fog, sky horizon, bg | art_direction.md@55b9063:196-197 (B.2a); tones.py:19 blend50 | |
| fog 14-105 m | Street fog range | art_direction.md@55b9063:224 | mockup scene used 16-150 (tones/work/lane/build_v5.py:22); doc wins |
| zenith #010408 | both skies | B.2a :197; tones.py:19 | no Touge zenith anywhere, so B.2a is used |
| city glow: none | sky | B.2a; tones.py:19 cityglow None | old skyline glow band dropped |
| ambient #5575A0 ×0.8 | prelit road/verge/rail/cedar/props, facade walls | B.2a; tones.py:19 | |
| every lamp #F0C894, k 0.85 | lamp heads, glow sprites, pools (both districts) | B.2a :199; tones.py:20 | conflicts with B.3 Touge "sodium/white"; B.2a is newer and wins |
| pools 3 hard steps, k 0.09; decal ×1.8; ground lamp 0.55; vertex r 13 m | road textures | tones.py:20-21; tones/work/lane/build_v5.py:219-228,268-275; make_tone_tex.py:25-30 | |
| glow sprite: white core, 3 alpha bands, 1.5 m at 0.9 | glow_lamp.png, lamp billboards | make_tone_tex.py:31-38; build_v5.py:276 | was 3.0 m |
| bloom 0.22, threshold 0, glow-only, Gaussian r 3 | post shader + glow SubViewport | B.2a; tones.py:21; tones/work/lane/post_v5.py:22-25 | B.1 said "bloom on neon only"; B.2a is newer. lane_chain/v5 post uses .35/.25 two-radius bloom; B.2a 0.22 used |
| saturation 1.05 | post shader before RGB555 | B.2a; tones.py:21; pattern_read/compose_mockups.py:14 | |
| stars (90,100,150), 70 | sky strip | tones.py:21; make_tone_tex.py:14-23 | |
| sky gradient t^1.8 | sky strip | make_tone_tex.py:14-23 | |
| Street lamps every 24 m one side, 12 m offset other | Street | build_v5.py:117-120 (2026-11-10) | tokyo_v2/scene_v2.py:25 had 16 m alternating (2026-10-31); newest wins |
| asphalt (46,46,54) | both roads | art/mood/tokyo_v2/make_tex_v2.py:38 | only road recipe that exists |
| Street edge line (196,170,70) | Street road | make_tex_v2.py:51 | |
| Touge fog #2A3236, 8-55 m | Touge | art_direction.md@55b9063:220 (B.3, Q2 still open) | B.2a fog is the general palette; B.3 is the only Touge value, so it is kept |
| neon #FF3C8C/#3CC8FF/#C85AFF | Street signs | B.2 :213 (still applies per B.2a :203) | hues close to the stance colours dropped (B.5 reserves them for UI) |
| facades/windows | Street | B.1 pre-lit + B.2 (B.2a :203) | lit by B.2a ambient |
| ATK #E8282C, DEF #2CB84A, NEU #F0C828, dark text on yellow | HUD | Austin 2026-11-11; lane_chain/v5/post_v5.py:14; tones/work/lane/post_v5.py:14; pattern_read/compose_mockups.py:10 | supersedes godot-build-guide.md@55b9063:940-942 (#dc2626/#16a34a/#d97706) |
| AMBER/AMBER_D/EDGE/EDGE_D/INK/PANEL | HUD | lane_chain/v5/post_v5.py:15-17 | |
| segmented timer, 16 segs, off (69,49,38), "04.8s" | HUD | pattern_read/compose_mockups.py:47-53 | |
| PS1 50/50 semi panels | HUD | lane_chain/v5/post_v5.py:149-153 | |
| NimbusSansNarrow Bold/BoldOblique, 1-bit, 9-13 px | HUD | lane_chain/v5/post_v5.py:10-12,26 | crisp UI per B.5 "drawn at native resolution" + mockup fontmode '1' |
| POW = Attack, EN = Defend, HAN = Neutral | chips | lane_chain/v5/post_v5.py:59; design/01-system-overview.md:8 | |
| OUT = Attack, MID = Neutral, IN = Defend | entry strip + chevrons | art_direction.md@55b9063:216; design/06-pattern-read.md:4 | same rule as race_core.gd entry_tell |
| Neutral / NEU | all player-facing text | Austin Q6 2026-11-11 | the sim keeps letter S |
| world textures linear, car albedo mipmapped | shaders | Austin Q4; art_direction A.8 sketch (filter_nearest_mipmap → linear_mipmap) | post stays nearest (A.5 integer upscale) |
| 640×480 | render | Austin Q3; A.5 | |

## Display calibration (not doc values; `display.json palette.calib`)
road_amb_gain 1.7, road_vertex_lamp_gain 2.6, road_decal_gain 2.2, facade_amb_gain 0.35. These scale the mockup light terms onto our stand-in textures,
targeting entry_blend50.png (off-pool road ~(30,34,37), pool ~(100,87,70), sky ~(7,15,29)).

## Still PLACEHOLDER (appears nowhere)
Searched: design/ (every file, incl. art/art_direction.md@55b9063, art/world_notes.md), art/ (READMEs, mood scripts tokyo_v2, logo README),
assets/ READMEs, design/godot-build-guide.md (incl. App. E), CHANGELOG, AGENTS, /workspace/mockups (tones, tones/work, lane_chain v1-v5, pattern_read,
race_state_study: READMEs + scripts). No docs/ directory exists.
- Touge lamp spacing (48 m, one per side, alternating). B.3 only says "sparse".
- Touge edge-line colour #B8B8B0.
- Touge verge #2E3A33. B.3 says "cold desaturated greens", with no hex.
- Cedar spacing 7 m and height 11 m; guardrail height 1.0 m.
- Touge ridge band colour.
- Street sidewalk width 4.5 m; prop density 6 m.
- Sign text: B.1 says made-up shop names only, but no names exist, so panels stay blank.
- Logo use in game: only art/logo/README.md (menu only, as before).
- Exit/apex call text: replaced by Austin's '<Stance> <phase>' names, which are final, not placeholders.
