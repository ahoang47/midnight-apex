"""Visible timing-QTE model for the qte-v1 draft (2026-11-10).

No repo edits. Skill parameters are PLACEHOLDERS until playtest data exists.

Model (placeholder)
-------------------
- One timing press: the marker's error about the zone centre is
  e ~ Normal(0, sigma), unbiased (no systematic early/late bias).
- Zone width is w, half-width a = w/2. The current Godot default zone
  is QTE_TIMING_WINDOW_BASE_MS = 800 ms; that value is only a
  presentation unit. All design work is in units of the default zone.
- Hit quality falls off linearly from 1 at the centre to 0 at the
  zone edge, and is 0 outside:

      s(e, w) = max(0, 1 - |e| / (w/2))

- The turn's raw QTE score is the mean of N independent presses.
  N does not change E[s]; this draft uses E[s] as a constant q_time
  (the same methodology as the winrate_n4000 oracle, which used a
  fixed q_time, not per-turn draws). N and mash speed are unused
  here and remain open.

Expected score (closed form)
----------------------------
With a = w/2 and phi, Phi the N(0, sigma) density and CDF:

    E[s] = erf(a / (sigma * sqrt(2)))
         - (sigma / a) * sqrt(2/pi) * (1 - exp(-a^2 / (2 sigma^2)))

sigma_average is chosen so E[s] at the default zone equals 0.6
(the oracle's q_time). sigma_weak and sigma_strong target 0.4 and 0.8
at that same default zone.
"""
from __future__ import annotations

import math

# Presentation unit only (Godot guide QTE_TIMING_WINDOW_BASE_MS). Placeholder.
W0_MS = 800.0
A0_MS = W0_MS / 2.0  # 400 ms

# Current hidden window (equations.py KNOT_WINDOW_105). Flat outside the ends.
KNOT_WINDOW_105 = (
    (0.80, 0.41),
    (0.85, 0.41),
    (0.90, 0.41),
    (0.95, 0.43),
    (1.00, 0.68),
    (1.05, 1.00),
)

# Placeholder skill targets at the default zone. Not playtest data.
SKILL_TARGETS = {"weak": 0.4, "average": 0.6, "strong": 0.8}


def knot_window(r: float) -> float:
    """Piecewise-linear KNOT_WINDOW_105, flat below 0.80 and capped at 1 above 1.05."""
    knots = KNOT_WINDOW_105
    if r <= knots[0][0]:
        return knots[0][1]
    if r >= knots[-1][0]:
        return min(1.0, knots[-1][1])
    for (x0, y0), (x1, y1) in zip(knots, knots[1:]):
        if x0 <= r <= x1:
            if x1 == x0:
                return y0
            return y0 + (y1 - y0) * (r - x0) / (x1 - x0)
    return knots[-1][1]


def expected_score(half_width: float, sigma: float) -> float:
    """E[max(0, 1 - |e| / a)] for e ~ N(0, sigma), a = half_width."""
    a = float(half_width)
    s = float(sigma)
    if a <= 0.0:
        return 0.0
    if s <= 0.0:
        return 1.0
    z = a / s
    return math.erf(z / math.sqrt(2.0)) - (s / a) * math.sqrt(2.0 / math.pi) * (
        1.0 - math.exp(-0.5 * z * z)
    )


def expected_score_from_width(width_over_w0: float, sigma_over_a0: float) -> float:
    """E[s] when width is a fraction of the default zone and sigma is in units of a0."""
    return expected_score(width_over_w0, sigma_over_a0)


def _solve_monotone(fn, target: float, lo: float, hi: float, rising: bool, n: int = 80) -> float:
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        val = fn(mid)
        if rising:
            if val < target:
                lo = mid
            else:
                hi = mid
        else:
            if val > target:
                lo = mid
            else:
                hi = mid
    return 0.5 * (lo + hi)


def sigma_for_target(target: float, half_width: float = 1.0) -> float:
    """sigma (same units as half_width) such that E[s] = target at that zone."""
    if not 0.0 < target < 1.0:
        raise ValueError(f"target must be in (0, 1), got {target}")
    return _solve_monotone(
        lambda sig: expected_score(half_width, sig),
        target,
        1e-8,
        50.0,
        rising=False,
    )


def half_width_for_target(target: float, sigma: float) -> float:
    """half-width (same units as sigma) such that E[s] = target."""
    if target <= 0.0:
        return 0.0
    if target >= 1.0 - 1e-15:
        return float("inf")
    return _solve_monotone(
        lambda a: expected_score(a, sigma),
        target,
        1e-10,
        50.0 * max(sigma, 1e-8),
        rising=True,
    )


def fit_sigmas(targets: dict[str, float] | None = None) -> dict[str, float]:
    """sigma / a0 for each named profile at the default zone (a = a0 = 1)."""
    targets = targets or SKILL_TARGETS
    out = {}
    for name, t in targets.items():
        sig = sigma_for_target(t, 1.0)
        out[name] = {
            "target_E_at_default_zone": t,
            "sigma_over_a0": sig,
            "sigma_ms": sig * A0_MS,
            "achieved_E_at_default_zone": expected_score(1.0, sig),
            "placeholder": True,
        }
    return out


def width_for_average_at_r(r: float, sigma_avg_over_a0: float) -> dict:
    """Zone width (fraction of default) so the average player's E[s] = 0.6 * W(r)."""
    W = knot_window(r)
    target = 0.6 * W
    a = half_width_for_target(target, sigma_avg_over_a0)  # in units of a0
    w_over_w0 = a  # a/a0 = (w/2)/(w0/2) = w/w0
    return {
        "r": r,
        "knot_window": W,
        "target_E": target,
        "w_over_w0": w_over_w0,
        "w_ms": w_over_w0 * W0_MS,
        "achieved_E_average": expected_score(w_over_w0, sigma_avg_over_a0),
    }


def scores_at_width(w_over_w0: float, sigmas_over_a0: dict[str, float]) -> dict[str, float]:
    return {name: expected_score(w_over_w0, sig) for name, sig in sigmas_over_a0.items()}
