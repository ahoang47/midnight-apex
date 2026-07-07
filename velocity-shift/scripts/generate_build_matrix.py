#!/usr/bin/env python3
"""Generate a matrix of player and opponent builds using design_racers.py equations.

Replaces config/sample_builds.json with a structured 7×3 build matrix
where each player build has a matched opponent with a growing edge.
"""
from __future__ import annotations
import json
import math
import sys

sys.path.insert(0, ".")

from scripts.design_racers import (
    solve_opponent,
    archetype_split,
    damage_ratio,
    MAX_STAT,
    S,
)

# ── Configuration ────────────────────────────────────────────────────

BUDGETS: list[int] = [300, 500, 800, 1200, 1700, 2200, 3000]

# Growing edge — lower target_s = bigger opponent stat advantage
TARGET_S: dict[int, float] = {
    300: 0.90,
    500: 0.88,
    800: 0.85,
    1200: 0.83,
    1700: 0.80,
}

OPP_QTE: dict[int, float] = {
    300: 0.50,
    500: 0.50,
    800: 0.55,
    1200: 0.60,
    1700: 0.65,
    2200: 0.70,
    3000: 0.75,
}

PLAYER_QTE: float = 0.50


def pow_cap(budget: int) -> int:
    cap = int(math.sqrt(budget * S))
    return min(budget, cap)


def power_rating(pow_val: float, def_val: float, eff_val: float) -> float:
    """Compute a display-only power level from stats."""
    return (pow_val + def_val + eff_val) / 100



# Archetypes: (label, pow_fraction_of_cap, archetype_split_ratio)
ARCHETYPES: list[tuple[str, float, int, str]] = [
    ("All-rounder", 0.45, 1, "balanced stats, even DEF/EFF split"),
    ("Bruiser",     0.75, 2, "high-POW burst, DEF-leaning stamina"),
    ("Endurance",   0.30, 3, "high-EFF stamina economy, lower POW"),
]

# Tier labels for naming
TIER_LABEL: dict[int, str] = {
    300:  "Starter",
    500:  "Novice",
    800:  "Journeyman",
    1200: "Veteran",
    1700: "Elite",
    2200: "Master",
    3000: "Legend",
}


# ── Build generation ─────────────────────────────────────────────────

def generate_player(budget: int, archetype_idx: int) -> dict:
    label, pow_frac, split_ratio, desc = ARCHETYPES[archetype_idx]
    cap = pow_cap(budget)
    p_pow = max(1, int(cap * pow_frac))
    remainder = budget - p_pow
    if remainder <= 0:
        p_def = 0
        p_eff = 0
    else:
        p_def, p_eff = archetype_split(remainder, split_ratio)
        p_def = min(p_def, MAX_STAT)
        p_eff = min(p_eff, MAX_STAT)

    return {
        "name": f"{TIER_LABEL[budget]} {label}",
        "pow": p_pow,
        "def": p_def,
        "eff": p_eff,
        "description": f"Budget {budget} {label.lower()} — {desc}",
    }


def generate_opponent(player: dict, budget: int) -> dict | None:
    p_pow, p_def, p_eff = player["pow"], player["def"], player["eff"]
    label = player["name"].split(" ", 1)[1]

    if p_def == 0:
        return None

    opp_ratio = p_pow / p_def  # mirror archetype

    if budget <= 1700:
        target_s = TARGET_S[budget]
        result = solve_opponent(p_pow, p_def, target_s, opp_ratio)
        if result is None:
            return None
        o_pow, o_def = result
        o_eff = float(p_eff)
    else:
        o_pow = min(p_pow * 1.10, float(MAX_STAT))
        o_def = min(p_def * 1.10, float(MAX_STAT))
        o_eff = min(float(p_eff), float(MAX_STAT))

    o_pow = min(o_pow, float(MAX_STAT))
    o_def = min(o_def, float(MAX_STAT))
    o_eff = min(o_eff, float(MAX_STAT))

    # Clamp POW to cap
    for _ in range(5):
        o_budget = o_pow + o_def + o_eff
        o_cap = pow_cap(int(o_budget))
        if o_pow <= o_cap:
            break
        o_pow = float(o_cap)
        o_def = min(o_pow / opp_ratio, float(MAX_STAT))

    o_qte = OPP_QTE[budget]

    s_actual = damage_ratio(p_pow, p_def, o_pow, o_def)
    eff_ratio = s_actual * (PLAYER_QTE / o_qte)
    edge_pct = round(abs(1 - eff_ratio) * 100)

    return {
        "name": f"{TIER_LABEL[budget]} {label} Rival",
        "pow": round(o_pow),
        "def": round(o_def),
        "eff": round(o_eff),
        "qte_factor": o_qte,
        "description": f"Budget {budget} rival — {label.lower()} archetype, "
                       f"{edge_pct}% effective edge over player",
    }


def main() -> None:
    player_builds: list[dict] = []
    opponent_builds: list[dict] = []

    for budget in BUDGETS:
        for archetype_idx in range(3):
            player = generate_player(budget, archetype_idx)
            opponent = generate_opponent(player, budget)
            if opponent is None:
                continue
            player_builds.append(player)
            opponent_builds.append(opponent)

    # ── Output ────────────────────────────────────────────────────────
    output = {
        "_comment": "Generated build matrix — player build presets for the CLI setup flow. "
                    "Opponents are generated at runtime from archetype + level.",
        "player_builds": player_builds,
    }

    path = "config/sample_builds.json"
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")

    # ── Summary ───────────────────────────────────────────────────────
    print(f"Wrote {len(player_builds)} player builds to {path}")
    print()
    print(f"{'Tier':>8} {'Archetype':>15} {'POW':>5} {'DEF':>5} {'EFF':>5} {'Lv':>4}   "
          f"{'O_POW':>5} {'O_DEF':>5} {'O_EFF':>5} {'O_Lv':>4} {'O_QTE':>5} {'S':>5} {'EffR':>5}")
    print("-" * 95)

    for p, o in zip(player_builds, opponent_builds):
        p_lv = power_rating(p["pow"], p["def"], p["eff"])
        o_lv = power_rating(o["pow"], o["def"], o["eff"])
        s = damage_ratio(p["pow"], p["def"], o["pow"], o["def"])
        eff_r = s * (PLAYER_QTE / o["qte_factor"])
        tier = [k for k, v in TIER_LABEL.items() if v in p["name"]][0]
        arch = p["name"].split(" ", 1)[1]
        print(f"{tier:>5} {arch:>15} {p['pow']:>5} {p['def']:>5} {p['eff']:>5} "
              f"{p_lv:>4.1f}   {o['pow']:>5} {o['def']:>5} {o['eff']:>5} "
              f"{o_lv:>4.1f} {o['qte_factor']:>5.2f} {s:>5.3f} {eff_r:>5.3f}")


if __name__ == "__main__":
    main()
