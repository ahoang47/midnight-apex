from __future__ import annotations
"""Interactive frontend — match setup, prompts, display, and entry point.

Setup flow: pick player build → pick encounter type → pick opponent
archetype → district and track. Opponent stats are generated from
archetype + level derived from the encounter type ratio. The opponent
plays its district line (LINE_SET_C) under the boss heat rule. Each
clash the player picks any stance whose heat gauge is not locked
(heat/load system, resources-v4b G2, 2026-11-13; no card draw).
"""

import datetime

from .cars import build_stats, ARCHETYPES
from .equations import qte_factor, DISTRICTS, qte_zone_width, QTE_ZONE_BASE_MS, QTE_PHASES
from .combat import official_tracks
from .models import Stance, StanceOutcome, CombatantStats, MatchConfig, MatchResult, \
    TurnResult, ClashResult, ClashContext
from .match import run_match
from .trace import TraceLogger
from .ai import ENCOUNTER_RATIOS, ENCOUNTER_PHASES, ENCOUNTER_LAP_SIZES
from .equations import HEAT_ORDER

ENCOUNTER_LABELS = {
    "wild": "Wild Encounter",
    "lieutenant": "Lieutenant Challenge",
    "boss": "Boss Encounter",
}

ENCOUNTER_MAX_TURNS = {
    "wild": 10,
    "lieutenant": 20,
    "boss": 30,
}


def fmt(v: float, decimals: int = 4) -> str:
    return f"{v:.{decimals}f}"


def _stance_label(c: object) -> str:
    return c.value if isinstance(c, Stance) else str(c)


def _cards_label(stances: list) -> str:
    if not stances:
        return "???"
    return "-".join(_stance_label(c) for c in stances)


def _heat_label(fill: list, locked: list) -> str:
    if not fill:
        return "?"
    return " ".join(f"{n}:{f*100:3.0f}%{'(L)' if lk else ''}" for n, f, lk in zip(HEAT_ORDER, fill, locked))


def _outcome_icon(outcomes: list[StanceOutcome]) -> str:
    icons = {StanceOutcome.WIN: "W", StanceOutcome.DRAW: "\u2014", StanceOutcome.LOSS: "L"}
    return " ".join(icons[o] for o in outcomes)


def _battle_icon(winner: str | None, player_name: str) -> str:
    if winner == "Player":
        return f"{player_name} \u2b06"
    elif winner == "Opponent":
        return "Opponent \u2b06"
    else:
        return "\u2014 tie \u2014"


def _write_log(result: MatchResult, cfg: MatchConfig) -> None:
    import os
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join("logs", f"vs_log_{timestamp}.txt")
    with open(filename, "w") as f:
        f.write("=" * 72 + "\n")
        f.write(f"  VELOCITY SHIFT \u2014 Match Log\n")
        f.write(f"  {result.player_name} vs {result.opponent_name}\n")
        f.write(f"  Turns: {result.turns_played}/{result.total_turns}  |  Seed: {cfg.seed}\n")
        f.write(f"  Result: {result.winner} (Decision)\n")
        f.write(f"  Position: {result.player_name} {result.player_position*100:.0f}% | "
                f"{result.opponent_name} {result.opponent_position*100:.0f}%\n")
        f.write(f"  Final progress: {result.player_name} {fmt(result.player_total_dp,1)} | "
                f"{result.opponent_name} {fmt(result.opponent_total_dp,1)}\n")
        f.write("=" * 72 + "\n\n")
        f.write(f"  {'T':>2} {'P-Picks':>12} {'O-Picks':<12} {'Battle':>14}  {'P_QTE':>5} {'O_QTE':>5}  "
                f"{'P_DP':>7} {'O_DP':>7}  {'Cum_P':>7} {'Cum_O':>7}\n")
        f.write("  " + "-" * 88 + "\n")
        cum_p = 0.0
        cum_o = 0.0
        for t in result.turn_results:
            cum_p += t.player_dp
            cum_o += t.opponent_dp
            p_picks = _cards_label(t.player_stances)
            o_picks = _cards_label(t.opponent_stances)
            p_heat = _heat_label(t.player_heat_fill, t.player_locked)
            o_heat = _heat_label(t.opponent_heat_fill, t.opponent_locked)
            battle = t.battle_winner or "\u2014"
            f.write(f"  {t.turn_number:>2}  {p_picks:>12} {o_picks:<12}  {battle:>14}  "
                    f"{fmt(t.player_qte, 1):>5} {fmt(t.opponent_qte, 1):>5}  "
                    f"{fmt(t.player_dp, 1):>7} {fmt(t.opponent_dp, 1):>7}  "
                    f"{fmt(cum_p, 1):>7} {fmt(cum_o, 1):>7}\n"
                    f"  {'':>2}  {'Heat:':>12} {p_heat}  |  {o_heat}\n")
        f.write("\n" + "=" * 72 + "\n")
    print(f"  [Log saved to {filename}]")


def print_turn_condensed(t: TurnResult, player_name: str = "P", opponent_name: str = "O") -> None:
    p_s = _cards_label(t.player_stances)
    o_s = _cards_label(t.opponent_stances)
    battle = _battle_icon(t.battle_winner, player_name)
    outcomes = _outcome_icon(t.battle_outcomes) if t.battle_outcomes else ""
    print(f"  T{t.turn_number:>2} | {p_s:>12} vs {o_s:<12} | {battle:>15} | "
          f"{outcomes} | Prog {fmt(t.player_progress or t.player_dp,1)}-{fmt(t.opponent_progress or t.opponent_dp,1)}")


def print_turn_verbose(t: TurnResult, player_name: str = "P", opponent_name: str = "O") -> None:
    p_s = _cards_label(t.player_stances)
    o_s = _cards_label(t.opponent_stances)
    battle = _battle_icon(t.battle_winner, player_name)
    outcomes = _outcome_icon(t.battle_outcomes) if t.battle_outcomes else ""
    print(f"\n  \u2500\u2500 Turn {t.turn_number}  {p_s} vs {o_s}  |  Battle: {battle} ({outcomes}) \u2500\u2500")
    print(f"  Progress:     {player_name}={fmt(t.player_progress or t.player_dp, 4)}  {opponent_name}={fmt(t.opponent_progress or t.opponent_dp, 4)}")
    for entry in t.trace:
        cat = entry["category"]
        label = entry["label"]
        value = entry["value"]
        formula = entry.get("formula", "")
        fstr = f"    [{cat:>8}] {label:30s} = {value}"
        if formula:
            fstr += f"  ({formula})"
        print(fstr)


def print_result(result: MatchResult, verbose: bool = False) -> None:
    print("\n" + "=" * 72)
    print("  MATCH SUMMARY")
    print("=" * 72)
    print(f"  {result.player_name} vs {result.opponent_name}")
    print(f"  Turns: {result.turns_played}/{result.total_turns}")
    print(f"  Result: {result.winner} (Decision)")
    print(f"  Position: {result.player_name}={result.player_position*100:.0f}%  "
          f"{result.opponent_name}={result.opponent_position*100:.0f}%")
    print(f"  Progress:  {result.player_name}={fmt(result.player_total_progress or result.player_total_dp, 1)}  "
          f"{result.opponent_name}={fmt(result.opponent_total_progress or result.opponent_total_dp, 1)}")
    print("\n  \u2500\u2500 Turn Breakdown \u2500\u2500")
    print(f"  {'T':>2} {'P-Picks':>12} {'O-Picks':<12} {'Battle':>15}  {'P_DP':>7} {'O_DP':>7}  "
          f"{'Cum_P':>7} {'Cum_O':>7}")
    print("  " + "-" * 82)
    cum_p = 0.0
    cum_o = 0.0
    for t in result.turn_results:
        cum_p += t.player_dp
        cum_o += t.opponent_dp
        p_picks = _cards_label(t.player_stances)
        o_picks = _cards_label(t.opponent_stances)
        p_heat = _heat_label(t.player_heat_fill, t.player_locked)
        o_heat = _heat_label(t.opponent_heat_fill, t.opponent_locked)
        battle = _battle_icon(t.battle_winner, result.player_name)
        print(f"  {t.turn_number:>2}  {p_picks:>12} {o_picks:<12}  {battle:>14}  "
              f"{fmt(t.player_dp, 1):>7} {fmt(t.opponent_dp, 1):>7}  "
              f"{fmt(cum_p, 1):>7} {fmt(cum_o, 1):>7}")
        print(f"  {'':>2}  {'Heat:':>12} {p_heat}  |  {o_heat}")
    if verbose:
        for t in result.turn_results:
            print_turn_verbose(t, result.player_name, result.opponent_name)
    print("=" * 72)


def _float(prompt: str, lo: float, hi: float, default: float | None = None) -> float:
    while True:
        label = f"{prompt} [{lo}-{hi}]"
        if default is not None:
            label += f" (default: {default})"
        label += ": "
        raw = input(label).strip()
        if not raw and default is not None:
            return default
        try:
            val = float(raw)
            if lo <= val <= hi:
                return val
            print(f"  Must be between {lo} and {hi}.")
        except ValueError:
            print("  Invalid number.")


def _int(prompt: str, lo: int, hi: int, default: int | None = None) -> int:
    while True:
        label = f"{prompt} [{lo}-{hi}]"
        if default is not None:
            label += f" (default: {default})"
        label += ": "
        raw = input(label).strip()
        if not raw and default is not None:
            return default
        try:
            val = int(raw)
            if lo <= val <= hi:
                return val
            print(f"  Must be between {lo} and {hi}.")
        except ValueError:
            print("  Invalid integer.")


def _choose(prompt: str, options: list[str], default: int = 0) -> int:
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input(f"Choice [1-{len(options)}] (default: {default}): ").strip()
        if not raw:
            return default
        try:
            val = int(raw)
            if 1 <= val <= len(options):
                return val
        except ValueError:
            pass
        print(f"  Enter 1-{len(options)}.")


def _str(prompt: str, default: str = "") -> str:
    raw = input(f"{prompt}: ").strip()
    if not raw and default:
        return default
    return raw or "Unknown"


def _load_sample_builds() -> dict:
    import json, os
    path = os.path.join(os.path.dirname(__file__), "..", "config", "sample_builds.json")
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"player_builds": []}


def _lap_count(encounter_type: str) -> int:
    return ENCOUNTER_PHASES.get(encounter_type, 1)


def _lap_turns(encounter_type: str) -> int:
    return ENCOUNTER_LAP_SIZES.get(encounter_type, 5)


def setup_match() -> MatchConfig:
    print("=" * 56)
    print("  VELOCITY SHIFT \u2014 COMBAT ENGINE")
    print("=" * 56)

    builds = _load_sample_builds()
    has_presets = bool(builds.get("player_builds"))

    # ── 1. Pick player build ──
    if has_presets and _choose("Use preset player build?", ["Yes", "No (manual entry)"], 1) == 1:
        pb_list = builds["player_builds"]
        pb_labels = [f"{b['name']}  ({b['archetype']} L{b['level']})" for b in pb_list]
        p_choice = _choose("Select player build", pb_labels + ["Custom (manual entry)"], 1)
        if p_choice <= len(pb_list):
            pb = pb_list[p_choice - 1]
            player_name = pb["name"]
            player_level = pb["level"]
            pow_p, en_p, han_p = build_stats(pb["archetype"], player_level)
            print(f"  \u2192 {pb['name']}: POW={fmt(pow_p,0)} EN={fmt(en_p,0)} HAN={fmt(han_p,0)}")
        else:
            player_name = _str("Player name", "Player")
            player_level = 1
            print("\n--- Player Stats ---")
            pow_p = _float("POW", 0, 1e9)
            en_p = _float("EN", 0, 1e9)
            han_p = _float("HAN", 0, 1e9)
    else:
        player_name = _str("Player name", "Player")
        player_level = 1
        print("\n--- Player Stats ---")
        pow_p = _float("POW", 0, 1e9)
        en_p = _float("EN", 0, 1e9)
        han_p = _float("HAN", 0, 1e9)

    # ── 2. Pick encounter type ──
    laps_w = _lap_count("wild")
    laps_l = _lap_count("lieutenant")
    laps_b = _lap_count("boss")
    tw = _lap_turns("wild")
    tl = _lap_turns("lieutenant")
    tb = _lap_turns("boss")
    enc_options = [
        f"Wild Encounter ({laps_w} lap \u00d7 {tw} turns, ratio {ENCOUNTER_RATIOS['wild']})",
        f"Lieutenant Challenge ({laps_l} laps \u00d7 {tl} turns, ratio {ENCOUNTER_RATIOS['lieutenant']})",
        f"Boss Encounter ({laps_b} laps \u00d7 {tb} turns, ratio {ENCOUNTER_RATIOS['boss']})",
    ]
    enc_choice = _choose("Select encounter type", enc_options, 2)
    enc_keys = ["wild", "lieutenant", "boss"]
    encounter_type = enc_keys[enc_choice - 1]
    opp_level = max(1, round(player_level * ENCOUNTER_RATIOS[encounter_type]))
    max_turns = ENCOUNTER_MAX_TURNS[encounter_type]
    laps = _lap_count(encounter_type)
    print(f"  \u2192 {ENCOUNTER_LABELS[encounter_type]}: opponent level {opp_level}, {laps} lap(s), {max_turns} turns")

    # ── 3. Pick opponent archetype ──
    arch_list = list(ARCHETYPES.keys())
    arch_choice = _choose("Select opponent archetype", arch_list, 4)
    opponent_archetype = arch_list[arch_choice - 1]
    pow_o, en_o, han_o = build_stats(opponent_archetype, opp_level)
    opponent_name = f"{opponent_archetype} Rival"
    print(f"  \u2192 {opponent_name}: POW={fmt(pow_o,0)} EN={fmt(en_o,0)} HAN={fmt(han_o,0)}")

    # ── 4. Seed, verbosity ──
    seed_raw = input("Random seed (optional, empty for none): ").strip()
    seed = int(seed_raw) if seed_raw else None

    detechoice = _choose("Mode:", ["Deterministic (seeded)", "Random (true RNG)"], 1)
    deterministic = detechoice == 1

    verbchoice = _choose("Debug verbosity:", ["Condensed", "Verbose (full trace)"], 1)
    verbose = verbchoice == 2


    player_stats = CombatantStats(
        name=player_name, pow=pow_p, en=en_p, han=han_p,
        level=player_level,
    )
    opponent_stats = CombatantStats(
        name=opponent_name, pow=pow_o, en=en_o, han=han_o,
        level=opp_level,
    )

    # ── 5. District and track (line tables) ──
    dist_list = list(DISTRICTS)
    d_choice = _choose("Select district", dist_list, 1)
    district = dist_list[d_choice - 1]
    tracks = official_tracks()[district.lower()]
    track_names = list(tracks)
    t_choice = _choose(f"Select {district} track", track_names, 1)
    track_name = track_names[t_choice - 1]
    corners = list(tracks[track_name])
    print(f"  → {district} / {track_name}: {'-'.join(corners)}")

    return MatchConfig(
        player_stats=player_stats,
        opponent_stats=opponent_stats,
        max_turns=max_turns,
        seed=seed,
        deterministic=deterministic,
        verbose=verbose,
        rival_personality=opponent_archetype,
        encounter_type=encounter_type,
        district=district,
        corners=corners,
    )


OUTCOME_ICONS = {StanceOutcome.WIN: "\u2713", StanceOutcome.DRAW: "\u2014", StanceOutcome.LOSS: "\u2717"}


def prompt_stance(ctx: ClashContext, who: str) -> Stance:
    """Prompt the player for one stance. Locked gauges cannot be picked; overrun picks show their payoff."""
    pos_names = ["Entry", "Apex", "Exit"]
    pos_name = pos_names[ctx.clash_index] if ctx.clash_index < 3 else f"slot {ctx.clash_index+1}"
    g = ctx.gauges
    for prev in ctx.previous_clashes:
        icon = OUTCOME_ICONS[prev.outcome]
        print(f"    Clash {prev.clash_index+1}: {_stance_label(prev.player_stance)} vs "
              f"{_stance_label(prev.opponent_stance)} \u2192 {icon}")
    print(f"  {who} heat: {_heat_label(g.fill(), g.locked)}")
    options = []
    for s_ in (Stance.POW, Stance.HAN, Stance.EN):
        if g.selectable(s_):
            m = g.mult_if(s_, ctx.corner)
            options.append((s_, f"{s_.value}" + (f" (overrun x{m:.2f})" if m < 1.0 else "")))
    available = ", ".join(f"{i+1}:{lbl}" for i, (_, lbl) in enumerate(options))
    while True:
        raw = input(f"  {ctx.corner} {pos_name} [{available}]: ").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
        except ValueError:
            pass
        print("  Invalid choice.")


def prompt_qte(turn: int, who: str) -> tuple[float, float, float]:
    """Prompt Entry/Apex/Exit scores (1-10). Blank / unplayed is 0 (Austin).

    The three raw scores (already /10) are averaged in match.py into the
    turn's single raw_qte; clash math is unchanged.
    """
    scores: list[float] = []
    for phase in QTE_PHASES:
        label = phase.capitalize()
        while True:
            raw = input(
                f"  [Turn {turn}] {who} {label} QTE score (1-10, blank=0): "
            ).strip()
            if raw == "":
                scores.append(0.0)
                break
            try:
                val = float(raw)
                if 1.0 <= val <= 10.0:
                    scores.append(qte_factor(val))
                    break
                print("  Must be between 1 and 10, or blank for unplayed (0).")
            except ValueError:
                print("  Invalid number.")
    return (scores[0], scores[1], scores[2])


def run_cli() -> None:
    cfg = setup_match()
    trace = TraceLogger()
    pn = cfg.player_stats.name
    on = cfg.opponent_stats.name

    laps = _lap_count(cfg.encounter_type)
    print(f"\n  {pn} vs {on} ({laps} lap(s), max {cfg.max_turns} turns)")
    p_tot = cfg.player_stats.pow + cfg.player_stats.en + cfg.player_stats.han
    o_tot = cfg.opponent_stats.pow + cfg.opponent_stats.en + cfg.opponent_stats.han
    r = p_tot / o_tot if o_tot else 1.0
    zw = qte_zone_width(r, cfg.qte_window_mod)
    print(f"  QTE zone: {zw:.2f} × default ({zw * QTE_ZONE_BASE_MS:.0f} ms at r={r:.4f}); "
          f"enter an Entry, Apex, and Exit score (blank = unplayed = 0); "
          f"the turn uses their average as the raw hit quality at this zone")
    print("  Heat: POW = engine, HAN = suspension, EN = brakes/tires. A full gauge locks (L) until it cools.")

    def get_player_stance(turn: int, clash_index: int, ctx: ClashContext) -> Stance:
        return prompt_stance(ctx, pn)

    def get_player_qte(turn: int):
        return prompt_qte(turn, pn)

    def _on_turn_start(turn: int, corner: str, p_heat, o_heat) -> None:
        print(f"\n  \u2694 Turn {turn} \u2014 corner {corner} \u2694")

    def _on_clash_resolved(turn: int, clash_index: int,
                           p_s: Stance, o_s: Stance, outcome: StanceOutcome) -> None:
        icon = OUTCOME_ICONS[outcome]
        print(f"  \u2192 {_stance_label(p_s)} vs {_stance_label(o_s)} \u2192 {icon}")

    def _on_clashes_complete(turn: int, clash_history: list[ClashResult]) -> None:
        outcome_strs = []
        for cr in clash_history:
            icon = OUTCOME_ICONS[cr.outcome]
            outcome_strs.append(f"{_stance_label(cr.player_stance)} vs {_stance_label(cr.opponent_stance)} {icon}")
        print(f"  Clashes: {' | '.join(outcome_strs)}")

    def _on_turn(turn: int, t: TurnResult, cum_p: float, cum_o: float) -> None:
        if cfg.verbose:
            print_turn_verbose(t, pn, on)
        else:
            print_turn_condensed(t, pn, on)
        total = cum_p + cum_o
        p_pos = cum_p / total if total else 0.5
        o_pos = cum_o / total if total else 0.5
        print(f"         Share: {pn}={p_pos*100:.0f}%  {on}={o_pos*100:.0f}%  |  "
              f"Progress: {pn}={fmt(cum_p,1)}  {on}={fmt(cum_o,1)}")

    def _on_lap_complete(phase_index: int, total_phases: int) -> None:
        remaining = cfg.max_turns - (phase_index * _lap_turns(cfg.encounter_type))
        print(f"\n  \u2550" * 36)
        print(f"  Lap {phase_index + 1}/{total_phases} \u2014 {remaining} turns remaining")
        print(f"  \u2550" * 36)

    result = run_match(
        cfg,
        get_player_stance, get_player_qte,
        trace,
        on_turn_start=_on_turn_start,
        on_clash_resolved=_on_clash_resolved,
        on_turn_complete=_on_turn,
        on_lap_complete=_on_lap_complete,
        on_clashes_complete=_on_clashes_complete,
    )

    print_result(result, verbose=cfg.verbose)
    _write_log(result, cfg)

    print("\n  \u2500\u2500 Quick Reference \u2500\u2500")
    for t in result.turn_results:
        print_turn_condensed(t, pn, on)
