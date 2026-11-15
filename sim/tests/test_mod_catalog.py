"""mods-v1 catalog (Austin 2026-11-14): 4 slots, 39 fixed-stat mods by ID, stock parts, price guards."""
import sys
sys.path.insert(0, ".")
from velocity_shift import equations as E, progression as P


def test_ids_and_fixed_stats():
    assert E.MOD_SLOTS == 4 and E.MOD_STOCK_PART_POINTS * E.MOD_SLOTS == 600
    assert len(E.MOD_CATALOG) == 39
    for mid, m in E.MOD_CATALOG.items():
        assert mid == f"MOD_{m['group']}_{m['stat']}_{m['mk']}" and m["stat"] in E.MOD_STATS
    assert "MOD_R1_POW_MK1" in E.MOD_CATALOG and "MOD_ARC_EN_MYTH4" in E.MOD_CATALOG
    for g in ("R1", "R2", "R3", "ARC"):                                   # same size for every stat, rising by Mk
        pts = [E.MOD_CATALOG[f"MOD_{g}_POW_{mk}"]["points"] for g2, mk, *_ in E.MOD_SETS if g2 == g]
        assert pts == sorted(pts)


def test_stock_car_and_full_fill():
    g = P.Garage()
    assert abs(g.power(0, 0, "street") - E.stats_at_level(0)) < 1e-9      # SP + stock parts = live stock car at L0
    for g_, mk, pts, _, _, fl in E.MOD_SETS:                               # 4 x Mk points cover the gap at fills_to
        stage = int(g_[1]) - 1 if g_ != "ARC" else 3 + ("MYTH1", "MYTH2", "MYTH3", "MYTH4").index(mk)
        assert E.MOD_SLOTS * pts >= P.mod_gap(fl, stage) - 1e-9, (g_, mk)


def test_price_guards_and_aspire():
    assert E.mod_price("MOD_R1_POW_MK3") <= 1000.0                        # > $1,000 drops 60/60 at the R1 cap under 30 %
    assert E.mod_price("MOD_ARC_POW_MYTH4") == 8000.0                     # $12,000 broke F4
    story = [r for w in P.run("story") for r in w["rows"]]
    cash = {(r["rnd"], r["rung"]): r["cash_pre"] for r in story}
    assert E.MOD_SLOTS * E.mod_price("MOD_R2_POW_MK3") > cash[(2, "oh1")] == 8750.0      # Mk3 set out of reach on sight (xp-carry-v1: was 8470)
    assert E.MOD_SLOTS * E.mod_price("MOD_R3_POW_MK3") > cash[(3, "oh1")] == 20510.0   # xp-carry-v1: was 24230


def test_buyer_one_stat_mods_only():
    out, G, done = P.run_with_garage("mixed")
    assert all(not m.endswith("_AERO") for m in G.owned)                   # the sim buyer never buys aero (<= 1 allowed)
    assert G.spent == 62180.0 and len(G.owned) == 32
