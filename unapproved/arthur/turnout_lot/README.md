# Touge turnout parking-lot kit (Arthur, unapproved)

Cel A soft, LotArt frame, not committed. The lot sits on the **inside of the bend** (cut / lattice side). Pocket 62 m × 11 m deep, 14 m tapers, 30 m approach, 110 m total; stalls 2.5 × 5.0 m at 70°; curb 0.15 m; 2 sodium lamps.

## Layout

- **11 m (slot default):** one angled stall row along the back + a through-aisle. Two rows do not fit.
- **16 m (comparison only):** two angled rows.
- Road paint (chevrons, yellow centre line) is authored in LotArt with x < 0 (into the 7.5 m road).
- White drop-side rail stays on Gordon's far side of the road; this kit does not add one.

## Paths

- Scratch build: `/workspace/turnout_build/`
- Checkout (untracked): `/workspace/arthur-turnout/unapproved/arthur/turnout_lot/`
- Comparison sheet: `renders/turnout_11_vs_16.png`
- Mapping for Gordon: `MAPPING.md`
- Packed scenes: `scenes/turnout_lot_w11.tscn`, `scenes/turnout_lot_w16.tscn`

## Rebuild

```
./run.sh                  # textures + 11 m + 16 m + Cel A-soft stand-in renders + sheet
SKIP_TEX=1 ONLY=w11 ./run.sh
POCKET_M=80 TAPER_M=16 POCKET_W=11 ROWS=1 N_LAMPS=2 ./run.sh
```

Glbs are exported Godot Y-up, +Z travel (`export_yup=True`, Blender stores (x, −z, y) for LotArt (x, y, z)).

## Shaders when instancing in the root project

- Floor / verge / cut / cedars: `scroll.gdshader` with `soft_surface=1`
- Stall lines, arrows, edge line, chevrons, centre line: `chevron.gdshader` (never inked)
- `Emit_*` (lamp head, vending face): `cel_k=0`
- Curbs, wheel stops, lattice, poles, sign, vending body: default prop toon + ink

## Weak spots

- Lattice modules along the mid wall are axis-aligned; taper flanks use a cheaper cut-slope panel instead of yawed modules (yawed copies presented a giant face to the road).
- Lamp pools are soft 6 m ovals under the heads (no overlap). They wash a fair width of the 11 m lot.
- The P sign is a painted plate; readable square-on, smaller at race-cam distance.
- Blender stand-in renders use the Cel A-soft post (fog, 1 px prop ink, bloom, RGB555+Bayer).
- Godot Cel A (scratch copy of Gordon's project, never his worktree): `renders/godot_cel_race_cam_640.png` and `renders/godot_cel_lot_overview_640.png`. The live HUD is in the frame because these are the game viewport; the 3D is the real Cel A stack (`CEL ON SOFT ON`). Scratch project: `/workspace/turnout_godot_scratch`.
