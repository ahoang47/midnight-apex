"""
Generate config/sample_builds.json — the player build presets the CLI offers.

Writes the archetype + level format that cli.py reads (pb["name"],
pb["archetype"], pb["level"]). One preset per archetype in cars.ARCHETYPES
per tier below. Stats are NOT stored: the CLI builds them at runtime with
cars.build_stats(), so this file never holds numbers that can drift.

Usage (from sim/):
  python3 scripts/generate_build_matrix.py           # print table only
  python3 scripts/generate_build_matrix.py --write   # also rewrite the JSON
"""
from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, ".")

from velocity_shift.cars import ARCHETYPES, build_stats

PATH = "config/sample_builds.json"

TIERS: list[tuple[str, int]] = [
    ("Rookie", 1),
    ("Starter", 10),
    ("Journeyman", 25),
    ("Veteran", 50),
    ("Elite", 75),
    ("Legend", 99),
]

COMMENT = (
    "Player build presets for the CLI setup flow. Stats are generated at runtime "
    "from archetype + level via cars.build_stats(). Opponents are generated at "
    "runtime from archetype + encounter ratio."
)


def build_presets() -> list[dict]:
    return [
        {"name": f"{tier} {arch}", "archetype": arch, "level": level}
        for arch in ARCHETYPES
        for tier, level in TIERS
    ]


def render_json(presets: list[dict]) -> str:
    """Match the hand-aligned one-preset-per-line layout of the existing file."""
    lines = []
    for p in presets:
        name = json.dumps(p["name"]) + ","
        arch = json.dumps(p["archetype"]) + ","
        name_pad = len(json.dumps(f"Journeyman {p['archetype']}") + ",")
        lines.append(
            f'    {{"name": {name:<{name_pad}} "archetype": {arch:<{len(arch) + 3}} "level": {p["level"]}}}'
        )
    body = ",\n".join(lines)
    return (
        "{\n"
        f'  "_comment": {json.dumps(COMMENT)},\n'
        '  "player_builds": [\n'
        f"{body}\n"
        "  ]\n"
        "}\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--write", action="store_true", help=f"rewrite {PATH}")
    args = ap.parse_args()

    presets = build_presets()
    if args.write:
        with open(PATH, "w") as f:
            f.write(render_json(presets))
        print(f"Wrote {len(presets)} player builds to {PATH}\n")

    print(f"{'Preset':>22} {'Lv':>3} {'POW':>7} {'EN':>7} {'HAN':>7}")
    print("-" * 50)
    for p in presets:
        pw, en, han = build_stats(p["archetype"], p["level"])
        print(f"{p['name']:>22} {p['level']:>3} {pw:>7.0f} {en:>7.0f} {han:>7.0f}")


if __name__ == "__main__":
    main()
