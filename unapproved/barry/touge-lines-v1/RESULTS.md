# touge-lines-v1: one Touge track, two directions (DRAFT, NOT APPROVED)

Barry, 2026-11-13. Austin asked why a player has to retune per Touge race, then to try fixing that by Touge line choices rather than the heat equations. Mid-study he clarified the official count (2026-11-13): **Touge is one track run uphill and downhill; Street and Wangan are two tracks each, run CW and CCW** (four variants per district). This study models that draft set first, then asks whether Touge line edits are still needed.

Nothing in `sim/` or `design/` was edited. Nothing is committed. Live constants stay at G2 (`G2_slant_m10`). Code: `tracks_draft.json`, `model.py`, `run_study.py`, `analyze_study.py`. Quoteable numbers are the full G2-rules run: **9 batches × 1,000 races** (seeds 20261112–20261120), 10 draft laps × 10/20/30 turns × 3 boss styles, 21-split grid + even, common random numbers across tunes (`results_baseline.npz`). A 1×400 screen (`results_baseline_screen.npz`) was used only to check the shape; it is not quoted below.

`design/01-system-overview.md` still says **3 tracks per district, 9 in total** (Austin 2026-11-12). That line will need updating. Not edited here.

## Draft track set

`sim/config/tracks_v1.json` still has five stand-in layouts per district and contradicts the 2026-11-13 count. The study set is in `tracks_draft.json` only:

| District | Layouts (from existing stand-ins) | Variants |
|---|---|---|
| Touge | `T1_Akina_Switchbacks` (hairpin-heavy switchback; signature HP / ES / DR) | `T_Uphill` = authored order; `T_Downhill` = reversed |
| Street | `S1_Shibuya_Grid`, `S3_Shinjuku_Underpass` | each × CW (authored) and CCW (reversed) |
| Wangan | `W1_Bayshore_Run`, `W3_C1_Outer` | each × CW and CCW |

Ten variants total. T2–T5, S2/S4/S5, W2/W4/W5 are dropped for this study.

**Reverse rule (PLACEHOLDER):** CCW and downhill reverse the corner order, and **IR ↔ DR** (an increasing-radius corner is decreasing-radius the other way). HP, ES, CH, N90, CR, SW are treated as direction-symmetric. The sim has no left/right handedness, so CW vs CCW is order plus that flip only.

That flip does nothing to Street S1/S3 (each already has one IR and one DR, so the multiset is unchanged). It does a lot to Wangan: the authored laps are IR-heavy and have no DR, so CCW is DR-heavy and the after-wear mix flips from POW-heavy to HAN-heavy (W1 CW 0.385/0.260/0.354 vs CCW 0.260/0.408/0.332). Touge T1 has two DR and no IR, so downhill becomes two IR.

## Uphill / downhill heat (Arthur)

Cited, and followed where they actually specify a number:

- `unapproved/arthur/mockups/districts/README.md` Pass 2 (Austin 2026-11-13) and the 2026-11-13 CHANGELOG entry “Touge on a grade”: the Touge road **climbs at 8.5% on the approach**, crests in the hairpin (0% at about 75% of the arc), **falls at 5% out of it**, and banks up to 6% (outside high). **Street and Wangan stay flat.** That art pass was presentation-only (“scoring unchanged”; sim not edited).
- `design/art/world_notes.md` (Austin 2026-11-02, Arthur): optional elevation for hills/Touge in the overworld; race tracks are pregenerated 10-turn segments, not a continuous course. No uphill/downhill heat rule there.
- Story: hairpin alt1 bark “the downhill does the passing” (`story/corner_lines.md`); epilogue is a low-stakes downhill run (`story/canon.md`, `plot.md`). No heat numbers.

There is no published sim rule for whole-race uphill vs downhill heat. PLACEHOLDER used here, after `track_wear` and with total load renormalised (so a direction is not just harder overall):

- Uphill: wear × `(1+0.085, 1, 1-0.05)` for POW / HAN / EN (8.5% climb, 5% residual drops).
- Downhill (reversed hairpin: 5% local climbs, 8.5% drops): wear × `(1-0.05, 1, 1+0.085)`.
- Street and Wangan: no gravity.

At this scale the tilt is small. Gravity-off vs gravity-on after-wear mixes (`demand_draft.json`): uphill 0.303/0.334/0.363 → 0.327/0.331/0.342; downhill 0.406/0.282/0.312 → 0.383/0.281/0.336. The IR↔DR flip is the main mix change; gravity slightly pulls the two directions together. The quoted run uses gravity on.

Because the official set changed from 15 laps to 10, **capacity and recovery recalibrate**. Cross-track average demand mix is now 0.320/0.294/0.387 (POW/HAN/EN), vs 0.351/0.295/0.353 on the old 15 stand-ins. Less POW capacity, more EN. That matters on Touge, where a correct read of the HAN-heavy mains plays a lot of POW.

## Background: why the old five Touge stand-ins needed a per-race tune

From the live G2 npz, before this draft set (`diagnosis.json`; not re-quoted as the current answer): the single “best on average” Touge tune (0.45/0.30/0.25) was essentially T1’s car and died on T5 (gaps of 13–22 pp at the cap). T1 wanted a POW-heavy split; T2 and T5 wanted 0.25/0.25/0.50 brakes on every length. Those preferred cars came from the signature HP/ES/DR mix, which is 7–9 of 10 corners on every old Touge stand-in, so non-signature line edits could not have unified them. Dropping T2–T5 removes that conflict.

## Does one Touge tune work for both directions?

**Yes.** The average player at the cap (read 0.6, QTE 0.6, pacing 0.6), one fixed Touge split **0.40 / 0.30 / 0.30** (POW/HAN/EN):

| | 10 | 20 | 30 |
|---|---|---|---|
| Touge district-fixed (both directions) | 65.2 | 53.5 | 40.9 |
| Touge per-race retuned | 67.0 | 54.2 | 41.8 |
| Retune gap (per-race − fixed) | 1.9 | 0.7 | 1.0 |
| T_Downhill, same fixed tune | 68.4 | 56.3 | 44.4 |
| T_Uphill, same fixed tune | 61.9 | 50.7 | 37.4 |

The fixed tune is at most 1.9 pp behind a per-direction retune. Uphill is the harder run (6.5–7.0 pp below downhill at the same tune), but it does not want a different car: its best splits sit next to 0.40/0.30/0.30. Downhill’s best cells are a bit more even/EN, and the shared 40/30/30 still holds.

## Does Touge still lag Street and Wangan?

**Yes, at 20 and 30 turns. Not because of retuning.** Same average player, one tune per district:

| District-fixed at the cap | Tune (P/H/E) | 10 | 20 | 30 |
|---|---|---|---|---|
| Touge | 0.40 / 0.30 / 0.30 | 65.2 | **53.5** | **40.9** |
| Wangan | 0.25 / 0.30 / 0.45 | 68.8 | 70.6 | 67.6 |
| Street | 0.50 / 0.25 / 0.25 | 74.7 | 67.8 | 57.4 |
| Touge − Wangan | | −3.6 | **−17.1** | **−26.7** |
| Touge − Street | | −9.5 | **−14.3** | **−16.5** |

The ~3 pp band is missed at every length vs Street, and at 20/30 vs Wangan (10-turn Touge is 3.6 pp under Wangan). Per-race retuning does not close it (Touge 67.0 / 54.2 / 41.8 vs Wangan 76.1 / 75.6 / 71.8). Uphill at 30 turns is 37.4% even when the tune is the cell’s best.

10-turn grind races stay in the easy band for all three districts (65–75). 80/80 at the cap stays high everywhere, including Touge (97.5 / 94.1 / 92.2). Perfect play at 1.0 is 100 on every district and length. Perfect play at 0.8, per-race tuned: Touge 59.8 / 14.1 / 18.2; Wangan 61.9 / 22.1 / 23.4; Street 76.2 / 47.2 / 63.9. A single district tune for that 0.8 player is much worse on Touge at 20/30 (5.4 / 1.1) — that player is more tune-sensitive than the average cap player.

Feel, average player at the cap, district-fixed tune. “Counter locked” is the share of correctly-read clashes whose counter is locked; “all three locked” is the limp share of clashes.

| | Touge 10/20/30 | Wangan 10/20/30 | Street 10/20/30 |
|---|---|---|---|
| Corners with a lock | 38.8 / 57.2 / 66.8 | 57.5 / 67.7 / 72.0 | 59.3 / 70.5 / 74.8 |
| Counter locked | 13.7 / 31.0 / 41.0 | 19.5 / 29.4 / 34.3 | 23.4 / 35.4 / 40.2 |
| All three locked (clash share) | 4.3 / 18.6 / **27.1** | 6.5 / 14.7 / 19.2 | 3.6 / 12.8 / 16.9 |
| Mean lock duration (extra corners) | 2.23 / 4.01 / 4.89 | 3.00 / 4.25 / 4.87 | 2.45 / 3.58 / 4.06 |
| Locks by bar (POW / HAN / EN) | 25.5 / 38.9 / 35.6 | 41.4 / 42.1 / 16.5 | 15.2 / 40.4 / 44.4 |

Touge does not lock more often than the others, but at 30 turns it limps more (27% of clashes). That is the long-race collapse: once all three bars are stuck, the rest of the race is barely playable.

## Are Touge line edits needed?

**Not for “one tune works uphill and downhill.”** That already holds with the current `LINE_SET_C` Touge mains. No candidate line table was run, and none is recommended for that goal.

**They are also the wrong tool for the 20/30 district-parity gap**, unless Austin wants to reopen signature lines with Desmond. This layout is 4 HP + 2 ES + 2 DR + 1 N90 + 1 CH (8 of 10 are Touge signature corners: hairpin `EHP`, esses `HHH`, decreasing-radius `HEH`; `story/corner_lines.md`). Alts were left untouched. The only mains a line pass could legally change here are N90, CH, and downhill’s IR (the flipped DR). Those cannot explain a 17–27 pp hole against Wangan, and the hole is already there when the car is retuned per race. Closing it would mean changing signature lines (in particular esses `HHH`, which a correct read answers with `PPP` and the repeat surcharge), changing the heat equations, or accepting that long Touge races are the hard ones.

A related calibration fact, not a line fact: dropping the other four (mostly POW-demanding) Touge stand-ins, and flipping Wangan CCW from IR to DR, moved average demand toward EN. Touge’s correct-read play is still POW-heavy, so the new capacity mix is a worse fit than on the 15-lap G2 set, where the same T1 uphill layout scored much higher (G2 per-race, average at the cap: 69.4 / 68.0 / 61.7). That older figure is from a different official set and is only context.

## Other findings (not Touge lines, but they show up on this set)

- **Wangan’s one-tune gap is larger than Touge’s** (per-race − fixed: 7.3 / 5.0 / 4.2 pp). CW wants a different car from CCW because of the IR↔DR flip (W1 CW best cells go to 0.25/0.25/0.50 or a HAN-heavy 10-turn split; CCW stays ~0.30/0.25/0.45). Absolute rates still stay high, so it does not “lag,” but if the IR↔DR assumption stands, Wangan is the district that actually wants a per-direction retune. If Austin would rather CW/CCW keep the same corner types (no IR↔DR), Wangan’s mix would not flip; I have not run that alternative.
- **Street at 30 turns is soft on S1** (fixed 50.5 CCW / 48.5 CW) and fine on S3 (64.7 / 65.7). The district average at 30 is 57.4, under the old 60–75 cap target. S1 and S3 also differ more from each other (up to 17 pp) than Touge’s two directions do.
- **Retune vs even / vs wrong district** (per-race tuned, average at the cap): 8.5 pp vs even, 17.4 pp vs the other districts’ best cell tune (was 13.5 / 26.7 on the 15-lap G2 set). Still a meta, weaker than G2. A Street car on Wangan is the worst mismatch (district-fixed Street tune on Wangan: 50.4 / 29.5 / 17.7). A Wangan car on Touge is 60.4 / 45.0 / 35.4, vs Touge’s own 65.2 / 53.5 / 40.9.
- **Reads vs pacing** (per-cell tuned): reads (perfect read − random guess, both best pacing) **27.7 pp**; pacing at read 0.6 (best − greedy) **17.3 pp**; ratio 0.62. A no-read perfect pacer still wins 72.3% at the cap. By district the mix is not even: Touge pacing 31.4 vs reads 20.3; Wangan pacing only 5.6 vs reads 20.9; Street reads 38.2 vs pacing 21.9. Long races are where pacing bites (6.2 / 19.0 / 26.7 at 10/20/30).

## Recommendation

Keep the current Touge default lines. One 40/30/30 Touge tune already covers uphill and downhill. Do not spend a line pass on a gap that retuning does not close.

Decide with Austin (and Desmond if lines or named-track identity come into it):

1. Is long Touge *supposed* to be the hard district at 20/30, with only the 10-turn grind in the 60–75 band?
2. If not, the fix is not non-signature line edits. It is signature-line / layout / equation-or-calibration work, which this brief left alone.
3. Confirm or drop the IR↔DR reverse rule — it is the thing that makes Wangan CW and CCW want different cars.
4. Update `design/01` (3 tracks per district → 2 Street + 2 Wangan + 1 Touge, each with two directions). Flag only; not edited.
5. The 8.5% / 5% gravity tilt is a PLACEHOLDER on top of Arthur’s presentation grades. If Austin wants a stronger or weaker grade effect, say so and I will rerun.

No story-character or signature bluff lines were changed. No limp-mode or boss-heat change. Arthur’s grade remains presentation in the live build; only this study applies it to wear.
