# Skill-tree sim results (thought experiment, unapproved)

Code: `sim/` (copies of the mod-skill-v1 and spirit-meter-v1 code; live `sim/velocity_shift/` is not changed). Output: `run1.json`, `calib.json`, `run2.json`, `run3.json`, `run3_matched.json`, `run4.json`.
How: paired seeds, ties count as half a win, averaged over the 3 boss styles. Bosses and all Touge races use the hardest track; other races use the 5-track district mean. Win % for 60/60, 80/80 and the reading curve (s = 0.6 + 0.2·j/6 per rung).
`st_match.py` adds the driver tree and carry state to the spirit match path. Identity check: with no driver it matches SpiritRunner on 0/90 mismatches.

## Placeholders [PH]
- **Driver points:** floor(3 + 2·√L). This is front-loaded: L0 3, L12 9, L29 13, L64 19.
- **Builds use DRIVER_TREE node values:**
  - R1: Steady hands (QTE window +0.05), Cool down (release +0.05), Fired up (fill +1).
  - R2: adds Hold it (+1 buff turn) and Kindling (loss fill 0.4).
  - R3: adds In the zone (window +0.10 total).
  - Finale: adds Second wind (+1 activation in long races).
  - Not simulated: Ride the edge, Scout, Feather.
- **Run 1, B stock:** 3266 / 3788. That is the previous cap minus half the previous tier's earned room.
- **Run 2, stakes bonus:** b = 0.5963 (`calib.json`). This matches the mean progress that ×1.25 adds on buff turns (curve player, story and mixed walks, hard track). On a buff turn a won clash pays ×1.596, a tie ×1 and a lost clash ×0.404.
- **Run 3:**
  - Layout: 2 opening road races, then k crews of 2 lieutenants (20 turns) and a crew boss (30 turns), with m road races (10 turns) before each crew after the first.
  - Opponent targets: roads use the kid targets. Lieutenants go from the mat1 to the oh2 target. Crew bosses use the boss target.
  - XP per win comes from today's story XP by race type. A loss gives 0 XP.
  - "Matched" budgets mean B = the car's expected power ÷ target.
- **Run 4:** one-car tune (0.40, 0.25, 0.35); the curve is shown at s = 0.7. Note that the per-rung curve reaches 0.8 at a boss, the same as 80/80.

## 1. Next-tier stock (table model, no spirit or driver)
- **A (new stock = previous cap, 3532 / 4044), story-only:**
  - R2 curve: 32.6, 54.5, 30.5, 30.8, 38.5, 53.9, 68.2 (boss). 80/80 range 63.8–91.0.
  - R3 curve: 13.6, 29.9, 29.7, 22.2, 32.1, 52.6, 62.2. 80/80 range 57.5–81.5.
  - 60/60 is 1–45 (the gym needs grinds).
- **B (3266 / 3788):**
  - R2 curve: 0.0, 7.7, 9.5, 17.3, 23.8, 36.8, 46.0. 80/80 range 16.4–56.2, boss 46.0.
  - R3 curve: 0, 3.7, 10.6, 12.0, 18.7, 37.3, 44.1. 80/80 boss 44.1.
  - Without catch-up, the R2 boss for 80/80 is 1.1.
- **Old car's mods in B:** they matter for the first 2 races only.
  - R2 kid1 with the old car: 24.2 (60/60) / 81.5 (80/80) / 24.2 (curve), against 0–16 for the new car.
  - From mat1 on, the old car is worse (80/80 10.5).
  - Driving the old car means the new car earns no XP.
- **Recommendation: A.** B breaks the story-only 80/80 ≥ 50 check (lows 44.6 in R2, 36.8 in R3), and its only effect is an early-race dip plus an awkward choice between the old and new car.

## 2. Spirit buff: ×1.25 payoff vs additive stakes (driver build on in both)
- **Mean spirit delta in win-% points** (over the driver-only result):

  | Race set | Mult (60/60 / 80/80 / curve) | Stakes (60/60 / 80/80 / curve) |
  |---|---|---|
  | Story | +3.2 / +6.2 / +7.6 | +3.5 / +5.7 / +7.6 |
  | Mixed | +7.6 / +3.0 / +7.7 | +7.2 / +2.5 / +6.8 |
  | Cap bosses | +6.6 / +0.9 | +6.3 / +0.8 |

  - The driver tree alone adds: story +1.4 / +3.5 / +4.1; mixed +4.8 / +2.9 / +4.9; cap +8.0 / +1.5.
  - The biggest per-race spirit gains are at kid races (+10–14). They are smallest at bosses for 80/80 (+0.5–1.0).
- **Cap bosses (60/60 / 80/80)** — gap is 80/80 − 60/60:

  | District | None | Driver | Driver + mult | Driver + stakes | Gap: none → mult / stakes |
  |---|---|---|---|---|---|
  | Street | 31.2 / 95.3 | 39.9 / 96.0 | 45.1 / 96.7 | 46.6 / 97.0 | 64.2 → 51.6 / 50.4 |
  | Wangan | 40.8 / 91.3 | 47.8 / 93.7 | 53.4 / 94.8 | 51.0 / 94.4 | 50.5 → 41.4 / 43.4 |
  | Touge | 30.1 / 94.1 | 38.3 / 95.6 | 47.4 / 96.7 | 47.4 / 96.4 | 64.0 → 49.3 / 49.0 |

  - 60/60 ≥ 30 passes everywhere.
  - 80/80 ≤ 95 fails on Street and Touge in every variant that includes the driver tree, because the driver tree alone pushes them over.
- **Recommendation:** the two buffs are within noise (≤ 1 point, cap SE about 1). Keep ×1.25 because it is simpler to explain.
  - Retune boss r with the driver tree and spirit on. 60/60 now has 15–23 points of headroom above 30, so Street and Touge bosses can be made harder until 80/80 is 95.
  - The snowball shrinks (gaps around 41–52) because 80/80 is saturated.

## 3. Gym structure (k crews, m mandatory roads between crews; table model plus run-2 deltas)
- **Today's per-race XP:** the share of the tier room reached before the round boss (R1 / R2 / R3):
  - k1 m1: 0.59 / 0.51 / 0.54
  - **k2 m1: 1.22 / 1.04 / 1.03**
  - k2 m2: 1.47 / 1.21 / 1.20
  - k3 m1: 1.86 / 1.57 / 1.51
  - k4 m4: up to 4.7
  - Only **k2 m1** (9 races per round) lands on the caps without grinds. R1 over-lands by 22%, so trim R1 XP by about 18% [PH].
- **With today's budget rule (B = C_ROUND ÷ target)**, a story-only car is under-powered mid-round:
  - The k2 m1 crew-1 boss is at r about 0.97–1.01: 60/60 0%, 80/80 18–34%.
  - The expected attempts are unbounded (`run3.json`).
  - So "mandatory loss blocks + no grinds" does not work under the current budgets.
- **Matched budgets (B = expected car power ÷ target), 60/60 with driver + spirit, expected attempts:**
  - k2 m1: 1.32 / 1.31 / 1.40 per race (max 2.1 at the bosses), **11.9 / 11.8 / 12.6 per round**.
  - Without driver or spirit: 1.61 / 1.53 / 1.82 per race (max 3.2), 14.5 / 13.8 / 16.4 per round.
  - More crews or roads only add races: k3 m1 17–18 per round, k4 m4 31–33 per round.
  - Boss checks match the cap results (no driver or spirit: 31.6 / 94.9, 39.7 / 90.7, 31.9 / 93.5).
- **Recommendation: 2 crews per round with 1 mandatory road race between them** (9 mandatory races), on matched budgets, with optional grinds kept as a catch-up.
  - A 60/60 player needs about 12 attempts per round (about 1.3 per race, about 2 per boss).
  - Watch item: each round has two boss-level walls. Consider putting the crew-1 boss at the oh2 target [PH].

## 4. Myth finale gauntlet (spirit A + driver build 4; r 1.075 / 1.058 / 1.044; 30 turns × 3)
P(clear all 3) as %, with per-race win % in brackets:

| Profile | On-tune, no carry | On-tune, carry | One car, no carry | One car, carry |
|---|---|---|---|---|
| 60/60 | 22.5 [62/62/59] | 9.0 [62/49/26] | 9.7 [52/37/50] | 2.8 [52/19/20] |
| 80/80 | 90.5 [98/95/98] | 72.3 [98/88/84] | 77.3 [90/89/96] | 52.8 [90/65/85] |
| Curve (s 0.7) | 64.3 [88/84/90] | 38.2 [88/71/58] | 44.7 [79/68/84] | 22.0 [79/42/55] |

- Carry (heat and meter state) is a net loss: carried heat hurts more than the carried meter helps.
- **For a 50% curve clear** (one car, carry), scale all r by about ×1.025: 45.0 at ×1.02 and 65.0 at ×1.04, so r is about 1.102 / 1.084 / 1.070.
  - Per-race win needed is about 79% on average, which matches 0.5^(1/3) = 79.4% for independent races. The measured split is about 92 / 66 / 77.
  - With one car and no carry, today's r already gives 44.7.
- **Caveat:** these r values are held fixed. A single car at fixed power against the rising FINALE budgets (494.8 / 566.3 / 648.2) would actually face r of about 1.368 / 1.195 / 1.044, so the budgets need to follow the chosen r.
- **Recommendation:**
  - Reset heat between legs (no carry). Carry the spirit meter only if it is wanted as a reward.
  - Keep r* with one car and no carry (curve about 45%). If heat carry is kept, raise r by about 2.5%.
  - The finale is a skill check: 60/60 3–23% vs 80/80 53–91%.
