"""mod_skill progression (LIVE: Austin approved 2026-11-19, "Approved for all").

Car = the fixed stock car (E.MS_STOCK_POINTS = 3000 car points) plus the EARNED points of its 4 mod slots. Race XP goes
into owned slots up to the slot's Mk ceiling (E.MS_TIER_POINTS); points re-assign freely across POW/HAN/EN at Reiko's.
XP with no room is lost from the car but still counts in the earned-XP LEDGER, which is what the crew FLOORS check
(E.MS_FLOOR_POINTS). Crew members are stat-locked (E.MS_CREW_BUDGET, via E.opponent_budget). Per round: 7 story races +
6 required wild encounters (13 mandatory); non-mandatory wins pay a wild encounter's XP for the first E.MS_NM_XP_CAP
wins of the round, cash only after that. Mods are bought at the mods-v1 prices and unlocks (E.MOD_SETS: Mk1 at round
open, Mk2 after the mat1 win, Mk3 after the mat2 win); 65 % of each purse pays the debt while it is open.
Constants: equations.py "mod_skill progression". Targets: E.MS_TARGETS (design/07-economy-and-mods.md)."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import equations as E
from .combat import official_tracks
from .models import CombatantStats, MatchConfig

DISTRICTS = tuple(d.lower() for d in E.ROUND_DISTRICTS)
RUNGS = E.LADDER_RUNGS                                   # kid1 .. boss
_KIND = dict(zip(E.LADDER_RUNGS, E.LADDER_RUNG_KIND))


def rung_index(rung: str | int) -> int:
    return rung if isinstance(rung, int) else RUNGS.index(rung)


def crew_budget(rnd: int, rung: str | int) -> float:
    """Stat total (stat units) of round index `rnd`'s crew member at `rung`."""
    return E.opponent_budget(rnd, rung_index(rung))


def floor_points(rnd: int, rung: str | int) -> int:
    return E.MS_FLOOR_POINTS[DISTRICTS[rnd]][rung_index(rung)]


def can_challenge(ledger_points: float, rnd: int, rung: str | int) -> bool:
    """Stat-lock floor: the earned-XP ledger (stock + every point of race XP earned, assigned or not) must reach the floor."""
    return ledger_points >= floor_points(rnd, rung) - 1e-9


def story_xp(rnd: int, rung: str | int) -> int:
    return E.MS_STORY_XP[rnd][rung_index(rung)]


def nm_xp(rnd: int, nm_xp_wins_this_round: int) -> int:
    """XP of a non-mandatory win: a wild encounter's XP while under the per-round cap, else 0 (cash only)."""
    return E.MS_WILD_XP[rnd] if nm_xp_wins_this_round < E.MS_NM_XP_CAP else 0


def mandatory_sequence(rnd: int) -> list[str]:
    """The round's 13 mandatory races in order: required wild encounters ("wild") before each rung after kid1."""
    seq: list[str] = []
    for j, rung in enumerate(RUNGS):
        seq += ["wild"] * E.MS_REQUIRED_WILDS[j] + [rung]
    return seq


def mandatory_path_points() -> dict[str, tuple[int, ...]]:
    """Earned points on arrival at each rung with mandatory wins only (this is how MS_FLOOR_POINTS is defined)."""
    out, pts = {}, E.MS_STOCK_POINTS
    for rnd, d in enumerate(DISTRICTS):
        row = []
        for k in mandatory_sequence(rnd):
            if k == "wild":
                pts += E.MS_WILD_XP[rnd]
            else:
                row.append(pts); pts += story_xp(rnd, k)
        out[d] = tuple(row)
    return out


def tier_ceiling(group_rnd: int, mk: int) -> int:
    """Earned-point ceiling of a slot holding round `group_rnd`'s Mk`mk` (1-3)."""
    return E.MS_TIER_POINTS[group_rnd][mk - 1]


def mod_price(group_rnd: int, mk: int, wholesale: bool = False) -> float:
    return E.mod_price(f"MOD_R{group_rnd + 1}_POW_MK{mk}", wholesale=wholesale)


def unlocked_mk(rnd: int, wins: set) -> int:
    """Highest Mk of round `rnd`'s group that is unlocked, given the ladder wins so far as {(rnd, rung)} (round open = Mk1)."""
    return 3 if (rnd, "mat2") in wins else 2 if (rnd, "mat1") in wins else 1


@dataclass
class Garage:
    """One car's mod slots, cash, debt and earned-XP ledger. Slot = [group round index, mk, earned points] or None."""
    district: str = "street"
    slots: list = field(default_factory=lambda: [None] * E.MOD_SLOTS)
    money: float = 0.0
    debt: float = E.DEBT_AMOUNT
    ledger: float = float(E.MS_STOCK_POINTS)
    spent: float = 0.0
    lost: float = 0.0

    def points(self) -> float:
        return E.MS_STOCK_POINTS + sum(s[2] for s in self.slots if s)

    def credit(self, purse: float) -> None:
        take = min(self.debt, E.DEBT_SHARE * purse) if self.debt > 0 else 0.0
        self.debt -= take; self.money += purse - take

    def shop(self, rnd: int, max_mk: int, wholesale: bool = False) -> None:
        """Buy the cheapest available upgrade (round `rnd`'s group, up to `max_mk`) while cash allows; earned points carry."""
        while True:
            opts = []
            for i, s in enumerate(self.slots):
                g, mk = (s[0], s[1]) if s else (-1, 0)
                nxt = (rnd, 1) if g < rnd else (g, mk + 1)
                if nxt[1] <= max_mk and nxt[0] == rnd:
                    opts.append((mod_price(*nxt, wholesale=wholesale), i, nxt))
            if not opts:
                return
            price, i, (g, mk) = min(opts)
            if price > self.money + 1e-9:
                return
            self.money -= price; self.spent += price
            self.slots[i] = [g, mk, self.slots[i][2] if self.slots[i] else 0.0]

    def assign(self, xp: float) -> float:
        """Add race XP to the ledger and to owned slots with room (most room first, spilling); returns the XP lost."""
        self.ledger += xp
        for s in sorted((s for s in self.slots if s), key=lambda s: s[2] - tier_ceiling(s[0], s[1])):
            room = tier_ceiling(s[0], s[1]) - s[2]
            if room > 0 and xp > 0:
                t = min(room, xp); s[2] += t; xp -= t
        self.lost += xp
        return xp


def crew_config(rnd: int, rung: str | int, player_points: float, *, corners: list | None = None, **kw) -> MatchConfig:
    """MatchConfig for a crew race: player on the district tune at `player_points` car points, the stat-locked crew member
    (boss shape for the boss), the rung's race length, and the Street boss's per-race stat weight. Default track: the
    district's hardest live track (E.BOSS_HARD_TRACK), the track the targets were measured on."""
    j = rung_index(rung); d = DISTRICTS[rnd]
    sp, sh, se = E.DISTRICT_TUNE[d]; tot = player_points / 10.0
    bp, bh, be = E.BOSS_STAT_SHARES[d] if j == 6 else (1 / 3, 1 / 3, 1 / 3)
    b = crew_budget(rnd, j)
    return MatchConfig(
        player_stats=CombatantStats(name="Player", pow=tot * sp, en=tot * se, han=tot * sh, level=50),
        opponent_stats=CombatantStats(name="Opponent", pow=b * bp, en=b * be, han=b * bh, level=50),
        max_turns=E.LADDER_TURNS[j], district=d, encounter_type="boss",
        corners=list(corners or official_tracks()[d][E.BOSS_HARD_TRACK[d]]),
        kappa_mult=E.MS_BOSS_KAPPA_MULT[d] if j == 6 else 1.0, **kw)
