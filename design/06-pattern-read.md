# Opponent pattern telegraphing 

**General rules:**
- Opponent face displayed in one corner, upcoming turn in another
- Each turn, opponent makes a face intended to telegraph their next choice
- Faces also correlate to **turn type**. Each archetype has a **3-stance sequence** (entry/apex/exit) for each turn type, representing the racing line through that corner. The face for clash position 0 shows the **entry** stance, position 1 shows the **apex** stance, and position 2 shows the **exit** stance. Whether any given face is truthful depends on deception mechanics. A bluff tell (betrayal signal in the expression) indicates that face is lying.
- **Track layouts are fixed per circuit** — authored, not randomized. Each archetype's cornering habits (the 3-stance sequences per turn type) remain consistent, but **bluffing behavior is per-character**, driven by lie rate and personality. Players learn archetype-wide driving lines, but must read each opponent's individual deception patterns.
- **Car motion telegraphs stance across two simultaneous channels** — track position (advance warning of entry stance) and suspension loading (advance warning of apex stance). Both are visible on the straightaway approach before corner entry. The face provides a secondary cross-reference with its own bluff mechanics.
---

## Deception mechanics

Four systems govern how reliable the opponent's face is. Each scales independently by tier and encounter type.

### 1. Lie rate
The probability that any given face does **not** match the AI's actual pick for that clash slot. Ranges from 0% (always truthful) to 100% (always lying).

### 2. Clash-position weighting
Deception is not uniform across all 3 clashes. At lower levels it only affects the entry (pos 0). As tiers increase it spreads to apex (pos 1) and eventually exit (pos 2). This lets players learn partial trust patterns — e.g., "the exit face is always true." Clash-position weighting will be archetype dependent - that's to say that some archetypes could always bluff on apex. 

---

## Turn type system

All turn types have left and right variants. No turn type may repeat more than twice consecutively in the track layout, regardless of direction.

Each turn type defines a 3-stance sequence per archetype representing the racing line through that corner:

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

Each archetype has **2 comfortable** turn types (double the normal bluff rate) and **2 weak** turn types (never bluff here).

| Archetype | Face type | Comfortable (2× bluff rate) | Weak (never bluffs) |
|-----------|-----------|----------------------------|---------------------|
| Aggressive (POW) | A — Scowling | Sweepers, Increasing Radius | Hairpins, Decreasing Radius |
| Defensive (EN) | B — Grinning | Constant Radius, Sweepers | Chicanes, Esses (S-Bends) |
| Balanced | B — Grinning | Constant Radius, Sweepers | Chicanes, Esses (S-Bends) |
| Precise (HAN) | F — Focused | Chicanes, Esses (S-Bends) | Sweepers, Hairpins |
| Adaptive | F — Focused | Chicanes, Esses (S-Bends) | Sweepers, Hairpins |

### Car motion types

Each stance has a 2-channel visual language, both playing simultaneously on the straightaway approach before corner entry. Opponents also have a **bluff** variant — the car looks like one stance but the opponent is actually playing another. All archetypes share this.

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

Exit (pos 2) reflects **position**, not stance. By exit, QTE is done and the DP gap is resolved. The leading car powers away with a clean exit; the trailing car struggles or defends. If the lead changed this turn, a short overtake animation plays after exit (car moves from behind to ahead).

Exit also feeds forward: the exit stance plus the next turn's type determines which entry stances are locked out next turn (see the lockout tables in `03-deckbuilding-clash.md`).

---

## Tell generation flow

For each turn and clash position, the opponent's face is determined as follows:

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

The player sees 3 faces per turn, revealed sequentially during the straight approach:
- **0–4s:** Entry face shown and held
- **4–8s:** Face crossfades to the apex expression
- **8–12s:** Face crossfades to the exit expression

Each face shows the expression matching the archetype's entry, apex, or exit phase for this turn type — plus a bluff tell if that phase's pick is deceptive. The observable hand provides a secondary cross-reference — impossible tells (stance not in hand) confirm deception at lower tiers.

Faces use a crossfade blend in the Godot version: 3 stacked TextureRects (ATK/DEF/NEU expression) with alpha crossfade driven by the phase schedule. A 4th overlay layer handles the bluff tell texture. This produces smooth transitions rather than hard cuts between stances.

---

### Deception by tier

| Tier | Wild | Lieutenant | Boss |
|------|------|------------|------|
| Novice | **Intensity:** 5. **Deception:** None. Always truthful. | **Intensity:** 5. **Deception:** None. Always truthful. | **Intensity:** 5. **Deception:** None. Always truthful. |
| Veteran | **Intensity:** 4. **Deception:** 0% lie rate. No deception. | **Intensity:** 3. **Deception:** 15% lie rate. Lead clash only. Hand bluffs: obvious. | **Intensity:** 3. **Deception:** 25% lie rate. Lead + middle. Hand bluffs: obvious. |
| Top | **Intensity:** 3. **Deception:** 25% lie rate. Lead clash only. Hand bluffs: obvious. | **Intensity:** 2. **Deception:** 40% lie rate. Lead + middle. Hand bluffs: smart. Reverse psychology on lead. | **Intensity:** 2. **Deception:** 50% lie rate. All clashes. Hand bluffs: smart. |

---

## Decision window

As the cars approach the straightaway section leading into the corner, the player has **8 seconds** to observe the opponent's car animation (track position + suspension loading), read the track context, and select all 3 stance cards (entry, apex, exit) before the corner. Any position unselected when the timer expires is auto-selected (semi-random).

Once all 3 cards are locked in, the turn renders as a cinematic corner play-through. Camera motion is attached to the turn type, and the cars animate through the scene with their behavior driven by the selected stances.

---

