# Midnight Apex — Godot Prototype

> Build a playable Godot prototype using only colored cubes. Tune gameplay constants,
> then replace cubes with real art — gameplay comes first.
>
> The Python code in `sim/velocity_shift/` is reference/prototype only — this is a
> full GDScript rewrite.

## How this works

| Icon | Who | What they do |
|------|-----|-------------|
| 🤖 | **MCP** | Creates scenes, scripts, and project settings using Godot tools |

---

## 0. Playtest-to-Troubleshooting Spec (PROPOSED)

> **Status: PROPOSED, spec only, uncommitted.** Drafted by Gordon (Godot) on 2026-11-06 at Austin's go-ahead, routed through Barry. Nothing in `project.godot`, `scenes/` or `scripts/` has been created or changed for it yet. Implementation starts after Austin locks §0.4.
> **Goal:** one keypress in a playtest gives any Midnight Apex bot (Gordon, Barry, Arthur, Nathaniel) an exact, copy-pasteable picture of *where* the game was (scene, coordinates, camera) and *what state* it was in (progression, economy, build, mid-race combat). With that, a bot can decode the moment, reproduce it in Godot, and debug it without guessing from a screenshot.
> **Number rule (`AGENTS.md`):** this section contains no balance values. Gameplay quantities are referenced by constant name and file (`HP_PER_LEVEL` and `RUBBER_BAND_PCT` in `sim/velocity_shift/equations.py` / `scripts/globals.gd`, `DECK_SIZE` in `sim/velocity_shift/deck.py`, `DEBT_SHARE` and `TIER_STAT_BUDGET` in `design/07-economy-and-mods.md`). The only literal numbers here are encoding sizes, pixel/viewport geometry and hotkeys.
> **Vocabulary:** follows the locked block in `design/01-system-overview.md`. The state token has **no reputation field** (reputation is lore only). Sabine's debt is her personal repair tab (`sabine_repair_debt`). The third stance is `Stance.NEUTRAL` in code, and debug output prints the code name `NEU`. The player-facing "Steady" vs "Neutral" name is still open on the `02` decision sheet (item 5).

### 0.1 Coordinate & Camera Reference System

**Axes and viewport**
- World axes follow Godot 4: right-handed and Y-up. `+X` is right, `+Y` is up and `-Z` is forward (the direction a `Camera3D` looks at zero rotation). Units are metres.
- Angles are in degrees and use Godot's `rotation_degrees` (Euler order YXZ): `pitch = x`, `yaw = y`, `roll = z`. `yaw = 0` faces `-Z`, positive yaw turns left (counter-clockwise seen from above), and the value is wrapped to `[-180, 180)`. `heading_deg` on cars and the player uses the same convention, wrapped to `[0, 360)`. On overworld maps, `-Z` is "north".
- The viewport is `640×480` with stretch mode `viewport` and aspect `keep` (§1.1; `project.godot` sets width, height and `stretch/mode`, and `keep` is Godot's default aspect). The 640×480 vs 640×448 question is still open as Arthur's Q3 in `design/art/art_direction.md`. Screen-space callouts use `(u, v)` in pixels: origin at top-left, `u ∈ [0, 640)`, `v ∈ [0, 480)`, always in the 640×480 base resolution before any upscale.

**3D Battle: two frames**
- *Track-relative (Frenet) frame `(seg, s, d, h, yaw_slip)`*, used in every bug report about car placement:
  - `seg` is the active segment: `STRAIGHT`, `ENTRY`, `APEX` or `EXIT`. It is derived from `TurnManager.State` (`STRAIGHT` → `STRAIGHT`; `CORNER_PLAYBACK` / `DAMAGE_BATCH` → the clash index 0/1/2 → `ENTRY`/`APEX`/`EXIT`).
  - `s ∈ [0.000, 1.000]` is normalized progress along that segment. On `StraightRoad` it is distance along `-Z` divided by the mesh length. On a corner it is `curve.get_closest_offset(local_pos) / curve.get_baked_length()` on the segment's `Curve3D` (§13.1 `Path3D`).
  - `d` is the signed lateral offset in metres from the road centreline (`-` left, `+` right). Here `right = tangent.cross(Vector3.UP)` at the closest baked point, so on today's straight (centreline at `x = 0` along `-Z`) `d == x`.
  - `h` is the height in metres above the road surface.
  - `yaw_slip` is the car's heading minus the road tangent's heading in degrees (drift angle, `+` = nose left).
- *Visual lead/trail from DP.* Car `s`/Z placement is purely a visualization of the DP gap (Appendix H). It must use the exact expressions in `TurnManager._determine_winner()`, so the picture can never disagree with the result:
  - `pos_p = player_cum_dp / opponent_max_hp`, `pos_o = opponent_cum_dp / player_max_hp`, with `*_max_hp = level × HP_PER_LEVEL` (`scripts/globals.gd`, ported from `sim/velocity_shift/equations.py`).
  - `lead = pos_p - pos_o`. A tie counts as the opponent leading (Appendix H tiebreaker). `CarAnimator.snap_to_gap(gap, max_gap)` stays the single place that maps the gap to Z offset. The HUD prints `lead` signed to 3 decimals.
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

- Field key: `f5b9114` is the short git SHA, with `*` meaning a dirty working tree. Then come scene, turn, `TurnManager.State` (`STA`/`STR`/`CRN`/`DMG`/`END`/`FIN`), `seg` and corner type (`TrackData.TURN_TYPES` name). The camera block is rig-mode code (`BCH`/`BCL`/`BCR`/`BOV`/`HUB`/`ISO`/`DBG`), `(x,y,z)`, yaw, pitch, and `f`=FOV or `o`=ortho size. Next are the cars' `(s, d)`, `lead`, the tier code (`WD`/`BT`/`LT`/`BS`/`MY`), the low 32 bits of the RNG seed in hex, and the shown face sequence. Hub line 2 shows act, the per-district ladder, the wild ramp, unlock initials (race-3 win, Mods, Substories, Wholesale, Aero, Betting) and debt open/closed, with no amount on the HUD. The active shell/livery IDs end the line.

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
| Battle with full 2-bit deck dump (`DECK_FULL`, §0.4 decision 4) | ~430–450 B | ~590–610 chars |

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
| `flags` | `u8` | bit0 `HAS_BATTLE_BLOCK`, bit1 `COMPRESSED`, bit2 `DIRTY_BUILD`, bit3 `DEBUG_FREE_CAM`, bit4 `DECK_FULL` (proposed), bit5 `PROJ_ORTHO`, bits6–7 reserved |
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
| `rng_state` | `u64` | Live `RandomNumberGenerator.state` at capture. Restore order: set `seed` first, then `state` (setting `seed` resets state) |
| `max_turns`, `turn_number` | `u8, u8` | `MatchConfig.max_turns`, `TurnManager.turn_number` |
| `turn_state` | `u8` | `TurnManager.State` (`START … MATCH_COMPLETE`) |
| `seg` | `u8` | `STRAIGHT, ENTRY, APEX, EXIT` |
| `current_turn_type` | `u8` | Index into `TrackData.TURN_TYPES` |
| `player_cum_dp`, `opponent_cum_dp` | `f64, f64` | GDScript `float` is 64-bit; `f64` keeps a resume bit-exact |
| `cars[2] (s, d, h, yaw_slip)` | `u16 + q16(d,100) + q16(h,100) + q16(yaw,10)` each | Player, then opponent |
| `player_hand`, `opponent_hand` | `u8 count` + 2-bit stances | Up to `DECK_HAND_SIZE` |
| `player_picks`, `opponent_picks` | `u8 count` + 2-bit stances | Up to `PICKS_PER_TURN` |
| `straight_timer_ms_left` | `u16` | From `StraightTimer` (`total_time - _elapsed`) |
| `face_sequence` + `bluff_flags` | `u8` (3×2-bit) + `u8` (3 bits) | Shown sequence from `FaceController.set_face_sequence()` / `TellGenerator.generate_tells()` and which positions are bluffs |
| `p_qte_score`, `o_qte_score` | `u8, u8` | Current/last QTE score ×10. Note: `_compute_damage()` still uses fixed placeholder QTE values instead of `QTEController` output, so these record whatever was actually used |
| `pick_history` | `u8 turns` + 6 bits/turn | Player picks for each completed turn (opponent picks are re-derived by `AIPicker` from the RNG) |
| `qte_history` | 2 B/turn | `p_qte`, `o_qte` per completed turn |
| deck piles (iff `DECK_FULL`) | `u8 count` + 2-bit stances, ×2 | Player and opponent draw piles in order, plus `u8×3` player discard counts (the player deck never reshuffles, so discard order doesn't affect future draws) |

### 0.3 End-to-End Playtest → Bot Reproduction Loop

**Austin's workflow (one keypress)**
1. Something looks wrong. Optionally press `F3` (or `Shift+F3`) so the screenshot carries orientation.
2. Press `F9`. The token is on the clipboard, and the `.json` + `.png` are in `user://playtest_dumps/`.
3. Paste `MX1:...` into a chat with any Midnight Apex bot, plus one line of what's wrong and, optionally, the `.png`. That's the whole bug report.

**What each bot does with it**

| Bot | Reads | Typical use |
|---|---|---|
| **Gordon** (Godot) | Everything | Decode, boot Godot into the exact state, step `TurnManager`, fix in `scripts/`/`scenes/` |
| **Barry** (Systems) | Block B (economy, unlocks, ladder, build) + Block C (stats, DP, hands, tier) | Check the state against `design/07` and the `02` decision sheet; feed the stats/tier into `sim/velocity_shift/` to see whether the sim agrees. Godot's `RandomNumberGenerator` (PCG32) is not Python's `random`, so a sim run reproduces the *state and math*, not the exact draws |
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
  - **Direct resume** (`DECK_FULL`): set seed + state, restore piles, hands, picks, DP, timer, faces.
  - **Replay**: rebuild decks from `rng_seed` (same `Deck.build` order: player, then opponent), then run turns `1..turn_number-1` headlessly from `pick_history` + `qte_history`. Afterwards the live RNG state must equal the stored `rng_state`; if not, the decoder reports **"replay desync"**, which is itself a determinism bug. That requires every gameplay random draw to go through `TurnManager._rng` (no bare `randf()`; `Deck.build()` must never hit its own `rng == null` fallback in a match).
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
4. **Battle reproduction mode:** full 2-bit deck dump (`DECK_FULL`, ~590–610-char tokens, direct resume), seed + pick/QTE history replay (~350–450 chars, also catches determinism desyncs), or both, with history always on and `DECK_FULL` as a flag?
5. **Release safety:** `--playtest-state` and `F10` clipboard hot-warp enabled in all debug builds (`OS.is_debug_build()`) and stripped from release exports, with `F9` capture kept in release for external testers or not?
6. **Who owns the append-only ID tables** that the token indexes (`RivalId` roster, mod/part IDs, shell/livery IDs, substory IDs): Barry in `design/07` / `sim/config/parts.json` with a Godot mirror, or a Godot-side `scripts/` table that `design/` references?

---

## 1. Project Bootstrap

**Goal:** `project.godot` configured, global singletons registered, resource types defined.

### 1.1 Project settings

**🤖 MCP configures:**

| Setting | Value |
|---------|-------|
| Display width | 640 |
| Display height | 480 |
| Stretch mode | `viewport` |
| Aspect | `keep` |
| Input map `qte_mash` | Space / X |
| Input map `qte_timing` | Enter / Z |
| Input map `ui_accept` | Enter / Space |
| Input map `ui_cancel` | Escape |

### 1.2 `globals.gd` (autoload)

**🤖 MCP creates** `scripts/globals.gd` — enums and constants.

```gdscript
enum Stance { ATTACK, DEFEND, NEUTRAL }
enum StanceOutcome { WIN = 1, NEUTRAL = 0, LOSS = -1 }
enum EncounterType { WILD, LIEUTENANT, BOSS }
enum PhaseType { AGGRESSIVE, REACTIVE, UNPREDICTABLE }
enum QteType { MASH, TIMING }
```

**Balance constants** (match `sim/velocity_shift/equations.py` exactly):

| Name | Value | Notes |
|------|-------|-------|
| `CLASH_STAKES` | 0.35 | clash_mult = 1 ± CLASH_STAKES |
| `BATTLE_BONUS` | 0.05 | battle_mult bonus per win-margin point |
| `MITIGATION_PER_1000` | 0.40 | EN reduction per 1000 EN |
| `MITIGATION_FLOOR` | 0.10 | minimum damage fraction |
| `HP_PER_LEVEL` | 180 | max_hp = level × HP_PER_LEVEL |
| `QTE_NORMALIZER` | 10.0 | qte_factor = score / QTE_NORMALIZER |
| `HAN_QTE_WEIGHT` | 0.50 | HAN modifier for both sides |
| `DECK_SIZE` | 192 | cards per deck |
| `DECK_ALPHA` | 0.85 | smoothing term for deck weights |
| `DECK_HAND_SIZE` | 6 | cards drawn per turn |
| `PICKS_PER_TURN` | 3 | stances selected per turn |
| `RUBBER_BAND_PCT` | 0.15 | % of avg max HP for full rubber-band |
| `STRAIGHT_DURATION` | 12.0 | seconds for all 3 picks |
| `PHASE_DURATION` | 4.0 | seconds per individual pick |
| `QTE_TIMING_WINDOW_BASE_MS` | 800 | base width of timing target zone |
| `QTE_TIMING_WINDOW_PER_GAP` | 50 | ms shrunk per level of opponent advantage |
| `QTE_TIMING_WINDOW_MIN_MS` | 200 | floor for timing target zone |
| `QTE_MASH_SPEED_PER_GAP` | 0.10 | press-rate multiplier per level gap |

### 1.3 `SignalBus.gd` (autoload)

**🤖 MCP creates** `scripts/SignalBus.gd` — central event bus.

```gdscript
signal match_started(cfg)
signal straight_started(turn, turn_type, stances, bluff_flags)
signal phase_pick(phase_index, phase_name)
signal card_selected(stance)
signal phase_pick_timeout(phase_index)
signal corner_started(player_stances, opponent_stances)
signal clash_resolved(position, player_stance, opponent_stance, outcome)
signal corner_ended(qte_score)
signal damage_batch_done(player_dp, opponent_dp, cum_p, cum_o, battle_mult)
signal turn_ended(turn)
signal lap_began(phase, total)
signal match_ended(winner, player_name, opponent_name)
```

### 1.4 Resource scripts

**🤖 MCP creates** `scripts/CombatantStats.gd` and `scripts/MatchConfig.gd`:

```gdscript
# CombatantStats.gd
extends Resource; class_name CombatantStats
@export var name: String
@export var pow: float
@export var en: float
@export var han: float
@export var level: int
```

```gdscript
# MatchConfig.gd
extends Resource; class_name MatchConfig
@export var player_stats: CombatantStats
@export var opponent_stats: CombatantStats
@export var max_turns: int = 99
@export var seed: int
@export var deterministic: bool = true
@export var rival_personality: String
@export var encounter_type: String
```

---

## 2. Battle Scene

**Goal:** A 3D scene with two colored cubes on a ground plane, full UI overlay.

### 2.1 Scene hierarchy

**🤖 MCP creates** `scenes/Battle.tscn`:

```
Battle (Node)                                   ← TurnManager.gd attached
├── World3D (SubViewport)                       ← 3D viewport (640×480, transparent)
│   ├── WorldEnvironment                        ← sky, ambient, fog
│   ├── DirectionalLight3D                     ← shadows off for simplicity
│   ├── Camera3D                               ← chase cam (see Step 12)
│   ├── StraightRoad (Node3D)
│   │   └── MeshInstance3D                     ← BoxMesh, gray ~4×0.1×30
│   ├── CornerRoad (Node3D)
│   │   └── MeshInstance3D                     ← curved plane (placeholder, hidden during straight)
│   ├── PlayerCube (MeshInstance3D)            ← BoxMesh 1×1×1, white material
│   ├── OpponentCube (MeshInstance3D)          ← BoxMesh 1×1×1, white material
│   └── CarAnimators (Node)
│       ├── PlayerCarAnimator (Node)           ← CarAnimator.gd
│       └── OpponentCarAnimator (Node)         ← CarAnimator.gd
│
├── CanvasLayer (2D UI — 640×480)
│   ├── TopBar (HBoxContainer)
│   │   ├── PositionLabel (Label)             ← "1st" / "2nd"
│   │   ├── PhaseLabel (Label)                ← "LAP 1/3"
│   │   ├── TurnTypeLabel (Label)             ← "Hairpin L"
│   │   └── CornerTimerBar (TextureProgress)  ← 12s countdown
│   │
│   ├── CenterContent (HBoxContainer)
│   │   ├── OpponentPanel (VBox, 160px)
│   │   │   ├── FaceStack (Control 120×160)
│   │   │   │   ├── FaceATK (TextureRect)
│   │   │   │   ├── FaceDEF (TextureRect)
│   │   │   │   ├── FaceNEU (TextureRect)
│   │   │   │   └── TellOverlay (TextureRect)
│   │   │   ├── OpponentNameLabel (Label)
│   │   │   └── DPBarOpponent (TextureProgress)
│   │   │
│   │   ├── CenterGap (Control)               ← 3D viewport shows through
│   │   │
│   │   └── CardPanel (VBox, 180px)
│   │       ├── PhasePromptLabel (Label)      ← "ENTRY — Pick your stance"
│   │       ├── StraightTimerBar (TextureProgress)
│   │       ├── AttackButton (Button)
│   │       ├── DefendButton (Button)
│   │       └── SteadyButton (Button)
│   │
│   ├── BottomBar (HBoxContainer)
│   │   ├── PhaseColumn (VBox)
│   │   │   ├── EntryLabel (Label, "ENTRY")
│   │   │   ├── ApexLabel (Label, "APEX")
│   │   │   └── ExitLabel (Label, "EXIT")
│   │   ├── PlayerColumn (VBox)
│   │   │   ├── P1Panel (Panel)               ← colored bg per stance
│   │   │   │   └── P1Label (Label, stance name)
│   │   │   ├── P2Panel (Panel)               ← colored bg per stance
│   │   │   │   └── P2Label (Label, stance name)
│   │   │   └── P3Panel (Panel)               ← colored bg per stance
│   │   │       └── P3Label (Label, stance name)
│   │   ├── OpponentColumn (VBox)
│   │   │   ├── O1Panel (Panel)               ← colored bg per stance
│   │   │   │   └── O1Label (Label, stance name)
│   │   │   ├── O2Panel (Panel)               ← colored bg per stance
│   │   │   │   └── O2Label (Label, stance name)
│   │   │   └── O3Panel (Panel)               ← colored bg per stance
│   │   │       └── O3Label (Label, stance name)
│   │   └── DPBarPlayer (TextureProgress)
│   │
│   └── QTEOverlay (CenterContainer, hidden)
│       ├── QTEPromptLabel (Label)
│       ├── MashIndicator (TextureProgress)
│       └── TimingIndicator (Control)
│           ├── QteTarget (TextureRect)      ← target zone
│           └── QteMarker (TextureRect)      ← moving marker
│
└── TurnManager (Node)                          ← TurnManager.gd
```

---

## 3. Deck

**Goal:** 192-card stat-proportional deck. GDScript port of `sim/velocity_shift/deck.py`.

### 3.1 `Deck.gd`

**🤖 MCP creates** `scripts/Deck.gd`:

```gdscript
class_name Deck

const DECK_SIZE = 192
const ALPHA = 0.85

static func build(pow: float, en: float, han: float,
                  reshuffle_on_end: bool = false,
                  rng: RandomNumberGenerator = null) -> Deck
    # Compute weights using ALPHA smoothing (matching deck.py):
    #   total = pow + en + han
    #   w_atk = (pow / total) * (1 - ALPHA) + ALPHA / 3
    #   w_def = (en / total) * (1 - ALPHA) + ALPHA / 3
    #   w_neu = (han / total) * (1 - ALPHA) + ALPHA / 3
    # Fill DECK_SIZE cards proportionally, shuffle, return Deck instance

func draw(n: int = 6) -> Array                  # Draw up to n cards, return Array[Stance]
func prepare_turn_hand(requirements: Dictionary = {}) -> Array   # AI draw with retry
func end_turn(played: Array, unpicked: Array)   # Discard or reshuffle
func hand_stance_counts(hand: Array) -> Dictionary  # {ATTACK: N, DEFEND: N, NEUTRAL: N}
```

**Key rules:**
- Opponent deck: `reshuffle_on_end = true` (all 6 back, reshuffled each turn)
- Player deck: `reshuffle_on_end = false` (played + unpicked → discard pile)
- If draw pile < 6, return remaining cards (no auto-reshuffle)
- Deck weights use the same ALPHA smoothing as the Python prototype

### 3.2 Deck weights reference

```
total = pow + en + han
w_atk = (pow / total) × (1 - ALPHA) + ALPHA / 3
w_def = (en / total) × (1 - ALPHA) + ALPHA / 3
w_neu = (han / total) × (1 - ALPHA) + ALPHA / 3
```

---

## 4. Straight Timer + Card Selection

**Goal:** 12s countdown, 3 sequential phases (entry/apex/exit), auto-pick on timeout.

> **Prototype timer, not the locked tell.** Austin locked the read on 2026-11-06 in `design/06-pattern-read.md`: the player locks all 3 cards up front, before corner playback, and the car tell is lane Entry (outside = Attack, center = Steady, inside = Defend), which can bluff by improper placement. Apex and Exit are inferred, with no explicit tell and no extra bluff layer. Shared Touge, Wangan, and Street tendencies are the intended inference, and the precise mapping is still TBD. The Aggressive, Defensive, and Precise rows in that doc are not that map. The steps below match the scripts that are already in the repo. They were not rewritten, and this decision did not pick 12s over the old 8s sentence in that doc.

### 4.1 `StraightTimer.gd`

**🤖 MCP creates** `scripts/StraightTimer.gd`:

```gdscript
extends TextureProgress

var total_time: float = 12.0
var phase_times: Array[float] = [4.0, 4.0, 4.0]
var current_phase: int = 0

signal phase_timeout(phase_index)
signal straight_complete

func start():
    # 12s countdown, emit phase_timeout at 4s, 8s, 12s
    # Update TextureProgress.value 0 → max over 12s
    # Phase prompt changes: ENTRY → APEX → EXIT
```

**Timeline:**

```
 0.0s  StraightTimer.start()
       → phase_pick(0) — CardHandUI enables, prompt: "ENTRY"
 4.0s  → phase_timeout(0) or player picks → phase_pick(1) — prompt: "APEX"
 8.0s  → phase_timeout(1) or player picks → phase_pick(2) — prompt: "EXIT"
 12.0s → straight_complete
```

### 4.2 `CardHandUI.gd`

**🤖 MCP creates** `scripts/CardHandUI.gd`:

```gdscript
func on_hand_dealt(hand: Array):
    counts = Deck.hand_stance_counts(hand)
    AttackButton.text = "ATTACK (x" + str(counts[ATTACK]) + ")"
    DefendButton.text = "DEFEND (x" + str(counts[DEFEND]) + ")"
    SteadyButton.text = "STEADY (x" + str(counts[NEUTRAL]) + ")"
    disable all buttons initially

func on_phase_pick(phase_index):
    enable all buttons with count > 0

func on_card_selected(stance):
    decrement count for that stance
    update button text
    if count == 0: disable button
    emit card_selected(stance)
    disable all buttons until next phase_pick

func on_pick_timeout(phase_index):
    auto-pick the stance with the highest remaining count
    (fallback: worst expected value)
```

---

## 5. Combat Math

**Goal:** Pure functions, 1:1 port from `sim/velocity_shift/equations.py` + `combat.py`.

### 5.1 `CombatResolver.gd`

**🤖 MCP creates** `scripts/CombatResolver.gd` — all static:

```gdscript
static func resolve_stance(a: Stance, b: Stance) -> StanceOutcome
    # Attack > Neutral > Defend > Attack

static func clash_mult(outcome: StanceOutcome) -> float
    # WIN → 1.35, LOSS → 0.65, NEUTRAL → 1.0

static func compute_damage(pow: float, qte_factor: float, clash_mult: float, battle_mult: float) -> float
    # pow × qte_factor × clash_mult × battle_mult

static func damage_mitigation(en: float, qte_factor: float) -> float
    # max(MITIGATION_FLOOR, 1 - (en/1000) × MITIGATION_PER_1000 × qte_factor)

static func qte_factor(score: float) -> float
    # score / QTE_NORMALIZER

static func apply_han_qte_mod(score: float, han_pct: float) -> float
    # score × (1 + HAN_QTE_WEIGHT × (han_pct - 1/3))

static func battle_winner(outcomes: Array) -> String
    # sum(outcome.values) — positive → "Player", negative → "Opponent", zero → "Tie"

static func battle_multiplier(outcome_sum: int) -> float
    # 1 + BATTLE_BONUS × abs(outcome_sum)

static func qte_rubber_band(player_gap: float, threshold: float, p_qte: float, o_qte: float) -> Dictionary
    # Returns { p_damage_qte, p_mitigation_qte, o_damage_qte, o_mitigation_qte }
    # Proportional blend: leader's disadvantaged stat erodes toward 1.0 as gap widens
```

Reference: `sim/velocity_shift/equations.py` — every formula is there.

---

## 6. Turn Manager

**Goal:** One state machine orchestrates the whole game loop.

### 6.1 `TurnManager.gd`

**🤖 MCP creates** `scripts/TurnManager.gd` — attached to Battle root.

```
States:
┌──────────────────────────────────────────────────────────────────────┐
│  START         → load config, build decks, init visuals              │
│       ↓                                                             │
│  STRAIGHT      → 12s timer with 3 sub-phases:                       │
│       │            [0-4s]  PICK_ENTRY                               │
│       │            [4-8s]  PICK_APEX                                │
│       │            [8-12s] PICK_EXIT                                │
│       ↓ (all 3 picks locked in)                                    │
│                                                                      │
│  CORNER_PLAYBACK → auto-resolve 3 clashes in sequence               │
│       │             + QTE runs simultaneously                        │
│       ↓ (QTE captured + all outcomes known)                         │
│                                                                      │
│  DAMAGE_BATCH   → compute DP, update bars, tween car positions      │
│       ↓ (tweens done)                                               │
│                                                                      │
│  END_TURN       → deck cycle, lap check                             │
│       ↓ (more turns)                    ↓ (max turns)              │
│  → STRAIGHT                           MATCH_COMPLETE               │
└──────────────────────────────────────────────────────────────────────┘
```

**State transition triggers:**

| State | Entered by | Exited by |
|-------|-----------|-----------|
| START | Scene loaded | Setup complete |
| STRAIGHT | Previous END_TURN (or START) | All 3 picks stored |
| CORNER_PLAYBACK | All 3 picks locked | QTE complete + 3 clashes resolved |
| DAMAGE_BATCH | Corner end | Tween animations done |
| END_TURN | Damage displayed | Deck cycled |
| MATCH_COMPLETE | Max turns reached | — |

---

## 7. QTE

**Goal:** Runs during the corner phase. Type depends on turn_type × player stance.

### 7.1 `QTEController.gd`

**🤖 MCP creates** `scripts/QTEController.gd`:

```gdscript
func start(qte_type: QteType, difficulty: Dictionary):
    # Show QTEOverlay
    # Mash: count presses against speed_multiplier requirement
    #   Fills MashIndicator TextureProgress over ~3-4s
    #   difficulty.speed_multiplier adjusts how fast fill depletes between presses
    #   At 1.5x, you must press 50% faster to maintain the same fill rate
    # Timing: moving marker across target zone
    #   difficulty.timing_window_ms sets the width of the target zone
    #   Multiple successful presses increase score
    # Read QTE type from TurnTypeData.get_qte_type(turn_type, player_stance)
    # Runs ~3-4s (concurrent with clash resolution)

func stop() -> float:
    # Mash: final score = fill% × 10, normalized 1.0–10.0
    # Timing: final score = (successful_presses / total_opportunities) × 10
    # Return final score (1.0–10.0)
```

**Difficulty:**

```gdscript
static func qte_difficulty(player_level: int, opponent_level: int) -> Dictionary:
    var gap = opponent_level - player_level
    return {
        timing_window_ms: max(QTE_TIMING_WINDOW_MIN_MS,
            QTE_TIMING_WINDOW_BASE_MS - gap * QTE_TIMING_WINDOW_PER_GAP),
        speed_multiplier: 1.0 + max(0, gap) * QTE_MASH_SPEED_PER_GAP,
    }
```

| gap | timing_window_ms | speed_multiplier | feel |
|-----|-----------------|-----------------|------|
| -10 | 800 (capped) | 1.0 | Player dominates — no bonus |
| 0 | 800 | 1.0 | Even match — base difficulty |
| +3 | 650 | 1.30 | Opponent fav — tighter timing |
| +6 | 500 | 1.60 | Tough — zone shrinks, mash races |
| +10 | 300 | 2.00 | Max before soft floor at 200ms |

### 7.2 QTE Type lookup

One continuous QTE per corner. Type determined by `(turn_type × stance)`:

| Turn Type | ATTACK | DEFEND | STEADY |
|-----------|--------|--------|--------|
| Hairpin | MASH | TIMING | TIMING |
| Constant Radius | TIMING | MASH | MASH |
| Decreasing Radius | MASH | TIMING | MASH |
| Increasing Radius | TIMING | MASH | TIMING |
| 90-Degree | MASH | TIMING | MASH |
| Chicane | TIMING | MASH | MASH |
| Esses | MASH | TIMING | TIMING |
| Sweeper | TIMING | MASH | TIMING |

---

## 8. AI Layer

**Goal:** Opponent card selection, QTE generation, data resources.

### 8.1 Data resources

**🤖 MCP creates** static data classes:

**`TurnTypeData.gd`** — per-district line tables. Mirrors `LINE_SET_C` in `sim/velocity_shift/equations.py` exactly (copied into `scripts/globals.gd` like every other sim constant, never retuned here): district (`touge`, `wangan`, `street`) → corner code (`HP`, `CR`, `DR`, `IR`, `N90`, `CH`, `ES`, `SW`) → `[main, alt1, alt2]`, each an Entry/Apex/Exit string of `D` (Defend), `S` (Steady = `Stance.NEUTRAL`) and `A` (Attack). The alternates share main's Entry: `alt1` switches Apex+Exit, `alt2` switches Exit only. Once per corner (each turn), the opponent draws one whole line with a single weighted pick over `[main, alt1, alt2]` with weights `[LINE_ADHERENCE, (1 - LINE_ADHERENCE) × LINE_ALT_WEIGHTS["alt1"], (1 - LINE_ADHERENCE) × LINE_ALT_WEIGHTS["alt2"]]`. It's one draw, not an adherence roll followed by an alternate roll. It plays the chosen line exactly, and its hand never blocks it. When `equations.py` changes a line (for example the 6fc87d5 Street `N90` and Wangan `IR`/`SW` edits), only the mirrored table changes:

```gdscript
static func get_lines(district: String, corner: String) -> Array[String]
    # Returns LINE_SET_C[district][corner] = [main, alt1, alt2]

static func pick_line(district: String, corner: String, rng: RandomNumberGenerator) -> Array[Stance]
    # One weighted pick over [main, alt1, alt2] (weights above), once per corner;
    # one rng draw (rng.rand_weighted(weights)); hand never blocks the line
    # Returns [entry_stance, apex_stance, exit_stance]

static func get_qte_type(turn_type: String, stance: Stance) -> QteType
    # Returns MASH or TIMING
```

**`ArchetypeData.gd`** — comfortable/weak turn zones per archetype:

```gdscript
static func get_meta_archetype(archetype: String) -> String    # "POW" / "EN" / "HAN"
static func get_face_type(archetype: String) -> String         # "Scowling" / "Grinning" / "Focused"
static func is_comfortable_turn(archetype: String, turn_type: String) -> bool
static func is_weak_turn(archetype: String, turn_type: String) -> bool
```

**`PersonalityData.gd`** — 5 personality configs (Aggressive, Defensive, Precise, Balanced, Adaptive) with 3 phases each. They mirror `PERSONALITY_MAP` in `sim/velocity_shift/ai.py`, which is the source of truth for each phase's type, weights, behavior override and hand requirements; see the phase table in `design/04-difficulty-tuning.md`. Wild races use phase 0 only, Lieutenants phases 0–1, Bosses all three.

**`TrackData.gd`** — predetermined 10-turn sequence per circuit:

```gdscript
static func get_track_layout(circuit_id: String) -> Array[String]
static func get_turn_type(turn: int, circuit_id: String) -> String
```

### 8.2 `AIPicker.gd`

**🤖 MCP creates** `scripts/AIPicker.gd`:

```gdscript
static func pick_card(hand: Array, opponent_hand: Array,
                      phase_index: int, personality: PersonalityConfig,
                      clash_index: int, previous_clashes: Array,
                      turn_number: int,
                      player_stance_history: Array[Stance],
                      rng: RandomNumberGenerator) -> Stance
    # MoveScore = EVWeight + PhaseWeight + PersonalityWeight + Randomness
    # Behavior overrides: counter, alternate, highest_ev, repeat_win
    # Unpredictable phase: 70% EV / 30% random
```

### 8.3 `AIQTE.gd`

**🤖 MCP creates** `scripts/AIQTE.gd`:

```gdscript
static func generate_qte(level: int, encounter_type: String,
                          rng: RandomNumberGenerator,
                          deterministic: bool,
                          han_pct: float) -> float
    # Baseline = 7.0 × level_ratio (Wild=0.35, Lieutenant=0.75, Boss=1.15)
    # Modified by HAN proportion via apply_han_qte_mod
    # Noise range shrinks as opponent level increases
```

---

## 9. Tell System

**Goal:** Opponent face display with deception and bluff tells, crossfade schedule.

> **Prototype face draft, not the locked tell.** The locked car tell is lane Entry under the visual-gap rule in `design/06-pattern-read.md`. Apex and Exit are inferred, and the Touge, Wangan, and Street mapping for that inference is still TBD. This section documents the face scripts already in the repo. It does not adopt the Aggressive, Defensive, and Precise rows as that mapping, and it does not add an Apex/Exit tell, an extra bluff layer, or a probability for bluffing Entry by improper placement.

### 9.1 `TellGenerator.gd`

**🤖 MCP creates** `scripts/TellGenerator.gd` — implements the deception flow from `06-pattern-read.md`:

```gdscript
static func generate_tells(turn: int, archetype: String,
                           turn_type: String, encounter_type: String,
                           rng: RandomNumberGenerator) -> Array[Dictionary]
    # 1. Look up true stance sequence from TurnTypeData
    # 2. Check comfort/weak zones
    # 3. Apply lie rate per clash position
    # 4. Apply clash-position weighting
    # 5. Apply reverse psychology (top tier)
    # Returns Array of 3 { stance: Stance, is_bluff: bool, expression_key: String }
```

### 9.2 Face types

Each archetype maps to one face type with 3 expressions:

| Face Type | ATK expression | ATK tell | DEF expression | DEF tell | NEU expression | NEU tell |
|-----------|---------------|----------|----------------|----------|----------------|----------|
| A — Scowling (POW) | Bared teeth, furrowed brow | Mouth closes over bared teeth briefly | Tight jaw, narrowed eyes | Eyes flick wide then narrow back | Flat stare, relaxed brow | Brow drops and returns |
| B — Grinning (EN) | Wide smile, raised brows | Raised brows drop flat | Thin smile, watchful eyes | Eyes shift to the side | Half-smirk, steady gaze | Half-smirk goes straight |
| F — Focused (HAN) | Intense stare, sharp focus | Intense gaze loses focus, drifts | Cocky smirk, raised brow | Raised brow drops flat | Relaxed half-smile | Half-smile vanishes |

### 9.3 `FaceController.gd`

**🤖 MCP creates** `scripts/FaceController.gd`:

```gdscript
func set_face_sequence(expressions: Array[Dictionary], face_type: String)
    # Called at straight start with 3 (stance, is_bluff) tuples
    # Load the correct ATK/DEF/NEU textures for this face_type
    # Set tell overlay textures per stance
    # AnimationTreeBlendManager handles the alpha crossfade timing

func set_tell_alpha(intensity: float, is_deceptive: bool)
    # TellOverlay.modulate.a = intensity × (1.0 if is_deceptive else 0.0)
```

**Face crossfade mechanism:**

```
FaceStack (Control)
├── FaceATK (TextureRect)   ← modulate.a driven by stance_blend schedule
├── FaceDEF (TextureRect)   ← modulate.a driven by stance_blend schedule
├── FaceNEU (TextureRect)   ← modulate.a driven by stance_blend schedule
└── TellOverlay (TextureRect) ← modulate.a = intensity × is_deceptive
```

At any moment exactly one face texture has `a = 1.0` during a phase, with smooth 0.5s crossfade between phases. The tell overlay sits on top at reduced alpha.

**Face reveal schedule:**

```
 0s-4s:   ENTRY face shown + tell (if deceptive)
 4s-8s:   Crossfade to APEX expression
 8s-12s:  Crossfade to EXIT expression
```

---

## 10. Position & Damage Display

**Goal:** Track cumulative damage, update DP bars, show clash results.

### 10.1 `PositionTracker.gd`

**🤖 MCP creates** `scripts/PositionTracker.gd`:

```gdscript
var player_total_dp: float = 0.0
var opponent_total_dp: float = 0.0

func add_turn_damage(player_dp: float, opponent_dp: float)
    # Accumulate
    # Update DPBarPlayer.value and DPBarOpponent.value
    # Compute and emit position label (1st/2nd)

func get_player_gap() -> float
    # return player_total_dp - opponent_total_dp

func get_rubber_band_threshold(avg_max_hp: float) -> float
    # return avg_max_hp * RUBBER_BAND_PCT
```

### 10.2 `DamageDisplay.gd`

**🤖 MCP creates** `scripts/DamageDisplay.gd`:

```gdscript
func animate_bars(player_new_total: float, opponent_new_total: float,
                  player_max_hp: float, opponent_max_hp: float)
    # Tween DPBarPlayer.value and DPBarOpponent.value from current to new
    # Duration: 0.8s
    # Flash "1st" / "2nd" label update
```

### 10.3 `ClashDisplay.gd`

**🤖 MCP creates** `scripts/ClashDisplay.gd`:

```gdscript
const COLORS = {
    ATTACK:  Color("#dc2626"),
    DEFEND:  Color("#16a34a"),
    NEUTRAL: Color("#d97706"),
}

func display_summary(player_stances: Array[int], opponent_stances: Array[int])
    # 2 rows × 3 cols: PhaseColumn | PlayerColumn | OpponentColumn
    # Color panels per stance

func reveal_phase(phase_index: int)
    # Brief scale-pulse fade-in for this row
```

### 10.4 `PhaseAnnouncer.gd`

**🤖 MCP creates** `scripts/PhaseAnnouncer.gd`:

```gdscript
func announce_lap(phase: int, total: int)
    # Show overlay: "LAP 2/3" with fade-in, hold 1.5s, fade-out
```

---

## 11. Car Animation

**Goal:** Each car has a straight Z-offset and corner path traversal. AnimationTree blends stance body language.

> **Drawn spacing is not the DP gap.** `snap_to_gap` in `scripts/CarAnimator.gd` still lerps a symmetric Z range from the DP fraction (`lerp(-5.0, 5.0, …)`). That script was not changed. The locked presentation rule is in `design/06-pattern-read.md`: when the player is behind, the rival is drawn only as far ahead as keeps lane and Entry readable from the fixed rear third-person player camera (no distance number approved); when the player is ahead, the trailer recedes in the top-center mirror with no matching rear cap. Actual cumulative DP is unchanged. Do not read a large lead's exact size off the visible spacing.

### 11.1 `CarAnimator.gd`

**🤖 MCP creates** `scripts/CarAnimator.gd` — one per car:

```gdscript
# ─── Straight phase ───────────────────────────────────────────────

var straight_base_z: float = 0.0

func snap_to_gap(gap: float, max_gap: float)
    # PROTOTYPE ONLY (still what CarAnimator.gd does). Not the locked visual gap.
    # The symmetric ±5 range caps the trailer the same way as the leader; the
    # locked rule caps only how far ahead of the player the rival is drawn.
    # global_position.z = straight_base_z + lerp(-5.0, 5.0, clamp(gap / max_gap, -1.0, 1.0))
    # Tween over 0.5s

func play_surge()
    # Brief forward burst (clash win)

func play_drop()
    # Brief backward fall (clash loss)

# ─── Corner phase ─────────────────────────────────────────────────

var corner_path: Curve3D
var corner_progress: float = 0.0
var progress_offset: float = 0.0

func begin_corner_traversal(path: Curve3D, duration: float = 3.5)
    # Store Path3D curve from CornerRoad
    # PROTOTYPE ONLY. The 10% path offset is not an approved draw distance.
    # Locked spacing is the visual-gap rule in design/06-pattern-read.md (no number).
    # Read current DP gap from PositionTracker
    # Set progress_offset = dp_gap / max_gap × 0.1 (10% path offset per full gap)
    # Tween corner_progress from 0.0 → 1.0 over duration

func _on_corner_progress_updated(progress: float)
    # position = corner_path.sample_baked(clamp(progress + progress_offset, 0.0, 1.0))
    # Align car rotation to path tangent

func play_overtake()
    # 0.5-1s pass animation — car moves from behind to ahead along corner path

func end_corner_traversal()
    # Reset to straight positioning
```

### 11.2 Animation Tree structure

**Car AnimationTree:**

```
AnimationTree
├── AnimationNodeBlend3 (root)
│   ├── Animation (corner_left)        ← base (blend via corner_blend param)
│   ├── Animation (corner_right)       ← base (blend via corner_blend param)
│   └── AnimationNodeBlend3 (stance blend)
│       ├── Animation (pose_attack)    ← blended via stance_blend param
│       ├── Animation (pose_defend)
│       └── Animation (pose_steady)
```

### 11.3 `AnimationTreeBlendManager.gd`

**🤖 MCP creates** `scripts/AnimationTreeBlendManager.gd` — drives both car AnimationTree and face crossfade:

```gdscript
func start_blend_cycle(entry_stance: Stance, apex_stance: Stance,
                       exit_stance: Stance, corner_direction: String)
    # PROTOTYPE face/stance crossfade. Not an explicit Apex/Exit tell.
    # Locked tell is lane Entry (design/06-pattern-read.md).
    # Set corner_blend on both car AnimationTrees (left=0.0, right=1.0)
    # Begin 12s stance_blend schedule:
    #   0s-4s:   stance_blend → entry_stance weight 1.0
    #   4s-8s:   crossfade → apex_stance weight 1.0
    #   8s-12s:  crossfade → exit_stance weight 1.0
    # Same schedule drives FaceStack alpha

func update_blend(delta: float)
    # Called each frame during STRAIGHT state
    # Interpolates stance_blend parameter

func set_tell_alpha(intensity: float, is_deceptive: bool)
    # TellOverlay.modulate.a = intensity × (1.0 if is_deceptive else 0.0)
```

### 11.4 Connected signals

- `turn_state_changed(STRAIGHT)`: `snap_to_gap(...)` with current DP
- `turn_state_changed(CORNER_PLAYBACK)`: `begin_corner_traversal(...)`
- `clash_resolved(position, ...)`: `play_surge()` on winner / `play_drop()` on loser
- `lead_changed`: `play_overtake()` on overtaking car
- `turn_state_changed(DAMAGE_BATCH)`: `end_corner_traversal()`

---

## 12. Camera

**Goal:** Fixed rear third-person camera on the player. The rival's drawn gap is asymmetric so Entry stays readable when the player is behind, and gets harder to read in the mirror when the player is ahead. Rule: `design/06-pattern-read.md` (Lane Entry and visual gap). Actual DP, position, and the win condition do not follow the drawn spacing.

### 12.1 Locked view (2026-11-06)

- The race view used to read Entry is a fixed rear third-person camera on the **player**. It is not placed behind both cars, and it does not pull back to keep an uncapped leader in shot.
- **Player behind:** cap how far ahead the rival is drawn so that rival's lane and Entry (outside = Attack, center = Steady, inside = Defend, relative to the next corner) stay readable. No distance number is approved. The cap is draw distance only. It is not `RUBBER_BAND_FRACTION`, not a real-gap cap, and not a damage or AI change. Visible spacing does not show the exact size of a large real lead.
- **Player ahead:** the trailing rival recedes in the top-center rear-view mirror. Do not cap that recession to match the forward cap. Headlights and lane get harder to read with distance. That loss of Entry information is intentional. Do not add a HUD lane marker or enlarge the lamps to undo it.
- Corner-playback camera paths later in this guide are the cinematic after the line is locked. They do not replace this view as the one Entry is read from, and they do not authorize a symmetrical rear cap.
- Display settings are unchanged: 640×480, viewport stretch, keep aspect, as in §1.1 and `project.godot`. A higher-resolution / CRT trial was an experiment only.

### 12.2 `BattleCamera.gd`

**🤖 MCP creates** `scripts/BattleCamera.gd` — attached to Camera3D.

The sketch below is the prototype chase cam. "Behind both cars" is not the locked view; §12.1 is.

```gdscript
# During STRAIGHT (prototype sketch — locked view is §12.1, fixed on the player):
#   - Rear third-person on the player, looking down the straight
#   - FOV ~65°, slight vertical tilt for speed feel
# During CORNER_PLAYBACK:
#   - Rotate ~15° around Y axis into corner direction
#   - FOV ~55°, closer to cars
#   - Subtle X roll to follow road camber
# During DAMAGE_BATCH:
#   - Hold same position as corner

func transition_to_corner(corner_direction: String)
    # If "left":  target_pos = origin + Vector3(-3, 0.5, 1)
    # If "right": target_pos = origin + Vector3(3, 0.5, 1)
    # Tween over 1.0s (ease-in-out)

func transition_to_straight()
    # Tween back to default chase cam position over 1.0s

func swing_overtake()
    # Brief camera shift (0.3s) to emphasize overtake during exit
```

---

## 13. Corner Cinematic

**Goal:** Turn the abstract clash into a visual corner playback with segment-based rendering.

### 13.1 Segment-based rendering

No continuous track. Each turn is a self-contained straight approach + corner segment. Previous segment unloaded, next segment loaded between turns (Initial D: Another Stage style).

| Game state | Visible road | Car positioning | Camera |
|---|---|---|---|
| LOAD_SEGMENT | (loading) | — | — |
| STRAIGHT | StraightRoad | Drawn spacing follows the visual-gap rule in 06 (not a 1:1 DP offset; prototype `snap_to_gap` is still symmetric) | Fixed rear third-person on the player |
| CORNER_PLAYBACK | CornerRoad | Pathing along Curve3D | Authored camera path |
| DAMAGE_BATCH | CornerRoad | Static at corner exit | Same as corner |
| END_TURN | (unload) | Snap back to straight Z | Swing back to chase cam |

### 13.2 Corner playback flow

```
1. Load corner segment (straight + corner meshes + camera path + car Path3D)
2. emit corner_started(player_stances, opponent_stances)
3. QTEController.start(qte_type)         ← runs through all 3 phases
4. RESOLVE_ENTRY → clash anim (~1.5s, QTE active) + CarAnimator.surge/drop
5. RESOLVE_APEX  → clash anim (~1.5s, QTE active) + CarAnimator.surge/drop
6. RESOLVE_EXIT  → position-based exit anim (~1.5s, QTE active) + CarAnimator.surge/drop
7. QTEController.stop() → qte_score
8. Damage computed from all 3 phases → DP gap resolved
9. Lead change check:
   a. If leader changed → play overtake animation (0.5-1s) + camera.swing_overtake()
   b. If unchanged → skip
10. emit corner_ended(qte_score)
11. Unload corner segment
```

### 13.3 Per turn-type camera choreography

Each turn type has an authored camera motion path — a Path3D the camera follows:

| Turn Type | Camera feel |
|-----------|-------------|
| Hairpin | Tight inside-line view |
| Sweeper | Wide tracking shot |
| Chicane | Side-angle for S-motion |
| Esses | Flowing follow-cam |
| 90-Degree | Sharp cut to apex |

---

## 14. Scene Management + Road FX

### 14.1 `StageManager.gd` (autoload)

**🤖 MCP creates** `scripts/StageManager.gd`:

```gdscript
func load_battle(config: MatchConfig)
    # Transition to Battle.tscn, pass config

func load_menu()
    # For future: load Menu scene

func load_results(result: MatchResult)
    # For future: show results overlay or scene
```

For v1: `load_battle()` is the primary entry point.

### 14.2 `RoadScroller.gd`

**🤖 MCP creates** `scripts/RoadScroller.gd` — UV-offset parallax to simulate speed.

```gdscript
extends ShaderMaterial

var scroll_speed: float = 0.05

func start_scrolling()
    # Begin incrementing UV offset each frame

func stop_scrolling()
    # Pause UV offset

func set_speed(factor: float)
    # Adjust for drama: faster during straight, slower during corner

func _process(delta):
    # uv_offset += scroll_speed × delta
    # Apply to road mesh material

func transition_to_corner()
    # Brief speed burst + decel as cars approach the bend
    set_speed(1.5) → wait 0.5s → set_speed(0.6)
```

Applied as `ShaderMaterial` on both road segments. The same UV-offset drives both straight and corner textures.

### 14.3 Corner segment lifecycle

```
1. END_TURN: unload previous corner segment
2. Load next corner segment (straight + corner + cam path + car path)
3. STRAIGHT: show straight mesh, cars at starting Z positions
4. CORNER_PLAYBACK: hide straight, show corner mesh, cars traverse Path3D
5. All 3 phases resolve → damage computed → overtake if applicable
6. Unload corner segment, loop
```

---

## 15. Tuning Loop

**Goal:** Play matches → adjust constants → play again. This is the whole point.

### 15.1 How to run

1. Open `Battle.tscn` in Godot, press **F5**
2. Match starts automatically (uses a default `MatchConfig`)
3. Pick 3 stances across 3 phases (entry → apex → exit)
4. Complete the QTE (mash or timing)
5. Watch DP bars + cubes update
6. Match ends at `max_turns` → winner displayed
7. Edit constants in `globals.gd` → **F5** to rerun

### 15.2 Quick-tune constants

| Constant | Effect | Recommended range |
|----------|--------|-------------------|
| `CLASH_STAKES` | How much each clash win/loss matters | 0.25 – 0.45 |
| `BATTLE_BONUS` | How much winning the battle amplifies damage | 0.03 – 0.10 |
| `MITIGATION_PER_1000` | How effective EN is per 1000 | 0.30 – 0.50 |
| `MITIGATION_FLOOR` | Minimum damage always dealt | 0.05 – 0.20 |
| `HP_PER_LEVEL` | HP per level (turns length) | 150 – 200 |
| `STRAIGHT_DURATION` | Seconds to pick 3 stances | 8.0 – 12.0 |
| `QTE_TIMING_WINDOW_BASE_MS` | Base timing target width | 600 – 1000 |
| `DECK_ALPHA` | Deck smoothing (higher = more even) | 0.70 – 0.95 |
| `RUBBER_BAND_PCT` | QTE comeback threshold | 0.10 – 0.25 |

### 15.3 Tuning flow

1. **Run vs Wild** (level gap favors you) — should feel dominant but not boring
2. **Run vs Lieutenant** (near parity) — should feel tense, each pick matters
3. **Run vs Boss** (level gap favors them) — should feel like an uphill fight
4. **Adjust** any constant that makes a matchup feel wrong
5. **Rerun** — no restart needed, just F5

### 15.4 Adding real art later

When gameplay is tuned to your liking:

1. Replace `PlayerCube` / `OpponentCube` BoxMesh with imported car `.glb`
2. Replace ground plane with road meshes (straight + corner variants)
3. Replace `TextureProgress` bars and `Button` textures with styled assets
4. Add corner cinematic (Path3D traversal, camera choreography)
5. Import face textures and wire into FaceStack TextureRects
6. The gameplay scripts (`Deck.gd`, `CombatResolver.gd`, `TurnManager.gd`, etc.) need zero changes

### 15.5 Edge cases

- **Tiebreaker:** opponent wins on equal position (enforced in TurnManager)
- **Empty deck:** player deck runs out of cards mid-match → draw returns fewer
- **Rapid clicking:** CardHandUI disables buttons between phases
- **Timer precision:** StraightTimer uses `delta` accumulation, not frame count

### 15.6 Deferred

- Sound / music — design signal hooks for future audio integration
- Skill trees — not in v1
- Mods system — separate design doc
- Menu → Overworld → Race flow — StageManager stubs exist
- Full face texture assets — placeholders until art pass

---

## Appendix A: File Manifest

**🤖 MCP creates:**

```
project.godot

scripts/
  globals.gd               — enums + constants
  SignalBus.gd             — 12 signals
  CombatantStats.gd        — resource
  MatchConfig.gd           — resource
  Deck.gd                  — 192-card stat-proportional
  StraightTimer.gd         — 12s, 3 phases
  CardHandUI.gd            — 3 buttons + counts
  CombatResolver.gd        — pure math
  TurnManager.gd           — state machine
  QTEController.gd         — mash + timing
  AIPicker.gd              — EV scoring
  AIQTE.gd                 — opponent QTE generation
  TurnTypeData.gd          — stance sequences + QTE type
  ArchetypeData.gd         — comfort/weak zones
  PersonalityData.gd       — 5 personalities, 3 phases each
  TrackData.gd             — circuit layouts
  TellGenerator.gd         — deception flow
  FaceController.gd        — face display + tell overlay
  PositionTracker.gd       — cumulative DP
  DamageDisplay.gd         — DP bar tweens
  ClashDisplay.gd          — 2×3 stance grid
  PhaseAnnouncer.gd        — lap boundaries
  CarAnimator.gd           — Z-offset + path traversal
  AnimationTreeBlendManager.gd — stance blend + face crossfade
  BattleCamera.gd          — chase cam + transitions
  StageManager.gd          — scene loading (autoload)
  RoadScroller.gd          — UV-offset parallax

scenes/
  Battle.tscn              — full node hierarchy
```

Total: **24 script files + 1 scene file**

---

## Appendix B: Turn Flow Reference

```
[STRAIGHT — 12s REAL TIME]
  Prototype flow (scripts unchanged). Locked tell is lane Entry under the
  visual-gap rule in design/06-pattern-read.md: 3 cards lock up front,
  Apex/Exit are inferred (Touge/Wangan/Street map still TBD; the old
  archetype rows are not that map), and a rival ahead of the player is drawn only as
  far as that lane stays readable. A rival behind recedes in the mirror.
  Car drives toward the corner. The rival shows lane Entry (not a separate Apex or Exit tell).
  Three opponent faces reveal SEQUENTIALLY with smooth crossfade
  (earlier face draft, not an Apex/Exit tell):
    0s-4s:   ENTRY face shown + tell (if deceptive)
             Player picks entry stance
    4s-8s:   Face crossfades to APEX expression
             Player picks apex stance
    8s-12s:  Face crossfades to EXIT expression
             Player picks exit stance
  Each pick has 4s window; auto-pick on expire.

[CARS ENTER CORNER — SEGMENT-BASED CINEMATIC]
  All 3 stances locked in. Corner segment plays out:
    1. RESOLVE_ENTRY → clash anim (~1.5s, QTE active)
    2. RESOLVE_APEX  → clash anim (~1.5s, QTE active)
    3. RESOLVE_EXIT  → position-based anim (~1.5s, QTE active)

  [CONTINUOUS QTE runs through all 3 phases]

[CORNER EXIT]
  QTE stops. Damage computed from all 3 phases → DP gap resolved
  Lead change check:
    - If changed → overtake animation (0.5-1s) + camera swing
    - If unchanged → skip
  DP bars update → position label updates
  Car positions tween. Drawn spacing follows the visual-gap rule, not the raw DP magnitude
  → Unload corner segment
  → DECK DISCARD / DRAW for next turn
  → Load next corner segment
  → Loop back to STRAIGHT (next corner)
```

### Mapping to Python reference

| Phase | Python equivalent |
|-------|-------------------|
| Straight (12s) | No equivalent — pure Godot UX |
| 3× CARD_PICK | `match.py` sequential pick loop (on straight) |
| 3× CLASH resolve | `equations.resolve_stance()` (in corner, batched) |
| 1× QTE (corner-long) | `cli.prompt_qte()` → `combat.py` QTE split |
| DAMAGE batch | `combat.resolve_turn()` (all 3 averaged) |
| DECK draw/discard | `deck.py` draw + end_turn |

---

## Appendix C: Signals Reference

All signals on `SignalBus` autoload singleton.

| Signal | Payload | Emitter | Fires When |
|--------|---------|---------|------------|
| `match_started(cfg: MatchConfig)` | `MatchConfig` | StageManager | Battle scene ready |
| `straight_started(turn, turn_type, entry_stance, apex_stance, exit_stance, is_deceptive)` | `int, String, int×3, Array[bool]` | TurnManager | Straight begins |
| `phase_pick(phase_index, phase_name)` | `int, String` | TurnManager | 0/entry, 1/apex, 2/exit |
| `card_selected(stance: int)` | `Stance` | CardHandUI | Player clicks stance button |
| `phase_pick_timeout(phase_index)` | `int` | StraightTimer | Per-pick sub-timer expired |
| `corner_started(player_stances, opponent_stances)` | `Array[int]×2` | TurnManager | Corner playback begins, QTE starts |
| `clash_resolved(position, player_stance, opponent_stance, outcome)` | `int×4` | TurnManager | Per-clash resolution done |
| `corner_ended(qte_score)` | `float` | TurnManager | All 3 clashes + QTE complete |
| `damage_batch_done(player_dp, opponent_dp, cum_player, cum_opponent, battle_mult)` | `float×5` | TurnManager | Damage computed, bars start animating |
| `turn_ended(turn)` | `int` | TurnManager | Deck cycled, ready for next straight |
| `lap_began(phase, total)` | `int, int` | TurnManager | Phase boundary crossed |
| `match_ended(winner, player_name, opponent_name)` | `String×3` | TurnManager | Max turns reached |

---

## Appendix D: Full Data Flow

```
BEFORE TURN: TurnManager reads TrackData for current turn_type
  → Set TurnTypeLabel
  → Set corner_blend (left/right) on AnimationTreeBlendManager
  → Look up opponent's entry/apex/exit stances from TurnTypeData
  → TellGenerator: deception check per position → 3 (stance, is_bluff) tuples
  → FaceController: load target textures for all 3 positions

1. TurnManager: state = STRAIGHT (12s)
     → Deck: draw 6, compute stance counts → CardHandUI: update button labels
     → StraightTimer: start 12s countdown
     → emit straight_started(...)
     → AnimationTreeBlendManager: begin stance_blend cycle
       (0-4s: entry_weight, 4-8s: apex_weight, 8-12s: exit_weight)
     → FaceStack: alpha crossfade follows same schedule

2. PICK_ENTRY (0-4s)
     → emit phase_pick(0, "ENTRY")
     → CardHandUI: enable buttons with count > 0
     a. Player clicks → emit card_selected(stance) → store
     b. OR 4s expires → emit phase_pick_timeout(0) → auto-pick → store
     → CardHandUI: disable, grey out consumed count
     → PhasePromptLabel: "APEX — Pick your stance"

3. PICK_APEX (4-8s)
     → same flow as ENTRY

4. PICK_EXIT (8-12s)
     → same flow as ENTRY

5. StraightTimer emits straight_complete
     → AIPicker: select opponent's 3 cards

6. TurnManager: state = CORNER_PLAYBACK
     → compute qte_difficulty = QTEController.qte_difficulty(player.level, opponent.level)
     → emit corner_started(player_stances, opponent_stances)
      → QTEController.start(qte_type, qte_difficulty)
      → ClashDisplay.display_summary(player_stances, opponent_stances)
      → Loop through 3 positions:
          CombatResolver.resolve_stance(player, opponent)
          → emit clash_resolved(...)
          → ClashDisplay.reveal_phase(position)
          → CarAnimator.play_surge() or play_drop()
     → QTEController.stop() → qte_score
     → emit corner_ended(qte_score)

7. TurnManager: state = DAMAGE_BATCH
     → CombatResolver: compute 3× DP, average, mitigate, battle_mult
     → HAN modifier applied to QTE scores
     → Rubber-band QTE split applied
     → PositionTracker: accumulate
     → CarAnimator: tween Z offsets to new gap
     → DamageDisplay: animate bars
     → emit damage_batch_done(...)

8. TurnManager: state = END_TURN
     → Deck.end_turn(played, unpicked)
     → Check lap boundary → emit lap_began(...)
     → If turns < max_turns → STRAIGHT
     → If turns >= max_turns → emit match_ended(...)
```

---

## Appendix E: Art Asset Checklist

### 3D Assets (human — Blender)

| Asset | Count | Notes |
|-------|-------|-------|
| Car body mesh | 1 | Low-poly PS1-style, shared by both cars |
| Player livery material | 1 | `.tres` + `.png` texture |
| Opponent livery material | 1 | `.tres` + `.png` texture |
| `corner_right` animation | 1 | glTF |
| `corner_left` animation | 1 | glTF |
| `pose_attack` animation | 1 | glTF |
| `pose_defend` animation | 1 | glTF |
| `pose_steady` animation | 1 | glTF |
| `surge_ahead` animation | 1 | glTF (0.3s) |
| `drop_back` animation | 1 | glTF (0.3s) |
| `road_straight` mesh | 1 | Long straight plane with lane markings (~30 units) |
| `road_corner_left` mesh | 1 | Curved plane arc left, same lane layout |
| `road_corner_right` mesh | 1 | Curved plane arc right, mirror of left |
| `barrier_straight` mesh | 2 | Road-edge barrier wall segment (straight) |
| `barrier_corner_left` mesh | 2 | Road-edge barrier wall following left curve |
| `barrier_corner_right` mesh | 2 | Road-edge barrier wall following right curve |
| Track texture | 1 | `.png` tiling road surface (shared UV across all segments) |
| Skybox | 1 cubemap | 6× `.png` or 1 equirect |

### Face Assets (human — Aseprite/Photoshop)

9 face portraits + 9 tell overlays (see Step 9 for expression reference):

| File | Subject |
|------|---------|
| `face_scowling_atk.png`, `face_scowling_def.png`, `face_scowling_neu.png` | Aggressive expressions |
| `face_grinning_atk.png`, `face_grinning_def.png`, `face_grinning_neu.png` | Defensive and Balanced expressions |
| `face_focused_atk.png`, `face_focused_def.png`, `face_focused_neu.png` | Precise and Adaptive expressions |
| `tell_scowling_atk.png`, `tell_scowling_def.png`, `tell_scowling_neu.png` | Aggressive tells |
| `tell_grinning_atk.png`, `tell_grinning_def.png`, `tell_grinning_neu.png` | Defensive and Balanced tells |
| `tell_focused_atk.png`, `tell_focused_def.png`, `tell_focused_neu.png` | Precise and Adaptive tells |

### UI Assets (human — Aseprite/Photoshop)

| Files | Count |
|-------|-------|
| Button idle/pressed (ATK, DEF, STEADY) | 6 |
| Panel backgrounds (9-slice) | 4 |
| Timer bar fills (straight, QTE mash) | 2 |
| QTE indicator (timing marker, timing target) | 2 |
| Outcome icons (WIN, LOSS, TIE) | 3 |
| Position icons (1st, 2nd) | 2 |
| DP bar fills (player, opponent) | 2 |
| Font | 1 `.ttf`/`.otf` |

---

## Appendix F: QTE Type Lookup + Difficulty Formula

One continuous QTE per corner. Type determined by `(turn_type × player stance)`.

| Turn Type | ATTACK | DEFEND | STEADY |
|-----------|--------|--------|--------|
| Hairpin | MASH | TIMING | TIMING |
| Constant Radius | TIMING | MASH | MASH |
| Decreasing Radius | MASH | TIMING | MASH |
| Increasing Radius | TIMING | MASH | TIMING |
| 90-Degree | MASH | TIMING | MASH |
| Chicane | TIMING | MASH | MASH |
| Esses | MASH | TIMING | TIMING |
| Sweeper | TIMING | MASH | TIMING |

### Mash mode (continuous)
- Rapid button press (input map: `qte_mash`)
- Fill bar builds during corner playback (~3-4s)
- Final score = fill % × 10, normalized 1–10
- **Difficulty scaling:** `speed_multiplier` adjusts how fast the fill bar depletes between presses — at 1.5×, you must press 50% faster to maintain the same fill rate.

### Timing mode (continuous)
- Moving marker oscillates across a target zone
- Timer ticks down; multiple successful presses increase score
- Final score = (successful_presses / total_opportunities × 10)
- **Difficulty scaling:** `timing_window_ms` sets the width of the target zone — at 800ms the zone is generous, at 200ms you must nail the frame. Both the window size and the marker oscillation speed scale with the gap.

### Difficulty formula

```gdscript
gap = opponent_level - player_level
timing_window_ms = max(QTE_TIMING_WINDOW_MIN_MS,
                       QTE_TIMING_WINDOW_BASE_MS - gap × QTE_TIMING_WINDOW_PER_GAP)
speed_multiplier = 1.0 + max(0, gap) × QTE_MASH_SPEED_PER_GAP
```

| gap | timing_window_ms | speed_multiplier | feel |
|-----|-----------------|-----------------|------|
| -10 | 800 (capped) | 1.0 | Player dominates — no bonus |
| 0 | 800 | 1.0 | Even match — base difficulty |
| +3 | 650 | 1.30 | Opponent fav — tighter timing |
| +6 | 500 | 1.60 | Tough — zone shrinks, mash races |
| +10 | 300 | 2.00 | Max before soft floor at 200ms |

---

## Appendix G: AI Stance Lookup

For each corner, the opponent's 3 stances come from the district line table, `LINE_SET_C[district][corner]` in `sim/velocity_shift/equations.py` (mirrored in `scripts/globals.gd`, read through `TurnTypeData.pick_line()`). The district is the race's `district_id`, and the corner code comes from `TrackData`. The locked car tell is lane Entry only (`design/06-pattern-read.md`), which is why every alternate shares main's Entry.

```
# Street race, corner N90:
lines  = LINE_SET_C["street"]["N90"]      # [main, alt1, alt2]
a       = LINE_ADHERENCE
weights = [a, (1 - a) * LINE_ALT_WEIGHTS["alt1"], (1 - a) * LINE_ALT_WEIGHTS["alt2"]]
line    = lines[rng.rand_weighted(weights)]   # one draw per corner, played exactly
stances = [line[0], line[1], line[2]]     # Entry, Apex, Exit (D/S/A)
```

Make the draw from the match `RandomNumberGenerator` so a playtest dump's Block C seed and RNG state reproduce the opponent's picks in Godot. Godot's generator isn't Python's, so this matches the sim's line rates, not its exact rolls.

## Appendix H: Notes / Gotchas

- **Stance naming:** UI displays "STEADY" but the enum is `Stance.NEUTRAL`. Button label and all UI text uses "STEADY"; all logic uses NEUTRAL.
- **Deck size:** 192 cards. Draw 6, pick 3, discard 3.
- **Opponent deck:** reshuffles each turn (player deck uses discard pile).
- **HP_PER_LEVEL = 180**, not 120.
- **No DNF / knockout** — match always runs to max_turns, then position decides.
- **Tiebreaker:** opponent wins on equal position.
- **Rubber-band threshold:** 15% of average max HP.
- **Car position in 3D:** drawn spacing only. Cumulative DP, position, and the win condition stay on the real gap (`design/06-pattern-read.md`, Lane Entry and visual gap). A capped lead ahead of the player is not the exact large-lead magnitude. The trailer is not given a matching cap. `CarAnimator.gd` still uses a symmetric Z lerp; that code was not updated with the rule.
- **AnimationTree blend:** 7 animations + 3-way blend node = smooth stance transitions for any 3-stance sequence. No per-combination baking.
- **Face crossfade:** 3 stacked TextureRects with alpha driven by same blend schedule as the car. 4th overlay layer for bluff tell.
- **Meta-archetypes:** 3 face types (Scowling/Grinning/Focused) shared by hard+soft pairs. 9 face textures + 9 tell overlays total.
- **Future screens:** Menu → Isometric Overworld → Race → Battle → Results → Overworld. Design scene loading (StageManager) with this in mind.
- **Skill points are in v1** (see 08); the tree layout is still undecided. Mods system design is separate.
- **Sound/music:** deferred. Design signal hooks for future audio integration.
