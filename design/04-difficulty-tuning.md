# Velocity Shift — Difficulty & Tuning

There are no tuning knobs. Difficulty is driven entirely by the **level gap** between combatants.

---

## Archetype Progression System

Builds belong to an archetype and a level. Stats are computed from `sim/velocity_shift/cars.py`. All archetypes start at 33/33/33 at level 1 and progress toward their target over 100 levels via an ease-in curve.

**Specialization curve:**

```
progress(L) = ((L - 1) / 99) ^ 1.5
```

**Stat percentage** (interpolate, then normalise to sum 100):

```
stat_pct(L) = 33 + (target - 33) × progress(L)
```

With `p=1.5`, identity develops slowly at low levels (fair matchups) and locks in during the mid-to-late game.

**Stat budget** (same for all archetypes at the same level):

```
total_budget = level × 30
POW_abs = total_budget × pow_pct / 100
```

| Tier | Level | Budget |
|------|-------|--------|
| Starter | 10 | 300 |
| Novice | 20 | 600 |
| Journeyman | 30 | 900 |
| Veteran | 45 | 1350 |
| Elite | 60 | 1800 |
| Master | 80 | 2400 |
| Legend | 100 | 3000 |

### Archetype Targets (Level 100)

| Archetype | L1 split | L100 target (POW / EN / HAN) | Deck bias | Play style |
|---|---|---|---|---|
| **Bruiser** | 33/33/33 | 55 / 20 / 25 | Heavy Attack cards | High burst, glassy |
| **Endurance** | 33/33/33 | 20 / 55 / 25 | Heavy Defend cards | Damage mitigation, outlasts opponents |
| **Swift** | 33/33/33 | 25 / 20 / 55 | Heavy Neutral cards | Flexible stance choices |
| **AR P** | 33/33/33 | 40 / 30 / 30 | Mild Attack lean | Jack-of-all-trades, power-tilt |
| **AR E** | 33/33/33 | 30 / 40 / 30 | Mild Defend lean | Jack-of-all-trades, endurance-tilt |
| **AR H** | 33/33/33 | 30 / 30 / 40 | Mild Neutral lean | Jack-of-all-trades, handling-tilt |

---

## Difficulty = Level Gap

The opponent's level is computed from the player's level and a fixed ratio per encounter type:

| Encounter type | Ratio | Opponent level (L50) | ~Turns to Decision | Player feel |
|---|---|---|---|---|
| **Wild** | 0.35× | L17 | 3–5 | Dominate — opponent is stat-poor |
| **Lieutenant** | 0.75× | L38 | 10–12 | Pressure — near stat parity, edges out |
| **Boss** | 1.15× | L57 | 12+ | Heat — opponent marginally stronger |

### Why this works

Each combatant's max HP is `level × HP_PER_LEVEL (180)`. Since damage scales with POW (which scales with level), the level gap cleanly maps to encounter difficulty:

- **Wild:** low-level opponent → low HP, low POW → dies fast, can't hurt you
- **Lieutenant:** near-level opponent → comparable HP and damage → close race
- **Boss:** higher-level opponent → more HP, more damage → you need to play well to survive

---

## Stat Effects on Difficulty

| Stat | Effect on difficulty |
|---|---|
| **POW** | Directly scales damage. Higher opponent POW forces player to win clashes or take big hits. |
| **EN** | Determines damage mitigation. Higher EN opponent reduces your effective DP. |
| **HAN** | Deck composition only (drives Neutral card weight). Higher HAN = more flexible stance choices. |

---

## Archetype Matchups

| Player build | Struggles against | Excels against |
|---|---|---|
| POW-heavy | EN-heavy tanks (mitigation resists damage) | Glass cannon (mirror) |
| EN-heavy | HAN-heavy (flexible stances, hard to predict) | POW-heavy (mitigation absorbs burst) |
| HAN-heavy | POW-heavy (Neutral loses to Attack) | EN-heavy (Neutral beats Defend) |
| Balanced | None strongly | None strongly |

---

## QTE Rubber-Band

The rubber-band splits each combatant's QTE factor between damage and mitigation *proportionally* to the DP gap. The threshold is 15% of average max HP:

```
threshold = avg_max_hp × 0.15
t = min(1.0, |gap| / threshold)

Leader:  damage_qte   = own QTE (always on)
         mitigation_qte = lerp(own QTE, 1.0, t)
Trailer: damage_qte   = lerp(own QTE, 1.0, t)
         mitigation_qte = own QTE (always on)
```

- **t = 0** (tied): both sides use full QTE for everything
- **t = 1** (gap ≥ 15% HP): full rubber-band — leader's defence and trailer's offence get no QTE benefit
- **0 < t < 1**: partial rubber-band — small gaps have small effects

---

## AI Difficulty — Phase-Based Personalities

Difficulty is driven by the level gap (above), but opponent *behavior variety* comes from 6 phase-based AI personalities defined in `sim/velocity_shift/ai.py`. Each personality has 3 phase-indexed behaviors — which index is active depends on the encounter's phase count.

### Personalities

| Personality | Phase 0 | Phase 1 | Phase 2 |
|-------------|---------|---------|---------|
| **Bruiser** | AGGRESSIVE (Atk+3) | REACTIVE (counter) | UNPREDICTABLE |
| **Endurance** | REACTIVE (counter) | AGGRESSIVE (Atk+3) | UNPREDICTABLE |
| **Swift** | AGGRESSIVE (highest_ev) | REACTIVE (counter) | UNPREDICTABLE |
| **AR P** | AGGRESSIVE (Atk+4) | AGGRESSIVE (Def+4) | AGGRESSIVE (Neu+4) |
| **AR E** | AGGRESSIVE (alternate) | REACTIVE (counter) | REACTIVE (repeat_win) |
| **AR H** | AGGRESSIVE (third_highest_ev) | REACTIVE (second_highest_ev) | UNPREDICTABLE |

### Phases per encounter

| Encounter | Phases | Active personality indices |
|-----------|--------|---------------------------|
| Wild | 1 | phase[0] only |
| Lieutenant | 2 | phase[0], phase[1] |
| Boss | 3 | phase[0], phase[1], phase[2] |

### Unique opponents

Each phase slot must use a **different** personality (no repeats per opponent), and the phase index matters (it selects which of the personality's 3 behaviors activates). This produces ordered permutations:

| Encounter | Slots | Calculation | Unique opponents |
|-----------|-------|-------------|------------------|
| Wild | 1 | 6 | 6 |
| Lieutenant | 2 | 6 × 5 | 30 |
| Boss | 3 | 6 × 5 × 4 | 120 |
| **Total** | | | **156** |

Opponent QTE baseline is derived from level: `4.0 + level × 0.025` (4.25 at L10 → 6.5 at L100).
