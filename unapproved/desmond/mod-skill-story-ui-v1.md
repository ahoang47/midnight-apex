# mod_skill: story and UI framing (proposal, unapproved)

Owner: Desmond. Based on touge-race 83b98d8 (design/07 goals block). Answers Barry's four asks from 2026-11-19. Nothing here is canon until Austin approves it; dialogue is placeholder for Nathaniel.

## 1. Stat floors: Rep
- **In-world reason:** crews only race people the scene is talking about. Every race the player runs earns **Rep**, and Rep is the earned-XP ledger shown under a story name. XP lost to a full mod slot still counts because people saw you win, even if the car couldn't hold more.
- **Display:** the crew ladder shows each rung's floor. A locked rung shows the crew member's silhouette with a lock and `Rep 3,110 / 3,165`. In free roam, the member waves the player off: "Nobody's heard of you yet. Come back." (placeholder).
- **Flag:** design/07 says "Reputation is lore only" (`story/barks.md:311` source). This makes Rep visible as a number. It needs Austin's OK and a matching wording change if approved.

## 2. Six required wild encounters per round: gatekeepers
- Each required wild is a **gatekeeper race**: someone in the crew's orbit who tests the player before the next rung and carries one line of gossip or a story clue afterward. They pay off the earlier scenes instead of being filler.
- Flavor per district:
  - **Street:** a livestream callout. A clout-chaser goes live and dares the player on camera.
  - **Wangan:** a booked tryout. The promoter sets up a paid audition run.
  - **Touge:** gossip at the turnout. Someone heard a rumor about the player and wants to see it.
- Each one ends with one flavor-text beat (Nathaniel) that leads into the next rung.

## 3. Non-mandatory XP cap (15 per round): the scene stops watching
- **In-world reason:** after 15 side wins in a district, nobody there cares about you beating randoms anymore. Wins still pay cash, but there's no new Rep. A new district means a new audience, so the cap resets.
- **Signal:** a side-race counter in the HUD or map, `Side-race Rep 12 / 15`. On the 15th win a one-time toast: "The scene's seen enough. Side races pay cash only this round." (placeholder). After the cap, the post-race screen shows `+0 Rep (capped)` next to the cash.

## 4. Street boss at half stat weight: his course, his rules
- **Recommended framing (course):** the influencer picks a tight downtown course built for footage: short straights, blind corners, nowhere for horsepower to show. "Anyone can win with money. Win on my street." It fits canon 22 (builds made for the camera, "My street, my camera") and needs no extra rule on screen.
- **Alternative (rules):** he insists on "content rules" for the stream (limits on how much the build can do) so the win is clean on camera. This is more explicit, but it reads as a rules exception.
- **UI:** the pre-race card for this race says something like "Driver's race: your build matters less here." so the player isn't surprised.

## Open for Austin
1. Is it OK to make Rep visible as a number (it was lore only)?
2. Gatekeeper framing for the required wilds?
3. The scene-stops-watching reason and the counter for the cap?
4. Course framing or rules framing for the Street boss?
