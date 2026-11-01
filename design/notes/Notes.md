### Opponent design
- I want to have opponents that are designed to force players to move towards a certain build
  - Determine if there's any one archetype that can defeat all of the others. 
- Opponents should have some sort of smart AI, like they're a bruiser build so they attack more often but they're also not retarded and pick attack all the time so you exploit with a EN heavy build.

#### Resolved

### Pink Slip Races 
- how am I going to handle the rougelite portion? I don't want players to use a high level car -> get rarer mods -> install them on low level cheap cars -> cheese the fuck out of low level races. 
- The intent for wild races is to have an algorithm generate evenly matched opponents to create skill up races, but if players farm rare mods and install them on the low level cars, now they'll be OP
- easiest way to resolve this would be to have a level floor for each mod, so you cna't install it on low level cars. 

#### Resolved

### Skills Gaps
- When programming actual game, cars need to be designed such that lieutenant builds are always stronger than player builds per the values in ai.py
  - Could just auto-generate stat values
    - This would lead to "boss gets weaker when player acquires" trope, need to be careful. 
  - Could just gate progression with diminishing returns until player defeats lieutenant/boss.
- Wild encounters can be auto-generated. 

#### Resolved
- HAN is a multiplier to opponent QTE. Opponent QTE is a function of player QTE score.

### Leveling 
- Leveling system??? How do????



#### Resolved
- come up with a way to enforce stat cap per level
  - Stat cap is done with the curve, and 05-skill-trees.md outlines the variance allowed with each archetype. \
- Since this is a rouge-lite, should there be pokemon style IVs on the cars? That would be kinda cool and make it fun. 
  - No longer rogue-lite

### Per Car Build 
Each car shall have: 
- 5 inventory slots 
- 1 "car specific" slot (maybe this could be the IV, make it such that it's not removeable) 
- all cars have perma mods that also affect visual identity

#### Resolved 
- Car build starts neutral, and moves towards curve build. 

### HP System


#### Resolved
- HP is now `level × hp_per_level` — a standalone value, decoupled from any stat
- Multiplicative damage pipeline, EN-based mitigation, clash system all unchanged
- Three encounter profiles tuned via `hp_per_level`: Wild (34), Standard (67), Boss (100)

### Race Position Display

Don't use raw HP remaining — it breaks when max HP differs (boss 1.15× = +1080 HP at L60).

**Use proportional damage taken instead:**
```
position_delta = (opponent_total_dp / opponent_max_hp)
               - (player_total_dp / player_max_hp)
```

Edge cases this resolves:
- **Boss fights:** Player with 4000/7200 (56% dmg) vs opponent 3500/8280 (42% dmg) → raw HP says player ahead (4000 > 3500), but proportional says opponent is less damaged (42% < 56%) → player is actually behind
- **Double KO:** Both at 100% → delta = 0, trigger DP tiebreaker notice
- **Decision:** Aligns with `match.py` HP% winner logic
- **Sudden death tie:** Delta = 0, player wins by rule

Visual: two HP bars labeled `current / max`, a `+X%`/`-X%`/`-` delta indicator, race position driven by `position_delta`, not raw HP.




