from __future__ import annotations
"""Headless batch runner for statistical analysis and balance testing.

Runs matches with a simulated player against the district line tables under
the heat/load gauges (resources-v4b G2, Austin approved 2026-11-13) and
exports results as JSON.

Simulated player (same model as resources-v4b `run_new`, mode "read"):
  * Read: each corner, with prob q_read the player reads the boss's line (it
    counters the most likely line, the main line for a balanced boss) and picks
    the selectable stance with the best value: V x Phi(outcome vs the guess) x
    stat weight x overrun multiplier - the boss's payoff - a pacing price.
    On a misread, each clash plays a tie vs the boss's actual stance with prob
    q_read, else the losing stance; if that gauge is locked, a random
    selectable stance.
  * Pacing ("reserve" rule, equations.PACE_*): on a paced turn a stance is
    priced when it would push its gauge past a soft ceiling, lowered when the
    next PACE_LOOKAHEAD corners need that gauge. The player paces on a share
    player_pacing of turns (default = q_read) and plays greedy otherwise.
  * q_read None (no quality set): a random selectable stance every clash.
"""

import json
import random
from dataclasses import dataclass, asdict
from typing import Callable

from .models import Stance, MatchConfig, MatchResult, ClashContext, CombatantStats
from .match import run_match, race_setup
from .combat import official_tracks, line_triples, parse_line, line_probs
from .equations import (
    OPPONENT_QTE, CORNER_HEAT_PASSIVE, STAT_M_W, PACE_RES_T, PACE_RES_K, PACE_RES_LOOK, PACE_LOOKAHEAD,
    raw_qte_score, clash_payoff, kappa_for_length, resolve_stance, counter_stance, loser_to_stance,
    _STANCE_INDEX, _INDEX_STANCE,
)
from .heat import track_wear, corner_demand, line_cost, boss_line_weights, build_shares
from .models import StanceOutcome


@dataclass
class SimulationResult:
    """A single simulation run's outcome and input snapshot."""
    match: MatchResult
    seed: int | None
    config_snapshot: dict


def _phi(q: float) -> tuple[float, float, float]:
    """Payoff by outcome index (loss, tie, win) at timing q."""
    return (clash_payoff(StanceOutcome.LOSS, q), clash_payoff(StanceOutcome.DRAW, q), clash_payoff(StanceOutcome.WIN, q))


class SimulationRunner:
    """Executes a single match with the simulated player (see module docstring)."""

    def __init__(self, cfg: MatchConfig):
        self.cfg = cfg
        self._rng = random.Random(None if cfg.seed is None else cfg.seed + 7_919)

    # ── skills
    def _play_quality(self) -> tuple[float, float] | None:
        """(q_read, q_time) for the simulated player, or None for the random player."""
        c = self.cfg
        if c.player_quality is None and c.player_read is None and c.player_timing is None:
            return None
        base = c.player_quality if c.player_quality is not None else 0.0
        read = c.player_read if c.player_read is not None else base
        timing = c.player_timing if c.player_timing is not None else base
        return read, timing

    def run(self) -> SimulationResult:
        c = self.cfg
        self._district, self._lap = race_setup(c)
        T = c.max_turns
        p, o = c.player_stats, c.opponent_stats
        p_tot = p.pow + p.en + p.han
        o_tot = o.pow + o.en + o.han
        r = p_tot / o_tot if o_tot else 1.0
        pq = self._play_quality()
        self._pq = pq
        if pq is not None:
            q_read, q_time = pq
            qt = raw_qte_score(r, profile=c.player_qte_profile,
                               q_time=None if c.player_qte_profile else q_time, window_mod=c.qte_window_mod)
            self._q_read = q_read
            self._pace_q = c.player_pacing if c.player_pacing is not None else q_read
            V = r ** kappa_for_length(T)
            php, pho = _phi(qt), _phi(OPPONENT_QTE)
            self._V, self._php, self._pho = V, php, pho
            self._d_lock = V * (php[2] - php[1]) + (pho[1] - pho[0])
            sh = build_shares(p.pow, p.en, p.han)
            self._mf = [1.0 + STAT_M_W * (x - 1 / 3) for x in sh]
            self._plan_race(T)
        result = run_match(
            c,
            self._pick_stance,
            lambda t: self._rng.uniform(0.1, 1.0),
            on_line_picked=self._on_line_picked,
        )
        return SimulationResult(match=result, seed=c.seed, config_snapshot=self._snapshot())

    # ── per-race plan: scouted guess per turn and the expected load of each turn
    def _plan_race(self, T: int) -> None:
        d, lap = self._district, self._lap
        wear = track_wear(d, lap)
        q = min(max(self._q_read, 0.0), 1.0)
        self._guess: list[list[Stance]] = []
        self._exp_load: list[list[float]] = []
        for t in range(T):
            k = lap[t % len(lap)]
            lines = [parse_line(x) for x in line_triples(d, k)]
            w = boss_line_weights(d, k, t, T, self.cfg.boss_style)
            guess = lines[max(range(3), key=lambda i: (w[i], -i))]
            self._guess.append(guess)
            need = [x * wi for x, wi in zip(corner_demand(d, k, q), wear)]
            pas = [x * wi for x, wi in zip(CORNER_HEAT_PASSIVE[k], wear)]
            readpart = [0.0, 0.0, 0.0]
            cl = [counter_stance(s) for s in guess]
            for s, x in zip(cl, line_cost(cl, k, wear)):
                readpart[_STANCE_INDEX[s]] += q * x
            read0 = [0.0, 0.0, 0.0]
            m0 = [counter_stance(s) for s in lines[0]]
            for s, x in zip(m0, line_cost(m0, k, wear)):
                read0[_STANCE_INDEX[s]] += q * x
            self._exp_load.append([readpart[i] + max(0.0, need[i] - pas[i] - read0[i]) + pas[i] for i in range(3)])

    def _on_line_picked(self, turn: int, corner: str, line: list[Stance]) -> None:
        self._actual = line
        if self._pq is not None:
            self._read = self._rng.random() < self._q_read
            self._pace_on = self._rng.random() < self._pace_q

    # ── stance choice
    def _pick_stance(self, turn: int, ci: int, ctx: ClashContext) -> Stance:
        g = ctx.gauges
        sel = g.selectable_stances()
        if self._pq is None:
            return self._rng.choice(sel)
        if not self._read:
            want = self._actual[ci] if self._rng.random() < self._q_read else loser_to_stance(self._actual[ci])
            return want if g.selectable(want) else self._rng.choice(sel)
        t = turn - 1
        guess = self._guess[t][ci]
        T = ctx.race_length
        short = [0.0, 0.0, 0.0]
        if self._pace_on and PACE_RES_LOOK > 0:
            end = min(T, t + 1 + PACE_LOOKAHEAD)
            fut = [0.0, 0.0, 0.0]
            for tt in range(t + 1, end):
                for i in range(3):
                    fut[i] += self._exp_load[tt][i]
            nf = max(1, end - (t + 1))
            short = [max(0.0, fut[i] - g.rec[i] * nf) / g.cap[i] for i in range(3)]
        best, best_s = None, None
        for s in _INDEX_STANCE:
            if not g.selectable(s):
                continue
            i = _STANCE_INDEX[s]
            o = resolve_stance(s, guess).value
            gain = self._V * self._php[o + 1] * g.mult_if(s, ctx.corner) * self._mf[i] - self._pho[-o + 1]
            if self._pace_on:
                t_eff = PACE_RES_T - PACE_RES_LOOK * short[i]
                over = ((g.load[i] + g.cost(s, ctx.corner)) / g.cap[i] - t_eff) / max(1 - t_eff, 0.05)
                gain -= PACE_RES_K * self._d_lock * max(0.0, over)
            if best is None or gain > best:
                best, best_s = gain, s
        return best_s

    def _snapshot(self) -> dict:
        return {
            "player": asdict(self.cfg.player_stats),
            "opponent": asdict(self.cfg.opponent_stats),
            "max_turns": self.cfg.max_turns,
            "seed": self.cfg.seed,
            "player_quality": self.cfg.player_quality,
            "player_read": self.cfg.player_read,
            "player_timing": self.cfg.player_timing,
            "player_pacing": self.cfg.player_pacing,
            "player_qte_profile": self.cfg.player_qte_profile,
            "qte_window_mod": self.cfg.qte_window_mod,
            "district": self._district,
            "corners": list(self._lap),
            "boss_style": self.cfg.boss_style,
        }


def simulate_win_rate(
    district: str,
    r: float,
    q: float,
    length: int,
    seed: int,
    n_per_track: int = 200,
    opp_total: float = 300.0,
    shares: tuple[float, float, float] | None = None,
    q_time: float | None = None,
    pacing: float | None = None,
    boss_style: str = "balanced",
    track_names: list[str] | None = None,
) -> float:
    """Win rate (%) of a SimulationRunner batch on a district's official tracks.

    Player total = r * opp_total split by `shares` (POW, HAN, EN; default even),
    even opponent, q_read = q, timing q_time (default q) at the visible zone for
    that r, pacing share `pacing` (default q). Ties count as a half-win.
    Seeds are spaced so tracks and races do not share nearby seeds.
    """
    tracks = official_tracks()[district.lower()]
    names = track_names or list(tracks)
    sp, sh, se = shares or (1 / 3, 1 / 3, 1 / 3)
    tot = opp_total * r
    player = CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50)
    o_stat = opp_total / 3.0
    opponent = CombatantStats(name="Opponent", pow=o_stat, en=o_stat, han=o_stat, level=50)
    wins = ties = n = 0
    for ti, name in enumerate(names):
        corners = list(tracks[name])
        for k in range(n_per_track):
            cfg = MatchConfig(
                player_stats=player,
                opponent_stats=opponent,
                max_turns=length,
                seed=seed + length * 1_000_000 + ti * 10_000 + k,
                district=district,
                corners=corners,
                player_read=q,
                player_timing=q if q_time is None else q_time,
                player_pacing=pacing,
                boss_style=boss_style,
                encounter_type="boss",
            )
            m = SimulationRunner(cfg).run().match
            if m.player_total_progress > m.opponent_total_progress:
                wins += 1
            elif m.player_total_progress == m.opponent_total_progress:
                ties += 1
            n += 1
    return 100.0 * (wins + 0.5 * ties) / n


def simulate_batch(
    base_cfg: MatchConfig,
    variants: list[dict] | None = None,
) -> list[SimulationResult]:
    results = []
    cfgs = [base_cfg]
    if variants:
        import copy
        for v in variants:
            cfg = copy.deepcopy(base_cfg)
            for key, val in v.items():
                setattr(cfg, key, val)
            cfgs.append(cfg)
    for cfg in cfgs:
        results.append(SimulationRunner(cfg).run())
    return results


def export_results(results: list[SimulationResult], path: str) -> None:
    data = []
    for r in results:
        entry = {
            "seed": r.seed,
            "config": r.config_snapshot,
            "winner": r.match.winner,
            "player_position": round(r.match.player_position, 4),
            "opponent_position": round(r.match.opponent_position, 4),
            "turns_played": r.match.turns_played,
            "player_total_progress": round(r.match.player_total_progress, 4),
            "opponent_total_progress": round(r.match.opponent_total_progress, 4),
            "turns": [
                {
                    "turn": t.turn_number,
                    "corner": t.corner_type,
                    "player_stances": [s.value for s in t.player_stances],
                    "opponent_stances": [s.value for s in t.opponent_stances],
                    "player_progress": round(t.player_progress, 4),
                    "opponent_progress": round(t.opponent_progress, 4),
                    "player_heat_mults": [round(x, 4) for x in t.player_heat_mults],
                    "player_heat_fill": [round(x, 4) for x in t.player_heat_fill],
                    "player_locked": t.player_locked,
                }
                for t in r.match.turn_results
            ],
        }
        data.append(entry)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
