"""Smoke tests for the headless batch runner (velocity_shift/simulation.py).

Guards against the runner's card callbacks drifting from match.run_match's
call signature, which once crashed every simulated match.
"""
from velocity_shift.cars import build_stats
from velocity_shift.models import CombatantStats, MatchConfig
from velocity_shift.simulation import SimulationRunner, simulate_batch


def _cfg(encounter: str = "wild", seed: int = 1) -> MatchConfig:
    p = build_stats("Aggressive", 50)
    o = build_stats("Precise", 38)
    return MatchConfig(
        player_stats=CombatantStats("Player", *p, level=50),
        opponent_stats=CombatantStats("Opponent", *o, level=38),
        max_turns=10,
        seed=seed,
        encounter_type=encounter,
        rival_personality="Precise",
    )


def test_runner_completes_a_match():
    result = SimulationRunner(_cfg()).run()
    assert result.match.turns_played == 10
    assert result.match.winner in ("Player", "Opponent", "Tie")


def test_runner_is_reproducible_with_seed():
    a = SimulationRunner(_cfg(seed=7)).run().match
    b = SimulationRunner(_cfg(seed=7)).run().match
    assert a.player_total_dp == b.player_total_dp
    assert a.opponent_total_dp == b.opponent_total_dp


def test_simulate_batch_runs_variants():
    results = simulate_batch(_cfg(), [{"seed": 2}, {"encounter_type": "boss"}])
    assert len(results) == 3
