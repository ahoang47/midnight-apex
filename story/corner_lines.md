# Corner Lines: In-World Reasons

Narrative flavor for the district corner lines. This file has no numbers. Each line is written Entry-Apex-Exit by stat: **POW**, **EN** or **HAN** (Austin 2026-11-12: everything behind the screen refers to stats; IN/MID/OUT is only the on-screen lane, with OUT = POW, MID = HAN, IN = EN relative to the corner). The lines are Barry's `LINE_SET_C` (sim letters A/D/S = POW/EN/HAN) in `sim/velocity_shift/equations.py`, read at `6fc87d5` and rechecked unchanged at `5e5d902`. Adherence and alt weights (`LINE_ADHERENCE`, `LINE_ALT_WEIGHTS`) are Barry's too. If the table changes, the lines here follow it and only the reasons get rewritten.

Alternative lines keep the main Entry. alt1 changes Apex and Exit, alt2 changes only Exit. The lane bluff (sitting in the wrong lane, design 06) is a separate layer and isn't covered here.

## Main lines

| Corner | Touge | Wangan | Street |
|---|---|---|---|
| Hairpin | EN-HAN-POW: brake on EN, roll the apex, drive off the turn to carry momentum down the hill | EN-HAN-POW: the same textbook hairpin, since highway crews treat a hairpin as a tollbooth, not a fight | EN-EN-POW: hold EN through the apex so nobody gets a nose in, then go |
| Constant radius | HAN-HAN-POW: hold the arc, carry speed, power out | HAN-POW-POW: the road stays open, so commit from the apex on | EN-HAN-EN: cover with EN, ride it out, cover again on exit, position over speed |
| Decreasing radius | HAN-EN-HAN: the mountain pinches, so protect at the late apex and smooth out | EN-EN-HAN: professionals don't gamble on a closing corner | EN-EN-HAN: door shut until it opens |
| Increasing radius | HAN-HAN-POW: patient, then let the road open up | POW-POW-EN: the road opens, so go flat out, then shut the door on the exit so the car behind can't use your draft on the next straight | HAN-HAN-POW: even Street lets an opening corner run |
| 90-degree | EN-HAN-POW: square it off, drive out | EN-HAN-POW: same | HAN-HAN-POW: it's an intersection, so you can't dive the corner of the block. Hold your lane through the cross street, then punch it out |
| Chicane | HAN-EN-POW: settle, protect the middle flick, drive out | EN-HAN-POW: brake early, keep it tidy, go | EN-POW-POW: protect the entry, then muscle through the flick |
| Esses | HAN-HAN-HAN: flow, with no stance changes and no lost momentum | HAN-HAN-HAN: same, since nobody wants to be the one who breaks rhythm on a bend | POW-HAN-POW: throw it in, settle, throw it out, loud at both ends |
| Sweeper | HAN-HAN-POW: hold the arc, power at the end | POW-POW-EN: flat out through the long bend, then close the door on the exit before the straight | EN-EN-EN: a long corner is a long time to defend |

District habits, for barks: Touge preserves momentum (mostly HAN, POW only on exits). Wangan commits where the road opens and shuts the door before the straights. Street fights for position (EN-heavy, POW as a lunge), except at intersections, where it waits out the cross street.

## Signature corners (first pass, draft 2026-11-11)

Austin's framing (locked, canon 30): each district has a handful of signature corners the player learns. On those, everyone in the district (wild racers, crew members and the crew boss) shares the same standard line and the same bluff. On every other corner, wild racers share one line and bluff, and named characters drive their own style (`plot.md` districts, Myth Driver sheets).

The corner choice below is a first pass, pending Barry's check. How it maps to the sim (which alternative counts as the shared bluff, adherence) is `<TBD: Barry>`. Each standard line is the district's main line above; no lines change.

| District | Signature corner | Standard line | Why everyone here drives it this way |
|---|---|---|---|
| Touge | Hairpin | EN-HAN-POW | Brake on EN, roll the apex, drive off the turn: momentum down the hill is how the mountain passes |
| Touge | Esses | HAN-HAN-HAN | Flow with no stance changes: nobody on the mountain breaks rhythm and loses momentum |
| Touge | Decreasing radius | HAN-EN-HAN | The mountain pinches, so protect at the late apex and smooth out |
| Wangan | Sweeper | POW-POW-EN | Flat out through the long bend, then close the door before the straight |
| Wangan | Increasing radius | POW-POW-EN | The road opens, so go flat out, then shut the door so the car behind can't use your draft |
| Wangan | Constant radius | HAN-POW-POW | The road stays open, so commit from the apex on |
| Street | 90-degree | HAN-HAN-POW | It's an intersection: hold your lane through the cross street, then punch it out |
| Street | Chicane | EN-POW-POW | Protect the entry, then muscle through the flick |
| Street | Hairpin | EN-EN-POW | Hold EN through the apex so nobody gets a nose in, then go |

Why these three: Touge's are the mountain's corners, Wangan's the open-highway corners, Street's the city-block corners.

## Alternative lines

An alternative is the line a driver takes when they think you've learned their district's habit. The lane and Entry stay honest; the difference shows at the apex (alt1) or only at the exit (alt2). On a signature corner the bluff is shared by everyone in the district (canon 30), so the who-and-why on those rows is the bark hook for who's best known for it, not who alone uses it. On every other corner the rung entries are a first pass at named characters' styles. By rung (pending Open Question 17):
- Kids: alts read as nerve or ego, not craft, either a cocky overcommit or a flinch.
- Mature members: deliberate counters ("I know you know").
- Old heads: habits from "that night" and the old generation, invisible until the apex and the hardest to learn.
- Crew boss: uses both, framed by personality (big brother, promoter, influencer).

### Touge (big-brother boss, young and gossipy kids, old heads who were there)
| Corner | Main | alt1: who and why | alt2: who and why |
|---|---|---|---|
| Hairpin | EN-HAN-POW | EN-EN-HAN: old head. "Don't win it on the hairpin, the downhill does the passing." Stays tucked and lets you run wide | EN-HAN-HAN: kid flinch. Doesn't trust the rear on the exit and feathers it |
| Constant radius | HAN-HAN-POW | HAN-EN-HAN: mature member closes the door mid-arc, having heard outsiders dive the long ones | HAN-HAN-HAN: old head saves the run for the next corner, momentum over the exit |
| Decreasing radius | HAN-EN-HAN | HAN-POW-EN: old head who knows exactly where this road pinches attacks the pinch, then shuts the door | HAN-EN-EN: kid gets spooked by the tightening and covers on the exit |
| Increasing radius | HAN-HAN-POW | HAN-EN-HAN: mature member sits on you mid-corner instead of opening up | HAN-HAN-HAN: the boss's "fair race" restraint, he doesn't pounce on the exit |
| 90-degree | EN-HAN-POW | EN-EN-HAN: old head blocks the corner and rolls out calm | EN-HAN-HAN: kid lifts out of the 90 after a near miss the week before (bark hook) |
| Chicane | HAN-EN-POW | HAN-POW-HAN: Delinquent-type kid tries to bully the middle flick, then has to steady it | HAN-EN-HAN: mature member keeps it tidy on exit to set up the next bend |
| Esses | HAN-HAN-HAN | HAN-EN-EN: old head. Once the flow breaks, he closes the whole second half | HAN-HAN-EN: boss protects the exit of the esses, protective of his crew's road |
| Sweeper | HAN-HAN-POW | HAN-EN-HAN: mature member covers mid-sweeper when you show a nose | HAN-HAN-HAN: old head never attacks a sweeper exit "since that night" (fog and memory hook) |

### Wangan (promoter boss, polite and cliquey professionals)
| Corner | Main | alt1: who and why | alt2: who and why |
|---|---|---|---|
| Hairpin | EN-HAN-POW | EN-EN-HAN: Office Lady-type mature member protects the car and plays the long game | EN-HAN-HAN: old head lifts on exit. "Nobody pays to see a wreck." |
| Constant radius | HAN-POW-POW | HAN-HAN-HAN: mature member refuses to commit in front of a reader and holds steady | HAN-POW-HAN: old head commits at the apex but saves the exit for the straight |
| Decreasing radius | EN-EN-HAN | EN-POW-EN: promoter "makes it a show" with a surprise apex lunge, then shuts it | EN-EN-EN: mature member, full block, by the book |
| Increasing radius | POW-POW-EN | POW-HAN-POW: old head who raced before everyone learned to block exits goes in hot, settles the apex, then races you out of it the old way | POW-POW-POW: kid forgets to shut the door and just floors it, the honest rookie habit |
| 90-degree | EN-HAN-POW | EN-EN-HAN: mature member, tidy, defensive, professional | EN-HAN-HAN: old head, no heroics on exit |
| Chicane | EN-HAN-POW | EN-EN-HAN: mature member keeps the door closed through the flick | EN-HAN-HAN: kid lifts on the exit, intimidated by the crowd |
| Esses | HAN-HAN-HAN | HAN-EN-EN: old head. If the rhythm breaks, he locks down the rest | HAN-HAN-EN: promoter covers the exit when the betting line favors him |
| Sweeper | POW-POW-EN | POW-HAN-POW: mature member reads your nose mid-sweeper, settles, then attacks the exit to beat you to the straight | POW-POW-POW: promoter plays to the crowd and goes flat out end to end when the money's on him |

### Street (influencer boss, a loud, online, clout-driven crew, old heads who paid for the sweep)
Street is the thinnest district, so its alternatives should be the most legible and personality-driven. A player who has listened to the Street crew should be able to guess who deviates and why.
| Corner | Main | alt1: who and why | alt2: who and why |
|---|---|---|---|
| Hairpin | EN-EN-POW | EN-POW-HAN: Punk-type kid's dive-bomb for the clip lunges at the apex and can't put the power down | EN-EN-HAN: old head who did sixty days doesn't floor it out of anything anymore |
| Constant radius | EN-HAN-EN | EN-EN-POW: mature member blocks the whole arc, then gets greedy at the exit | EN-HAN-POW: kid forgets the plan and floors it on exit ("for the camera") |
| Decreasing radius | EN-EN-HAN | EN-POW-EN: influencer lunges at the pinch for the shot, then shuts the door | EN-EN-EN: Mechanic-type mature member protects the car and the position |
| Increasing radius | HAN-HAN-POW | HAN-EN-HAN: mature member, the group-chat theorist. "Everyone says you counter the opener," so he covers mid-corner | HAN-HAN-HAN: old head lets you go and saves it for the next block |
| 90-degree | HAN-HAN-POW | HAN-EN-HAN: old head. Corners of the block are for blocking, so he sits on the apex and rolls out calm | HAN-HAN-HAN: kid who got pulled over filming this intersection last month stays off the throttle out of the 90 |
| Chicane | EN-POW-POW | EN-HAN-HAN: influencer smooths the flick so the onboard footage stays clean | EN-POW-HAN: old head muscles the middle but stays calm on exit |
| Esses | POW-HAN-POW | POW-EN-HAN: mature member throws it in, then shuts the second half | POW-HAN-HAN: kid throws it in loud, then runs out of nerve |
| Sweeper | EN-EN-EN | EN-POW-POW: kid gets bored blocking and floors it, the cocky overcommit | EN-EN-POW: influencer blocks all the way, then sends it for the finish-line shot |

Street story hook: kids announce their habits on stream ("Watch me send it into turn two"), which makes Street's alts the easiest to learn from barks. The sixty-days old head's hairpin alt2 (never floors exits) is the mechanical echo of his reveal line.
