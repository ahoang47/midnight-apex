#!/usr/bin/env python3
from __future__ import annotations
import math
import sys

sys.path.insert(0, ".")


def pow_cap(budget: int) -> int:
    cap = int(math.sqrt(budget * S))
    return min(budget, cap)


def power_rating(pow_val: float, def_val: float, eff_val: float) -> float:
    """Compute a display-only power level from stats."""
    return (pow_val + def_val + eff_val) / 100

S = 300
MAX_STAT = 1000
MAX_BUDGET = 3000
DC = 0.01
CLASH_STAKES = 0.3

CLASH_OUTCOMES: list[tuple[str, float]] = [
    ("Player sweeps (3-0)", 1 + CLASH_STAKES),
    ("Player wins   (2-1)", (2 * (1 + CLASH_STAKES) + (1 - CLASH_STAKES)) / 3),
    ("Neutral       (1-1)", 1.0),
    ("Opponent wins (1-2)", ((1 + CLASH_STAKES) + 2 * (1 - CLASH_STAKES)) / 3),
    ("Opponent sweeps(0-3)", 1 - CLASH_STAKES),
]

ARCHETYPES = {
    "mirror":    None,
    "POW-heavy": 2.0,
    "balanced":  1.0,
    "DEF-heavy": 0.5,
}


def archetype_split(remainder: int, choice: int, custom_def: int | None = None) -> tuple[int, int]:
    ratios = {1: (0.5, 0.5), 2: (0.7, 0.3), 3: (0.3, 0.7),
              4: (0.85, 0.15), 5: (0.15, 0.85)}
    if choice == 6 and custom_def is not None:
        d, e = custom_def, remainder - custom_def
    else:
        dr, er = ratios[choice]
        d, e = int(remainder * dr), int(remainder * er)

    d = min(d, MAX_STAT)
    e = min(e, MAX_STAT)
    leftover = remainder - d - e
    if leftover > 0:
        d = min(d + leftover, MAX_STAT)
        leftover = remainder - d - e
        e = min(e + leftover, MAX_STAT)
    return d, e


def damage_ratio(p_pow: float, p_def: float, o_pow: float, o_def: float) -> float:
    return (p_pow / o_pow) * ((1 + DC * p_def) / (1 + DC * o_def))


def solve_opponent(
    p_pow: float, p_def: float, target_s: float, opp_ratio: float,
) -> tuple[float, float] | None:
    D = 1 + DC * p_def
    r = opp_ratio
    a = r * DC
    b = r
    c = -p_pow * D / target_s

    disc = b * b - 4 * a * c
    if disc < 0:
        return None
    sqrt_disc = math.sqrt(disc)
    o_def = (-b + sqrt_disc) / (2 * a)
    o_pow = opp_ratio * o_def
    if o_def <= 0 or o_pow <= 0:
        return None
    return (o_pow, o_def)


def design_racer() -> dict:
    print("=== VELOCITY SHIFT — Vehicle Racer Designer ===\n")

    while True:
        raw = input("Total stat budget [1\u20133000]: ").strip()
        try:
            budget = int(raw)
            if 1 <= budget <= MAX_BUDGET:
                break
        except ValueError:
            pass
        print("  Enter a whole number between 1 and 3000.")

    cap = pow_cap(budget)

    print(f"\n--- POW ---")
    print(f"POW cap for budget {budget}: {cap}")
    while True:
        raw = input(f"POW [{cap}]: ").strip()
        if not raw:
            pow_val = cap
            break
        try:
            p = int(raw)
            if 1 <= p <= cap:
                pow_val = p
                break
        except ValueError:
            pass
        print(f"  Enter 1\u2013{cap}.")

    remainder = budget - pow_val

    if remainder == 0:
        def_val = eff_val = 0
        print("\n  Note: all-offense build \u2014 0 DEF, 0 EFF.")
    else:
        print(f"\n--- DEF + EFF split (remainder: {remainder}) ---")
        print("  1: Balanced  (50/50)")
        print("  2: Turtle    (70/30)")
        print("  3: Endless   (30/70)")
        print("  4: Defensive (85/15)")
        print("  5: Efficient (15/85)")
        print("  6: Custom    (enter DEF manually)")

        while True:
            raw = input("\nChoice [1]: ").strip()
            choice = int(raw) if raw else 1
            if 1 <= choice <= 5:
                def_val, eff_val = archetype_split(remainder, choice)
                break
            if choice == 6:
                while True:
                    raw = input("  DEF: ").strip()
                    try:
                        d = int(raw)
                        if 0 <= d <= remainder:
                            def_val, eff_val = archetype_split(remainder, 6, d)
                            break
                    except ValueError:
                        pass
                    print(f"  Enter 0\u2013{remainder}.")
                break
            print("  Enter 1\u20136.")

        labels = {1: "Even split \u2014 no particular strength or weakness.",
                  2: "High DEF \u2014 absorbs hits well, lower stamina sustain.",
                  3: "High EFF \u2014 never gasses out, but squishier.",
                  4: "Extreme DEF \u2014 maxes armor first, minimal efficiency.",
                  5: "Extreme EFF \u2014 maxes stamina economy, minimal armor.",
                  6: f"Custom: DEF={def_val}, EFF={eff_val}."}
        print(f"\n  \u2192 {labels[choice]}")

    print("\n--- Details ---")
    name = input("Name [Unnamed Racer]: ").strip() or "Unnamed Racer"
    desc = input("Description: ").strip() or ""

    return {"name": name, "pow": pow_val, "def": def_val, "eff": eff_val, "description": desc}


def design_opponent(player: dict) -> tuple[float, float, float, float, float, str] | None:
    p_pow, p_def, p_eff = player["pow"], player["def"], player["eff"]

    if p_def == 0:
        print("\n  Player has 0 DEF \u2014 cannot generate a matched opponent.")
        return None

    print("\n=== Opponent Generation ===\n")

    print("  Archetype (POW/DEF ratio):")
    print("    1: Mirror    \u2014 same POW/DEF split as player")
    print("    2: POW-heavy \u2014 high power, lower defense")
    print("    3: Balanced  \u2014 equal POW and DEF")
    print("    4: DEF-heavy \u2014 high defense, lower power")
    while True:
        raw = input("\n  Archetype [1]: ").strip()
        arch_choice = int(raw) if raw else 1
        if 1 <= arch_choice <= 4:
            break
        print("  Enter 1\u20134.")

    arch_map = {1: "mirror", 2: "POW-heavy", 3: "balanced", 4: "DEF-heavy"}
    archetype = arch_map[arch_choice]

    print("\n  Difficulty (who has the advantage?):")
    print("    1: Even       \u2014 perfectly matched")
    print("    2: Advantage  \u2014 player has slight edge")
    print("    3: Challenge  \u2014 opponent has slight edge")
    while True:
        raw = input("\n  Difficulty [1]: ").strip()
        diff_choice = int(raw) if raw else 1
        if 1 <= diff_choice <= 3:
            break
        print("  Enter 1\u20133.")

    target_s_map = {1: 1.0, 2: 1.15, 3: 0.85}
    target_s = target_s_map[diff_choice]

    print("\n  Opponent EFF:")
    print(f"    1: Same as player ({p_eff})")
    print("    2: Custom")
    while True:
        raw = input("\n  Choice [1]: ").strip()
        eff_choice = int(raw) if raw else 1
        if eff_choice == 1:
            opp_eff = p_eff
            break
        elif eff_choice == 2:
            while True:
                raw = input("  Opponent EFF (0\u20131000): ").strip()
                try:
                    v = int(raw)
                    if 0 <= v <= 1000:
                        opp_eff = v
                        break
                except ValueError:
                    pass
                print("  Enter 0\u20131000.")
            break
        print("  Enter 1\u20132.")

    if archetype == "mirror":
        opp_ratio = p_pow / p_def
    else:
        opp_ratio = ARCHETYPES[archetype]

    K = p_pow * (1 + DC * p_def) / target_s
    min_r = (p_pow * (1 + DC * p_def)) / (target_s * 1000 * (1 + DC * 1000))
    max_r = None
    if K > 1000:
        max_r = 1000 * DC / (K / 1000 - 1)

    if opp_ratio < min_r or (max_r and opp_ratio > max_r):
        max_r_str = f"{max_r:.4f}" if max_r else "\u221e"
        print(f"\n  Infeasible with these settings \u2014 opponent ratio {opp_ratio:.4f} "
              f"outside range [{min_r:.4f}, {max_r_str})")
        print("  Try a different archetype or difficulty.")
        return None

    result = solve_opponent(p_pow, p_def, target_s, opp_ratio)
    if result is None:
        print("\n  No feasible opponent. Try different parameters.")
        return None

    o_pow, o_def = result

    # Clamp each stat to 1000
    o_pow = min(o_pow, float(MAX_STAT))
    o_def = min(o_def, float(MAX_STAT))
    opp_eff = min(opp_eff, float(MAX_STAT))

    # Clamp POW to the POW cap, recalculating DEF to maintain ratio
    for _ in range(5):
        o_budget = o_pow + o_def + opp_eff
        o_cap = pow_cap(int(o_budget))
        if o_pow <= o_cap:
            break
        o_pow = float(o_cap)
        o_def = min(o_pow / opp_ratio, float(MAX_STAT))

    # Final budget cap check
    o_budget = o_pow + o_def + opp_eff
    if o_budget > MAX_BUDGET:
        print(f"\n  Opponent budget {o_budget:.0f} exceeds max {MAX_BUDGET}. Try different settings.")
        return None

    return o_pow, o_def, opp_eff, target_s, opp_ratio, archetype


def display_player_output(player: dict) -> None:
    print("\n--- Player Racer ---")
    print("{")
    print(f'  "name": "{player["name"]}",')
    print(f'  "pow": {player["pow"]},')
    print(f'  "def": {player["def"]},')
    print(f'  "eff": {player["eff"]},')
    print(f'  "qte_factor": 0.5,')
    print(f'  "mods": [],')
    print(f'  "description": "{player["description"]}"')
    print("}")


def display_opponent_comparison(player: dict, o_pow: float, o_def: float, opp_eff: float,
                                 target_s: float, opp_ratio: float, archetype: str) -> None:
    p_pow, p_def, p_eff = player["pow"], player["def"], player["eff"]

    actual_s = damage_ratio(p_pow, p_def, o_pow, o_def)

    p_budget = p_pow + p_def + p_eff
    o_budget = o_pow + o_def + opp_eff
    p_cap = pow_cap(int(p_budget))
    o_cap = pow_cap(int(o_budget))

    p_base = p_pow / (1 + DC * o_def)
    o_base = o_pow / (1 + DC * p_def)

    p_ratio = p_pow / p_def

    print(f"\n{'Player':>20s}  {'Opponent':>20s}")
    line_chr = "\u2500"
    print(f"  {line_chr*21}    {line_chr*21}")
    print(f"  POW: {p_pow:<5.0f}            POW: {o_pow:<5.0f}")
    print(f"  DEF: {p_def:<5.0f}            DEF: {o_def:<5.0f}")
    print(f"  EFF: {p_eff:<5.0f}            EFF: {opp_eff:<5.0f}")
    p_lv = power_rating(p_pow, p_def, p_eff)
    o_lv = power_rating(o_pow, o_def, opp_eff)
    arrow = '>' if o_lv > p_lv else '<' if o_lv < p_lv else '='
    print(f"  Lv: {p_lv:<5.1f}            Lv: {o_lv:<5.1f}  ({arrow})")
    print(f"  POW/DEF: {p_ratio:<.3f}          POW/DEF: {opp_ratio:<.3f}")
    print(f"  Budget: {p_budget:<5.0f}           Budget: {o_budget:<5.0f}")
    print(f"  POW cap: {p_cap:<5.0f}           POW cap: {o_cap:<5.0f}")
    print()

    label = "perfectly matched" if abs(actual_s - 1) < 0.005 else \
            f"player {'>' if actual_s > 1 else '<'} opponent"
    print(f"  Damage ratio S = {actual_s:.4f}  ({label})")
    print(f"  Opponent budget = {o_budget/p_budget*100:.1f}% of player's")
    print(f"  Base DP/clash (full STM, perfect QTE):")
    print(f"    Player: {p_base:.2f}  |  Opponent: {o_base:.2f}  |  Ratio: {p_base/o_base:.4f}")
    print()

    print(f"  Clash outcome impact (clash_stakes={CLASH_STAKES}):")
    for label, avg in CLASH_OUTCOMES:
        p_dp = p_base * avg
        o_dp = o_base * (2 - avg)
        print(f"    {label:>22s}:  P_DP={p_dp:>7.2f}  O_DP={o_dp:>7.2f}")

    QTE_PAIRS: list[tuple[float, float, str]] = [
        (10.0, 10.0, "both perfect"),
        (10.0,  5.0, "player perfect, opponent poor"),
        ( 5.0, 10.0, "player poor, opponent perfect"),
        ( 7.5,  7.5, "both average"),
        ( 5.0,  5.0, "both poor"),
    ]
    print()
    print(f"  QTE execution impact (full STM):")
    for p_qte, o_qte, desc in QTE_PAIRS:
        p_qf = p_qte / 10.0
        o_qf = o_qte / 10.0
        print()
        print(f"  P_QTE={p_qte:<4.1f}  O_QTE={o_qte:<4.1f}  ({desc}):")
        for label, avg in CLASH_OUTCOMES:
            p_dp = p_base * p_qf * avg
            o_dp = o_base * o_qf * (2 - avg)
            r = p_dp / o_dp
            print(f"    {label:>22s}:  P_DP={p_dp:>7.2f}  O_DP={o_dp:>7.2f}  Ratio={r:.4f}")

    print(f"\n--- Opponent JSON ---")
    print("{")
    print(f'  "name": "Opponent ({archetype})",')
    print(f'  "pow": {o_pow:.0f},')
    print(f'  "def": {o_def:.0f},')
    print(f'  "eff": {opp_eff},')
    print(f'  "qte_factor": 0.5,')
    print(f'  "mods": [],')
    print(f'  "description": "Auto-generated {archetype} opponent"')
    print("}")


def main() -> None:
    player = design_racer()
    display_player_output(player)

    result = design_opponent(player)
    if result is None:
        return
    o_pow, o_def, opp_eff, target_s, opp_ratio, archetype = result
    display_opponent_comparison(player, o_pow, o_def, opp_eff, target_s, opp_ratio, archetype)


if __name__ == "__main__":
    main()
