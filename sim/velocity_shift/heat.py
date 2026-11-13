from __future__ import annotations
"""Heat / load gauges (resources-v4b G2; Austin approved 2026-11-13).

Rules and constants: equations.py, "Heat / load resource system". This module
holds the parts that need the line tables and official tracks:

* load calibration: corner_demand -> track_wear -> avg_heat_demand (sets every
  gauge's capacity and recovery), same maths as resources-v4b (resources_v2
  corner_demand_q / track_wear, DEMAND_SLANT, TRACK_NORMALIZE);
* HeatGauges: one side's three gauges through a race;
* boss line weights by style (sim-only boss styles, PLACEHOLDER).

Arrays are in HEAT_ORDER (POW, HAN, EN), indexed with equations._STANCE_INDEX.
"""

import itertools
from functools import lru_cache
from typing import Sequence

from .models import Stance
from .equations import (
    CORNER_HEAT_COST, CORNER_HEAT_PASSIVE, HEAT_BASE_COST, HEAT_REPEAT_SURCHARGE,
    HEAT_CAP_TURNS, HEAT_RECOVERY, HEAT_RELEASE, HEAT_DEMAND_SLANT, HEAT_REF_Q,
    BOSS_HEAT_CAP_TURNS, BOSS_HEAT_RECOVERY, BOSS_HEAT_RELEASE, BOSS_HEAT_LOCK_ON_PASSIVE,
    BOSS_STYLE_BLEND, BOSS_HOT_SWITCH, BOSS_CONS_SWITCH, LIMP_MULT,
    heat_capacity, overrun_mult, counter_stance, loser_to_stance,
    _STANCE_INDEX, _INDEX_STANCE,
)
from .combat import line_triples, line_probs, parse_line, official_tracks, normalize_district

_EPS = 1e-9


def line_cost(line: Sequence[Stance], corner: str, wear: Sequence[float] = (1.0, 1.0, 1.0)) -> list[float]:
    """Per-clash load of a 3-stance line at `corner`, with the repeat surcharge and the track's wear."""
    seen = [0, 0, 0]
    out = []
    for s in line:
        i = _STANCE_INDEX[s]
        out.append(HEAT_BASE_COST * CORNER_HEAT_COST[corner][i] * wear[i] * (1 + HEAT_REPEAT_SURCHARGE * seen[i]))
        seen[i] += 1
    return out


@lru_cache(maxsize=None)
def corner_demand(district: str, corner: str, q: float = HEAT_REF_Q) -> tuple[float, float, float]:
    """Expected per-turn load (HEAT_ORDER, before wear) at one corner for a player with read skill q.

    Live read model vs the 65/21/14 line split: a correct read (prob q) plays the
    counters of the main line; a misread ties each clash with prob q, else loses.
    Exact over the 2^3 misread combinations; plus the corner's passive load.
    """
    district = normalize_district(district)
    tris = [parse_line(t) for t in line_triples(district, corner)]
    w = line_probs()
    d = list(CORNER_HEAT_PASSIVE[corner])
    rd = [counter_stance(s) for s in tris[0]]
    for s, c in zip(rd, line_cost(rd, corner)):
        d[_STANCE_INDEX[s]] += q * c
    for wl, ln in zip(w, tris):
        for combo in itertools.product((0, 1), repeat=3):
            p = 1.0
            for b in combo:
                p *= q if b else 1 - q
            mine = [s if b else loser_to_stance(s) for s, b in zip(ln, combo)]
            for s, c in zip(mine, line_cost(mine, corner)):
                d[_STANCE_INDEX[s]] += (1 - q) * wl * p * c
    return tuple(d)


def raw_track_demand(district: str, lap: Sequence[str], q: float = HEAT_REF_Q) -> tuple[float, float, float]:
    """Mean per-turn load of a lap before wear."""
    acc = [0.0, 0.0, 0.0]
    for k in lap:
        for i, v in enumerate(corner_demand(district, k, q)):
            acc[i] += v
    return tuple(a / len(lap) for a in acc)


def _official_laps() -> list[tuple[str, list[str]]]:
    out = []
    for d, tr in sorted(official_tracks().items()):
        for name in sorted(tr):
            out.append((d, list(tr[name])))
    return out


@lru_cache(maxsize=None)
def _avg_raw() -> tuple[float, float, float]:
    laps = _official_laps()
    acc = [0.0, 0.0, 0.0]
    for d, lap in laps:
        for i, v in enumerate(raw_track_demand(d, lap)):
            acc[i] += v
    return tuple(a / len(laps) for a in acc)


@lru_cache(maxsize=None)
def _track_wear(district: str, lap: tuple[str, ...]) -> tuple[float, float, float]:
    raw = raw_track_demand(district, lap)
    tot = sum(_avg_raw())
    rs = sum(raw)
    g = HEAT_DEMAND_SLANT
    return tuple(tot * ((1 - g) / 3 + g * x / rs) / x for x in raw)


def track_wear(district: str, lap: Sequence[str]) -> tuple[float, float, float]:
    """Per-gauge multiplier (HEAT_ORDER) on a lap's stance costs and passive load.

    Every lap asks the same total load as the official-track average (for a
    HEAT_REF_Q reader), and its mix is target_s = total x ((1-g)/3 + g x raw_s / raw_total),
    g = HEAT_DEMAND_SLANT. `lap` is the lap of corner codes (not the whole race).
    """
    return _track_wear(normalize_district(district), tuple(lap))


@lru_cache(maxsize=None)
def avg_heat_demand() -> tuple[float, float, float]:
    """Cross-track average per-turn load (HEAT_ORDER), after wear: sets capacity and recovery."""
    laps = _official_laps()
    acc = [0.0, 0.0, 0.0]
    for d, lap in laps:
        raw = raw_track_demand(d, lap)
        w = track_wear(d, lap)
        for i in range(3):
            acc[i] += raw[i] * w[i]
    return tuple(a / len(laps) for a in acc)


def build_shares(pow_stat: float, en_stat: float, han_stat: float) -> tuple[float, float, float]:
    """Build shares in HEAT_ORDER (POW, HAN, EN)."""
    tot = pow_stat + en_stat + han_stat
    if tot <= 0:
        return (1 / 3, 1 / 3, 1 / 3)
    return (pow_stat / tot, han_stat / tot, en_stat / tot)


class HeatGauges:
    """One side's three gauges (POW engine heat, HAN suspension load, EN brake/tire heat) for a race."""

    def __init__(self, shares: Sequence[float], r: float, wear: Sequence[float],
                 cap_turns: float = HEAT_CAP_TURNS, recovery: float = HEAT_RECOVERY,
                 release: float = HEAT_RELEASE, lock_on_passive: bool = True):
        self.cap, self.rec = heat_capacity(tuple(shares), r, avg_heat_demand(), cap_turns, recovery)
        self.release = release
        self.lock_on_passive = lock_on_passive
        self.wear = tuple(wear)
        self.load = [0.0, 0.0, 0.0]
        self.locked = [False, False, False]
        self.uses = [0, 0, 0]          # uses of each stance this turn (repeat surcharge)

    @classmethod
    def for_player(cls, pow_stat, en_stat, han_stat, r, wear) -> "HeatGauges":
        return cls(build_shares(pow_stat, en_stat, han_stat), r, wear)

    @classmethod
    def for_boss(cls, pow_stat, en_stat, han_stat, wear) -> "HeatGauges":
        """Boss gauges: v3 heat rules (BOSS_HEAT_*), r = 1."""
        return cls(build_shares(pow_stat, en_stat, han_stat), 1.0, wear,
                   BOSS_HEAT_CAP_TURNS, BOSS_HEAT_RECOVERY, BOSS_HEAT_RELEASE, BOSS_HEAT_LOCK_ON_PASSIVE)

    # ── queries
    def begin_turn(self) -> None:
        self.uses = [0, 0, 0]

    def cost(self, stance: Stance, corner: str) -> float:
        i = _STANCE_INDEX[stance]
        return HEAT_BASE_COST * CORNER_HEAT_COST[corner][i] * self.wear[i] * (1 + HEAT_REPEAT_SURCHARGE * self.uses[i])

    def selectable(self, stance: Stance) -> bool:
        return not self.locked[_STANCE_INDEX[stance]]

    def selectable_stances(self) -> list[Stance]:
        return [s for s in _INDEX_STANCE if self.selectable(s)]

    def all_locked(self) -> bool:
        return all(self.locked)

    def overrun_if(self, stance: Stance, corner: str) -> float:
        """Overrun fraction x if `stance` were played now (0 = within capacity)."""
        i = _STANCE_INDEX[stance]
        return max(0.0, self.load[i] + self.cost(stance, corner) - self.cap[i]) / self.cap[i]

    def mult_if(self, stance: Stance, corner: str) -> float:
        """Payoff multiplier if `stance` were played now (LIMP_MULT when all three are locked)."""
        if self.all_locked():
            return LIMP_MULT
        return overrun_mult(self.overrun_if(stance, corner))

    def fill(self) -> list[float]:
        """load / capacity per gauge (1.0 = full)."""
        return [l / c for l, c in zip(self.load, self.cap)]

    def least_loaded(self, only_unlocked: bool) -> Stance:
        best, bi = None, None
        for i in range(3):
            if only_unlocked and self.locked[i]:
                continue
            f = self.load[i] / self.cap[i]
            if best is None or f < best:
                best, bi = f, i
        return _INDEX_STANCE[bi]

    # ── updates
    def _lock_new(self) -> None:
        for i in range(3):
            if self.load[i] >= self.cap[i] - _EPS:
                self.locked[i] = True

    def play(self, stance: Stance, corner: str) -> tuple[float, float, bool]:
        """Play `stance` (caller checks it is selectable unless limping). Returns (payoff mult, overrun x, limp)."""
        limp = self.all_locked()
        i = _STANCE_INDEX[stance]
        if not limp and self.locked[i]:
            raise ValueError(f"{stance.value} is locked (gauge full); pick one of {[s.value for s in self.selectable_stances()]}")
        x = self.overrun_if(stance, corner)
        self.load[i] += self.cost(stance, corner)
        self.uses[i] += 1
        self._lock_new()
        return (LIMP_MULT if limp else overrun_mult(x)), (0.0 if limp else x), limp

    def end_turn(self, corner: str) -> None:
        """Passive corner load (can lock, unless lock_on_passive is False), recovery, then release
        below `release` x capacity."""
        for i in range(3):
            self.load[i] += CORNER_HEAT_PASSIVE[corner][i] * self.wear[i]
        if self.lock_on_passive:
            self._lock_new()
        for i in range(3):
            self.load[i] = max(0.0, self.load[i] - self.rec[i])
            if self.locked[i] and self.load[i] < self.release * self.cap[i] - _EPS:
                self.locked[i] = False


def boss_stance(gauges: HeatGauges, wanted: Stance) -> Stance:
    """Boss heat rule: play the line's stance; if its gauge is locked, the least-loaded unlocked one;
    if all three are locked, limp on the least-loaded gauge."""
    if gauges.all_locked():
        return gauges.least_loaded(only_unlocked=False)
    if gauges.selectable(wanted):
        return wanted
    return gauges.least_loaded(only_unlocked=True)


def boss_line_weights(district: str, corner: str, turn_index: int, race_length: int,
                      style: str = "balanced") -> tuple[float, float, float]:
    """Weights over [main, alt1, alt2] for this corner (0-based turn_index). PLACEHOLDER styles (sim only)."""
    base = line_probs()
    if style == "balanced":
        return base
    tris = [parse_line(t) for t in line_triples(district, corner)]
    costs = [sum(line_cost(t, corner)) for t in tris]
    cheap = sorted(range(3), key=lambda i: costs[i])        # stable, same as numpy argsort(kind="stable")
    dear = cheap[::-1]
    frac = turn_index / race_length
    if style == "hot_early":
        order = dear if frac < BOSS_HOT_SWITCH else cheap
    elif style == "conserver":
        order = cheap if frac < BOSS_CONS_SWITCH else dear
    else:
        raise ValueError(f"unknown boss style {style!r}")
    w0 = [0.0, 0.0, 0.0]
    for rank, li in enumerate(order):
        w0[li] = base[rank]
    b = BOSS_STYLE_BLEND
    return tuple((1 - b) * x + b * y for x, y in zip(base, w0))
