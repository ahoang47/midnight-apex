# Sprite-stack touge (look test)

A short night race drawn as sprite stacks. It is a look test for Midnight Apex, not a replacement for the Godot game. Nothing here is imported by the game (`prototypes/sprite-stack-scene/.gdignore`).

The district is a narrow touge: one left sweeper, sodium lamps, cedars, a dim turnout stand, and a finish banner. You drive KITE. DAYBREAK, HATCHET and CHALK run ahead.

## Run

Open `index.html` in a browser. The slice PNGs are also embedded in `sheets_data.js`, so Chrome can read the pixels when the file is opened from disk. Or:

```bash
cd prototypes/sprite-stack-scene
python3 -m http.server 8080
```

Then open `http://localhost:8080/`. The frame is 640×480, nearest-neighbour scaled 2× to 1280×960.

| Key | |
|---|---|
| W A S D or arrows | drive |
| `[` `]` | stack spacing (default 1 screen px). The HUD has no bracket glyphs; the number still updates. |
| `,` `.` | camera squash (default 0.75) |
| R | restart |

`index.html?t=6` draws one frame after 6 seconds of the car driving itself. The headless check uses that.

## Check

```bash
python3 prototypes/sprite-stack-scene/test_stack.py
```

Pillow is required (the same one that built the sheets). The test checks the stacking rules from the primer (hand-pasted slices match, squash, spacing, a 90° turn, the nose follows the heading), the sheet sizes, and that headless Chrome loads the page without an error.

## How the slices were made

`tools/slice_glb.py` reads the game GLBs (node translations applied, glow quads skipped) and stamps every triangle into a 16 px/m voxel grid. A column is filled between shell hits so the stack is solid. A short gap whose floor faces up and whose ceiling faces down is left empty, which keeps the wheel arches open. Slice 0 is the ground and the left tile. The sheet faces +y, and the centre pixel is the vehicle root on the ground.

| On screen | Mesh |
|---|---|
| KITE | `assets/cars/s2000/car_s2000.glb` |
| DAYBREAK | `assets/cars/mx5/car_mx5.glb` |
| HATCHET | `assets/cars/wrx_sti/car_wrx_sti.glb` |
| CHALK | `assets/cars/gr_corolla/car_gr_corolla.glb` |

Lamps, cedars, posts, the stand and the finish posts are procedural stacks in the night palette. They are not slices of the environment GLBs.

Regenerate (from the repo root, with Pillow and NumPy):

```bash
python3 prototypes/sprite-stack-scene/tools/slice_glb.py
```

`slices/preview.png` is the four cars at three headings, squash 0.75.

Draw order and the turn formula live in `tools/stack_math.py` and are repeated in `main.js`. Props that never turn are baked once. Cars are redrawn every frame. Whole stacks sort by the ground point. The finished stack gets one 1 px outline; slices are not outlined. Then the 640×480 buffer is saturation 1.05, RGB555 with the 4×4 Bayer matrix from `shaders/post.gdshader`, then the 2× nearest blit. The HUD is drawn after that, in hard pixels, with a 2 px shadow.

## Art-rule notes

Followed: 640×480, no AA, nearest 2×, RGB555 + ordered Bayer last, HUD after the dither, dry matte road, navy fog `#0B172B` into zenith `#010408`, every lamp the same sodium `#F0C894` with a smooth pool, cool opaque glass, blob shadows, head and tail flares, made-up names, the turnout stand kept dimmer than the cars (its brightest voxel is below every car's).

Compromises, because a stack has no normals at draw time and the camera has to stay high:

- The camera is the primer's high angle (squash 0.75), not the locked chase camera. A stack read from a chase cam falls apart.
- Cel bands, the hard spec and the env-map term are baked from one fixed view (the car shader's key and a camera above and behind). They turn with the car. Moon fill is weaker than the live shader so the bake stays a night scene. The RX-7's painted livery sits in the same yellow family as the MX-5, so the fourth stack is the light GR Corolla mesh under the name CHALK.
- Ink is the silhouette of the finished stack. There is no depth/normal buffer to ink only the near side of a crease. Lane lines, the road and blob shadows are not inked.
- Glass uses the GLB colour, lifted just enough that the greenhouse is visible. It stays dark and blue.
- Fog far is 34 m, plus a screen-space term, so the road still dissolves into the sky inside this short view. The approved touge far distance is 78 m.
