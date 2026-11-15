# mods-v1 — decision record (draft, Barry, 2026-11-14)

**Picked by Austin (2026-11-14), relayed by the lead agent:**
1. **4 mod slots** (replaces the old 6-slot rule; `MOD_SLOTS` 6 → 4 at go-live).
2. **Canon staging in every round:** the round's Mk1 set (POW / HAN / EN) opens with the round, Mk2 unlocks after the mat1 win, Mk3 after the mat2 win (visible, locked, from round open). R1's shop opens on the Prologue race-3 win (`MOD_UNLOCK_RACE = 3`). Arc: MYTH1 after P1, MYTH2 after F1, MYTH3 after F2, MYTH4 after F3.
3. **Aspire Mk3 prices:** `MOD_R2_*_MK3` $5,000, `MOD_R3_*_MK3` $8,000 (R1 Mk3 stays $1,000).
4. **IDs only, no display names yet:** `MOD_<R1|R2|R3|ARC>_<POW|HAN|EN>_<MK1..MK3|MYTH1..MYTH4>`, aero `<ID>_AERO`.

Unchanged rules: each mod boosts one fixed stat and never changes or levels; rebalancing is buying / equipping new mods plus
the 20 % retune; at most one aero (1.75×, after the R1 boss); wholesale −20 % on R1–R3 mods during R2–R3; the mod cap stays
1.07 × P.

## Final catalog (4 slots)
| Unlocks | IDs (× POW / HAN / EN) | Points | Price |
|---|---|---|---|
| R1 open (Prologue race 3 win) | `MOD_R1_{POW,HAN,EN}_MK1` | 213 | $150 |
| after R1 mat1 | `MOD_R1_{POW,HAN,EN}_MK2` | 218 | $500 |
| after R1 mat2 | `MOD_R1_{POW,HAN,EN}_MK3` | 223 | $1,000 |
| R2 open | `MOD_R2_{POW,HAN,EN}_MK1` | 242 | $700 |
| after R2 mat1 | `MOD_R2_{POW,HAN,EN}_MK2` | 249 | $1,500 |
| after R2 mat2 | `MOD_R2_{POW,HAN,EN}_MK3` | 255 | $5,000 |
| R3 open | `MOD_R3_{POW,HAN,EN}_MK1` | 279 | $1,200 |
| after R3 mat1 | `MOD_R3_{POW,HAN,EN}_MK2` | 288 | $2,500 |
| after R3 mat2 | `MOD_R3_{POW,HAN,EN}_MK3` | 292 | $8,000 |
| arc: P1 win | `MOD_ARC_{POW,HAN,EN}_MYTH1` | 333 | $2,500 |
| arc: F1 win | `MOD_ARC_{POW,HAN,EN}_MYTH2` | 375 | $4,000 |
| arc: F2 win | `MOD_ARC_{POW,HAN,EN}_MYTH3` | 426 | $6,000 |
| arc: F3 win | `MOD_ARC_{POW,HAN,EN}_MYTH4` | 501 | $8,000 (stand-in, = live T4) |

Machine-readable: `catalog_final.json`. Per-rung money and gear: `final_tables.md`.

## Verified (sim, config `final_4`, realistic just-in-time buyer)
- 60/60 at cap 31.6 / 40.1 / 30.2 (≥ 30) · 80/80 at cap 94.9 / 91.6 / 92.9 (90–95) — same as live.
- 80/80 story-only minimums 53.0 / 54.4 / 50.5, bosses 53.0 / 57.7 / 55.8 (≥ 50) — same as live.
- Mixed grinds 3+10 / 3+10 / 4+8 (wall 3–6) · 60/60 13 / 15 / 18 — same as live.
- Finale 80/80 81.7 / 82.7 / 79.3 / 81.7; finale grinds per step 60/60 11 / 7 / 7 / 9, 60/80 7/6/6/7, 80/60 6/6/6/7, 80/80 0.
- Grind races: 60/60 min 50.3 %, 80/80 min 85.6 %.

## Open flags (not caused by the catalog unless stated)
- 60/60 needs **11** grinds in finale step 1 (target ≤ 10); identical in live and the full-fill control.
- R3 story-only minimum is 50.5 % (oh1), thin but as live.
- Catalog effect: early R1 is a little harder than live (80/80 kid2 95.5 vs 98.9; 60/60 R1 kid1 50.3 vs 85.6), because live assumed mods the player couldn't afford.
- Price guards: R1 Mk3 ≤ $1,000; MYTH4 ≤ $8,000 (both tested).
- Stock part value (150 per slot) and the per-slot mod model are new and not in live yet.
- MYTH4 $8,000 is still a stand-in.
- Money wording in design docs belongs to Desmond's USD pass, so the price rows need his sign-off.
