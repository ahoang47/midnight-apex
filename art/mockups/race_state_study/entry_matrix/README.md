# Truthful rival Entry matrix + proposed PLAYER Line Lock UI

## Deliverables
12 gameplay PNGs (1280x960), native 640x480 copies in raw/, four 3-column comparison sheets (3920x1290), and an optional native-panel overview (1960x2300). manifest.json lists exact file:// links for all individual frames and sheets.

State filename prefixes:
- 01_ahead_pressure: S2000 ahead / 6 m along-road centre gap.
- 02_ahead_room: S2000 ahead / 18 m along-road centre gap.
- 03_close_behind: S2000 behind / 6 m along-road centre gap.
- 04_far_behind: S2000 behind / 18 m along-road centre gap.

Suffixes: _outside.png, _center.png, _inside.png. Comparison sheets: <state>_entry_comparison.png. Optional overview: entry_matrix_overview.png.

All race-state names are FROM RIVAL S2000'S PERSPECTIVE. Yellow Miata ND always PLAYER; red S2000 always RIVAL. The three column headings are external ground truth, not an in-game reveal of the rival's stance.

## Controlled staging / exact cameras
Reuses fixed_chase's player, camera, authored right hairpin, road markings, environment, car appearances and actual top-centre mirror without per-case adaptation.
- Player world root always (0,-28,.16), Center lane, +Y heading.
- Main camera always (1.4,-35.6,3.1), target (3.6,-6,-.9); 25 mm / 36 mm horizontal fit, H FOV 71.507775 deg, V FOV 56.738093 deg. Offset from player root in world/travel-aligned axes (1.4,-7.6,2.94).
- Mirror camera always (0,-28,1.60), target (0,-60,-2.2), 14 mm / 36 mm horizontal fit, H FOV 104.250033 deg; actual 192x64 render, one horizontal flip, one-to-one at native screen x224..415 / y16..79.
- Rival Y = -22 / -10 / -34 / -46 for the four states. Rival X = -3.3 / 0 / +3.3 for Outside / Center / Inside. Both car roots remain XYZ (0,0,pi), heading +Y. No body pitch, turn-in, braking cue, weaving or bluff variant.
- Truthful Entry ONLY: Outside=ATK; Center=STY (Steady); Inside=DEF, all relative to the same RIGHT HAIRPIN.
- 6/18 m are along-road longitudinal centre gaps, not Euclidean distance across lanes, gameplay thresholds or tuned values. No gap adjustment was necessary.

Camera matrices are compared numerically with fixed_chase metadata, not merely checked by eye. Only the rival's requested longitudinal/lateral position changes between conditions. No player geometry is hidden, no mirror FOV is adapted, no car/lamp is enlarged or relocated inside the mirror.

## Proposed player UI
All frames include the SAME native, late-90s angular navy/amber PLAYER LINE LOCK selector:
- Active ENTRY: amber cursor and `< MID / STY >`, CONFIRM prompt, D-PAD LANE and circle SET affordance. It is NOT locked.
- APEX and EXIT: SET / NOT SET. No rival '?', hidden/feint badge, future card or implied lane controls on these phases.
- L1/R1 PHASE navigation and 0 LOCKED.
- Full sample HAND (6): ATK x2 / DEF x2 / STY x2. No card is subtracted before any lock.
- Sample 04.8s countdown and segmented bar at top-left, HAIRPIN R at top-right, genuine mirror top-centre.
Selector is placed upper-right (x414..628,y107..315), not over the foreground Miata or bottom-edge trailing-rival fragments. Geometric rival footprint/selector overlap is checked. The mirror can genuinely show the Miata's own roof/rear silhouette; this is kept, not erased.

Every comparison sheet explicitly labels PROPOSED UI + MIRROR, NOT IMPLEMENTED, with sample hand/timer values. This is a static visual proposal, not working in-engine controls or a balance specification. No player stats, Apex/Exit variants, opponent intent strip, projected true line or specialization habits are introduced.

## Art / pipeline
Same PSX asset-pack environment and car meshes as fixed_chase. Half-teal palette and pale sodium street lamps are unchanged. Native EEVEE 640x480, one sample, filter zero; 1-bit HUD text/polygons; exact 50/50 navy panels; original RGB555 + 4x4 Bayer; exact 2x nearest. No CRT pass. Rear view uses actual geometry/depth, original painted headlamp regions made emissive on the mesh, low headlight sprites and no added mirror bloom. Neither lamp spacing nor vehicle geometry is faked.

## Readability findings / limitations
Specific per-case observations are in visibility_notes.json, repeated under each sheet column, and included in verification.json. Projected bounding boxes do NOT prove unoccluded visibility, so findings are based on inspecting the actual frames and enlarged native mirror inserts too.

Forward ahead cases can show all three truthful lanes; the close Center case remains genuine alignment/overlap, not an artificially offset rival. Trailing cases must not be inferred from offscreen tags: Outside can be wholly outside the main view; Center/Inside may show only clipped lower-edge body fragments close behind. Far trailing rivals are behind the forward camera. The mirror is the actual additional view, not a ghost.

Near mirror views provide more lateral context; far rivals have only about a 9x6-pixel mesh footprint at native mirror resolution. Headlamp pair/tyre position and exact lane placement at distance are consequently limited. Own-car occlusion and the mirror's limited road context remain real limitations. No claim of guaranteed Entry readability, calibrated distance, dynamic reliability, future stance prediction or a settled specialization table follows from these stills. Use reflected lane markings and corner context, not a fixed screen-left/right=stance rule.

## Rebuild / verification
TONE=blend50 /workspace/tools/blender-4.2.3-linux-x64/blender -b -t 6 -P build_entry_matrix.py -- entry
python3 compose_entry_matrix.py
python3 verify_entry_matrix.py

All generated files stay under this entry_matrix directory on the network box. Repo docs/assets were read only; no repository modifications, commits, pushes or personal-computer access.
