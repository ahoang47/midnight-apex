# Line select camera: Entry / Apex / Exit (UNAPPROVED PROPOSAL)

Proposal only. Austin has not approved this, so nothing here is final UI, camera spec or mechanics.

## Flow (Austin's idea)
1. **Entry pick.** The existing selector on the fixed chase camera. The rival can be seen in its Entry lane, which is the only tell.
2. **Apex pick.** Once Entry is set, the camera moves to the apex: a raised view from the outside of the corner, so you can see the apex and the inside, center and outside lanes there. No rival is shown, because Apex has no tell.
3. **Exit pick.** The camera moves to the exit and looks down the exit lanes. Again, no rival is shown.
4. **Line locked.** The camera goes back to Entry with all 3 slots filled and a LINE LOCKED banner. Playback starts from here.

## Frames (1280x960 = 640x480 native, 2x nearest)
- `1_entry_pick.png`: Chase camera. The rival S2000 is in the OUTSIDE lane (an ATK tell on a right hairpin). The Entry slot is active.
- `2_apex_pick.png`: Apex camera. Entry is filled and Apex is active. Lane marks show OUT, MID and IN at the apex.
- `3_exit_pick.png`: Exit camera. Entry and Apex are filled and Exit is active.
- `4_line_locked.png`: Back on the chase camera with the banner and all 3 slots set. The rival is back in its Entry lane.
- `line_select_cam_contact_sheet.png`: All 4 frames in order, labelled 1 to 4.

The corner plate in the top right shows the hairpin and the three camera stops (E, A and X), with the current stop in amber.

## Sample values, not specs
- The picks (MID/NEU, IN/DEF, OUT/ATK), the timer, the hand of 6 and its counts going down are all illustrative.
- Showing Apex and Exit picks as `lane / stance` borrows the Entry rule (outside = ATK, center = NEU, inside = DEF). No Apex or Exit lane mapping has been approved, so that part is open.
- The player car is the yellow MX5 and the rival is the red S2000, the same as race_state_study/entry_matrix.

## Art and pipeline
- **Scene.** A cheap Touge right hairpin built in Blender: a 3-lane road strip, W-beam guardrail with posts, chevron boards, a cut bank on the inside, a drop-off on the outside, cedar cards, and ridge cards in the distance.
- **Lighting and tone.** Same unlit vertex-light, fog and emission method as lane_chain/v5 and entry_matrix. Uses the approved `blend50` tone: fog #0B172B, ambient #5575A0, pale sodium #F0C894 lamps with hard 3-step pools, and bloom (.22, 0). The fog is closer than in the city scenes.
- **Cars.** Game .glb models with the A.4 faked shine.
- **Render.** EEVEE at 640x480, 1 sample, filter 0. The HUD is drawn at native size with 1-bit text and PS1 50/50 panels, then RGB555 + 4x4 Bayer, then 2x nearest.

Rebuild: `./run.sh` (see the script for its dependencies). The .blend file and raw passes are kept on the box only.
