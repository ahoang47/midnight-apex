# Skill Parity: play quality, stat gap and win rate

> **HISTORY (2026-11-13):** `sim/scripts/parity_sweep.py` was removed with the card draw and the legacy HP/DP match path. Numbers below are from that old engine. Current targets and checks: `design/02-equations-reference.md` (heat/load section) and `sim/scripts/balance_gauntlet.py`.

> Author: Barry (Chief of Systems), 2026-11-02. **Source of truth: `sim/scripts/parity_sweep.py`.** Every figure below is from a run of that script on 2026-11-02 (commands in §7). If the engine changes, re-run it; don't edit numbers here by hand.
> Status: measurement plus **PROPOSALS**. No game constant in `sim/velocity_shift/equations.py` was changed. The only engine changes are opt-in: `MatchConfig.player_quality`, `MatchConfig.opponent_qte_ratio`, three new player-QTE constants and `RUBBER_BAND_FRACTION` (same value, moved out of `match.py`).

## 1. Target (Austin, 2026-11-02)

"I want the feel of a challenge near stat parity, so as a spitball only if you play a race 90% right would you be able to win."

Working success criterion: **at stat parity, q50 ≈ 0.9**, where q50 is the play quality at which the player wins half their races.

Context: skill points are in v1. Races 1–3 are scripted and use skill points only, Reiko's mods unlock when the PC wins race 3, wholesale at the end of Round 1, aero when the debt hits zero, and betting at the end of Round 2 (see 01). Skill points and mods should both be expressible as a stat shift in the equation in §4. That supersedes "No skill trees in v1" in `design/godot-build-guide.md` and the "deferred" status in `design/05-skill-trees.md`.

## 2. Definition of play quality q

q in [0, 1] is the fraction of the race the player "plays right" (`sim/velocity_shift/simulation.py`, constants in `equations.py`):

- **Card read (each clash).** With probability q, the player reads the AI's real pick and plays the card that beats it. If that card isn't in hand, they play the same stance (a tie), and if they don't have that either, any card. Otherwise they play a random card from hand.
- **QTE (each turn).** With probability q, the QTE is perfect (`PERFECT_QTE` = 10). Otherwise it's uniform between `PLAYER_QTE_MIN` and `PLAYER_QTE_MAX` (1–10).
- **q = 0** is exactly the old random sim player. With `player_quality=None` (the default) the runner behaves exactly as before.

A "read" stands in for the whole tell system (faces, car motion, lies), which the sim doesn't model. q = 0.9 means: right on 9 of 10 clashes and 9 of 10 QTEs.

How the read works: the AI's pick never depends on which card the player chooses, because it sees the player's whole remaining hand. So the runner makes the AI's pick first, caches it, and gives the same card to the AI callback.

## 3. Measured: current constants

**Configs.** `parity_<enc>` means same level, AI QTE ratio 1.0, and that encounter's turn count and phases (Wild 10 turns, Lieutenant 20, Boss 30). `game_<enc>` is today's rule (`cli.py:305`): opponent level **and** AI QTE both × `ENCOUNTER_RATIOS`.

**Pooling.** Each cell pools all 25 archetype pairs (player × opponent, 5 mirrors) × 80 seeds, so **N = 2000** (about ±2.2 percentage points at 50%, 95% CI).

### 3.1 Win rate vs q at stat parity (pooled over levels 10/30/50/80, N = 8000 per row)

| q | 0.0 | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 | 1.0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| parity_wild | 9.1 | 23.8 | 44.6 | 65.7 | 83.4 | 92.4 | 96.9 | 98.7 | 99.4 | 99.8 | 100 |
| parity_lieutenant | 6.1 | 18.9 | 44.1 | 69.9 | 87.8 | 95.2 | 98.2 | 99.2 | 99.8 | 100 | 100 |
| parity_boss | 4.0 | 12.2 | 32.0 | 63.1 | 85.0 | 94.1 | 97.7 | 99.0 | 99.8 | 100 | 100 |

**q50 at parity is 0.21–0.27**, at every level and encounter length:

| | L10 | L30 | L50 | L80 |
|---|---|---|---|---|
| Wild | 0.212 | 0.221 | 0.230 | 0.244 |
| Lieutenant | 0.214 | 0.218 | 0.229 | 0.242 |
| Boss | 0.253 | 0.255 | 0.261 | 0.271 |

**Gap to target: about 0.65 of q.** At parity today, a player who plays right one time in four wins half their races, and anything over q 0.5 wins about 95%.

Per archetype pair (L50, N = 400 per pair per q), q50 ranges from **0.01 to 0.48** at Lieutenant length (median 0.21). Aggressive-as-player is easiest (vs Defensive 0.009). Aggressive-as-opponent is hardest (Defensive vs Aggressive 0.472). POW dominates.

### 3.2 Today's encounter rules (stats and QTE both scaled)

| | q50 L10 | L30 | L50 | L80 | win% at q=0 | at q=0.9 |
|---|---|---|---|---|---|---|
| game_wild (×0.75) | 0 | 0 | 0 | 0 | 99.9 | 100 |
| game_lieutenant (×1.1) | 0.528 | 0.522 | 0.512 | 0.512 | 0.1 | 98.1 |
| game_boss (×1.2) | 0.827 | 0.823 | 0.822 | 0.814 | 0.0 | 73.5 |

(The win% columns are pooled over levels.) The double-scaled ratio (level and QTE) is what makes Boss hard today. Wild can't be lost.

## 4. The skill parity equation

Fitted by binomial maximum likelihood over q 0–1 (step 0.1) × opponent/player level ratio r 0.7–1.4 (step 0.1), at L50, AI QTE ratio 1.0, **N = 1000 per cell**, 88 cells per encounter:

    P(win) = 1 / (1 + exp( -( a·(q - q0) - b·ln r ) ))

where r = opponent level / player level. Stat totals and HP both scale with level (`cars.build_stats`, `HP_PER_LEVEL`).

| fit | a | q0 | b | RMS error | max error |
|---|---|---|---|---|---|
| parity_wild | 8.83 | 0.217 | 18.30 | 1.8 pts | 6.9 pts |
| parity_lieutenant | 10.49 | 0.214 | 26.18 | 2.0 pts | 7.1 pts |
| parity_boss | 10.68 | 0.236 | 29.30 | 3.9 pts | 18.8 pts |
| pooled (all three) | 9.35 | 0.221 | 22.72 | 6.3 pts | 27.3 pts |

Use the per-encounter fits. The pooled fit is too loose, because longer races are less random. The boss fit's worst cells are at high r with q near 1, where the measured curve flattens: at r = 1.4, q = 1.0 wins only 28.1%.

**Reading it.** The 50% line is **q50(r) = q0 + (b/a)·ln r**. b/a is 2.07 for Wild, 2.50 for Lieutenant and 2.74 for Boss. So at Lieutenant length, **a 10% stat edge for the opponent costs the player about 0.24 of q**. Measured q50 by level ratio (Lieutenant length): 1.0 → 0.230, 1.1 → 0.449, 1.2 → 0.668, 1.3 → 0.856, 1.4 → never reaches 50%.

**Skill points and mods** enter as a change to r. Put the player's effective stat total in the denominator, r = opponent stat total / (player stat total + skill/mod stat). The fit was made by moving **levels**, which moves stats and HP together. A bonus to stats alone (no HP) may be worth a different amount. That needs its own sweep once the skill-point and mod formats are defined (see §6).

## 5. Levers: what moves q50 (parity_lieutenant, L50, N = 2000 per q)

All prototyped in the script only (scratch patches in worker processes). **Not applied to `equations.py`.**

| change | q50 | win% q=0.8 | q=0.9 | q=1.0 |
|---|---|---|---|---|
| current | 0.230 | 100 | 100 | 100 |
| AI QTE ratio 1.2 (QTE 8.4) | 0.375 | 99.9 | 100 | 100 |
| AI QTE ratio 10/7 (QTE 10, the cap) | 0.521 | 95.8 | 99.3 | 100 |
| CLASH_STAKES 0.35 → 0.20 | 0.264 | 100 | 100 | 100 |
| CLASH_STAKES 0.35 → 0.60 | 0.195 | 100 | 100 | 100 |
| BATTLE_BONUS 0.05 → 0.20 | 0.224 | 100 | 100 | 100 |
| RUBBER_BAND_FRACTION 0.15 → 0.50 | 0.228 | 100 | 100 | 100 |
| RUBBER_BAND_FRACTION 0.15 → 0.05 | 0.231 | 99.9 | 100 | 100 |
| AI read 0.30 | 0.417 | 98.2 | 99.8 | 100 |
| AI read 0.50 | 0.583 | 86.8 | 94.5 | 98.8 |
| AI read 0.70 | 0.774 | 52.9 | 70.8 | 85.6 |
| AI read 0.80 | 0.898 | 34.1 | 50.3 | 68.8 |
| AI read 0.85 | 0.961 | 26.5 | 39.5 | 57.8 |
| AI read 0.30 + AI QTE 10 | 0.779 | 54.8 | 75.0 | 88.2 |
| **AI read 0.40 + AI QTE 10** | **0.893** | 31.9 | 51.5 | 71.7 |
| AI read 0.60 + AI QTE 8.4 | 0.913 | 29.8 | 47.0 | 66.2 |
| AI read 0.50 + AI QTE 10 | never 50% | 15.7 | 28.2 | 47.3 |

**AI read r_ai** is a prototype lever. Each clash, with probability r_ai, the AI swaps its pick for the card that beats the player's actual card, if it has one. That overrides the pick the player read. In game terms it's "the opponent reads you back": a bluff the player can't catch. CLASH_STAKES, BATTLE_BONUS and the rubber band barely move q50. The player's edge comes from out-reading an AI that already plays its expected value against the player's hand, plus out-QTEing an AI fixed at 7.

**Checked across all levels and encounter lengths (parity, N = 1000 per q):**

| candidate | q50 range over Wild/Lt/Boss × L10/30/50/80 |
|---|---|
| AI read 0.80 | 0.835–0.963 (drifts with level) |
| **AI read 0.40 + AI QTE 10** | **0.874–0.916** (flattest) |
| AI read 0.60 + AI QTE 8.4 | 0.896–0.938 |

## 6. PROPOSALS (for Austin, not applied)

1. **Hit q50 ≈ 0.9 at parity with AI skill, not AI stats:** AI QTE at the cap (TYPICAL_QTE 7 → 10, or ratio 10/7) plus an AI read rate of 0.40, as a new constant `AI_READ_RATE`. That needs a real engine hook in `ai.py` or `match.py` and a matching tell rule in Godot (Desmond). Measured: q50 0.874–0.916 everywhere. The trade-off: a flawless player (q = 1.0) wins only 63–87%, and q = 0.8 wins 21–36%.
2. **Encounter tiers then move r_ai and r instead of double-scaling QTE.** With the AI QTE at the cap, `ENCOUNTER_RATIOS` can't push QTE higher, so tiers would scale AI read rate and/or level ratio. Per §4, each +10% opponent level adds about 0.24 to q50 at Lieutenant length, so tiers above parity would need small level gaps (Wild below parity, Boss just above). This ties into the pending encounter-scaling fix.
3. **Archetype matchups need their own pass.** At parity, q50 spans 0.01–0.48 by pair, so Aggressive is over-tuned against everything.
4. **Skill points and mods:** once their stat format is set, re-run the gap sweep with stat-only bonuses (not levels) to get their exchange rate in q.

## 7. Reproduce

From `sim/` with the venv:

    python3 scripts/parity_sweep.py all --seeds 80 --out results.json   # curve (N=2000), pairs (N=400), gap (N=1000), levers (N=2000)
    python3 scripts/parity_sweep.py fit --in results.json                # refit §4 from saved results
    python3 scripts/parity_sweep.py validate --seeds 40 --ai-read 0.4 --ai-qte-ratio 1.4285714285714286

`all` takes about 15 minutes on 8 workers. Each `validate` takes about 70 seconds.

**Known limitations.** The sim has no tells, lies or track corners, so q is an abstraction. The player deck never reshuffles (192 cards at 6 per turn is 32 turns, enough for 30-turn Boss races). Win means a higher position at the final turn.
