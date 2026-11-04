# Changelog

> Session journal for the whole repo: changes, decisions, reasoning, and reversions. **Read before making changes** to avoid repeating past mistakes. Newest entry at the top.
>
> Entries before 2026-10-31 "Repo restructure" were merged from two older logs and keep their **original wording and paths**. Old → new paths: `velocity-shift/overview/0X-*.md` (also written `overview/0X-*.md` or `Notes/06-pattern-read.md`) → `design/0X-*.md`; `godot_prototype.md` → `design/godot-build-guide.md`; `art_direction.md` → `design/art/art_direction.md`; `Notes/` → `design/notes/`; `story/high_level_story.md` → `story/pitch.md`; `story/plot_points.md` → `story/plot.md`; `story/character_sheets.md` → `story/characters/index.md`; `story/sabine.md`, `story/myth_driver_*.md` → `story/characters/`; `velocity_shift/`, `tests/`, `scripts/*.py`, `config/`, `main.py` of the prototype → `sim/…`.
>
> Same-day ordering between the two old logs is a best guess (neither log recorded times). On 2026-10-31 Arthur wrote the restore and BRZ entries into both logs; both copies are kept.

---

## 2026-11-03 — Barry: aero parts and respec cost in the mods spec (proposal)
- `design/07-economy-and-mods.md` §6.3: aero parts are stat parts with a fixed base boost plus a small free pool of points to put into POW, EN or HAN at the wind tunnel. Tunes lock, with a paid respec. Agreed with Austin and Nathaniel in the Integration room; no new stat layer, per Austin. Added Q18 (respec cost) to the bottom of §11. Follow-up the same day (Austin): aero unlocks when the debt reaches zero, mid Round 2 (first set to after Round 1, then moved by Austin to spread out unlocks; story: Sabine takes the PC out for drinks), parts are bought once and kept, a respec moves a capped number of points per visit at a price per point (same rule for skill points and aero), and betting is confirmed to unlock at the end of Round 2 (corrected from 'after the Wangan boss'), with Round 3 harder to push risky bets. No sims run (the economy/mods sim still waits for success criteria).


## 2026-11-03 — Barry: two-axis play quality (q_read, q_time); target win-rate curves (PROPOSED) as 02 §0
- Austin agreed to a clean-sheet equation redesign: targets first, then the minimal core equations (clash resolution, QTE, AI skill), each constant doing one job. `design/02-equations-reference.md` §0 "Target curves (PROPOSED)" is the draft spec, for Austin to mark up. Placement in 02 is Austin's call; nothing existing in 02 (or any other doc) was deleted, rewritten or renumbered. Cleanup and reconciling 02 §1–8, 03, 04 and 08 with §0 come later.
- Per Austin, added a header "Stale; do not reference unless explicitly asked to" above the old 02 §1–8 (no text deleted), since the clean-sheet redesign will replace them.
- Austin (t29u): play quality is split into two independent skills, and the targets must keep three play styles viable (strong reader / sloppy timing, sloppy reader / sharp timing, balanced). §0 rewritten in place for that; the single-q targets from earlier today (Boss a 22, q0 0.90) are superseded.
- Sim (opt-in, defaults unchanged): `MatchConfig.player_read` (q_read, chance per clash of reading and countering the AI's real pick) and `player_timing` (q_time, chance per turn of a perfect-10 QTE). `player_quality = q` still works as shorthand for both (verified identical results); an unset axis falls back to `player_quality`, then to 0 (random). `SimulationRunner._play_quality` resolves them. `parity_sweep.py` gains a `grid2d` mode (q_read × q_time at stat parity, plus `fit_features`, a general logistic fitter). 25/25 tests and the gauntlet pass.
- Measured (`parity_sweep.py grid2d --seeds 40`, Lieutenant and Boss length, N = 4000 per cell, raw output in `/workspace/parity/grid2d.*`): read and timing are **substitutes**. They add on the log-odds scale (Lt: a_r 4.94, a_t 5.92, interaction +0.21; Boss: a_r 5.38, a_t 6.22, interaction +0.68), and either alone wins today (1.0 / 0 wins 91.1% Lt, 88.1% Boss; 0 / 1.0 wins 97.0% and 95.5%). Timing is worth 1.16–1.20× reading per unit.
- Proposed target form: s = (q_read + q_time) / 2, P = logistic(a(s − s0) − b ln r), equal weights so styles are balanced at equal total skill. Wild a 12, s0 0.58, b 12.59; Lieutenant a 14, s0 0.72, b 14.69; Boss a 16, s0 0.86, b 16.79. Boss at parity: 0.9 / 0.9 wins 65.5%, perfect 90.4%, a 1.0 / 0.6 specialist 27.7% (69.2% at r 0.9). +10% opponent stats ≈ +0.10 of s.
- Acceptance test: 324-cell grid (3 tiers × 6 q_read × 6 q_time × r 0.9/1.0/1.1); max abs error ≤ 6 pts, RMS ≤ 3; perfect play at parity ≥ 85% in every tier; style balance ≤ 5 pts at equal total skill; a_t / a_r within 0.9–1.1; level stability ±0.03; monotonic. Six open questions for Austin in §0.9. Desmond flags in §0.10: the read axis depends on the tells, so the lie rates in `design/06-pattern-read.md` directly cap what q_read is worth.
- Why: the parity sweep (08 §5) shows CLASH_STAKES, BATTLE_BONUS and the rubber band barely move q50, and ENCOUNTER_RATIOS scale both opponent level and AI QTE. Only measured figures from 08 and today's grid2d run are cited; everything else is labeled a target. No economy or mods sims run.


## 2026-11-03 — Nathaniel: Myth Driver #1's sighting beat
- Austin locked it: after Round 1 Touge, #1 spots Sabine's work on the PC's car and makes a snide comment about her bringing the cops. It works as bad data, since the PC reads it as a snitch hint, but it's really his distrust of her detective uncle (canon 2), which pays off in the Finale. Updated `plot.md` §4 and `characters/myth_driver_1.md`, and removed the open question.


## 2026-11-03 — Nathaniel: Myth Driver race-lines question removed
- Austin: beats are enough, and exact dialogue is unimportant for now. Removed the 'Myth Driver race lines' open question; the locked beats stay (canon 17–18: #1 insists she left on her own, #2's guilt hints she was a scapegoat). The dialogue gets written when the Finale is scripted. Renumbered the open questions.


## 2026-11-02 — Nathaniel: add the reverse-speakeasy barkeep; Jesse and Reiko aren't Sabine's employees
- Austin added a new character, the owner and barkeep of a "reverse speakeasy," a bar that hides a secret wind tunnel. Reiko sells her parts there and Jesse tunes cars there. He's friendly with Sabine, doesn't care for the drama, and is just in it for the cars, like Jesse and Reiko. The wind tunnel runs on illegally snaked (stolen) power. Austin first made the bar the crew's hangout, then reversed it: the main hangout stays Sabine's garage, so the prologue garage intro stands. Canon decision 24, new sheet `characters/barkeep.md` (mechanical fields `<TODO: Barry via Desmond>`), and an entry in `characters/index.md`.
- Sabine doesn't employ Jesse or Reiko. She isn't part of the scene, and they just hang out with her. `plot.md` §2 Garage Intro now says so. The bar's name, location and barkeep name are on hold as detail work (`<TODO>`).
- Open questions added at the bottom before Substories: the bar's name and location, and when the PC first visits it (renumbered).
- Not rewritten, flagged for Austin: the garage-intro script (`scripts/prologue.md`, where Jesse slides out from under a car in Sabine's garage and promises to fix the wreck), the rebuild debt (canon 19), Reiko's wholesale scene, "Sabine introduces her crew," and where the Round 2 Jesse beat takes place.

## 2026-11-02 — Nathaniel: climax restructure, the PC races for the truth and the apology party
- Austin locked a new climax. The wrongful accusation at the end of Round 3 stays ("Get out of my garage."). Because the PC knows they messed up, they race all three Myth Drivers in the Finale to find the truth, and the contradictions in their accounts unravel the snitch story. The PC goes to Sabine with "I know what really happened," and she blows up at them for digging into her past. The PC leaves, then convinces all three Myth Drivers to come and apologize too: "one big apology party." The climax is a final race between the PC and Sabine at the Fushigi-Yama summit. How the PC gets her there, and whether the apologies come before, during or after the race, are `<TODO>`. The ending, the parting shot, "And when are you calling them?" and the epilogue are unchanged.
- Changed: canon decisions 4, 5, 15, 16 (plus the cross-references in 17 and 18), the Backstory Timeline (new step 7 "The blowup"; steps renumbered to 10), `plot.md` Mentor Confrontation, the FINALE intro, §7–§10 and the Mentor and Player Arc bullets, `pitch.md` climax, and the Resolution lines in `characters/sabine.md` and `myth_driver_1/2/3.md`. The PC now learns the truth during the Finale races, but Sabine still learns the real reasons only at the summit, from the Myth Drivers. "I was wrong. Be there." is gone from the summit and now appears only in the epilogue, sent to the hometown crew.
- Removed the "Myth Drivers each catch wind and come on their own out of guilt" version. The open question about how word reaches them is answered (the PC convinces them) and is off the list. Added questions for how the PC gets Sabine to the race, the timing of the apologies, and how each Myth Driver's real reason comes out in the races. Substories stays last (renumbered).
- Why: Austin felt the story had drifted from his original spine, the PC reconciling Sabine and her old crew, with Sabine angry he even tried, leading to a final race. A variant with no accusation was considered and dropped. The accusation stays because it's the PC's reason to race for the truth.

## 2026-11-02 — Nathaniel: the PC's missed call and backstory beats
- `story/plot.md` §5 Round 2 Touge: Austin locked it. As the racer says he texted Sabine for weeks and never heard back, the PC's phone buzzes with a hometown number and the PC lets it ring out. Nobody comments.
- Why: Austin pointed out that Sabine's "And when are you calling them?" has no weight if the PC's past only comes out at the end. The PC's story has to build alongside Sabine's ("same same but different energy"). The other beats (the Prologue dodge, the Round 2 "Had one. Left.", the Round 3 slip, the full telling at the summit) are first passes added to the open questions. The PC's apology moved to the bottom of the list because it depends on those beats (renumbered).

## 2026-11-02 — Nathaniel: Sabine's reaction to the accusation
- Austin locked it: Sabine doesn't defend herself. She's been accused of this once already and doesn't want to waste the energy again, so it reads as tired, not proud. After a long silence she says "Get out of my garage." It's in canon decision 15 and timeline step 5, `plot.md` Mentor Confrontation and `pitch.md`. Jesse and Reiko staying quiet in the background is left as a `<PROPOSAL>`. The question is off the list (renumbered).
- Why: it fits someone who never explained herself to the Myth Drivers either, and it keeps the uncle's heart attack hidden until the summit.

## 2026-11-02 — Nathaniel: Round 2 Wangan reveal
- `story/plot.md` §5: Austin rewrote Round 2 Wangan. Most people came to the Wangan runs for Sabine, so when she walked away, the betting went down. The bets recovered because the promoter is an excellent businessman, but it was never quite the same. The light personal losses from the sweep stay. The `<CHECK>` is cleared and the question is off the list (renumbered).
- Why: it makes her cost to the scene concrete and ties it to the promoter's betting world (canon 21) without opening a new thread.

## 2026-11-02 — Nathaniel: how #1 and #3 knew about #2's date
- Austin locked this: Sabine never told anyone. #2 vented to #1 and #3 himself, they teased him for weeks, and he convinced himself the jokes started with her. At the summit he throws it at her ("You told everyone I asked you out."), and #1 or #3 answers, "Man, *you* told us." It's in canon timeline step 1, `plot.md` §9, `characters/myth_driver_2.md` and `characters/sabine.md`. The `<CHECK>` flags are cleared and the question is off the list (renumbered).
- Why: it closes the gap in how they knew without anyone breaking Sabine's privacy. It's the same misread as the rest of the story, since #2 blames her for something he did, and it gives the summit a beat where his grudge falls apart before the old-flame truth lands.

## 2026-11-02 — Nathaniel: two reveal lines cut
- `story/plot.md`: Austin cut "ask her uncle lol" from the Round 2 Street group chat because it was too on the nose, and cut the old head's "couple weeks" line from Round 3 Touge. The missing two weeks now come up only through the Round 2 Touge texts. "Reveal checks" is off the open-questions list. Substories moved to the bottom at Austin's request ("save those for the end") (renumbered).

## 2026-11-02 — Skill parity: play-quality sweep and fitted win-rate equation [sim] (Barry, Chief of Systems)
- Austin approved fitting a skill parity equation, with his feel target as the first success criterion: at stat parity you should only win if you play about 90% right (q50 ≈ 0.9).
- **Engine changes (opt-in; defaults unchanged, all 25 tests pass):**
  - `models.MatchConfig` gains `player_quality` (q in [0, 1]) and `opponent_qte_ratio`.
  - `simulation.SimulationRunner` gains a q-player: it counters the AI's real pick with probability q and hits a perfect QTE with probability q, otherwise it plays like the old random player. To do that it makes the AI's pick first and caches it, which is safe because the AI's pick never depends on the player's card.
  - `equations.py` gains `PLAYER_QTE_MIN`, `PLAYER_QTE_MAX` and `PERFECT_QTE`. The rubber-band 0.15 literal in `match.py` moved to `equations.RUBBER_BAND_FRACTION` with the same value, because all constants belong in `equations.py`. `balance_gauntlet.py` still hard-codes its own 0.15 copy.
- New `sim/scripts/parity_sweep.py` (pure stdlib, multiprocessing) runs the sweeps, the fit and the lever prototypes. New `design/08-skill-parity.md` records the results and proposals; the script is the source of truth.
- **Findings:**
  - At parity, q50 is 0.21–0.27 at every level and encounter length (N=2000 per cell), far below 0.9. The fitted logistic is P = 1/(1+exp(-(a(q-q0) - b ln r))). For Lieutenant: a=10.49, q0=0.214, b=26.18, RMS error 2.0 pts.
  - The best tested route to 0.9 is AI skill: AI QTE at the cap plus a prototype AI read rate of 0.40, which gives q50 0.874–0.916 everywhere. CLASH_STAKES, BATTLE_BONUS and the rubber band barely move q50.
  - Today's double-scaled ratios give Boss a q50 of about 0.82 and make Wild unlosable.
- **No game constant was changed;** the lever results are proposals for Austin. Skill points (now in v1) are expressed as a shift in the stat ratio r.
- Committed on Austin's go-ahead: only the write-up, `design/08-skill-parity.md`. The engine changes and `sim/scripts/parity_sweep.py` stay local for now, so the doc's pointers to them land with a later push.

## 2026-11-02 — Nathaniel: the missing crew reveals filled in
- `story/plot.md` §4–6: Austin approved the full reveal set after a read-through. Round 1 Street has the clip of Sabine leaving right before the sweep and #3 as "the one who went pro." Round 2 Touge has the unanswered texts. Round 2 Street has the group-chat theories and the influencer's interview offer ("Clean people talk"). Round 3 Touge has the old head who saw her on the phone. Round 3 Wangan has the promoter's "She had her reasons. Not my place." Round 3 Street gets the final straw: "I did sixty days. Lost my car. She didn't even get a ticket."
- The sweep's cost builds lightly, through plain facts in Round 1 Wangan, personal losses in Round 2 Wangan and occasional crew flavor text, so "sixty days" lands. Austin picked this over a heavier version that would have given someone in every district a sweep injury, because it's less on the nose.
- Rejected and why: the detective-uncle line in Round 2 Touge was too on the nose. The promoter's betting books were a throwaway that raises a question the story never answers. For Round 3 Street, a farewell party didn't fit canon (#3 never went pro), a deleted video would be hard to animate, and "she always knew when to leave" felt contrived.
- Still flagged `<CHECK>`: "ask her uncle lol," and whether to keep or cut the "couple weeks" echo in Round 3 Touge. Open questions: "Missing story reveals" removed; "Clues" became "Reveal checks"; the Round 2 rewrite check is narrowed to Wangan (renumbered).

## 2026-11-02 — Economy spec: open questions are now a FIFO queue [design] (Barry, Chief of Systems)
- `design/07-economy-and-mods.md` §11 now lists open questions oldest first, with dates, following the queue Nathaniel keeps in `story/canon.md`. Austin asked for the same blind FIFO here: he gets one question at a time from the top, and new questions go to the bottom.
- The encounter-scaling fix (open since 2026-11-01) and the success criteria for the sim are now at the top of the queue. Arthur's body-kit and wing question was added at the bottom.
- Removed as resolved: rep is lore only (Austin via Nathaniel), and mods may show on the car within the car rules (Arthur). The overlap question now starts from canon decision 19 (a share of each win goes to the debt) and lists Desmond's trickle-from-bonuses idea as an alternative. Question references in the spec were renumbered.
- Logged Austin's progression plan in §11: Round 1 uses skill points only, Reiko's mods come from Round 2, and capped betting from Round 3 pays for pricier mods. This brings skill points into v1, so the "deferred" status in `design/05-skill-trees.md` is now out of date. The docs have no skill-to-win-rate equation; the closest thing is the damage ratio S in `sim/scripts/design_opponent.py`.

## 2026-11-02 — Logo: approved one-line wordmark [art] (Arthur, Art Director)
- Austin approved round-3 V3, now in `art/logo/`. It's a black-and-white one-line wordmark: solid MIDNIGHT with the chicane M, flares on the left, a heavily extruded APEX whose A traces an out-in-out racing line (kerb at the apex), and katakana underneath. He rejected round 1 as too soft and rounded, so everything is hard-edged. He picked W2's one-line layout, S1's APEX and H1's flares from round 2, in black and white.

## 2026-11-02 — .gitignore: keep licensed GR Corolla blueprint files local [art] (Arthur, Art Director)
- Ignored the Dimensions.com SVG and the four renders that reproduce it (`art/vehicles/gr_corolla/...`). Their licence is non-commercial with no redistribution, and the repo is public. Desmond asked for this so a `git add -A` can't push them.

## 2026-11-02 — Female character base: chest height raised [art] (Arthur, Art Director)
- Austin pointed out that the female bust sat too low (it showed on the poster draft). It was in the model: the apex was at 1.163 m, about 18 cm under the shoulders. He asked for +5 cm and then another +5 cm, so it's now at **1.256 m** (+9.3 cm), about 4 cm above the Spine2 joint. The fix lives in the build script (`art/characters/base/build/spec.py` `fem_trunk_z()` / `TRUNK_ZF` / `TRUNK_WZ`, plus the weight lookup in `build_char.py`), so rebuilds keep it.
- Only female trunk heights move: the waist ring rises 3.7 cm, the bust ring 9.3 cm and the armpit ring 4.2 cm, so the upper chest isn't pinched. The hem and shoulders stay put. Ring widths and depths and the Slim/Bulky factors stay tied to each ring, so all three builds get the raised chest.
- The apex is now ~79 % Spine2 / 21 % Spine1 (was ~93 % Spine1). The armpit ring is weighted so it picks up only ~3 % UpperArm, and the A-pose and Bulky armpit checks are clean.
- Tris (686 body), vertex count, UVs and textures are unchanged. Compromise: the texture follows the verts, so the tee stretches about 1.45× between the waist and the bust and compresses above it, and the jacket pockets sit about 2–3 cm higher. It's plain fabric with no print, so it isn't visible at game resolution. The male is untouched.
- Rebuilt `char_base.blend` and `assets/characters/base/char_base_f.glb` and re-rendered the female turnarounds, deform check, swap sheet and lineups. Before/after (original vs new): `art/characters/base/renders/chest_fix_before_after.jpg`. Not committed.

## 2026-11-02 — Nathaniel: why the PC left home
- Austin locked the PC's real reason for leaving the hometown crew: they felt weak. The PC believed they were the weak link holding the crew back and left rather than say it. The crew never saw it that way. Recorded in canon decision 13, `plot.md` §1 and §11. "PC backstory" is off the open-questions list (renumbered).
- Why: it's forgivable, so the fun epilogue race still works. It's a misread like the Myth Drivers', and the race shows the crew wanted the PC all along. An earlier tie to the blown engine in the opening was dropped as a stretch.

## 2026-11-02 — World notes: overworld camera reference [art] (Arthur, Art Director)
- Updated `design/art/world_notes.md` with the overworld camera, based on Racing Lagoon free roam at 16:30 (Austin's reference). It's a high overhead perspective view at roughly 50–65°, rotatable, and not a chase cam or true isometric. Also added what that means for art: rooftops and ground carry the look, no one-sided cut-outs, and a lighter overworld car LOD.

## 2026-11-02 — World notes: OSM-based overworld, turn-based pregenerated tracks [art] (Arthur, Art Director)
- Added `design/art/world_notes.md`, which records Austin's direction. The overworld uses OSM road layouts only, with no real buildings, and is stylized and remixed into the fictional city per canon decision 6. Races are turn-based on pregenerated tracks (Racing Lagoon), which means a corner-segment kit per district. The isometric overworld camera is flagged as an open question. These are notes only; nothing is built.

## 2026-11-02 — Nathaniel: PC's hometown crew and the epilogue race
- Austin chose who the PC walked out on: their hometown crew. The PC was its driver and left the week of a big race for a job in the city without telling anyone, so the crew thinks the PC ditched them. The PC's real reason stays `<TBD>`. Recorded in canon decision 13, `plot.md` §1 and Player Arc.
- Austin added an epilogue (new `plot.md` §11, canon timeline step 9, `pitch.md`). After Sabine's parting shot she asks "And when are you calling them?" (the proposal is now locked and off the list). The PC calls the crew with "I was wrong. Be there.", they come to Fushigi-Yama, and after an awkward apology they run a low-stakes race for fun. Barry owns its tuning.
- Why: Austin pointed out that the PC has to make the call, so the crew showing up because of the influencer's clips was dropped. A rescue by luck wouldn't resolve the PC's arc. The fun race gives the game a light ending after the summit.
- Open questions: PC backstory narrowed to the real reason for leaving; "And when are you calling them?" removed (renumbered); "Epilogue details" added at the bottom.

## 2026-11-02 — Nathaniel: Sabine's parting shot locked
- Austin picked Sabine's parting shot to the Myth Drivers: "My uncle's doing fine, by the way. Since none of you ever asked." It's in canon decision 5, `plot.md` §10, `pitch.md` and `characters/sabine.md`, and is off the open-questions list (renumbered).
- Why: it's quiet rather than cruel, and it lands the third reason she won't rejoin (nobody acknowledged her uncle's heart attack, decision 23) without spelling it out.

## 2026-11-02 — Barry: economy spec, promoter's betting side game
- `design/07-economy-and-mods.md` §7.5 (new): a proposal for the high-stakes betting side game the Wangan promoter opens after Round 2 (story: `story/canon.md` decision 21, from Austin via Nathaniel). The PC bets on their own non-boss races, with odds set by the expected win chance minus a house edge so pattern-reading skill beats the line. Stakes are capped, an optional handicap raises the odds, the debt share applies if the debt is somehow still open, and winnings are spent at Reiko's wholesale prices. All values are `TBD`. Added a metric (#13) and an open question (#15). Nothing was run, per Austin's rule.

## 2026-11-02 — Barry: economy spec, repair debt no longer takes all winnings
- `design/07-economy-and-mods.md` §7: Austin ruled that not all winnings go to the repair debt. The strict rule (A) is ruled out, and the allowance rule (B) is now the baseline, with a share `DEBT_SHARE` (TBD, under 1.0) going to the debt from the Prologue on, so the PC can buy some parts before the debt clears and feels Reiko's discount right away. This overrides the "all winnings" wording in `story/canon.md:40`; Nathaniel owns the story text.
- Wholesale timing confirmed by Austin: Reiko's discount unlocks after Round 1, matching the spec and `story/plot.md:98`.

## 2026-11-02 — GR Corolla: lean car (clay + detail pass), game .glb + Godot scene [art] (Arthur, Art Director)

Austin signed off the clay shape ("Honestly great. Let's just go for a detail pass."). The detail pass follows the WRX STI / S2000 / BRZ lean builds. Pushed to proto-build on Austin's go-ahead. No other car, `lean_common` or `tokyo_v2` file changed.

**New:**
- `assets/cars/gr_corolla/`:
  - `car_gr_corolla.glb` (textures embedded; Godot import hints give the VehicleBody3D `GRC` and VehicleWheel3D `Hub_XX`).
  - `car_gr_corolla.tscn`: an inherited scene with mass, COM, wheel/travel/steer/AWD values, a body collision box, `susp_follow.gd` on `Susp_XX` and the glow FX hidden. This is new compared with the other cars, which ship the .glb only.
  - `susp_follow.gd` + `.uid` (same script as the other cars, own uid) and a README with the rig table.
- `art/vehicles/gr_corolla/`: sources and scripts. Blueprint: the Dimensions.com vector SVG (`bp/gr_dimensions.svg`). Clay output is in `out/` and `renders/`; detail output is in `detail/` (blend, glb, textures, gates, renders). Also `make_all.sh`, `threeview/`, `lineup/` and `godot/make_tscn.py`.
- `art/mood/tokyo_gr/`: night vibe check of the GR on the Tokyo v2 street (non-binding). It reuses `tokyo_v2/scene_v2.py` unchanged, the same way `scene_duo.py` does.

**Numbers:**
- **1,888 tris** total (cap 2,000; clay was 1,922).
- IoU: side .978, top .991, front .978, rear .978 (pass).
- 9-pose clearance: all clear, tightest 7.6 mm.
- Textures: body 1024², parts atlas 256², glow 128×64, env 256×128. All RGB555 + Bayer.

**Detail pass:**
- **Clay review fixes:**
  - Nose shading: custom split normals taken from the uncut loft.
  - Grille and diffuser:
    - Douglas–Peucker corner outlines with planar floors.
    - The diffuser is now one centre + exhaust opening.
    - The corner vents are painted.
  - Wing tip filled (28 tris).
  - Mirrors are tapered 3-ring shells.
- **Livery:**
  - White body; gloss-black roof, pillars, wing and mirrors.
  - Matte-black lower aero.
  - Red diffuser accent.
- **Painted detail:**
  - Panel lines drawn from the SVG vectors.
  - Hex grille and intake mesh; vent slats; diffuser fins.
  - Tail lamps.
  - Flat made-up plates.
- **Badges:**
  - A made-up apex-chevron emblem.
  - An illegible red badge.
  - The real maker emblem paths in the SVG are dropped and never painted.
- **Lamps:**
  - The headlamp lens art comes from the parts atlas on the 30 mm molding pocket.
  - Head + tail glow sprites (`GRC_FX_LampGlow`, hidden by default).
- **Wheels:** 15-spoke gunmetal wheels; the made-up tyre lettering reads correctly on both sides.

**Checked in Godot 4.6.3** (Compatibility fallback, scratch copy of the repo):
- The .glb imports and the scene loads.
- The car settles at the design ride height, drives and steers.
- The struts follow the wheels.
- Sheet: `art/vehicles/gr_corolla/detail/renders/gr_corolla_detail_godot46_800.jpg`.

**Reasoning:**
- The livery is white with a black roof, so the GR stands apart from the blue/red/blue lineup.
- Cutting the angular rear corner vents and the jagged grille outline caused the saw-tooth clay read, so that detail is carried in the texture instead.

**Known gaps:**
- Tail lamps are painted on the body texture. They light up only through the glow sprites, as on the WRX.
- The body material's env term also shows on the dark grille floor: a neon band in the Tokyo shot.
- The mirrors still read a little boxy.
- Headless Godot import of the repo needs the Blender importer disabled or a Blender path set, because of the `.blend` sources. This is not new and not specific to this car.
- Corrected a claim from the clay README: the flat 20/30 mm clearance entries are the liner inner-wall offsets, not a probe radius.

---

## 2026-11-02 — Economy and mod parts: draft sim spec [design] (Barry, Chief of Systems)

Draft only, waiting on Austin's success criteria and approval. Nothing was run or simulated. No code, constants or story files changed. Not committed or pushed.

**New:**
- `design/07-economy-and-mods.md`: the spec for the headless sim's economy and mod parts. It covers the money and repair-debt ledger, Reiko's wholesale discount, race payouts by encounter type and round, a shop and part catalog that plugs into the existing POW/EN/HAN, clash and QTE terms (additive only, never HP), slots and level floors, opponent parts, and a season runner (Prologue → Rounds 1–3, Touge → Wangan → Street). It also lists candidate metrics and open questions. Every value not already in the repo is a named `TBD` constant.

**Reasoning:**
- Austin asked for the economy to be architected from the existing docs before anything runs. Desmond's repair-debt questions (amount, which race clears it, wholesale size and the overlap) depend on it.
- It collects what the story and design docs already say (with file:line citations) and lists 12 conflicts between them. The main ones: whether rep is tracked, doc vs code encounter ratios, slot counts, and the retry fee.
- Key finding: opponents scale off the player's level (`cli.py:305`), so in the current model only parts change the player's strength relative to opponents. The pending encounter-scaling fix has to come before any debt or payout number.

---

## 2026-11-02 — Story: the family emergency was the uncle's heart attack [story] (Nathaniel, Narrative Lead)

Lead approved. Not committed or pushed.

**Changed:**
- `story/canon.md` timeline step 2 and decision 23, `story/characters/sabine.md`: the call the night of the sweep was her uncle-dad having a heart attack. He survived; she spent about two weeks with him through surgery and recovery, out of contact, which is when the Myth Drivers decided she'd run. FIFO item removed and the rest renumbered.

**Reasoning:**
- The lead wanted it serious enough to keep her out of contact for a week or two, but not a tragedy. It also stings because the man she was caring for is the uncle #1 distrusted.

---

## 2026-11-02 — Story: city-wide sweep; Sabine left for a family emergency [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` timeline step 2, decision 5 and new decision 23, plus `story/plot.md` Round 1 Wangan: the sweep was a large, coordinated crackdown across all three districts in one night (benign, routine enforcement). Sabine left minutes before because her uncle called about an unrelated family emergency, and she was the only one of the old generation who walked away clean. Nobody ever acknowledged what she went through, which becomes a third reason she won't rejoin.
- FIFO item "Police sweep details" narrowed to what the family emergency was.

**Reasoning:**
- The lead wanted the sweep bigger, touching every district. The unrelated call keeps it benign while giving the Myth Drivers (and later the PC) a damning-looking coincidence, and it gives Sabine's refusal an emotional core.

---

## 2026-11-02 — Story: rival chain dropped [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/plot.md` Rounds intro: removed the per-district rival chain (and changed "reputation gating" to "street cred gating" to match decision 12).
- `story/pitch.md`: removed "recurring rivals" and "district rival encounters"; "rival encounters" and "rival progression" became crew rematches and crew progression.
- `story/canon.md`: "Rivals" removed from the FIFO stack and the rest renumbered. Myth Driver #2's "Resentful rival" role label is unchanged (it describes his relationship, not a rival chain).

**Reasoning:**
- The crews (run from their kids up to their boss each round) already carry the progression, so a separate rival chain was redundant.

---

## 2026-11-02 — Story: Street crew boss is a cocksure influencer [story] (Nathaniel, Narrative Lead)

Lead approved. Not committed or pushed.

**Changed:**
- `story/canon.md` new decision 22 and `story/plot.md` Street district: the Street crew boss is a young-ish, cocksure influencer who built his following after the old generation broke up and isn't really about the old scene. First pass: he idolized #3 and felt abandoned when #3 left to "go pro".

**Reasoning:**
- It fits Street's "cultural fracture" role and, as the lead put it, reflects how a lot of car enthusiasts are now, which contrasts with the old generation.

---

## 2026-11-02 — Story: the promoter is Sabine's old flame [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` decision 21, `story/plot.md` Wangan district, `story/characters/sabine.md`, `story/characters/myth_driver_2.md`: the Wangan crew boss (the smooth, flashy promoter) was privately involved with Sabine back in the old generation's day. That's the real reason she turned down #2's date. It stays private, only hinted at, until the summit, when #2 learns why she said no.

**Reasoning:**
- It sells #2's date rejection, and it hits hard because #2 is the Wangan Myth Driver: he and the promoter share the same highway.

---

## 2026-11-02 — Story: Wangan crew boss is a promoter; betting side game after Round 2 [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` new decision 21 and `story/plot.md` Wangan district: the Wangan crew boss is a promoter who organizes the runs, takes bets and gets a cut. He's pragmatic about Sabine (her walking away was bad for business). After Round 2 he unlocks a high-stakes betting side game for extra money; mechanics handed to Barry.

**Reasoning:**
- It fits Wangan's "pragmatic interpretation" role, sets up the Round 2 Wangan reveal about what her leaving cost the scene, and gives the lead's betting side game an in-world owner.

---

## 2026-11-02 — Story: Sabine never vanished; Touge boss respects her [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` (decision 2, the PC's hook, timeline step 3, new decision 20), `story/pitch.md`, `story/characters/sabine.md`, `story/plot.md` (Round 1–2 reveals, Mentor Arc, Player Arc): Sabine didn't vanish. She walked away from the old generation without a word and still drives and runs her garage, but keeps clear of every crew. New decision 20: most of the scene respects her and is puzzled, not bitter; suspicion comes from a few voices.
- `story/plot.md` Round 1 Touge: the crew boss line (first pass) is now respectful and puzzled; the "something to hide" line moves to a crew kid, and the boss shuts it down.

**Reasoning:**
- The lead felt it was unrealistic for every character to be bitter toward Sabine. Planting the clue through gossip keeps the bad data without making everyone hostile.

---

## 2026-11-02 — Story: only a share of winnings goes to the debt [story] (Nathaniel, Narrative Lead)

Lead corrected. Not committed or pushed.

**Changed:**
- `story/canon.md` decision 19 and `story/plot.md` §3 and §5 intro: a share of each win goes to the debt until it clears in Round 2, not all winnings. The PC keeps the rest, which they spend on parts once Reiko's wholesale opens after Round 1 (confirmed). The share size is Barry's TBD.

**Reasoning:**
- The lead pointed out that "all winnings to the debt" doesn't fit wholesale unlocking while the debt is still open.

---

## 2026-11-02 — Story: each round runs the whole crew, kids to old heads to boss [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` decision 11 and timeline step 5, `story/plot.md` (Districts, Rounds intro, the six Round 2–3 slots), `story/pitch.md`: still one crew and one crew boss per district. Each round the player runs through the whole crew in rank order (its kids who inherited the myth, then its more mature members who know not everything is what it seems, then its old heads, then the boss). The next round, the boss has leveled up the whole crew. Flavor text after every race reveals a little more.
- FIFO stack: "Crew escalation" dropped (answered by this); "Crews and crew bosses" now also covers each crew's kids, mature members and old heads.

**Reasoning:**
- The lead wanted the crews' ranks to mirror the contradicting clues (myth, then doubt, then people who were there). He pointed out that the boss wouldn't race the PC right after they'd only beaten the kids, so every round goes through the full crew. Alternatives considered and dropped in the same session: a new crew each round, a stand-in "boss", and spreading the ranks across rounds.

---

## 2026-11-02 — Story: debt scene drafted [story] (Nathaniel, Narrative Lead)

Lead approved ("Keep it for now"). Not committed or pushed.

**Changed:**
- `story/scripts/prologue.md` §3: first-pass debt scene. Sabine fronted the rebuild, and the PC races under her garage with winnings going there first until they're even. Jesse and Reiko each give their own "translation". The invoice amount stays `<TBD: Barry>`.
- `story/canon.md`: the debt-scene question removed from the FIFO stack and the rest renumbered.

**Reasoning:**
- It closes the prologue, matches canon decision 19, and keeps Jesse warm and Reiko guarded.

---

## 2026-11-02 — Story: no mod money until the debt clears; Reiko gives wholesale after Round 1 [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md` decision 19: winnings all go to the debt until it's cleared in Round 2, so the PC can't really afford mods before then. After Round 1 Reiko warms up and gives the PC wholesale prices (revised from "after Round 2" so the PC has plenty of access to parts by Round 3); the debt still clears in Round 2. The discount size joins the debt amount as Barry's TBD.
- `story/plot.md` §2 (Reiko), §4 and §5 intros: updated to match, with a `<TODO: scene>` for Reiko's wholesale moment at the end of Round 1.

**Reasoning:**
- It ties Reiko's warming-up arc to the economy and pays off her garage-intro line, "Wholesale is for crew. You're not crew."

---

## 2026-11-02 — Story: debt terms set, paid off in Round 2 [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/canon.md`: new decision 19. Sabine fronted the rebuild; the PC drives for her garage until it's even (winnings to the garage first, wins rebuild her garage's standing). The debt is settled during Round 2, and the PC stays afterward for the fun and the mystery. The amount is a systems number handed to Barry via Desmond. FIFO item #1 narrowed to the debt scene script.
- `story/plot.md` §3 and §5 intro, `story/scripts/prologue.md` §3: updated to match.

**Reasoning:**
- The lead put the amount in Barry's court and wanted the debt to end mid-game so the PC's reason to stay shifts from obligation to fun and curiosity.

---

## 2026-11-02 — Story: garage intro script drafted; Jesse warm, Reiko guarded [story] (Nathaniel, Narrative Lead)

Lead approved the direction ("I dig it"). Not committed or pushed.

**Changed:**
- `story/scripts/prologue.md` §2: garage intro completed. Reiko is cool toward the PC ("Wholesale is for crew. You're not crew." / "We'll see."); Jesse is warm and welcoming and jokes that Reiko took a year to learn his name. Ends on Sabine's "Which brings us to the bill." to hand off to §3 The Debt.
- `story/plot.md` §2: one-line personalities added for Jesse and Reiko.
- `story/canon.md`: the garage-intro question removed from the FIFO stack and the rest renumbered (debt terms are now #1).

**Reasoning:**
- The lead wanted Jesse a little warmer and Reiko someone who has to warm up to the PC, which gives her a small arc across the rounds.

---

## 2026-11-02 — Story: the Tuner is Jesse, the Buyer is Reiko [story] (Nathaniel, Narrative Lead)

Lead decided. Not committed or pushed.

**Changed:**
- `story/plot.md` §2 and `story/scripts/prologue.md` §2: the Tuner's and Buyer's `<TODO: name>` placeholders replaced with "Jesse" and "Reiko".
- `story/canon.md`: "Tuner's name" and "Buyer's name" removed from the top of the FIFO open-questions stack; the remaining items were renumbered (the rest of the garage intro script is now #1).

**Reasoning:**
- The lead picked "Jesse" as a nod to *The Fast and the Furious* and "Reiko" as a nod to *Tokyo Drift*.

---

## 2026-11-02 — Story: open questions cleaned into one FIFO stack [story] (Nathaniel, Narrative Lead)

Lead asked. Not committed or pushed.

**Changed:**
- `story/canon.md` — "Open Questions" replaced by a numbered "Open Questions (FIFO — oldest first)" list: 26 one-line items, each with the date it first appeared (from git history and this log; ties broken by outline order) and where it lives. Pull from the top; new questions go to the bottom. Every open `<TODO>`/`<TBD>`/`<CHECK>`/`<PROPOSAL>` in `story/` maps to an item. The old bundled bullets were split (crews/escalation/reveals, Tuner/Buyer, the rift).
- Decision 18 wording fixed for the locked race order: #1 (first race) says Sabine "left"; the contradiction surfaces at #2's race, when his hints say "pushed". Updated in canon decision 18, `plot.md` §7 (#1 and #2) and `characters/myth_driver_1.md` / `myth_driver_2.md`.

**Dropped as stale:** the decision-18 "first contradiction" snag (fixed above). No other live markers referred to tricks at the summit, a public rumor, jealousy, nine bosses, the daylight commute or Act 2 Myth Driver races; those were already closed in earlier passes.

**Reasoning:**
- The lead wants one ordered stack to work through, oldest first, without stale questions.

---

## 2026-11-02 — Story: Myth Driver first sightings in Round 1 [story] (Nathaniel, Narrative Lead)

Lead approved. Not committed or pushed.

**Changed:**
- `story/canon.md` — decision 11: each Myth Driver makes a first sighting right after his district's Round 1 crew is cleared (#1 Touge, #2 Wangan, #3 Street). The races stay in the Finale. A sighting never reveals the private accusation and doesn't mention the other Myth Drivers. Timeline step 5 updated.
- `story/plot.md` — a "Myth Driver sighting" bullet in Round 1 Touge, Wangan and Street (`<TODO: sighting beat>`); §7 notes the races follow those sightings.
- `story/characters/myth_driver_1/2/3.md` — "First sighting" line added.

**Reasoning:**
- The lead expected this from the outline. The original `plot_points.md` had a "Myth Driver encounter" in each district's Act 2 section, right after the district boss. It moved wholesale into the Finale when the rounds structure replaced it, so no early appearance was left. Sightings put each legend on screen early without spending the race or the reveal.
- Follow-up (lead): at each sighting the Myth Driver talks with the PC (no race yet), building the mythos around the fallout and driving the PC to dig further, without revealing the accusation. The Finale race order is locked as Touge (#1) → Wangan (#2) → Street (#3), following the sightings, which closes the order TODO in `plot.md` §7. Updated canon decision 11, the `plot.md` sighting bullets and §7, and each `myth_driver_N.md`.

---

## 2026-11-02 — Story: private snitch accusation, PC's betrayal hook, why Sabine takes the PC in [story] (Nathaniel, Narrative Lead)

Lead approved. Committed on the lead's go-ahead (push pending).

**Changed:**
- `story/canon.md`:
  - Decision 2: the accusation never spread. Only the Myth Drivers and Sabine know; they froze her out quietly, and the scene only knows she vanished around the sweep.
  - Decision 3: she believes she was frozen out over the accusation and never told anyone.
  - Decision 4: Myth Driver races happen "during the Finale" (was stale "Act 2").
  - Decision 13: the PC's old crew/family believe the PC betrayed them, plus the Round 1 hook.
  - New decision 14: why Sabine takes the PC in (needs a driver; sees herself in them, never admits it).
  - Timeline steps 1–5 rewritten so nothing is public.
  - New open question: how/when the PC first learns there was an accusation `<TBD>`.
- `story/plot.md`:
  - §1–2: Sabine's reasons for taking the PC in.
  - Round 1 Touge: the first-pass crew boss line ("Sabine? She was one of us…") and the PC's hook.
  - Every beat implying the scene knows a snitch rumor rewritten as disappearance, speculation and misremembering (Round 1 Touge, Round 2 all three, Round 3 Street, Mentor Confrontation, Summit Setup wording, Mentor Arc, Player Arc).
- `story/pitch.md` — Core Story Mystery: the accusation stays private; the scene only knows she vanished.
- `story/characters/sabine.md`, `myth_driver_1.md`, `myth_driver_2.md` — "snitch rumor" → private accusation; the date stays private (no low-level racer spreading it); Sabine's reason for taking the PC in.
- New `<CHECK: rewritten for private-rumor canon — Austin to confirm>` markers wherever the original intent was unclear.

- Follow-up (lead): the PC puts the accusation together from clues in the crew reveals; nobody tells them. New canon decision 15; the open question is closed and replaced by a "clue per reveal" item. The PC names it at the Mentor Confrontation and Sabine confirms she was accused and not the informant. The dependent `<CHECK>`s (timeline step 5, `plot.md` Mentor Confrontation, `pitch.md` Core Story Mystery) are cleared. Each round's intro in `plot.md` gets a `<TODO: clue per reveal>` with an example. Myth Driver #2's scapegoat `<CHECK>` stays, noting the PC already knows by then.

- Follow-up (lead): the Mentor Confrontation is locked at the end of Round 3 (`<PROPOSAL>` removed in `plot.md` and `pitch.md`). The PC pieces together misleading clues and accuses Sabine of being the snitch (her reaction `<TODO>`), which blows up their relationship. The PC races the Myth Drivers while estranged. At the summit the benign sweep comes out, and the PC owns repeating the Myth Drivers' mistake. Sabine's choice of the PC's crew now follows the PC's apology. The PC's motive after the rift is locked as canon decision 16: doubt (the Myth Drivers' contradicting accounts) drives the racing, and guilt (it echoes home) makes it personal. The motive TODO is closed in `plot.md` §7–8, the Player Arc and `pitch.md`. Also locked: the PC tricks only the Myth Drivers into the summit and is honest with Sabine ("I was wrong. Be there.", first-pass), the first time the PC breaks their pattern of leaving without explanation. Updated in canon decision 4, timeline step 7 and the open questions, `plot.md` §8 and the Player Arc (first step toward the apology), and `pitch.md`. Then superseded by the lead: there is **no trick**. The PC honestly invites Sabine to the summit to apologize, and the three Myth Drivers each hear about it separately, feel guilty, and come on their own, perhaps to apologize too (`<TODO: how word reaches the Myth Drivers>`). The trick TODO and the cut-off "They each individually agree" TODO are closed. Updated in canon decision 4, timeline step 7, the open questions, `plot.md` §8–9 and `pitch.md`. Also locked: Myth Driver #2 hints at Sabine's innocence (possible scapegoat) in his Finale race out of guilt over her ousting. It's one of the first cracks in the PC's certainty and foreshadows his summit apology. New canon decision 17; the #2 `<CHECK>` in `plot.md` §7 is cleared; `myth_driver_2.md` is updated. Then Myth Driver #3's motive was replaced (lead): not jealousy. He wanted out to go pro and didn't want Sabine hurt by him leaving, so he was glad she was gone; letting her be pushed out was easier on him and harder on her. He never actually went pro (why: `<TBD>`). It's also a real reason she declines to rejoin, and he mirrors the PC (leaving without facing the goodbye). His `<CHECK>` is cleared: in his Finale race he half-owns it, and the full reason comes at the summit. Updated: canon decisions 2, 5 and 9, timeline steps 1 and 8, the open questions; `plot.md` §7, §9, §10 and the Player Arc; `pitch.md`; `myth_driver_3.md` (role and story), `sabine.md`, `characters/index.md` (role). Final pass: Myth Driver #1's contradiction (first pass) is that he insists Sabine *left* on her own the night of the sweep, while #2's hints say she was *pushed*. It's the first time two accounts can't both be true, and it starts the PC's doubt. New canon decision 18; the `<TODO: what it is>` in `plot.md` §7 is resolved; `myth_driver_1.md` and the open questions are updated. Also made explicit in canon (decision 2, timeline step 1) and `myth_driver_1.md` that all three Myth Drivers knew about Sabine's uncle-dad; only #1 held it against her. Updated: canon decisions 5, 13 and 15, timeline steps 5–8 and the open questions; `plot.md` Rounds intro and clue lines, Mentor Confrontation, §7–10, Mentor and Player Arcs; `pitch.md` Core Story Mystery.

**Reasoning:**
- The lead wants the accusation hidden, which adds mystery and keeps Sabine's story in shadow. It also means the PC hears only "she vanished, she must have had something to hide", the same thing their own people say about them.

---

## 2026-11-01 — Character bases (male/female): Mixamo-named rig, painted outfit atlases, Slim/Bulky [art] (Arthur, Art Director)

The lead approved the character base pass. One male and one female base body is now the shared start point for every human character. Work toward individual characters comes next.

**New:**
- `assets/characters/base/` — game-ready files:
  - `char_base_m.glb` and `char_base_f.glb` (textures embedded), `textures/{m,f}/*.png`, and `humanoid_bonemap.tres`.
  - A README covering the Godot import: BoneMap → SkeletonProfileHumanoid, nearest filtering, outfit texture swap, Slim/Bulky blend shapes, hiding/showing the hood or collar add-on, and tri counts.
- `art/characters/base/` — source:
  - `char_base.blend` and the build scripts (`build/`: `spec.py`, `paint_textures.py`, `build_char.py`, `render_checks.py`, `compose.py`, and headless Godot checks in `build/godot/`).
  - Review renders: turnarounds for male/female × standard/slim/bulky, swap sheets, `builds_lineup`, `lineup_mf`, `tuneup_before_after`, `deform_check`.
  - Paint templates `renders/uv_template_{m,f}.png`, `godot_import_log.txt`, a README and `CREDITS.md`.
- **Skeleton:**
  - 25 bones with Mixamo names (`mixamorig:Hips` …), identical names and hierarchy for both sexes.
  - Clean deform rig with no IK or poles, T-pose, root at the feet.
  - Male 1.83 m, female 1.70 m. Godot 4.6.3 BoneMap check: all 17 required bones mapped (unmapped bones are optional: root, eyes, jaw, fingers). Retargeted import gives `GeneralSkeleton`.
- **Mesh:**
  - One skinned body mesh per sex (686 tris). Clothes are painted onto a 256² outfit atlas; changing outfit means swapping the texture.
  - Separate pieces: the Head (124 tris, 128² face), two hair pieces per sex, and a tiny outfit add-on (male hood 40 tris, female jacket collar 20 tris).
  - Complete characters: male 880 (tee) / 920 (hoodie); female 900–974. Budget ≤ 1,200.
- **Outfits:** tee + jeans + sneakers for both sexes, plus a teal hoodie (male) and a mustard zip jacket (female). Hair: male crop and quiff; female bob, and a side-swept fringe with a high ponytail.
- **Body builds:** `Slim` / `Bulky` shape keys on every mesh with one skeleton. Bulky widens the torso, belly and chest, thickens the limbs and neck, and shifts the limbs outward.

**Reasoning:**
- Mixamo names plus the humanoid BoneMap let any Mixamo or humanoid animation library retarget onto both sexes. A single shared rig keeps animation sets shared too.
- The lead asked for clothes painted on, the classic PS1 way, instead of layered meshes. That gives one mesh, no poke-through, cheaper characters, and outfits that cost only a texture. Small silhouette steps (tee hem, sleeve hem, jeans hem, sneaker shape) keep the clothed read.
- The CC0 source character had an Akira/Kaneda-like outfit and face. The bases were rebuilt from scratch and the look fully replaced, to keep to the no-real-IP rule. The original download is not in the repo (see `CREDITS.md`).
- Tune-up pass after review: heads +12% with a shorter neck (≈6.6 heads tall), arms about 8.5% shorter, the female ponytail reads from the front, and Bulky/Slim pushed further so the three builds read distinctly.

**Known gaps:**
- No finger bones (mitten hands with a thumb).
- Bone rolls are untested against a real Mixamo FBX.
- Godot's Auto-Map wasn't run headless; the BoneMap was built from an explicit name table.
- Shape keys don't move joints.
- Every outfit shares the tee/jeans silhouette; skirts and shorts need an add-on or a body variant.
- The hood/collar add-on and Hair_B are visible on import and must be toggled in-game.
- Ears are flat quads.
## 2026-11-01 — Story: lean `plot.md` beat outline, `scripts/prologue.md`, PC "running from something" framing [story] (Nathaniel, Narrative Lead)

Lead approved. Not committed or pushed.

**Changed:**
- `story/plot.md` — rewritten as a lean beat outline (356 → 194 lines). Same sections (Prologue §1–3, Districts reference, Rounds 1–3 with Touge/Wangan/Street, Mentor Confrontation `<PROPOSAL>`, Finale §7–10, Substories, Structural Themes) and every `<TODO>`/`<TBD>`/`<PROPOSAL>`/`<CHECK>` marker and locked decision kept. The line-by-line script, popups and stage directions moved out. PC framing added to §1 beats, the summit (`<PROPOSAL>` line) and the Player Arc.
- `story/canon.md` — decision 13 (first pass): the PC is mid-20s, moved for work but is running from something (walked out on their own crew/family without explaining); mirrors Sabine; helping her reconcile is guilt by proxy; the summit callback is a `<PROPOSAL>`. Open questions: PC backstory added.

**New:**
- `story/scripts/prologue.md` — the full §1 opening and §2 garage-intro scripts moved from `plot.md`, unchanged except for the lead-approved PC lines: arrival ("...Well. It's got a garage." / "Nobody here knows me. That's the point."), accepting the race ("...Why not. Not like anyone's waiting up."), the blowout ("...Figures."), "Around. I just moved here." with Sabine's "...Sure.", "...Yeah. Thanks." and the closing "...Fair." A §3 placeholder holds the debt-script TODO.

**Reasoning:**
- The lead wanted `plot.md` to stay outline-focused; scripts now live in `story/scripts/` so no dialogue is lost.
- Follow-up (lead): the overworld tutorial now runs on the drive home from work at dusk, flowing into the back-road headlight challenge. The drive-to-work segment and its arrival popup are cut from `scripts/prologue.md`; the commute TODO is closed in `plot.md`, the script and `canon.md` (decision 11's Prologue line; open question removed). The quieter PC lines set up the new framing: a PC hiding their own walk-out makes Sabine's story personal to them.

---

## 2026-11-01 — Story: one crew per district (rematches), "street cred", round themes locked [story] (Nathaniel, Narrative Lead)

Decided by the lead. Not committed or pushed.

**Changed:**
- `story/plot.md` — Districts reference: one crew `<TBD>` and one crew boss `<TBD>` per district (three of each in total); the old boss voices ("ideological dominance", "pragmatic interpretation", "cultural fracture") now belong to each district's crew boss, so their TODOs are closed. Round sections: "Match 1" in Round 1, "Rematch 2/3" with an escalation `<TODO>` in Rounds 2–3. Round themes (Incident / Consequences / Distortion) are no longer a proposal. Street cred now explains why a crew won't grant a rematch until the player has proven themselves in the other districts. The Mentor Confrontation stays a `<PROPOSAL>`.
- `story/canon.md` — decision 11: one crew and crew boss per district, re-faced and stronger each round; round themes added. Decision 12: "street creed" → "street cred", rematch wording. Timeline step 5 and the open questions updated (the crew-count / nine-boss TBD is gone; crew escalation added).
- `story/pitch.md` — Progression Structure and the district list describe one recurring crew per district; "street creed" → "street cred".
- `story/barks.md` — boss purpose "Define district climax" → each round's climax with a returning crew boss.
- `CHANGELOG.md` — "creed" → "cred" in my earlier entry today.

**Reasoning:**
- Re-facing one crew that keeps improving gives each district a single rivalry to build across the rounds, and it cuts the cast from nine crew bosses to three.

---

## 2026-11-01 — Story: Prologue / Rounds 1–3 / Finale act structure; street cred gating [story] (Nathaniel, Narrative Lead)

Act structure and cred rule locked by the lead. Not committed or pushed.

**Changed:**
- `story/plot.md` — restructured into Prologue (§1–3, the old Act 1, unchanged), a Districts reference section (identity, racer type/archetype tables, stakes), Rounds 1–3 (§4–6; each with Touge → Wangan → Street, every district with Crew `<TBD>`, Crew Boss `<TBD>`, Story Reveal), Finale (§7 Myth Drivers, §8 Summit Setup, §9 The Summit, §10 Ending) and a Substories placeholder.
  - Street cred explains the rotation as in-world flavor only (not a tracked stat).
  - The old per-district mystery themes and key beats are redistributed as round-by-round reveals, marked `<PROPOSAL>` (Round 1 = the incident, Round 2 = consequences, Round 3 = distortion); empty slots are `<TODO: reveal>`.
  - The old Mentor Confrontation sits at the end of Round 3 as a `<PROPOSAL>`.
  - Myth Driver #2/#3 beats moved to the Finale, marked `<CHECK: conflicts with canon>`.
  - The old district-boss voices are kept in the Districts reference with a TODO for which crew boss carries them.
- `story/canon.md` — decisions 11 (act structure; main plot grounded, weirdness in substories) and 12 (street cred gates the rotation); stakes line says crew boss; timeline rewritten for rounds and the Finale; open questions updated (crew count `<TBD>`/nine crew bosses, substories).
- `story/pitch.md` — the empty Progression Structure section now states the act structure; "district boss" → crew boss (district list, Boss Structure, Myth Drivers, mystery sources); the mentor confrontation now follows the three rounds and is marked `<PROPOSAL>`.

**Reasoning:**
- The lead replaced one boss + Myth Driver per district with three rounds of crews and a Myth Driver finale. Moving district identity into one reference section keeps the rounds from repeating it, and the same Crew / Crew Boss / Story Reveal layout in every slot shows exactly which reveals are still missing.

---

## 2026-11-01 — Story: `plot.md` outline cleanup [story] (Nathaniel, Narrative Lead)

Tidy only — no new plot points. Lead asked for a clean outline. Not committed or pushed.

**Changed:**
- `story/plot.md` — restructured into Act 1 (§1 Opening, §2 Garage Intro, §3 The Debt), Act 2 (shared district structure, then §4 Touge, §5 Wangan, §6 Street, each with the same sub-headings: Racer Types, Mystery Theme, Key Beats, Boss, Myth Driver), Act 3 (§7 Mentor Confrontation, §8 Summit Setup) and Act 4 (§9 The Summit, §10 Ending).
  - Racer Types are now tables with each type's archetype, matching `canon.md`.
  - Boss stakes and the retry rule from `canon.md` added to the shared structure; each Myth Driver section lists his hidden motive from canon.
  - The "Mystery Progression Model" theme section was folded into each district's Mystery Theme; the duplicate is gone.
  - Grammar, punctuation and markdown fixed in the existing voice; "mentor" → Sabine where it means her.
  - Every open item is an explicit `<TODO>`/`<TBD>`: names, crews/rivals, boss philosophies, Myth Driver contradiction, sweep details, how the PC tricks everyone, the cut-off "They each individually agree" line, garage script, debt terms, dusk commute, parting shot.

**Reasoning:**
- The outline mixed plain text and markdown, numbered sections unevenly and gave each district a different shape, so gaps were hard to see. Parallel district sections make missing pieces obvious and turn the TODOs into a question list for the lead.

---

## 2026-11-01 — Story: racer type ↔ archetype pairing, "racer types" wording, pink slips cut [story] (Nathaniel, Narrative Lead)

Approved by the lead in the Narrative/Systems chat. Not committed or pushed.

**Changed:**
- `story/canon.md` — new "Racer Types and Archetypes" section: one racer type per archetype per district (table), named rivals may break it, boss stakes (money, rep, rare shop mods, story; a loss means retry).
- `story/pitch.md`, `story/plot.md` — "Racer Archetypes"/"Archetypes" headings and "archetype-based" wording → "racer types", so "archetype" only means the sim's driving style.
- `story/barks.md` — boss stakes: "Pink slips" → "Big cash payout" and "Rare mods unlocked in the shop".

**Reasoning:**
- The lead wants an even pairing: 15 racer types ÷ 3 districts = 5 per district, matching the 5 renamed archetypes (see Barry's entry below).
- Pairings follow what each archetype shows in its first phase, since common racers only race Wild events. Adaptive racers (Honor Student, Consultant, Influencer) will read soft until Barry's phase fix lands.
- Losing the car on a boss defeat was cut in the 2026-06-17 redesign; the design plan is retry on a loss, payout plus rare mods on a win.

**Still open:** the barks "Personalities" list (Calm, Aggressive, ...) and mid-race tone headings will be rewritten as one voice per racer type.

---

## 2026-11-01 — Archetypes renamed to plain English; AR P cut (5 archetypes × 15 racer types) [sim][design] (Barry, Chief of Systems)

Approved by the lead in the Narrative/Systems chat. Not committed or pushed.

**Rename:** Bruiser → **Aggressive**, Endurance → **Defensive**, Swift → **Precise**, AR E → **Balanced**, AR H → **Adaptive**. **AR P removed.** The stat splits and AI phase behaviors of the five survivors are unchanged.

**Changed:**
- `sim/velocity_shift/cars.py` — archetype keys renamed; AR P (40/30/30) removed.
- `sim/velocity_shift/ai.py` — personality configs renamed (`AGGRESSIVE_DRIVER`, `DEFENSIVE_DRIVER`, `PRECISE_DRIVER`, `BALANCED_DRIVER`, `ADAPTIVE_DRIVER`; the `_DRIVER` suffix keeps them apart from `PhaseType.AGGRESSIVE`); AR P config and map entry removed; the `get_personality` fallback is now Aggressive.
- `sim/config/sample_builds.json` — regenerated with `generate_build_matrix.py --write`: 30 presets (5 archetypes × 6 tiers), up from 36.
- `sim/tests/test_cars.py`, `test_equations.py`, `test_simulation.py` — new names. 25/25 pass.
- `design/04-difficulty-tuning.md` (archetype and personality tables), `design/06-pattern-read.md` (sequence sections, the shared-sequence note, the face table), `design/03-deckbuilding-clash.md` (examples, "6 personalities" → 5), `design/notes/mod_notes.md` (example).
- The stat name EN ("Endurance") in `01` and `02` is a stat, not the archetype, so it was left as is.

**Gauntlet after the change** (engine values, 5 archetypes): Aggressive 756–540, Defensive 598–698, Precise 603–693, Balanced 645–651, Adaptive 638–658.

**Reasoning:**
- The lead wants each district to have one racer type per archetype, with racer types leaning to one archetype (named rivals can break it). 15 racer types ÷ 3 districts = 5 per district, so 5 archetypes divide evenly.
- AR P was cut because its stats sit close to Aggressive's and its opening phase attacks every card, so it plays like Aggressive in Wild races (which only use phase 1).
- Names describe how each one drives, so someone outside the dev team can read them.

**Godot (done after the lead's go-ahead, since no playtest was running):**
- `scripts/ArchetypeData.gd` — match arms renamed and AR P dropped (Balanced shares Defensive's EN meta-archetype, face, and comfortable/weak turns; Adaptive shares Precise's).
- `scripts/PersonalityData.gd` — configs renamed (`_aggressive` … `_adaptive`), `_ar_p` removed, fallback is now Aggressive.
- `scripts/TurnTypeData.gd` — base-archetype mapping is now Balanced → Defensive and Adaptive → Precise; the table keys were renamed.
- `design/godot-build-guide.md` — names updated. Its personality phase table was stale (it didn't match `ai.py` for any archetype), so it was replaced with a pointer to `ai.py` and `04-difficulty-tuning.md`.
- No Godot editor on this computer, so the scripts were checked by search only (no old names left anywhere in `scripts/` or `scenes/`), not by running the game.

**Flag for Desmond and Arthur:** with AR P gone, face types are Aggressive = Scowling, Defensive and Balanced = Grinning, Precise and Adaptive = Focused, so two pairs share a face.

---

## 2026-10-31 — Sim tooling fixes: runner crash, gauntlet uses engine values, build-matrix format [sim] (Barry, Chief of Systems)

Tooling only. No game constants, formulas or docs changed. Not committed or pushed.

**Changed:**
- `sim/velocity_shift/simulation.py` — the player card callback took 4 arguments, but `match.run_match` passes 5 (it now also passes the opponent's hand). Every `SimulationRunner` match crashed with a `TypeError`. The callback now accepts the opponent's hand and ignores it, since the simulated player still picks at random.
- `sim/scripts/balance_gauntlet.py` — removed its own copies of the settings and imports them from the engine instead. Archetypes and stats come from `cars.ARCHETYPES` and `cars.build_stats`, encounter ratios from `ai.ENCOUNTER_RATIOS`, turn limits from `cli.ENCOUNTER_MAX_TURNS`, and the opponent level uses the same `round(level × ratio)` rule as `cli.py`. Before this it tested 4 hand-set 800/100/100-style builds, ratios 0.35/0.75/1.15 and 4/10/15 turns, none of which the game uses. It now runs 6 archetypes × 3 encounters, 5832 runs, and still prints ALL CHECKS PASS. The docstring now warns that the archetype PASS rule is only "at least one win and one loss".
- `sim/scripts/generate_build_matrix.py` — rewritten. The old version wrote pow/def/eff presets from a retired stat model into `config/sample_builds.json`, and `cli.py` (`pb["archetype"]`) would then crash on any preset. It now writes the archetype + level format the CLI reads (6 archetypes × 6 tiers) and stores no stats. It only prints a table unless you pass `--write`. Its `--write` output is byte-identical to the current `config/sample_builds.json`, so that file did not change.

**New:**
- `sim/tests/test_simulation.py` — 3 smoke tests for `SimulationRunner` and `simulate_batch`, so a signature drift like this one fails the tests. 25/25 pass.

**Reasoning:**
- The tools have to measure what the engine actually runs before they can back a balance change. The gauntlet in particular was passing while testing values from an older design.

**Still open (not touched here):**
- `scripts/design_opponent.py` and `scripts/design_racers.py` still use the old POW/DEF/EFF model and a hard-coded CLASH_STAKES of 0.3 (the code uses 0.35), and `--stronger` is documented but doesn't exist.
- The rubber-band threshold of 0.15 is hard-coded in `match.py` and copied in the gauntlet's predictor.
- The gauntlet's PASS rule is still too loose to catch imbalance.
- Doc sync and the encounter-scaling proposal (the ratio counts twice, in both opponent level and QTE) come next.

---

## 2026-10-31 — Lean cars: WRX STI, S2000, BRZ at ≤ 2,000 tris with suspension rig and headlamp molding; Part A updated [art] (Arthur, Art Director)

Lead approved the lean rebuilds. The approved originals (S2000 4,354 tris, BRZ 4,079 tris) stay in place for history; the lean build in each car's `lean/` folder is the new game version, with an engine copy in `assets/cars/`.

**New:**
- `art/vehicles/wrx_sti/` — Subaru Impreza WRX STI (GDB "bugeye"), built blueprint-only: pass-2 clay trace (`build_wrx.py`, `make_all.py`, `bp/`, `parts/`, `tex/`, blueprint, keyline table) plus the lean build in `lean/`. **1,966 tris**; IoU side .978 / top .978 / front .956 / rear .956; 9-pose clearance all clear (tightest 18 mm). Headlamps sit in a shallow 3.5 cm pocket cut into the nose with painted lamp art on the lens faces; 4-tri head-glow quad hidden by default.
- `art/vehicles/s2000/lean/` — **1,916 tris**; IoU side .952 / top .992 / front .930 / rear .951; clearance all clear (tightest 3 mm at full lock + bump). Thin raised surround around each headlamp, lamp art re-fitted.
- `art/vehicles/brz/lean/` — **1,999 tris**; IoU side .971 / top .980 / front .948 / rear .932; clearance all clear (tightest 16 mm). Thin raised surround around each headlamp.
- `art/vehicles/lean_common/` — shared lean tools: `leanlib.py` (loft, rig, clearance), `render_kit.py`, `deliver_kit.py` (RGB555 + Bayer sheets), `susp_follow.gd`, `lamps/` (headlamp close-ups, outline segmentation, molding ring), `threeview/` (three-view sheets), `lineup/` (3-car lineup).
- `assets/cars/{wrx_sti,s2000,brz}/` — `car_<id>.glb` (textures embedded), `susp_follow.gd` and a README with the Godot VehicleBody3D / VehicleWheel3D setup, tri count and glow FX note.
- Every lean car: mono body mesh (aero merged), separate hub-pivoted wheels, body origin at the estimated centre of mass, ±30° steering lock, strut + arm on a non-spinning `Susp_XX` follow node driven by `susp_follow.gd`.

**Changed:**
- `design/art/art_direction.md` Part A — budget **≤ 5,000 → ≤ 2,000 tris per car** incl. wheels, struts and FX, detail in shading/textures (A.2.1, A.7, K1); suspension no longer forbidden — only the simple strut + arm rig is allowed (A.2.3); new A.2.6 mono body mesh, A.2.7 suspension + steering rig with the 9-pose clearance test, A.2.8 headlamp light molding + painted lamp art; A.1.5 line classification extended to lamp outlines vs body lines and made binding; Appendix W notes the S2000 lean game version.
- `art/vehicles/s2000/README.md`, `art/vehicles/brz/README.md` — pointer to the lean game version at the top. Nothing else in the original builds changed.

**Reasoning:**
- The lead set a 2,000-tri cap per car: cars need to be cheap enough for the game scene, and the look comes from painted textures and faked shine, not loops.
- Working suspension with separately pivoted wheels mattered more to the lead than extra body detail; the strut sits on a follow node so it tracks travel and steer without spinning with the wheel.
- Flat painted headlamps read as blobs at the lean budget. A little real geometry (shallow pocket on the WRX, thin surround on the S2000/BRZ) plus painted art reads at low cost. The WRX pocket was kept shallow so the nose isn't over-carved.
- The blueprint stays the truth: lamp outlines and pocket depth were taken from classified blueprint lines (body line vs lamp outline), not photos.

**Known gaps:** S2000 and BRZ lean builds have no lamp glow sprites or blob shadow yet; the rig and `susp_follow.gd` are untested inside Godot; S2000 front clearance at full lock + bump is tight (3 mm).

---

## 2026-10-31 — Story canon locked: three Myth Drivers, no informant, Fushigi-Yama summit [story] (Nathaniel, Narrative Lead)

Applies the lead's canon decisions from the lore audit. Not committed or pushed. Mechanical fields (archetype, face type, lie rate, stance preferences) were left as `TODO`.

**New:**
- `story/canon.md` — source-of-truth page: the 10 decisions, a backstory timeline (ousting → breakup → player arrives → districts → summit → ending) and open questions.

**Changed:**
- `story/pitch.md` — fictional mashup city (name `<TBD>`); districts' in-world names `<TBD>`; Fushigi-Yama added to Touge; dusk opening instead of "normal daytime life"; player any gender, Sabine always female (opposite-gender rule dropped); "Circuit specialist" → Street specialist (#3) with Myth Driver numbers per district; Myth Drivers haven't spoken since the breakup; sweep was benign and there was no informant; Sabine believes the rumor; "four Myth Drivers" → three; challenge-each climax → summit meeting; ending → calm decline + parting-shot TODO.
- `story/plot.md` — dusk opening (daylight commute flagged TODO); "U-Haul" and "Novelty Hill Rd" removed; `<Mentor>`/`<mentor>` → Sabine; duplicated garage-intro bullets removed from §3; unfinished garage script flagged TODO; "Americanized" removed; Myth Driver numbers on district beats; sections renumbered 8–11 → 7–10 (there was no §7); "all four" → three; Honor Restoration and Final Meeting rewritten around the Fushigi-Yama summit; cut-off "They each individually agree" kept and flagged TODO; Sabine's arc now "believes the rumor; learns the truth at the summit".
- `story/barks.md` — "$100,000" → "100,000 <currency>".
- `story/characters/sabine.md` — believes the snitch rumor until the summit; Myth Driver #4 line deleted; "tells them to fuck off" → calm decline + parting-shot TODO.
- `story/characters/myth_driver_1/2/3.md` — District field added (Touge/Wangan/Street); snitch rumor named as each one's cover; "sting operation" → police sweep; #2/#3 talking to each other moved clearly into the past; #3 gains the go-pro motive; resolution "Sabine confronts him" → truth comes out at the Fushigi-Yama summit.
- `story/characters/index.md` — pointer to `canon.md`; district added to each Myth Driver.

**Reasoning:**
- The audit found the Myth Driver count (3 vs 4), who knows the truth, who confronts whom, the setting (real US road and dollars vs Japanese districts), time of day and the mentor's gender all contradicting each other across files. The lead resolved them; `canon.md` keeps them in one place so the other files don't drift again.
- Names, the parting shot and the summit setup were left as `<TBD>`/`<TODO>` rather than invented, because the lead decides major plot points.

**Not changed (systems questions for Barry):** pink slips as a boss stake in `story/barks.md` (car loss was removed in the 2026-06-17 mod redesign); the three personality lists that don't map to each other (`barks.md` "Personalities", the barks mid-race categories, and the sim's six AI personalities).

---

## 2026-10-31 — Repo restructure: one layout, one AGENTS.md, one changelog [repo] (Desmond, Chief of Design)

Layout approved by the lead. Done with `git mv` so file history is kept. Not committed or pushed; staged on local branch `restructure` (from `origin/proto-build`) for the lead's review.

**Moves:**
- `velocity-shift/overview/01–06-*.md` → `design/` (same names); `godot_prototype.md` → `design/godot-build-guide.md`; `sample_battle_screen.html` → `design/`; `art_direction.md` → `design/art/art_direction.md`.
- `velocity-shift/Notes/Notes.md`, `mod_notes.md` → `design/notes/`.
- `velocity-shift/story/high_level_story.md` → `story/pitch.md`; `plot_points.md` → `story/plot.md`; `barks.md` → `story/barks.md`; `sabine.md`, `myth_driver_1-3.md` → `story/characters/`; `character_sheets.md` → `story/characters/index.md`.
- `velocity-shift/velocity_shift/`, `tests/`, `scripts/`, `config/`, `main.py`, `pyproject.toml`, `.gitignore` → `sim/`; `readme.md` → `sim/README.md`.
- Godot project (`project.godot`, `scenes/`, `scripts/`, `icon.*`) and Arthur's source-art tree `art/` stay at the root.

**New:**
- `assets/{cars,env,faces,ui,fonts}/.gitkeep` and `design/art/.gitkeep` — empty homes for game-ready art.
- Empty `.gdignore` in `sim/`, `design/`, `story/` so Godot does not import Python, docs or story files.
- `AGENTS.md` (root) — merges the two old AGENTS.md files: repo rules, Godot facts, sim test instructions with `sim/` paths, folder map with owners (Barry: `sim/` + `design/`; Nathaniel: `story/`; Arthur: `assets/`, `art/`, `design/art/`; Desmond: coordination), and the rule that `sim/` code is the source of truth for numbers.
- `CHANGELOG.md` (root) — this file; merges `overview/changelog.md` and `velocity-shift/overview/changelog.md` with every entry kept and tagged by origin.
- `sim/.gitignore` — added `__pycache__/` (running the tests left untracked bytecode in the tree).

**Removed:** `velocity-shift/AGENTS.md`, `overview/changelog.md`, `velocity-shift/overview/changelog.md`, and the now-empty `velocity-shift/` and `overview/` folders.

**References updated:** `design/01-system-overview.md` (architecture tree root `sim/main.py`, docs path `../design/`, `velocity_shift/…` → `sim/velocity_shift/…`), `design/02`, `03`, `04`, `godot-build-guide.md` (`velocity_shift/…` → `sim/velocity_shift/…`), `design/05-skill-trees.md` (`Notes/mod_notes.md` → `design/notes/mod_notes.md`), `design/art/art_direction.md` (pitch path, `godot_prototype.md` → `design/godot-build-guide.md` ×3), `story/characters/index.md` and `sabine.md` (`Notes/06-pattern-read.md` → `design/06-pattern-read.md`), `art/README.md`, `art/vehicles/brz/README.md`, `art/vehicles/s2000/README.md` (art guide path). No game logic or numbers changed. Sim tests: 22/22 pass from `sim/`.

**Reasoning:**
- The Python prototype, design docs and story were all nested under one game subfolder inside the Godot project, with two AGENTS.md files and two changelogs that had already drifted (both received the same 2026-10-31 art entries). One top-level home per discipline lets each bot own one folder.
- Numbers had drifted across docs (HP per level, deck size, stance naming). Making `sim/` the single source of truth and having docs point at it stops further drift. Known conflicts were **listed, not fixed** — they belong to Barry (Systems & Balance).
- `.gdignore` keeps Godot from importing hundreds of non-game files and slowing the editor.

---

## 2026-10-31 — BRZ reference car (detail pass) + S2000/BRZ duo vibe check (Arthur, Art Director)

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


- `art/vehicles/brz/` — **new.** Subaru BRZ (ZD8) built to the vehicle standard (Part A), the same way as the S2000.
  - Size: 4,079 tris (≤ 5k).
  - Blueprint IoU: side .9651 / top .9815 / front .9453 / rear .9275, against gates of .95 / .95 / .92 / .92.
  - Paint: blue, matched to the reference photos.
  - Textures:
    - 1024² body: baked AO, painted form shading for the door scoop, hood valley, haunch and ducktail, and vector panel lines from the blueprint's feature lines
    - 256² atlas: 10 twin-spoke wheel, lamps, honeycomb grille, fictional plate and badges
    - 256×128 painted env map
    - all RGB555 + Bayer
  - Contents: clay + detail build scripts, blueprint data and IoU gate, `.blend/.glb/.obj/.fbx` exports, clean and PSX renders, compare sheets, README.
  - Verified: rebuilt from a temp copy of the folder with the same tri count and IoU, and byte-identical textures.
  - The front 3/4 dealer photo is left out because its licensing is unclear.
- `art/mood/tokyo_v2/` — **added** `scene_duo.py`, `post_duo.py` and `renders/duo/` previews. They show both cars parked side by side on the Tokyo v2 night street, using the same unlit/PSX recipe and post (640×448 → RGB555 + Bayer → 2× nearest). This is a non-binding vibe check; `scene_v2.py` is untouched.
- `velocity-shift/overview/art_direction.md` — A.1.5 added, pending lead review: trust the blueprint and classify its lines before overriding it.

**Reasoning:**
- **The corrected lesson.** The blueprint was right. BRZ passes 2–3 misread the window/DLO lines and trusted a low, about 4%-small photo camera solve. Pass 4 rebuilt from the blueprint alone, like the S2000, and was approved. The lead approved the detail pass ("Way better… hit detail work"), asked to see the BRZ next to the S2000 in a similar scene, and approved pushing to `proto-build` without a PR.

---

## 2026-10-31 — BRZ (detail pass) added; S2000 + BRZ duo vibe check; A.1.5 blueprint lesson (pending review)

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


- `art/vehicles/brz/` — **new.** Subaru BRZ (ZD8), the second car built to Part A.
  - Size and gate: 4,079 tris. Blueprint IoU side .965 / top .982 / front .945 / rear .928.
  - Paint and textures: blue. Painted 1024² body (baked AO, vector panel lines) and a 256² atlas, both RGB555 + Bayer.
  - Lamps: wedge headlights and swept boomerang taillights.
  - Faked shine. Made-up brands only.
  - Contents: build scripts (clay + detail), blueprint data, exports (`.blend/.glb/.obj/.fbx`), key renders and a README.
- `art/mood/tokyo_v2/scene_duo.py`, `post_duo.py`, `renders/duo/` — **new.** The S2000 and BRZ parked side by side on the Tokyo v2 street. This is a vibe check and non-binding. `scene_v2.py` is unchanged.
- `overview/art_direction.md` — **A.1.5 added (pending lead review):** trust the blueprint and classify its lines before overriding it; photos never set geometry. A note corrects the BRZ lesson quoted in A.1.3.

**Reasoning:**
- **The lesson.** The BRZ took four clay passes.
  - Passes 2–3 concluded that "the blueprint draws the car too tall" and moved the body toward a photo camera solve. That solve turned out to be about 4% small and low.
  - The lead's correction: the blueprint doesn't disagree; the window lines were confused.
  - Pass 4 went back to the S2000 method (classify the blueprint lines, build from the blueprint alone, gate on IoU) and was approved ("Way better").
  - Recording the corrected lesson keeps A.1.3's photo check from being read as permission to override the blueprint.
- **The duo.** The lead asked to see the BRZ next to the S2000 in a similar scene before pushing.

---

## 2026-10-31 — Art direction guide + S2000 reference car restored after art-box data loss (Arthur, Art Director)

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


- `velocity-shift/overview/art_direction.md` — **restored (reconstructed)** v2 draft of the game-wide art guide. Part A is the binding vehicle standard; Part B is [VIBE]/[PROPOSAL] scene guidance; Part C has naming, open questions Q1–Q9 and doc conflicts K1–K7; Appendix W is the S2000 worked example.
- `art/` — new source-art tree. `art/vehicles/s2000/` holds the S2000 reference car (build scripts, textures, `.glb/.blend/.obj/.fbx`, blueprint refs, IoU overlays, key renders, README). `art/mood/tokyo_v2/` holds the Tokyo v2 vibe-check scene scripts and small previews (generated files git-ignored).

**Reasoning:** the original guide (written 2026-10-30/31, never committed) and all S2000 work lived only on the art box's `/workspace`, which was wiped when the box moved to a fresh instance (2026-10-31 ~11:31 AM PT; restore step reported "store empty; first boot"). The lead asked to restore the S2000 and the rules and to push finished art to the repo so it can't be lost again.

**Recovery detail:**
- S2000: recovered **verbatim** from the last zip sent in chat (scripts, textures, exports, references). Re-running the scripts reproduces it pixel-identically (4,354 tris; IoU side .961 / top .992 / front .925 / rear .944). Hard-coded `/workspace/s2000` paths were made relative for the repo copy.
- Art guide: **reconstructed** from the approved skill text, the chat record and the surviving style-reference sheet; structure and every binding rule match v2, wording and the Touge/Wangan palette/fog numbers are re-proposed. Two rules from the BRZ build were added and flagged as pending lead review (photo check of window/roof/hood/wheel lines beyond IoU; clay-stage shape sign-off).
- Tokyo v2 scene: scripts **rebuilt** from the recipe (originals lost); the approved original frames survive at `art/mood/tokyo_v2/renders/original_800/`.

**Earlier entries lost with the box (summarised):** 2026-10-31 — first art guide written (general, not S2000-specific, after context from Desmond); later the same day reorganised so the car rules are the only binding standard and all scene content is mood reference ("The key rules are for the cars only. The scene will likely not make it to the game.").

---

## 2026-10-31 — `art_direction.md` restored after data loss (reconstructed v2)

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/art_direction.md` re-added. The v2 draft was never committed and was lost when the art box was wiped (2026-10-31 ~11:31 AM PT). Rebuilt from the approved skill text, the chat record and the surviving Tokyo v2 style-reference sheet.

- **Part A — Vehicle standard [MUST]:** blueprint build + IoU gate (side/top ≥ 0.95, front/rear ≥ 0.92), ≤ 5k tris, painted 1024² body with baked AO, vector panel lines, 256² parts atlas, 512² fabric, RGB555 + Bayer textures, faked shine (ambient + one key + Blinn + painted env map, env ≤ 0.45), opaque cool-tinted glass, no interior/brakes/engine, made-up brands, review in the 640×480 reference frame, checklist, Godot shader sketch (untested).
- **Part B — [VIBE]/[PROPOSAL]:** what made Tokyo v2 work, its palette, district proposals, cameras, portraits/UI, engine notes, advisory scene checklist.
- **Part C:** naming and `art/` layout, open questions Q1–Q9, doc conflicts K1–K7. **Appendix W:** S2000 worked example.
- **New since v2 (flagged pending review):** A.1.3 photo check of window/roof/hood/wheel lines (IoU alone missed a too-tall BRZ body), A.1.4 clay-stage shape sign-off.
- Touge/Wangan palette and fog numbers are re-proposed (originals lost) and still need sign-off (Q2).

**Reasoning:** lead asked to restore the rules from the chat session and push finished art so it isn't lost again.

**Lost entries (summarised):** 2026-10-31 — `art_direction.md` created as the general game art guide (after context from Desmond); then reorganised so car rules come first and are the only binding standard, with all scene content relabelled [VIBE]/[PROPOSAL] and nothing deleted.

---

## 2026-07-07 — Fixed Battle.tscn loading error + missing class_names

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


- `scenes/Battle.tscn` — Fixed `load_steps=2` → `load_steps=6` in scene header. The value was too low (2 instead of 6: 1 scene + 2 ext_resources + 3 sub_resources), causing Godot's parser to choke when encountering all 5 resource entries before node data.
- `scripts/StraightTimer.gd` — Added `class_name StraightTimer` so GDScript can resolve the type in `TurnManager.gd:32` (`straight_timer: StraightTimer`).
- `scripts/CardHandUI.gd` — Added `class_name CardHandUI` so GDScript can resolve the type in `TurnManager.gd:33` (`card_hand_ui: CardHandUI`).
- `scripts/FaceController.gd` — Added `class_name FaceController` so GDScript can resolve the type hint.
- `scenes/Battle.tscn` — Added `FaceController` node (`res://scripts/FaceController.gd`) as child of root `Battle` node.
- `scripts/TurnManager.gd` — Changed static call `FaceController.set_face_sequence(...)` to instance call via `@onready var face_controller: FaceController = $FaceController`.
- `scenes/Battle.tscn` — Added `uid=` fields to `ext_resource` lines (needed in Godot 4.4+). Attached `StraightTimer.gd` to `CornerTimerBar` and `CardHandUI.gd` to `CanvasLayer` so their `@onready` paths resolve. Updated `load_steps` to 9.
- `scripts/RoadScroller.gd` — Changed `extends ShaderMaterial` → `extends Node` with `@export var material: ShaderMaterial`. `ShaderMaterial` (a `Resource`) has no `_process` or `get_tree()` — both are `Node` methods.

**User handoffs (still needed):**
- Register `globals.gd` and `SignalBus.gd` as autoloads in Project Settings
- Color PlayerCube (blue) and OpponentCube (red) materials in editor
- Position Camera3D at (0, 5, 8) looking at (0, 0, -5) — verify after scene import
- Resize ground plane to look like a narrow road lane
- Arrange UI panels so they don't obscure the 3D viewport
- Tune constants in `globals.gd` via playtesting (Step 15)

---

## 2026-07-07 — Full 15-step Godot prototype build

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


Built the complete Godot prototype per `velocity-shift/overview/godot_prototype.md`. 27 scripts + 1 scene + project config.

**Project config:**
- Display: 640×480, viewport stretch, keep aspect
- Input maps: `qte_mash` (Space/X), `qte_timing` (Enter/Z), `ui_accept`, `ui_cancel`

**Phase 1 — Foundation (Steps 1–4):**
- `scripts/globals.gd` — enums, constants (CLASH_STAKES=0.35, DECK_SIZE=192, etc.), lockout lookup
- `scripts/SignalBus.gd` — 12 signals
- `scripts/CombatantStats.gd` — Resource: name, pow, en, han, level
- `scripts/MatchConfig.gd` — Resource: player/opponent stats, max_turns, seed, etc.
- `scenes/Battle.tscn` — Full hierarchy: SubViewport (World3D), CanvasLayer (UI), TurnManager
- `scripts/Deck.gd` — 192-card stat-proportional deck with ALPHA=0.85 smoothing
- `scripts/StraightTimer.gd` — 12s countdown, 3×4s phases, signal on timeout
- `scripts/CardHandUI.gd` — 3 stance buttons, count display, lockout, auto-pick

**Phase 2 — Core Combat Loop (Steps 5–7):**
- `scripts/CombatResolver.gd` — All pure combat math: resolve_stance, clash_mult, compute_damage, mitigation, qte_factor, HAN mod, rubber-band split
- `scripts/TurnManager.gd` — State machine: START→STRAIGHT→CORNER_PLAYBACK→DAMAGE_BATCH→END_TURN→MATCH_COMPLETE, full data flow
- `scripts/QTEController.gd` — Mash (fill bar with depletion) + Timing (oscillating marker) QTE modes, difficulty scaling

**Phase 3 — AI + Tell System (Steps 8–9):**
- `scripts/AIPicker.gd` — EV-scoring card selection, 6 behavior overrides (highest_ev, counter, alternate, repeat_win, etc.)
- `scripts/AIQTE.gd` — Opponent QTE generation with encounter ratio scaling
- `scripts/TurnTypeData.gd` — 8 turn types × 3 archetypes stance sequence tables + QTE type lookup + bluff tables
- `scripts/ArchetypeData.gd` — Meta-archetype mapping, face type, comfort/weak turn zones
- `scripts/PersonalityData.gd` — 6 personalities (Bruiser, Endurance, Swift, AR P, AR E, AR H) with 3 phases each
- `scripts/TrackData.gd` — 3 preset circuit layouts (10-turn sequences)
- `scripts/TellGenerator.gd` — Deception flow: lie rate, position weighting, intensity, comfort/weak scaling
- `scripts/FaceController.gd` — Face display with alpha crossfade, tell overlay

**Phase 4 — Display + Animation (Steps 10–12):**
- `scripts/PositionTracker.gd` — Cumulative DP, gap, rubber-band threshold
- `scripts/DamageDisplay.gd` — DP bar tweens
- `scripts/ClashDisplay.gd` — 2×3 stance grid with color-coded panels
- `scripts/PhaseAnnouncer.gd` — Lap boundary overlay
- `scripts/CarAnimator.gd` — Z-offset by DP gap, surge/drop, corner path blank
- `scripts/AnimationTreeBlendManager.gd` — Stance blend schedule (0-4-8-12s)
- `scripts/BattleCamera.gd` — Chase cam, corner transitions, overtake swing

**Phase 5 — Scene Management (Steps 13–14):**
- `scripts/StageManager.gd` — Scene loading (Battle.tscn) with auto-MatchConfig wiring
- `scripts/RoadScroller.gd` — UV-offset parallax shader material

---

## 2026-07-07 — velocity-shift copied into repo as reference

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


- Copied entire `velocity-shift/` project into midnight-apex root (minus `.git/` and `__pycache__/`) so all prototype reference material is local.
- Updated `AGENTS.md` intro path from absolute `C:\...` to relative `velocity-shift/`.

---

## 2026-07-07 — Initial setup

> *Merged entry — from root `overview/changelog.md` (Godot project log).*


- Created `AGENTS.md` combining midnight-apex project context with velocity-shift reference. Key directives: no auto-push, changelog maintenance, velocity-shift as prototype reference.
- Created `overview/changelog.md` for change tracking.

---

## 2026-07-07 — Human-centric tasks stripped from prototype doc

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


All 16 `🧑 You:` sections removed from `overview/godot_prototype.md` — autoload registration, editor setup, constant tuning, verification steps, and placeholder notes. The doc is now MCP-only; no tasks require manual editor intervention.

**Reasoning:** The `globals.gd`/`SignalBus.gd` autoload registration that was previously a human step is now handled by MCP via `project.godot`. Remaining tuning/verification steps are development workflow notes, not document-level tasks. Removing them keeps the doc focused on what MCP produces.

---

## 2026-07-06 — Godot docs merged into single prototype document

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/godot_outline.md` + `overview/godot_cube_prototype.md` → `overview/godot_prototype.md`

Merged the comprehensive reference outline and the step-by-step cube tutorial into a single 15-step linear document (1400+ lines). Old files deleted.

**Structural changes:**
- 15 sequential steps replace the previous 8-section outline / 10-step tutorial split
- Steps 1–4: Bootstrap, scene, deck, timer + card selection
- Steps 5–7: Combat math, turn manager, QTE
- Steps 8–9: AI layer, tell system (expanded from simplified tells to full face controller)
- Steps 10–14: Display, car animation, camera, corner cinematic, scene management
- Step 15: Tuning loop + deferred items
- Appendices A–H: file manifest, turn flow reference, signals, data flow, art checklist, QTE lookup/difficulty, AI stance lookup, gotchas

**🧑/🤖 split preserved** throughout. All detail from both sources carried forward (lockout, AnimationTree blend, FaceStack, BattleCamera, corner cinematic, RoadScroller, StageManager).

---

## 2026-07-06 — Exit→Entry lockout mechanic

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/03-deckbuilding-clash.md` — added Exit→Entry lockout section with 3 placeholder matrices (Attack / Defend / Steady exit), 8×8 turn-type cross-reference (all TBD except Chicane→Hairpin / Attack→Steady). Narrative justification for the Chicane→Hairpin example.

`overview/01-system-overview.md` — added key design property #9.

`overview/06-pattern-read.md` — updated exit paragraph to reference lockout.

`overview/godot_prototype.md` — lockout in CardHandUI (Step 4), TurnManager fields + static lookup (Step 6), Appendix D data flow.

**Reasoning:** Creates inter-turn sequencing decisions — the optimal exit for this corner may lock you out of an important entry for the next corner, forcing players to think ahead across turn boundaries. Turn-type-dependent lockout means the same exit stance carries different risk depending on what corner comes next.

---

## 2026-07-03 — Cube prototype tutorial added

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/godot_cube_prototype.md` — new file alongside the existing `godot_outline.md`:

- Simplified tutorial-style document focused on getting the combat loop running with colored cubes as placeholder 3D assets
- 10 sequential steps with clear 🤖 MCP / 🧑 Developer split
- 8s straight timer (matching `06-pattern-read.md`), 3 sequential pick phases
- Includes simplified tells (text/color HUD-based, matching `06-pattern-read.md` deception flow)
- Deferred: corner cinematic, car animations, face textures, segment loading, road shader
- Referenced from: `overview/06-pattern-read.md` (stance tables), `velocity_shift/equations.py` (math), `velocity_shift/ai.py` (personalities), `velocity_shift/deck.py` (deck weights)

**Reasoning:** The full `godot_outline.md` is comprehensive but overwhelming for initial prototyping. The cube prototype lets the developer tune gameplay constants before investing in 3D art assets, with a clear tutorial path that distinguishes what MCP automates vs what the developer configures.

---

## 2026-07-03 — Level-gap QTE difficulty scaling

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/godot_outline.md` — QTE timing/mash difficulty is now driven by level gap:

- **§4.1 QTEController.gd** — added `qte_difficulty()` static function: `timing_window_ms` shrinks and `speed_multiplier` increases as `opponent_level - player_level` grows
- **§1.2 globals.gd** — added 4 QTE difficulty constants (`QTE_TIMING_WINDOW_BASE_MS`, `QTE_TIMING_WINDOW_PER_GAP`, `QTE_MASH_SPEED_PER_GAP`, `QTE_TIMING_WINDOW_MIN_MS`)
- **§3.3 AIQTE.gd** — added note that level gap also feeds into AI consistency (shrinking noise range)
- **Appendix E** — added difficulty scaling descriptions for both mash & timing modes, with formula, constants, and example table (gap -10 → +10)
- **Appendix C** — updated data flow step 6 to compute and pass `qte_difficulty` to `QTEController.start()`

**Reasoning:** Higher-level opponents should feel mechanically sharper — your timing windows tighten and your mash rate must increase. The gap-based formula (`gap = opponent_level - player_level`) keeps even matches at base difficulty and only penalizes the player when outmatched.

---

## 2026-07-02 — Decision window updated: 8s real-time + corner cinematic scene

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/06-pattern-read.md` — updated Decision window:
- Removed slo-mo framing; 4s → 8s real-time straightaway approach to select all 3 cards
- Timeout auto-selects unselected positions (semi-random)
- Added corner cinematic scene: camera attached to turn type, car animation driven by selected stances

`overview/godot_outline.md` — timing flow updated to reflect cinematic corner scene after card selection

**Reasoning:** The slo-mo framing added unnecessary complexity (no gameplay need for it) and 4s was too tight to read both car animation channels and pick 3 cards. 8s real-time keeps tension through the straightaway approach. The cinematic corner scene gives visual payoff for the card selections and makes the turn feel like an actual driving moment rather than an abstract clash.

---

## 2026-07-02 — Corner cinematic system + segment-based rendering

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/godot_outline.md` — added corner cinematic system (§4.4):
- Segment-based rendering (Initial D: Another Stage style) — each turn loads/unloads its own straight + corner segment
- Per turn-type authored camera paths (not static camera)
- Stance-driven car traversal along corner Path3D
- QTE runs all 3 phases; damage computed after exit
- Overtake detection: if lead changed, short overtake animation (0.5-1s) + camera swing plays after exit
- Updated §4.1 (QTE runs all 3 phases), §4.2 (corner playback flow with overtake check), §6.1 (segment lifecycle), §6.2 (overtake animation), §6.4 (CarAnimator.play_overtake), §6.5 (BattleCamera.swing_overtake), Appendix A (revised corner flow)

`overview/06-pattern-read.md` — updated exit note:
- Exit reflects position (leading car pulls away, trailing car struggles)
- Overtake as separate short animation after DP resolution if lead changed

**Reasoning:** Segment-based rendering avoids maintaining a full continuous track while keeping each corner visually distinct. Overtake as a post-resolution extra animation gives clear visual payoff for lead changes without complicating the 3-phase stance system.

---

## 2026-07-02 — Merged remote godot_outline.md (1093-line full Godot implementation outline)

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/godot_outline.md` — replaced the 27-line placeholder with the full implementation outline from the remote branch, covering:
- Sections 1–8: Foundation, Engine Core, AI Layer, Corner + QTE, Position + Blend System, 3D Visuals, Art Integration, Wrap
- Appendices A–G: Turn Flow, Signals, Data Flow, Art Checklist, QTE Lookup, AI Stance Lookup, Notes/Gotchas
- My only local edit (timing flow step 3) was already superseded by the remote's more detailed TurnManager state machine and Appendix A corner playback description

`overview/06-pattern-read.md` — preserved local changes (positioning-based car motion, 8s decision window, cinematic corner scene); remote changes to this file (12s, sequential face reveals) were conflicting and discarded per user direction.

---

## 2026-07-02 — Stance projection changed to positioning-based car motion system

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/06-pattern-read.md` — replaced the entire **Car motion types** section:
- **Channel 1 (entry):** track position — outside bias = ATK, center bias = NEU, full-width weaving = DEF
- **Channel 2 (apex):** suspension loading — rear squat = ATK, front dive = DEF, flat = NEU
- Both channels play simultaneously on the straightaway approach before corner entry
- Bluffs use position/suspension that reads opposite the true stance, with secondary cues leaking the truth
- Removed old "in front / behind" framing
- Exit (pos 2) has no dedicated visual channel

`overview/godot_outline.md` — created with implementation outline for TrackPositionController, SuspensionAnimationController, StanceVisualConfig resource, and timing flow.

**Reasoning:** The old front/behind framing was ambiguous (who's in front changes mid-turn) and didn't give a clear visual read under time pressure. Position-based telegraphing maps directly to racing intuition — a car weaving wide is attacking, a car covering the full track is defending, a car holding center is steady. Suspension loading adds a second readable axis for apex intent, and playing both on the straightaway gives the player two simultaneous cross-referencing tells to decode deception.

---

## 2026-06-30 — Decision window added to pattern-read doc

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`overview/06-pattern-read.md` — added a **Decision window** section at the end explaining that time slows to a crawl before each turn, giving the player 4 seconds to read the opponent's face and select a card. Passing on timeout is equivalent to playing a neutral with zero effect.

**Reasoning:** Formalizes the real-time pressure that makes the telegraphing system meaningful — players must read bluff tells under time constraint, not with unlimited analysis. The 4-second window creates a tension rhythm (observe → decide → execute) that matches the racing theme.

---

## 2026-06-26 — Character sheets restructured with pattern-read fields

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Split into per-character files

`story/character_sheets.md` → index; each character moved to their own file (`story/sabine.md`, `story/myth_driver_{1..4}.md`). All 5 sheets now include Myth Driver #4 (was accidentally truncated in the monolithic write). Each containing:
- **Narrative Identity** — role, backstory, conflict, resolution (preserved from old content)
- **Battle Identity** — archetype, face type, comfortable/weak turn types (TODO)
- **Deception Profile** — lie rate, clash-position weighting, intensity, reverse psychology (TODO; hand bluffs excluded per future rework)
- **Progression / Tier** — tier, difficulty class, level range (TODO)
- **Stance Preferences** — notes that strong/weak turns are fixed by archetype per pattern-read tables; other turn types have a per-character per-position preference (TODO)

**Reasoning:** Each character needs mechanical attributes that plug into the pattern-read system (face expressions, bluff behavior, turn-type proficiency) so their in-match behavior is consistent with their narrative identity. The TODO fields are intentionally left blank for the author to assign meaningful values.

---

## 2026-06-26 — Track layout randomization removed from pattern-read doc

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`Notes/06-pattern-read.md` — removed all references to randomized track layout generation:
- **Line 45**: "randomized 10 turn sequence" → "predetermined 10-turn sequence"
- **Lines 46-47**: Removed incomplete "Each match shall include at least" sentence and "Seeded from MatchConfig" line
- **Line 7**: Added narrative framing bullet — tracks are fixed per circuit, archetype cornering habits remain consistent, but bluffing behavior is per-character (driven by lie rate and personality)

**Reasoning:** Player pattern memorization was a concern for fixed layouts, but since the game is narrative-driven, each character has their own bluffing habits defined by lie rate, personality, and the archetype comfort/weak zone system. The track itself becomes authored scenery rather than RNG.

---

## 2026-06-26 — Fixed preset builds format

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


`config/sample_builds.json` used the old stat system (`pow`/`def`/`eff` with no `archetype`/`level`), causing `KeyError: 'archetype'` when selecting a preset build. Replaced with builds keyed by archetype + level, matching the current `cars.build_stats()` API. 36 presets (6 archetypes × 6 tier levels).

---

## 2026-06-26 — Deckbuilding & Clash Docs Rewrite

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Fully rewritten: `overview/03-deckbuilding-clash.md`

The doc was highly out of date vs the codebase. Changes:

- **DECK_SIZE 36 → 192** — all card counts, formulas, composition table ("~12" → "~64"), and strategic cycle math (6 turns → 32 turns) updated
- **Selection phase** — rewritten from batch pick-3-and-arrange to sequential per-position picks with immediate clash resolution (lead → middle → anchor, one card at a time)
- **QTE rubber-band** — replaced the simplified binary split with the actual proportional blend system (threshold = 15% avg max_hp, `blend = min(1.0, abs(gap)/threshold)`)
- **HAN → QTE modifier** — added section documenting `apply_han_qte_mod` / `HAN_QTE_WEIGHT = 0.5`
- **Draw phase / deck reshuffle** — corrected to reflect player discard vs opponent `reshuffle_on_end` (no universal auto-reshuffle)
- **Flowchart** — updated to show sequential clash flow instead of batch arrangement
- **Played cards → discard** — noted opponent cards return to draw pile reshuffled

---

## 2026-06-23 — Unused Code Cleanup

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Removed dead code across the codebase

**Deleted:**
- `velocity_shift/config.py` — entire module; `build_from_archetype` had zero call sites (CLI calls `cars.build_stats()` directly)

**Production modules (`velocity_shift/`):**
- `velocity_shift/ai.py` — removed `ENCOUNTER_CEILINGS` dict (defined but never read); removed unused `rng` param from `_apply_override` signature and call site
- `velocity_shift/models.py` — removed `TurnResult.phase` field (written at `match.py:155` but never read by any code path)
- `velocity_shift/match.py` — removed write to `turn_result.phase`
- `velocity_shift/cli.py` — removed unused `get_phase` import
- `velocity_shift/simulation.py` — removed unused `get_phase` import

**Tests:**
- `tests/test_systems.py` — removed unused `Card`, `ClashResult` imports

**Scripts:**
- `scripts/balance_gauntlet.py` — **rewritten** to use current `resolve_turn` API directly (previously called `run_match` with an incompatible signature and referenced a nonexistent `opponent_ai_mode` field on `MatchConfig`)
- `scripts/generate_build_matrix.py` — removed legacy `MODS_MAP` dict; removed `opponent_builds` from JSON output (unconsumed by the game)
- `scripts/design_racers.py` — fixed two Python 3.11-incompatible f-string backslash expressions (`\u2500` inside `{}`) which also prevented `generate_build_matrix.py` from running

**Config:**
- `config/sample_builds.json` — regenerated without `opponent_builds` key

**Docs:**
- `AGENTS.md` — rewritten for concision: fixed stale test counts (5→9, 6→5, 7→8) and `DECK_SIZE` (36→192); pruned low-signal sections (stats table, damage formula, HP/DNF, encounter table); preserved git/changelog directives and high-signal gotchas; updated `python3`→`python` command

---

## 2026-06-21 — DNF State Removed

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Removed knockout / early-exit mechanic

**Removed** the DNF (Did Not Finish) rule where a combatant would lose when cumulative damage received ≥ max_hp. The match always runs all `max_turns`, then decides by position.

**Files touched:**
- `velocity_shift/match.py` — stripped early-exit check from turn loop; cleaned up stale `knockout` logic
- `velocity_shift/models.py` — removed dead DNF-related fields
- `velocity_shift/cli.py` — removed DNF display wiring
- `velocity_shift/ai.py` — removed DNF-related context from AI callbacks
- `velocity_shift/simulation.py` — removed DNF handling from batch runner
- `testing/test_systems.py` — removed knockout-specific test cases
- `scripts/balance_gauntlet.py` — removed DNF scenario
- `AGENTS.md`, `overview/*.md` — updated docs to reflect position-only win condition

**Reasoning:** DNF created a snowball problem — once a combatant fell behind, their max_hp deficit made recovery impossible. Removing it made races competitive for longer and pushed the decision to the full race distance, where skill (card selection) matters more than early luck.

---

## 2026-06-20 — HAN Stat Use

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Unified HAN → QTE modifier for both sides

**Replaced** the divergent HAN implementations with a single shared formula in `velocity_shift/equations.py`:

- Added `apply_han_qte_mod(qte_score, han_pct)` — same function used for both player and opponent
- Added `HAN_QTE_WEIGHT = 0.5` constant (moved from `ai.py`)
- Added `TYPICAL_QTE = 7.0` — AI QTE baseline, no longer derived from player QTE

**File changes by module:**
- `velocity_shift/ai.py` — `get_ai_qte` simplified: dropped `player_qte` and `ceiling` params, uses `TYPICAL_QTE × ratio` then `apply_han_qte_mod`. Removed local `HAN_QTE_WEIGHT`.
- `velocity_shift/match.py` — `apply_han_qte_mod` applied to both sides' raw QTE after callbacks. Opponent callback type changed to `Callable[[int], float]`.
- `velocity_shift/cli.py` — `get_opponent_qte` simplified to single-param. Removed `ENCOUNTER_CEILINGS` import.
- `velocity_shift/simulation.py` — same simplification. Removed `ENCOUNTER_CEILINGS` import.
- `tests/test_systems.py` — four opponent QTE lambdas updated to `lambda t:` signature.
- `tests/test_equations.py` — added 4 tests for `apply_han_qte_mod`.

**Intent:** HAN now affects QTE score (raw QTE × HAN modifier) for both sides through the same formula. Neutral point at han_pct = 1/3. Swift-like (55% HAN) gets +10.8%, Bruiser-like (25%) gets −4.2%. No double-dipping — HAN modifies the QTE score once, the existing pipeline (qte_factor → compute_damage → damage_mitigation) handles everything else.

---

## 2026-06-17 — Mod System Redesign

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Rewritten: `Notes/mod_notes.md`

**Replaced** the entire mod system design:
- Removed roguelite layer (car loss on boss defeat → narrative gating)
- Single assigned car, chosen from 2–3 chassis archetypes at new game
- Chassis has fixed stat ratio from L1, scales linearly — no convergence
- Mods are shop-bought equipment with trade-offs and unique effects (no drops)
- Loadout slots start at ~3, grow with car level
- Tree/mod categories deferred (TBD)

### Updated: `overview/05-skill-trees.md`

- Stripped speculative per-archetype tree tables
- Replaced "RunMods" references with current Mods system
- Flagged tree design as deferred with link to `Notes/mod_notes.md`
- Kept additive-only principle and system interactions as design guardrails

---

## 2026-06-10 — AI Personality Documentation + HP_PER_LEVEL Fixes

> *Merged entry — from `velocity-shift/overview/changelog.md` (prototype/design-docs log).*


### Updated: `overview/04-difficulty-tuning.md`

**Replaced** the stale `## AI Difficulty (opponent behavior)` section (lines 116–125), which listed long-removed strategy names (`deterministic_attack`, `deterministic_defend`, `deterministic_neutral`, `random`) with an up-to-date section documenting the current phase-based personality system:

- **Personalities table** — all 6 personalities (Bruiser, Endurance, Swift, AR P, AR E, AR H) mapped to their 3 phase-indexed behaviors (AGGRESSIVE / REACTIVE / UNPREDICTABLE with weights and overrides)
- **Phases per encounter table** — Wild (1), Lieutenant (2), Boss (3) with active personality indices
- **Unique opponents table** — ordered permutations per encounter:
  - Wild: 6
  - Lieutenant: 30
  - Boss: 120
  - **Total: 156 unique opponents**

Also **fixed** `HP_PER_LEVEL` value from 120 → 180 to match `velocity_shift/equations.py:20`.

### Updated: `overview/01-system-overview.md`

**Fixed** `HP_PER_LEVEL` value from 120 → 180 in the Normalization section to match `velocity_shift/equations.py:20`.

### Updated: `overview/03-deckbuilding-clash.md`

**Fixed** stale line 72: replaced "configurable strategy (attack-bias, defend-bias, random, etc.)" with a reference to the current phase-based personality system.

---

### Fully expanded: `Notes/06-pattern-read.md`

Replaced the original bullet list with a full spec covering:
- **4 deception mechanics** — lie rate, hand-dependent bluffing, clash-position weighting, reverse psychology tell
- **Turn type system** — 8 turn types (Hairpin, Straight, Chicane, Banked, S-Curve, Technical, Esses, Tunnel) with archetype-turn stance preference table (6×8 grid)
- **Track layout generation** — random per match, seeded, wraps if needed
- **Face types** — 6 cohesive expression palettes (one per archetype), 3 expressions each (ATK/DEF/NEU)
- **Expression intensity** — scale 1–5, gated by tier and encounter type
- **Bluff tell** mechanics — per-face-type betrayal signals, perceptibility tied to intensity
- **Tell generation flow** — step-by-step how a face is determined each turn
- **Combined deception axis** table including intensity values
