# betting-v2-mods-v1 (draft, not live) — Barry 2026-11-14

> Committed 2026-11-14 as a draft (not live). Run on the sim as it was before xp-carry-v1 fix C went live (no carry-over); not re-run since. Story-only cash differs under the live carry-over (end R2 $13,940 vs $17,660), so re-run before relying on story-only figures.

Re-run of the betting check on the **live** economy: mods-v1 garage + just-in-time buyer, the 15 live stand-in tracks,
live betting constants (`BET_ODDS = "fair"`, net = stake × (1−p)/p, no clamp, no house edge, `BETTING_UNLOCK_AFTER = 2`,
`BET_MIN` $500, `BET_MAX` $2,000, `BET_ELIGIBLE = "any"`, no count cap). Myth4 stays at $8,000 (Austin is fine with it; nothing changed).
Sim: `bet_mc.py` → `results.json` (1,000 Monte Carlo trials per profile × policy, `mc_log.txt`). `sim/` unchanged.

Method: R1–R2 are the live deterministic walk (betting is locked). From R3 on, every race attempt is rolled with the player's real p
(hardest track for 20–30-turn races, district mean for 10-turn, the same p the walk's clear check uses), and the odds are priced on that p.
A lost story race is re-run; a lost grind pays nothing and gives no XP. The live buyer spends after every credit. The roll-free walk reproduces
live exactly (end-R3 cash $16,922 / $16,102 / $16,102 / $30,420, finale and arc grinds identical to `verify_live`).
Policies: **likely** = bet $2,000 when p ≥ 65 %; **always** = bet $2,000 (or all cash if less) on every race; **grind** = always, but grind races only.
Ruin = a lost bet leaves cash below BET_MIN ($500). Play continues afterwards (purses keep coming).

## Mean profit per bet and ruin
| Profile | policy | bets / run (grind) | mean profit per bet | mean profit per run (p10 / p90) | ruin |
|---|---|---|---|---|---|
| 60/60 hard | likely | 61.7 (55.4) | −$4.1 | −$251 (−$8,743 / +$7,257) | 1.1 % |
| | always | 106.7 (70.1) | +$4.4 | +$468 (−$24,442 / +$25,190) | **54.9 %** |
| | grind | 70.0 (70.0) | −$0.1 | −$6 (−$18,111 / +$17,592) | **33.1 %** |
| 60/80 mixed | likely | 52.4 (40.6) | −$4.2 | −$219 (−$5,525 / +$4,677) | 6.3 % |
| | always | 73.8 (40.4) | +$2.2 | +$162 (−$14,956 / +$13,069) | 15.5 % |
| | grind | 40.6 (40.6) | +$2.3 | +$94 (−$4,754 / +$3,246) | 0.0 % |
| 80/60 mixed | likely | 50.1 (38.4) | −$3.4 | −$172 (−$5,769 / +$4,231) | 8.1 % |
| | always | 73.8 (38.1) | +$3.8 | +$282 (−$22,093 / +$17,495) | **21.8 %** |
| | grind | 38.4 (38.4) | −$2.9 | −$113 (−$3,355 / +$2,645) | 0.0 % |
| 80/80 story | likely | 14.1 (0) | +$0.8 | +$12 (−$3,824 / +$4,190) | 2.2 % |
| | always | 26.7 (0) | −$8.5 | −$226 (−$10,617 / +$9,274) | 4.6 % |
Every mean is zero within Monte Carlo noise (a $2,000 bet has a standard deviation of roughly $1,000–$3,000). Fair odds mean zero expected value by construction.

## Exploit check: betting on easy grind races
| Profile | grind win p (R3 worst / arc touge-wangan-street) | grind bets / run | profit per grind bet | grind-only profit per run (p10 / p90) |
|---|---|---|---|---|
| 60/60 | 54.0 % / 80.1-85.5-91.0 % | 70.0 | −$0.1 | −$6 (−$18,111 / +$17,592) |
| 60/80 | — / 92.5-94.1-97.7 % | 40.6 | +$2.3 | +$94 (−$4,754 / +$3,246) |
| 80/60 | — / 95.7-98.0-99.1 % | 38.4 | −$2.9 | −$113 (−$3,355 / +$2,645) |
| 80/80 | (doesn't grind) / 98.8-99.2-99.7 % | 0 | — | $0 |
**No exploit.** On an easy grind the payout shrinks with p (p = 0.9 pays $222 on $2,000; p = 0.99 pays $20), so farming favourites earns
nothing on average. The old even-money printer (+$241k on finale grinds, econ-v1) is gone under fair odds.

## Cash and gear impact (mean; p10 / p50 / p90)
| Profile | End R3 cash: no bet → likely / always | After the finale: no bet → likely / always |
|---|---|---|
| 60/60 | $16,922 → $16,806 / $18,572 (always p10 $4,400) | $35,242 → $34,991 / $37,136 (always $14,763 / $36,477 / $60,432) |
| 60/80 | $16,102 → $15,977 / $16,709 (always p10 $4,794) | $28,482 → $28,263 / $29,155 (always $15,552 / $29,552 / $41,552) |
| 80/60 | $16,102 → $16,059 / $18,248 (always p10 $3,089) | $27,740 → $27,568 / $29,768 (always $13,934 / $31,179 / $45,235) |
| 80/80 | $30,420 → $30,369 / $30,323 (always p10 $22,818) | $16,995 → $17,015 / $17,009 (always $7,537 / $18,269 / $26,269) |

| Race (mean win p) | no bet | likely | always |
|---|---|---|---|
| R3 boss 60/60 / 60/80 / 80/60 / 80/80 | 30.3 / 67.6 / 70.1 / 55.8 | 30.2 / 67.6 / 70.1 / 55.8 | 29.2 / 67.2 / 67.6 / 55.8 |
| F4 60/60 / 60/80 / 80/60 / 80/80 | 34.7 / 72.6 / 74.1 / 81.7 | 34.7 / 72.6 / 74.1 / 81.5 | 34.0 / 72.0 / 73.0 / 80.3 (80/80 worst trial 53.8) |
| Finale grinds per step, 60/60 attempts (wins on the roll-free walk 11/7/7/9) | 13.7/8.2/7.7/11.3 | same | 13.7/8.2/7.7/11.4 |
Betting never makes a car stronger. Losing streaks under always-max can delay a mod purchase (80/60 R3 boss 70.1 → 67.6 mean;
one 80/80 trial met F4 at 53.8 without its last Myth4). Grind counts don't move.

## Flags
- **Nothing broken in the economy:** mean profit per bet is about $0 for every profile and policy, and no grind-farming exploit exists.
- **Ruin under always-max is high for weak profiles:** 60/60 54.9 %, 80/60 21.8 %, and 60/60 grind-only 33.1 %. The buyer keeps cash low and
  BET_MAX is all-in below $2,000, so one lost long-shot bet zeroes the wallet. It's a variance problem, not an exploit. Optional UX lever: block bets that would leave cash below BET_MIN.
- **Fair odds only work if the game prices odds on the same p the race uses.** The sim prices on the profile's true p. If the game quotes odds from
  a profile table while a player plays better, betting turns +EV again (not simmed). Bets at small p pay a lot (60/60 F4 at 34.7 % pays $3,764 on $2,000).
- Myth4 at $8,000: unchanged, and every profile still affords the Myth set before F4 with no bet.
