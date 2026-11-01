# Velocity Shift — Equations Reference

Every formula in the combat engine. All are pure functions in `sim/velocity_shift/equations.py`. All game-rule constants are module-level names — tunable in one place, never per-encounter.

---

## 1. Hit Points (HP)

```
max_hp = level × HP_PER_LEVEL (120)
```

| Variable | Range | Notes |
|----------|-------|-------|
| level | 1+ | Combatant's level (from cars.py archetype progression) |

**Intent:** HP scales linearly with level. Used to compute position (damage ratio) at match end.

---

## 2. Damage (per clash, before mitigation)

**File:** `sim/velocity_shift/equations.py` — `compute_damage()`

```
DP_i = POW × QTE_factor × clash_mult_i × battle_mult
```

| Variable | Source | Range | Notes |
|----------|--------|-------|-------|
| POW | CombatantStats | 0+ | Attacker's power |
| QTE_factor | derived | 0.1–1.0 | QTE_score / QTE_NORMALIZER (10) |
| clash_mult_i | derived | 0.65–1.35 | Per-clash outcome |
| battle_mult | derived | 1.0+ | 1 + BATTLE_BONUS × \|sum\| |

**Intent:** Pure multiplicative chain. No gates, no interaction terms, no sigmoid.

### Turn DP (after mitigation)

```
DP_turn_effective = average(DP_1, DP_2, DP_3) × opponent_mitigation_mult
```

Where mitigation comes from the *opponent's* EN (they defend against your damage):

```
opponent_mitigation_mult = max(MITIGATION_FLOOR, 1 - (opponent_EN / 1000) × MITIGATION_PER_1000 × opponent_QTE_factor)
```

---

## 3. QTE Effectiveness

**File:** `sim/velocity_shift/equations.py` — `qte_factor()`

```
QTE_factor = QTE_score / QTE_NORMALIZER (10)
```

| Variable | Range | Notes |
|----------|-------|-------|
| QTE_score | 1–10 | Execution rating per turn |

**Intent:** Linear normalization. A QTE_score of 7 yields a 0.7 multiplier on all damage for that turn.

---

## 4. Clash Multiplier

**File:** `sim/velocity_shift/equations.py` — `clash_mult()`

```
clash_mult = 1 + CLASH_STAKES (0.35) × outcome_value
```

| Variable | Range | Notes |
|----------|-------|-------|
| outcome_value | {-1, 0, +1} | LOSS / NEUTRAL / WIN |

| Outcome | Bonus | Mult |
|---------|-------|------|
| WIN | +0.35 | 1.35× |
| NEUTRAL | 0 | 1.00× |
| LOSS | -0.35 | 0.65× |

**Intent:** Single-parameter outcome modifier. 0.35 is the fixed game-wide clash stakes.

---

## 5. Battle Multiplier

**File:** `sim/velocity_shift/combat.py` — (inline in `resolve_turn()`)

```
battle_mult = 1 + BATTLE_BONUS (0.05) × |sum(outcome_values)|
```

| Variable | Range | Notes |
|----------|-------|-------|
| outcome_sum | -3 to +3 | Sum of 3 per-clash outcome values (±1 each) |

| Result | Margin | Mult |
|--------|--------|------|
| Tie | 0 | 1.00× |
| 2-1 win | 1 | 1.05× |
| 3-0 sweep | 3 | 1.15× |

**Intent:** Winning a battle should feel impactful. Each point of win margin gives a small flat boost to all damage that turn.

---

## 6. Stance Resolution

**File:** `sim/velocity_shift/equations.py` — `resolve_stance()`

```
Attack  vs Attack   → NEUTRAL
Attack  vs Neutral  → WIN      (Attack beats Neutral)
Attack  vs Defend   → LOSS     (Defend beats Attack)
Neutral vs Neutral  → NEUTRAL
Neutral vs Defend   → WIN      (Neutral beats Defend)
Neutral vs Attack   → LOSS     (Attack beats Neutral)
Defend  vs Defend   → NEUTRAL
Defend  vs Attack   → WIN      (Defend beats Attack)
Defend  vs Neutral  → LOSS     (Neutral beats Defend)
```

RPS cycle: **Attack > Neutral > Defend > Attack**

---

## 7. Battle Winner

**File:** `sim/velocity_shift/combat.py` — `battle_winner()`

```
outcome_values = [outcome_value_1, outcome_value_2, outcome_value_3]
winner = sign(sum(outcome_values))
battle_mult = 1 + 0.05 × |sum|
```

| Sum | Result | battle_mult |
|-----|--------|-------------|
| > 0 | Player wins clashes | 1.05 (2-1) or 1.15 (3-0) |
| < 0 | Opponent wins clashes | 1.05 or 1.15 for opponent |
| = 0 | Tie | 1.00 |

---

## 8. Damage Mitigation

**File:** `sim/velocity_shift/equations.py` — `damage_mitigation()`

```
mitigation_mult = max(MITIGATION_FLOOR, 1 - (EN / 1000) × MITIGATION_PER_1000 × QTE_factor)
```

Applied per turn: each combatant's EN reduces the opponent's effective DP.

| Variable | Range | Notes |
|----------|-------|-------|
| EN | 0+ | Defender's Endurance stat |
| QTE_factor | 0.1–1.0 | Defender's execution quality that turn |

| Scenario | Mitigation mult | Damage taken |
|----------|----------------|--------------|
| EN=0 | 1.0 | 100% |
| EN=500, QTE=0.7 | 0.86 | 86% |
| EN=1000, QTE=0.7 | 0.72 | 72% |
| EN=1000, QTE=1.0 | 0.60 | 60% |
| EN=1650, QTE=1.0 | 0.34 | 34% |

**Intent:** Higher EN makes you tougher, but only if you're driving well (QTE). Good execution rewards both offense and defense. The 10% floor prevents total immunity.
