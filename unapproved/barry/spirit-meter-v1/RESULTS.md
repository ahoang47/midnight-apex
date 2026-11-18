> **CUT (Austin 2026-11-18):** spirit meter removed; it does not add anything. Kept for reference only.

# spirit-meter-v1 RESULTS (Barry DRAFT, 2026-11-18, touge-race @ bbdda07, mod_skill)

Every number comes from the scripts in this folder, run on the live match engine (sim/velocity_shift, imported
read-only). Nothing in sim/ was edited. All spirit parameters are PLACEHOLDERS.

## Summary (under 200 words)
A spirit meter hooked onto a copy of the live match path (matches the live runner 120/120 with spirit off).
**Recommended placeholder (A): +25 % clash payoff for 3 turns, 1 activation per race, meter 100, fill 6 per won clash × match
multiplier (k = 1), ties 0.5, losses 0.25.** It adds +5.5 pp per story race for the reading-curve player. Story-only 80/80 low
goes 49.3 → 56.2, and capped bosses gain +5.1 to +6.0 at 60/60. One activation is worth about 5-6 pp in the mid range and
about 1.3 pp near the ceiling. **No snowball:** the gap widens only where 60/60 sits near 0 (story-only bosses, +3.2) and
shrinks where 80/80 nears 100 (mixed −4.0, cap about −4.5). Free heat is the exception (+10.3). **Criteria:** 60/60 ≥ 30 and
story-only 80/80 ≥ 50 hold. The Street boss 80/80 at the cap goes 94.9 → 96.1, over 95, with every buff. Re-tune only the
Street boss target, 1.044 → about 1.040 (table 93.5 + 1.2 = 94.7; 60/60 26.0 + 6.0 = 32.0). The fill knobs mainly decide who
activates and when, not how much it pays.

## 1. Model (placeholders)
- **Fill:** each executed clash (not limping) adds `base × outcome × mm`. The outcome factor is win 1.0, tie 0.5, loss `loss_frac`.
  The meter doesn't fill while a buff runs.
- **Match (placeholder for skill trees):** `mm = 1 + k × (3 × share of the played stance's stat in the car build − 1)`,
  the same form as `STAT_M_W`. On a 25-50 % band build that is 1 − 0.25k to 1 + 0.5k. The alternative was "the stance fits the
  district tune". It gives the same number here, because every mod_skill build sits on the district tune. The two only differ
  for off-tune builds.
- **Policy:** the sim player activates at the start of the next turn after the meter fills, up to `max_acts` per race.
  Its stance choice ignores the buff (the simple SimulationRunner player).
- **Buffs:**
  - pay: player clash payoff × (1 + a) for `dur` turns.
  - qte: zone width × (1 + a) through `qte_window_mod`.
  - heat: on activation, every gauge empties and unlocks, and played stances add no load for `dur` turns.
- **Races** (mod-skill-v1 `results.json`, recommended config):
  - Story-only and mixed walks, 21 races each, with the walk's r and POW share (HAN 25 %).
  - Bosses at the cap: r 1.044 / 1.0548 / 1.0702, on tune.
  - Each race uses the walk's shown cell: the hardest track for bosses and every Touge race, otherwise the mean of the 5
    district tracks. Results average the 3 boss styles. Ties count as half a win.
- **Profiles** (as in the win tables):
  - c6060 = read, timing and pacing at 0.6.
  - c8080 = all three at 0.8.
  - curve = all three at s = 0.6 + 0.2 × rung/6 (story-only standard reading curve).
- **N** (paired seeds, so the deltas are tighter than the base):
  - Bosses at the cap: 2,400 races per cell (base ±0.5 to ±1.0 pp SE).
  - Story and mixed walks: 900 per race (hard cell 3 × 300, district cell 5 × 3 × 60; base ±1.7 pp SE or better).
  - Stage-2 base values agree with the mod-skill-v1 win tables to a mean |diff| of 1.17 pp (max 3.43, n = 84).

## 2. Screen (screen.json, bosses at the cap, N = 600 per cell): what each knob does
- **Fill knobs (base, match k, loss fraction, meter size) barely move the win %** once the meter fills inside the race,
  because only the buff pays. Base 4 to 16, k 0 to 3 and loss 0 to 1 all land at +4.7 to +7.3 (60/60) and +0.8 to +2.3 (80/80).
  Only the ratio base/size matters, so size is redundant with base.
- **Fill knobs decide WHO gets the buff and WHEN** (fill_turn.json, N = 180), with base 6, k 1, loss 0.25:
  - 10-turn kid race: 60/60 activates in 81 % of races (mean turn 8.5) and 80/80 in 96 % (turn 7.9).
  - With k = 0 those drop to 48 % and 83 %.
  - At base 4 almost no 10-turn race activates (0-3 % with k 0-1).
  - Off-tune Street build in Wangan, 30-turn boss: 60/60 activates in 74 % of races against 95 % on tune.
  - So Austin's "won + matched fills heavy" works mostly through the win term. The match multiplier brings the fill about
    1 turn earlier (k 0 → 2).
- **Buff size × duration is the main knob.** Pay +10 % to +50 % for 2-5 turns gives +1.0 to +21.5 (60/60) and +0.2 to +4.5 (80/80).
  QTE width +25 % to +100 % is weak: +1.0 to +6.7 (60/60), and about +0.2 at 80/80, where timing is already near the top.
  Free heat for 1-3 turns is strong: +12.7 to +18.8 (60/60), +3.5 to +5.5 (80/80).
- **Activations:** 2 per race roughly doubles the gain. More than 2 rarely happens in 30 turns (2.83-2.96 mean even uncapped).

## 3. Final candidates (final.json; meter base 6, size 100, k 1, tie 0.5, loss 0.25)
### Bosses at the mod_skill cap (hardest track, 30 turns, N = 2400 per cell, paired seeds)
| Setting | Street 60/60 | Wangan 60/60 | Touge 60/60 | Street 80/80 | Wangan 80/80 | Touge 80/80 | criteria (table + delta) |
|---|---|---|---|---|---|---|---|
| no spirit (measured) | 32.7 ±1.0 | 38.8 ±1.0 | 31.4 ±0.9 | 94.8 ±0.5 | 91.5 ±0.6 | 93.8 ±0.5 | table: 31.6/39.5/30.3, 94.9/90.6/92.9 |
| A pay.25x3 1act | +6.0 ±0.5 | +5.1 ±0.5 | +5.6 ±0.5 | +1.2 ±0.2 | +1.2 ±0.2 | +1.3 ±0.2 | breaks: Street 80/80 96.1 |
| B pay.25x3 1per10t | +11.5 ±0.7 | +9.0 ±0.6 | +11.0 ±0.6 | +1.8 ±0.3 | +1.3 ±0.2 | +2.1 ±0.3 | breaks: Street 80/80 96.7 |
| C pay.20x3 1per10t | +9.2 ±0.6 | +7.2 ±0.5 | +8.9 ±0.6 | +1.5 ±0.3 | +1.1 ±0.2 | +1.9 ±0.3 | breaks: Street 80/80 96.4 |
| D pay.15x3 1act | +3.1 ±0.4 | +2.9 ±0.3 | +3.7 ±0.4 | +0.7 ±0.2 | +0.8 ±0.2 | +0.9 ±0.2 | breaks: Street 80/80 95.6 |
| E heat x1 1act | +14.0 ±1.1 | +8.1 ±1.0 | +11.9 ±1.1 | +3.7 ±0.5 | +3.6 ±0.5 | +4.0 ±0.5 | breaks: Street 80/80 98.6, Touge 80/80 96.9 |

### Story-only walk (no grinds): 21 races, mean change and lows (pp)
| Setting | mean Δ 60/60 | mean Δ 80/80 | mean Δ curve | 80/80 low (race) | curve low (race) | boss gap 80/80−60/60 Δ | activations 10/20/30-turn (80/80) |
|---|---|---|---|---|---|---|---|
| no spirit | – | – | – | 49.3 (Touge oh1) | 1.4 (Touge kid1) | gap 56.7 | – |
| A pay.25x3 1act | +2.0 | +4.7 | +5.5 | 56.2 (Touge oh1) | 3.3 (Touge kid1) | +3.2 | 0.89/0.97/0.99 |
| B pay.25x3 1per10t | +2.5 | +5.3 | +6.7 | 56.4 (Touge oh1) | 3.3 (Touge kid1) | +5.2 | 0.89/1.45/2.01 |
| C pay.20x3 1per10t | +1.9 | +4.3 | +5.4 | 55.3 (Touge oh1) | 2.9 (Touge kid1) | +4.1 | 0.89/1.45/2.01 |
| D pay.15x3 1act | +1.2 | +3.0 | +3.3 | 54.0 (Touge oh1) | 2.4 (Touge kid1) | +2.0 | 0.89/0.97/0.99 |
| E heat x1 1act | +1.4 | +9.7 | +7.9 | 57.0 (Touge kid1) | 1.7 (Touge kid1) | +10.3 | 0.89/0.97/0.99 |

### Mixed walk (grinds to the targets): 21 races, mean change and lows (pp)
| Setting | mean Δ 60/60 | mean Δ 80/80 | mean Δ curve | 80/80 low (race) | curve low (race) | boss gap 80/80−60/60 Δ | activations 10/20/30-turn (80/80) |
|---|---|---|---|---|---|---|---|
| no spirit | – | – | – | 70.8 (Touge oh1) | 12.6 (Touge kid1) | gap 60.3 | – |
| A pay.25x3 1act | +4.9 | +2.5 | +5.5 | 74.8 (Touge oh1) | 17.6 (Touge kid1) | -4.0 | 0.90/0.99/1.00 |
| B pay.25x3 1per10t | +6.3 | +2.6 | +5.9 | 74.8 (Touge oh1) | 17.6 (Touge kid1) | -8.9 | 0.90/1.51/2.23 |
| C pay.20x3 1per10t | +5.1 | +2.1 | +4.7 | 74.1 (Touge oh1) | 16.8 (Touge kid1) | -7.2 | 0.90/1.51/2.23 |
| D pay.15x3 1act | +2.9 | +1.5 | +3.2 | 73.4 (Touge oh1) | 15.8 (Touge kid1) | -2.5 | 0.90/0.99/1.00 |
| E heat x1 1act | +6.1 | +5.8 | +8.4 | 78.6 (Touge kid1) | 14.7 (Touge kid1) | -7.3 | 0.90/0.99/1.00 |

### Win points per activation (Δ / mean activations)
| Setting | cap bosses 60/60 | cap bosses 80/80 | story 60/60 | story 80/80 | story curve |
|---|---|---|---|---|---|
| A pay.25x3 1act | 5.6 | 1.3 | 2.3 | 5.0 | 6.1 |
| B pay.25x3 1per10t | 5.7 | 0.8 | 2.4 | 3.9 | 5.4 |
| C pay.20x3 1per10t | 4.6 | 0.7 | 1.9 | 3.2 | 4.4 |
| D pay.15x3 1act | 3.2 | 0.8 | 1.4 | 3.1 | 3.7 |
| E heat x1 1act | 11.4 | 3.8 | 1.7 | 10.2 | 8.9 |

The criteria column adds the measured delta to the mod-skill-v1 table values: 60/60 31.6 / 39.5 / 30.3 and 80/80 94.9 / 90.6 / 92.9.
Without spirit, Street 80/80 sits at 94.9, so even D (+0.7) crosses 95.

## 4. Answers
- **One activation is worth:**
  - about 5-6 pp in the mid range: the story curve player, 60/60 on capped bosses, and 80/80 on story-only races near 50 %.
  - about 1 pp at 80/80 on capped bosses (near the ceiling), and about 2 pp at 60/60 on story-only races (near the floor).
  - (A: 6.1 curve, 5.6 cap 60/60, 5.0 story 80/80, 1.3 cap 80/80.)
- **Snowball:** none in the sense of the strong getting stronger. The gap change follows the S-curve: it grows only where 60/60 is
  pinned near 0 (story-only, +3.2 with A) and shrinks where 80/80 is near 100 (mixed −4.0, cap about −4.5). Free heat is the
  exception (+10.3 story). Keep it out, or make it a late driver-tree capstone.
- **Recommended placeholder:** A, +25 % payoff × 3 turns, 1 activation, base 6 / 100, k 1, tie 0.5, loss 0.25.
  - It gives a felt +5 pp for the average (curve) player and +6 at 60/60 on bosses.
  - For a bigger feel, B (one activation per 10 turns) gives +6.7 curve and +11.5 on the Street 60/60 boss, still inside the criteria except Street 80/80.
  - D (+15 %) is too faint (+3.3 curve).
- **Ladder re-tune:** only the Street boss, for the 80/80 ≤ 95 cap: target r 1.044 → about 1.040. From the live table at S1, 30 turns,
  r 1.040 gives 80/80 93.5 and 60/60 26.0. With A's deltas (measured at 1.044) that is 94.7 and 32.0. Note that the 60/60 floor then
  relies on spirit (26.0 without it). Wangan (91.9 with A) and Touge (94.2 with A from the mod_skill 92.9) pass. The other rungs pass
  as they are; re-tune them only if spirit should be absorbed into difficulty rather than felt.
- **Caveats:** the sim player doesn't time its activation or change stances under a buff, so a real player gets a bit more. The
  deltas at r 1.040 are assumed equal to the measured deltas at 1.044. The match placeholder will change once the car tree exists.

## Files
- `spirit_match.py`: the hook. It copies `run_match` with 4 marked SPIRIT hooks, and `SpiritRunner` subclasses SimulationRunner.
- `core.py`: paired batches and `check_identity()`.
- Screens and stages: `screen.py`, `stage2.py`, `final.py`, `fill_turn.py`.
- Summaries: `summarize2.py`, `summarize_final.py` (writes `final_tables.md`).
- Rerun: `python3 screen.py; python3 stage2.py; python3 fill_turn.py; python3 final.py; python3 summarize_final.py` (8 cores, about 12 min).
