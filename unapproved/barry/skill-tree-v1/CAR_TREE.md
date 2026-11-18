# Car trees: one template, four classes (Barry DRAFT 2026-11-18)

Tags: [sim] from sim/velocity_shift or a Barry study; [PH] placeholder. Car points come from the mod_skill XP tables (README §3).

## 1. Template shape (every car)
```
                         [ CHASSIS CORE ]  stock 3,000 / 3,532 / 4,044 points by tier, base split set at Reiko's
                                 |         (inside the class band and the 25-50 % rule [sim: BUILD_STAT_*_SHARE])
         +-----------------------+-----------------------+
     [ POW branch ]          [ HAN branch ]          [ EN branch ]
       socket(s)               socket(s)               socket(s)        4 sockets total [sim: MOD_SLOTS = 4]; pattern per class
       stat track              stat track              stat track       earned points fill the socket's mod up to its ceiling
       quirk node @50 %        quirk node @50 %        quirk node @50 %  unlocks when that branch's sockets are half full
       capstone @100 %         capstone @100 %         capstone @100 %   unlocks when the branch is full
                                 |
                       [ SIGNATURE ] the class quirk: always on, plus a mastery technique (README §5)
```
- **Sockets are the mods** (mod_skill rule). Earned car points go into the mod you pick and spill to the next one [sim: mod-skill-v1].
  - Each mod splits its points over POW/HAN/EN with at least 60 % on its own stat [sim: X = 0.60].
  - Buying a mod tier from Reiko raises that socket's ceiling: 133 / 128 / 146 per socket for T1 / T2 / T3 cars
    [sim-derived: (cap − stock) / 4].
  - "Upgrading the sword" = buying the next tier for a socket. Prices are the Mk1 list, $150 / $700 / $1,200 [sim].
- **No extra currency.** Quirk and capstone nodes unlock from socket fill, so the tree is the visible map of the mods.
- **Quirk and capstone nodes only bend heat levers that already exist** in equations.py, for this car only:
  - corner costs (CORNER_HEAT_COST), passive load (CORNER_HEAT_PASSIVE)
  - repeat surcharge (HEAT_REPEAT_SURCHARGE 1.0)
  - capacity and recovery (HEAT_CAP_TURNS 3, HEAT_RECOVERY 1)
  - overrun (OVERRUN_SLOPE 2.0, OVERRUN_FLOOR 0.4)

  Every node value is [PH], and all values are additive offsets (design/05 §1).
- **Same shape for every car, different socket pattern, band and signature.** Players learn one tree once. The class changes
  where the points can go and what bends.
- **Spirit hook:** the class sets which spirit buff the car delivers (pay / qte / heat; spirit-meter-v1), and the driver owns the meter.

## 2. Example classes
Stat bands are inside the global 25-50 % rule. Each centres on its district tune [sim: DISTRICT_TUNE]; the widths are [PH].

### a. Starter hatch (FF, balanced): Prologue + R1, T1
- **Band:** POW / HAN / EN each 30-37 % [PH]. Sockets: P H E + 1 flex (any stat) [PH].
- **Signature "Forgiving":** a locked gauge unlocks at 0.40 × capacity instead of 0.30 [PH; sim lever HEAT_RELEASE 0.3].
- **Nodes:**
  - POW quirk: IR/SW POW cost −0.1.
  - HAN quirk: CH/ES HAN cost −0.1.
  - EN quirk: HP/N90 EN cost −0.1.
  - Capstone (any branch): +5 % recovery on that gauge [all PH].
- **Spirit buff:** pay +25 % × 3 turns (the spirit-meter-v1 recommendation).
- **Weakness:** never on a district tune. An even locked base is 9.2-14.2 share points off the Street tune [sim: mod-skill-v1],
  and STAT_M_W rewards specialising [sim: 1.0]. Fine for the Prologue, a handicap by mid R1.

### b. Street tuner (FR turbo coupe): R1 Street, T1
- **Band:** POW 45-50 / HAN 25-30 / EN 25-30 [PH] around the Street tune 50/25/25 [sim]. Sockets P P H E [sim: Street kit PPHE].
- **Signature "Overboost":** POW overrun hurts less, OVERRUN_SLOPE 2.0 → 1.5 on the POW gauge only [PH lever].
- **Nodes:**
  - POW quirk: SW/IR POW cost −0.15.
  - POW capstone: POW capacity +10 %.
  - HAN quirk: N90 HAN passive −0.1.
  - EN quirk: N90 EN cost −0.1 [all PH].
- **Spirit buff:** pay (the burst car).
- **Weakness:** brakes. N90 and HP corners cost EN 1.4 [sim: CORNER_HEAT_COST], and a 25-30 % EN share gives a small EN gauge
  (capacity follows share^1.5 [sim: HEAT_SHARE_EXP]). Hairpin-heavy tracks lock it.

### c. AWD GT (heavy grand tourer): R2 Wangan, T2
- **Band:** POW 25-30 / HAN 25-30 / EN 45-50 [PH] around the Wangan tune 25/25/50 [sim]. Sockets P H E E [sim: Wangan kit PHEE].
- **Signature "Long legs":** EN repeat surcharge 1.0 → 0.7, so it can lean on EN in back-to-back clashes [PH lever].
- **Nodes:**
  - EN quirk: EN recovery +10 %.
  - EN capstone: SW EN passive → 0.
  - POW quirk: SW POW cost −0.1.
  - HAN quirk: CR HAN cost −0.1 [all PH].
- **Spirit buff:** heat-lite, one free-heat turn at half strength. Spirit-meter-v1 measured the full version as too strong; [PH].
- **Weakness:** weight. CH and ES corners cost HAN 1.3 / 1.4 [sim], and the HAN gauge is small at 25-30 %. Chicanes lock it.

### d. Light FR (lightweight touge car): R3 Touge, T3
- **Band:** POW 40-45 / HAN 25-30 / EN 30-35 [PH] around the Touge tune 45/25/30 [sim]. Sockets P H E E
  [sim: mod-skill-v1 recommends PHEE in Touge].
- **Signature "Light on its feet":** ES/CH HAN cost −0.2 and HP HAN passive 0.3 → 0.2 [PH levers].
- **Nodes:**
  - HAN quirk: repeat surcharge on HAN −0.2.
  - POW quirk: DR POW cost −0.1.
  - EN quirk: HP EN cost −0.1.
  - EN capstone: EN recovery +10 % [all PH].
- **Spirit buff:** qte. A wider zone suits the precision car. Spirit-meter-v1 measured it as weak, so it would need a bigger amount [PH].
- **Weakness:** low total EN for long races. Over 30 turns of DR/HP corners (EN 1.3 / 1.4) the EN gauge sits near overrun.
  The overrun floor of 0.4 [sim] is its real enemy.

## 3. Rules of thumb
- Every class must reach its district tune exactly at the cap (mod_skill's pattern kits do [sim: tune distance 0.0]).
  A class band that excludes the tune is a trap.
- A quirk is worth at most one node's worth of win %, to be measured with a spirit-meter-style hook before shipping [PH].
- Opponents keep stock archetypes with no trees (design/05).
