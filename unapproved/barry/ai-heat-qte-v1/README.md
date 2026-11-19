# ai-heat-qte-v1 (Barry DRAFT, 2026-11-19, unapproved)

Austin's two asks, relayed by Gordon on 2026-11-19: "making sure his sims run heat in the opponents as well" and
"capping opponents QTE scores, as a 100% perfect QTE every time will not be fun". Nothing live is changed: no edit to
`equations.py` or any file in `sim/`. The script swaps the AI's QTE and heat rules in-process only.

## 1. Opponent heat: yes, it runs. Same gauges, but not the same rules as the player

The AI runs heat in every sim race, through the same `HeatGauges` class as the player:
- `sim/velocity_shift/match.py:83-84` builds both sides' gauges (`for_player` and `for_boss`).
- `match.py:117-118`: the AI plays each clash through `o_heat.play()`, which adds load, applies overrun, locks a full gauge, and limps when all three are locked.
- `match.py:139-140`: both sides get `end_turn` (passive corner load, recovery, release).
- `match.py:169-170` and `combat.py:101-104`: both sides' heat multipliers scale their clash payoff.
- Overrun and limp are identical for both sides: `heat.py:187-191` and `heat.py:213-223` (`overrun_mult`, `LIMP_MULT 0.4`).

There are four differences, all deliberate (the "v3 boss" rules, marked PLACEHOLDER in `equations.py:274-279`):

| Rule | Player | AI | Where |
|---|---|---|---|
| Release (a locked gauge unlocks below this share of capacity) | 0.3 | **0.8** | `equations.py:268` vs `:278` |
| Passive corner load can lock a gauge | yes | **no** | `heat.py:143`, `:230`; `equations.py:279` |
| Capacity and recovery scale with r | r = player total / AI total | **r = 1** | `heat.py:156-163` |
| Stance choice under heat | reads the line and paces (reserve rule) | **plays its line stance; if that gauge is locked, plays the least-loaded unlocked one** (no pacing) | `heat.py:238-245`, `simulation.py:9-19` |

**Effect of switching the AI to the player rules** (measured, AI QTE still 1.0): bosses get far easier. At 60/60, Street goes 32.2 → 69.7, Wangan 38.7 → 90.4, and Touge 30.9 → 91.2. The cause is that an AI that can't pace keeps running into locked gauges and limps. On the parity test race at r = 1 the effect is small: the mirror match goes 0.6 → 3.3 at 60/60 and 40.7 → 47.9 at 80/80. Tables in §3.

**Proposal (draft):** keep AI heat on with the current AI rules. They exist so that an AI that never paces still holds up under heat. If Austin wants exact rule parity, the AI also needs a pacing rule (a new AI behaviour; that means engine work in Godot, Gordon/Desmond), and every boss r would have to be retuned. That was not simmed here.

Side note: `MatchConfig.opponent_qte_ratio` (`models.py:168`) is never read by the live engine. `match.py:168` always passes `OPPONENT_QTE` (`equations.py:133`, 1.0). The parity blocks' `"opponent_qte_ratio": 1.0` therefore has no effect.

## 2. AI QTE options (simulated)

The AI's per-turn raw QTE replaces `OPPONENT_QTE` (live is 1.0 every turn). Draws come from a seeded RNG separate from the match RNG and are rounded with `round_qte_score`. The simulated player's own read of the AI uses the option's mean.

| Option | Rule | Boss 60/60 (St / Wa / To) | Boss 80/80 (St / Wa / To) | Test race mirror 60/60 / 80/80 |
|---|---|---|---|---|
| Live | 1.0 every turn | 32.2 / 38.7 / 30.9 | 94.7 / 91.4 / 92.8 | 0.6 / 40.7 |
| **A. Fixed cap 0.90** (F90) | 0.90 every turn | 46.9 / 49.6 / 46.1 | 97.8 / 94.4 / 96.5 | 1.4 / 56.7 |
| **B. Seeded spread, mean 0.90** (D90) | per turn N(0.90, 0.07), clamped to 0.70-1.00 | 46.7 / 49.5 / 46.3 | 97.7 / 94.3 / 96.4 | 1.4 / 56.5 |
| C. Fixed cap 0.85 / spread mean 0.85 (F85 / D85, N(0.85, 0.08), clamped to 0.65-0.98) | | 53.6 / 53.8 / 52.8 | 98.5 / 95.2 / 97.4 | 2.1 / 62.9 |
| D. AI uses the player's skill model (SK90): times like a 0.9-skill player on its own visible zone | about 0.71-0.74 vs bosses, 0.825 at parity | 67.7 / 66.4 / 71.5 | 99.3 / 97.3 / 99.2 | 2.4 / 66.0 |

Also measured (full tables in `tables.md`): F95, F80, F70, F60, SK80, and the off-tune test-race pairings.

Readings:
- At the same mean, a spread gives the same win rate as a fixed cap (B ≈ A within 0.3 pt). The spread only changes how it looks: the AI sometimes misses and sometimes nails it.
- Every cap makes bosses easier. 60/60 rises 8-16 pt per 0.05 cut, and 80/80 crosses the 95 % ceiling on Street and Touge from 0.90 down.
- **The parity test race barely moves at 60/60.** Even a 0.60 cap only lifts the mirror match to 13.0 %. The bigger driver is the player's own timing. At r = 1 the visible zone is 0.57 × default, so a 60/60 player's expected raw QTE is 0.402 and an 80/80 player's is 0.652 (`raw_qte_score(1.0, q_time)`). An AI cap alone won't make parity races winnable for an average player.
- The parity blocks aren't balanced on Touge tracks. A Touge-tune car vs a Wangan-tune car wins 0.0 / 10.8 % (60/60 / 80/80); reversed, 6.7 / 69.8 %. That's relevant to the car-select screen in `touge-race-parity`.

## 3. Recommendation (draft for Austin)

**Option B: a seeded spread, mean 0.90, sd 0.07, clamped to 0.70-1.00, drawn once per turn from its own seeded RNG.** It plays the same as a 0.90 cap, but the AI visibly misses sometimes, which answers "not perfect every time". Use one value for every rung for now. A per-rung ramp (for example a lower mean on early rungs, rising to 0.90 at the boss) is possible, but no rung below the boss was simmed. It would need the progression win-rate oracle (`sim/config/winrate_g2_live_tracks_v1.json`, built at AI QTE 1.0) regenerated first.

**Retune knock-on (measured, Option B, boss r scan):**

| District | Live r | Under B at live r (60/60 / 80/80) | r that holds 30 / 95 | Result |
|---|---|---|---|---|
| Street | 1.044 | 46.7 / 97.7 | none found: 1.036 → 30.9 / 96.4, 1.032 → 22.6 / 95.1 | **fails on r alone**; needs another knob |
| Wangan | 1.0548 | 49.5 / 94.3 | live r holds (tight); 1.050 → 44.4 / 93.0 | OK |
| Touge | 1.0702 | 46.3 / 96.4 | 1.066 → 31.3 / 92.9 (1.064 → 29.4 / 91.7, 1.068 → 44.2 / 96.2) | OK at about 1.066 |

Street was already tight at 94.7 with a perfect AI, and a 0.95 cap doesn't hold either (1.040 → 31.8 / 96.2, 1.036 → 25.2 / 93.7). Any AI QTE cap therefore means moving the boss ceilings (r) and finding a second Street lever (for example kappa, the Street boss's own QTE mean, or the Street tune). That would be a follow-up sim after Austin picks an option. Ceilings and r stay as they are until then.

## Reproduce
Run from this folder (8 cores, about 6 min total). n = 6,000 per cell (boss: 2,000 per style × 3 styles; test race: 400 per track × 5 Touge tracks × 3 styles); SE ≤ 0.65 pt.
```
python3 ai_heat_qte.py touge 400
python3 ai_heat_qte.py boss 2000
python3 ai_heat_qte.py touge 400 F70,F60,SK90,SK80
python3 ai_heat_qte.py boss 2000 SK90,SK80
python3 ai_heat_qte.py rscan 2000 D90 '{"street":[1.028,1.032,1.036],"wangan":[1.046,1.050],"touge":[1.052,1.058,1.064]}'
#   rscan.json here also merges D90 touge [1.066,1.068] and F95 street [1.036,1.040] (each rscan run overwrites rscan.json)
python3 make_tables.py
```
The boss cells match the live check (`unapproved/barry/mod-skill-v1/boss_engine_check.py`): the same seeds, the hardest track per district, 30 turns, 3 boss styles, the fixed layout at the round cap, and ties counted as half. The baseline reproduces 32.2 / 94.7, 38.7 / 91.4, and 30.9 / 92.8 (live check: 32.3 / 94.7, 38.8 / 91.0, 30.7 / 92.7). The test race uses the `touge-race-parity` v3 blocks (3,000 points; points / 10 = stat units), 10 turns, no mods, all 5 Touge tracks. Pairings: brz vs mx5 (Touge-tune mirror), brz vs gr_corolla, and gr_corolla vs brz.

Files: `ai_heat_qte.py` (runner), `make_tables.py`, `boss.json`, `touge.json`, `rscan.json`, `tables.md`.
