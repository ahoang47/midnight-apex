#!/usr/bin/env python3
"""
Design a well-matched opponent for Velocity Shift.

Given player POW/DEF/EFF, produces an opponent with equal effective
damage output (S=1.0) and the same stat distribution.

Usage:
  python3 scripts/design_opponent.py --p-pow 750 --p-def 600 --p-eff 400
  python3 scripts/design_opponent.py --p-pow 800 --p-def 100 --p-eff 300 --stronger
  python3 scripts/design_opponent.py --p-pow 750 --p-def 600 --p-eff 400 --archetype balanced
"""
from __future__ import annotations

import argparse
import math
import sys

DESC = __doc__
S = 300
MAX_STAT = 1000
MAX_BUDGET = 3000
DC = 0.01          # def_scaling
CLASH_STAKES = 0.3

CLASH_OUTCOMES: list[tuple[str, float]] = [
    ("Player sweeps (3-0)", 1 + CLASH_STAKES),
    ("Player wins   (2-1)", (2 * (1 + CLASH_STAKES) + (1 - CLASH_STAKES)) / 3),
    ("Neutral       (1-1)", 1.0),
    ("Opponent wins (1-2)", ((1 + CLASH_STAKES) + 2 * (1 - CLASH_STAKES)) / 3),
    ("Opponent sweeps(0-3)", 1 - CLASH_STAKES),
]

sys.path.insert(0, ".")

ARCHETYPES = {
    "mirror":    None,    # same POW/DEF ratio as player
    "POW-heavy": 2.0,
    "balanced":  1.0,
    "DEF-heavy": 0.5,
}


def pow_cap(budget: int) -> int:
    cap = int(math.sqrt(budget * S))
    return min(budget, cap)


def power_rating(pow_val: float, def_val: float, eff_val: float) -> float:
    """Compute a display-only power level from stats."""
    return (pow_val + def_val + eff_val) / 100


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description=DESC,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--p-pow", type=float, required=True, help="Player POW (0–1000)")
    parser.add_argument("--p-def", type=float, required=True, help="Player DEF (0–1000)")
    parser.add_argument("--p-eff", type=float, required=True, help="Player EFF (0–1000)")
    parser.add_argument("--target-s", type=float, default=None,
                        help="Damage ratio S (>1 = player advantage, <1 = opponent advantage)")
    parser.add_argument("--opp-eff", type=float, default=None,
                        help="Opponent EFF (default: same as player)")

    arch_help = "Archetype: " + ", ".join(f"'{k}'" for k in ARCHETYPES)
    parser.add_argument("--archetype", choices=list(ARCHETYPES),
                        default="mirror", help=arch_help + " (default: mirror)")

    adv = parser.add_argument_group("advanced (override archetype)")
    adv.add_argument("--opp-ratio", type=float, default=None,
                     help="Opponent POW/DEF ratio (overrides --archetype)")

    args = parser.parse_args()

    for name, val in [("POW", args.p_pow), ("DEF", args.p_def), ("EFF", args.p_eff)]:
        if not (0 <= val <= 1000):
            print(f"Error: Player {name} must be 0–1000, got {val}", file=sys.stderr)
            sys.exit(1)
    if args.p_def == 0:
        print("Error: Player DEF must be > 0.", file=sys.stderr)
        sys.exit(1)

    target_s = args.target_s if args.target_s is not None else 1.0
    if target_s <= 0:
        print("Error: --target-s must be positive.", file=sys.stderr)
        sys.exit(1)

    opp_ratio = args.opp_ratio
    if opp_ratio is None:
        if args.archetype == "mirror":
            opp_ratio = args.p_pow / args.p_def
        else:
            opp_ratio = ARCHETYPES[args.archetype]

    opp_eff = args.opp_eff if args.opp_eff is not None else args.p_eff

    min_r = (args.p_pow * (1 + DC * args.p_def)) / (target_s * 1000 * (1 + DC * 1000))
    K = args.p_pow * (1 + DC * args.p_def) / target_s
    if K > 1000:
        max_r = 1000 * DC / (K / 1000 - 1)
    else:
        max_r = None

    if opp_ratio < min_r or (max_r and opp_ratio > max_r):
        print(f"Error: Opponent ratio {opp_ratio:.4f} outside feasible range "
              f"[{min_r:.4f}, {max_r:.4f}]" if max_r else
              f"[{min_r:.4f}, ∞)", file=sys.stderr)
        print(f"  Try a different --archetype or use --target-s / --opp-ratio.", file=sys.stderr)
        sys.exit(1)

    result = solve_opponent(args.p_pow, args.p_def, target_s, opp_ratio)
    if result is None:
        print("Error: No feasible opponent. Try different parameters.", file=sys.stderr)
        sys.exit(1)

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
        print(f"Error: Opponent budget {o_budget:.0f} exceeds max {MAX_BUDGET}.",
              file=sys.stderr)
        sys.exit(1)

    actual_s = damage_ratio(args.p_pow, args.p_def, o_pow, o_def)

    p_budget = args.p_pow + args.p_def + args.p_eff
    o_budget = o_pow + o_def + opp_eff

    p_base = args.p_pow / (1 + DC * o_def)
    o_base = o_pow / (1 + DC * args.p_def)

    p_ratio = args.p_pow / args.p_def
    print()
    print(f"{'Player':>20s}  {'Opponent':>20s}")
    print(f"  {'─'*21}    {'─'*21}")
    print(f"  POW: {args.p_pow:<5.0f}            POW: {o_pow:<5.0f}")
    print(f"  DEF: {args.p_def:<5.0f}            DEF: {o_def:<5.0f}")
    print(f"  EFF: {args.p_eff:<5.0f}            EFF: {opp_eff:<5.0f}")
    p_lv = power_rating(args.p_pow, args.p_def, args.p_eff)
    o_lv = power_rating(o_pow, o_def, opp_eff)
    arrow = '>' if o_lv > p_lv else '<' if o_lv < p_lv else '='
    print(f"  Lv: {p_lv:<5.1f}            Lv: {o_lv:<5.1f}  ({arrow})")
    p_cap = pow_cap(int(p_budget))
    o_cap = pow_cap(int(o_budget))
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


if __name__ == "__main__":
    main()
