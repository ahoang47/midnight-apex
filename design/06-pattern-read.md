# Opponent pattern telegraphing 

**General rules:**
- **Lane Entry is the car tell** (locked 2026-11-06; full rule in the next section). Relative to the next corner, outside = Attack, center = Steady, inside = Defend. Entry can bluff by sitting in the wrong lane. Apex and Exit are inferred, not shown.
- An earlier draft put the opponent's face in one corner and the upcoming turn in another, and had the face telegraph the next choice. That face is not the live tell.
- **Track layouts are fixed per circuit** — authored, not randomized. Shared Touge, Wangan, and Street tendencies are the intended specialization habits for inferring Apex and Exit. The precise habits, and any race-state-dependent Apex/Exit mapping, are still TBD. The Aggressive, Defensive, and Precise rows later in this doc are a historical draft, not that source.
- The face palettes, lie-rate table, weaving channel, and suspension channel below are an earlier draft. They are not the live read. A face does not telegraph Apex or Exit, and there is no separate Apex/Exit bluff.
---

## Lane Entry and visual gap (locked 2026-11-06)

Austin locked this. It is how the rival is drawn and how Entry is read. It does not change combat math.

**Line lock.** The player locks all 3 cards, the line, up front, before corner playback.

**Lane Entry**, relative to the next corner:

| Lane | Stance |
|------|--------|
| Outside | Attack |
| Center | Steady |
| Inside | Defend |

Entry can bluff by improper placement: the car is shown in a lane that is not the stance it will play. No probability for that bluff was set here.

**Apex and Exit** have no explicit tell and no extra bluff layer. They are inferred, not shown. The intended inputs are the Entry read, shared Touge, Wangan, and Street tendencies, the corner's geometry, and the real lead/gap at the start of selection. Those district tendencies, and the race-state-dependent Apex/Exit mapping, are not defined yet. No habit table and no probability is added here. The Aggressive, Defensive, and Precise rows below are an older unreconciled draft. They are not those specializations and not the adopted source of actual Apex or Exit. Corner-description notes in those rows (late braking, a long single apex, a delayed apex, an early apex, and the other turn writeups) are illustrative earlier examples, not an approved stance map.

**Asymmetric visual gap.** Cumulative DP, position, and the win condition stay on the real gap. The spacing below is only how far apart the cars are drawn. It is not a cap on the real gap, not an AI change, not a damage change, and not a change to the mathematical rubber band (`RUBBER_BAND_FRACTION` in `sim/velocity_shift/equations.py`).

- When the **player is behind**, cap how far ahead the rival is drawn so the rival's lane and Entry stay readable from the fixed rear third-person camera on the player. No distance number is approved. Readability tests set it later. Because that drawn lead is capped, visible spacing does not show the exact size of a large real lead.
- When the **player is ahead**, the trailing rival recedes in the top-center rear-view mirror. Distance makes the headlights and the lane harder to read, so the leader gets less Entry information. That is an intentional, in-world catch-up in information. It is not a readability bug. Do not undo it with a HUD lane marker, by enlarging the lamps, or with a cap on how far behind the rival is drawn.

The race camera stays on the player. It does not sit behind whichever car is leading, and it does not zoom out to keep an uncapped leader in frame.

---

## Deception mechanics

> **Earlier face draft, not the live Entry bluff.** The live bluff is improper lane placement, in the locked section above. Nothing below sets a probability for that. Clash-position lie rates that spread onto Apex and Exit are not an Apex/Exit tell or a second bluff layer.

Four systems govern how reliable the opponent's face is in this earlier draft. Each scales independently by tier and encounter type.

### 1. Lie rate
The probability that any given face does **not** match the AI's actual pick for that clash slot. Ranges from 0% (always truthful) to 100% (always lying).

### 2. Clash-position weighting
Deception is not uniform across all 3 clashes. At lower levels it only affects the entry (pos 0). As tiers increase it spreads to apex (pos 1) and eventually exit (pos 2). This lets players learn partial trust patterns — e.g., "the exit face is always true." Clash-position weighting will be archetype dependent - that's to say that some archetypes could always bluff on apex. 

---

## Turn type system

> **Historical draft, not the district map.** These Aggressive, Defensive, and Precise rows are an older unreconciled draft. They are not the adopted source of actual Apex or Exit. Shared Touge, Wangan, and Street tendencies are intended, and the precise mapping is still TBD. The description notes (late braking, a long single apex, a delayed apex, an early apex, and the other turn writeups) are illustrative earlier examples, not an approved stance map. The Entry/Bluff, Apex/Bluff, and Exit/Bluff columns are the earlier face draft, not the live Entry bluff (improper lane placement) and not an Apex/Exit tell. No cell was added or changed.

All turn types have left and right variants. No turn type may repeat more than twice consecutively in the track layout, regardless of direction.

In this historical draft, each turn type lists a 3-stance sequence per archetype. That listing is not the approved Touge, Wangan, or Street mapping:

- **Entry (pos 0):** braking/turn-in phase 
- **Apex (pos 1):** the defining moment of the corner 
- **Exit (pos 2):** power/acceleration 

### Aggressive (POW)

| Turn Type | Description | Entry/Bluff | Apex/Bluff | Exit/Bluff | must not appear before | must not appear after |
|---|---|---|---|---|---|---|
| Hairpins | Extremely tight, U-shaped corners requiring heavy, late braking and a near 180-degree turnaround. | DEF/ATK | DEF/ATK | ATK/NEU | N/A | N/A |
| Constant Radius (Circular) | These turns have an even arc and a single, long consistent apex. | DEF/ATK | ATK/NEU | ATK/NEU | Constant Radius | Constant Radius |
| Decreasing Radius | Corners that tighten as you go through them. They require a delayed, late apex, as getting on the throttle too early forces the car wide on corner exit. | DEF/ATK | DEF/ATK | NEU/DEF | Increasing Radius | N/A |
| Increasing Radius | Corners that open up as you exit. Drivers typically use an early apex to get on the power much sooner. | DEF/ATK | ATK/NEU | ATK/NEU | N/A | Decreasing Radius |
| 90-Degree Corners | Literal right-angle turns that require pointing the car quickly through a sharp turn. | DEF/ATK | DEF/ATK | ATK/NEU | N/A | N/A |
| Chicanes | Tight, alternating sequences of turns (often left-right or right-left). They are inserted into high-speed straights to slow cars down to improve safety and promote overtaking opportunities. | DEF/ATK | DEF/ATK | ATK/NEU | N/A | N/A |
| Esses (S-Bends) | A flowing sequence of continuous, alternating curves. Getting the first turn correct in a sequence is crucial, as a mistake ruins the line for the rest. | DEF/ATK | DEF/ATK | ATK/NEU | Chicanes | Chicanes |
| Sweepers | Long, fast, gradual turns where drivers hold a consistent, high-speed arc for a prolonged time. | DEF/ATK | ATK/NEU | ATK/NEU | N/A | N/A |

### Defensive (EN)

| Turn Type | Description | Entry/Bluff | Apex/Bluff | Exit/Bluff | must not appear before | must not appear after |
|---|---|---|---|---|---|---|
| Hairpins | Extremely tight, U-shaped corners requiring heavy, late braking and a near 180-degree turnaround. | NEU/ATK | ATK/DEF | ATK/DEF | N/A | N/A |
| Constant Radius (Circular) | These turns have an even arc and a single, long consistent apex. | NEU/ATK | DEF/NEU | NEU/ATK | Constant Radius | Constant Radius |
| Decreasing Radius | Corners that tighten as you go through them. They require a delayed, late apex, as getting on the throttle too early forces the car wide on corner exit. | NEU/ATK | ATK/DEF | NEU/ATK | Increasing Radius | N/A |
| Increasing Radius | Corners that open up as you exit. Drivers typically use an early apex to get on the power much sooner. | NEU/ATK | DEF/NEU | ATK/DEF | N/A | Decreasing Radius |
| 90-Degree Corners | Literal right-angle turns that require pointing the car quickly through a sharp turn. | NEU/ATK | NEU/ATK | ATK/DEF | N/A | N/A |
| Chicanes | Tight, alternating sequences of turns (often left-right or right-left). They are inserted into high-speed straights to slow cars down to improve safety and promote overtaking opportunities. | NEU/ATK | ATK/DEF | NEU/ATK | N/A | N/A |
| Esses (S-Bends) | A flowing sequence of continuous, alternating curves. Getting the first turn correct in a sequence is crucial, as a mistake ruins the line for the rest. | NEU/ATK | NEU/ATK | NEU/ATK | Chicanes | Chicanes |
| Sweepers | Long, fast, gradual turns where drivers hold a consistent, high-speed arc for a prolonged time. | NEU/ATK | DEF/NEU | NEU/ATK | N/A | N/A |

### Precise (HAN)

| Turn Type | Description | Entry/Bluff | Apex/Bluff | Exit/Bluff | must not appear before | must not appear after |
|---|---|---|---|---|---|---|
| Hairpins | Extremely tight, U-shaped corners requiring heavy, late braking and a near 180-degree turnaround. | DEF/ATK | NEU/DEF | ATK/NEU | N/A | N/A |
| Constant Radius (Circular) | These turns have an even arc and a single, long consistent apex. | NEU/DEF | NEU/DEF | ATK/NEU | Constant Radius | Constant Radius |
| Decreasing Radius | Corners that tighten as you go through them. They require a delayed, late apex, as getting on the throttle too early forces the car wide on corner exit. | DEF/ATK | NEU/DEF | ATK/NEU | Increasing Radius | N/A |
| Increasing Radius | Corners that open up as you exit. Drivers typically use an early apex to get on the power much sooner. | DEF/ATK | NEU/DEF | ATK/NEU | N/A | Decreasing Radius |
| 90-Degree Corners | Literal right-angle turns that require pointing the car quickly through a sharp turn. | DEF/ATK | ATK/NEU | ATK/NEU | N/A | N/A |
| Chicanes | Tight, alternating sequences of turns (often left-right or right-left). They are inserted into high-speed straights to slow cars down to improve safety and promote overtaking opportunities. | DEF/ATK | NEU/DEF | ATK/NEU | N/A | N/A |
| Esses (S-Bends) | A flowing sequence of continuous, alternating curves. Getting the first turn correct in a sequence is crucial, as a mistake ruins the line for the rest. | NEU/DEF | ATK/NEU | ATK/NEU | Chicanes | Chicanes |
| Sweepers | Long, fast, gradual turns where drivers hold a consistent, high-speed arc for a prolonged time. | DEF/ATK | NEU/DEF | ATK/NEU | N/A | N/A |

> **Balanced** and **Adaptive** share the same 3-stance sequences as Defensive and Precise respectively.

- Each match generates a **track layout**: a predetermined 10-turn sequence. A single turn type drives all 3 clashes — the entry/apex/exit lookup within the turn type provides the per-position stance.

---

## Tell system

### Face types

Each face type is a cohesive expression palette — one expression per stance. Every archetype is assigned one face type. When deceptive, a **bluff tell** (listed alongside each expression above) is embedded. Perceptibility is gated by intensity: at level 5 it's obvious, at level 1 it's nearly invisible.

| Face Type | ATK expression | ATK tell | DEF expression | DEF tell | NEU expression | NEU tell |
|-----------|---------------|----------|----------------|----------|----------------|----------|
| A — Scowling (POW) | Bared teeth, furrowed brow | Mouth closes over bared teeth briefly | Tight jaw, narrowed eyes | Eyes flick wide then narrow back | Flat stare, relaxed brow | Brow drops and returns |
| B — Grinning (EN) | Wide smile, raised brows | Raised brows drop flat | Thin smile, watchful eyes | Eyes shift to the side | Half-smirk, steady gaze | Half-smirk goes straight |
| F — Focused (HAN) | Intense stare, sharp focus | Intense gaze loses focus, drifts | Cocky smirk, raised brow | Raised brow drops flat | Relaxed half-smile | Half-smile vanishes |

### Archetype reference

> Same historical draft as the stance rows above. Not the Touge, Wangan, or Street tendencies, and not an approved bluff map.

Each archetype has **2 comfortable** turn types (double the normal bluff rate) and **2 weak** turn types (never bluff here).

| Archetype | Face type | Comfortable (2× bluff rate) | Weak (never bluffs) |
|-----------|-----------|----------------------------|---------------------|
| Aggressive (POW) | A — Scowling | Sweepers, Increasing Radius | Hairpins, Decreasing Radius |
| Defensive (EN) | B — Grinning | Constant Radius, Sweepers | Chicanes, Esses (S-Bends) |
| Balanced | B — Grinning | Constant Radius, Sweepers | Chicanes, Esses (S-Bends) |
| Precise (HAN) | F — Focused | Chicanes, Esses (S-Bends) | Sweepers, Hairpins |
| Adaptive | F — Focused | Chicanes, Esses (S-Bends) | Sweepers, Hairpins |

### Car motion types

> **Not the current tell.** The live car read is lane Entry (outside / center / inside) under the visual-gap rule above. The weaving patterns, suspension poses, and apex bluffs in this section are the earlier draft. Do not implement them as tells, and do not treat them as the bluff layer for Entry.

Each stance has a 2-channel visual language in that earlier draft, both playing simultaneously on the straightaway approach before corner entry. Opponents also have a **bluff** variant — the car looks like one stance but the opponent is actually playing another. All archetypes share this.

#### Channel 1 — Track position (entry / pos 0 tell)

The opponent constantly maneuvers left and right on the straightaway. The **bias within that movement** telegraphs stance:

| Stance | Movement pattern | Visual |
|--------|----------------|--------|
| **Attack** | Biases toward outside | Weaving drifts progressively wider between corrections; spends more time on the outside edge; corrections are aggressive flicks |
| **Defend** | Covers full width | Full-range lateral movement; shifts unpredictably to block; erratic amplitude; no sustained center tendency |
| **Steady** | Centers around middle | Narrow-band weaving; small, smooth corrections around the ideal line; no sustained drift to either edge |

##### Entry bluffs

**Attack bluff** (looks attack-biased, actually defend/steady):
- Weaves wide but the corrections are soft, not committed
- Returns to center too quickly after each wide excursion
- No tension in the wide-side suspension

**Defend bluff** (looks defensive weaving, actually attack):
- Wide-range weaving follows a rhythm — setting up a switchback
- Consistently leaves a specific gap open on one side — bait
- Corrections are snappier than true defense

**Steady bluff** (looks steady, actually attack/defend):
- Attack variant: small corrections but each one edges slightly wider; RPMs build
- Defend variant: small corrections but brake light patterns flicker — setting up to block
- Hardest to read — the difference is in micro-trends over the 4s window

#### Channel 2 — Suspension loading (apex / pos 1 tell)

| Stance | Suspension | Visual |
|--------|------------|--------|
| **Attack** | Rear squats | Weight transfers rearward under braking — loading power for exit; nose lifts slightly; car looks poised to spring |
| **Defend** | Front dives | Weight shifts forward — braking hard to rotate car; nose dips, car settles into a defensive posture |
| **Steady** | Flat / balanced | Neutral weight distribution; composed braking attitude; no exaggerated pitch |

##### Apex bluffs

**Attack bluff** (rear squat but actually defend/steady):
- Rear squats but steering correction follows — the load-up has no commitment
- Car doesn't carry the rotation; stays pointed straight

**Defend bluff** (front dive but actually attack):
- Front dive but RPMs are climbing — settling weight not to slow, but to launch
- Brake lights flick off early

**Steady bluff** (balanced but actually attack/defend):
- Attack: micro rear squat under apparent calm — tiny pitch change betrays power loading
- Defend: micro front dive — a brake pulse masked as a gear shift

Exit (pos 2) in this earlier draft reflects **position**, not stance. By exit, QTE is done and the DP gap is resolved. The leading car powers away with a clean exit; the trailing car struggles or defends. If the lead changed this turn, a short overtake animation plays after exit (car moves from behind to ahead). That playback is not an Exit tell. Drawn spacing still follows the locked visual-gap rule: a rival ahead of the player is not left so far up the road that lane and Entry cannot be read, and a rival behind is not held at a matching distance. The on-screen gap is not the real DP lead.

Exit also feeds forward: the exit stance plus the next turn's type determines which entry stances are locked out next turn (see the lockout tables in `03-deckbuilding-clash.md`). That lockout is a play rule, not a visual tell.

---

## Tell generation flow

> **Earlier face draft.** The live tell is lane Entry, read under the visual-gap rule. This flow does not show Apex or Exit, and it is not a second bluff layer.

For each turn and clash position, the opponent's face in this earlier draft is determined as follows:

1. **Look up turn type** from the track layout: `layout[turn_num % len(layout)]`
2. **Look up the 3-stance sequence** from the turn type table. Select the stance for the current clash position:
   - **pos 0** → **entry** stance
   - **pos 1** → **apex** stance
   - **pos 2** → **exit** stance
3. **Look up face type** from the archetype reference table
4. **Face shown** = face type's expression for the selected phase stance
5. **Deception check** — look up the archetype's comfort zone for this turn type:
   - **Weak turn**: face is always truthful (lie rate 0%)
   - **Comfortable turn**: normal lie rate doubled across all 3 positions
   - **Other**: normal lie rate
   
   Then apply hand-dependent bluffing, clash-position weighting, and reverse psychology.
6. **If deceptive**: the face shows the phase stance, but the bluff tell is active
7. **Intensity** determines how exaggerated all of the above is

This earlier draft showed 3 faces per turn, revealed sequentially during the straight approach (entry, then apex, then exit). That sequence is not the live tell. The player does not get an explicit Apex face or Exit face. Entry is the rival's lane, read from the player camera under the visual-gap rule, and it can bluff by improper placement.

The same earlier draft crossfades three face textures (ATK/DEF/NEU) on the phase schedule, with a fourth overlay for a bluff. That crossfade is not the live tell and does not show Apex or Exit.

---

### Deception by tier

> Earlier face-draft rates. Not probabilities for an Entry bluff by improper placement, and not an Apex/Exit bluff layer. Cells unchanged.

| Tier | Wild | Lieutenant | Boss |
|------|------|------------|------|
| Novice | **Intensity:** 5. **Deception:** None. Always truthful. | **Intensity:** 5. **Deception:** None. Always truthful. | **Intensity:** 5. **Deception:** None. Always truthful. |
| Veteran | **Intensity:** 4. **Deception:** 0% lie rate. No deception. | **Intensity:** 3. **Deception:** 15% lie rate. Lead clash only. Hand bluffs: obvious. | **Intensity:** 3. **Deception:** 25% lie rate. Lead + middle. Hand bluffs: obvious. |
| Top | **Intensity:** 3. **Deception:** 25% lie rate. Lead clash only. Hand bluffs: obvious. | **Intensity:** 2. **Deception:** 40% lie rate. Lead + middle. Hand bluffs: smart. Reverse psychology on lead. | **Intensity:** 2. **Deception:** 50% lie rate. All clashes. Hand bluffs: smart. |

---

## Decision window

The player locks all 3 cards, the line, up front, before corner playback. While choosing, the car tell they can read is lane Entry, under the visual-gap rule above. Apex and Exit are inferred, not revealed as the approach plays. The intended inputs are that Entry, shared Touge, Wangan, and Street tendencies, the corner's geometry, and the real lead/gap at the start of selection. The precise district habits and the race-state-dependent Apex/Exit map are still TBD. The archetype rows in this doc are not that map.

The corner then plays back as a cinematic. Authored per-corner camera motion does not replace the fixed rear third-person player camera as the view Entry is read from, and it does not change the spacing rule. Playback does not change cumulative DP.

This decision does not set the selection timer. An older sentence in this section said 8 seconds of watching track position and suspension. `design/godot-build-guide.md` still builds a 12-second straight split into entry, apex, and exit picks, matching the prototype scripts. Those two durations are an open mismatch, not a number approved here.

---

