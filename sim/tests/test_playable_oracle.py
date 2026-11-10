"""Playable engine (match.py / SimulationRunner) should track winrate_n4000.json."""
from velocity_shift.progression import win_rate
from velocity_shift.equations import AVERAGE_PLAY_Q
from velocity_shift.simulation import simulate_win_rate

# Official district cells (q=0.6) from the 6fc87d5 oracle / progression.
# Tolerance is ±2 points around the published min–max band.
CELLS = [
    ("street", 1.05, "Street boss at target"),
    ("wangan", 1.05, "Wangan boss at target"),
    ("street", 1.0355, "Street mature #2 skipped"),
    ("touge", 1.05, "Touge boss at target"),
]
SEEDS = (20261113, 20261114, 20261115)
LENGTHS = (10, 20, 30)
N_PER_TRACK = 200  # 1000 races per (seed, length); enough for roughly ±2 points


def _batch(district, r, q=AVERAGE_PLAY_Q):
    rates = []
    for L in LENGTHS:
        for sd in SEEDS:
            rates.append(simulate_win_rate(district, r, q, L, sd, n_per_track=N_PER_TRACK))
    return rates


def test_playable_engine_tracks_oracle_street_and_wangan_boss():
    for district, r, label in CELLS[:2]:
        lo, hi = win_rate(r, AVERAGE_PLAY_Q, district)
        rates = _batch(district, r)
        mid = sum(rates) / len(rates)
        overall = (min(rates), max(rates))
        assert overall[0] >= lo - 2.0, f"{label}: low {overall[0]:.1f} < oracle {lo:.1f}-2"
        assert overall[1] <= hi + 2.0, f"{label}: high {overall[1]:.1f} > oracle {hi:.1f}+2"
        # Midpoint of the batch should sit near the published band.
        assert lo - 2.0 <= mid <= hi + 2.0, f"{label}: mid {mid:.1f} vs oracle {lo:.1f}–{hi:.1f}"


def test_playable_engine_tracks_oracle_street_skip_and_touge_boss():
    for district, r, label in CELLS[2:]:
        lo, hi = win_rate(r, AVERAGE_PLAY_Q, district)
        rates = _batch(district, r)
        mid = sum(rates) / len(rates)
        overall = (min(rates), max(rates))
        assert overall[0] >= lo - 2.0, f"{label}: low {overall[0]:.1f} < oracle {lo:.1f}-2"
        assert overall[1] <= hi + 2.0, f"{label}: high {overall[1]:.1f} > oracle {hi:.1f}+2"
        assert lo - 2.0 <= mid <= hi + 2.0, f"{label}: mid {mid:.1f} vs oracle {lo:.1f}–{hi:.1f}"
