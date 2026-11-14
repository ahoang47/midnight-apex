# Decision: campaign cut only (Austin, 2026-11-14)

Austin: "I think campaign cut only. The finale race is a narrative conclusion so the pacing would be affected otherwise."

- **Chosen:** campaign set `C_rec` from RESULTS.md. R1 every story race ×0.90 (effective `STORY_FILL` 0.558), R2 oh2 ×0.60, R3 oh2 ×0.80.
  Made live as `STORY_XP_MULT` in `sim/velocity_shift/equations.py`.
- **Rejected:** the arc/finale settings (t62 and t55, and the flat arc cut).
  The finale is the story's conclusion, and both settings change its pacing: mixed players grind 11/10/8/10 (t62) or 13/12/9/12 (t55) per finale step instead of 7/6/6/7, and the strong player arrives 2-3 levels lower.
  `ARC_STORY_FILL` (0.80) and `FINALE_ARC` stay exactly as live.
- **Not taken:** the `C_even` R2 variant (oh1+oh2 ×0.70). It costs one more grind in R2 for mixed and 60/60.
  With `C_rec`, R2's oh2 win doesn't reach a new level before the boss (80/80 arrives at L23 for both oh2 and the boss).

Verified on the live sim after the change (`python scripts/run_progression.py --rows`, plus this folder's `arc.py` with no arc multipliers):
- 80/80 story-only boss (hardest track): R1 L6 53.0, R2 L23 57.7, R3 L41 55.7. Lowest story race per round 53.0 / 54.1 / 50.4. Ends L7 / L25 / L43.
- Mixed: 3+10 / 3+10 / 4+8, cash $11,150 / $42,372.50 / $78,282.50. 60/60: 13 / 15 / 18 grinds, boss at cap 31.6 / 39.3 / 30.6.
- Finale unchanged: 80/80 billed 81.7 / 82.7 / 79.3 / 81.7 at L61 / 76 / 91 / 112. Arc grind 7/6/6/7 (60/80), 6/6/6/7 (80/60), 11/7/7/9 (60/60).

Note for re-runs: `camp.py` multipliers now stack on the live `STORY_XP_MULT`. Use `camp.uniform((1, 1, 1))` for the live state.
