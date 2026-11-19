"""econ-v1 progression (3-round ladder, Variant C, USD) reproduction tests.

Pinned numbers are the econ-v1 live-tracks recalibration, approved and made live in commit 6d3641f (live stand-in tracks, bosses on
the hardest track per district, Austin 2026-11-14), money in USD. Re-pinned 2026-11-19 for the 0.80 random AI QTE, the boss
retune and the EN-heavy Street boss (Austin approved; win-rate table v2). Constants are unchanged; walk outputs moved."""
import pytest
import sys
sys.path.insert(0, ".")
from velocity_shift import equations as E, progression as P


def test_curves_and_caps():
    assert abs(E.sp_at_level(12) - E.SP_START * 1.1) < 1e-9          # SP(L) = 240 x 1.1^(L/12) (whole points / 10)
    assert abs(E.xp_to_next(0) - 100.0) < 1e-12 and abs(E.xp_to_next(10) / E.xp_to_next(9) - 1.08) < 1e-12
    assert [round(c, 1) for c in E.C_ROUND] == [353.1, 404.3, 462.8]
    assert tuple(int(round(E.level_for_sp(c * E.SP_CAP_FRACTION / E.MOD_CAP_FRACTION))) for c in E.C_ROUND) == E.CAP_LEVEL
    assert tuple(l for _, l in P.finale_caps()) == E.FINALE_CAP_LEVEL == (64, 79, 94, 115)


def test_grind_taper():
    assert E.grind_xp(10, 12) < E.grind_xp(5, 12)                      # tapers toward the cap
    assert abs(E.grind_xp(12, 12) - E.GRIND_FRAC * E.GRIND_TAPER_FLOOR * E.xp_to_next(12)) < 1e-9


def test_ladder_targets_at_cap():
    for x in P.ladder():
        rnd = x["rnd"] - 1
        assert abs(E.C_ROUND[rnd] / x["B"] - x["target_r"]) < 1e-12
    assert {d: E.LADDER_TARGET_R[d][6] for d in E.LADDER_TARGET_R} == E.BOSS_TARGET_R == {"street": 1.046, "wangan": 1.040, "touge": 1.050}
    for d, lad in E.LADDER_TARGET_R.items():
        assert all(a >= b for a, b in zip(lad, lad[1:])), d                         # ladders never step up


def test_hardest_track_boss_win_rates():
    """At-cap bosses on the hardest live track (table v2, N=2000/style point checks at the boss r; Austin 2026-11-19)."""
    got = {(x["rnd"], x["district"]): x for x in P.at_cap_table() if x["rung"] == "boss" or x["rnd"] == "F"}
    def row(key):
        return tuple(got[key]["wr"][pr]["hard"] for pr in P.PROFILES)
    assert row((1, "Street")) == (31.2, 72.0, 62.3, 93.9)                             # S1 Shibuya, r 1.046, EN-heavy boss
    assert row((2, "Wangan")) == (40.9, 64.8, 80.9, 92.5)                             # W3 C1 Outer, r 1.040
    assert row((3, "Touge")) == (32.4, 70.0, 63.6, 91.9)                              # T3 Usui, r 1.050
    fin = [x for x in P.at_cap_table() if x["rnd"] == "F"]
    assert [tuple(x["wr"][pr]["hard"] for pr in ("c6060", "c8080")) for x in fin] == [(60.9, 98.6), (61.4, 97.5), (58.1, 98.3), (60.9, 98.6)]
    for d in E.BOSS_TARGET_R:
        assert P.boss_check(E.BOSS_TARGET_R[d], d)["ok"], d
    assert E.BOSS_BAND_8080 == (90.0, 95.0) and E.BOSS_FLOOR_6060 == 30.0


@pytest.mark.xfail(strict=True, reason="Finale r (FINALE_TARGET_R) is still tuned for the old perfect AI; with the 0.80 random "
                   "AI QTE every billed finale is out of band (80/80 97.5-98.6). Retune not approved yet; draft in "
                   "unapproved/barry/ai-heat-qte-v1/ (Austin 2026-11-19).")
def test_finale_in_band():
    for (_, d, _), r in zip(E.FINALE, E.FINALE_TARGET_R):
        assert P.boss_check(r, d, boss=False)["ok"], d


def test_walks_reproduce_eval_final_c():
    mixed = P.run("mixed")
    assert [(w["wall"], w["wall_grind"], w["post_wall_to_cap"], w["total_grind"]) for w in mixed] == [("mat2", 3, 10, 13), ("mat1", 2, 11, 13), ("mat1", 3, 9, 12)]
    assert [w["L"] for w in mixed] == [12, 29, 46] and all(w["reached_cap"] for w in mixed)
    # mods-v1 (Austin 2026-11-14): the walk buys mods just in time, so it ends each round with the cash left after the shop
    assert [round(w["money"], 2) for w in mixed] == [5050.0, 13232.5, 11702.5] and mixed[0]["debt"] == 0.0
    assert mixed[-1]["mods_spent"] == 66580.0
    hard = P.run("hard")
    assert [w["total_grind"] for w in hard] == [14, 14, 12] and [w["L"] for w in hard] == [12, 29, 46]   # was 13/15/18 (perfect AI)
    assert [(w["wall_grind"], w["post_wall_to_cap"]) for w in hard] == [(1, 13), (6, 8), (2, 10)]
    story = P.run("story")
    assert [w["L"] for w in story] == [7, 26, 43] and story[0]["debt"] == 3000.0     # story-only R1 leaves $3,000 debt
    # xp-carry-v1 fix C (Austin 2026-11-14): leftover XP carries over, so story-only enters R2 at L7 and R3 at L26
    assert [w["rows"][0]["arrive_L"] for w in story] == [0, 7, 26]
    worst = [min(P.hard_win(r["wr"]["c8080"]) for r in w["rows"]) for w in story]
    assert worst == [40.6, 58.4, 48.0]          # was 53.0 / 54.4 / 50.5; criterion 3 (>= 50) now fails R1/R3: test_story_criterion_3
    # Austin 2026-11-14 campaign story-XP cut (STORY_XP_MULT): 80/80 story-only meets each boss one level lower
    boss = [(w["rows"][-1]["arrive_L"], P.hard_win(w["rows"][-1]["wr"]["c8080"])) for w in story]
    assert boss == [(6, 40.6), (23, 58.4), (41, 48.0)]
    assert story[0]["rows"][0]["equipped"] == ["stock"] * 4 and story[0]["rows"][0]["cash_pre"] == 0.0   # kid1 runs stock
    assert story[0]["rows"][1]["wr"]["c8080"]["district"] == 98.6                       # kid2 at 88.9 % fill
    assert [round(w["money"], 2) for w in story] == [5900.0, 13940.0, 26700.0] and story[-1]["mods_spent"] == 27300.0
    # skill-points-v1 (Austin 2026-11-14): whole points, 25-50 % band, 20 % retune budget; R2 arrives off the Wangan tune
    assert [round(w["rows"][-1]["wr"]["c6060"]["hard"], 1) for w in hard] == [31.2, 41.5, 31.2]
    assert [w["build"] for w in mixed] == [(1320, 660, 660), (792, 756, 1474), (1556, 865, 1037)]
    assert [w["rows"][0]["pow_share"] for w in mixed] == [50.0, 30.0, 45.0]           # entry POW share R1 / R2 / R3


@pytest.mark.xfail(strict=True, reason="Criterion 3 (80/80 story-only >= 50 % on every rung) breaks under the 0.80 random AI "
                   "QTE + EN-heavy Street boss: the story-only player meets the R1 boss at 40.6 % and the R3 boss at 48.0 %. "
                   "Story XP retune not approved; draft in unapproved/barry/ai-heat-qte-v1/ (Austin 2026-11-19).")
def test_story_criterion_3():
    story = P.run("story")
    assert min(min(P.hard_win(r["wr"]["c8080"]) for r in w["rows"]) for w in story) >= 50.0


def test_story_xp_mult_campaign_only():
    assert E.STORY_XP_MULT[0] == (0.90,) * 7
    assert E.STORY_XP_MULT[1] == (1.0, 1.0, 1.0, 1.0, 1.0, 0.60, 1.5) and E.STORY_XP_MULT[2] == (1.0, 1.0, 1.0, 1.0, 1.0, 0.80, 1.0)
    assert E.ARC_STORY_FILL == 0.80                                                  # finale pacing unchanged (Austin 2026-11-14)
    a = E.story_xp(0, 2, 0, 12) / (E.STORY_FILL[0] * E.STORY_W[2] / sum(E.STORY_W) * sum(E.xp_to_next(L) for L in range(0, 12)))
    assert abs(a - 0.90) < 1e-12


def test_leftover_xp_carries_over_with_catchup():
    # xp-carry-v1 fix C (Austin 2026-11-14): entering at the previous cap pays exactly the pre-carry XP; entering below
    # it adds CATCHUP_XP_FRAC x CATCHUP_XP_SHARE[rung] of the shortfall to that cap (kid1 / kid2 / mat1 only)
    assert E.CATCHUP_XP_FRAC == 0.75 and E.CATCHUP_XP_SHARE == (0.40, 0.40, 0.20, 0.0, 0.0, 0.0, 0.0)
    cap1, cap2 = E.CAP_LEVEL[0], E.CAP_LEVEL[1]
    for j in range(7):
        at_cap = E.STORY_XP_MULT[1][j] * E.STORY_FILL[1] * E.STORY_W[j] / sum(E.STORY_W) * sum(E.xp_to_next(L) for L in range(cap1, cap2))
        assert abs(E.story_xp(1, j, cap1, cap2) - at_cap) < 1e-9
        short = sum(E.xp_to_next(L) for L in range(7, cap1))
        assert abs(E.story_xp(1, j, 7, cap2) - at_cap - 0.75 * E.CATCHUP_XP_SHARE[j] * short) < 1e-9
    mixed = P.run("mixed")
    assert [w["rows"][0]["arrive_L"] for w in mixed] == [0, 12, 29]                  # grinders reach every cap: no change


def test_money_and_shop():
    assert E.purse(0, "kid") == 1000.0 and E.purse(2, "boss") == 10800.0 and abs(E.purse(2, "kid", grind=True) - 742.5) < 1e-9
    assert E.mod_price("MOD_R1_POW_MK1") == 150.0 and E.mod_price("MOD_R3_POW_MK3", aero=True) == 14000.0
    assert E.mod_price("MOD_R3_HAN_MK3_AERO") == 14000.0
    assert E.mod_price("MOD_R2_EN_MK3", wholesale=True) == 5000.0 * 0.8
    assert E.mod_price("MOD_ARC_EN_MYTH4", wholesale=True) == 8000.0                  # no wholesale on ARC
    assert [E.wholesale_active(n) for n in range(4)] == [False, True, True, False]
    assert P.t4_package_price() == 3 * 8000.0 + 14000.0 and "MOD_ARC_POW_MYTH4" in E.MOD_PRICE_STANDIN


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
    assert f4["opponent"] == "Sabine" and f4["district"] == "touge" and f4["B"] == 741.9 and f4["cap"] == 115
    assert abs(arc[0]["xp"] - 18591.3) < 0.1                                         # P1 share of the L46-L64 gap
    assert [a["B"] for a in arc if not a["billed"]] == [382.78, 412.29, 480.89, 464.83, 441.61, 555.28, 497.48, 625.54, 560.43, 713.17]


def test_order_is_fixed():
    assert P.check_order(E.DEFAULT_CREW_ORDER) == E.DEFAULT_CREW_ORDER
    assert E.DEFAULT_CREW_ORDER == {1: ("Street",), 2: ("Wangan",), 3: ("Touge",)}
    for bad in ({1: ("Touge",), 2: ("Wangan",), 3: ("Street",)}, {1: ("Street", "Wangan"), 2: ("Wangan",), 3: ("Touge",)}):
        try:
            P.check_order(bad)
        except ValueError:
            continue
        assert False, f"order {bad} must be rejected"
