"""Line-table picks in combat.py / match.py must follow LINE_SET_C.

The rule matches lines-v1 / the winrate_n4000.json rebuild: one categorical
draw per corner among [main, alt1, alt2] with probabilities line_probs().
"""
from collections import Counter
from random import Random

from velocity_shift.combat import (
    LETTER_TO_STANCE, line_probs, line_triples, parse_line, pick_line,
    official_tracks, track_corners, corner_at_turn,
)
from velocity_shift.equations import LINE_SET_C, LINE_ADHERENCE, LINE_ALT_WEIGHTS
from velocity_shift.models import Stance, CombatantStats, MatchConfig
from velocity_shift.match import run_match


def _p_pick(turn, clash_index, ctx):
    return ctx.gauges.selectable_stances()[0]


def test_line_probs_match_adherence_and_alt_weights():
    a = LINE_ADHERENCE
    w = LINE_ALT_WEIGHTS
    pr = line_probs()
    assert pr[0] == a
    assert abs(pr[1] - (1 - a) * w["alt1"]) < 1e-12
    assert abs(pr[2] - (1 - a) * w["alt2"]) < 1e-12
    assert abs(sum(pr) - 1.0) < 1e-12
    # Gordon's two-step wording is the same distribution: 0.65 / 0.21 / 0.14
    assert abs(pr[0] - 0.65) < 1e-12
    assert abs(pr[1] - 0.21) < 1e-12
    assert abs(pr[2] - 0.14) < 1e-12


def test_pick_line_is_always_a_table_triple():
    rng = Random(0)
    for district, corners in LINE_SET_C.items():
        for cn, triples in corners.items():
            allowed = {tuple(parse_line(s)) for s in triples}
            for _ in range(50):
                line = tuple(pick_line(district, cn, rng))
                assert line in allowed
            # Title-case district names used by progression also work
            line = tuple(pick_line(district.title(), cn, Random(1)))
            assert line in allowed


def test_pick_line_frequencies_match_weights():
    rng = Random(20261113)
    n = 20_000
    triples = line_triples("street", "N90")
    # Street N90 after lines-v1 S-A: HHP / HEH / HHH
    assert triples == ["HHP", "HEH", "HHH"]
    counts = Counter()
    for _ in range(n):
        line = "".join({v: k for k, v in LETTER_TO_STANCE.items()}[s] for s in pick_line("street", "N90", rng))
        counts[line] += 1
    pr = line_probs()
    for triple, p in zip(triples, pr):
        assert abs(counts[triple] / n - p) < 0.015, (triple, counts[triple] / n, p)


def test_run_match_plays_table_lines_and_skips_personality():
    corners = track_corners("street", 0)
    assert corners[0] == "N90"
    cfg = MatchConfig(
        player_stats=CombatantStats(name="P", pow=100, en=100, han=100, level=10),
        opponent_stats=CombatantStats(name="O", pow=100, en=100, han=100, level=10),
        max_turns=10,
        seed=20261113,
        district="Street",
        corners=corners,
        rival_personality="Aggressive",  # must be ignored for opponent cards
    )
    result = run_match(cfg, _p_pick, lambda t: 1.0)
    assert result.turns_played == 10
    for t, turn in enumerate(result.turn_results, start=1):
        cn = corner_at_turn(corners, t)
        assert turn.corner_type == cn
        allowed = {tuple(parse_line(s)) for s in line_triples("street", cn)}
        assert tuple(turn.opponent_line) in allowed
        # The boss plays its line unless that gauge is locked (heat.boss_stance swaps it);
        # turn 1 starts cold, so there it plays the line exactly.
        if t == 1:
            assert turn.opponent_stances == list(turn.opponent_line)


def test_run_match_line_picks_ignore_archetype():
    """Same seed and track must yield the same opponent lines regardless of personality."""
    corners = track_corners("wangan", 0)
    def run(personality: str):
        cfg = MatchConfig(
            player_stats=CombatantStats(name="P", pow=100, en=100, han=100, level=10),
            opponent_stats=CombatantStats(name="O", pow=100, en=100, han=100, level=10),
            max_turns=10,
            seed=7,
            district="wangan",
            corners=corners,
            rival_personality=personality,
        )
        return run_match(cfg, _p_pick, lambda t: 0.5)

    a = run("Aggressive")
    b = run("Precise")
    for ta, tb in zip(a.turn_results, b.turn_results):
        assert ta.opponent_line == tb.opponent_line
        assert ta.opponent_stances == tb.opponent_stances


def test_official_tracks_match_winrate_layouts():
    tracks = official_tracks()
    assert set(tracks) == {"touge", "wangan", "street"}
    for d, named in tracks.items():
        assert len(named) == 5
        for seq in named.values():
            assert len(seq) == 10
            for cn in seq:
                assert cn in LINE_SET_C[d]
