# Corner Lines: In-World Reasons

Narrative flavor for the district corner lines. This file has no numbers. Each line is written Entry-Apex-Exit as line choices **IN** (needs EN), **MID** (needs HAN) and **OUT** (needs POW), per Austin 2026-11-12. IN/MID/OUT is relative to the corner, so OUT on a left and OUT on a right are the same choice and the same stat (design 06 lane rule). The lines are Barry's `LINE_SET_C` (sim letters D/S/A = IN/MID/OUT) in `sim/velocity_shift/equations.py`, read at `6fc87d5` and rechecked unchanged at `5e5d902`. Adherence and alt weights (`LINE_ADHERENCE`, `LINE_ALT_WEIGHTS`) are Barry's too. If the table changes, the lines here follow it and only the reasons get rewritten.

Alternative lines keep the main Entry. alt1 changes Apex and Exit, alt2 changes only Exit. The lane bluff (sitting in the wrong lane, design 06) is a separate layer and isn't covered here.

## Main lines

| Corner | Touge | Wangan | Street |
|---|---|---|---|
| Hairpin | IN-MID-OUT: brake inside, roll the apex, drive off the turn to carry momentum down the hill | IN-MID-OUT: the same textbook hairpin, since highway crews treat a hairpin as a tollbooth, not a fight | IN-IN-OUT: hold the inside through the apex so nobody gets a nose in, then go |
| Constant radius | MID-MID-OUT: hold the arc, carry speed, power out | MID-OUT-OUT: the road stays open, so commit from the apex on | IN-MID-IN: cover the inside, ride it out, cover again on exit, position over speed |
| Decreasing radius | MID-IN-MID: the mountain pinches, so protect at the late apex and smooth out | IN-IN-MID: professionals don't gamble on a closing corner | IN-IN-MID: door shut until it opens |
| Increasing radius | MID-MID-OUT: patient, then let the road open up | OUT-OUT-IN: the road opens, so go flat out, then shut the door on the exit so the car behind can't use your draft on the next straight | MID-MID-OUT: even Street lets an opening corner run |
| 90-degree | IN-MID-OUT: square it off, drive out | IN-MID-OUT: same | MID-MID-OUT: it's an intersection, so you can't dive the corner of the block. Hold your lane through the cross street, then punch it out |
| Chicane | MID-IN-OUT: settle, protect the middle flick, drive out | IN-MID-OUT: brake early, keep it tidy, go | IN-OUT-OUT: protect the entry, then muscle through the flick |
| Esses | MID-MID-MID: flow, with no stance changes and no lost momentum | MID-MID-MID: same, since nobody wants to be the one who breaks rhythm on a bend | OUT-MID-OUT: throw it in, settle, throw it out, loud at both ends |
| Sweeper | MID-MID-OUT: hold the arc, power at the end | OUT-OUT-IN: flat out through the long bend, then close the door on the exit before the straight | IN-IN-IN: a long corner is a long time to defend |

District habits, for barks: Touge preserves momentum (mostly MID (HAN), OUT (POW) only on exits). Wangan commits where the road opens and shuts the door before the straights. Street fights for position (IN-heavy (EN), OUT (POW) as a lunge), except at intersections, where it waits out the cross street.

## Signature corners (first pass, draft 2026-11-11)

Austin's framing (locked, canon 30): each district has a handful of signature corners the player learns. On those, everyone in the district (wild racers, crew members and the crew boss) shares the same standard line and the same bluff. On every other corner, wild racers share one line and bluff, and named characters drive their own style (`plot.md` districts, Myth Driver sheets).

The corner choice below is a first pass, pending Barry's check. How it maps to the sim (which alternative counts as the shared bluff, adherence) is `<TBD: Barry>`. Each standard line is the district's main line above; no lines change.

| District | Signature corner | Standard line | Why everyone here drives it this way |
|---|---|---|---|
| Touge | Hairpin | IN-MID-OUT | Brake inside, roll the apex, drive off the turn: momentum down the hill is how the mountain passes |
| Touge | Esses | MID-MID-MID | Flow with no stance changes: nobody on the mountain breaks rhythm and loses momentum |
| Touge | Decreasing radius | MID-IN-MID | The mountain pinches, so protect at the late apex and smooth out |
| Wangan | Sweeper | OUT-OUT-IN | Flat out through the long bend, then close the door before the straight |
| Wangan | Increasing radius | OUT-OUT-IN | The road opens, so go flat out, then shut the door so the car behind can't use your draft |
| Wangan | Constant radius | MID-OUT-OUT | The road stays open, so commit from the apex on |
| Street | 90-degree | MID-MID-OUT | It's an intersection: hold your lane through the cross street, then punch it out |
| Street | Chicane | IN-OUT-OUT | Protect the entry, then muscle through the flick |
| Street | Hairpin | IN-IN-OUT | Hold the inside through the apex so nobody gets a nose in, then go |

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
| Hairpin | IN-MID-OUT | IN-IN-MID: old head. "Don't win it on the hairpin, the downhill does the passing." Stays tucked and lets you run wide | IN-MID-MID: kid flinch. Doesn't trust the rear on the exit and feathers it |
| Constant radius | MID-MID-OUT | MID-IN-MID: mature member closes the door mid-arc, having heard outsiders dive the long ones | MID-MID-MID: old head saves the run for the next corner, momentum over the exit |
| Decreasing radius | MID-IN-MID | MID-OUT-IN: old head who knows exactly where this road pinches attacks the pinch, then shuts the door | MID-IN-IN: kid gets spooked by the tightening and covers on the exit |
| Increasing radius | MID-MID-OUT | MID-IN-MID: mature member sits on you mid-corner instead of opening up | MID-MID-MID: the boss's "fair race" restraint, he doesn't pounce on the exit |
| 90-degree | IN-MID-OUT | IN-IN-MID: old head blocks the corner and rolls out calm | IN-MID-MID: kid lifts out of the 90 after a near miss the week before (bark hook) |
| Chicane | MID-IN-OUT | MID-OUT-MID: Delinquent-type kid tries to bully the middle flick, then has to steady it | MID-IN-MID: mature member keeps it tidy on exit to set up the next bend |
| Esses | MID-MID-MID | MID-IN-IN: old head. Once the flow breaks, he closes the whole second half | MID-MID-IN: boss protects the exit of the esses, protective of his crew's road |
| Sweeper | MID-MID-OUT | MID-IN-MID: mature member covers mid-sweeper when you show a nose | MID-MID-MID: old head never attacks a sweeper exit "since that night" (fog and memory hook) |

### Wangan (promoter boss, polite and cliquey professionals)
| Corner | Main | alt1: who and why | alt2: who and why |
|---|---|---|---|
| Hairpin | IN-MID-OUT | IN-IN-MID: Office Lady-type mature member protects the car and plays the long game | IN-MID-MID: old head lifts on exit. "Nobody pays to see a wreck." |
| Constant radius | MID-OUT-OUT | MID-MID-MID: mature member refuses to commit in front of a reader and holds steady | MID-OUT-MID: old head commits at the apex but saves the exit for the straight |
| Decreasing radius | IN-IN-MID | IN-OUT-IN: promoter "makes it a show" with a surprise apex lunge, then shuts it | IN-IN-IN: mature member, full block, by the book |
| Increasing radius | OUT-OUT-IN | OUT-MID-OUT: old head who raced before everyone learned to block exits goes in hot, settles the apex, then races you out of it the old way | OUT-OUT-OUT: kid forgets to shut the door and just floors it, the honest rookie habit |
| 90-degree | IN-MID-OUT | IN-IN-MID: mature member, tidy, defensive, professional | IN-MID-MID: old head, no heroics on exit |
| Chicane | IN-MID-OUT | IN-IN-MID: mature member keeps the door closed through the flick | IN-MID-MID: kid lifts on the exit, intimidated by the crowd |
| Esses | MID-MID-MID | MID-IN-IN: old head. If the rhythm breaks, he locks down the rest | MID-MID-IN: promoter covers the exit when the betting line favors him |
| Sweeper | OUT-OUT-IN | OUT-MID-OUT: mature member reads your nose mid-sweeper, settles, then attacks the exit to beat you to the straight | OUT-OUT-OUT: promoter plays to the crowd and goes flat out end to end when the money's on him |

### Street (influencer boss, a loud, online, clout-driven crew, old heads who paid for the sweep)
Street is the thinnest district, so its alternatives should be the most legible and personality-driven. A player who has listened to the Street crew should be able to guess who deviates and why.
| Corner | Main | alt1: who and why | alt2: who and why |
|---|---|---|---|
| Hairpin | IN-IN-OUT | IN-OUT-MID: Punk-type kid's dive-bomb for the clip lunges at the apex and can't put the power down | IN-IN-MID: old head who did sixty days doesn't floor it out of anything anymore |
| Constant radius | IN-MID-IN | IN-IN-OUT: mature member blocks the whole arc, then gets greedy at the exit | IN-MID-OUT: kid forgets the plan and floors it on exit ("for the camera") |
| Decreasing radius | IN-IN-MID | IN-OUT-IN: influencer lunges at the pinch for the shot, then shuts the door | IN-IN-IN: Mechanic-type mature member protects the car and the position |
| Increasing radius | MID-MID-OUT | MID-IN-MID: mature member, the group-chat theorist. "Everyone says you counter the opener," so he covers mid-corner | MID-MID-MID: old head lets you go and saves it for the next block |
| 90-degree | MID-MID-OUT | MID-IN-MID: old head. Corners of the block are for blocking, so he sits on the apex and rolls out calm | MID-MID-MID: kid who got pulled over filming this intersection last month stays off the throttle out of the 90 |
| Chicane | IN-OUT-OUT | IN-MID-MID: influencer smooths the flick so the onboard footage stays clean | IN-OUT-MID: old head muscles the middle but stays calm on exit |
| Esses | OUT-MID-OUT | OUT-IN-MID: mature member throws it in, then shuts the second half | OUT-MID-MID: kid throws it in loud, then runs out of nerve |
| Sweeper | IN-IN-IN | IN-OUT-OUT: kid gets bored blocking and floors it, the cocky overcommit | IN-IN-OUT: influencer blocks all the way, then sends it for the finish-line shot |

Street story hook: kids announce their habits on stream ("Watch me send it into turn two"), which makes Street's alts the easiest to learn from barks. The sixty-days old head's hairpin alt2 (never floors exits) is the mechanical echo of his reveal line.
