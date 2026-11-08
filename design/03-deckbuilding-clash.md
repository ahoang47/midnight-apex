# Midnight Apex — Deckbuilding & Clash Mechanics

> Vocabulary follows the locked terms in 01.

---

## Deck Construction (pre-match)

Each combatant gets exactly **192 cards**. Card type proportions are derived from their three core stats:

```
total  = POW + EN + HAN
alpha  = 0.85
beta   = 0.15

wp     = alpha × POW / total  + beta / 3
wd     = alpha × EN / total   + beta / 3
wn     = alpha × HAN / total  + beta / 3
tw     = wp + wd + wn

Attack  = round(192 × wp / tw)
Defend  = round(192 × wd / tw)
Neutral = 192 - Attack - Defend
```

The `alpha=0.85` smoothing term blends stat proportions with equal thirds, preventing any single stance from overwhelming the deck at extreme stat spreads. A build with POW=900, EN=50, HAN=50 still gets ~5% of each off-stance card, preserving RPS flexibility.

Stats have no upper bound. Deck composition scales naturally — more POW yields more Attack cards regardless of absolute value.

### What deck composition encodes

| Build focus | Card pool tendency |
|---|---|
| POW-heavy | Mostly Attack cards — aggressive, high damage potential |
| EN-heavy | Mostly Defend cards — survivability, damage mitigation |
| HAN-heavy | Mostly Neutral cards — adaptable, flexible picks |
| Balanced (~even) | ~64 of each — unpredictable, no strong bias |

The deck is shuffled once at construction. Deck composition stays fixed for the entire match.

---

## Per-Turn Card Flow

```
Position-based picks (3 sequential clashes):
                    ┌──────────────────┐
                    │   DRAW PILE       │
                    │  (remaining)      │
                    └────────┬─────────┘
                             │ draw 6
                             ▼
                    ┌──────────────────┐
                    │     HAND (6)      │
                    └────────┬─────────┘
                             │
               ┌─────────────┼─────────────┐
               ▼             ▼             ▼
         Pos 0 (lead)   Pos 1 (mid)   Pos 2 (anchor)
         pick 1 card    pick 1 card    pick 1 card
         → resolve      → resolve      → resolve
               │             │             │
               └─────────────┼─────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  BATTLE BONUS     │
                    │  × |outcome sum|  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  DAMAGE (3×)      │
                    │  avg → mitigate  │
                    └──────────────────┘
```

### Draw phase

- Each combatant draws 6 cards from their personal deck
- The player's deck uses a discard pile: played and unpicked cards enter the discard pile at turn end
- The opponent's deck uses `reshuffle_on_end`: all 6 cards return to the draw pile and are reshuffled each turn, guaranteeing pattern-consistent hands for their personality phase
- Player decks **do not** auto-reshuffle when the draw pile runs out — once depleted, further draws return fewer cards
- Opponent decks never run out (full reshuffle each turn)

### Selection phase (sequential by position)

Cards are chosen one position at a time:

1. **Lead (pos 0):** Player picks 1 card from their 6-card hand. Opponent picks 1 from theirs. Clash resolves immediately.
2. **Middle (pos 1):** From remaining 5 cards, player picks 1, opponent picks 1. Clash resolves.
3. **Anchor (pos 2):** From remaining 4 cards, each side picks their final card. Clash resolves.

The opponent's AI picks use a phase-based personality (`sim/velocity_shift/ai.py` — 5 personalities, each with 1–3 phase-indexed behaviors). Each phase defines hand requirements (minimum card counts per stance) and a selection strategy (EV scoring, behavior overrides like `counter`, `alternate`, `highest_ev`, or pure random for unpredictable phases).

After all 3 clashes resolve, damage is computed for the turn.

### Played cards → discard

- **Player deck:** The 3 played cards + 3 unpicked cards → discard pile at turn end
- **Opponent deck:** The 3 played cards + 3 unpicked cards → draw pile, reshuffled

---

## Clash Resolution

Each turn has 3 clashes, resolved position-wise:

```
Lead     vs Lead     → StanceOutcome_1
Middle   vs Middle   → StanceOutcome_2
Anchor   vs Anchor   → StanceOutcome_3
```

### Per-clash outcome

Stances are resolved via the RPS cycle:

| Attacker | Defender | Result |
|---|---|---|
| Attack | Neutral | WIN |
| Attack | Defend | LOSS |
| Neutral | Defend | WIN |
| Neutral | Attack | LOSS |
| Defend | Attack | WIN |
| Defend | Neutral | LOSS |
| Any | Same | NEUTRAL |

**RPS cycle:** `Attack > Neutral > Defend > Attack`

### Per-clash damage contribution

```
clash_mult_i  = 1 + CLASH_STAKES × outcome_value
battle_mult   = 1 + BATTLE_BONUS × |sum(outcomes)|
DP_i          = POW × QTE_factor × clash_mult_i × battle_mult
```

Where `outcome_value = +1` for WIN, `0` for NEUTRAL, `-1` for LOSS.
DP is floored at 0 (negative damage is impossible).

### Per-turn mitigation

After averaging the 3 per-clash DP values, each side's damage is reduced by the opponent's mitigation:

```
mitigation_mult   = max(MITIGATION_FLOOR, 1 - (EN/1000) × MITIGATION_PER_1000 × QTE_factor)
DP_turn_effective = avg(DP_1, DP_2, DP_3) × opponent_mitigation_mult
```

Constants: `CLASH_STAKES = 0.35`, `BATTLE_BONUS = 0.05`, `MITIGATION_PER_1000 = 0.4`, `MITIGATION_FLOOR = 0.1`, `QTE_NORMALIZER = 10.0`.

### HAN → QTE modifier

Both sides have their raw QTE score (1–10) modified by HAN proportion before entering combat:

```
han_pct  = HAN / (POW + EN + HAN)
modified = raw_QTE × (1 + HAN_QTE_WEIGHT × (han_pct - 1/3))
```

Where `HAN_QTE_WEIGHT = 0.5`. Neutral at `han_pct = 1/3` (no change). A high-HAN build (Precise, 55% HAN) gets ~+10.8%; a low-HAN build (Aggressive, 25%) gets ~−4.2%. The same formula applies to both player and AI. This value is then normalised to a `qte_factor` (score / 10.0, clamped 0–1) by `resolve_turn`.

### QTE rubber-band (proportional blend)

The rubber-band mechanic stops one side from snowballing by eroding QTE advantage as the gap grows. It uses a **threshold-based proportional blend**, not a binary switch.

```
threshold = avg_max_hp × 0.15
blend     = min(1.0, |player_gap| / threshold)
```

Each turn, each side's QTE factor is split into two values — one for damage, one for mitigation — based on who is ahead:

| Gap | Damage QTE | Mitigation QTE |
|---|---|---|
| **Leader** | `qte` | `qte + (1 - qte) × blend` |
| **Trailer** | `qte + (1 - qte) × blend` | `qte` |
| **Tied (gap=0)** | `qte` | `qte` |

The "disadvantaged" stat (leader's mitigation / trailer's damage) is **blended toward 1.0** as the gap widens. At full blend (gap ≥ threshold), it reaches 1.0 — effectively removing QTE contribution from that term. At gap=0, both stats use the full QTE factor evenly.

This prevents the **double-dip** scenario where a single player's QTE simultaneously boosts their damage and reduces incoming damage, while keeping the transition smooth rather than abrupt.

### Best-of-3 (affects damage via battle_mult)

```
outcomes_sum = outcome_value_1 + outcome_value_2 + outcome_value_3
battle_mult  = 1 + BATTLE_BONUS × |outcomes_sum|
```

- Sum > 0 → Player wins the battle → both sides get `battle_mult` boost
- Sum < 0 → Opponent wins the battle → both sides get `battle_mult` boost
- Sum = 0 → Tie → `battle_mult = 1.0`

The battle winner's `battle_mult` applies to **all 3 clashes** for **both sides** that turn.

---

## Strategic Considerations

### Deck management

- With a fixed 192-card deck and 6 drawn per turn, you cycle through the deck every 32 turns (192/6)
- **Player deck:** Discard pile grows over time; draw pile shrinks. Once empty, draws yield fewer cards per turn.
- **Opponent deck:** Reshuffles all 6 cards back into the draw pile each turn — card type ratios stay constant for the opponent across the match
- Per-turn variance means you might draw 6 Neutrals from a POW-heavy deck (unlikely but possible)

### Archetype matchup theory

| Attacker | Defender | Dynamic |
|---|---|---|
| POW-heavy | EN-heavy | Offense vs tough defense. Race to overcome mitigation before RNG swings against you. |
| HAN-heavy | POW-heavy | Flexible stances vs aggressive. Adaptability vs burst potential. |
| Balanced | Balanced | Variance-driven — deck composition matters less per turn, QTE and reads decide. |

---

## Turn DP vs Match DP

- Each of the 3 clashes produces its own DP value
- Turn DP = average of the 3 per-clash DP values
- Match total accumulates turn DP across all turns
- **Decision:** after max_turns, the winner is the combatant with the higher position (DP / opponent_max_hp)
- **Tie:** if positions are equal after max_turns, the opponent wins
