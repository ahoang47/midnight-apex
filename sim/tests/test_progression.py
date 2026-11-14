"""econ-v1 progression (3-round ladder, Variant C, USD) reproduction tests.

Pinned numbers are unapproved/barry/econ-v1 eval_final_C.json and RESULTS.md (Variant C), money x100 to USD."""
import sys
sys.path.insert(0, ".")
from velocity_shift import equations as E, progression as P


def test_curves_and_caps():
    assert abs(E.sp_at_level(12) - E.SP_START * 1.1) < 1e-9          # SP(L) = 240 x 1.1^(L/12)
    assert abs(E.xp_to_next(0) - 100.0) < 1e-12 and abs(E.xp_to_next(10) / E.xp_to_next(9) - 1.08) < 1e-12
    assert [round(c, 1) for c in E.C_ROUND] == [353.1, 404.3, 462.8]
    assert tuple(int(round(E.level_for_sp(c * E.SP_CAP_FRACTION / E.MOD_CAP_FRACTION))) for c in E.C_ROUND) == E.CAP_LEVEL
    assert tuple(l for _, l in P.finale_caps()) == E.FINALE_CAP_LEVEL == (63, 76, 95, 114)


def test_grind_taper():
    assert E.grind_xp(10, 12) < E.grind_xp(5, 12)                      # tapers toward the cap
    assert abs(E.grind_xp(12, 12) - E.GRIND_FRAC * E.GRIND_TAPER_FLOOR * E.xp_to_next(12)) < 1e-9


def test_ladder_targets_at_cap():
    for x in P.ladder():
        rnd = x["rnd"] - 1
        assert abs(E.C_ROUND[rnd] / x["B"] - x["target_r"]) < 1e-12
    assert {d: E.LADDER_TARGET_R[d][6] for d in E.LADDER_TARGET_R} == E.BOSS_TARGET_R == {"street": 1.053, "wangan": 1.040, "touge": 1.066}


def test_variant_c_boss_win_rates():
    """At-cap bosses reproduce RESULTS.md Variant C (exact grid points)."""
    got = {x["district"]: x["wr"] for x in P.at_cap_table() if x["rung"] == "boss"}
    assert got["Street"]["c6060"] == {"district": 38.8, "S1_CW": 30.9, "S1_CCW": 31.2}
    assert got["Street"]["c8080"] == {"district": 96.3, "S1_CW": 93.9, "S1_CCW": 95.4}
    assert got["Wangan"]["c6060"]["district"] == 36.4 and got["Wangan"]["c8080"]["district"] == 91.4
    assert got["Touge"]["c6060"] == {"district": 37.4, "uphill": 33.7, "downhill": 41.0}
    assert got["Touge"]["c8080"] == {"district": 90.8, "uphill": 89.6, "downhill": 91.9}
    assert (got["Street"]["c6080"]["district"], got["Wangan"]["c8060"]["district"], got["Touge"]["c8060"]["uphill"]) == (76.5, 73.4, 66.4)


def test_walks_reproduce_eval_final_c():
    mixed = P.run("mixed")
    assert [(w["wall"], w["wall_grind"], w["post_wall_to_cap"], w["total_grind"]) for w in mixed] == [("mat1", 3, 9, 12), ("mat1", 3, 9, 12), ("mat1", 4, 8, 12)]
    assert [w["L"] for w in mixed] == [12, 29, 46] and all(w["reached_cap"] for w in mixed)
    assert [round(w["money"], 2) for w in mixed] == [10600.0, 41190.0, 77100.0] and mixed[0]["debt"] == 0.0
    hard = P.run("hard")
    assert [w["total_grind"] for w in hard] == [13, 16, 18] and [w["L"] for w in hard] == [12, 29, 46]
    story = P.run("story")
    assert [w["L"] for w in story] == [8, 26, 43] and story[0]["debt"] == 3000.0     # story-only R1 leaves $3,000 debt
    worst = [min(P.hard_win(r["wr"]["c8080"]) for r in w["rows"]) for w in story]
    assert min(worst) >= 50.0                                                        # criterion 3


def test_money_and_shop():
    assert E.purse(0, "kid") == 1000.0 and E.purse(2, "boss") == 10800.0 and abs(E.purse(2, "kid", grind=True) - 742.5) < 1e-9
    assert E.mod_price("T1") == 1600.0 and E.mod_price("T3", aero=True) == 7000.0
    assert E.mod_price("T2", wholesale=True) == 2800.0 * 0.8 and E.mod_price("T4", wholesale=True) == 8000.0   # no wholesale on T4
    assert [E.wholesale_active(n) for n in range(4)] == [False, True, True, False]
    assert P.t4_package_price() == 54000.0 and "T4" in E.MOD_PRICE_STANDIN


def test_betting_fair_odds():
    assert E.bet_net_payout(1000.0, 0.5) == 1000.0 and abs(E.bet_net_payout(2000.0, 0.8) - 500.0) < 1e-9
    assert abs(0.8 * E.bet_net_payout(2000.0, 0.8) - 0.2 * 2000.0) < 1e-9            # EV 0 at true p
    assert not E.bet_allowed(1, 1000.0) and E.bet_allowed(2, 500.0) and E.bet_allowed(2, 2000.0) and not E.bet_allowed(3, 2500.0)
    assert E.BET_ELIGIBLE == "any" and E.BET_COUNT_CAP is None and E.BET_ODDS_CLAMP is False


def test_unlock_markers():
    marks = {x["district"]: x["unlocks"] for x in P.ladder() if x["rung"] == "boss"}
    assert "aero" in marks["Street"][0] and marks["Wangan"] == ["betting unlocks"] and "T4 at P1" in marks["Touge"][0]


def test_finale_arc():
    arc = P.finale_arc()
    assert [a["id"] for a in arc] == ["P1", "P2", "P3", "P4", "F1", "M11", "M12", "F2", "M21", "M22", "F3", "M31", "M32", "F4"]
    assert [a["id"] for a in arc if a["unlock_t4"]] == ["P1"]
    f4 = arc[-1]
    assert f4["opponent"] == "Sabine" and f4["district"] == "touge" and f4["B"] == 741.9 and f4["cap"] == 114
    assert abs(arc[0]["xp"] - 16754.5) < 0.1                                         # finale_arc_recommended.json P1


def test_order_is_fixed():
    assert P.check_order(E.DEFAULT_CREW_ORDER) == E.DEFAULT_CREW_ORDER
    assert E.DEFAULT_CREW_ORDER == {1: ("Street",), 2: ("Wangan",), 3: ("Touge",)}
    for bad in ({1: ("Touge",), 2: ("Wangan",), 3: ("Street",)}, {1: ("Street", "Wangan"), 2: ("Wangan",), 3: ("Touge",)}):
        try:
            P.check_order(bad)
        except ValueError:
            continue
        assert False, f"order {bad} must be rejected"
