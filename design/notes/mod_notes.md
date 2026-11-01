# Mod System Design

## Core Loop

1. Pick starting car chassis (2–3 archetypes with fixed stat ratios from L1)
2. Race wild & lieutenant encounters for currency
3. Car levels up:
   - Stats scale linearly (fixed archetype ratio — no convergence, no redistribution)
   - Unlocks loadout slots at key levels
   - Gates access to higher-tier mods
4. Buy mods from the shop with currency (boss wins expand the shop inventory)
5. Equip mods into loadout slots — your stat expression & build customization
6. Boss fight:
   - Win → currency + rare mods enter shop + narrative advances
   - Lose → retry (no destruction, no progress)

## Archetypes (Chassis)

- Fixed stat ratio from L1 (e.g. Bruiser = 55/20/25, Swift = 25/20/55)
- Each level multiplies the ratio linearly — identity is immediate and permanent
- No convergence, no redistribution of the ratio

## Progression Rules

- Car level → linear stat growth (fixed ratio) + loadout slot unlocks + mod tier gates
- No player stat allocation — chassis is the skeleton, mods are the muscle

## Narrative Gating

- Losing a story mission blocks narrative advancement (Yakuza-style gate)
- No car or mod destruction on loss
- Optional: entry fee paid per retry attempt

## Loadout Slots

- Start with ~3 slots, unlock more at key car levels (up to ~8–10)
- Each slot holds one mod
- Swapping mods between encounters is free — encourages experimentation

## Mods (Shop Only)

- Individual equipment items bought from the shop with currency
- Have level requirements (e.g. Turbo Mk3: L25+)
- Three design flavors (mix and match per mod):
  - **Sharp trade-offs** — e.g. +15 POW, −10 EN
  - **Unique effects** — e.g. "First clash each turn auto-wins" or "QTE window +20% but max clash stakes reduced"
  - **Both** — stat penalty + unique upside
- Shop inventory expands when bosses are defeated (narrative reward)
- Encounter design forces adaptation — different mod loadouts matter match-to-match

## Reward Structure

| Encounter | Currency | Other |
|-----------|----------|-------|
| Wild | Small | — |
| Lieutenant | Moderate | — |
| Boss | Large | Shop inventory expands with rare mods |

## Opponent Mods

- Opponents have their own mods matching their archetype
- Opponent mods are visible in the UI pre-match, before the player accepts

## Tree / Mod Categories

- TBD — categories and mechanics decided later

## Design Notes

- **Mods are the only player expression vector.** Chassis identity is fixed; all build decisions happen in the loadout screen. This keeps the fantasy of "growing your one car" while giving the player meaningful choices to make before each race.
- **No free lunches.** Every mod that gives a strong upside carries a trade-off or a niche window of effectiveness. Equipping a pure-stat mod means you're giving up a slot that could hold a unique effect.
- **Encounter design is the bottleneck.** Opponents should be tuned such that the same loadout doesn't work every time. The player should be glancing at the opponent's visible mods and swapping their own to counter.
- **Shop-only acquisition aligns with the narrative.** You're one driver with one car, building reputation in a scene. You earn money from races and spend it at the shop — no random drops, no farming.
- **No roguelite layer.** Loss costs progress (narrative gate) but never destroys your car or mods. The penalty is "try again," not "start over."
