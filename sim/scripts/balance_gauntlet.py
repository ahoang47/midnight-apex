"""
Balance Gauntlet — verifies gameplay feel across stat archetypes, QTE execution
levels, clash outcome scenarios, and encounter types.

Archetypes (cars.py), encounter ratios (ai.ENCOUNTER_RATIOS) and turn limits
(cli.ENCOUNTER_MAX_TURNS) are imported from the engine, not copied.
Note: the archetype PASS rule is only "at least one win and one loss"; read
the win/loss counts, not just the PASS tag.

Usage:
  python3 scripts/balance_gauntlet.py          # only show failures
  python3 scripts/balance_gauntlet.py --all    # show all matchups
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict

sys.path.insert(0, ".")

from velocity_shift.models import Stance, StanceOutcome, CombatantStats, TurnState
from velocity_shift.combat import resolve_turn_legacy as resolve_turn
from velocity_shift.equations import CLASH_STAKES, BATTLE_BONUS, HP_PER_LEVEL, qte_factor, resolve_stance, clash_mult, damage_mitigation

BASE_LEVEL = 50

QTE_LEVELS = {
    "weak":   2.0,
    "mid":    5.0,
    "strong": 9.0,
}

# Archetypes, encounter ratios and turn limits come from the engine so the
# gauntlet tests what the game actually runs (sim code is the source of truth).
from velocity_shift.cars import ARCHETYPES as CAR_ARCHETYPES, build_stats
from velocity_shift.ai import ENCOUNTER_RATIOS
from velocity_shift.cli import ENCOUNTER_MAX_TURNS as _CLI_MAX_TURNS

ARCHETYPES = [(name,) for name in CAR_ARCHETYPES]

_ENC_LABELS = {"wild": "Wild", "lieutenant": "Lieutenant", "boss": "Boss"}

ENCOUNTER_TYPES: dict[str, float] = {
    _ENC_LABELS[k]: v for k, v in ENCOUNTER_RATIOS.items()
}

ENCOUNTER_MAX_TURNS = {
    _ENC_LABELS[k]: v for k, v in _CLI_MAX_TURNS.items()
}


def _opp_level(p_level: int, enc_name: str) -> int:
    """Same rule as cli.py: round(player_level * ratio), min 1."""
    return max(1, round(p_level * ENCOUNTER_TYPES[enc_name]))


def _stats(arch_name: str, level: int) -> tuple[float, float, float]:
    """(pow, en, han) from cars.build_stats, as the engine builds them."""
    return build_stats(arch_name, level)


# Each outcome label maps to (player_stances, opponent_stances) that produce it
_CLASH_PAIRS = {
    "WIN":     ([Stance.POW, Stance.POW, Stance.POW],
                [Stance.HAN, Stance.HAN, Stance.HAN]),
    "LOSS":    ([Stance.EN, Stance.EN, Stance.EN],
                [Stance.HAN, Stance.HAN, Stance.HAN]),
    "TIE":     ([Stance.HAN, Stance.HAN, Stance.HAN],
                [Stance.HAN, Stance.HAN, Stance.HAN]),
}

CLASH_SCENARIO_SEQS = {
    "always_win":     [["WIN", "WIN", "WIN"]],
    "mostly_win":     [["WIN", "WIN", "TIE"], ["WIN", "WIN", "LOSS"], ["WIN", "TIE", "TIE"]],
    "mixed":          [["WIN", "LOSS", "TIE"]],
    "mostly_lose":    [["LOSS", "LOSS", "TIE"], ["LOSS", "LOSS", "WIN"], ["LOSS", "TIE", "TIE"]],
    "always_lose":    [["LOSS", "LOSS", "LOSS"]],
    "always_draw": [["TIE", "TIE", "TIE"]],
}


def _run_turns(
    player: CombatantStats,
    opponent: CombatantStats,
    p_qte: float,
    o_qte: float,
    scenario: str,
    max_turns: int,
) -> tuple[float, float]:
    """Run *max_turns* of resolve_turn with controlled clash outcomes.

    Returns (player_total_dp, opponent_total_dp).
    """
    seqs = CLASH_SCENARIO_SEQS[scenario]
    threshold = (player.level * HP_PER_LEVEL + opponent.level * HP_PER_LEVEL) / 2.0 * 0.15

    p_total = 0.0
    o_total = 0.0

    for turn in range(1, max_turns + 1):
        outcomes = seqs[(turn - 1) % len(seqs)]
        p_cards = []
        o_cards = []
        for out in outcomes:
            p_stances, o_stances = _CLASH_PAIRS[out]
            p_cards.append(p_stances[turn % 3])
            o_cards.append(o_stances[turn % 3])

        ts = TurnState(
            turn_number=turn,
            player_cards=p_cards,
            opponent_cards=o_cards,
            player_qte=p_qte,
            opponent_qte=o_qte,
        )

        gap = p_total - o_total
        tr = resolve_turn(ts, player, opponent, player_gap=gap, rubber_band_threshold=threshold)

        p_total += tr.player_dp
        o_total += tr.opponent_dp

    return p_total, o_total


# ── Algebraic prediction  ──────────────────────────────────────────


def _predict_winner(p_arch, o_arch, p_qte: float, o_qte: float,
                    scenario: str, enc_name: str) -> str:
    """Algebraic per-turn simulator predicting match winner.

    Mirrors combat.py's rubberband logic and position win conditions.
    Cycles through clash sequences per-turn instead of using averages.
    Returns 'Player', 'Opponent', or 'Tie'.
    """
    p_level = BASE_LEVEL
    o_level = _opp_level(p_level, enc_name)
    p_pow, p_en, p_han = _stats(p_arch[0], p_level)
    o_pow, o_en, o_han = _stats(o_arch[0], o_level)
    max_turns = ENCOUNTER_MAX_TURNS[enc_name]

    p_max_hp = p_level * HP_PER_LEVEL
    o_max_hp = o_level * HP_PER_LEVEL
    threshold = (p_max_hp + o_max_hp) / 2.0 * 0.15

    p_qf = max(0.0, min(1.0, qte_factor(p_qte)))
    o_qf = max(0.0, min(1.0, qte_factor(o_qte)))

    p_total = o_total = gap = 0.0
    seqs = CLASH_SCENARIO_SEQS[scenario]

    for turn in range(max_turns):
        outcomes = seqs[turn % len(seqs)]
        sp = so = 0.0
        ss = 0
        for i, out in enumerate(outcomes):
            p_stance, o_stance = _CLASH_PAIRS[out]
            outcome = resolve_stance(p_stance[i], o_stance[i])
            sp += clash_mult(outcome)
            so += clash_mult(StanceOutcome(-outcome.value))
            ss += outcome.value
        p_cm = sp / 3.0
        o_cm = so / 3.0
        bm = 1.0 + BATTLE_BONUS * abs(ss)

        blend = 0.0
        if threshold > 0:
            blend = min(1.0, abs(gap) / threshold)
        elif gap != 0:
            blend = 1.0

        if gap > 0:
            p_dq, p_mq = p_qf, p_qf + (1.0 - p_qf) * blend
            o_dq, o_mq = o_qf + (1.0 - o_qf) * blend, o_qf
        elif gap < 0:
            p_dq, p_mq = p_qf + (1.0 - p_qf) * blend, p_qf
            o_dq, o_mq = o_qf, o_qf + (1.0 - o_qf) * blend
        else:
            p_dq = p_mq = p_qf
            o_dq = o_mq = o_qf

        p_turn = p_pow * p_dq * p_cm * bm
        p_turn *= damage_mitigation(o_en, o_mq)

        o_turn = o_pow * o_dq * o_cm * bm
        o_turn *= damage_mitigation(p_en, p_mq)

        p_total += p_turn
        o_total += o_turn
        gap = p_total - o_total

        p_pos = p_total / o_max_hp
    o_pos = o_total / p_max_hp
    if p_pos > o_pos:
        return "Player"
    if o_pos > p_pos:
        return "Opponent"
    return "Tie"


def run_gauntlet() -> dict:
    results = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))

    total = (len(ARCHETYPES) ** 2 * len(ENCOUNTER_TYPES) * len(QTE_LEVELS) ** 2
             * len(CLASH_SCENARIO_SEQS))
    done = 0

    for enc_name in ENCOUNTER_TYPES:
        ratio = ENCOUNTER_TYPES[enc_name]
        for clash_scenario in CLASH_SCENARIO_SEQS:
            for p_arch in ARCHETYPES:
                p_name = p_arch[0]
                p_level = BASE_LEVEL
                p_pow, p_en, p_han = _stats(p_name, p_level)
                o_level = _opp_level(p_level, enc_name)
                for o_arch in ARCHETYPES:
                    o_name = o_arch[0]
                    o_pow, o_en, o_han = _stats(o_name, o_level)

                    for p_qte_label, p_qte_val in QTE_LEVELS.items():
                        for o_qte_label, o_qte_val in QTE_LEVELS.items():
                            qte_key = f"{p_qte_label}_v_{o_qte_label}"
                            key = (p_name, o_name)

                            p_stat = CombatantStats(
                                name="Player", pow=p_pow, en=p_en, han=p_han,
                                level=p_level,
                            )
                            o_stat = CombatantStats(
                                name="Opponent", pow=o_pow, en=o_en, han=o_han,
                                level=o_level,
                            )

                            p_total, o_total = _run_turns(
                                p_stat, o_stat,
                                p_qte_val, o_qte_val,
                                clash_scenario,
                                ENCOUNTER_MAX_TURNS[enc_name],
                            )

                            p_max_hp = p_level * HP_PER_LEVEL
                            o_max_hp = o_level * HP_PER_LEVEL
                            p_pos = p_total / o_max_hp
                            o_pos = o_total / p_max_hp

                            if p_pos > o_pos:
                                winner = "Player"
                            elif o_pos > p_pos:
                                winner = "Opponent"
                            else:
                                winner = "Tie"

                            results[enc_name][clash_scenario][qte_key][key] = {
                                "p_total": p_total,
                                "o_total": o_total,
                                "winner": winner,
                                "turns_played": ENCOUNTER_MAX_TURNS[enc_name],
                            }
                            done += 1

        print(f"  Progress: {done}/{total} runs", end="\r")

    print(f"  Progress: {done}/{total} runs")
    return results


def analyze(results: dict, show_all: bool = False) -> None:
    qte_combos = [f"{a}_v_{b}" for a in QTE_LEVELS for b in QTE_LEVELS]
    overall_pass = True

    def _check(p_arch, o_arch, p_qte, o_qte, scenario, enc_name, entry) -> bool:
        expected = _predict_winner(p_arch, o_arch, p_qte, o_qte, scenario, enc_name)
        if expected == "Tie":
            return True
        return entry["winner"] == expected

    for enc_name in list(results.keys()):
        print(f"\n{'='*100}")
        print(f"  ENCOUNTER TYPE: {enc_name}")
        print(f"{'='*100}")

        for clash_scenario in CLASH_SCENARIO_SEQS:
            print(f"\n  === Clash: {clash_scenario} ===")

            # --- Section A: Mirror matches ---
            mirror_rows = []

            for qte_combo in qte_combos:
                p_label, o_label = qte_combo.split("_v_")

                for p_arch in ARCHETYPES:
                    p_name = p_arch[0]
                    for o_arch in ARCHETYPES:
                        if p_name != o_arch[0]:
                            continue
                        key = (p_name, p_name)
                        entry = results[enc_name][clash_scenario][qte_combo].get(key)
                        if entry is None:
                            continue

                        ok = _check(
                            p_arch, o_arch,
                            QTE_LEVELS[p_label], QTE_LEVELS[o_label],
                            clash_scenario, enc_name, entry,
                        )
                        tag = "PASS" if ok else "FAIL"
                        if not ok:
                            overall_pass = False

                        if show_all or not ok:
                            mirror_rows.append(
                                f"  {p_name:>10s}  {p_label:>5s} {o_label:>5s}  "
                                f"{entry['p_total']:>6.0f} {entry['o_total']:>6.0f}  "
                                f"{entry['winner']:>12s}  {tag:>6s}"
                            )

            if mirror_rows:
                print(f"\n  -- Mirror matches --")
                header = (
                    f"  {'Archetype':>10s}  {'P_QTE':>5s} {'O_QTE':>5s}  "
                    f"{'P_DP':>6s} {'O_DP':>6s}  "
                    f"{'Winner':>12s}  {'Status':>6s}"
                )
                print(header)
                print(f"  {'-'*10}  {'-'*5} {'-'*5}  "
                      f"{'-'*6} {'-'*6}  "
                      f"{'-'*12}  {'-'*6}")
                for row in mirror_rows:
                    print(row)

            # --- Section B: Mismatches ---
            fail_details = []
            total_pairs = 0
            fail_count = 0

            for qte_combo in qte_combos:
                p_label, o_label = qte_combo.split("_v_")

                for p_arch in ARCHETYPES:
                    p_name = p_arch[0]
                    for o_arch in ARCHETYPES:
                        o_name = o_arch[0]
                        if p_name == o_name:
                            continue
                        key = (p_name, o_name)
                        entry = results[enc_name][clash_scenario][qte_combo].get(key)
                        if entry is None:
                            continue

                        total_pairs += 1
                        ok = _check(
                            p_arch, o_arch,
                            QTE_LEVELS[p_label], QTE_LEVELS[o_label],
                            clash_scenario, enc_name, entry,
                        )
                        if not ok:
                            fail_count += 1
                            overall_pass = False
                            fail_details.append(
                                f"    FAIL: {p_name} ({p_label}) vs {o_name} ({o_label}) \u2014 "
                                f"{'P' if entry['winner']=='Opponent' else 'O'}_DP={entry['p_total']:.0f} "
                                f"{'P' if entry['winner']=='Player' else 'O'}_DP={entry['o_total']:.0f} "
                                f"winner={entry['winner']}"
                            )

            if show_all or fail_count > 0:
                print(f"\n  -- Mismatches --")
                if fail_count == 0:
                    print(f"  {total_pairs} pairs checked \u2014 0 failures \u2014 PASS")
                else:
                    print(f"  {total_pairs} pairs checked \u2014 {fail_count} failures \u2014 FAIL")
                    for d in fail_details:
                        print(d)

    # ── Cross-archetype balance: no single build dominates ──
    print(f"\n  -- Archetype Balance --")
    arch_wins: dict[str, int] = defaultdict(int)
    arch_losses: dict[str, int] = defaultdict(int)
    for enc_name in results:
        for scenario in CLASH_SCENARIO_SEQS:
            for qte_combo in qte_combos:
                for p_arch in ARCHETYPES:
                    pn = p_arch[0]
                    for o_arch in ARCHETYPES:
                        on = o_arch[0]
                        if pn == on:
                            continue
                        entry = results[enc_name][scenario][qte_combo].get((pn, on))
                        if entry is None:
                            continue
                        if entry["winner"] == "Player":
                            arch_wins[pn] += 1
                            arch_losses[on] += 1
                        elif entry["winner"] == "Opponent":
                            arch_wins[on] += 1
                            arch_losses[pn] += 1

    for arch_name in [a[0] for a in ARCHETYPES]:
        w = arch_wins.get(arch_name, 0)
        l = arch_losses.get(arch_name, 0)
        ok = w > 0 and l > 0
        if not ok:
            overall_pass = False
        tag = "PASS" if ok else "FAIL"
        print(f"  {arch_name:>10s}: {w:>4d} wins, {l:>4d} losses  {tag:>6s}")

    print(f"\n{'='*100}")
    if overall_pass:
        print(f"  GAUNTLET RESULT: ALL CHECKS PASS")
    else:
        print(f"  GAUNTLET RESULT: SOME CHECKS FAILED")
    print(f"{'='*100}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Balance Gauntlet \u2014 verify gameplay feel across stat archetypes"
    )
    parser.add_argument("--all", action="store_true",
                        help="Show all matchups (default: only failures)")
    args = parser.parse_args()

    print(f"Balance Gauntlet \u2014 {len(ARCHETYPES)} archetypes, {len(ENCOUNTER_TYPES)} encounter types, "
          f"{len(QTE_LEVELS)}^2 QTE combos, {len(CLASH_SCENARIO_SEQS)} clash scenarios")

    results = run_gauntlet()
    analyze(results, show_all=args.all)
