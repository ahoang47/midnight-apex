from velocity_shift.cars import ARCHETYPES, progress, stat_pct, build_stats

# All 6 archetypes must be defined
ALL_ARCHETYPES = ["Bruiser", "Endurance", "Swift", "AR P", "AR E", "AR H"]


def test_archetypes_defined():
    for name in ALL_ARCHETYPES:
        assert name in ARCHETYPES, f"Missing archetype: {name}"
        t = ARCHETYPES[name]
        for k in ("pow", "en", "han"):
            assert k in t, f"{name} missing key {k}"
        total = t["pow"] + t["en"] + t["han"]
        assert abs(total - 100) < 0.01, f"{name} target sum {total} != 100"


def test_progress_bounds():
    assert progress(1) == 0.0, "Level 1 should have 0 progress"
    assert progress(100) == 1.0, "Level 100 should have 1.0 progress"
    for lv in range(1, 101):
        p = progress(lv)
        assert 0.0 <= p <= 1.0, f"Progress {p} out of bounds at level {lv}"
    prev = -1.0
    for lv in range(1, 101):
        cur = progress(lv)
        assert cur >= prev, f"Progress regressed at level {lv}"
        prev = cur


def test_stat_pct_sums_to_100():
    for arch in ALL_ARCHETYPES:
        for lv in (1, 25, 50, 75, 100):
            sp, se, sh = stat_pct(arch, lv)
            total = sp + se + sh
            assert abs(total - 100) < 0.01, (
                f"{arch} L{lv}: {sp:.2f}+{se:.2f}+{sh:.2f}={total:.2f} != 100"
            )


def test_stat_pct_start():
    """At level 1 all archetypes are ~33/33/33."""
    for arch in ALL_ARCHETYPES:
        sp, se, sh = stat_pct(arch, 1)
        for val in (sp, se, sh):
            assert abs(val - 100 / 3) < 0.01, (
                f"{arch} L1: {sp:.2f}/{se:.2f}/{sh:.2f} not at 33/33/33"
            )


def test_stat_pct_end():
    """At level 100 each archetype hits its target."""
    for arch in ALL_ARCHETYPES:
        sp, se, sh = stat_pct(arch, 100)
        t = ARCHETYPES[arch]
        assert abs(sp - t["pow"]) < 0.01, f"{arch} L100 POW expected {t['pow']}, got {sp}"
        assert abs(se - t["en"]) < 0.01, f"{arch} L100 EN expected {t['en']}, got {se}"
        assert abs(sh - t["han"]) < 0.01, f"{arch} L100 HAN expected {t['han']}, got {sh}"


def test_stat_pct_monotonic():
    """Each stat moves monotonically from start toward target."""
    for arch in ALL_ARCHETYPES:
        t = ARCHETYPES[arch]
        prev = 100 / 3
        for lv in range(1, 101):
            sp, se, sh = stat_pct(arch, lv)
            for stat_val, target in [(sp, t["pow"]), (se, t["en"]), (sh, t["han"])]:
                if target > 100 / 3:
                    assert stat_val >= prev - 0.01, f"{arch} L{lv} {stat_val:.2f} < prev {prev:.2f}"
                elif target < 100 / 3:
                    assert stat_val <= prev + 0.01, f"{arch} L{lv} {stat_val:.2f} > prev {prev:.2f}"


def test_build_stats_same_level_equal_budget():
    """All archetypes at same level should have identical total stat sum."""
    for lv in (1, 10, 25, 50, 75, 100):
        totals = set()
        for arch in ALL_ARCHETYPES:
            p, e, h = build_stats(arch, lv)
            totals.add(round(p + e + h, 6))
        assert len(totals) == 1, (
            f"Level {lv} budgets differ: {totals}"
        )


def test_build_stats_non_negative():
    for arch in ALL_ARCHETYPES:
        for lv in range(1, 101):
            p, e, h = build_stats(arch, lv)
            assert p >= 0 and e >= 0 and h >= 0, (
                f"{arch} L{lv}: negative stats ({p}, {e}, {h})"
            )
