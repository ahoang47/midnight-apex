# Canon — Source of Truth

Decisions made by the lead (Austin). If any other story file disagrees with this page, this page wins. Major plot points change only with the lead's approval.

---

## Decisions

1. **Three Myth Drivers, one per district.** #1 Touge, #2 Wangan, #3 Street. There is no #4.
2. **No informant.** The police sweep was benign and coincidental. The snitch accusation was a convenient story each Myth Driver used to cover his own personal reason for pushing Sabine out:
   - #1 — distrust of her uncle-dad, a detective
   - #2 — she turned down his date request
   - #3 — jealousy; he wanted her out of the way (see 9)
   - Always called the **police sweep** (not "sting operation").
3. **Sabine doesn't know.** She genuinely believes she was ousted over the snitch rumor and learns the real reasons only at the end.
4. **Climax at the summit.** The player tricks all three Myth Drivers *and* Sabine into meeting at the summit of **Fushigi-Yama**, the Touge district's mountain. That's where the truth comes out. Racing each Myth Driver in his district during Act 2 stays.
5. **Ending.** Sabine calmly declines their offer to rejoin because she has the player's crew now, then gets in one cutting parting shot: `<TODO: parting shot — Austin to approve>`.
6. **Setting.** A fictional mashup city, neither Japan nor the US. No real-world places or currencies. City name, in-world district names and currency are `<TBD>`.
7. **Time of day.** The opening happens at dusk; the game is at night from then on.
8. **Gender.** Sabine is always female. The player character can be any gender.
9. **Myth Driver #3 is the Street specialist.** Circuit and street racing are the same idea in this universe. His extra motive: he wanted out, to go pro in the circuit.
10. **Silence since the breakup.** The Myth Drivers haven't spoken since the breakup. Anything about them talking to each other happened before it. The summit is their first meeting since.
11. **Act structure.** Prologue → Rounds 1–3 → Finale.
    - **Prologue:** dusk arrival, the overworld tutorial on the drive home from work, the race with Sabine, the blowout, the garage intro and the debt.
    - **Rounds 1–3:** each district has exactly one crew and one crew boss (three crews, three crew bosses in total). Each round the player faces each district’s crew and its crew boss in Touge, then Wangan, then Street, in that order; Rounds 2 and 3 are rematches against the same crew, which gets stronger every time. Every crew defeat reveals another piece of the police sweep mystery.
    - **Round themes:** Round 1 = the incident, Round 2 = its consequences across the scene, Round 3 = distortion (what people misremember), each seen from every district.
    - **Finale:** finishing Round 3 unlocks the three Myth Driver encounters (one per district), then the Fushigi-Yama summit and the ending.
    - The main plot stays grounded; JRPG weirdness and extra lore go in substories and side quests.
12. **Street cred gates the rotation.** After the player beats a crew, it won't give them a rematch until they've proven themselves in the other districts: they don't have enough street cred yet. Cred is earned by beating the other districts' crews, which is why each round rotates Touge → Wangan → Street. Street cred is an in-world lore explanation only, not a tracked stat.
13. **Player character (first pass).** The PC is mid-20s and any gender, moved to the city for work, but is really running from something: they walked out on their own crew/family without explaining why. This mirrors Sabine, who was pushed out of her crew over a lie. Helping Sabine reconcile is the PC working through their own guilt by proxy. At the summit Sabine may turn it back on them ("And when are you calling them?" — `<PROPOSAL>`).

---

## Racer Types and Archetypes

"Racer type" is the story role (Delinquent, Salaryman, ...). "Archetype" is the driving style from the sim (`sim/velocity_shift/`). Each district has exactly one racer type per archetype; each racer type always uses its archetype. Only named rivals may break the pattern, on purpose.

| Archetype | Touge | Wangan | Street |
|---|---|---|---|
| **Aggressive**: attacks right away | Delinquent | Executive | Punk |
| **Defensive**: waits, then punishes your habits | Gang Leader | Office Lady | Mechanic |
| **Precise**: always makes the smartest move | Drifter | Doctor | Engineer |
| **Balanced**: follows a set rhythm | High Schooler | Salaryman | Skater |
| **Adaptive**: cautious early, sharper later | Honor Student | Consultant | Influencer |

Never reuse archetype names as character or racer-type names. Crew boss stakes are money, rep, rare shop mods and story progress; losing a crew boss race means a retry, never losing the car.

## Backstory Timeline

1. **The old generation.** Sabine races alongside the three Myth Drivers. Pressure builds privately: #1 never trusts her because of her uncle, #2 resents the turned-down date (a low-level racer saw it and spread rumors), #3 is jealous and wants out to go pro.
2. **The police sweep.** A benign, coincidental sweep hits the scene. The snitch rumor attaches to Sabine, and each Myth Driver uses it as cover for his own reason. Sabine is ousted.
3. **The breakup.** The old generation fractures. The Myth Drivers stop speaking to each other and fade into semi-retired legend. Sabine builds her own garage crew, still believing the rumor was the reason.
4. **The player arrives.** The player moves to the city at dusk. A first race with Sabine ends in a blown engine; she tows the car to her garage and the player enters the scene owing a repair debt.
5. **Rounds 1–3.** Each round the player beats the same three crews and their crew bosses (each stronger than last time) in Touge, then Wangan, then Street, earning the street cred for the next rematch; every crew defeat reveals another piece of the mystery. Sabine deflects; when confronted she says she was present but was not the informant (where this confrontation sits is a `<PROPOSAL>` in `plot.md`).
6. **The Myth Drivers.** Finishing Round 3 unlocks a race with each Myth Driver: Touge (#1), Wangan (#2), Street (#3). The player gathers contradictory accounts.
7. **The summit.** The player tricks all three Myth Drivers and Sabine into meeting at the summit of Fushigi-Yama. The truth comes out, and Sabine learns the real reasons for the first time.
8. **Ending.** They reconcile and offer Sabine her place back. She calmly declines because she has the player's crew, and gets in one parting shot.

---

## Open Questions

- **Names:** the city, in-world district names, currency, the three Myth Drivers, the three crews and their crew bosses (all `<TBD>`).
- **Parting shot:** Sabine's final line (`<TODO: parting shot — Austin to approve>`).
- **The sweep:** details of the informant-free police sweep (when, what triggered it, who was caught, why Sabine was "present"), and how the uncle-dad fits in, if at all.
- **The summit setup:** how the player tricks each Myth Driver and Sabine into coming (`plot.md` §8 "They each individually agree" is a TODO).
- **Crews and crew bosses:** identities and organizers of the three crews, how each crew escalates between rounds, and the story reveal each crew defeat gives (several round slots in `plot.md` are `<TODO: reveal>`).
- **Substories:** none written yet.
- **PC backstory:** who the PC walked out on, why, and whether they ever call (`<TBD>`); Sabine's "And when are you calling them?" line at the summit is a `<PROPOSAL>`.
- **Tuner and Buyer:** names and personalities for Sabine's garage crew; the rest of the garage intro script.
- **Debt terms:** how much the player owes for the rebuild and how racing repays it.
