# Playtest-to-Troubleshooting Spec

> **UNAPPROVED.** Moved out of `design/godot-build-guide.md` on 2026-11-11 per Austin's directive: anything other bots need to reference goes in the repo, and work he has not approved goes in `unapproved/<owner>/`. The section below is verbatim.

## 0. Playtest-to-Troubleshooting Spec (PROPOSED)

> **Status: PROPOSED, spec only, uncommitted.** Drafted by Gordon (Godot) on 2026-11-06 at Austin's go-ahead, routed through Barry. Nothing in `project.godot`, `scenes/` or `scripts/` has been created or changed for it yet. Implementation starts after Austin locks §0.4.
> **Goal:** one keypress in a playtest gives any Midnight Apex bot (Gordon, Barry, Arthur, Nathaniel) an exact, copy-pasteable picture of *where* the game was (scene, coordinates, camera) and *what state* it was in (progression, economy, build, mid-race combat). With that, a bot can decode the moment, reproduce it in Godot, and debug it without guessing from a screenshot.
> **Number rule (`AGENTS.md`):** this section contains no balance values. Gameplay quantities are referenced by constant name and file (`KAPPA_BY_LENGTH` and `KNOT_WINDOW_105` in `sim/velocity_shift/equations.py` / `scripts/globals.gd`, `HAND_SIZE` and `DECK_ALPHA` in `sim/velocity_shift/equations.py`, `DEBT_SHARE` and `TIER_STAT_BUDGET` in `design/07-economy-and-mods.md`). The only literal numbers here are encoding sizes, pixel/viewport geometry and hotkeys.
> **Vocabulary:** follows the locked block in `design/01-system-overview.md`. The state token has **no reputation field** (reputation is lore only). Sabine's debt is her personal repair tab (`sabine_repair_debt`). The third stance is `Stance.NEUTRAL` in code, and debug output prints the code name `NEU`. The player-facing name is **Neutral** (resolved: approved 2026-11-11, art Q6 at 55b9063, design/01 canon block Stats line; `02` decision sheet item 5 closed). "Steady" is dropped.

### 0.1 Coordinate & Camera Reference System

**Axes and viewport**
- World axes follow Godot 4: right-handed and Y-up. `+X` is right, `+Y` is up and `-Z` is forward (the direction a `Camera3D` looks at zero rotation). Units are metres.
- Angles are in degrees and use Godot's `rotation_degrees` (Euler order YXZ): `pitch = x`, `yaw = y`, `roll = z`. `yaw = 0` faces `-Z`, positive yaw turns left (counter-clockwise seen from above), and the value is wrapped to `[-180, 180)`. `heading_deg` on cars and the player uses the same convention, wrapped to `[0, 360)`. On overworld maps, `-Z` is "north".
- The viewport is `640×480` with stretch mode `viewport` and aspect `keep` (§1.1; `project.godot` sets width, height and `stretch/mode`, and `keep` is Godot's default aspect). The 640×480 vs 640×448 question is still open as Arthur's Q3 in `design/art/art_direction.md`. Screen-space callouts use `(u, v)` in pixels: origin at top-left, `u ∈ [0, 640)`, `v ∈ [0, 480)`, always in the 640×480 base resolution before any upscale.

**3D Battle: two frames**
- *Track-relative (Frenet) frame `(seg, s, d, h, yaw_slip)`*, used in every bug report about car placement:
  - `seg` is the active segment: `STRAIGHT`, `ENTRY`, `APEX` or `EXIT`. It is derived from `TurnManager.State` (`STRAIGHT` → `STRAIGHT`; `CORNER_PLAYBACK` / `PROGRESS_BATCH` → the clash index 0/1/2 → `ENTRY`/`APEX`/`EXIT`).
  - `s ∈ [0.000, 1.000]` is normalized progress along that segment. On `StraightRoad` it is distance along `-Z` divided by the mesh length. On a corner it is `curve.get_closest_offset(local_pos) / curve.get_baked_length()` on the segment's `Curve3D` (§13.1 `Path3D`).
  - `d` is the signed lateral offset in metres from the road centreline (`-` left, `+` right). Here `right = tangent.cross(Vector3.UP)` at the closest baked point, so on today's straight (centreline at `x = 0` along `-Z`) `d == x`.
  - `h` is the height in metres above the road surface.
  - `yaw_slip` is the car's heading minus the road tangent's heading in degrees (drift angle, `+` = nose left).
- *Visual lead/trail from progress.* Car `s`/Z placement is purely a visualization of the progress gap (Appendix H). It must use the exact expressions in `TurnManager._determine_winner()`, so the picture can never disagree with the result:
  - `pos_p = player_cum_progress / (player_cum_progress + opponent_cum_progress)` and `pos_o = 1 - pos_p`, both `0.5` while the total is 0. These are the same shares as `MatchResult.player_position` / `opponent_position` in `sim/velocity_shift/match.py`.
  - `lead = pos_p - pos_o` (`PositionTracker.get_lead()`, §10.1). Equal totals are a tie (`lead = 0`), with no opponent tiebreaker. `CarAnimator.snap_to_gap(gap, max_gap)` stays the single place that maps the lead to Z offset. The HUD prints `lead` signed to 3 decimals.
- *World frame `(x, y, z)`* is `Node3D.global_position` inside `Battle/World3D` (a `SubViewport` in `scenes/Battle.tscn`). `World3D` holds world-origin children, so local `position` equals `global_position` today, but the token always stores `global_position`.
- *Named rig modes on top of today's camera.* `scripts/BattleCamera.gd` currently tweens `position` between `_default_pos`, `_default_pos + _corner_offset_left` and `_default_pos + _corner_offset_right`, plus a short `swing_overtake()` nudge. Each of those becomes a `CamRigMode` value (below), and the camera sets `rig_mode` when a transition starts, so a dump taken mid-tween still names its target mode. `CarAnimator.gd` exposes `get_frenet() -> Dictionary` for its car. Current gaps found while grounding this spec (not fixed, spec only): `BattleCamera.gd` is not attached to `World3D/Camera3D` in `Battle.tscn` (the camera sits at a hard transform that matches `_default_pos`), and `PlayerCarAnimator`/`OpponentCarAnimator` are children of a plain `Node` (`World3D/CarAnimators`), so their `get_parent().position` tweens don't reach the cubes. Nothing calls `snap_to_gap` or `transition_to_corner` yet.

**Isometric Overworld and hub coordinates**
- `SceneId` enum (`u8`, **append-only**; never renumber within a schema version):

| Value | `SceneId` | Place (locked vocabulary) |
|---|---|---|
| 0 | `UNKNOWN` | Boot, menus, anything not yet mapped (`MENU`/`RESULTS` may be appended) |
| 1 | `GARAGE` | Sabine's garage: Jesse's tuning bay and Reiko's parts counter |
| 2 | `SPEAKEASY` | The barkeep's bar |
| 3 | `WIND_TUNNEL` | The speakeasy's hidden wind tunnel (aero tuning) |
| 4 | `WANGAN_PA` | The promoter's subsea Wangan parking-area home base (betting races) |
| 5 | `OW_TOUGE` | Touge district overworld |
| 6 | `OW_WANGAN` | Wangan district overworld |
| 7 | `OW_STREET` | Street district overworld |
| 8 | `BATTLE` | `scenes/Battle.tscn` (any race tier) |

- The player position is ground-plane world `(x, y, z)` plus `heading_deg`, plus a **1 m integer grid cell** `(gx, gz) = (floor(x), floor(z))`. Austin or Arthur can then call out a prop, car placement or collision snag as "`OW_TOUGE` cell (112, -48)", in screenshots and in chat.

**Standardized camera rig state** (one struct, used by the HUD, the token and restore)
- `rig_mode: CamRigMode` takes one of `BATTLE_CHASE` (`_default_pos`, `STRAIGHT`), `BATTLE_CORNER_L`, `BATTLE_CORNER_R`, `BATTLE_OVERTAKE` (during `swing_overtake()`), `HUB_FIXED` (authored hub cameras), `OVERWORLD_ISO` (semi-isometric follow, `design/art/art_direction.md` B.4) or `DEBUG_FREE` (fly cam; sets the `DEBUG_FREE_CAM` token flag). The list is append-only.
- `pos (x, y, z)` is `Camera3D.global_position`, and `rot_deg (pitch, yaw, roll)` is `global_rotation_degrees`.
- `projection` records `fov_deg` for `PROJECTION_PERSPECTIVE` or `ortho_size` (`Camera3D.size`) for `PROJECTION_ORTHOGONAL`. A one-bit flag says which, so either answer to Arthur's Q8 (long lens vs true ortho) fits without a schema change.
- `look_target (x, y, z)` is the point passed to `look_at()`, or `pos + 10 × forward` when none was set.

**Toggleable one-line debug HUD (`F3`)**
- `scripts/DebugOverlay.gd` is an autoload that adds a `CanvasLayer` at `layer = 128`, above every game layer. A single `Label` with a monospace pixel font sits on a translucent black backing. Every `Control` in it uses `mouse_filter = MOUSE_FILTER_IGNORE`, so it never eats clicks meant for `CanvasLayer/TopBar` or the card hand.
- `F3` (`debug_hud_toggle`) switches it off ↔ 1 line. `Shift+F3` (`debug_hud_expand`) adds a second line. It is anchored top-left at `(u, v) = (2, 2)`. Each line is ≤ 80 characters, so it fits 640 px at an 8 px glyph width. It refreshes at most 10×/s. Because `TopBar` is currently unanchored at `(0, 0)`, a `HUD_ANCHOR` debug const (top-left / bottom-left) in `DebugOverlay.gd` lets Austin move it off the bar if it hides something.
- Example **Battle** frame (line 1, then `Shift+F3` line 2):

```
f5b9114* BATTLE T07 CRN APEX Hairpin | BCL (-3.0,5.5,9.0) y-15 p-20 f55
P s.62 d-0.8 | O s.58 d+0.9 | lead+.016 | LT | rng 9F3A21C4 | NEU NEU ATK
```

- Example **Overworld / hub** frame:

```
f5b9114 OW_TOUGE c(112,-48) h270 | ISO (120.0,18.0,-36.0) y45 p-35 o24.0
R1 lad T:MAT W:KID S:--- | ramp 2/1/0 | unl R3.M.S.W.-.- | debt>0 | sh00 lv03
```

- Field key: `f5b9114` is the short git SHA, with `*` meaning a dirty working tree. Then come scene, turn, `TurnManager.State` (`STA`/`STR`/`CRN`/`PRG`/`END`/`FIN`), `seg` and corner type (`TrackData.TURN_TYPES` name). The camera block is rig-mode code (`BCH`/`BCL`/`BCR`/`BOV`/`HUB`/`ISO`/`DBG`), `(x,y,z)`, yaw, pitch, and `f`=FOV or `o`=ortho size. Next are the cars' `(s, d)`, `lead`, the tier code (`WD`/`BT`/`LT`/`BS`/`MY`), the low 32 bits of the RNG seed in hex, and the shown face sequence. Hub line 2 shows act, the per-district ladder, the wild ramp, unlock initials (race-3 win, Mods, Substories, Wholesale, Aero, Betting) and debt open/closed, with no amount on the HUD. The active shell/livery IDs end the line.

### 0.2 Compact State Token ("Mini Save File" — `MX1`)

**Envelope and integrity**
- Format: `MX1:<git7>:<base64url_payload>:<crc16_hex4>`. It is one ASCII line using only `[A-Za-z0-9_:-]`, with no spaces, `=`, `+`, `/`, `*` or backticks. It survives chat, Slack and Markdown, and a double-click selects it whole on most clients.
  - `MX1` is the envelope + schema version. A breaking layout change bumps it to `MX2`, and decoders reject versions they don't know, loudly.
  - `git7` is the 7-character short SHA of the running build (§0.4 `.build_sha`).
  - `payload` is `StreamPeerBuffer` bytes (`big_endian = false`, so little-endian) → Base64URL without `=` padding. In Godot that is `Marshalls.raw_to_base64()`, then `+`→`-`, `/`→`_` and strip `=`. Python decodes it with `base64.urlsafe_b64decode` after re-padding.
  - Compression: if the raw payload exceeds 192 bytes, the encoder tries `PackedByteArray.compress(FileAccess.COMPRESSION_DEFLATE)` and keeps the result only if it is smaller. In that case it sets `COMPRESSED` and prefixes a `u16` uncompressed length (Godot's `decompress()` needs it). Godot's DEFLATE mode emits a zlib stream, which Python reads with `zlib.decompress`.
  - `crc16_hex4` is CRC-16/CCITT-FALSE (poly `0x1021`, init `0xFFFF`, no reflection, xorout `0`; check value `"123456789"` → `29B1`), uppercase hex. It covers the ASCII bytes `MX1` + `git7` followed by the wire payload bytes (after any compression). Python: `binascii.crc_hqx(data, 0xFFFF)`.
- Byte budget (estimated from the schema below with a throwaway packer, not repo code):

| Capture | Raw payload | Token length |
|---|---|---|
| Hub / overworld (Blocks A+B) | ~140–150 B | ~200–215 chars |
| Battle, turn 1 (A+B+C, history mode) | ~250–260 B | ~350–365 chars |
| Battle, late race (pick/QTE history grows 1 B + 2 B per completed turn) | ~300–330 B | ~420–450 chars |

All of these are still one line. Packed binary compresses poorly, so DEFLATE is a safety valve for future growth, not the main lever.

**Single-keypress capture (`F9`, `debug_dump_state`)**
1. `PlaytestState.capture()` gathers Blocks A/B(/C) from the live scene and builds the token. `DisplayServer.clipboard_set(token)`.
2. A non-intrusive toast appears for 1.5 s in the HUD layer, `MX1 copied · dump saved (412 ch)`, even when the HUD is off.
3. It writes `user://playtest_dumps/<local_ISO>_<git7>.json` with `:` replaced by `-` for Windows paths, e.g. `2026-11-06T10-42-07_f5b9114.json`, adding `_2`, `_3`, … on collision. The file is a human-readable mirror of exactly the same decoded fields, plus `token`, `lints` (§0.3), `godot_version` (`Engine.get_version_info()`), `os` (`OS.get_name()`) and `renderer`. On Austin's Windows machine `user://` resolves to `%APPDATA%\Godot\app_userdata\Midnight Apex\`.
4. It writes a `.png` with the same stem via `get_viewport().get_texture().get_image().save_png(...)`, which is the root viewport, i.e. what Austin saw. Note: `World3D` is a bare `SubViewport` in `Battle.tscn`. It only appears in the root capture if it is displayed through a `SubViewportContainer`/`TextureRect`, so the dump also saves `World3D`'s own texture as `<stem>_3d.png` when the scene is `BATTLE`.
- Capture never pauses the game and never consumes RNG.

**Wire / logical schema (3 blocks, fixed order, little-endian)**

Types: `u8/u16/u32/u64`, `i8/i16/i32`, `f32/f64`. `q16(x, k)` is `i16(round(x × k))`. `bits[n]` is `u8 n_bits` followed by `ceil(n/8)` bytes, LSB-first. `list<u16>` is `u8 count` followed by that many `u16`. Every enum is append-only within `MX1`.

*Block A — Header & Spatial (always present)*

| Field | Type | Notes |
|---|---|---|
| `schema_version` | `u8` | `1` (redundant with the envelope; guards against hand-spliced tokens) |
| `flags` | `u8` | bit0 `HAS_BATTLE_BLOCK`, bit1 `COMPRESSED`, bit2 `DIRTY_BUILD`, bit3 `DEBUG_FREE_CAM`, bit4 reserved, bit5 `PROJ_ORTHO`, bits6–7 reserved |
| `git_sha7` | envelope | Not repeated in the payload; covered by the CRC |
| `scene_id` | `u8` | `SceneId` |
| player `pos (x, y, z)` | `f32×3` | World frame (in `BATTLE`: the player car) |
| player `heading_deg` | `q16(…,10)` | 0.1° steps |
| player `(s, d)` | `u16` (s×65535) + `q16(d,100)` | Battle: Frenet. Hubs/overworld: `s = 0`, `d = 0`; `(gx, gz)` is derived from `x, z`, not stored |
| `rig_mode` | `u8` | `CamRigMode` |
| cam `pos (x, y, z)` | `f32×3` | |
| cam `rot_deg (pitch, yaw, roll)` | `q16(…,10)×3` | |
| `fov_or_ortho` | `u16` (×100) | `fov_deg` or `ortho_size` per `PROJ_ORTHO` |
| cam `look_target (x, y, z)` | `f32×3` | |

*Block B — Progression, Unlocks, Economy & Build (always present)*

| Field | Type | Notes |
|---|---|---|
| `act` | `u8` | `PROLOGUE, ROUND_1, ROUND_2, ROUND_3, FINALE` |
| `prologue_races_done` | `u8` | 0–3 scripted races completed (races 1–3 are scripted) |
| `unlock_bits` | `u8` | bit0 `race_3_won` (canon 19 gate), bit1 `mods_unlocked` (set by race-3 win), bit2 `substories_open` (race-3 win), bit3 `wholesale_unlocked` (end of Round 1), bit4 `aero_unlocked` (early Round 2: set when the first Round 2 crew's boss falls, whichever crew that is, per `DEBT_CLEAR_AFTER` in `sim/velocity_shift/equations.py`; `sabine_repair_debt` hits 0 at the same point), bit5 `betting_unlocked` (end of Round 2, `BETTING_UNLOCK_AFTER`). The derived flags are stored explicitly on purpose so the decoder can flag contradictions (§0.3 lints) |
| `ladder[3]` | `u8×3` | Per district `TOUGE, WANGAN, STREET` in the current round: `NONE, KIDS_CLEARED, MATURE_CLEARED, OLD_HEADS_CLEARED, BOSS_CLEARED` |
| `crew_order[3][3]` | `u8×9` | **Free crew order.** For each round R1–R3, the district the PC picked in play positions 1–3 (`TOUGE, WANGAN, STREET, NONE` = not picked yet). Each round must be a permutation of `DISTRICTS`, and the PC is locked into a crew until its boss falls. Difficulty steps and unlock points are keyed by play position, not district (`OPTION_A_ROUND_STEP` goes to the first crew played in R2/R3; `DEBT_CLEAR_AFTER` / `BETTING_UNLOCK_AFTER` / `FINALE_UNLOCK_AFTER` are `(round, crews beaten in that round)`), so a repro needs this field. There is no fixed district order (`DEFAULT_CREW_ORDER` is a sim example only) |
| `beat_pc_bits` | `bits[n]` | **Loss persistence (canon 27).** Indexed by `RivalId`; a set bit means "this lieutenant/crew boss has beaten the PC and remembers it". Only lieutenant (kids, mature members, old heads) and crew-boss `RivalId`s may ever be set. Wild races and Myth Driver races have no loss persistence, so they have no bits or always-zero bits. Race 3's win gate lives in `unlock_bits`, not here |
| `wild_ramp[3]` | `u8×3` | Per district: number of that district's lieutenants cleared that drives the Wild ramp (`02` decision sheet item 9 / item 11 row; proposed, not locked) |
| `defeated_bits` | `bits[n]` | Same `RivalId` index: lieutenants and crew bosses the PC has beaten. Reiko's horizontal shop stock is derived from it (canon 28) |
| `shop_tier_bits` | `u8` | Rare tier-jump gates opened by crew-boss wins (canon 28; tiers per `TIER_UNLOCK` in `design/07-economy-and-mods.md` §6.4) |
| `wallet` | `i32` | Currency units (name TBD in 07) |
| `sabine_repair_debt` | `i32` | Remaining personal repair tab; `DEBT_SHARE` of winnings goes here while > 0 (07 §7) |
| `car_level` | `u16` | |
| `archetype_id` | `u8` | `Aggressive, Defensive, Precise, Balanced, Adaptive` (order of `sim/velocity_shift/cars.py`) |
| `pow_pts, en_pts, han_pts` | `u16×3` | Allocated skill points (POW / EN / HAN) |
| `unspent_pts` | `u16` | |
| `loadout_mod_ids` | `list<u16>` | Index 0 is the fixed car-specific slot (Notes.md; Jesse's DAQ candidate), then the regular slots. IDs index the future part catalog (07 §9.1 `sim/config/parts.json`); `0xFFFF` = empty slot |
| `stash_mod_ids` | `list<u16>` | Garage stash: owned shop parts plus substory skewed-sidegrade rewards (≤ `TIER_STAT_BUDGET`, never aero) |
| `aero (pow, en, han)` | `u8×3` | Wind-tunnel free-point split of the equipped aero part (`AERO_FREE_POINTS[tier]`, 07 §6.3). Must be all-zero while `aero_unlocked = 0` |
| `active_shell_id` | `u8` | 0 = starter shell |
| `unlocked_shells_bits` | `bits[n]` | Starter, standout-substory oddball shells (`SUBSTORY_SHELL_COUNT` TBD), and crew-boss signature shells won only in crew boss betting races at `WANGAN_PA` (canon 26, 28) |
| `active_livery_id` | `u8` | `0xFF` = none. Liveries are per-shell UV bakes (`art_direction.md` A.3) |
| `unlocked_liveries_bits` | `bits[n]` | A livery bit set while its shell bit is clear is a **breadcrumb** livery; the decoder prints it as such |
| `completed_substories_bits` | `bits[n]` | (canon 28) |
| `ext` | `u8 count` + TLV (`u8 tag, u8 len, bytes`) | Forward-compatible tail for fields that lock later without a schema bump: skill-tree node picks once the tree layout locks (05/08), flat-vs-scaled mod hooks (07 Q6), respec counters (07 Q18). Unknown tags are skipped and listed by the decoder |

There is no reputation field (reputation is lore only), and Sabine's debt is only ever her personal repair tab (`sabine_repair_debt`).

*Block C — Mid-Battle Snapshot (present iff `HAS_BATTLE_BLOCK`)*

| Field | Type | Notes |
|---|---|---|
| `encounter_tier` | `u8` | `WILD, BETTING, LIEUTENANT, BOSS, MYTH_DRIVER`, i.e. code strings `wild`, `betting`, `lieutenant`, `boss`, `myth_driver`. `globals.gd` `EncounterType` only has `WILD, LIEUTENANT, BOSS` today and `MatchConfig.encounter_type` is a `String`; `PlaytestState.gd` maps both and does not change `globals.gd` |
| `district_id` | `u8` | `TOUGE, WANGAN, STREET, NONE` (Finale / scripted) |
| `opponent_id` | `u16` | `RivalId`; `0xFFFF` = ad-hoc opponent, followed by `u8 len + UTF-8 name` (`CombatantStats.name`) |
| opponent `archetype_id` | `u8` | Same enum as Block B |
| `rival_personality` | `u8` | Index into the `PersonalityData.get_personality()` names (`MatchConfig.rival_personality`) |
| opponent `level` | `u16` | |
| opponent `loadout_mod_ids` | `list<u16>` | |
| `player_eff_stats`, `opponent_eff_stats` | `f32×3` each | The `CombatantStats` pow/en/han actually fed to `MatchConfig`. This makes a battle restorable before the build → stats pipeline exists and lets the decoder diff "build says X, match got Y" |
| `circuit_id` | `u8` | Index into `TrackData._CIRCUITS` keys (`default, highway, technical`); `TurnManager` passes `""` → `default` today |
| `rng_seed` | `u64` | The match's initial seed. `TurnManager._ready()` calls `_rng.randomize()` and only seeds when `deterministic and seed != 0`, so the hook must always assign an explicit seed (drawn from a throwaway randomized RNG) and keep it |
| `rng_state` | `u64` | Live `RandomNumberGenerator.state` at capture. Restore order: set `seed` first, then `state` (setting `seed` resets state). Every future line pick and hand draw comes from this state, so there are no deck piles to store |
| `max_turns`, `turn_number` | `u8, u8` | `MatchConfig.max_turns`, `TurnManager.turn_number` |
| `turn_state` | `u8` | `TurnManager.State` (`START … MATCH_COMPLETE`) |
| `seg` | `u8` | `STRAIGHT, ENTRY, APEX, EXIT` |
| `current_turn_type` | `u8` | Index into `TrackData.TURN_TYPES` |
| `player_cum_progress`, `opponent_cum_progress` | `f64, f64` | Cumulative race progress (`PositionTracker`, mirrors `MatchResult.player_total_progress` / `opponent_total_progress`). GDScript `float` is 64-bit; `f64` keeps a resume bit-exact |
| `cars[2] (s, d, h, yaw_slip)` | `u16 + q16(d,100) + q16(h,100) + q16(yaw,10)` each | Player, then opponent |
| `player_hand` | `u8 count` + 2-bit stances | This turn's fresh hand, up to `HAND_SIZE` (drawn i.i.d. from `deck_weights()` after the line pick, §3) |
| `opponent_line` | `u8` (3×2-bit) | This corner's line from `TurnTypeData.pick_line()` (Entry, Apex, Exit); the opponent has no separate hand |
| `player_picks`, `opponent_picks` | `u8 count` + 2-bit stances | Up to `PICKS_PER_TURN` |
| `straight_timer_ms_left` | `u16` | From `StraightTimer` (`total_time - _elapsed`) |
| `face_sequence` + `bluff_flags` | `u8` (3×2-bit) + `u8` (3 bits) | Shown sequence from `FaceController.set_face_sequence()` / `TellGenerator.generate_tells()` and which positions are bluffs |
| `p_q_time`, `o_q_time` | `u8, u8` | Current/last turn's timing skill ×100, as passed to `CombatResolver.resolve_turn()` (before the knot window and HAN, which `clash_progress` applies): player = `QTEController` score / `QTE_NORMALIZER`, opponent = `OPPONENT_QTE` |
| `pick_history` | `u8 turns` + 6 bits/turn | Player picks for each completed turn (opponent picks are re-derived by `AIPicker` from the RNG) |
| `qte_history` | 2 B/turn | `p_q_time`, `o_q_time` per completed turn (same encoding) |

### 0.3 End-to-End Playtest → Bot Reproduction Loop

**Austin's workflow (one keypress)**
1. Something looks wrong. Optionally press `F3` (or `Shift+F3`) so the screenshot carries orientation.
2. Press `F9`. The token is on the clipboard, and the `.json` + `.png` are in `user://playtest_dumps/`.
3. Paste `MX1:...` into a chat with any Midnight Apex bot, plus one line of what's wrong and, optionally, the `.png`. That's the whole bug report.

**What each bot does with it**

| Bot | Reads | Typical use |
|---|---|---|
| **Gordon** (Godot) | Everything | Decode, boot Godot into the exact state, step `TurnManager`, fix in `scripts/`/`scenes/` |
| **Barry** (Systems) | Block B (economy, unlocks, ladder, build) + Block C (stats, progress, hands, tier) | Check the state against `design/07` and the `02` decision sheet; feed the stats/tier into `sim/velocity_shift/` to see whether the sim agrees. Godot's `RandomNumberGenerator` (PCG32) is not Python's `random`, so a sim run reproduces the *state and math*, not the exact draws |
| **Arthur** (Art) | Block A (scene, camera, rig, projection) + shell/livery IDs + `.png` | Framing, 640×480 readability, shell/livery/UV issues; re-render the exact frame with `--dump-frame` |
| **Nathaniel** (Narrative) | Block B (act, ladder, `beat_pc_bits`, substories, race-3 gate) | Which barks/dialogue should have fired (e.g. a loss-persistence rematch line) |

**Decoder / inspector CLI**: same codec and same output. Two placement options, and the folder boundary is the deciding factor (`AGENTS.md` "Stay in your folder"):
- **Option 1, Godot-only (zero cross-folder writes; Godot folder).** The codec lives as static functions in `scripts/PlaytestState.gd`. A tiny `scripts/tools/mx1_decode.gd` (`extends SceneTree`, because `--script` needs a `SceneTree`/`MainLoop` script) preloads it, prints JSON + lints and quits:
  `godot --headless --path /workspace/midnight-apex --script res://scripts/tools/mx1_decode.gd -- --decode "MX1:..."`
  Godot is already on the box (`/usr/local/bin/godot`), and decoding needs no renderer.
- **Option 2, pure Python (Barry's folder, only with Barry's OK).** `sim/scripts/decode_state.py` is zero-dependency Python 3.10+ (`base64`, `binascii`, `struct`, `zlib`, `json`), run from `sim/` like the other scripts:
  `python scripts/decode_state.py "MX1:..." [--json] [--lint] [--to-matchconfig]`
  `--to-matchconfig` is the optional sim bridge. It builds a `velocity_shift.models.MatchConfig` from Block B/C (effective stats, levels, tier, max turns) so a battle dump runs straight in the Python sim. Barry writes or approves it; Gordon doesn't touch `sim/`.
- Either way, both codecs (or the one chosen) must round-trip three golden tokens (hub, battle, compressed). These get pasted into this section when the codec lands.
- **Lints** printed on every decode, each a bug class caught for free:
  - `mods_unlocked`/`substories_open` ≠ `race_3_won`
  - `aero_unlocked` with `sabine_repair_debt > 0`, or a non-zero aero split while aero is locked
  - `aero_unlocked` before `DEBT_CLEAR_AFTER` is reached (fewer than one crew boss beaten in Round 2 per `crew_order` + `ladder`), or still locked after it
  - `betting_unlocked` before `BETTING_UNLOCK_AFTER` (end of Round 2)
  - a `crew_order` round that repeats a district, a picked crew whose boss isn't beaten while a later position in that round is set (lock-in broken), or a round opened before the previous one finished
  - `wholesale_unlocked` in `PROLOGUE`/`ROUND_1` before its end-of-round event
  - any `beat_pc_bits` set for a non-lieutenant/non-boss `RivalId`
  - a ladder step past a rival not in `defeated_bits`
  - `git7` ≠ the running build
  - a replay desync (below)

**Direct Godot reproduction and hot-load**
- CLI boot: `godot --path /workspace/midnight-apex -- --playtest-state "MX1:..." [--resume] [--dump-frame <path.png>]`. The value may also be `@<path>.json` to load a saved dump. `PlaytestState` (autoload) reads `OS.get_cmdline_user_args()`, validates version + CRC and warns on a `git7` mismatch. It then changes to the scene for `scene_id` (only `BATTLE` → `res://scenes/Battle.tscn` exists today; other IDs report "scene not built yet" instead of guessing). Next it applies Block B to the progression state (a future `GameState` autoload) and Block C through `TurnManager.restore_snapshot()`. Camera Block A is applied last via `BattleCamera.apply_rig_state()`, which kills running tweens. Finally it sets `get_tree().paused = true` unless `--resume` is passed.
- Battle restore has two modes (§0.4 decision 4):
  - **Direct resume**: set seed + state, restore the current hand, opponent line, picks, progress totals, timer, faces. Later turns' lines and hands follow from `rng_state`.
  - **Replay**: seed the RNG from `rng_seed`, then run turns `1..turn_number-1` headlessly from `pick_history` + `qte_history`. Each turn redraws in `match.py` order: line pick, then the player's fresh hand. Afterwards the live RNG state must equal the stored `rng_state`; if not, the decoder reports **"replay desync"**, which is itself a determinism bug. That requires every gameplay random draw to go through `TurnManager._rng` (no bare `randf()`; `Deck.draw_hand()` takes the match RNG and has no fallback RNG).
- `--dump-frame <path.png>`: after the warp, wait 2 rendered frames, save the root viewport (plus `_3d.png`) and quit. Don't use `--headless` for this, because the headless dummy renderer draws nothing. On the box, run it on the box desktop display. The box has no GPU for the Mobile (Vulkan) renderer, so a `--rendering-method gl_compatibility` capture is fine for placement and framing but not final PSX shading, which Arthur judges on Austin's Windows D3D12 build.
- In-game hot-load (`F10`, `debug_load_clipboard_state`): reads `DisplayServer.clipboard_get()`, trims it, and runs the same validate → warp path in a running debug session. A bot can then send Austin a modified token ("try this exact moment with the opponent one level higher") and he warps with one key.

### 0.4 Implementation Touchpoints & Open Decisions (for Austin to lock)

None of these files or edits exist yet. They are created only after Austin locks this spec.

| File | Planned change | Folder owner |
|---|---|---|
| `scripts/PlaytestState.gd` (new, autoload `PlaytestState`) | `MX1` codec (pack/unpack, CRC-16, Base64URL, DEFLATE), `capture()`, `restore()`, `F9`/`F10` handlers, cmdline boot, dump writer, lints | Godot |
| `scripts/DebugOverlay.gd` (new, autoload) | `F3`/`Shift+F3` HUD, toast | Godot |
| `scripts/tools/mx1_decode.gd` (new, Option 1 only) | `SceneTree` CLI wrapper | Godot |
| `project.godot` | Autoloads `PlaytestState`, `DebugOverlay`; input actions `debug_hud_toggle` (F3), `debug_hud_expand` (Shift+F3), `debug_dump_state` (F9), `debug_load_clipboard_state` (F10) | Godot |
| `scripts/TurnManager.gd` | Always-explicit seed; `capture_snapshot()` / `restore_snapshot()`; append `pick_history`/`qte_history` in `_end_turn()`; `seg` getter | Godot |
| `scripts/BattleCamera.gd` (+ attach to `World3D/Camera3D` in `Battle.tscn`) | `rig_mode` set in `transition_to_corner`/`transition_to_straight`/`swing_overtake`; `get_rig_state()` / `apply_rig_state()` | Godot |
| `scripts/CarAnimator.gd` (+ `Battle.tscn` node wiring) | `get_frenet()`; point tweens at the car `Node3D` rather than the plain `CarAnimators` parent | Godot |
| `scripts/StraightTimer.gd`, `FaceController.gd`, `TellGenerator.gd` | Expose ms-left / set elapsed; current face sequence + bluff flags | Godot |
| Future `GameState` autoload | Owns Block B fields at runtime (doesn't exist yet) | Godot |
| `.build_sha` + `.gitignore` entry | A pre-run/export helper writes `git rev-parse --short=7 HEAD` (+ dirty bit from `git status --porcelain`) to `res://.build_sha`; editor runs fall back to `OS.execute("git", …)` | Root/coordination (Desmond) |
| `sim/scripts/decode_state.py` (Option 2 only) | Pure-Python decoder + `--to-matchconfig` bridge | **Barry** (`sim/`) |

**Open decisions for Austin**
1. **Hotkeys and HUD placement:** `F3` HUD / `Shift+F3` expand / `F9` dump / `F10` clipboard warp, with the HUD at top-left (it overlaps the unanchored `TopBar` visually, though never for clicks) or bottom-left?
2. **What `F9` writes:** always the `.json` + `.png` (+ `_3d.png` in Battle) into `user://playtest_dumps/` alongside the clipboard token, or `.json` only with screenshots on `Shift+F9`?
3. **Decoder home:** Godot-only `scripts/tools/mx1_decode.gd` (no cross-folder writes), Barry-hosted `sim/scripts/decode_state.py` with the `--to-matchconfig` bridge so battle dumps run directly in `sim/velocity_shift/`, or both (with shared golden tokens)?
4. **Battle reproduction mode:** direct resume from the snapshot (`rng_state` + current hand/line/totals), seed + pick/QTE history replay (also catches determinism desyncs), or both? Both fit the same ~350–450-char token, since there are no deck piles to dump.
5. **Release safety:** `--playtest-state` and `F10` clipboard hot-warp enabled in all debug builds (`OS.is_debug_build()`) and stripped from release exports, with `F9` capture kept in release for external testers or not?
6. **Who owns the append-only ID tables** that the token indexes (`RivalId` roster, mod/part IDs, shell/livery IDs, substory IDs): Barry in `design/07` / `sim/config/parts.json` with a Godot mirror, or a Godot-side `scripts/` table that `design/` references?


### 0.5 Two-corner test token (`TC2`): implemented in `unapproved/gordon/two-corner/` (UNAPPROVED)

> Added by Gordon on 2026-11-11 with the shots10 sim re-pin, which Austin approved at 10:56 PM PT. This token belongs to the two-corner engine test only. It is a working example of the replay mode in §0.2 / Q4 and does not lock any part of `MX1`.

- **Format:** `TC2:<sim7>:<build10>:<base64url(json)>:<crc16_hex4>`.
  - `sim7` is the pinned sim commit (`_pin` HEAD; `f0efecf` since shots10).
  - `build10` is the first 10 hex characters of a SHA-1 over the build's own files: `project.godot`, `scripts/*.gd`, `shaders/*`, `spec/display.json`, `spec/race_config.json`. `tools/stamp_build.py` writes both values into `godot/spec/build.json`. `tools/run_parity.sh` runs it first.
  - The CRC is CRC-16/CCITT-FALSE, as in §0.2, over the ASCII `TC2` + `sim7` + `build10`, followed by the payload bytes.
  - The HUD menu shows `pin <sim7> build <build10>`.
- **Payload:** `seed`, `rng_draws`, `corner_index`, `phase`, the current `picks` and `auto`, and `turns[]`. Each completed turn has `picks` (hand indices after any auto-fill), `auto`, and `qte` = `[entry, apex, exit]`. Each phase score is either `null` (unplayed = `PHASE_QTE_UNPLAYED` = 0, Austin) or a `"0x<16 hex>"` IEEE-754 bit pattern. `cum_player` and `cum_opponent` are stored the same way, as a check only.
  - Scores are stored as bit patterns because Godot's JSON and decimal parser is not correctly rounded. In a box test, 37% of random doubles failed to round-trip through `JSON.stringify` → `parse_string`. TC1 stored totals as JSON numbers, so a load could drift by 1 ulp.
- **Load = replay:** `race_core.gd load_state()` seeds a fresh core and replays every turn's picks and phase scores through the same `submit_qte()` path, then re-picks the current corner. If the replayed phase, corner, `rng_draws` and the totals' bits differ from the token, it reports **"replay desync"**.
  - A token whose `sim7` differs from the running build is refused.
  - A token with the same `sim7` but a different `build10` loads with a warning. Results replay exactly; visuals may differ.
- **Old seeds reproduce on their own build:**
  - Results depend on the seed, the picks, the QTE input and the **sim pin**, so record `sim7` + `build10` (the token does this) with any seed you report.
  - `TC1:<sim7>:…` tokens are from sim 212eaab and repo `unapproved/gordon/two-corner` builds up to 4322b31. That era used a single 1–10 timing per turn. They are refused with a message telling you to check that commit out and replay there.
- **Tools:** `python3 tools/decode_token.py '<token>'` decodes TC2 and TC1, checks the CRC and turns the bit patterns into numbers. `F9` copies a token and `F10` loads one from the clipboard.
- **For `MX1` (proposal, not decided):** Austin's three QTEs per turn mean `qte_history` needs three values per turn (Entry / Apex / Exit, each a score or unplayed) instead of one. In §0.2 that is about 3 × `u16` per turn rather than 2 B per turn.
