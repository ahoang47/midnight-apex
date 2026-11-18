> **SHELVED (Austin 2026-11-18, after sims):** skill-tree not suited to the intended gameplay; back to mod_skill.

> **THOUGHT EXPERIMENT ONLY (Austin 2026-11-18):** skill_tree is a side experiment, not the current build. The build direction is mod_skill.

# skill-tree-v1: driver tree + car trees (Barry DRAFT, 2026-11-18, touge-race @ bbdda07)

Austin's direction: the **driver** is the persistent character, with an EXECUTION tree. **Cars are RPG weapons**: each car
has its own POW/HAN/EN tree, its own mods (like upgrading a sword) and its own play style. The driver outgrows a car, so it gets
replaced. Files: `DRIVER_TREE.md`, `CAR_TREE.md`, this README.

Tags: **[sim]** = from sim/velocity_shift or a Barry study (source named). **[PH]** = placeholder, not measured. Untagged design
text is a proposal.

## 1. The model in one table
| | Driver | Car |
|---|---|---|
| Persists | the whole game | one round (tier), then replaced |
| Earns | driver XP → levels (today's curve) → driver points | car points (mod_skill story/grind XP) → the car's tree nodes |
| Holds | execution: QTE, reading, heat craft, pacing, spirit | stats (POW/HAN/EN), mods, one signature quirk |
| Ceiling | L115 [sim: FINALE_CAP_LEVEL] | the tier cap: 3532 / 4044 / 4628 points [sim: mod-skill-v1] |

## 2. Today's numbers it builds on [sim]
- **Levels:** SP(L) = 240 × 1.10^(L/12). At 10 points per SP that is 2,400 points at L0. Levels give 19.1 points each at L0,
  47.3 at L114 (the code comment rounds this to 48) and 47.7 at L115. The cap is L115 (5,983 points).
  XP to the next level is 100 × 1.08^L. Cumulative XP is 1,898 at L12, 10,397 at L29, 41,843 at L46 and 8.72 M at L115.
- **Level caps:** R1 / R2 / R3 L12 / 29 / 46; finale L64 / 79 / 94 / 115.
- **mod_skill** (mod-skill-v1, recommended):
  - Stock car 3,000 points (2,400 + 4 × 150 stock parts), with a free setup inside 25-50 % per stat.
  - 4 mod slots, each with an earned-points ceiling of 133 / 261 / 407 by tier, giving 3,532 / 4,044 / 4,628 points at the R1 / R2 / R3 caps.
  - Own-stat share X = 0.60. Kits PPHE / PHEE / PHEE. Overflow spills to the next mod.
  - It reproduces the live campaign within 0.1-1.0 pp.
- **District tunes (POW/HAN/EN):** Street 50/25/25, Wangan 25/25/50, Touge 45/25/30.

## 3. XP split: two currencies per race, not a split of one pool (proposal)
- **Car points = the mod_skill story and grind XP tables, unchanged.** Those tables are calibrated in car points and reproduce the
  live power curve, so the car side needs no new tuning.
  - Story R1 145.0 / 115.8 / 26.9 / 25.1 / 27.0 / 26.8 / 154.3, R2 and R3 in mod-skill-v1/planner/constants.ts.
  - Grind 13 / 15 / 14 per win.
- **Driver XP = today's level XP at the same races, unchanged.** The level curve and the caps L12 / 29 / 46 stay. Levels stop adding
  stats. They add driver points instead: 1 per level [PH], which gives 12 / 29 / 46 points by the R1 / R2 / R3 caps and 115 at L115.
- Why not split one pool (f to the driver, 1 − f to the car)? Every f below 1 under-feeds the car against the calibrated curve,
  so the ladder would need refitting. Two currencies keep both calibrations. If one pool is wanted anyway, f is an open question (§6).
- **Balance warning:** stats then come only from the car, which is exactly mod_skill and is verified. The driver tree is NEW
  execution power on top. Like spirit (spirit-meter-v1: one +25 %/3-turn activation is +5.5 pp on the curve), it raises win %,
  so the boss bands need a re-check once node values are fixed.

## 4. Car tiers and "outgrown"
- **A car's tier is the round it was built for.** It has a stock total and a ceiling, and its points ceiling is tied to the
  driver-level cap of that round [sim numbers, PH tie-in]:

  | Tier | Round | Stock points | Ceiling (cap) | Earned room | Per mod socket | Rated to driver level |
  |---|---|---|---|---|---|---|
  | T1 | Prologue + R1 Street | 3,000 | 3,532 | 532 | 133 | L12 |
  | T2 | R2 Wangan | 3,532 [PH: = T1 cap] | 4,044 | 512 | 128 | L29 |
  | T3 | R3 Touge | 4,044 [PH: = T2 cap] | 4,628 | 584 | 146 | L46 |
  | T4+ | arc / finale | open (§6) | from the finale budgets | | | L64 / 79 / 94 / 115 |

  The ceilings are the mod_skill cap points. The stock of each new tier equals the last tier's cap [PH], so a swap never costs power.
- **Outgrown means two things at once:**
  1. **The car is maxed.** Its tree is full and car points stop landing. Overflow becomes mastery (§5).
  2. **The ladder passes it.** A capped T1 car (353.2 power) in R2, hardest-track cell where it applies [sim, win tables]:
     - 80/80: kid1 87.7 %, kid2 78.8 %, mat1 21.0 %, mat2 4.7 %, boss 0.8 %.
     - 60/60: kid1 32.6 %, mat1 onward about 0 %.

     It still handles the first two races of the next round, then falls off a cliff. That is a natural "time for a new car" beat.
- **Buying the next tier unlocks when the driver reaches the previous round's cap level** (L12 / L29 / L46) [PH]. That is the
  round end, the same time as today's round unlocks.

## 5. What carries over when a car is replaced
- **Driver:** level, points and tree, 100 %.
- **Mastery:** car points earned past a full tree bank as mastery. At 100 % mastery [PH: 25 % of the tier's earned room], the
  driver permanently learns that car class's signature technique as a driver-tree node (FF9-style "learn the weapon's ability").
  This is the "sliver of mastery". It is execution, never raw stats, so it doesn't break the next tier's ladder.
- **Not carried:** the car's points and quirk. Mods stay on the car (they're fitted to the chassis). Reiko takes trade-ins at 50 %
  of the price paid [PH]; Mk1 list prices are $150 / $700 / $1,200 [sim].
- **Kept:** the old car stays in the garage for show and for substory races with a level cap (art reuse) [PH].

## 6. Open questions
1. ~~One XP pool split f vs two currencies~~ **DECIDED (Austin 2026-11-18): two currencies**, driver XP and car points earned separately.
2. **DECIDED (Austin 2026-11-18): front-loaded** so R1 gets real choices. Exact curve TBD [PH].
3. **EXPLORE BOTH (Austin 2026-11-18):** sim both A (stock = previous cap) and B (stock a bit lower). Original question: Do T2/T3 stock totals equal the previous cap (no power dip), or a little lower so the old car's mods matter at the start of a round?
4. **LEANING (Austin 2026-11-18):** one Myth car plus an Elite-4-style gauntlet: race all 3 Myth drivers back to back with no stop between races. Not final; sim the gauntlet odds. Original question: Finale tiers: one T4 Myth car or several? Finale budgets are 494.8 / 566.3 / … [sim: FINALE]; ARC MYTH mods already exist.
5. **DECIDED (Austin 2026-11-18): a choice of 2-3 car classes per round**; one story car would cheapen car-as-weapon. Original question: Car choice inside a tier: one class per round (story-led), or 2-3 per tier with an off-tune option? (An even locked base is
   9.2-14.2 share points off the Street tune [sim: mod-skill-v1]; the starter is that cost made visible.)
6. **DECIDED (Austin 2026-11-18): no driver respec; car respec is OK (free).** Original question: Respec: the car-tree split is free (mod_skill), while the driver tree follows the 20 % retune rule [sim: RETUNE_BUDGET_FRACTION]?
7. **DECIDED (Austin 2026-11-18): mastered techniques are free.**
8. **DECIDED (Austin 2026-11-18): the driver owns the meter (fill, activations); the car sets what the buff does.** Original question: Spirit meter ownership: the driver (meter, fill, activations) and the car (what the buff is)? Proposed in DRIVER_TREE §E and CAR_TREE §2.
9. **EXPLORE BOTH (Austin 2026-11-18):** test spirit as multiplicative (x1.25) and as an additive clash_stakes bonus. Do not sim yet. Original question: Additive-only rule (design/05 §1): spirit's payoff buff is multiplicative in the prototype. Recast it as an additive
   `clash_stakes` bonus before shipping?

## 7. Story and art impacts
- **Arthur (art): cars become characters.**
  - One hero model per class: starter hatch, street tuner, AWD GT and light FR, plus a T4 Myth car.
  - Each needs visible mod states per socket (3 tiers) and a mastered or "retired" garage pose.
  - That is at least 4-5 new car models instead of one evolving car, plus a garage scene.
- **Desmond (story): the trade-in is a story beat every round.**
  - Reiko sells or builds the next car, Sabine reacts, and the old car's retirement gets a send-off.
  - The car should feel like a partner, Initial D style. Mastery techniques need names and one line of lore each.
  - Who gives the PC each car, and does the Prologue car come back (in the finale or as a keepsake)?
- **UI:** a garage screen, a car tree screen, a driver tree screen and a mastery bar.

## 8. Gym structure (Austin 2026-11-18, proposal direction)
- Pokemon-style rounds: multiple crews per round = gyms; each crew boss = gym leader, lieutenants = trainers. Mandatory road races between crews (free roam: drivers approach the player).
- Crews per round and mandatory races between crews: **set by sim** (not run yet).
- Optional grind races: **stay optional**, alongside the mandatory ones.
- Losing a mandatory race: **blocks progress**.
- Needs Desmond / Nathaniel / Arthur before build (round structure, rosters, art count).
