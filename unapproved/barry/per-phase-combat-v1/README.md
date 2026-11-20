# per-phase-combat-v1: Street/Wangan resolve combat per phase (Barry DRAFT, 2026-11-20, UNAPPROVED)

> **Canon (design/01, acf9b25; Austin direct 2026-11-20 6:12 AM PT):** in Wangan and Street, Entry, Apex and Exit each resolve
> their own clash when the phase ends, and car order can change after each phase (passing). Touge is unchanged.
> **Open point (1) DECIDED (Austin, direct, 6:14 AM PT):** "Each phase uses its own QTE score. Perhaps this is where the spirit
> meter can come in, because there's no incentive to winning all three phases currently."
> **Touge what-if (Austin 6:14 AM: "Try simming it with touge, as well."):** data only; canon keeps Touge per-turn.

Nothing here touches sim/. Patch `per_phase.patch` (against touge-race 83b98d8+ sim/) was run on a branch copy; runner
`per_phase_climb.py`, output `per_phase_climb.json`. Seeds 96,000,000 + style x 100,000 + k (same as the live climb).

## 1. Spec (what changes in the sim)

- **Already per clash.** The live engine plays 3 clashes per turn (`match.py:134-152`): each clash's stances, heat
  `play()` and outcome are resolved in order, and `resolve_turn` (`combat.py:139-156`) pays each clash's progress
  separately. The race is won on total progress. So "resolve each phase when it ends" with nothing else changed gives
  **identical numbers**; the only real changes are which QTE score each clash uses and what (if anything) order does.
- **resolve_turn for per-phase districts** (`E.PER_PHASE_DISTRICTS = ("street", "wangan")`): clash i uses the player's
  phase-i score and the AI's phase-i score (`p_qte_by_clash` / `o_qte_by_clash`). Running order = running progress totals,
  updated after each clash (display / passing). Touge calls the unchanged path: verified identical (`per_phase=False`, 60
  Street boss races, total progress 3009.138969 both).
- **Player QTE:** one press per phase. Real play: the phase's own score (no turn average). Sim player: one press drawn from
  the existing press model (`expected_hit_quality`: s = max(0, 1 - |e|/a), e ~ N(0, sigma)) from its own RNG
  (seed + 15,485,863); E[s] is unchanged, but a single press is noisier than the expected value the live sim uses.
- **AI QTE:** one N(0.80, 0.08) draw **per phase** (3 per turn) from the existing AI RNG, clamped and rounded as today.
- **Heat / gauges:** unchanged. `play()` per clash already happens in phase order; `begin_turn` / `end_turn` (passive
  cooling, locks) stay per turn.
- **Stance picks and the 12 s pick timer:** unchanged. All three picks are made in the SELECT straight (12 s,
  `display.json pick_timer_s`) before the corner, so no picking mid-corner. The boss's line is still planned per turn.
- **Spirit option (sweep reward), prototyped:** win all 3 clashes of a turn, and that side's clash progress is x1.20 next
  turn (both sides; doesn't stack, so no snowball).

## 2. Open points

1. **Own phase QTE: DECIDED by Austin (above).** My data agreed it's the more honest rule (each clash is scored by its own
   press), but it costs the player a lot (see 3).
2. **Mid-turn order change: recommend it changes nothing mechanically in v1.** Order = running progress, shown after each
   phase. The sim has no leader/defender, draft or line effect today (the winner is total progress), and the line is fixed
   per turn before the corner. Any drafting or defender effect is a new mechanic and would need its own proposal and
   tuning. The incentive Austin is asking for is better served by the sweep reward, which is measurable and symmetric.

## 3. Results (live mod_skill climb; 80/80 floor: 2,000 races per cell, boss 6,000; boss cells 6,000)

Strong 80/80 at the floor, kid1 -> boss (Live = config/mod_skill_climb_v1.json, n = 6,000 per cell):

| | Street | Wangan | Touge (what-if) |
|---|---|---|---|
| Live | 97.83 / 91.45 / 87.03 / 81.9 / 76.68 / 71.02 / **66.87** | 97.4 / 90.8 / 86.12 / 78.98 / 74.17 / 70.03 / **66.07** | 98.35 / 90.0 / 84.58 / 79.88 / 75.35 / 70.85 / **67.65** |
| PP (own phase QTE) | 97.6 / 87.49 / 84.63 / 75.73 / 67.62 / 61.41 / **62.15** | 96.85 / 88.34 / 83.58 / 74.02 / 65.02 / 59.01 / **60.0** | 98.75 / 90.24 / 83.83 / 78.43 / 73.92 / 67.17 / **63.7** |
| SP (PP + spirit x1.20) | 97.75 / 88.59 / 86.09 / 78.23 / 70.07 / 64.36 / **64.07** | 97.25 / 89.04 / 84.33 / 75.23 / 67.52 / 61.76 / **61.4** | 98.75 / 90.49 / 84.43 / 78.88 / 74.32 / 68.52 / **65.27** |
| CTRL (presses, turn avg) | 97.95 / 90.29 / 86.74 / 79.73 / 73.37 / 66.52 / 65.4 | 97.0 / 89.24 / 84.83 / 77.03 / 70.72 / 65.82 / 63.72 | 98.7 / 90.54 / 84.78 / 79.43 / 75.18 / 69.67 / 66.45 |

Boss: weak at floor / weak at max / strong at max:

| | Street | Wangan | Touge (what-if) |
|---|---|---|---|
| Live | 2.28 / 32.63 / 94.5 | 1.55 / 35.9 / 89.6 | 2.88 / 38.57 / 94.77 |
| PP | 0.45 / **19.3** / 94.27 | 0.12 / **21.65** / 88.85 | 0.52 / **23.87** / 94.33 |
| SP | 0.5 / **20.75** / 94.45 | 0.15 / **22.93** / 89.32 | 0.75 / **25.28** / 94.68 |

Strong player sweeps 8.5 / 8.6 / 7.3 % of boss turns (about 2.5 of 30); weak at max sweeps 6.5 / 5.6 / 5.0 %.

**Criteria:**
- **Boss band 66-68 (G1a 65-70): FAILS** in every district for PP (62.15 / 60.0 / 63.7) and SP (64.07 / 61.4 / 65.27; only
  Touge SP is inside G1a, and still below 66).
- **Strictly falling ≥ 3.0 per step (G3c): FAILS** Street and Wangan. PP: Street kid2 -> mat1 2.86, oh2 -> boss -0.74
  (inverted); Wangan oh2 -> boss -0.99 (inverted). SP: Street 2.50 and 0.29; Wangan 0.36. **Touge holds** (smallest step
  PP 3.47, SP 3.25).
- **G2a (weak at max ≥ 30): FAILS** in all three (19.3-25.3).
- G3b (≥ +10), G4a, G4b (≤ 10), G5 (≤ 95): **hold** in all variants.
- **Reading gap** (boss: strong at floor - weak at max): Live 34.2 / 30.2 / 29.1 -> PP 42.9 / 38.4 / 39.8 -> SP
  43.3 / 38.5 / 40.0. Per-phase widens it by about 9-11 pp; spirit adds only 0.1-0.4 on top.

**Why:** CTRL shows about 1.5-2.5 pp of the strong-boss drop is single-press noise. The rest (2-3.7 pp strong, about 8-10
weak) comes from scoring each clash on its own press: tau is concave, so press-to-press spread costs more than an averaged
score does. The AI's spread (sd 0.08) is far smaller than a 60/60 player's, so per-phase hurts weak readers most. The press
sigma is a PLACEHOLDER until playtest, so the size of this effect depends on it.

**Spirit:** it lifts strong players by +1.5-1.9 pp at the boss and weak players at max by +1.3-1.4. It's real but small,
the same finding as the cut spirit-meter-v1 (Austin 2026-11-18: "it doesn't add anything"). A second variant, not run:
"sweep bank" (each sweep +1 spirit; at 2 spirit, x1.25 for 2 turns, then reset). That pays more, but snowball risk is
higher at the bosses.

## 4. Retune it would need (estimate only, not run)

Slopes from the live table near the boss (Street floor -> max: +4.1 % r moves strong +27.6 pp and weak +30.4 pp, about
6.7 / 7.4 pp per 1 % r):
- **Boss band back to 66-68:** boss budgets about -0.7 % (Street, Touge) and -1 % (Wangan).
- **G2a ≥ 30:** +8 to +11 pp for weak at max, about -1.1 to -1.5 % boss budget. That overshoots the strong band (+7-10 pp),
  so stats alone can't fix both. It needs a timing lever for per-phase districts too, such as a wider zone
  (`qte_window_mod`) or lower press sigma, which helps weak readers most.
- **Ladder:** oh2 is now above the boss in Street and Wangan; oh2 budgets need about -1.5 to -2 % relative to the boss,
  and Street kid2 / mat1 need about 0.3 % separation.
