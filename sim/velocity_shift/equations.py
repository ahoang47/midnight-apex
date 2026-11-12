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

# ── Legacy HP/DP constants (resolve_turn_legacy only; not the playable engine) ──

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
# (`config/winrate_n4000.json`, real N=4000 sim output). The playable engine
# in combat.py / match.py uses this same model: LINE_SET_C line picks,
# KAPPA_BY_LENGTH, OPPONENT_QTE, the visible QTE zone (`QTE_ZONE_WIDTH_105`,
# approved qte-v1, 2026-11-11), and the Phi/tau clash payoff. The older
# HP/DP resolve path is resolve_turn_legacy. KNOT_WINDOW_105 is legacy
# (winrate_n4000.json / progression oracle, and the generator of the zone table).
# All XP numbers are stand-ins pending playtest.

# ── Combat race-balance settings (final-v1 + approved qte-v1, 2026-11-11) ──
# r = (player SP + mods) / opponent budget. The stat gap is a VISIBLE QTE
# zone width (qte_zone_width), not a hidden multiplier on the score.
# Legacy hidden window, kept for the winrate_n4000.json / progression oracle
# and as the generator of QTE_ZONE_WIDTH_105 (qte-v1 inverted E[s] so the
# average player's expected raw score equals AVERAGE_PLAY_Q * knot_window(r)).
# 2026-11-11 (slots-v2, Austin approved): r=1.00 knot 0.68 -> 0.67, so a +75% window mod (1.15 x w0 cap) no longer
# clears the R2/R3 opener boss walls without grinding (avg 49.07 mid); balanced grind 141/153/121 unchanged.
KNOT_WINDOW_105 = ((0.80, 0.41), (0.85, 0.41), (0.90, 0.41), (0.95, 0.43), (1.00, 0.67), (1.05, 1.00))
KAPPA_BY_LENGTH = {10: 1.55, 20: 1.35, 30: 1.20}   # stat-gap leverage V = r**kappa, by race length (turns)
RACE_LENGTHS = (10, 20, 30)
SIM_SEEDS = (20261113, 20261114, 20261115)
OPPONENT_QTE = 1.0             # story-rung opponents time perfectly (uniform across rungs)
# Visible QTE zone (qte-v1, Austin approved 2026-11-11). Presentation unit
# is QTE_ZONE_BASE_MS (Godot QTE_TIMING_WINDOW_BASE_MS). Widths below are
# fractions of that default zone. Interpolation: see qte_zone_width().
QTE_ZONE_BASE_MS = 800
# Exact inversions of E[s] at the KNOT_WINDOW_105 r knots for sigma_average
# (the 4-dp figures 0.3276, 0.3448, 0.5698, 1.0 are these values rounded; r=1.00 was 0.5802 before 2026-11-11).
# The last knot is 1.0 exactly (sigma_average is fitted so E[s] at w0 is 0.6).
QTE_ZONE_WIDTH_105 = (
    (0.80, 0.32758027216269503),
    (0.85, 0.32758027216269503),
    (0.90, 0.32758027216269503),
    (0.95, 0.3447526695824932),
    (1.00, 0.5698111340658429),
    (1.05, 1.0),
)
# PLACEHOLDER until playtest data exists. Fitted so expected_hit_quality(σ, 1)
# equals 0.4 / 0.6 / 0.8 at the default zone. Units are half-widths of w0
# (a0 = QTE_ZONE_BASE_MS / 2).
QTE_SKILL_TARGET_E = {"weak": 0.4, "average": 0.6, "strong": 0.8}
QTE_SKILL_SIGMA_OVER_A0 = {  # PLACEHOLDER
    "weak": 0.9074726672615829,
    "average": 0.5139633886624675,
    "strong": 0.25066753386161233,
}
# Window-only mods: MatchConfig.qte_window_mod is a multiplicative bonus on
# the current zone (0.10 = +10% of qte_zone_width(r)). Slot competition and
# the 105%-all-slots rule belong to the upcoming slot sim; they are not
# modelled here.
# Per-phase QTE input (Austin, 2026-11-11, relayed by Gordon, then
# revised the same night): Entry, Apex, and Exit can each supply a raw
# score, and the turn's raw_qte is their mean. An unplayed or timed-out
# phase counts as 0 (Austin). Clash math is unchanged: one raw_qte and
# the existing q_eff formula per turn. The timeout window is the zone's
# own visible sweep — Barry's proposal; Austin answered only the score.
QTE_PHASES = ("entry", "apex", "exit")
PHASE_QTE_UNPLAYED = 0.0
# Phi/tau clash payoff (final-v1 / equations_v1 K, unchanged). Per clash:
#   g = V * Phi(outcome, q_eff) * M,  V = r**kappa,
#   q_eff = clip(raw_qte * (1 + ETA * (han_share - 1/3)), 0, 1)
# No knot_window factor. The player's raw_qte already reflects the visible
# zone at the race's fixed r (and any window-mod bonus). HAN still scales
# both sides — same as equations_v2.clash_progress. The opponent uses
# OPPONENT_QTE with HAN (window was never applied to them).
W0 = 0.10                      # win payoff at q=0
T_MAX = 0.75                   # tie payoff at q=1, as a fraction of a perfect win
L_MAX = 0.25                   # loss payoff at q=1
TAU_BETA = 0.10                # share of timing value held back as the top bonus
TAU_P_TOP = 8.0                # sharpness of the top bonus (only bites near q=1)
TAU_GAMMA = 0.0                # 0 = concave body 1-(1-q)**2; >0 = q**GAMMA
MU = 0.5                       # POW share raises win payoff; EN share raises tie/loss payoff
ETA = 0.5                      # HAN share raises effective timing (same value as HAN_QTE_WEIGHT)
DECK_ALPHA = 0.85              # deck-weight mix: ALPHA * stat share + (1-ALPHA)/3
HAND_SIZE = 6                  # cards drawn per turn; 3 are played (Entry/Apex/Exit)
LINE_ADHERENCE = 0.65          # boss follows its district line with prob a; 1-a = bluff/deviation
LINE_ALT_WEIGHTS = {"alt1": 0.6, "alt2": 0.4}
# Line set C: per district, per corner type -> [main, alt1, alt2] lines, each "Entry Apex Exit"
# (D = Defend, S = Steady, A = Attack). Alternatives share main's Entry (unreadable at lock):
# alt1 switches Apex+Exit, alt2 switches Exit only. Mechanical stand-in.
# 2026-11-10 (lines-v1 S-A + W-A, Austin): Street N90 DDA -> SSA; Wangan SW and IR AAA -> AAD.
# Touge unchanged. In-world feel approved by Austin (Nathaniel, 2026-11-10; story/corner_lines.md).
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
# Aero parts (design/07 §6.3; Austin approved 2026-11-11, slots-v2): a stat part with a fixed base plus a free pool
# assigned to POW/EN/HAN at the wind tunnel. It goes in any slot, at most one is equipped, and its whole stat total
# (base + pool) counts inside MOD_CAP_FRACTION like any other mod. The free pool is at most AERO_FREE_POOL_MAX_FRACTION
# of the part's stat total (above 10%, retuned aero lets avg players clear R3 Street's boss / the Summit unground).
# Per-tier AERO_FREE_POINTS values are still TBD; they must satisfy pool <= AERO_FREE_POOL_MAX_FRACTION x tier total.
AERO_FREE_POOL_MAX_FRACTION = 0.10
AERO_MAX_EQUIPPED = 1
AERO_COUNTS_IN_MOD_CAP = True
REFERENCE_RULE = "V2"          # reference rises with each lieutenant win; crew boss = crew budget
MOD_TIMING = "c"               # mods unlock progressively with lieutenant wins
# Crew-local level floor on the mature #2 mod tier (slots-v2 fix b3; Austin approved 2026-11-12; design/07 §6.4).
# The mod tier a crew unlocks for its mature #2 race (LADDER_RUNGS index MOD_TIER_FLOOR_RUNG) shows "requires level N"
# and cannot be fitted until the player's level is >= N, even when it is affordable. N = the level at that rung of a
# player who reached the previous crew boss's level cap and has not ground in this crew, + MOD_TIER_FLOOR_MARGIN
# (never above the rung's level cap). Keyed by (round, 0-based play position in the round), like the budget steps:
# the same in all 216 play orders. Values are generated by progression.derive_mod_tier_floors() and pinned by
# tests/test_mod_floor.py; change the inputs, rerun it, and paste its output here.
MOD_TIER_FLOOR_RUNG = 3
MOD_TIER_FLOOR_MARGIN = 1
MOD_TIER_LEVEL_FLOOR = {(1, 0): 4, (1, 1): 14, (1, 2): 26,
                        (2, 0): 54, (2, 1): 71, (2, 2): 83,
                        (3, 0): 111, (3, 1): 128, (3, 2): 140}
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
    """LEGACY hidden QTE window W(r) from KNOT_WINDOW_105 (flat outside the ends, capped at 1).

    Not used by the playable engine. Kept for the winrate_n4000.json /
    progression oracle and as the generator of qte_zone_width().
    """
    xs = [k[0] for k in KNOT_WINDOW_105]; ys = [k[1] for k in KNOT_WINDOW_105]
    if r <= xs[0]:
        return ys[0]
    for (x0, y0), (x1, y1) in zip(KNOT_WINDOW_105, KNOT_WINDOW_105[1:]):
        if r <= x1:
            return min(1.0, y0 + (y1 - y0) * (r - x0) / (x1 - x0))
    return min(1.0, ys[-1])


def expected_hit_quality(sigma_over_a0: float, width_over_w0: float) -> float:
    """E[s] for one timing press: s = max(0, 1 - |e| / (w/2)), e ~ Normal(0, σ).

    `width_over_w0` is the zone width as a fraction of QTE_ZONE_BASE_MS;
    `sigma_over_a0` is σ in units of the default half-width a0.
    Skill σ values are PLACEHOLDER until playtest data exists.
    """
    a = float(width_over_w0)
    s = float(sigma_over_a0)
    if a <= 0.0:
        return 0.0
    if s <= 0.0:
        return 1.0
    z = a / s
    return math.erf(z / math.sqrt(2.0)) - (s / a) * math.sqrt(2.0 / math.pi) * (
        1.0 - math.exp(-0.5 * z * z)
    )


def _qte_sigma_for_target(target: float) -> float:
    """σ / a0 such that expected_hit_quality(σ, 1) = target. Internal."""
    if not 0.0 < target < 1.0:
        raise ValueError(f"target must be in (0, 1), got {target}")
    lo, hi = 1e-8, 50.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if expected_hit_quality(mid, 1.0) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _qte_width_for_target(target: float, sigma_over_a0: float) -> float:
    """Zone width / w0 such that expected_hit_quality(σ, w) = target. Internal."""
    if target <= 0.0:
        return 0.0
    if target >= 1.0 - 1e-15:
        return float("inf")
    lo, hi = 1e-10, 50.0 * max(sigma_over_a0, 1e-8)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if expected_hit_quality(sigma_over_a0, mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def qte_sigma_over_a0(profile: str | None = None, q_time: float | None = None) -> float:
    """σ / a0 for a named PLACEHOLDER profile, or for a skill with E[s]=q_time at w0."""
    if profile is not None:
        if profile not in QTE_SKILL_SIGMA_OVER_A0:
            raise ValueError(f"unknown QTE skill profile {profile!r}")
        return QTE_SKILL_SIGMA_OVER_A0[profile]
    if q_time is None:
        raise ValueError("need a skill profile or a q_time")
    if q_time <= 0.0:
        return float("inf")
    if q_time >= 1.0:
        return 0.0
    for name, target in QTE_SKILL_TARGET_E.items():
        if abs(q_time - target) < 1e-12:
            return QTE_SKILL_SIGMA_OVER_A0[name]
    return _qte_sigma_for_target(q_time)


def qte_zone_width(r: float, window_mod: float = 0.0) -> float:
    """Visible zone width as a fraction of QTE_ZONE_BASE_MS, at stat ratio r.

    Interpolation matches qte-v1: invert expected_hit_quality so the
    average player's E[s] equals AVERAGE_PLAY_Q * knot_window(r), then
    apply the window-mod bonus as a multiplier, width * (1 + window_mod).
    The result is flat below r=0.80 and plateaus at 1.0 (before the mod)
    for r >= 1.05. The zone depends only on the race's fixed r and the
    mod; it does not change with mid-race position. The same width is
    used for Entry, Apex, and Exit. The timeout window for an unplayed
    phase is this visible sweep (Barry's proposal; Austin answered only
    that an unplayed phase scores 0).

    window_mod is a multiplicative bonus (0.10 = +10% of the current
    zone). Slot competition and the 105%-all-slots rule are not applied
    here (upcoming slot sim).
    """
    target = AVERAGE_PLAY_Q * knot_window(r)
    if r >= KNOT_WINDOW_105[-1][0] or abs(target - AVERAGE_PLAY_Q) < 1e-15:
        width = 1.0
    else:
        width = _qte_width_for_target(target, QTE_SKILL_SIGMA_OVER_A0["average"])
    width = width * (1.0 + window_mod)
    return 0.0 if width < 0.0 else width


def raw_qte_score(
    r: float,
    profile: str | None = None,
    q_time: float | None = None,
    window_mod: float = 0.0,
) -> float:
    """Expected raw QTE score at the race's fixed r (no HAN, no knot_window).

    A named profile or an explicit q_time (E[s] at the default zone,
    back-compat with tests / player_timing) is evaluated at qte_zone_width
    (r, window_mod). Skill σ is PLACEHOLDER until playtest.
    """
    if profile is None and q_time is None:
        profile = "average"
    sig = qte_sigma_over_a0(profile, q_time)
    return expected_hit_quality(sig, qte_zone_width(r, window_mod))


def phase_raw_qte(score: float | None) -> float:
    """Raw QTE for one Entry/Apex/Exit phase. None / unplayed is 0 (Austin)."""
    if score is None:
        return PHASE_QTE_UNPLAYED
    return float(score)


def mean_phase_qte(value: float | None | list | tuple) -> float:
    """Turn raw_qte from a scalar or three phase scores.

    A 3-tuple/list (Entry, Apex, Exit) is averaged; None / unplayed is 0
    (Austin, 2026-11-11). A scalar is returned as-is. Clash math is not
    changed: the result is the single raw_qte for the turn.
    """
    if isinstance(value, (list, tuple)) and len(value) == 3 and not isinstance(value, (str, bytes)):
        return sum(phase_raw_qte(v) for v in value) / 3.0
    if value is None:
        return PHASE_QTE_UNPLAYED
    return float(value)


def aero_free_pool_max(part_stat_total: float) -> float:
    """Largest free (wind-tunnel) pool an aero part may carry: AERO_FREE_POOL_MAX_FRACTION of its stat total.

    The pool only redistributes points inside the part's total, so the part still counts in full
    against MOD_CAP_FRACTION. Per-tier AERO_FREE_POINTS are TBD (design/07 §6.3).
    """
    return AERO_FREE_POOL_MAX_FRACTION * max(0.0, float(part_stat_total))


def kappa_for_length(race_length: int) -> float:
    """Stat-gap leverage for a race of `race_length` turns.

    Official table is 10/20/30 only. Any other length uses the closest key
    (no interpolated kappa — we do not invent values).
    """
    if race_length in KAPPA_BY_LENGTH:
        return KAPPA_BY_LENGTH[race_length]
    return KAPPA_BY_LENGTH[min(KAPPA_BY_LENGTH, key=lambda L: abs(L - race_length))]


def timing_value(q: float) -> float:
    """tau(q) in [0, 1]: concave body + top bonus. tau(0)=0, tau(1)=1."""
    q = 0.0 if q < 0.0 else 1.0 if q > 1.0 else q
    body = (1 - (1 - q) ** 2) if TAU_GAMMA <= 0 else q ** TAU_GAMMA
    return (1 - TAU_BETA) * body + TAU_BETA * q ** TAU_P_TOP


def clash_payoff(outcome: StanceOutcome, q: float) -> float:
    """Phi(outcome, q): progress fraction of a perfect win, before stats."""
    t = timing_value(q)
    if outcome == StanceOutcome.WIN:
        return W0 + (1 - W0) * t
    if outcome == StanceOutcome.NEUTRAL:
        return T_MAX * t
    return L_MAX * t


def stat_shares(pow_stat: float, en_stat: float, han_stat: float) -> tuple[float, float, float, float]:
    """(total, pow_share, en_share, han_share)."""
    tot = pow_stat + en_stat + han_stat
    if tot <= 0:
        return 0.0, 1 / 3, 1 / 3, 1 / 3
    return tot, pow_stat / tot, en_stat / tot, han_stat / tot


def clash_progress(
    outcome: StanceOutcome,
    q_time: float,
    pow_stat: float,
    en_stat: float,
    han_stat: float,
    boss_total: float,
    kappa: float,
) -> float:
    """g = V * Phi(o, q_eff) * M.

    q_eff = clip(q_time * (1 + ETA * (han_share - 1/3)), 0, 1).
    No knot_window factor: the player's q_time is already the raw score
    at the visible zone. HAN still applies to both sides.
    """
    tot, pow_s, en_s, han_s = stat_shares(pow_stat, en_stat, han_stat)
    r = tot / boss_total if boss_total else 1.0
    V = r ** kappa
    qe = q_time * (1.0 + ETA * (han_s - 1 / 3))
    qe = 0.0 if qe < 0.0 else 1.0 if qe > 1.0 else qe
    if outcome == StanceOutcome.WIN:
        M = 1.0 + MU * (pow_s - 1 / 3)
    else:
        M = 1.0 + MU * (en_s - 1 / 3)
    return V * clash_payoff(outcome, qe) * M


def deck_weights(pow_stat: float, en_stat: float, han_stat: float) -> tuple[float, float, float]:
    """Multinomial weights for (Attack, Steady, Defend) = (POW, HAN, EN)."""
    tot, pow_s, en_s, han_s = stat_shares(pow_stat, en_stat, han_stat)
    raw = (
        pow_s * DECK_ALPHA + (1 - DECK_ALPHA) / 3,
        han_s * DECK_ALPHA + (1 - DECK_ALPHA) / 3,
        en_s * DECK_ALPHA + (1 - DECK_ALPHA) / 3,
    )
    s = sum(raw)
    return (raw[0] / s, raw[1] / s, raw[2] / s)


def counter_stance(s: Stance) -> Stance:
    """The stance that beats `s` (Defend > Attack > Neutral > Defend)."""
    if s == Stance.ATTACK:
        return Stance.DEFEND
    if s == Stance.NEUTRAL:
        return Stance.ATTACK
    return Stance.NEUTRAL


def loser_to_stance(s: Stance) -> Stance:
    """The stance that loses to `s`."""
    if s == Stance.ATTACK:
        return Stance.NEUTRAL
    if s == Stance.NEUTRAL:
        return Stance.DEFEND
    return Stance.ATTACK


# Stance index order used by assign_hand / deck_weights: Attack, Steady, Defend.
_STANCE_INDEX = {Stance.ATTACK: 0, Stance.NEUTRAL: 1, Stance.DEFEND: 2}
_INDEX_STANCE = (Stance.ATTACK, Stance.NEUTRAL, Stance.DEFEND)


def assign_hand(
    hand_counts: list[int],
    wanted: list[Stance],
    fallback: list[Stance | None],
    rng,
) -> list[Stance]:
    """Greedy assign from a 6-card hand: lock wanted stances, then fallbacks, then any leftover.

    Same rule as final-v1 / equations_v1._assign. `hand_counts` is [Attack, Steady, Defend].
    """
    c = list(hand_counts)
    out = [-1, -1, -1]
    want_i = [_STANCE_INDEX[s] for s in wanted]
    fb_i = [None if s is None else _STANCE_INDEX[s] for s in fallback]
    for i in range(3):
        if c[want_i[i]] > 0:
            out[i] = want_i[i]
            c[want_i[i]] -= 1
    for i in range(3):
        if out[i] < 0 and fb_i[i] is not None and c[fb_i[i]] > 0:
            out[i] = fb_i[i]
            c[fb_i[i]] -= 1
    for i in range(3):
        if out[i] < 0:
            left = [s for s in range(3) for _ in range(c[s])]
            s = left[rng.randrange(len(left))]
            out[i] = s
            c[s] -= 1
    return [_INDEX_STANCE[i] for i in out]


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
