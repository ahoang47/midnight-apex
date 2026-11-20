# cooldown-v1: Austin's Touge playtest, WRX vs MX-5 (Barry ANALYSIS + PROPOSAL, 2026-11-20, UNAPPROVED, nothing live)

> Austin (playtest relayed by Gordon, build 060d9f3, sim pin 83b98d8): "I also think cooldown sucks, but it might be related
> to the car I chose." No sim/ or Godot numbers are changed here.

## Cars (Godot 060d9f3 vs sim)
- `scripts/globals.gd:143` `CAR_DRAFT_BLOCKS` (used because `spec/race_config.json:77` `use_draft_blocks: true`; still
  UNAPPROVED, `unapproved/barry/touge-race-parity/blocks.json` @ fd59332):
  - **WRX STI** POW/HAN/EN **750 / 750 / 1500**, which is the **Wangan** shape (25/25/50), on a Touge track.
  - **MX-5** **1350 / 750 / 900**, the Touge tune (45/25/30). Both total 3000, so r = 1.
- **No per-car cooldown values** exist in Godot or the sim. Heat capacity and recovery come only from build shares and r
  (`heat_capacity`, `HEAT_SHARE_EXP` 1.5) and the shared constants (globals.gd mirrors equations.py). The player uses the
  player rules (release at 30 % of capacity, passive load can lock). The AI uses the softer boss rules (release at 80 %,
  no passive locks; resources-v4b G2, approved).
- WRX gauges on this track (capacity P/H/E): **2.94 / 2.48 / 8.38**, recovery 0.98 / 0.83 / 2.79 per turn. MX-5 (AI rules):
  7.26 / 2.53 / 3.98. Touge corners are HAN-hungry (HP 1.2, ES 1.4, CH 1.3), so the WRX's small HAN and POW gauges fill fast.

## Replay (`replay_tc4.py` → `replay_tc4.json`): exact
TC4 decoded and checked against Gordon's decode (seed 98,739,619, lead first, 10 turns, picks and QTEs as relayed). Pick
index = `race_core.gd:23` HAND `P,H,E,P,H,E,P,H,E` (index mod 3: 0 POW, 1 HAN, 2 EN). Replayed with the live sim pieces
under Godot's resolve order. Cumulative totals are **bit-identical: 18.01890640578472 vs 12.978010809835675**.

| Turn | Corner | Played | Player mults | Locked at turn end (P/H/E) | Note |
|---|---|---|---|---|---|
| 1 | HP | EHH (auto) | 1, 1, **0.40** | – H – | 2nd HAN overran; HAN stays locked t1-t5 |
| 2 | ES | PEP | 1, 1, 1 | – H – | |
| 3 | HP | PEE | 1, 1, 1 | – H – | |
| 4 | DR | PEP | 1, 1, **0.76** | P H – | POW overran |
| 5 | ES | EEE | 1, 1, 1 | P H – | |
| 6 | HP | EEE | 1, 1, **0.40** | – – E | EN overran (repeat surcharge) |
| 7 | N90 | HPH | 1, 1, **0.71** | – H E | |
| 8 | HP | PPP | 1, 1, **0.40** | P H E | all three locked |
| 9 | DR | (limp) | 0.4 x3 | P H E | full limp |
| 10 | CH | (limp) | 0.4 x3 | P H E | full limp |

In total: 9 of 10 turns started with a locked gauge, 5 clashes overran, and **6 of 30 clashes were limp** (×0.4). HAN was
locked for 5 straight turns. Austin still won 18.02 to 12.98.

## 2,000 seeded races per split (`matchup_mc.py`; 80/80 sim player with pacing, vs MX-5 under AI rules, same track)

| Player split | Win % | Turns starting locked | Limp clashes | Overrun clashes | Locks per race | Mean lock length (turns) |
|---|---|---|---|---|---|---|
| **WRX 25/25/50** | 81.25 | **47.6 %** | **13.1 %** | 8.3 % | 2.65 | **3.80** |
| MX-5 / Touge tune 45/25/30 | 72.15 | 34.6 % | 2.7 % | 5.3 % | 1.68 | 3.31 |
| Even 33/33/33 | 74.5 | 26.1 % | 2.1 % | 4.2 % | 1.62 | 2.49 |
| HAN-heavy 30/45/25 | 56.4 | 39.2 % | 7.8 % | 5.7 % | 2.08 | 3.38 |

So the WRX's split makes cooldown clearly worse: about 1.8x the locked turns of an even car, 6x the limp clashes, and
locks 1.3 turns longer. It still wins the most, because EN-heavy play pays on this track. Austin is right that the car is a
big part of it.

## Verdict
**Working as coded** (Godot = sim, exactly). **Working as intended** for the rules as approved: specialized builds trade
cooldown for payoff. But the feel is harsh. Even a Touge-tuned car starts a third of its turns with a lock, and a lock lasts
3.3 turns of a 10-turn race (30 % release plus passive load). That's a feel problem rather than a balance bug, so here is a
**proposal, not a change**.

## Proposal options (what-ifs, same 2,000 seeds; none live)
- **A. Player release 0.3 → 0.5** (`HEAT_RELEASE`; the AI stays at 0.8): locks get about 1 turn shorter for every build.
  WRX lock length 3.80 → 2.62 turns, limp 13.1 → 6.3 %; even 2.49 → 1.77, limp 2.1 → 0.9 %. The cost is that the player's
  win rate rises about 4-6 pp for every build (WRX 87.5, MX-5 76.5, even 79.1, HAN-heavy 61.55). That shifts the live
  mod_skill climb and the balance gauntlet, so it would need a re-pin pass (boss stats about +0.7 to +1 %, rough
  estimate) before going live.
- **B. Flatter share scaling `HEAT_SHARE_EXP` 1.5 → 1.0:** this only helps specialized builds (WRX limp 13.1 → 9.6 %, locked
  turns 47.6 → 38.3 %, lock length 3.80 → 3.66). Even builds are unchanged (26.1 %). But it also reshapes the AI's gauges and
  cuts the WRX's edge (win 81.25 → 71.0), so it's mostly a specialization nerf.
- Tested and **not recommended:** no passive locks for the player (WRX limp 13.1 → 12.2 %, lock length 3.80 → 3.92). It
  barely helps.
- **No-number option (Gordon, UI):** show each gauge's "unlocks in N turns" and warn when a pick would overrun or lock. Most
  of Austin's limp came from picks (EEE / PPP on a hairpin, the auto-filled HH on turn 1) whose cost the plan panel could
  have flagged.

Recommendation: A, plus the UI warning, if Austin wants cooldown to feel lighter. Otherwise keep the live rules and pick a
Touge-shaped car for Touge.
