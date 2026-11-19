# Mountain districts, pass 5: every road 7.5 m (approved mockup)

Arthur (Art Director). Austin approved the 7.5 m frames on 2026-11-19. Earlier passes (v1–v4) stay in `unapproved/arthur/mockups/mountain_districts/`.

Same pipeline and look as the earlier mountain passes: Cel A soft, Godot 4.6.3 GL Compatibility, 3D at 640x480 with RGB555 + Bayer last, HUD at 1280x960 unshaded and uninked, one #F0C894 sodium, navy #0B172B fog, no LIMP tag.

Every frame uses the same CAT chasing setup: the rival is 11 m ahead in the player's line with its taillights in the chevrons and the red tail wash. The CAT CHASING tie-gap box is on. Player and chevrons sit on that lane, and the plan box has that stance selected (OUT = A / POW, MID = S / HAN, IN = D / EN). No floating OUT / MID / IN markers. The v3 chase camera (half-pitch) and HUD are unchanged.

## Pass 5 (v5): every road 7.5 m

Austin, 2026-11-18: *"Actually. Just make all 7.5meters."* / *"7.5 meter roads."*

- **Width:** every road is now 7.5 m kerb to kerb. The touge was 6.0 m, the main street 5.8 m and the canyon street 4.8 m; Wangan was already 7.5 m. All use the Wangan lane offsets (1.75 m) and chevron width, so OUT / MID / IN sit 1.75 m apart and the rival sits in the player's lane in every frame.
- **What follows the width:** all dressing hangs off the road edge, so the guardrails, walls, facades and poles move out with it. The canyon blocks stay tight to a 0.35 m kerb strip, and the walkway is stretched facade to facade.
- **Unchanged:** grades, the v3 camera and the HUD.
- **Files:** all 15 frames are `*_v5.png`, and `mountain_districts_sheet_v5.png` has the same 5 rows as v4 with width labels (touge, Wangan skyline, Wangan sea bridge, street main, street canyon). The six Wangan v5 frames are byte-identical to their v4 frames.
- **Rebuilding:** `./run.sh` builds v5, and `python3 make_sheet.py v5` rebuilds the sheet. `MTN_V=1-4` still exist in the script, but those earlier frames live in the unapproved folder.

## Weak spots

- At 7.5 m the canyon street reads as a narrow city street, not an alley. It is more open overhead and the near facades are less dominant.
- The touge's hairpin now feels wider and less tight.
- The road textures for touge and street are stretched to the new width, so their painted edge lines are a little wider.

## Rebuild

```
./run.sh                 # textures + Blender props + import + 15 v5 frames + sheet_v5
SKIP_ASSETS=1 ./run.sh   # renders + sheet only
ONLY="wangan:bridge" ./run.sh   # one section
python3 make_sheet.py v5
```

`godot/` is self-contained. Blender helpers that used to be loaded from the deleted `wangan_two_corner` experiment are vendored as `blender/build_wangan.py`.
