# Economy and Mod Parts: Headless Sim Specification

> **Status (2026-11-13):** econ-v1 is live in `sim/velocity_shift/equations.py` and `progression.py` (Austin go-ahead). Money is USD at ×100. Live figures are written in the sections below; remaining TBDs and proposal-only modules (the shop catalog, season runner, respec costs, substory payouts) are called out.
> Author: Barry (Chief of Systems), 2026-11-02; money, unlock and ladder figures updated 2026-11-13 from the live sim (Desmond).
> Rules for this document: anything stated as existing cites `file:line`. Anything else is labeled **PROPOSAL** or **OPEN QUESTION**. Every number not already in the live sim is a named constant set to `TBD`.
> The original 2026-11-02 draft header (waiting on success criteria; nothing simulated) is superseded for the live econ-v1 constants; proposal sections that never landed are unchanged.

---

## 1. Purpose and scope

**Purpose.** Give the Python headless sim (`sim/velocity_shift/`) a way to play a whole season, from the Prologue through Round 3. Along the way it tracks money, the repair debt, the shop, mod parts and Reiko's wholesale discount. The goal is to answer balance questions with data: how much the debt should be, which race clears it, what payouts and prices should be, and whether a player with no mods can still win early races.

**In scope (headless sim only):**
- Money: earning it, the repair debt, and spending it in the shop.
- Mod parts: a catalog, loadout slots, level floors, shop unlocks, and how each part changes the existing combat numbers.
- A season runner: Prologue → Round 1 (Street) → Round 2 (Wangan) → Round 3 (Touge), one district crew per round (Austin, 2026-11-13; `DEFAULT_CREW_ORDER` is the only legal order), with wild races, crew races, crew boss races and retries.
- Opponent mods (opponents carry their own parts).
- Metrics output, so Austin can attach success criteria.

**Out of scope:**
- Godot/UI, the overworld, dialogue, and part visuals (those go to Arthur, see §11).
- Skill trees. They are deferred (`design/05-skill-trees.md:3`, `design/godot-build-guide.md:1313`).
- The Finale (Myth Driver races and the summit). **OPEN QUESTION Q15** asks whether money still matters there.
- Tells and bluffs. Porting them to the sim is on hold by Austin's call.
- Changing combat formulas. Mods plug into terms that already exist (§6.3).

---

## 2. Sources: what the repo already says

### 2.1 Story (owned by Nathaniel, read-only here)

| Fact | Source |
|---|---|
| Core loop: "Earn money, parts, and reputation" and "Upgrade and tune vehicle builds" | `story/pitch.md:62-63` |
| Act structure is Prologue → Rounds 1–3 → Finale. One district per round: Round 1 Street, Round 2 Wangan, Round 3 Touge. Each district has one crew and one crew boss, raced once with no rematches (Austin, 2026-11-13; replaces the 2026-11-10 free crew order) | `story/canon.md:24-29`, `story/pitch.md:73` |
| Each round the PC runs that round's district crew once, in order: kids, then mature members, then old heads, then the crew boss (no rematches, 2026-11-13). The lieutenant tier is the kids, mature members and old heads, rising in difficulty within the crew, and each round's crew sits higher than the last. | `story/canon.md:50`, `:141` |
| Reputation explains the rotation in-world only. **It is not a tracked stat** | `story/canon.md:31`, `story/plot.md:93` |
| Beating crew members (lieutenants) expands Reiko's paid shop stock; crew boss stakes are money, reputation (lore only), rare shop mods and story progress. Losing means a retry and never losing the car | `story/canon.md`, `story/plot.md:42` (canon 28) |
| Boss stakes in the barks: "Big cash payout" and "Rare mods unlocked in the shop" (also territory, crew respect, district unlocks, narrative reveals). No pink slips; crew bosses' signature shells come from crew boss betting races at the promoter's subsea parking-area home base, and standout substories award a small pool of oddball shells (canon 26, 28) | `story/barks.md:336-342`, `story/canon.md` |
| Debt (decision 19): Sabine fronted the engine rebuild, labor and tow on a personal repair tab after feeling responsible for the blowout (she stepped away from the scene and isn't building a crew or garage name). A share of winnings repays it until it clears when the PC beats the Street crew boss at the end of Round 1 (Austin, 2026-11-13; live `DEBT_CLEAR_AFTER` = 1). Reiko gives wholesale at the same moment, and by Round 3 the PC has plenty of parts access. Live amounts (econ-v1): debt **$16,000**, share **0.65**, wholesale **20 %** off T1–T3 | `story/canon.md` (14, 19, 24) |
| Round 1: until the debt clears, "winnings all go to the debt, so there's little money for mods" (moved from Round 2, 2026-11-13) | `story/plot.md:121` |
| End of Round 1: Reiko gives wholesale at the same moment the debt clears (Street crew boss; 2026-11-13) | `story/plot.md:98`, `story/canon.md:96` |
| Invoice covers "Engine, labor, tow" (amount **$16,000**). "Winnings come here first, until we're even." On losing: "Then you owe me longer" | `story/scripts/prologue.md:89-93` |
| Reiko: "Wholesale is for crew. You're not crew." / "We'll see." | `story/scripts/prologue.md:74-77` |
| Jesse (the Tuner) does mods and installs a DAQ system: "The more races you run, the more data he gets, and the better your car will be." | `story/scripts/prologue.md:72`, `story/plot.md:28` |
| Each district has exactly one racer type per archetype (15 racer types in total) | `story/canon.md:46-54` |
| Each round is one district: Street, then Wangan, then Touge. The PC runs that district's whole crew once (kids, mature members, old heads, then the boss), with no rematches, and flavor text follows every race | `story/plot.md:43`, `:97` |
| Barks come in four race tiers: wild (opponent starts it), wild (player starts it), lieutenant race (crew members, "These are mini-bosses") with lines keyed to Rounds 1–3, and crew boss. Reputation is lore only | `story/barks.md:29`, `:185`, `:210-228`, `:311` |

### 2.2 Design docs

| Fact | Source |
|---|---|
| Loop: race wild and lieutenant encounters for currency, the car levels up (unlocking slots and gating mod tiers), buy mods in the shop, and boss wins expand the shop | `design/notes/mod_notes.md:3-15` |
| On a loss, the narrative gate blocks progress and nothing is destroyed. An optional entry fee is paid per retry | `design/notes/mod_notes.md:28-32` |
| Start with about 3 loadout slots and unlock up to about 8–10 at key car levels. One mod per slot, and swapping is free | `design/notes/mod_notes.md:34-38` |
| Mods are shop-only, have level requirements (e.g. "Turbo Mk3: L25+"), and come in 3 flavors: sharp trade-offs (+15 POW, −10 EN), unique effects, or both | `design/notes/mod_notes.md:40-47` |
| Rewards: Wild = Small currency, Lieutenant = Moderate, Boss = Large plus rare mods entering the shop | `design/notes/mod_notes.md:51-57` |
| Opponents carry their own archetype-matched mods, visible before the match | `design/notes/mod_notes.md:59-62` |
| Mod categories are TBD | `design/notes/mod_notes.md:64-66` |
| "No free lunches"; "no random drops, no farming"; "No roguelite layer" | `design/notes/mod_notes.md:71-74` |
| Anti-cheese rule: a level floor on each mod, so rare mods can't go on low-level cars | `design/notes/Notes.md:9-11` |
| Per car: 5 inventory slots plus 1 non-removable "car specific" slot. Perma mods also affect visual identity | `design/notes/Notes.md:36-40` |
| Modifiers must be additive to existing terms, never new multiplicative layers. One node per category | `design/05-skill-trees.md:25-36` |
| Mods are a separate system and supply stats or effects directly. Opponents use stock stats plus their own mods. HP = level × HP_PER_LEVEL and should never be touched | `design/05-skill-trees.md:50-53` |
| All game constants live in `equations.py` | `design/01-system-overview.md:133`, `sim/velocity_shift/equations.py:7-9` |

### 2.3 Sim code (how things work today)

| Fact | Source |
|---|---|
| 5 archetypes with level-100 POW/EN/HAN targets: Aggressive 55/20/25, Defensive 20/55/25, Precise 25/20/55, Balanced 30/40/30, Adaptive 30/30/40 | `sim/velocity_shift/cars.py:3-11` |
| Stats start at 33/33/33 and move toward the target along `((L-1)/99)^1.5` | `sim/velocity_shift/cars.py:13-29` |
| Stat budget = level × 30 | `sim/velocity_shift/cars.py:32-40` |
| `CombatantStats` = name, pow, en, han, level. No equipment field exists | `sim/velocity_shift/models.py:43-54` |
| Constants: CLASH_STAKES 0.35, BATTLE_BONUS 0.05, MITIGATION_PER_1000 0.4, MITIGATION_FLOOR 0.1, HP_PER_LEVEL 180, QTE_NORMALIZER 10, HAN_QTE_WEIGHT 0.5 | `sim/velocity_shift/equations.py:16-22` |
| *(history: card draw removed 2026-11-13; stat share now sizes the heat gauges and weights the stance played, see 02 heat/load section)* Deck mix is weighted by stat share (POW, EN, HAN shares → POW, EN, HAN cards), so any stat change also changes the cards | `sim/velocity_shift/deck.py:4`, `:29-44` |
| QTE factor is clamped to 0–1 | `sim/velocity_shift/combat.py:111-112` |
| Encounter ratios: wild 0.75, lieutenant 1.1, boss 1.2 (they live in `ai.py`, not `equations.py`) | `sim/velocity_shift/ai.py:17-21` |
| Opponent level = round(player level × ratio) | `sim/velocity_shift/cli.py:305` |
| Opponent QTE = TYPICAL_QTE (7.0) × the same ratio | `sim/velocity_shift/ai.py:36`, `:292-308`, `sim/velocity_shift/simulation.py:70` |
| Turn limits: wild 10, lieutenant 20, boss 30 (in `cli.py`) | `sim/velocity_shift/cli.py:28-32` |
| Simulated player picks cards at random and rolls QTE uniformly from 1 to 10 | `sim/velocity_shift/simulation.py:52-57` |
| The ratio counts twice (in opponent level and in QTE). A fix is pending | `CHANGELOG.md:312` |
| Money, debt, purses, mod prices, betting stakes and the 3-round XP/level ladder are live in `equations.py` / `progression.py` (econ-v1, Austin go-ahead 2026-11-13). There is still no shop catalog, `economy.py` ledger or season runner; the interactive CLI still picks levels from presets | `sim/velocity_shift/equations.py`, `sim/velocity_shift/progression.py`, `sim/config/sample_builds.json`, `sim/velocity_shift/cli.py` |

### 2.4 Conflicts between sources

| # | Conflict | Sources | Effect on this spec |
|---|---|---|---|
| C1 | **Rep: tracked or not?** Resolved: reputation is lore only. Barks are keyed to rounds, not a rep stat | `story/canon.md:31`, `story/barks.md:222` | The sim tracks no rep |
| C2 | **Encounter ratios.** Docs say 0.35 / 0.75 / 1.15. Code says 0.75 / 1.1 / 1.2 | `design/04-difficulty-tuning.md:58-62`, `design/01-system-overview.md:99-103` vs `sim/velocity_shift/ai.py:17-21` | Code is what runs. Both are superseded by the pending fix |
| C3 | **Opponent QTE.** Doc says `4.0 + level × 0.025`. Code and Godot say 7.0 × ratio | `design/04-difficulty-tuning.md:148` vs `sim/velocity_shift/ai.py:36`, `scripts/AIQTE.gd:3-24` | Same pending fix |
| C4 | **Slot counts.** About 3 slots growing to 8–10, versus 5 slots plus 1 car-specific slot | `design/notes/mod_notes.md:36` vs `design/notes/Notes.md:38-39` | Q7 |
| C5 | **Stat ratio.** mod_notes says the ratio is fixed from L1 with "no convergence". Code and 04 say stats start 33/33/33 and converge to the target | `design/notes/mod_notes.md:19-21` vs `sim/velocity_shift/cars.py:13-29`, `design/04-difficulty-tuning.md:20-23` | The spec follows the code |
| C6 | **Archetype count.** mod_notes says "2–3 archetypes". The code has 5. 04 refers to "6 personalities" | `design/notes/mod_notes.md:5`, `design/04-difficulty-tuning.md:117`, `:141-145` vs `sim/velocity_shift/ai.py:278-284` | The spec uses 5 |
| C7 | **Pink slips / roguelite.** Notes.md has a "Pink Slip Races" heading, but canon and barks rule pink slips out | `design/notes/Notes.md:8` vs `story/canon.md:56`, `story/barks.md:336-342` | No pink slips |
| C8 | **Retry cost.** mod_notes has an optional entry fee per retry, and Sabine says "Then you owe me longer". Canon only says "retry" | `design/notes/mod_notes.md:32`, `story/scripts/prologue.md:92-93` vs `story/canon.md:56` | Q9 |
| C9 | **Farming.** Wild races are auto-generated (endless), yet "no random drops, no farming" | `design/notes/Notes.md:20` vs `design/notes/mod_notes.md:73` | Q8 |
| C10 | **Constants location.** The rule says all constants live in equations.py, but encounter tables and turn limits live in ai.py and cli.py | `design/01-system-overview.md:133` vs `sim/velocity_shift/ai.py:17-34`, `sim/velocity_shift/cli.py:28-32` | The new economy constants follow the rule (§9.2) |
| C11 | **Is money all or "first"?** Canon says winnings go "to the garage first" and also "all go to repaying it". Plot says "little money for mods" | `story/canon.md:40`, `story/plot.md:121` | The default reads it as 100%. Q4 |
| C12 | **Parts as rewards.** Pitch says "Earn money, parts". mod_notes says parts are shop-only with no drops | `story/pitch.md:62` vs `design/notes/mod_notes.md:42`, `:73`; canon 28 | Story races (lieutenants and crew bosses) add paid stock to Reiko's shop and never hand out free parts; substories can award one-off skewed-sidegrade parts straight to the garage stash (canon 28) |

---

## 3. Currencies and resources

| Resource | Status | Spec |
|---|---|---|
| **Money** (USD at ×100, Austin 2026-11-13; in-world currency name is still TBD: `story/canon.md` decision 6) | Live in `equations.py` | One wallet. Everything in the sim is priced in USD |
| **Repair debt** | Story canon (`story/canon.md` 19) | A ledger separate from the wallet: `DEBT_AMOUNT` **$16,000**, paid down by `DEBT_SHARE` **0.65** of each purse while open (§7) |
| **Car level** | Exists in code (`models.py:54`) | Drives stats, HP, slot unlocks and part level floors. Grows from XP since 2026-11-09 (§8.0, `sim/velocity_shift/progression.py`); slot unlocks and part floors still TBD (Q5 answered) |
| **Reiko standing** | Story (`story/plot.md:98`) | A boolean `wholesale_unlocked`, set by a story event, not a meter |
| **Rep / reputation** | Conflicting (C1) | **PROPOSAL:** not tracked in v1. If Austin wants it, the sim adds a counter that gates crew races (resolved: lore only) |
| **DAQ data** (Jesse) | Story flavor (`prologue.md:72`) | **PROPOSAL:** the in-world reason the car levels up. "More races, more data, better car" maps onto XP (Q5) |

---

## 4. Encounter mapping (story ↔ sim)

The sim has 3 encounter types (`ai.py:17-34`). The story has random racers, crew members ("mini-bosses", `barks.md:210-212`), rivals and the crew boss.

**PROPOSAL:**

| Story | Sim type | Per district per round |
|---|---|---|
| Random racer (any of the district's 5 racer types) | `wild` | `WILD_RACES_PER_DISTRICT = TBD` (optional, capped, see Q8) |
| Lieutenant race (crew members: kids, mature members, old heads) | `lieutenant` | `CREW_RACES_PER_DISTRICT = TBD` (required before the boss) |
| Crew boss | `boss` | 1 (required, retried until won) |
| Sabine (Prologue) | **OPEN QUESTION Q14** | 1, scripted loss (blowout, `canon.md:63`) |

The opponent's archetype comes from the district's racer-type table (`canon.md:48-54`). The boss's archetype is TBD per crew (crews are TBD in `canon.md:75`).

---

## 5. Income

### 5.1 Race payouts

**Live formula** (`equations.purse`; round index 0 = R1):

```
payout = BASE_PAYOUT[kind] × ROUND_PAYOUT_MULT[round]                  (on a win)
payout = GRIND_PAYOUT_FRACTION × BASE_PAYOUT_WILD × ROUND_PAYOUT_MULT  (grind / 10-turn wild)
```

Kind is `kid` (wild purse), `mature` / `old_head` (crew purse), or `boss`. `DISTRICT_PAYOUT_MULT` and `LOSS_PAYOUT_FRACTION` are not in the live code (a loss pays nothing).

| Constant | Value | Tune against |
|---|---|---|
| `BASE_PAYOUT_WILD` | **$1,000** | Kid rungs and wilds (R1 base) |
| `BASE_PAYOUT_CREW` | **$2,500** | Mature and old-head rungs |
| `BASE_PAYOUT_BOSS` | **$8,000** | Crew boss purse (R1 base) |
| `ROUND_PAYOUT_MULT` | **1.00 / 1.15 / 1.35** (R1 / R2 / R3) | So R3 boss equals $10,800 in the sim; that billed finale-purse figure is a sim assumption, not canon |
| `GRIND_PAYOUT_FRACTION` | **0.55** | A grind race pays 0.55 × that round's wild purse |
| `DISTRICT_PAYOUT_MULT` | not live | Only if districts should differ |
| `LOSS_PAYOUT_FRACTION` | not live (losses pay 0) | Nothing in the docs pays for a loss |
| `RETRY_ENTRY_FEE[encounter]` | TBD, default 0 | mod_notes.md:32 "optional". See Q9 |

### 5.2 Story-race rewards and shop unlocks (canon 19, 28)
- **Lieutenant win:** `BASE_PAYOUT_CREW` cash, plus horizontal part options at that round's stat budget added to Reiko's paid shop stock as her suppliers open up (`LIEUTENANT_SHOP_UNLOCKS = TBD`).
- **Crew boss win (Austin, 2026-11-09):** XP (levels, so some skill points, from `STORY_FILL` / `STORY_W`), `BASE_PAYOUT_BOSS` cash (times that round's `ROUND_PAYOUT_MULT`), a shell and a graphic, plus story progress (the next district or round unlocks). Mods are **bought only**.
- **⚠ CONFLICT, pending Desmond's rewording:** canon 28 (and `mod_notes.md:48`, `:57`) still say crew boss wins add rare tier-jump parts to Reiko's shop, and canon 26 says crew bosses' signature shells come only from betting races. Canon is not rewritten here; Desmond owns the rewording.
- Story races never give parts away for free (C12).

### 5.3 Substory rewards and other income (canon 26, 28)
Substories unlock alongside mods and the open city after the PC wins scripted race 3 (canon 19, 28). Each substory is one-time and awards one prize straight to the player:
- **Cash** (`SUBSTORY_CASH_PAYOUT[round] = TBD`, proposed around one wild-to-lieutenant purse for that round): runs through Sabine's normal `DEBT_SHARE` repair-tab cut while the debt is open. Keeping one cut rule avoids exceptions, and keeping pre-clear cash substories few means skipping vs clearing them nudges the end-of-Round-1 debt clear by at most a race or two (inside the existing wild-race spread).
- **Free mod part** straight to the garage stash: capped by existing slot limits and level floors, paced (`SUBSTORY_FREE_PARTS_MAX[round] = TBD`, proposed 1–2 in Round 1 across non-overlapping slots), **never aero** (aero stays gated on `debt == 0`), and built as a **skewed sidegrade**—bigger upside in one stat paid for by a real penalty in another, at the same or slightly lower net stat total than that round's shop parts (`≤ TIER_STAT_BUDGET[tier]`). Skipping substories costs weird specialist builds, never raw power, and Reiko's clean upgrades stay worth buying.
- **Shell-specific graphic/livery** (cosmetic only, zero combat or economy impact): UV-baked per shell (`design/art/art_direction.md` A.3). Unlocking a livery before owning its shell sits in the garage as a breadcrumb to hunt that shell down; Round 1–2 livery substories target the starter shell (or a substory shell already earned) so early rewards never sit unusable for two rounds before betting opens.
- **Cosmetic shell** (zero combat or economy impact): a small pool of oddball/capstone shells (`SUBSTORY_SHELL_COUNT = TBD`, mesh scope flagged to Desmond and Arthur), while crew bosses keep their signature shells exclusive to Round 3+ betting races at the promoter's subsea Wangan home base.

Other repeatable non-race income (e.g. garage work) is still **OPEN QUESTION Q10**.

---

## 6. Spending: the shop and mod parts

### 6.1 Shop rules (from the docs)
- Shop catalog parts are bought with money from Reiko (`mod_notes.md:40-42`); one-off skewed-sidegrade parts can also come directly from substories into the garage stash (§5.3, canon 28).
- Each part has a level floor (`mod_notes.md:43`, `Notes.md:11`).
- Lieutenant wins expand horizontal shop stock and crew boss wins add rare tier-jump stock (`mod_notes.md:48`, canon 28).
- Swapping parts between races is free (`mod_notes.md:38`). Selling parts back is not mentioned anywhere (Q11).

### 6.2 Slots
**PROPOSAL** (resolves C4 as a constant, Q7): `SLOT_UNLOCK_LEVELS = TBD` (a list of car levels). `BASE_SLOTS = TBD` (3 per mod_notes or 5 per Notes). Plus 1 fixed car-specific slot (`Notes.md:39`), which the sim could fill with Jesse's DAQ as a starter part (story flag for Nathaniel).

### 6.3 What a part can touch in the existing model
Every effect is **additive to an existing term** (`05-skill-trees.md:25-31`). None touches HP (`05-skill-trees.md:53`).

| Category (PROPOSAL, names are placeholders) | Touches | Existing hook |
|---|---|---|
| Engine / power | +POW (trade-off: −EN or −HAN) | `compute_damage` (`equations.py:48-58`), deck POW share (`deck.py:40`) |
| Chassis / armor | +EN (trade-off: −POW or −HAN) | `damage_mitigation` (`equations.py:61-68`), deck EN share |
| Suspension / handling | +HAN (trade-off) | `apply_han_qte_mod` (`equations.py:30-35`), deck HAN share |
| Unique: clash | `+Δ` on CLASH_STAKES for certain clashes (e.g. "first clash each turn auto-wins", `mod_notes.md:46`) | `clash_mult` (`equations.py:38-45`). Needs a new hook |
| Unique: QTE | `+Δ` to the QTE score or to mitigation floor terms (e.g. "QTE window +20% but max clash stakes reduced", `mod_notes.md:46`) | QTE pipeline (`match.py:130-136`). Needs a hook |

**PROPOSAL, how stat parts apply:** `final_stat = build_stats(arch, level) + Σ part flat bonuses`. **OPEN QUESTION Q6:** should bonuses be flat or scale with level? Flat bonuses fade in value as levels rise, which the level floors and tiers would offset. Stat parts also shift the deck mix (`deck.py:29-44`), which is a feature, but it needs to be reported.

**Aero parts and the wind tunnel (PROPOSAL, from the Integration room 2026-11-03; Austin agreed in principle, no numbers yet):**
- An aero part is a stat part with a **fixed base boost** plus a **small free pool** of points the player assigns to POW, EN or HAN at the speakeasy's wind tunnel (bought from Reiko at Sabine's garage). No new stat layer.
- The free pool makes an aero part worth more than a fixed part with the same total, so it needs a higher price or a slightly smaller total. Live price: `AERO_PRICE_MULT` **1.75** × the regular mod of its tier. `AERO_FREE_POINTS[tier] = TBD`, kept small relative to `TIER_STAT_BUDGET`.
- **Caps (Austin approved 2026-11-11, slots-v2; `equations.py`):** an aero part goes in **any slot**, **at most one** is equipped (`AERO_MAX_EQUIPPED = 1`), and its whole stat total (base + pool) **counts inside the 107 % cap** (`AERO_COUNTS_IN_MOD_CAP`, `MOD_CAP_FRACTION` 1.07, was 1.05; G2 heat system, Austin 2026-11-13). The free pool is **at most 10 %** of the part's total (`AERO_FREE_POOL_MAX_FRACTION = 0.10`, `aero_free_pool_max`), so every `AERO_FREE_POINTS[tier]` must be ≤ 0.10 × that tier's total. Why: with retuning before every race, a 20–30 % pool let average players clear R3 Street's crew boss (with a window mod, 100/0/0) or the Summit (70/20/10) with no grinding; at 10 % no wall is cleared (`unapproved/barry/slots-v2/RESULTS.md` Q5/Q7). Aero is still never worse than the mod it replaces (+0.03 … +1.01 pp at 10 %), so it needs the price premium above.
- **Tunes lock once set** (aero and regular skill/stat points alike), but a paid respec always exists so a bad build can't strand a player. Story reasons for the cost (Nathaniel): a second tunnel session burns more stolen power, Jesse has to cut and re-weld his own work, and Reiko doesn't take back fitted parts. `RESPEC_COST = TBD` (Q18).
- **Unlock and respec (Austin, 2026-11-03):** aero unlocks when the debt reaches zero, when the PC beats the Street crew boss at the end of Round 1 (Austin, 2026-11-13; `AERO_UNLOCK_AFTER` / `DEBT_CLEAR_AFTER` = 1; `aero_unlocked` is set by `debt == 0`). In the story, Sabine takes the PC out for drinks at the speakeasy to celebrate. Parts are bought once and kept, so only tunes relock. A respec, whether Jesse moving skill points or a tunnel retune for aero, moves at most `RESPEC_POINTS_PER_VISIT = TBD` points per visit, at `RESPEC_COST_PER_POINT = TBD` each. A small counter-tune before a boss stays affordable, and a full rebuild costs a lot or takes several visits. Retuning between races is allowed on purpose: you scout, then build a counter.

**Phasing PROPOSAL:** v1 of the sim has stat parts only. Unique-effect parts come in v2, once the hooks are specified separately.

### 6.4 Tiers, rarity, prices
| Constant | Value | Notes |
|---|---|---|
| `MOD_TIERS` / `PART_TIERS` | Live: T1 / T2 / T3 / T4 | Shop names still TBD |
| `MOD_TIER_LEVEL_FLOOR` | Live: T1 0, T2 13, T3 30, T4 47 | T2 opens with R2, T3 with R3, T4 after R3 and the P1 win. See below |
| `MOD_PRICE` | Live: T1 **$1,600**, T2 **$2,800**, T3 **$4,000**, T4 **$8,000** (per slot; T2–T4 are the upgrade from the tier below) | **T4 $8,000 is a stand-in**, not locked. Aero is 1.75 × the regular mod of its tier |
| `TIER_STAT_BUDGET[tier]` | TBD | Net bonus (upside minus trade-off) |
| `TIER_UNLOCK[tier]` | TBD: round start / lieutenant ladder / boss defeated / wholesale | Shop gating (canon 28) |
| `LIEUTENANT_PART_SOURCE[round][crew_step]` | TBD | Horizontal shop options unlocked by beating kids / mature / old heads |
| `RARE_PART_SOURCE[boss_id]` | TBD | Which crew boss adds which rare tier-jump parts |

**Mod tier level floors (live, econ-v1).** Constants in `sim/velocity_shift/equations.py`: `MOD_TIER_LEVEL_FLOOR` T1 0 / T2 13 / T3 30 / T4 47, and `T4_UNLOCK_RACE` = P1. Logic in `sim/velocity_shift/progression.py`: `mod_tier_floor`, `mod_tier_available`. `sim/tests/test_mod_floor.py` pins the floors and the P1 gate.
- A tier shows **"requires level N"** in the shop and can't be fitted below N, even when the player can afford it. T2 opens with R2 (cap of R1 is 12), T3 with R3 (cap of R2 is 29), T4 after R3 (cap of R3 is 46) once the PC wins pre-finale race P1.
- These replace the old per-(round, play position) floors (`MOD_TIER_FLOOR_RUNG`, `MOD_TIER_FLOOR_MARGIN`, `derive_mod_tier_floors`) from the 9-crew free-order ladder.
- The earlier slots-v2 write-up of why a floor exists (a newly unlocked tier must not skip a wall) is in `design/notes/slots-v2/README.md` (b3 section); that evidence is from the old ladder and is not re-simmed here.

The catalog itself (individual parts) lives in a data file (§9.2). **No part list is invented here.** It is authored after Q6/Q7 are answered.

### 6.5 Opponent parts
Opponents carry archetype-matched parts (`mod_notes.md:61`). **PROPOSAL:** `OPPONENT_PART_TIER[round][encounter] = TBD`. Each round is a different district's crew (2026-11-13), so each crew and its boss get their own level and part tier; there are no rematches, so no boss rebuild between rounds.

---

## 7. Repair debt and Reiko's discount

### 7.1 Rules (from canon)
- The debt starts at `DEBT_AMOUNT` **$16,000** after the Prologue (`canon.md` 19, `prologue.md:89`).
- While the debt is open, a share of each win goes to the debt and the rest to the wallet: `DEBT_SHARE` **0.65**. Austin ruled on 2026-11-02 that not all winnings go to the debt, which overrides the "all winnings" wording (C11, Q4).
- It must clear **at the end of Round 1**, when the PC beats the Street crew boss (Austin, 2026-11-13; canon 19; live `DEBT_CLEAR_AFTER` = 1).
- Wholesale unlocks **at the end of Round 1** (`plot.md`): `WHOLESALE_DISCOUNT` **0.20** off list on T1–T3 (`WHOLESALE_TIERS`), from `WHOLESALE_STARTS_AFTER` 1 through `WHOLESALE_ENDS_AFTER` 3 (never on T4).
- Losing doesn't add debt. It only delays payment ("owe me longer", `prologue.md:93`), unless the retry fee (Q9) is charged against the debt.

### 7.2 Timeline
| Phase | Debt | Wholesale | Can buy? |
|---|---|---|---|
| Prologue → end of Round 1 | Open | No | Yes, from the wallet share, at full price |
| End of Round 1 (Street crew boss: debt clears and wholesale unlocks together, 2026-11-13) → end of Round 3 | Paid | Yes | Yes, at wholesale |

### 7.3 The overlap: can the PC buy anything?

**Mostly moot since 2026-11-13:** the debt now clears at the same moment wholesale unlocks (the Street crew boss at the end of Round 1), so there's no window with wholesale on and the debt open. The `DEBT_SHARE` choice below still sets how much the PC can spend before that.

| Option | How it works | Pros | Cons |
|---|---|---|---|
| ~~**A. Strict**~~ (ruled out) | `DEBT_SHARE = 1.0`. Nothing is bought until the debt clears. The discount only matters afterward | Literal canon (`canon.md:40` "all") | Reiko's unlock does nothing for part of Round 2 |
| **B. Allowance** (live) | `DEBT_SHARE` **0.65** from the Prologue | Wholesale is felt right away; the PC can buy a few parts at full price in Round 1 | Bends "all winnings", already ruled as the live baseline |
| **C. Boss money is free** | Wild/crew winnings go to the debt, and boss payouts go to the wallet (or the reverse) | Clear rule, and boss cash feels big | Bends canon. Story needs to change |
| **D. Reiko cuts the bill** | The wholesale unlock also reprices the remaining debt by `WHOLESALE_DISCOUNT` (she sources the rebuild parts cheaper) | Ties Reiko's arc to the debt, and the debt clears sooner | New story beat. Needs Nathaniel |

**Ruled out:** A. Austin said on 2026-11-02 that not all winnings go to the debt. **Live (econ-v1):** option **B**, with `DEBT_SHARE` **0.65** applying from the Prologue (not only after wholesale), so the PC can buy a few parts at full price in Round 1. Options C and D and a `DEBT_RULE` switch are not live (07 Q4).

### 7.4 How the clearing race gets picked (once numbers exist)
**Live amount:** `DEBT_AMOUNT` is the flat **$16,000** in `equations.py`, with `DEBT_CLEAR_AFTER` = 1. Canon (Q1, locked 2026-11-13) still times the clear to the Street crew boss at the end of Round 1, the same moment wholesale unlocks and aero opens. A median-clear solve over seeds is not what set this number. (The target used to be the first Round 2 crew's boss from 2026-11-10, and "mid Round 2" before that.)

---

### 7.5 The promoter's betting side game (live stakes and odds, econ-v1)
Story: the Wangan crew boss is a race promoter who opens a betting side game after Round 2 (`story/canon.md` 21, `story/plot.md`). Shell and prompt rules stay with canon 26. Live constants are in `equations.py` (Austin go-ahead 2026-11-13: fair odds, unlock after R2, any race, no cap).

- **What you bet on:** the PC's own race. The PC stakes wallet cash on winning before the race starts. `BET_ELIGIBLE` is **any** race (story, grind/wild, pre-finale arc, finale). No betting on other racers in v1.
- **Unlock:** `BETTING_UNLOCK_AFTER` = 2, set at the **end of Round 2** (Austin and canon), separate from the aero unlock. Crew bosses' signature shells (cosmetic car bodies) are a bonus prize only in crew boss betting races at the promoter's subsea Wangan parking-area home base—any wild race can become a betting race through a prompt, which never awards shells—while a few standout substories award oddball shells (canon 26, 28). The PC never stakes their own shell.
- **Odds (live):** true fair odds, no house edge, no clamp. Net payout on a win is `stake × (1 − p) / p`, where p is the player's real win probability (`bet_net_payout`; `BET_ODDS` = "fair", `BET_HOUSE_EDGE` = 0, `BET_ODDS_CLAMP` = False). The earlier promoter house-edge line is not live.
- **Stakes (live):** `BET_MIN` **$500** to `BET_MAX` **$2,000**. There is no wallet-fraction cap and no count cap (`BET_COUNT_CAP` is None).
- **High-stakes option:** a handicap the promoter asks for (`HANDICAP_ODDS_BONUS`) is still TBD (Q16) and is not in the live code.
- **Risk:** a loss forfeits the whole stake.
- **Debt share:** by canon, the debt clears at the end of Round 1, before betting unlocks, so normally they never overlap. If a player reaches Round 3 with debt still open, `DEBT_SHARE` applies to net bet winnings the same way it applies to purses, so betting can't be used to dodge the debt.
- **Reiko's discount:** no direct link. Bet winnings go to the wallet and are spent at the wholesale prices that unlocked after Round 1.
- **Sim side:** `bet_allowed` / `bet_net_payout` in `equations.py`. A shop-policy Monte Carlo still lives in `unapproved/barry/econ-v1/` (not the live progression walk).

## 8. Progression curve

### 8.0 XP → levels → skill points (locked by Austin 2026-11-09; all XP numbers stand-ins pending playtest)
Code: `sim/velocity_shift/progression.py`; constants: `sim/velocity_shift/equations.py` (econ-v1 section); report: `python scripts/run_progression.py` from `sim/`. Live on the 3-round ladder and the heat-system oracle `sim/config/winrate_g2_econ_v1.json` (Austin go-ahead 2026-11-13).
- **Loop.** Story wins and grind races pay XP; XP fills car levels; skill points come only from levels (`sp_at_level`). SP grows with level (`SP_START` × `SP_GROWTH_PER_12_LEVELS` **(L / 12)**), and XP per level grows faster (`xp_to_next(L) = XP_BASE × XP_GROWTH ** L`), so leveling gets harder.
- **XP cap.** The level cap is the SP cap (`SP_CAP_FRACTION` 0.80 of P). Caps are per round, not raised per story win: `CAP_LEVEL` **12 / 29 / 46** (R1 / R2 / R3). Finale caps are `FINALE_CAP_LEVEL` **63 / 76 / 95 / 114**. XP earned past the current cap is lost. (`CAP_ALLOC_CREW` / `CAP_ALLOC_ROUND_OPEN` are removed.)
- **Story XP.** A round's story races pay `STORY_FILL` (0.62 / 0.75 / 0.80) of the XP from the round's entry level to its cap, split over the 7 rungs by `STORY_W`. Story alone does not reach the cap, so the player grinds the shortfall.
- **Grind taper.** A 10-turn grind win pays `GRIND_FRAC` (0.70) × `xp_to_next(L)` × a taper that falls toward `GRIND_TAPER_FLOOR` (0.20) as the cap nears (`GRIND_TAPER_TAU` 3.6). (`TAPER_*` and `grind_payout_fraction` are removed.)
- **Budgets.** Opponent budget B = `C_ROUND` / `LADDER_TARGET_R` on the 1.07 cap chain (`ANCHOR_B` 330, `K_STEP` 1.07, `MOD_CAP_FRACTION` 1.07). `DEFAULT_CREW_ORDER` is the only legal order (Street, then Wangan, then Touge). (`OPTION_A_CREW_STEP` / `OPTION_A_ROUND_STEP` and the old 9-crew free-order ladder are removed.)
- **Round 3 → finale.** Completing Round 3 opens the pre-finale training arc (01 canon, 2026-11-13); winning its first race (P1) unlocks the big finale mods (T4). Live sim arc purses (`ARC_PURSE`) are $2,500 / $3,375 / $5,000 for 10- / 20- / 30-turn races. The billed finale purse `FINALE_PURSE` ($10,800, equal to the R3 boss purse) is a sim assumption, not canon. (`FINALE_MOD_SHARE` / `FINALE_GRIND_SHARE` are removed.)
- **Rewards.** Boss wins pay XP (some SP via levels), money, a shell and a graphic; mods are bought only (see the canon 28 conflict in §5.2).
- **Open items:** (1) every XP number is a stand-in until playtest; (2) T4 $8,000 is a stand-in; (3) ~~aero has no rule yet against the SP/mod caps~~ resolved 2026-11-11 (Austin), and the live cap is 107 %: aero counts inside the cap, free pool ≤ 10 %, any slot, max one (§6.3); (4) the earlier Street / Wangan / Myth #2 skip-wall win-rate notes were from the pre-refit 9-crew ladder and are not restated here; (5) the finale window is extrapolated above r 1.05 (`KNOT_WINDOW_105` ends at 1.05).


The bullets below are the original 2026-11-02 season-runner proposal. The "leveling barely moves win rates" finding describes the old CLI (`player × ENCOUNTER_RATIOS`), not the live ladder; the "blocker for picking a debt number" is resolved by the live econ-v1 amounts.

- **Key finding from the code:** opponent level is `round(player level × ratio)` (`cli.py:305`) and opponent QTE is fixed per encounter (`ai.py:292-308`). Raising the player's level therefore barely changes win rates, because opponents scale with the player. **Under the current model, parts are the only thing that moves the player relative to opponents**, and "crews get stronger every round" (`canon.md:26`) has nothing behind it.
- **PROPOSAL:** in season mode, opponent level and parts come from a table, `OPPONENT_LEVEL[round][district][encounter] = TBD` and `OPPONENT_PART_TIER`, instead of from the player's level. The player's car level grows through `XP_PER_RACE[encounter] = TBD` (Jesse's DAQ, Q5). The pending encounter-scaling fix (`CHANGELOG.md:312`) should be designed for this mode.
- **No-mods check (Desmond's ask):** the player has **no parts** in scripted races 1–3 (mods unlock when the PC wins race 3), so those races must be winnable on stock stats plus levels alone. The team reports current win rates of about 100% for wild races and about 0–0.6% for lieutenant/boss races. **I have not verified that here, because nothing may run**. If it holds, the no-mods early game fails at crew and boss races until the scaling fix lands. **Flag: blocker for picking a debt number.**
- Intended curve (**PROPOSAL**, targets come from Austin): win-rate bands per round and encounter type, with and without parts. The gap between "with parts" and "no parts" is how much parts matter.

---

## 9. Sim architecture

### 9.1 New modules (PROPOSAL)
| File | Role |
|---|---|
| `sim/velocity_shift/parts.py` | Load the catalog, validate a loadout (slots, level floors, ownership), and `apply_parts(stats, loadout) -> CombatantStats`. Pure functions |
| `sim/velocity_shift/economy.py` | Wallet and debt ledger, `payout()`, `price()` (with wholesale), `pay_debt()`, `buy()`. Pure functions plus one small `Ledger` dataclass |
| `sim/velocity_shift/campaign.py` | Season runner: walks Prologue → R1 Street → R2 Wangan → R3 Touge (one crew each) × (wild, crew, boss), runs each race through the existing `SimulationRunner`, applies payouts, debt, XP, shop unlocks, and retries |
| `sim/velocity_shift/shop_policy.py` | Simulated player's buying and equipping rules (e.g. "best affordable part that fits the archetype"). Several policies make it possible to test whether a purchase was a good choice |
| `sim/config/parts.json` | Part catalog (id, category, tier, level floor, price, effects, rarity, unlock source) |
| `sim/config/season.json` | Season layout: race counts, opponent levels and part tiers per round/district/encounter, boss → rare part unlocks, story flags (wholesale at end of R1) |
| `sim/scripts/run_season.py` | Batch runner: N seeds → metrics JSON/CSV |

### 9.2 Where values live
- **Rules and knobs** (`DEBT_AMOUNT`, `DEBT_SHARE`, `DEBT_RULE`, `WHOLESALE_DISCOUNT`, payout bases and multipliers, retry fee, XP, slot unlock levels) go in `equations.py` under a new "Economy" header, per `01-system-overview.md:133`.
- **Content** (individual parts and the season layout) goes in JSON data files, like `sample_builds.json`.
- **Separately (C10):** move `ENCOUNTER_RATIOS`, `TYPICAL_QTE` and `ENCOUNTER_MAX_TURNS` into `equations.py` as part of the scaling fix.

### 9.3 Data flow
```
season.json ──► campaign.py ──► for each race:
                 │  player stats = parts.apply_parts(cars.build_stats(arch, lvl), loadout)
                 │  opp stats    = parts.apply_parts(build_stats(opp_arch, opp_lvl), opp_parts)
                 │  SimulationRunner(MatchConfig) ──► winner
                 │  economy: payout → debt first (DEBT_RULE) → wallet; XP → level
                 │  story flags: boss win → shop unlocks; end R1 → wholesale
                 └► shop_policy: buy/equip ──► next race
            ──► metrics JSON/CSV
```

### 9.4 Existing code that would change (after approval)
- `models.py`: `MatchConfig` (or the caller) gets final stats after parts. `CombatantStats` (`models.py:43-54`) stays the same, because parts resolve into pow/en/han before the match.
- `equations.py`: an Economy constants block. v2 adds additive hooks for unique effects.
- `simulation.py`: optionally lets campaign mode pass its own opponent QTE/level instead of `ENCOUNTER_RATIOS` (`simulation.py:69-71`).
- `cli.py`: a "Season" menu entry and a loadout picker. Single matches stay as they are.
- `design/01-system-overview.md` and `04`: sync when anything lands.

### 9.5 Test plan outline
- `parts`: level floors enforced, slot limits enforced, trade-offs applied, HP unchanged, bonuses additive.
- `economy`: the debt never goes negative, overpayment flows to the wallet, wholesale applies only after the flag, nothing can be bought while the debt is open under rule A, retry fee follows Q9.
- `campaign`: deterministic with a fixed seed, rounds run Street, Wangan, Touge with one crew each (2026-11-13; the live `progression` tests use this same `DEFAULT_CREW_ORDER`, the only legal order), a boss loss always retries, the season always terminates (retry cap as a safety stop).
- Regression: with no parts and no economy, single-match results match today's `SimulationRunner`.

---

## 10. Candidate metrics (no targets. Austin sets those)

1. Money over time (per race and per round), split into debt paid, wallet balance and spent.
2. The race where the debt clears: median and 10th–90th percentile spread across seeds.
3. Races (and retries) needed to clear the debt.
4. Win rate per round × district × encounter type, **with parts vs with no parts**.
5. Boss retries per boss: mean and max.
6. Parts owned and slots filled at the end of each round (especially at the start of Round 3).
7. Total wholesale savings, split into during the overlap and after the debt clears.
8. Money left unspent at season end (is there anything to buy?).
9. Share of income from wild races (farming check).
10. Player vs opponent effective power per round (stat totals after parts, levels, HP).
11. How often each part is bought or equipped (dead or overpowered parts).
12. Deck-mix shift caused by parts (POW/EN/HAN share).
13. Betting: share of Round 3 income from bets, the bettor's average return at fair odds, and the chance of going broke under each betting policy.
14. Substories: share of wallet cash and debt repayment from substories, how much clearing zero vs all substories shifts the end-of-Round-1 debt-clearing race, and equip rate of free substory sidegrades vs Reiko's paid shop parts.

---

## 11. Open questions (FIFO — oldest first)

Pull from the top, one at a time; new questions go to the bottom. Remove a question once Austin answers it and record the answer in the section it affects.

1. (2026-11-01) ~~**Encounter-scaling fix:** approve a proposal before any debt or payout numbers are set (§8)?~~ Live purses, debt and prices are set (econ-v1, 2026-11-13). The old note that leveling barely moves win rates described the pre-ladder CLI.
2. (2026-11-02) **Success criteria** for the economy and mods sim. Nothing runs until these arrive and this spec is approved.
3. (2026-11-02) ~~**Which Round 2 race clears the debt?**~~ Resolved 2026-11-13: the Street crew boss at the end of Round 1.
4. (2026-11-02) **Overlap add-ons:** a share of each win goes to the debt (canon decision 19). Do C (boss money is free) or D (Reiko cuts the bill) layer on top? Desmond's alternative: purses go fully to the debt and bonus payouts trickle to the PC.
5. (2026-11-02) **How does the car level up?** **Answered (Austin, 2026-11-09):** XP from story wins and grind races fills levels, and levels pay skill points (§8.0). Number kept so Q6+ references stay valid.
6. (2026-11-02) **Part bonuses:** flat or scaled with level?
7. (2026-11-02) **Slots:** about 3 growing to 8–10, or 5 plus 1 car-specific? (C4)
8. (2026-11-02) **Wild races:** capped per district, low-paying, or uncapped? (C9)
9. (2026-11-02) **Losing:** is there a retry fee, and does it add to the debt? (C8)
10. (2026-11-02) Any *repeatable* income besides races (e.g. garage work)? One-time substory cash rewards are locked in canon 28 (§5.3).
11. (2026-11-02) Can parts be sold back?
12. (2026-11-02) Should crews getting stronger come from opponent levels, opponent parts, or both (§8)?
13. (2026-11-02) Can the PC switch cars or archetypes, or is it one car for the whole game (`mod_notes.md:70`)?
14. (2026-11-02) Is the Prologue race with Sabine simulated (scripted loss) or skipped?
15. (2026-11-02) Does money matter in the Finale?
16. (2026-11-02) **Betting (§7.5):** stakes ($500–$2,000) and fair odds are live (econ-v1). Still open: own races only vs the live `BET_ELIGIBLE` = any, and handicap bets in or out of v1? The unlock is settled: end of Round 2.
17. (2026-11-02) **Body kits and wings:** Arthur says each needs a full alternate body mesh per car. In or out? Texture swaps and stance are cheap and already possible.
18. (2026-11-03) **Respec cost:** what are `RESPEC_POINTS_PER_VISIT` (points moved per visit) and `RESPEC_COST_PER_POINT`, for Jesse's skill points and for aero retunes? Should the two share values? Expensive but always possible.
19. (2026-11-04) **Losing the race-3 gate:** mods need a *win* at scripted race 3 (canon 19), so what happens when the player loses race 3: an immediate rematch with the same driver, or more races until they win one? And for crew members and crew bosses (who remember losses per canon 27), should a remembered loss change the rival's difficulty or only their dialogue?

**Progression (Austin, 2026-11-04, canon 19 and 27; canon 27 narrowed 2026-11-05):** races 1–3 are scripted and use skill points only. Regular mods (bought once from Reiko at full price) unlock when the PC **wins** race 3, because Reiko sees the PC is serious (`MOD_UNLOCK_RACE = 3`, win required), and the open world (wild races, searching out lieutenants, substories) opens with them. Beating lieutenants expands Reiko's horizontal shop stock while crew bosses unlock rare mods; substories award cash (through the open repair-tab cut), free skewed-sidegrade mods (never aero), shell-specific liveries, or rare oddball shells (canon 26, 28). Wholesale unlocks at the end of Round 1, aero when the debt hits zero (end of Round 1, Street crew boss, 2026-11-13), and betting at the end of Round 2, which pays for pricier mods in Round 3. Loss persistence applies only to crew members (lieutenants) and crew bosses—a driver who beats the PC remembers it—while wild races and Myth Driver races don't have loss persistence. There's no grinding before race 3, so it has to be winnable at starting stats with tutorial-level play, and a rematch happens at the same stats. Skill points in v1 override "No skill trees in v1" in the old build guide and 05. Still to define: where points come from, how much a point is worth, and respec limits (Q18).

Resolved: rep is lore only, with no tracked number (Austin via Nathaniel, 2026-11-02). Mods may show on the car within the car rules (Arthur, 2026-11-02).

**Flags:**
- **Desmond / Nathaniel (story):** the overlap rule (Q4) and option D are story changes. Jesse's DAQ as the leveling reason, and as the fixed car-specific slot (Q5). The in-world currency name is still TBD (canon 6); the sim unit is USD.
- **Arthur / Desmond (art & scope):** `Notes.md:40` says perma mods change the car's look; part categories (§6.3) will need visual variants if that holds. Canon 26/28 also adds a small pool of standout substory shells (`SUBSTORY_SHELL_COUNT = TBD`, full body meshes) alongside cheap per-shell UV livery swaps (`art_direction.md` A.3); confirm mesh budget before locking shell count. No art work is requested until approved.
- **Blocker (resolved for live amounts):** the old encounter-scaling fix is no longer gating the live purses, debt and prices (econ-v1). Respec costs, substory cash, retry fees and the T4 stand-in are still open.
