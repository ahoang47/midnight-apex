# Line Lock candidate comparison

Deliverables (all local network-box files; no repository edits/commits/pushes):
- mockup_a_named_lines.png — 1280x960
- mockup_b_tactical_hud.png — 1280x960
- compare_a_vs_b.png — 2580x1010
- raw/mockup_a_named_lines.png and raw/mockup_b_tactical_hud.png — native 640x480

## Shared frame and rendering
Uses the actual build_v5.py asset-import, URBAN road/buildings, tree/barrier/streetlight packs, unlit vertex lighting/fog, sky cards, fake car shine and lamp-sprite culling. Both cars face +Y on the straight before turn-in. White GR Corolla foreground; blue WRX ahead. Identical camera/environment/three-lane markings between candidates; only rival pose/position and HUD/road tells differ. No front headlamp throw. Rear lamps remain lit.

Approved blend50 palette comes directly from tones.py: fog #0B172B, zenith #010408, ambient #5575A0; all lamps #F0C894. Three-step lamp pools; bloom only from glow pass, Gaussian radius 3 at weight .22; no broad bloom. Native EEVEE 640x480, 1 sample, filter size zero. HUD fontmode='1', navy (10,14,36) panels with exact 50/50 PS1 blending and 45-degree cuts, hard slanted stance chips. Final RGB555 + original post_v5 4x4 Bayer matrix, then exact 2x nearest. verification.json proves dimensions, pixel repetition and 32 levels per channel.

Shared road repaint samples unmarked asphalt from URBAN/textures/road4.png, not a generated modern surface. Two crisp lane dividers and perspective-warped OUT / MID / IN asphalt stencils clarify left/outside versus right/inside. One longer lane dash through the rival's decision zone makes B's divider straddle readable. HAIRPIN R badge, U-turn-right icon, 04.8s segmented timer and real warning board ahead establish corner direction.

## A: named racing line / road-first
Rival centered in outside-left lane, with 2.8-degree body-only front dive, rear brake sprites and tiny hard-edged backfire polygon. DEF -> DEF -> ATK is the Aggressive Hairpin sequence in current design/06-pattern-read.md. Eight flat hard-edged chevrons are true camera projections of world-ground polygons, 50/50 blended onto tarmac; green/green/red, no luminous ribbon. Dim dashed red fork and tiny ? provide an alternate early-dive ambiguity. Compact leader tag identifies LATE APEX without obscuring the WRX. Rival hand 3/2/1; player STY locked, STY actively selected, DEF queued. RPS colours/counters follow ATK > STY > DEF > ATK.

## B: road Entry + tactical Apex/Exit (incorporates Austin's update)
Rival root centered on left/mid divider at x=-1.65, yawed 10.9 degrees inward while still travelling the straight approach, with body pitch neutral. No projected road chevrons/backfire. Entry slot is ON ROAD / LANE READ, with a tiny three-lane gauge and blue car straddling the outside/mid line plus a subtle leader; it is NOT a truthful abstract stance chip. Apex is hatched ? / HIDDEN; Exit is red ATK with amber ! and AUDIBLE / FEINT brackets. Solid confirmed vocabulary is shown on the player's locked yellow STY entry, labelled MID / LOCKED. Rival counts 2/2/2, player hand 2/2/1 plus 1 LOCKED. Slot columns are exactly x=226,356,486 for both rows.

Portrait is the actual textured male base from art/characters/base/char_base.blend (bulky .45, Hair_B, hoodie), 72x72 native, front-facing static bust. Retains original painted head/outfit/hair atlas with nearest sampling, fixed navy/warm dashboard fake lighting. Small 1-bit brow/pupil/mouth accents add focus to the rendered generic face; not an invented finished rival character.

## Verification and honest limits
Inspected both full frames, native frames, comparison, individual car crops and enlarged tactical strip. No text overlap/clipped panels observed; player car remains clear of bottom strip. Exact nearest upscale and RGB555 levels verified programmatically. Reopen using fresh _qa names if viewer caches the original filenames.

This is a Blender + PIL design mockup, not native Godot or an implemented gameplay system. The existing environment turns roughly 90 degrees; the actual full 180-degree hairpin is offscreen/represented by signage, as permitted in the brief. A's projected late-apex/exit path and fork compress into the distance, so the callout carries the exact sequence; the tiny fork is intentionally subtle. Rival body dive versus flat suspension is subtle in a single 640x480 still; animation would be the proper test. The portrait is a generic base with focused paint accents, not final character art. No claim that a static frame proves a temporal bluff/weave or dynamic suspension behavior. Scene contains ~64k triangles inherited from the asset-pack mockup, not an optimized in-game scene.

## Rebuild (all output inside this directory)
TONE=blend50 /workspace/tools/blender-4.2.3-linux-x64/blender -b -t 6 -P build_battle.py -- entry
/workspace/tools/blender-4.2.3-linux-x64/blender -b battle_base.blend -t 6 -P refine_lanes.py
# render_portrait.py rebuilds the raw base bust; portrait_focused.png contains documented 1-bit mood accents.
python3 compose_mockups.py
