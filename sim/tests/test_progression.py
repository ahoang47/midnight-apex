"""Story XP / level progression (grind v8c) reproduction tests."""
import sys
sys.path.insert(0, ".")
from velocity_shift import equations as E, progression as P


def test_curves():
    SP, XC, X = P.curves()
    assert abs(SP[12] - E.SP_START * 1.1) < 1e-6           # SP(L) = 240 · 1.1^(L/12)
    assert abs(X[1] - 100.0) < 1e-9 and X[150] > 19 * X[1]  # leveling gets harder
    assert all(E.sp_per_level(L + 1) > E.sp_per_level(L) for L in range(1, 162))


def test_taper_monotone_within_crew_and_level():
    for L in (1, 50, 150):
        f = [E.grind_payout_fraction(L, j) for j in range(7)]
        assert all(a > b for a, b in zip(f, f[1:]))
    assert E.grind_payout_fraction(150, 3) < E.grind_payout_fraction(10, 3)


def test_v8c_reproduction():
    rows, t = P.run("forced")
    w, fin = P.walls(rows)
    assert [(m, b) for _, m, b in w] == [(7, 6), (7, 6), (7, 6), (8, 9), (7, 7), (7, 7), (9, 10), (8, 8), (8, 8)]
    assert [c for c, _, _ in w] == ["R1 Touge", "R1 Wangan", "R1 Street", "R2 Wangan", "R2 Street", "R2 Touge", "R3 Street", "R3 Touge", "R3 Wangan"]
    assert fin == [4, 6, 4, 6]
    assert t["grind_races"] == 155 and t["levels"] == 162 and t["lost_xp"] == 0
    assert P.pattern(rows).startswith("1T:kkmM7ooB6")


def test_round_opening_by_position():
    R = P.ladder()[0]
    ro = sorted({r["crew"] for r in R if r["ro"]})
    assert ro == ["R2 Wangan", "R3 Street"]


def test_boss_outpays_lieutenants_every_crew():
    rows, _ = P.run("forced")
    for c in {r["crew"] for r in rows if r["crew"] not in ("Prologue", "Finale")}:
        ds = [r for r in rows if r["crew"] == c]
        assert ds[-1]["win_levels"] > max(r["win_levels"] for r in ds[:-1])
        assert min(r["win_levels"] for r in ds[:-1]) >= 0.25 - 1e-6
