 - the webpage sim doesnt take into account how a player gets better at reading lines over time
 - The mods don't seemingly add a ton of flavor, seems like we can get away with just MK1 mods each round, the additional mods are unnecessary. I know I asked for that, but nothing incentivizes players to get new mods. 
    - How about instead, mods are required to get skill points, and each mod has a ceiling of skill points it can get? For instance, MOD_R2_POW_MK2 has a total of 249 points, how about we make 249 the ceiling and set it to a floor that is balanced? We remove the skill points from solely leveling. 
    - Proposed update: You have a stock car, no mods. Grinding doesn't gain you any XP, but it earns you some cash. You use the cash to buy mods. Each mod starts at 0 XP, and has a ceiling of skill points. Each pool of skill points is freely assignable, but in a ratio. I.e., POW mod gets a pool of stat points that you can assign to POW/EN/HAN, but the majority of points need to be applied to POW. This may mess with the retuning spec. 
- Second, independent thread, proposed update from a different LLM changing completely how we handle things. 
# Racing RPG Design Discussion
## Transcript and Design Summary

### 1. Translating a traditional RPG into a racing RPG

**Initial premise**

Explore how the systems of a classless action RPG, such as *Skyrim* or *Elden Ring*, could translate into a racing RPG centered on touge, wangan, and street racing.

The initial RPG framework includes:

- Attributes
- Skills and proficiencies
- Abilities and techniques
- Equipment
- Progression and character builds

**Core translation**

The driver is the persistent RPG character, while the car functions as equipment.

This allows the player to change vehicles without losing the progression of their character.

| Traditional RPG | Racing RPG |
|---|---|
| Character | Driver |
| Character attributes | Driver attributes |
| Weapon | Car |
| Weapon scaling | Driver/car compatibility |
| Weapon upgrades | Vehicle modifications |
| Weapon skills | Driving proficiencies |
| Abilities | Driving techniques |
| Equipment accessories | Performance accessories |
| Armor | Safety equipment |
| Weapon affinity | Vehicle tuning/setup |

### 2. Driver attributes and proficiencies

Potential driver attributes:

- **Reflexes:** Reaction time and maneuver execution.
- **Precision:** Accuracy of steering and driving inputs.
- **Composure:** Resistance to mistakes under pressure.
- **Awareness:** Recognition of traffic, opponents, and surroundings.
- **Technique:** Effectiveness of advanced maneuvers.
- **Adaptability:** Ability to drive unfamiliar vehicles.

Potential driving disciplines:

**Touge**
- Cornering
- Racing line
- Apex management
- Trail braking
- Weight transfer
- Corner linking
- Uphill and downhill driving
- Momentum conservation

**Wangan**
- High-speed stability
- Drafting
- Slipstream positioning
- High-speed braking
- Acceleration management
- Overtaking

**Street**
- Traffic awareness
- Route familiarity
- Environmental awareness
- Rapid maneuvering
- Opportunistic passing
- Adaptability

The disciplines could share foundational proficiencies while offering specialized branches. Drivers could specialize or develop into hybrids rather than being assigned fixed classes.

### 3. Cars as equipment

Cars have their own characteristics and upgrade paths.

Potential vehicle attributes:

- Power
- Handling
- Durability
- Stability
- Weight
- Traction
- Braking
- Aerodynamics

These attributes involve tradeoffs rather than universally positive values.

Examples:

- Lightweight FR cars may favor technical touge and momentum driving.
- High-power AWD or GT cars may favor high-speed racing.
- Versatile street builds may perform across multiple disciplines.

Any car could enter any discipline. Its configuration and compatibility with a particular technique would influence its effectiveness.

### 4. Translating combat into racing

Racing does not have a direct equivalent to dealing damage in an action RPG.

Potential translations:

| Action RPG | Racing RPG |
|---|---|
| Damage dealt | Time gained |
| Damage received | Time lost |
| Critical hit | Perfect maneuver |
| Armor | Stability and protection |
| Health | Mechanical condition |
| Stun | Opponent disruption or lost momentum |
| Buff | Temporary performance advantage |
| Debuff | Handling or performance impairment |
| Enemy defeat | Opponent beaten |
| Boss health bar | Rival's competitive challenge |

Possible feedback systems include:

- Segment times
- Racing line accuracy
- Entry and exit speed
- Cornering efficiency
- Drafting effectiveness
- Technique execution grades
- Personal bests

Progression should improve the driver's available techniques, consistency, execution windows, and capabilities rather than relying exclusively on arbitrary percentage bonuses.

### 5. Driver proficiency versus vehicle compatibility

**Question explored:**

What happens when the character has a high Trail Braking stat but the car is not built for trail braking? What happens when the car is well matched?

The discussion separated three variables:

1. **Driver proficiency:** The driver's mastery of trail braking.
2. **Vehicle compatibility:** How well the car's mechanical configuration supports the technique.
3. **Execution:** How well the technique is performed.

Potential scenarios:

- **High proficiency, poor compatibility:** An experienced driver uses a car whose setup makes the maneuver difficult. The driver understands the technique, but the vehicle does not respond as desired.
- **Low proficiency, excellent compatibility:** A novice drives a car configured for the maneuver. The car responds predictably, but the driver cannot consistently exploit its capabilities.
- **High proficiency, excellent compatibility:** The driver and vehicle work together, allowing controlled entry, rotation, apex execution, and strong exit speed.

Vehicle modifications such as tires, brake balance, suspension geometry, and damping can improve compatibility.

The underlying principle:

> Driver proficiency determines what the driver can extract. Vehicle compatibility determines how well the vehicle responds and what it can give.

### 6. The distinction between player skill and character skill

**User:**

> Trail breaking as a concept lays with me, the player. Damage dealt in an rpg is different. One button push executes a swing, but a swing can deal different damage.

**Assistant:**

That's an important distinction. You're identifying a difference between **player-executed actions** and **character-mediated actions**.

In a traditional RPG, the player chooses to swing a sword. The character's stats determine how effective that swing is. The player doesn't need to personally know how to swing a sword.

Trail braking is different. If the player must
 