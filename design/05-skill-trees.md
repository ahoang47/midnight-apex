# Velocity Shift — Skill Trees (Design Reference)

> **Status:** Deferred. Mods (shop-bought equipment with trade-offs/unique effects) serve as the player's stat expression layer. Skill tree categories and mechanics are not yet decided. See `design/notes/mod_notes.md` for current design.

---

## Current identity layers

| Layer | Scope | Where it lives | Status |
|-------|-------|----------------|--------|
| **Archetype** | Fixed stat ratio, linear level scaling | `cars.py` | Implemented |
| **Mods** | Loadout equipment — stat expression & build customization | Shop-bought | Design phase |
| **Skill Tree** | Permanent passive modifiers | TBD | Deferred |

### Mods vs the old "RunMods" concept

The previous "RunMod" system (pre-fight loadout selections) has been replaced by **Mods** — individual equipment items bought from the shop that provide stat bonuses (with trade-offs), unique effects, or both. Unlike RunMods, mods are not per-archetype and not temporary — they are persistent equipment that lives in the player's inventory.

---

## Balance rules (for when tree is designed)

These principles should guide future tree design:

### 1. Additive modifiers only

Tree nodes should modify existing combat terms **additively**, not multiplicatively. This prevents runaway stacking.

| Additive | Multiplicative |
|---|---|
| `clash_mult = 1 + (clash_stakes + tree_bonus) * outcome` | `clash_mult = 1 + clash_stakes * outcome * tree_bonus` |
| `battle_mult = 1 + (battle_bonus + tree_bonus) * \|sum\|` | `battle_mult = 1 + battle_bonus * \|sum\| * tree_bonus` |

### 2. One node per category

If using categories, a build should activate at most one node per category.

### 3. Point costs

TBD. If using a point system, costs should scale by tier.

---

## Interaction with existing systems

| System | Interaction |
|--------|-------------|
| **Damage formula** | Tree bonuses should be additive modifiers to existing terms (clash_stakes, battle_bonus, mitigation_floor). They should never introduce new multiplicative layers. |
| **Deck / draw** | Tree nodes could modify draw count/quality. |
| **Mods** | Separate system. Mods are equipped in loadout slots and provide stats/effects directly. Tree could modify mod effectiveness. |
| **QTE** | Tree nodes could raise baseline or reduce penalties. |
| **AI opponents** | Opponents do not use skill trees. They use stock archetype stats + their own mods. |
| **HP / Knockout** | Should remain unaffected. HP = level × HP_PER_LEVEL — tree nodes should never touch this formula. |

---

## Implementation notes

- **Not yet implemented.** This document describes the intended design direction.
- Tree data would live in a new module when designed.
- Combat integration would go in `combat.py:resolve_turn()` — reading active passives from the player's build and applying additive modifiers before damage calculation.
- The metagame layer (point earning, UI, saving builds) is outside the combat engine's scope.
