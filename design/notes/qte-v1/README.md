# qte-v1 — visible QTE window

Approved by Austin on 2026-11-11 and ported into `sim/` the same day. This folder is the record of the draft (`RESULTS.md`, `results.json`); it is no longer unapproved.

The live constants and functions live in `sim/velocity_shift/equations.py` (`QTE_ZONE_BASE_MS`, `QTE_ZONE_WIDTH_105`, `QTE_SKILL_SIGMA_OVER_A0`, `qte_zone_width`, `expected_hit_quality`, `raw_qte_score`). Skill σ values remain placeholders until playtest.

To reproduce the draft tables (does not edit `sim/`):

```
python3 run.py
```

Count banks are the existing final-v1 / lines-v1 official banks (q_read = 0.6).
