from __future__ import annotations
"""Pure mathematical functions for combat calculations.

All functions are stateless — no side effects, no mutable state.
Every formula is deterministic given its inputs.

All game-rule constants live here as module-level names, NOT
per-encounter configurable parameters. To tune the game, change
these values and re-run.
"""

import math

from .models import Stance, StanceOutcome

# ── Game-rule constants (global knobs, not per-encounter) ──────────────

CLASH_STAKES = 0.35           # clash_mult = 1 ± CLASH_STAKES
BATTLE_BONUS = 0.05           # battle_mult bonus per win-margin point
MITIGATION_PER_1000 = 0.4     # EN reduction factor per 1000 EN
MITIGATION_FLOOR = 0.1        # minimum damage fraction (10 % always gets through)
HP_PER_LEVEL = 180            # max_hp = level × HP_PER_LEVEL
QTE_NORMALIZER = 10.0         # qte_factor = score / QTE_NORMALIZER
HAN_QTE_WEIGHT = 0.5         # shared modifier for both sides
RUBBER_BAND_FRACTION = 0.15  # full rubber-band at a DP gap of this × average max HP

# ── Simulated-player play quality (opt-in, MatchConfig.player_quality) ──
# q in [0, 1] = the fraction of the race the player "plays right".
#   * Card read: each clash, with probability q the player reads the
#     opponent's real pick and plays its counter (else a tie card, else
#     any card); otherwise the player picks a random card.
#   * QTE: each turn, with probability q the player hits PERFECT_QTE;
#     otherwise the score is uniform in [PLAYER_QTE_MIN, PLAYER_QTE_MAX].
# q = 0 reproduces the old random player exactly (random card, uniform QTE).
# The two parts are independent skills: MatchConfig.player_read (q_read,
# card read) and MatchConfig.player_timing (q_time, QTE). player_quality=q
# is shorthand for q_read = q_time = q.
PLAYER_QTE_MIN = 1.0
PLAYER_QTE_MAX = 10.0
PERFECT_QTE = 10.0


def qte_factor(qte_score: float) -> float:
    """Normalise a QTE score (1–10) to a 0.1–1.0 multiplier."""
    return qte_score / QTE_NORMALIZER


def apply_han_qte_mod(qte_score: float, han_pct: float) -> float:
    """Modify a QTE score by HAN proportion. Same formula for both sides.
    han_pct = han / (pow + en + han).
    Neutral at han_pct == 1/3, scales linearly with HAN_QTE_WEIGHT.
    """
    return qte_score * (1.0 + HAN_QTE_WEIGHT * (han_pct - 1 / 3))


def clash_mult(outcome: StanceOutcome) -> float:
    """Return the damage multiplier for a single clash result.

    * WIN    → 1 + CLASH_STAKES
    * NEUTRAL → 1.0
    * LOSS   → 1 - CLASH_STAKES
    """
    return 1.0 + CLASH_STAKES * outcome.value


def compute_damage(
    pow_stat: float,
    qte_factor: float,
    clash_mult: float,
    battle_mult: float,
) -> float:
    """Compute raw damage for one clash.

    Formula: max(0, POW × QTE_factor × clash_mult × battle_mult)
    """
    return max(0.0, pow_stat * qte_factor * clash_mult * battle_mult)


def damage_mitigation(en_stat: float, qte_factor: float) -> float:
    """Return the mitigation multiplier that reduces incoming damage.

    At least MITIGATION_FLOOR × 100 % of damage always gets through.
    Reduction = (EN / 1000) × MITIGATION_PER_1000 × QTE_factor
    """
    reduction = (en_stat / 1000.0) * MITIGATION_PER_1000 * qte_factor
    return max(MITIGATION_FLOOR, 1.0 - reduction)


def resolve_stance(a: Stance, b: Stance) -> StanceOutcome:
    """Resolve a single rock-paper-scissors clash between two stances.

    Rules:
        ATTACK > NEUTRAL > DEFEND > ATTACK
        Same stance → NEUTRAL
    """
    if a == b:
        return StanceOutcome.NEUTRAL
    if (a == Stance.ATTACK and b == Stance.NEUTRAL) or \
       (a == Stance.NEUTRAL and b == Stance.DEFEND) or \
       (a == Stance.DEFEND and b == Stance.ATTACK):
        return StanceOutcome.WIN
    return StanceOutcome.LOSS


# ══════════════════════════════════════════════════════════════════════
# Story race-balance + XP/level progression model (Barry, 2026-11-09)
# ══════════════════════════════════════════════════════════════════════
# Final settings from the final-v1 combat sweep and the grind-v1 v8c
# progression study (Austin's decisions of 2026-11-09). These drive the
# story ladder model in `progression.py` and its win-rate oracle
# (`config/winrate_n4000.json`, real N=4000 sim output). The turn-by-turn
# HP/DP combat in combat.py / match.py does NOT read these yet.
# All XP numbers are stand-ins pending playtest.

# ── Combat race-balance settings (final-v1) ──
# r = (player SP + mods) / opponent budget. Player-only QTE window:
# fraction of timing skill that lands, piecewise-linear in r (capped at 1).
KNOT_WINDOW_105 = ((0.80, 0.41), (0.85, 0.41), (0.90, 0.41), (0.95, 0.43), (1.00, 0.68), (1.05, 1.00))
KAPPA_BY_LENGTH = {10: 1.55, 20: 1.35, 30: 1.20}   # stat-gap leverage V = r**kappa, by race length (turns)
RACE_LENGTHS = (10, 20, 30)
SIM_SEEDS = (20261113, 20261114, 20261115)
OPPONENT_QTE = 1.0             # story-rung opponents time perfectly (uniform across rungs)
LINE_ADHERENCE = 0.65          # boss follows its district line with prob a; 1-a = bluff/deviation
LINE_ALT_WEIGHTS = {"alt1": 0.6, "alt2": 0.4}
# Line set C: per district, per corner type -> [main, alt1, alt2] lines, each "Entry Apex Exit"
# (D = Defend, S = Steady, A = Attack). Alternatives share main's Entry (unreadable at lock):
# alt1 switches Apex+Exit, alt2 switches Exit only. Mechanical stand-in.
# 2026-11-10 (lines-v1 S-A + W-A, Austin): Street N90 DDA -> SSA; Wangan SW and IR AAA -> AAD.
# Touge unchanged. In-world feel of the new lines pending Nathaniel's review.
LINE_SET_C = {
    "touge": {"HP": ["DSA", "DDS", "DSS"], "CR": ["SSA", "SDS", "SSS"], "DR": ["SDS", "SAD", "SDD"], "IR": ["SSA", "SDS", "SSS"],
              "N90": ["DSA", "DDS", "DSS"], "CH": ["SDA", "SAS", "SDS"], "ES": ["SSS", "SDD", "SSD"], "SW": ["SSA", "SDS", "SSS"]},
    "wangan": {"HP": ["DSA", "DDS", "DSS"], "CR": ["SAA", "SSS", "SAS"], "DR": ["DDS", "DAD", "DDD"], "IR": ["AAD", "ASA", "AAA"],
               "N90": ["DSA", "DDS", "DSS"], "CH": ["DSA", "DDS", "DSS"], "ES": ["SSS", "SDD", "SSD"], "SW": ["AAD", "ASA", "AAA"]},
    "street": {"HP": ["DDA", "DAS", "DDS"], "CR": ["DSD", "DDA", "DSA"], "DR": ["DDS", "DAD", "DDD"], "IR": ["SSA", "SDS", "SSS"],
               "N90": ["SSA", "SDS", "SSS"], "CH": ["DAA", "DSS", "DAS"], "ES": ["ASA", "ADS", "ASS"], "SW": ["DDD", "DAA", "DDA"]},
}
BUILD_STAT_MIN_SHARE = 0.25    # build bounds: each of POW/HAN/EN is 25–50 % of the total
BUILD_STAT_MAX_SHARE = 0.50

# ── Stat caps, reference rule, mods ──
SP_CAP_FRACTION = 0.80         # skill points cap at 80 % of the reference budget (= level cap)
MOD_CAP_FRACTION = 1.05        # SP + mods cap at 105 % of the reference budget before the finale
MOD_SHARE_OF_REF = 0.25        # mods available at a rung = 0.25 × reference (bought only, never earned)
REFERENCE_RULE = "V2"          # reference rises with each lieutenant win; crew boss = crew budget
MOD_TIMING = "c"               # mods unlock progressively with lieutenant wins
CLEAR_THRESHOLD = 50.0         # a rung is "clear" when average play (q 0.6) wins >= 50 % (midpoint of seed/length range)
AVERAGE_PLAY_Q = 0.6
GOOD_PLAY_Q = 0.8

# ── Story ladder (per crew: kid, kid, mature, mature, old head, old head, crew boss) ──
LADDER_RUNGS = ("kid", "kid", "mature", "mature", "old head", "old head", "crew boss")
LADDER_R = (1.13, 1.11, 1.10, 1.08, 1.07, 1.06, 1.05)   # target r at each rung's level cap
SCRIPTED_BUDGETS = {2: 218.2, 3: 224.3}                 # scripted races 2/3 (r 1.10 / 1.07 vs 240 SP)
SABINE_BUDGET = 300.0                                   # Option A base (scripted race 1 opponent)

# ── Option A budget steps: by round POSITION, not district ──
OPTION_A_CREW_STEP = 1.10      # every crew after the previous one
OPTION_A_ROUND_STEP = 1.30     # whichever crew OPENS Round 2 / Round 3
# Crew order is FREE within a round (Austin, 2026-11-10): the player picks any crew, is locked into its
# ladder until its boss falls, and rounds stay gated. Everything above (budget step, caps, story XP,
# taper) is keyed by PLAY POSITION in the round, never by district.
DISTRICTS = ("Touge", "Wangan", "Street")
DEFAULT_CREW_ORDER = {1: ("Touge", "Wangan", "Street"),
                      2: ("Wangan", "Street", "Touge"),
                      3: ("Street", "Touge", "Wangan")}   # one example play order, used for reports/tests only
# Unlock markers by (round, crews beaten in that round):
DEBT_CLEAR_AFTER = (2, 1)      # debt hits zero + aero unlocks after the first Round 2 crew's boss
BETTING_UNLOCK_AFTER = (2, 3)  # betting unlocks at the end of Round 2
FINALE_UNLOCK_AFTER = (3, 3)   # finale (and its big mods) unlocks after Round 3
FINALE = (("Myth #1", "Touge", 1086.8), ("Myth #2", "Wangan", 1195.5),
          ("Myth #3", "Street", 1315.0), ("Summit", "Touge", 1446.5))   # finale budgets (×1.10 steps)

# ── Level curve (GEO): SP(L) = 240 · 1.1^(L/12) ──
SP_START = 240.0
SP_GROWTH_PER_12_LEVELS = 1.10
XP_BASE = 100.0                # XP to go from level 0 to 1
XP_SP_EXPONENT = 1.5           # x(L) = XP_BASE · (SP(L-1)/240)^1.5 · s(L)/s(1): leveling gets harder

# ── Level-cap raises per win (front-loaded integer allocation of a crew's levels) ──
CAP_ALLOC_CREW = (2, 2, 3, 3, 1, 0, 1)          # ordinary crew (12 levels)
CAP_ALLOC_ROUND_OPEN = (12, 3, 3, 3, 1, 0, 0.5)   # first crew of R2/R3 (weights; [18,4,4,4,2,0,1] of 33). 2026-11-10: was
                                                 # (12,3,3,3,.5,.5,.5); lifts the opener's old head #2 skip-grind dip

# ── Story XP per win ──
STORY_XP_LT = 0.2              # lieutenant win = 0.2 × XP of the levels it unlocks (ordinary crew)
STORY_XP_LT_ROUND_OPEN = 0.4   # ... 0.4 × in a round-opening crew
STORY_XP_LT_FLOOR = 0.25       # every lieutenant win pays at least 0.25 level
STORY_XP_BOSS = 1.0            # crew boss (and scripted race 3) pays 1.0 × the levels it unlocks, immediately
                               # (2 levels normally; 18 levels when it unlocks a round-opening kid #1)

# ── Grind race XP: per-crew taper T2 ──
# grind race XP = f(L, j) · x(L); L = level being filled, j = rung index 0..6 (finale rungs j = 4)
TAPER_F0 = 1.9
TAPER_RUNG = 0.88
TAPER_LEVEL_TAU = 550.0
TAPER_FINALE_RUNG = 4

# ── Finale exemption (caps lifted) ──
FINALE_MOD_SHARE = 0.86        # finale stat rise split: 86 % mods, 14 % grind (levels)
FINALE_GRIND_SHARE = 0.14


def knot_window(r: float) -> float:
    """Player QTE window W(r) from KNOT_WINDOW_105 (flat below/above the ends, capped at 1)."""
    xs = [k[0] for k in KNOT_WINDOW_105]; ys = [k[1] for k in KNOT_WINDOW_105]
    if r <= xs[0]:
        return ys[0]
    for (x0, y0), (x1, y1) in zip(KNOT_WINDOW_105, KNOT_WINDOW_105[1:]):
        if r <= x1:
            return min(1.0, y0 + (y1 - y0) * (r - x0) / (x1 - x0))
    return min(1.0, ys[-1])


def sp_per_level(level: int) -> float:
    """s(L): skill points gained on reaching `level` (GEO curve)."""
    g = SP_GROWTH_PER_12_LEVELS ** (1 / 12)
    return SP_START * (g - 1) * g ** (level - 1)


def xp_to_next(level: int, sp_before: float) -> float:
    """x(L): XP to fill `level`, given total SP at level-1."""
    return XP_BASE * (sp_before / SP_START) ** XP_SP_EXPONENT * sp_per_level(level) / sp_per_level(1)


def grind_payout_fraction(level: int, rung: int) -> float:
    """T2 taper: grind race XP as a fraction of x(level). Falls with rung inside a crew and with level."""
    return TAPER_F0 * (1 - TAPER_RUNG * rung / 6) * math.exp(-level / TAPER_LEVEL_TAU)
