# qte-v1 — visible QTE window replaces hidden knot_window(r)

Draft only (`/workspace/barry-drafts/qte-v1`). No repo edits. Austin's direction (2026-11-10): the stat gap should make the visible QTE harder or easier, replacing the hidden `knot_window(r)` multiplier; specific mods exist that only widen the QTE window; the QTE must not change with mid-race position.

All win rates below were produced by this run from the official clash-count banks (q_read = 0.6, N = 4000, seeds 20261113–15 × 10/20/30 turns). Skill σ values and the linear-falloff press model are **placeholders until playtest data exists**. Numbers are not invented.

## 1. QTE model (placeholders)

- Timing error `e ~ Normal(0, σ)`, unbiased.
- Zone width `w`, default `w0 = 800 ms` (Godot `QTE_TIMING_WINDOW_BASE_MS`; presentation unit only). Half-width `a0 = 400 ms`.
- Hit quality: `s = max(0, 1 − |e| / (w/2))` — 1 at centre, 0 at the edge and outside.
- Raw turn score used here is `E[s]` (closed form), as a constant `q_time`. This matches the oracle's fixed-`q_time` methodology. Multiple presses would not change `E[s]`; mash speed is unused in this draft.
- `q_eff = raw × HAN modifier`, with **no** `knot_window`. Runs are balanced (HAN share = 1/3, modifier = 1), so `q_eff = raw`.
- Zone width depends on the race's fixed stat ratio `r`, not on mid-race lead.

| profile | target E[s] at default zone | σ / a0 | σ (ms) | achieved E[s] |
|---------|----------------------------:|-------:|-------:|--------------:|
| weak | 0.4 | 0.907473 | 362.989 | 0.400000 |
| average | 0.6 | 0.513963 | 205.585 | 0.600000 |
| strong | 0.8 | 0.250668 | 100.267 | 0.800000 |

Closed-form check vs Monte Carlo (n=200,000): max |Δ| = 0.001314.

## 2. Zone width w(r)

`w(r)` is chosen so the **average** player's expected raw score equals `0.6 × KNOT_WINDOW_105(r)`, the current effective `q_time × window` value. Widths are fractions of the default zone.

| r | W(r) | target E[s] = 0.6·W | w(r)/w0 | w (ms at w0=800) |
|--:|-----:|--------------------:|--------:|-----------------:|
| 0.80 | 0.41 | 0.2460 | 0.3276 | 262.1 |
| 0.85 | 0.41 | 0.2460 | 0.3276 | 262.1 |
| 0.90 | 0.41 | 0.2460 | 0.3276 | 262.1 |
| 0.95 | 0.43 | 0.2580 | 0.3448 | 275.8 |
| 1.00 | 0.68 | 0.4080 | 0.5802 | 464.2 |
| 1.05 | 1.00 | 0.6000 | 1.0000 | 800.0 |
| 1.10 | 1.00 | 0.6000 | 1.0000 | 800.0 |

On the 0.80–1.10 grid (step 0.0025): monotone non-decreasing = True; min first difference = 0.000000e+00; max first difference = 0.027071 (steepest step r=1.0475→1.0500). `w(r)` is flat on [0.80, 0.90] (inherited from W) and plateaus for r ≥ 1.05 at the default zone. Between knots it is a smooth increasing transform of the piecewise-linear W, so it has the same kinks as W (derivative jumps at 0.90, 0.95, 1.00, 1.05) but the segments are not linear in w.

## 3. Oracle cells, window removed

New model: `qhat = E[s | w(r), σ_profile]`. Current model (comparison): `qhat = q_time × W(r)` with q_time 0.4 / 0.6 / 0.8. **q_read stays 0.6** in both (timing only; this is not the official table's q=0.8 column, which also changes read skill). Average should sit inside the official 0.6 band ±2 points.

### Average vs official 0.6 band

| cell | r | official 0.6 | current model (0.6·W) | new model (E[s]) | Δ mid vs current | inside official ±2? |
|------|--:|-------------:|----------------------:|-----------------:|-----------------:|--------------------:|
| Touge boss at target | 1.05 | 63.4–67.8 | 63.4–67.8 | 63.4–67.8 | +0.00 | True |
| Wangan boss at target | 1.05 | 62.0–66.8 | 62.0–66.8 | 62.0–66.8 | +0.00 | True |
| Street boss at target | 1.05 | 61.4–65.1 | 61.4–65.1 | 61.4–65.1 | +0.00 | True |
| Touge mature #2 skipped | 1.0355 | 41.8–51.4 | 41.8–51.4 | 41.8–51.4 | +0.00 | True |
| Wangan mature #2 skipped | 1.0355 | 43.9–52.1 | 43.9–52.1 | 43.9–52.1 | +0.00 | True |
| Street mature #2 skipped | 1.0355 | 42.8–49.6 | 42.8–49.6 | 42.8–49.6 | +0.00 | True |
| Myth #2 skipped | 1.0336 | 41.1–48.4 | 41.1–48.4 | 41.1–48.4 | +0.00 | True |
| Summit skipped | 1.0359 | 42.5–51.4 | 42.5–51.4 | 42.5–51.4 | +0.00 | True |

### Skill spread: new E[s] vs current q_time × W(r)

At r = 1.05 the default zone is used, so the three profiles reproduce 0.4 / 0.6 / 0.8 exactly and the win-rate spread matches the current model. At r < 1.05 the tighter zone does **not** scale scores linearly: a strong player loses less than `0.8·W(r)` would predict, a weak player a little more than `0.4·W(r)`.

| cell | profile | qhat current | qhat new | official-style band current | band new | Δ mid |
|------|---------|-------------:|---------:|----------------------------:|---------:|------:|
| Touge boss at target | weak | 0.4000 | 0.4000 | 6.5–23.9 | 6.5–23.9 | +0.00 |
| Touge boss at target | average | 0.6000 | 0.6000 | 63.4–67.8 | 63.4–67.8 | +0.00 |
| Touge boss at target | strong | 0.8000 | 0.8000 | 81.7–95.0 | 81.7–95.0 | +0.00 |
| Wangan boss at target | weak | 0.4000 | 0.4000 | 6.9–22.5 | 6.9–22.5 | +0.00 |
| Wangan boss at target | average | 0.6000 | 0.6000 | 62.0–66.8 | 62.0–66.8 | +0.00 |
| Wangan boss at target | strong | 0.8000 | 0.8000 | 81.4–94.5 | 81.4–94.5 | +0.00 |
| Street boss at target | weak | 0.4000 | 0.4000 | 6.5–22.3 | 6.5–22.3 | +0.00 |
| Street boss at target | average | 0.6000 | 0.6000 | 61.4–65.1 | 61.4–65.1 | +0.00 |
| Street boss at target | strong | 0.8000 | 0.8000 | 79.5–94.0 | 79.5–94.0 | +0.00 |
| Touge mature #2 skipped | weak | 0.3629 | 0.3503 | 1.5–13.5 | 1.0–11.5 | -1.24 |
| Touge mature #2 skipped | average | 0.5443 | 0.5443 | 41.8–51.4 | 41.8–51.4 | +0.00 |
| Touge mature #2 skipped | strong | 0.7258 | 0.7661 | 75.0–86.6 | 76.0–91.1 | +2.77 |
| Wangan mature #2 skipped | weak | 0.3629 | 0.3503 | 1.9–11.8 | 1.2–10.4 | -1.03 |
| Wangan mature #2 skipped | average | 0.5443 | 0.5443 | 43.9–52.1 | 43.9–52.1 | +0.00 |
| Wangan mature #2 skipped | strong | 0.7258 | 0.7661 | 74.7–86.3 | 76.1–90.5 | +2.79 |
| Street mature #2 skipped | weak | 0.3629 | 0.3503 | 1.7–11.9 | 1.0–10.5 | -1.06 |
| Street mature #2 skipped | average | 0.5443 | 0.5443 | 42.8–49.6 | 42.8–49.6 | +0.00 |
| Street mature #2 skipped | strong | 0.7258 | 0.7661 | 73.0–85.3 | 74.0–89.6 | +2.64 |
| Myth #2 skipped | weak | 0.3580 | 0.3442 | 1.4–11.2 | 0.9–9.7 | -1.00 |
| Myth #2 skipped | average | 0.5370 | 0.5370 | 41.1–48.4 | 41.1–48.4 | +0.00 |
| Myth #2 skipped | strong | 0.7160 | 0.7613 | 69.8–83.6 | 76.1–88.8 | +5.76 |
| Summit skipped | weak | 0.3639 | 0.3516 | 1.6–13.5 | 1.2–12.1 | -0.90 |
| Summit skipped | average | 0.5459 | 0.5459 | 42.5–51.4 | 42.5–51.4 | +0.00 |
| Summit skipped | strong | 0.7278 | 0.7671 | 75.6–86.6 | 76.0–91.2 | +2.51 |

Pooled (equal-weight mean of the three districts, then min/max over seeds × lengths) for the shared-r skip cells:

| cell | r | profile | current pooled | new pooled | Δ mid |
|------|--:|---------|---------------:|-----------:|------:|
| mature #2 skipped (any district) | 1.0355 | weak | 1.8–12.4 | 1.1–10.8 | -1.12 |
| mature #2 skipped (any district) | 1.0355 | average | 43.0–50.7 | 43.0–50.7 | +0.00 |
| mature #2 skipped (any district) | 1.0355 | strong | 74.7–85.7 | 75.7–90.0 | +2.65 |
| Myth #2 skipped | 1.0336 | weak | 1.4–11.5 | 0.9–9.9 | -1.05 |
| Myth #2 skipped | 1.0336 | average | 40.2–47.4 | 40.2–47.4 | +0.00 |
| Myth #2 skipped | 1.0336 | strong | 70.0–83.2 | 75.7–88.3 | +5.40 |
| Summit skipped | 1.0359 | weak | 1.8–12.4 | 1.2–11.3 | -0.91 |
| Summit skipped | 1.0359 | average | 43.6–50.7 | 43.6–50.7 | +0.00 |
| Summit skipped | 1.0359 | strong | 75.4–85.7 | 75.7–90.0 | +2.31 |

## 4. Window-only mods

A window mod multiplies the current `w(r)` by 1.10 / 1.20 / 1.30 (it does not change `r` or `V = r**kappa`). Gains are versus the no-mod new model for the same profile. Also shown: a flat add of +10/20/30% of the **default** zone (`w(r) + x·w0`).

### Multiplicative +X% of w(r) — win-rate gain

| cell | profile | no mod | +10% | gain | +20% | gain | +30% | gain |
|------|---------|-------:|-----:|-----:|-----:|-----:|-----:|-----:|
| Touge boss at target | weak | 6.5–23.9 | 12.9–31.4 | +6.93 | 20.9–37.4 | +13.93 | 29.7–44.4 | +21.87 |
| Touge boss at target | average | 63.4–67.8 | 65.3–75.2 | +4.68 | 70.6–80.0 | +9.74 | 71.8–84.8 | +12.73 |
| Touge boss at target | strong | 81.7–95.0 | 84.5–95.6 | +1.69 | 84.6–96.0 | +1.95 | 84.6–96.6 | +2.25 |
| Wangan boss at target | weak | 6.9–22.5 | 13.8–30.7 | +7.56 | 22.1–37.6 | +15.20 | 31.4–44.2 | +23.15 |
| Wangan boss at target | average | 62.0–66.8 | 64.3–75.0 | +5.29 | 69.6–80.0 | +10.45 | 71.2–83.5 | +13.00 |
| Wangan boss at target | strong | 81.4–94.5 | 86.2–94.8 | +2.61 | 86.4–95.9 | +3.20 | 86.4–96.6 | +3.56 |
| Street boss at target | weak | 6.5–22.3 | 12.6–29.9 | +6.86 | 20.9–36.3 | +14.24 | 28.8–42.4 | +21.21 |
| Street boss at target | average | 61.4–65.1 | 63.3–73.1 | +4.95 | 68.4–78.4 | +10.15 | 70.0–82.7 | +13.06 |
| Street boss at target | strong | 79.5–94.0 | 84.2–94.5 | +2.64 | 84.4–95.4 | +3.16 | 84.4–96.3 | +3.62 |
| Touge mature #2 skipped | weak | 1.0–11.5 | 3.0–16.8 | +3.63 | 6.3–22.3 | +8.05 | 10.9–27.1 | +12.77 |
| Touge mature #2 skipped | average | 41.8–51.4 | 53.5–57.3 | +8.80 | 58.1–65.5 | +15.17 | 64.0–71.2 | +21.01 |
| Touge mature #2 skipped | strong | 76.0–91.1 | 81.0–92.5 | +3.18 | 81.7–93.3 | +3.93 | 81.7–94.1 | +4.34 |
| Wangan mature #2 skipped | weak | 1.2–10.4 | 3.2–15.4 | +3.47 | 6.6–20.9 | +7.89 | 11.7–25.6 | +12.76 |
| Wangan mature #2 skipped | average | 43.9–52.1 | 53.4–57.6 | +7.51 | 56.6–64.3 | +12.46 | 63.1–70.8 | +18.95 |
| Wangan mature #2 skipped | strong | 76.1–90.5 | 80.7–92.2 | +3.12 | 81.4–92.6 | +3.71 | 81.4–93.2 | +4.03 |
| Street mature #2 skipped | weak | 1.0–10.5 | 2.8–15.1 | +3.20 | 6.3–20.7 | +7.76 | 10.6–25.3 | +12.19 |
| Street mature #2 skipped | average | 42.8–49.6 | 52.5–55.9 | +8.01 | 57.1–62.3 | +13.50 | 62.2–69.5 | +19.67 |
| Street mature #2 skipped | strong | 74.0–89.6 | 78.8–91.4 | +3.26 | 79.5–92.0 | +3.95 | 79.5–92.7 | +4.28 |

### Flat add +X% of w0 — win-rate gain (same cells)

| cell | profile | no mod | +0.10 w0 | gain | +0.20 w0 | gain | +0.30 w0 | gain |
|------|---------|-------:|---------:|-----:|---------:|-----:|---------:|-----:|
| Touge boss at target | weak | 6.5–23.9 | 12.9–31.4 | +6.93 | 20.9–37.4 | +13.93 | 29.7–44.4 | +21.87 |
| Touge boss at target | average | 63.4–67.8 | 65.3–75.2 | +4.68 | 70.6–80.0 | +9.74 | 71.8–84.8 | +12.73 |
| Touge boss at target | strong | 81.7–95.0 | 84.5–95.6 | +1.69 | 84.6–96.0 | +1.95 | 84.6–96.6 | +2.25 |
| Wangan boss at target | weak | 6.9–22.5 | 13.8–30.7 | +7.56 | 22.1–37.6 | +15.20 | 31.4–44.2 | +23.15 |
| Wangan boss at target | average | 62.0–66.8 | 64.3–75.0 | +5.29 | 69.6–80.0 | +10.45 | 71.2–83.5 | +13.00 |
| Wangan boss at target | strong | 81.4–94.5 | 86.2–94.8 | +2.61 | 86.4–95.9 | +3.20 | 86.4–96.6 | +3.56 |
| Street boss at target | weak | 6.5–22.3 | 12.6–29.9 | +6.86 | 20.9–36.3 | +14.24 | 28.8–42.4 | +21.21 |
| Street boss at target | average | 61.4–65.1 | 63.3–73.1 | +4.95 | 68.4–78.4 | +10.15 | 70.0–82.7 | +13.06 |
| Street boss at target | strong | 79.5–94.0 | 84.2–94.5 | +2.64 | 84.4–95.4 | +3.16 | 84.4–96.3 | +3.62 |
| Touge mature #2 skipped | weak | 1.0–11.5 | 3.6–18.1 | +4.57 | 7.3–25.2 | +9.96 | 13.9–31.4 | +16.40 |
| Touge mature #2 skipped | average | 41.8–51.4 | 54.7–58.3 | +9.89 | 61.8–67.8 | +18.20 | 64.0–74.5 | +22.66 |
| Touge mature #2 skipped | strong | 76.0–91.1 | 81.5–92.5 | +3.45 | 81.7–94.1 | +4.34 | 81.7–94.5 | +4.53 |
| Wangan mature #2 skipped | weak | 1.2–10.4 | 3.7–16.7 | +4.33 | 8.1–23.8 | +10.05 | 14.9–30.7 | +16.96 |
| Wangan mature #2 skipped | average | 43.9–52.1 | 55.3–58.6 | +8.96 | 60.6–66.8 | +15.69 | 63.2–73.7 | +20.41 |
| Wangan mature #2 skipped | strong | 76.1–90.5 | 81.2–92.2 | +3.40 | 81.4–93.2 | +4.03 | 81.4–93.9 | +4.34 |
| Street mature #2 skipped | weak | 1.0–10.5 | 3.0–16.4 | +3.98 | 7.6–23.6 | +9.88 | 13.8–29.9 | +16.10 |
| Street mature #2 skipped | average | 42.8–49.6 | 54.4–56.8 | +9.38 | 60.0–65.1 | +16.30 | 62.3–71.8 | +20.81 |
| Street mature #2 skipped | strong | 74.0–89.6 | 79.3–91.5 | +3.60 | 79.5–92.7 | +4.28 | 79.5–93.5 | +4.65 |

### Stat-point equivalence (average player, multiplicative mods)

A flat stat mod raises `r` (and therefore both `V = r**kappa` and `w(r)`, until the zone plateaus at r = 1.05). Window mods raise only the zone. Equivalence is the `r'` whose new-model average mid win rate matches the window-mod mid, searched first inside the 105% cap (`r ≤ 1.05`) and then, if needed, above it.

| cell | r0 | mod | mid WR | r' inside cap? | r' | Δr | ΔSP at R1 Touge B | ΔSP at R3 Wangan B |
|------|---:|-----|-------:|:---------------|---:|---:|------------------:|-------------------:|
| Touge boss at target | 1.05 | +10% w(r) | 70.26 | no | 1.0707 | +0.0207 | +6.8 | +20.5 |
| Touge boss at target | 1.05 | +20% w(r) | 75.32 | no | 1.0945 | +0.0445 | +14.7 | +43.9 |
| Touge boss at target | 1.05 | +30% w(r) | 78.31 | no | 1.1024 | +0.0524 | +17.3 | +51.8 |
| Wangan boss at target | 1.05 | +10% w(r) | 69.67 | no | 1.0714 | +0.0214 | +7.1 | +21.2 |
| Wangan boss at target | 1.05 | +20% w(r) | 74.84 | no | 1.0943 | +0.0443 | +14.6 | +43.7 |
| Wangan boss at target | 1.05 | +30% w(r) | 77.39 | no | 1.1010 | +0.0510 | +16.8 | +50.4 |
| Street boss at target | 1.05 | +10% w(r) | 68.20 | no | 1.0714 | +0.0214 | +7.1 | +21.2 |
| Street boss at target | 1.05 | +20% w(r) | 73.40 | no | 1.0943 | +0.0443 | +14.6 | +43.7 |
| Street boss at target | 1.05 | +30% w(r) | 76.31 | no | 1.1010 | +0.0510 | +16.8 | +50.4 |
| Touge mature #2 skipped | 1.0355 | +10% w(r) | 55.39 | yes | 1.0422 | +0.0067 | +2.1 | +6.3 |
| Touge mature #2 skipped | 1.0355 | +20% w(r) | 61.76 | yes | 1.0479 | +0.0124 | +3.9 | +11.7 |
| Touge mature #2 skipped | 1.0355 | +30% w(r) | 67.60 | no | 1.0618 | +0.0263 | +8.3 | +24.9 |
| Wangan mature #2 skipped | 1.0355 | +10% w(r) | 55.51 | yes | 1.0419 | +0.0064 | +2.0 | +6.0 |
| Wangan mature #2 skipped | 1.0355 | +20% w(r) | 60.46 | yes | 1.0479 | +0.0124 | +3.9 | +11.7 |
| Wangan mature #2 skipped | 1.0355 | +30% w(r) | 66.95 | no | 1.0618 | +0.0263 | +8.3 | +24.9 |
| Street mature #2 skipped | 1.0355 | +10% w(r) | 54.23 | yes | 1.0419 | +0.0064 | +2.0 | +6.0 |
| Street mature #2 skipped | 1.0355 | +20% w(r) | 59.71 | yes | 1.0474 | +0.0119 | +3.8 | +11.2 |
| Street mature #2 skipped | 1.0355 | +30% w(r) | 65.89 | no | 1.0618 | +0.0263 | +8.3 | +24.9 |

ΔSP = Δr × opponent budget. Representative budgets: mature #2 R1 Touge 315.8 / R3 Wangan 944.9; boss R1 Touge 330.0 / R3 Wangan 987.5.

## 5. Cap-dodge risk and recommended limits

The 105% cap is the real dodge. Window mods do not spend SP or the 25% mod budget. At r=1.05 the zone is already the default, so a +X% mod pushes E[s] above 0.6 and raises win rate while a legal stat mod cannot raise r further. Across the three boss-at-target districts, an average player gains about 5.0 / 10.1 / 12.9 mid-WR points from +10/20/30% of w(r) — enough to turn a ~64% mid into the mid-70s. Street boss +10% has no match inside the cap; the uncapped equivalent is r'=1.0714 (Δr=+0.0214, about 7.1 SP on R1 Touge's budget or 21.2 SP on R3 Wangan's).

The 80% SP cap is not dodged. At r=0.80, V=r**kappa still dominates: the pooled average mid stays 0.00 with no mod, 0.00 / 0.01 / 0.04 with +10/20/30% of w(r), and only 0.57 with a flat +0.30 w0. Window mods cannot replace stats when the player is that far under budget.

At mature #2 skipped (r=1.0355, 0.0145 of r still inside the 105% cap) window mods compete with legal stats and sit on the steep part of the win-rate curve. Across the three districts the average +10/20/30% mid-WR gains are about 8.1 / 13.7 / 19.9 points. +10% and +20% can be matched by a legal stat bump (Street +10% Δr=+0.0064, +20% Δr=+0.0119; a few SP at R1 and about 6–12 at R3). Street mature #2 +30% cannot be matched inside the cap (search stopped at r=1.05, mid still short); the uncapped equivalent is r'=1.0618 (Δr=+0.0263).

Recommended limit (from these runs, still a design choice): cap **total** zone width at **1.15 × w0** (920 ms if w0 stays 800). That allows at most a +15% mod at boss at target, which blocks the +20/+30% cap dodge that is worth ~10–13 mid-WR points there. When the player is behind, w(r) is well below w0 (0.85× at mature #2 skipped, 0.33× at r=0.80), so a +30% of current w(r) still sits under the 1.15 w0 ceiling and remains available as a catch-up tool — useful at the skipped wall, not a substitute for the 80% SP floor. A slot cost alone is not enough: at the 105% cap a window slot has no legal stat alternative, so its opportunity cost is zero unless the width cap (or a rule that window mods spend a fraction of the 25% mod budget) is also in place. A milder alternative is 1.20 × w0 if +15% feels too tight in playtest; I would not leave width uncapped.

| r | meaning | no-mod mid (avg, pooled) | +10% w(r) | +20% | +30% | +0.30 w0 flat |
|--:|---------|-------------------------:|----------:|-----:|-----:|--------------:|
| 0.80 | SP cap / no mods at a 1.05 reference | 0.00 | 0.00 | 0.01 | 0.04 | 0.57 |
| 1.00 | between caps | 9.31 | 13.73 | 19.18 | 25.21 | 38.98 |
| 1.05 | 105% mod cap / boss at target | 64.53 | 69.58 | 74.59 | 77.26 | 77.26 |

## Surprises and notes

- Average-player new-model bands sit inside the official 0.6 band ±2 on 8/8 named cells. They should match the current 0.6·W model almost exactly, because E[s] was calibrated to that value; leftover difference is rounding only.
- At Street mature #2 skipped (r=1.0355, w/w0=0.8548), the strong player's qhat is 0.7661 vs the linear 0.7258, mid WR 81.80 vs 79.16. The weak player's qhat is 0.3503 vs 0.3629. A tight visible zone punishes imprecision more, but a precise player still hits it — the hidden linear window flattened that difference.
- At r=0.80 (the 80% SP cap with no mods) the effect is larger: the same tight zone (w/w0=0.3276) gives the strong placeholder E[s]=0.4581 against a linear 0.8·W(0.80)=0.3280.
- q_read was held at 0.6. The official winrate table's q=0.8 column is not the right comparison here; that column also uses the 0.8 read bank and sits in the high 90s at these cells.
- The QTE does not depend on mid-race progress in this model: w is a function of the race's fixed stat ratio r only.
- Recommended total-width cap: 1.15×w0. At r=1.05, w is already w0, so +20% and +30% would be clipped; at r=1.0355, w/w0=0.8548, and even +30% of w(r) is 1.1113×w0, still under 1.15.

## How to reproduce

```
cd /workspace/barry-drafts/qte-v1 && python3 run.py
```

Requires numpy and the existing count banks under `barry-drafts/final-v1` and `barry-drafts/lines-v1`. Does not import or edit the midnight-apex working tree except to read `sim/config/winrate_n4000.json` for the official bands.

