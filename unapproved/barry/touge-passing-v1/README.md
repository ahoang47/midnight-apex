# touge-passing-v1: Touge passing, start from the PA (Barry, LIVE for Touge)

> **LIVE 2026-11-20 (Austin, 6:00 PM PT: "Yes, make Touge passing live with these stats."): go-live commit `5c79dea`.** Promoted into
> `sim/velocity_shift/` for **Touge only**: `E.PER_PHASE_DISTRICTS = ("touge",)`, `E.PHASE_SMOOTH_W = 0.35`,
> `E.PLAYER_PRESS_SEED_OFFSET`, `E.sample_press_score`, `E.smooth_phase_qte`, the per-phase path in `match.run_match`, per-clash
> QTE in `combat.resolve_turn` (`p_qte_by_clash` / `o_qte_by_clash`), `TurnResult.player_clash_qte` / `opponent_clash_qte` /
> `phase_order`, `MatchConfig.per_phase` (None = by district; False forces per-turn), and the Touge crew stats of variant I
> (364.96 / 389.10 / 400.41 / 411.94 / 421.80 / 432.32 / 442.14). Street and Wangan stay per-turn. The live
> `experience_gauntlet.py` reproduces the variant I seed-96 row below bit for bit; Street/Wangan are unchanged. This folder's
> `touge_passing.py` is now the historical draft (the live sim is the source of truth). Godot port list: section "Godot port
> (go-live)" just below; the older 10-step list further down is superseded by it.

## Godot port (go-live, for Gordon after Austin tells him)

1. Regenerate `scripts/globals.gd`: `python3 tools/touge_race/gen_globals.py` (sets `PIN_COMMIT` to `5c79dea`). New constants to
   mirror: `PER_PHASE_DISTRICTS` ("touge"), `PHASE_SMOOTH_W` 0.35, and the Touge `MS_CREW_BUDGET` row if Godot reads crew stats.
   The release-0.5 change (`HEAT_RELEASE` 0.3 → 0.5, 68b3fc9) is still unported and lands with the same regeneration.
2. `scripts/race_core.gd` `submit_qte()`: in Touge, score clash i with the smoothed phase QTE
   (Entry = press; Apex = round(0.35 x Apex + 0.65 x Entry); Exit = round(0.35 x Exit + 0.65 x mean(Entry, Apex)), with
   `round_qte_score`), port of `equations.smooth_phase_qte`. Unplayed phase = 0 as today.
3. AI QTE: 3 draws per turn from `o_qte_rng` in Entry, Apex, Exit order (Entry = today's draw), each clamped + rounded, then
   smoothed the same way (`match.py` per-phase block). This changes the AI RNG draw count per turn.
4. Resolve per clash (`combat.resolve_turn` with `p_qte_by_clash` / `o_qte_by_clash`); track order after each phase on the
   running totals (`TurnResult.phase_order`) for the visible pass.
5. Remove the roles and swap: `race_core.gd` `role_first` / `role()` / `swap_after()` / `at_swap()` / banking / `seg_*`;
   `main.gd` ROLE mode and `--role`; `spec/race_config.json` `swap_after_turn`; `hud/turnout_banner.gd`, the role prompt;
   `hud/gap_meter.gd` CHASING/LEADING (whole-race gap). Bump the state token version (it stores `role_first`).
6. PA start: the turnout lot moves to before turn 1 (`track_road.gd`, `touge_dressing.gd`, `turnout_lot.tscn`); visible passing
   replaces `display.json` `visual_gap.touge` (rival keeps its role's side). Presentation details are still open with Austin
   (side by side vs one behind at the roll-out).
7. Rerun parity: `python3 tools/touge_race/parity_touge.py` against `5c79dea` (drop `role_first` from its print/args). Until the
   port lands, Touge parity against the live sim will legitimately FAIL (per-phase vs per-turn); run it against the Godot pin
   instead (`SIM_PATH` = a checkout of globals.gd's `PIN_COMMIT`), the same way the unported release-0.5 change is handled.
   Do not mark parity green against `5c79dea` before the port.

---

> **STALE below as the current state (pre-go-live drafts; the results tables remain the measured record).**


## 2026-11-20 UPDATE (Austin, 5:54 PM PT session: "Let's try it"): w 0.35 + re-pin, rounded and confirmed on 2 seed sets

Austin said "Let's try it" to option 2 smoothing (w 0.35) plus re-pin G, rounded and rerun before calling it final. Still a
draft: sim/ untouched. Runner gained `--touge-budget` (exact Touge crew stats) and `--seed` (base seed; default 96,000,000 as
experience_gauntlet.py; the second set is 97,000,000, disjoint). n = 6,000 per cell on each set.

**Best: variant I** (2 decimals, like live `MS_CREW_BUDGET`). Touge crew stats kid1 .. boss:

| | kid1 | kid2 | mat1 | mat2 | oh1 | oh2 | boss |
|---|---|---|---|---|---|---|---|
| Live | 370.52 | 389.10 | 400.41 | 411.94 | 423.42 | 434.22 | 444.00 |
| G rounded | 364.96 | 389.10 | 400.41 | 411.94 | 421.94 | 432.20 | 442.14 |
| H | 364.96 | 389.10 | 400.41 | 411.94 | 421.80 | 432.45 | 442.14 |
| **I (best)** | **364.96** | 389.10 | 400.41 | 411.94 | **421.80** | **432.32** | **442.14** |

| Goal (target) | G rnd s96 | G rnd s97 | H s96 | H s97 | **I s96** | **I s97** | I margin (worst) |
|---|---|---|---|---|---|---|---|
| G1a boss strong at floor (66-68) | 66.63 | 67.35 | 66.63 | 67.35 | **66.63** | **67.35** | 0.63 (mean 66.99, centred) |
| G1b losses/round, proxy (1.5-4) | 1.85 | 1.78 | 1.86 | 1.78 | **1.86** | **1.78** | 0.28 (live 1.76) |
| G2a min weak at max (>= 30) | 31.35 | 31.83 | 31.35 | 31.83 | **31.35** | **31.83** | 1.35 |
| G2b attempts/round, proxy (<= 60) | 16.36 | 16.28 | 16.36 | 16.29 | **16.36** | **16.28** | 43.6 |
| G3a drop kid1 -> boss (>= 30) | 31.92 | 31.18 | 31.92 | 31.18 | **31.92** | **31.18** | 1.18 |
| G3b boss read gap (>= 10) | 35.28 | 35.52 | 35.28 | 35.52 | **35.28** | **35.52** | 25.3 |
| G3c smallest step (>= 3.0) | 3.43 | **3.00** | **2.95 FAIL** | 3.72 | **3.40** | **3.72** | 0.40 |
| G4a lowest strong at floor (>= 40) | 66.63 | 67.35 | 66.63 | 67.35 | **66.63** | **67.35** | 26.6 |
| G4b boss weak at floor (<= 10) | 0.40 | 0.53 | 0.40 | 0.53 | **0.40** | **0.53** | 9.47 |
| G5 boss strong at max (<= 95) | 94.00 | 94.13 | 94.00 | 94.13 | **94.00** | **94.13** | 0.87 |

Ladders, strong at floor kid1 -> boss | weak at max:
- G rnd s96: 98.55 90.38 84.52 78.2 74.15 70.72 66.63 | 94.43 83.45 89.68 87.08 84.52 68.37 31.35
- G rnd s97: 98.53 90.7 84.58 78.92 74.9 71.9 67.35 | 94.92 84.78 90.55 87.48 84.48 67.9 31.83
- I s96: 98.55 90.38 84.52 78.2 74.43 70.03 66.63 | 94.43 83.45 89.68 87.08 84.65 68.27 31.35
- I s97: 98.53 90.7 84.58 78.92 75.2 71.48 67.35 | 94.92 84.78 90.55 87.48 84.68 67.7 31.83

- **G rounded** passed both sets, but on seed 97 the oh1 -> oh2 step was exactly 3.00. **H** (oh1 easier, oh2 harder) overshot:
  seed 96 oh2 -> boss 2.95 FAIL. **I** splits the difference: steps (mat2 -> oh1, oh1 -> oh2, oh2 -> boss) 3.77 / 4.40 / 3.40
  (s96) and 3.72 / 3.72 / 4.13 (s97).
- **Within ~0.6 of a bound:** G1a sits 0.63 above 66 on s96 and 0.65 below 68 on s97; the band is 2 wide, so the 2-set mean
  66.99 is as centred as it gets. G1b (proxy) is 0.28-0.36 above its 1.5 floor; live Touge is 1.76, so this is not new, and
  raising it means a harder ladder (costs G2a). G5 has 0.87-1.00 of room; lowering it means a stronger boss, which costs G1a
  and G2a. I left both.
- Files: `log_final_s96/97.txt` (G rounded), `log_H_s96/97.txt`, `log_I_s96/97.txt` (+ `res_*.json`). Rerun:
  `python3 run_touge_passing.py --variant w035 --touge-budget 364.96,389.10,400.41,411.94,421.80,432.32,442.14 [--seed 97000000]`

---

> **STALE below (superseded 2026-11-20 by the update above for the re-pin values; the rules spec, port list and flags still
> stand).**


**Ask:** Austin, relayed by Gordon (2026-11-20 5:01 PM PT, his words): "Yes, have Barry spec Touge passing now on that plan."
The plan: the Touge race starts from the PA, there are no cat-and-mouse roles and no turn-5 swap, and passing resolves per
phase like Wangan/Street (design/01, acf9b25). Simmed against the experience goals (design/07 top, G1-G5).

Nothing in `sim/` changed. The variant is opt-in: `touge_passing.py` (a copy of live `match.run_match` at 6b53d74 plus the
per-phase path; `install()` points `velocity_shift.simulation.run_match` at it). Runner: `run_touge_passing.py`, which calls the
live `sim/scripts/experience_gauntlet.py` unchanged (live 0.5 unlock, live crew stats, same seeds, n = 6,000 per cell).
Street and Wangan are untouched (the opt-in only lists Touge), so only Touge was run.
Identity check: with per-phase off, `run_match_pp` gives the live totals bit for bit (Touge boss, seed 96,000,000:
57.39455612382199 / 47.45129698008691 both).

## 1. What the live Touge race does today (read from the repo)

- **Sim:** there are no roles at all. A Touge race is 10 turns, 3 clashes per turn, each turn scored with ONE player QTE (the
  turn's Entry/Apex/Exit mean) and ONE AI draw; the winner is the higher total progress. Heat gauges carry over all 10 turns.
- **Godot (Gordon's touge-race build):** cat and mouse is presentation only (`scripts/race_core.gd:10`, "Purely
  presentational: progress keeps summing"). The player picks "Lead or chase first?" on the parked start line (`main.gd`
  ROLE mode). After turn 5 (`spec/race_config.json` `swap_after_turn` 5) the cars roll through the turnout lot (the PA, a
  roadside parking area, Arthur's approved 16 m `art/kits/turnout_lot`), swap lead and chase, turns 1-5 are "banked" and the
  on-screen gap meter restarts at even. The rival never visibly passes; it stays on its role's side (`display.json`
  `visual_gap.touge`).
- **PA = the turnout parking area** (Gordon README: "Turnout after turn 5 ... a roadside parking area").

## 2. Rules spec (proposal)

1. **Start from the PA.** Both cars start in the turnout lot (the PA) and roll out onto the road before turn 1, even (0-0).
   There is no role prompt and no parked start-line pick. Mechanically the race starts exactly as now: progress 0-0, both
   gauges empty, the same race seed. Who rolls out first is presentation only (open question 3).
2. **No roles, no turn-5 swap, no turnout mid-race.** Nothing is banked; the gap meter and car order show the whole race.
   No sim number depended on the roles or the swap, so removing them changes no number by itself.
3. **Passing per phase, like Wangan/Street.** Each of Entry, Apex and Exit resolves its own clash when that phase ends, and the
   car order after each phase = running total progress, so a car can pass mid-corner. The winner is still the higher total
   progress after turn 10 (exact tie = tie).
4. **Which QTE score each phase uses** (the only rule that moves numbers):
   - Player: one press per phase. Sim player: one press from the live press model, s = max(0, 1 - |e|/a), e ~ N(0, sigma)
     (same E[s] as the live expected score; own RNG, seed + 15,485,863).
   - AI: one N(0.80, 0.08) draw per phase (Entry = today's per-turn draw, then Apex, then Exit, from the same AI RNG), clamped
     and rounded as today.
   - **Option 2 smoothing (w = 0.35, the per-phase-combat-v1 pick, unapproved):** phase score = w x this press + (1 - w) x mean
     of the earlier presses this turn; Entry = its own press. Both sides. **PP** = w 1.0 = each phase on its own press
     (Austin's 6:14 AM rule for Wangan/Street).
5. **Order has no mechanical effect in v1.** Being ahead after a phase gives no draft, defence or line bonus (same as the
   Wangan/Street proposal). Picks are still all made in the SELECT straight before the corner (12 s timer).
6. **Heat:** unchanged. Gauges carry over all 10 turns (as today; the turnout never reset heat).

## 3. Results (experience gauntlet, Touge, n = 6,000 per cell, SE about 0.61 pp at the boss band)

| Goal (target) | Live (per turn) | Passing PP (w 1.0) | Passing w 0.35 | w 0.35 + re-pin G |
|---|---|---|---|---|
| G1a boss strong at floor (66-68) | 66.35 pass | 60.07 FAIL | 61.95 FAIL | 66.65 pass |
| G1b story losses/round, proxy (1.5-4) | 1.76 pass | 2.44 pass | 2.20 pass | 1.85 pass |
| G2a min weak at max (>= 30) | 33.98 pass | 18.18 FAIL | 23.33 FAIL | 31.37 pass |
| G2b attempts/round, proxy (<= 60) | 15.72 pass | 19.26 pass | 17.70 pass | 16.35 pass |
| G3a drop kid1 -> boss (>= 30) | 30.32 pass | 36.52 pass | 34.67 pass | 31.90 pass |
| G3b boss read gap (>= 10) | 32.37 pass | 41.88 pass | 38.62 pass | 35.28 pass |
| G3c smallest step (>= 3.0) | 4.43 pass | -0.03 FAIL | 1.95 FAIL | 3.43 pass |
| G4a lowest strong at floor (>= 40) | 66.35 pass | 60.03 pass | 61.95 pass | 66.65 pass |
| G4b boss weak at floor (<= 10) | 0.52 pass | 0.03 pass | 0.18 pass | 0.40 pass |
| G5 boss strong at max (<= 95) | 92.15 pass | 91.63 pass | 91.77 pass | 94.00 pass |

Strong 80/80 at the floor, kid1 -> boss | weak 60/60 at the max build:
- Live: 96.67 91.85 85.83 81.07 75.82 70.78 66.35 | 96.5 91.67 94.98 93.33 89.65 70.88 33.98
- PP: 96.58 89.97 83.3 76.87 68.52 60.03 60.07 | 90.43 80.82 87.55 84.6 78.45 54.95 18.18
- w 0.35: 96.62 90.38 84.52 78.2 70.77 63.9 61.95 | 91.68 83.45 89.68 87.08 82.12 60.72 23.33
- w 0.35 + re-pin G: 98.55 90.38 84.52 78.2 74.15 70.72 66.65 | 94.43 83.45 89.68 87.08 84.53 68.37 31.37

**Why it fails without a re-pin:** per-phase scoring hurts the upper ladder most (a single press is noisier than the averaged
score, and tau is concave). The boss drops 4.4 pp (w 0.35) / 6.3 pp (PP) for the strong player and 10.7 / 15.8 pp for the weak
player at max, and oh2 -> boss flattens (1.95 / -0.03).

**Lever measured: Touge crew re-pin (budget multipliers kid1..boss, w 0.35).** All runs are in `log_w035_repin*.txt`:

| Run | Multipliers (kid1, kid2, mat1, mat2, oh1, oh2, boss) | Result |
|---|---|---|
| A | 1, 1, 1, 1, 0.9945, 0.9885, 0.9918 | boss 71.97: G1a, G3a, G3c FAIL |
| B | 1, 1, 1, 1, 0.994, 0.987, 0.9905 | boss 73.53: G1a, G3a, G3c, G5 (95.05) FAIL |
| C | 1, 1, 1, 1, 0.9971, 0.9948, 0.9963 | G1a 65.78, G3c 2.50 FAIL |
| D | 1, 1, 1, 1, 0.9971, 0.9945, 0.9958 | G3a 29.97, G3c 1.97 FAIL |
| E | 1, 1, 1, 1, 0.9971, 0.99535, 0.996 | all pass (G1a 66.33, G3a 30.28, G3c 3.07) |
| F | 0.985, 1, 1, 1, 0.9971, 0.99535, 0.996 | all pass (G1a 66.33, G3a 32.22, G3c 3.07) |
| **G** | **0.985, 1, 1, 1, 0.9965, 0.99535, 0.9958** | **all pass (G1a 66.65, G2a 31.37, G3a 31.90, G3c 3.43, G5 94.00)** |

G as stats (live -> G): kid1 370.52 -> 364.96, oh1 423.42 -> 421.94, oh2 434.22 -> 432.20, boss 444.00 -> 442.14 (kid2, mat1,
mat2 unchanged). Not a final pick: the thinnest margins are about 1 SE (G1a +0.65 over 66, G2a +1.37, G5 1.00 under), the
values are unrounded (a real re-pin rounds to 2 dp and reruns), and Touge stats are steep here (about 12 pp strong / 18 pp
weak per 1 % boss budget). The re-pin was only run at w 0.35; PP (w 1.0) would need its own, larger re-pin (not run).

## 4. Open questions for Austin

1. **w:** each phase on its own press (PP, your rule for Wangan/Street) or option 2 smoothing w 0.35 (unapproved)? PP costs
   more (boss 60.07, weak at max 18.18) and needs a bigger re-pin.
2. **Re-pin:** accept a Touge crew re-pin like G (kid1 1.5 %, oh1 0.35 %, oh2 0.47 %, boss 0.42 % lower)? Without it G1a, G2a and G3c fail.
3. **PA start presentation:** do both cars roll out of the PA side by side, or one behind the other? Is the mid-race turnout
   gone entirely (my reading of "no turn-5 swap")?
4. **Mid-corner order:** display only in v1 (no draft/defence effect), same as the Wangan/Street open point?
5. **Promotion:** Wangan/Street per-phase isn't in sim/ yet either. Promote all three districts together (one shared
   `PER_PHASE_DISTRICTS` + w constant) or Touge alone?

## 5. Godot port list for Gordon (after Austin approves; nothing to build yet)

1. Barry promotes to `sim/velocity_shift/` first (match.py per-phase path, combat resolve per clash, equations
   `PER_PHASE_DISTRICTS` incl. "touge", the w constant, Touge `MS_CREW_BUDGET` re-pin) and sends the hash.
2. Regenerate `scripts/globals.gd` with `python3 tools/touge_race/gen_globals.py` (new: per-phase district list, w, Touge crew
   stats; `PIN_COMMIT` = the promotion hash).
3. `scripts/race_core.gd` `submit_qte()`: score each clash with its own (smoothed) phase QTE instead of the mean; draw the AI
   QTE 3 times per turn from `o_qte_rng` in Entry, Apex, Exit order (Entry = today's draw; the RNG draw count changes); keep
   running order after each phase.
4. `scripts/race_core.gd`: remove `role_first`, `role()`, `swap_after()`, `at_swap()`, the banking (`banked_*`) and `seg_*`
   (gap = whole race); drop `role_first` from `setup()` and the save/replay state, and bump the state token version.
5. `scripts/main.gd`: remove ROLE mode (`_to_role`, `_role_key`, `_choose_role`, `role_sel`, `--role`); MENU -> CARSEL -> RACE
   starting in the PA; remove the mid-race turnout playback.
6. `spec/race_config.json`: remove `swap_after_turn` / `_swap_doc`; add the PA start (e.g. `"start": "pa"`).
7. `scripts/track_road.gd` / `scripts/touge_dressing.gd` / `scenes/turnout_lot.tscn`: place the turnout pocket before turn 1
   instead of on turn 5's exit straight (the `swap_after_turn` checks); the lot camera becomes the start shot; the parked
   start marks (`display.json` `start_marks`) go or move.
8. HUD: delete `scripts/hud/turnout_banner.gd` and the role prompt (`hud.gd` entries `role`, `turnout`);
   `scripts/hud/gap_meter.gd` drops CHASING/LEADING and shows the whole-race gap and order.
9. Visible passing: replace `display.json` `visual_gap.touge` (rival stays on its role's side) with order from running
   progress after each phase, with an overtake beat (`design/godot-build-guide.md:907`: leader changed -> overtake animation).
10. `tools/touge_race/parity_touge.py`: drop `role_first`, re-pin and rerun parity on the per-phase totals.

## 6. Story / art flags (for Desmond)

- **Story:** no `story/` or design narrative file mentions cat and mouse, lead/chase roles or the swap (grep 2026-11-20). The
  Touge rival-intro note "gossip at the turnout" (`design/notes/mod-skill-story-ui-v1.md:17`) now fits the PA start. Canon 6
  (no real-world place names): the PA needs an in-world name if it's ever named on screen.
- **Art:** Arthur's approved turnout lot kit (`art/kits/turnout_lot`) is still used but moves to the race start (start shot,
  roll-out path). The "TURNOUT · SWAP" banner, the "Lead or chase first?" prompt, the CHASING/LEADING gap meter labels and the
  start-line stripe/grid boxes (Austin t121 item 12) are affected. Touge now needs visible passing (overtake beat).

## Files

`touge_passing.py` (draft module), `run_touge_passing.py` (runner), `log_*.txt` / `res_*.json` (live, pp, w035, w035_repinA-G).
Rerun: `python3 run_touge_passing.py --variant w035 --rung-scale 0.985,1,1,1,0.9965,0.99535,0.9958` (about 35-60 s on 8 cores).
