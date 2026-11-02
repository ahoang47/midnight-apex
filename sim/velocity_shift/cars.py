from __future__ import annotations

ARCHETYPES: dict[str, dict[str, float]] = {
    # Plain-English names (2026-11-01). Old names: Bruiser, Endurance, Swift,
    # AR E, AR H. AR P was cut (5 archetypes x 15 racer types).
    "Aggressive":             {"pow": 55, "en": 20, "han": 25},
    "Defensive":              {"pow": 20, "en": 55, "han": 25},
    "Precise":                {"pow": 25, "en": 20, "han": 55},
    "Balanced":               {"pow": 30, "en": 40, "han": 30},
    "Adaptive":               {"pow": 30, "en": 30, "han": 40},
}

START_PCT: float = 100.0 / 3.0


def progress(level: int) -> float:
    if level <= 1:
        return 0.0
    return min(1.0, ((level - 1) / 99.0) ** 1.5)


def stat_pct(archetype: str, level: int) -> tuple[float, float, float]:
    t = ARCHETYPES[archetype]
    p = progress(level)
    raw_p = START_PCT + (t["pow"] - START_PCT) * p
    raw_e = START_PCT + (t["en"] - START_PCT) * p
    raw_h = START_PCT + (t["han"] - START_PCT) * p
    total = raw_p + raw_e + raw_h
    return (raw_p / total * 100, raw_e / total * 100, raw_h / total * 100)


def build_stats(
    archetype: str,
    level: int,
    budget_per_level: float = 30.0,
    scale: float = 1.0,
) -> tuple[float, float, float]:
    total = level * budget_per_level * scale
    p_pct, e_pct, h_pct = stat_pct(archetype, level)
    return (total * p_pct / 100, total * e_pct / 100, total * h_pct / 100)
