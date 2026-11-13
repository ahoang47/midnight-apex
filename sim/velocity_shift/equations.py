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
#   * Read: each corner, with probability q_read the player reads the boss's
#     line and plays the best selectable stance against it (heat-aware); on a
#     misread each clash ties with prob q_read, else loses (simulation.py).
#   * QTE: q_time is the expected hit quality at the default zone, evaluated
#     at the race's visible zone (raw_qte_score). PLAYER_QTE_* / PERFECT_QTE
#     are the legacy 1–10 scale (HP/DP only).
#   * Pacing: MatchConfig.player_pacing (default q_read), see PACE_*.
# player_quality=q is shorthand for q_read = q_time = q.
PLAYER_QTE_MIN = 1.0
PLAYER_QTE_MAX = 10.0
PERFECT_QTE = 10.0


def qte_factor(qte_score: float) -> float:
    """Normalise a QTE score (1–10) to a 0.1–1.0 multiplier."""
    return qte_score / QTE_NORMALIZER


def apply_han_qte_mod(qte_score: float, han_pct: float) -> float:
    """Modify a QTE score by HAN proportion. Same formula for both sides.
    han_pct = han / (pow + en + han).
    No change at han_pct == 1/3, scales linearly with HAN_QTE_WEIGHT.
    """
    return qte_score * (1.0 + HAN_QTE_WEIGHT * (han_pct - 1 / 3))


def clash_mult(outcome: StanceOutcome) -> float:
    """Return the damage multiplier for a single clash result.

    * WIN    → 1 + CLASH_STAKES
    * DRAW   → 1.0
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

    Rules (design/02 §6.0 naming map):
        POW > HAN > EN > POW
        Same stance → draw (StanceOutcome.DRAW)
    """
    if a == b:
        return StanceOutcome.DRAW
    if (a == Stance.POW and b == Stance.HAN) or \
       (a == Stance.HAN and b == Stance.EN) or \
       (a == Stance.EN and b == Stance.POW):
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
KAPPA_BY_LENGTH = {10: 1.55, 20: 1.35, 30: 1.20}   # final-v1 base stat-gap leverage, by race length (turns)
# Heat system (G2, 2026-11-13): the live kappa is KAPPA_BY_LENGTH x KAPPA_HEAT_MULT (see kappa_for_length).
KAPPA_HEAT_MULT = {10: 1.75, 20: 2.25, 30: 2.25}
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
# QTE score rounding (Austin approved via Desmond, 2026-11-12). Every QTE
# phase score is rounded to QTE_SCORE_DECIMALS where it is computed
# (raw_qte_score, phase_raw_qte), before mean_phase_qte, q_eff, clash or
# progress math sees it, so a 1-ULP libm difference in erf/exp between
# platforms (glibc 2.41 vs 2.43) cannot change gameplay. Rule (round_qte_score):
#   floor(x * 10**QTE_SCORE_DECIMALS + 0.5) / 10**QTE_SCORE_DECIMALS
# i.e. half-up on the scaled double, then an exact-integer division. Only
# IEEE-754 correctly rounded * + / and floor are used, so the bits are the
# same everywhere. Not Python round() (half-even on the exact binary value)
# and not Godot snappedf() (divides and multiplies by the inexact 0.001);
# both can give different bits. Godot mirrors with
#   floor(x * 1000.0 + 0.5) / 1000.0
QTE_SCORE_DECIMALS = 3
# Phi/tau clash payoff (final-v1 / equations_v1 K). Per clash (heat system, 2026-11-13):
#   g = V * Phi(outcome, q) * stat_payoff_mult(share of the stance played) * heat_mult,
#   V = r**kappa (kappa_for_length), heat_mult = overrun_mult(x) or LIMP_MULT (1.0 inside capacity).
# No knot_window factor and no HAN timing modifier: the player's raw_qte already
# reflects the visible zone at the race's fixed r (and any window-mod bonus).
# The opponent uses OPPONENT_QTE.
W0 = 0.10                      # win payoff at q=0
T_MAX = 0.75                   # tie payoff at q=1, as a fraction of a perfect win
L_MAX = 0.25                   # loss payoff at q=1
TAU_BETA = 0.10                # share of timing value held back as the top bonus
TAU_P_TOP = 8.0                # sharpness of the top bonus (only bites near q=1)
TAU_GAMMA = 0.0                # 0 = concave body 1-(1-q)**2; >0 = q**GAMMA
# MU / ETA (POW/EN/HAN share multipliers) and the card draw (DECK_ALPHA, HAND_SIZE,
# deck_weights, assign_hand) were removed 2026-11-13: the heat/load resource
# system below replaces them (resources-v4b G2, Austin approved).
LINE_ADHERENCE = 0.65          # boss follows its district line with prob a; 1-a = bluff/deviation
LINE_ALT_WEIGHTS = {"alt1": 0.6, "alt2": 0.4}
# Line set C: per district, per corner type -> [main, alt1, alt2] lines, each "Entry Apex Exit"
# (P = POW, E = EN, H = HAN; letters renamed 2026-11-12 from A/D/S, map in design/02 §6.0). Alternatives share main's Entry (unreadable at lock):
# alt1 switches Apex+Exit, alt2 switches Exit only. Mechanical stand-in.
# 2026-11-10 (lines-v1 S-A + W-A, Austin): Street N90 EEP -> HHP; Wangan SW and IR PPP -> PPE.
# Touge unchanged. In-world feel approved by Austin (Nathaniel, 2026-11-10; story/corner_lines.md).
LINE_SET_C = {
    "touge": {"HP": ["EHP", "EEH", "EHH"], "CR": ["HHP", "HEH", "HHH"], "DR": ["HEH", "HPE", "HEE"], "IR": ["HHP", "HEH", "HHH"],
              "N90": ["EHP", "EEH", "EHH"], "CH": ["HEP", "HPH", "HEH"], "ES": ["HHH", "HEE", "HHE"], "SW": ["HHP", "HEH", "HHH"]},
    "wangan": {"HP": ["EHP", "EEH", "EHH"], "CR": ["HPP", "HHH", "HPH"], "DR": ["EEH", "EPE", "EEE"], "IR": ["PPE", "PHP", "PPP"],
               "N90": ["EHP", "EEH", "EHH"], "CH": ["EHP", "EEH", "EHH"], "ES": ["HHH", "HEE", "HHE"], "SW": ["PPE", "PHP", "PPP"]},
    "street": {"HP": ["EEP", "EPH", "EEH"], "CR": ["EHE", "EEP", "EHP"], "DR": ["EEH", "EPE", "EEE"], "IR": ["HHP", "HEH", "HHH"],
               "N90": ["HHP", "HEH", "HHH"], "CH": ["EPP", "EHH", "EPH"], "ES": ["PHP", "PEH", "PHH"], "SW": ["EEE", "EPP", "EEP"]},
}

# ══════════════════════════════════════════════════════════════════════
# Heat / load resource system (resources-v4b candidate G2_slant_m10;
# Austin approved 2026-11-13: "I'm happy with this new resource system").
# Source study: unapproved/barry/resources-v4/retune/ (RESULTS.md, resources_v4b.py).
# Replaces the card draw. Each turn the player picks any stance for each of
# Entry / Apex / Exit, subject to three gauges that all recover during the race:
#   POW = engine heat, HAN = suspension load, EN = brake/tire heat.
# Gauge arrays everywhere are in HEAT_ORDER (POW, HAN, EN), same as _STANCE_INDEX.
# Rules (heat.py implements them; equations below are the pure parts):
#   * Playing stance s adds  cost = HEAT_BASE_COST x CORNER_HEAT_COST[corner][s] x wear_s
#     x (1 + HEAT_REPEAT_SURCHARGE x (uses of s earlier this turn)) to gauge s.
#   * A stance is selectable while its gauge is not locked. Playing it may push the load
#     past capacity (overrun): that clash's payoff x overrun_mult(x), x = (load - cap) / cap.
#   * A gauge locks when load >= cap (also mid-turn) and unlocks only once load < release x cap.
#   * End of turn: load += CORNER_HEAT_PASSIVE x wear (can lock), then load = max(0, load - recovery),
#     then release check. Load carries over (no cap on load). The car starts cold (load 0).
#   * All three locked = limp: the side plays its least-loaded gauge (load / cap) at LIMP_MULT.
#   * Capacity / recovery per turn = HEAT_CAP_TURNS / HEAT_RECOVERY x the cross-track average
#     per-turn load (heat.avg_heat_demand()) x heat_share_mult(shares) x r**HEAT_R_EXP.
#   * wear_s: per-track multiplier (heat.track_wear) so every official track asks the same total
#     load (TRACK_NORMALIZE) and each track's mix is pushed HEAT_DEMAND_SLANT x further from even.
#   * Clash payoff x stat_payoff_mult(share of the stance played) (STAT_M_W), all three stats.
# Bosses keep the v3 heat rules (BOSS_HEAT_*): how bosses manage heat is an open story question
# (Desmond / Nathaniel); until then they play their district line and swap a locked stance for
# their least-loaded unlocked one.
HEAT_ORDER = ("POW", "HAN", "EN")
# Per-corner multiplier on what each stance costs (POW/engine, HAN/suspension, EN/brakes). PLACEHOLDER (resources-v1)
CORNER_HEAT_COST = {
    "HP":  (0.8, 1.2, 1.4),   # hairpin: heavy braking, big weight transfer
    "CR":  (1.0, 1.2, 0.8),   # constant radius: sustained load
    "DR":  (0.8, 1.1, 1.3),   # decreasing radius: trail braking
    "IR":  (1.3, 0.9, 0.7),   # increasing radius: on the throttle early
    "N90": (1.0, 0.8, 1.4),   # 90-degree street corner: hard stop
    "CH":  (0.9, 1.3, 1.1),   # chicane: quick direction changes
    "ES":  (0.8, 1.4, 0.9),   # esses: suspension working constantly
    "SW":  (1.4, 0.9, 0.6),   # sweeper: flat out
}
# Passive load the corner adds each turn whatever is played (POW, HAN, EN). PLACEHOLDER (resources-v1)
CORNER_HEAT_PASSIVE = {
    "HP":  (0.0, 0.3, 0.3),
    "CR":  (0.1, 0.2, 0.0),
    "DR":  (0.0, 0.2, 0.3),
    "IR":  (0.3, 0.1, 0.0),
    "N90": (0.1, 0.0, 0.4),
    "CH":  (0.0, 0.3, 0.2),
    "ES":  (0.0, 0.4, 0.1),
    "SW":  (0.4, 0.1, 0.0),
}
HEAT_BASE_COST = 1.0           # cost of one stance at a 1.0 corner
HEAT_REPEAT_SURCHARGE = 1.0    # k-th use of the same stance in one turn costs 1 + this x (k-1)
HEAT_CAP_TURNS = 3.0           # even build's capacity = this x average per-turn load
HEAT_RECOVERY = 1.0            # even build's recovery per turn = this x average per-turn load
HEAT_SHARE_EXP = 1.5           # capacity and recovery x 3 s**e / sum(s**e) (sums to 3: specialising adds no total)
HEAT_R_EXP = 1.0               # capacity and recovery x r**HEAT_R_EXP (stat total vs the boss)
HEAT_RELEASE = 0.3             # a locked gauge unlocks once load < HEAT_RELEASE x capacity
OVERRUN_SLOPE = 2.0            # overrun payoff = max(OVERRUN_FLOOR, 1 - OVERRUN_SLOPE x x)
OVERRUN_FLOOR = 0.4
LIMP_MULT = 0.4                # payoff of a clash played with all three gauges locked
HEAT_DEMAND_SLANT = 2.0        # 1 = the raw mix that falls out of the district lines; 2 = twice as far from even
HEAT_REF_Q = 0.6               # loads are calibrated on a player who reads 60 % of corners
STAT_M_W = 1.0                 # clash payoff x (1 + STAT_M_W x (share of the stance played - 1/3))
# Boss gauges: v3 heat rules (release 0.8), even split, r = 1. PLACEHOLDER pending Desmond / Nathaniel.
BOSS_HEAT_CAP_TURNS = 3.0
BOSS_HEAT_RECOVERY = 1.0
BOSS_HEAT_RELEASE = 0.8
BOSS_HEAT_LOCK_ON_PASSIVE = False   # v3/G2 boss: a gauge locks only when the boss plays into it, not from passive load
# Boss line styles (sim only, PLACEHOLDER; story question for Desmond / Nathaniel). "balanced" is the live
# 65/21/14 split. "hot_early" / "conserver" blend BOSS_STYLE_BLEND of a cost ranking into it: hot_early runs
# the dearest line first until BOSS_HOT_SWITCH of the race, then the cheapest; conserver the reverse at BOSS_CONS_SWITCH.
BOSS_STYLES = ("balanced", "hot_early", "conserver")
BOSS_STYLE_BLEND = 0.3
BOSS_HOT_SWITCH = 0.5
BOSS_CONS_SWITCH = 2 / 3
# Simulated-player pacing (sim AI only, not a game rule). "reserve" rule: price a stance when it would push its
# gauge past a soft ceiling PACE_RES_T x cap, lowered by PACE_RES_LOOK x the expected shortfall of the next
# PACE_LOOKAHEAD corners; price = PACE_RES_K x (value of a win over a tie) x how far past the ceiling.
# An average player paces on AVERAGE_PLAY_Q of turns and plays greedy otherwise (MatchConfig.player_pacing).
PACE_RES_T = 0.7
PACE_RES_K = 2.0
PACE_RES_LOOK = 0.5
PACE_LOOKAHEAD = 3

BUILD_STAT_MIN_SHARE = 0.25    # build bounds: each of POW/HAN/EN is 25–50 % of the total
BUILD_STAT_MAX_SHARE = 0.50

# ── Stat caps, reference rule, mods ──
SP_CAP_FRACTION = 0.80         # skill points cap at 80 % of the reference budget (= level cap)
MOD_CAP_FRACTION = 1.07        # SP + mods cap at 107 % of the reference budget before the finale (was 1.05; G2 heat system, Austin 2026-11-13)
# STALE until the ladder is refit for the heat system: progression.py (ladder, grind, XP, MOD_TIER_LEVEL_FLOOR) still runs
# on the card-draw win-rate oracle (config/winrate_n4000.json), which was built at a 1.05 cap. It keeps that frozen cap here
# so its report stays self-consistent; it is NOT the game's cap. Refit pending (Barry).
PROGRESSION_MOD_CAP_FRACTION = 1.05
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
    return round_qte_score(expected_hit_quality(sig, qte_zone_width(r, window_mod)))


def round_qte_score(x: float) -> float:
    """Round a QTE score to QTE_SCORE_DECIMALS: floor(x * 10**d + 0.5) / 10**d.

    Half-up on the scaled value, then exact-integer division, so the result
    is the double nearest k / 10**d and is bit-identical on every IEEE-754
    platform (Godot: floor(x * 1000.0 + 0.5) / 1000.0). Non-finite values
    pass through unchanged.
    """
    x = float(x)
    if not math.isfinite(x):
        return x
    scale = float(10 ** QTE_SCORE_DECIMALS)
    return math.floor(x * scale + 0.5) / scale


def phase_raw_qte(score: float | None) -> float:
    """Raw QTE for one Entry/Apex/Exit phase, rounded by round_qte_score. None / unplayed is 0 (Austin)."""
    if score is None:
        return PHASE_QTE_UNPLAYED
    return round_qte_score(score)


def mean_phase_qte(value: float | None | list | tuple) -> float:
    """Turn raw_qte from a scalar or three phase scores.

    A 3-tuple/list (Entry, Apex, Exit) is averaged (each phase already
    rounded by phase_raw_qte, summed in Entry, Apex, Exit order, then / 3);
    None / unplayed is 0 (Austin, 2026-11-11). A scalar is returned as-is
    (it is treated as an already-computed turn raw_qte). Clash math is not
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
    """Stat-gap leverage for a race of `race_length` turns: KAPPA_BY_LENGTH x KAPPA_HEAT_MULT.

    Official table is 10/20/30 only. Any other length uses the closest key
    (no interpolated kappa — we do not invent values).
    """
    if race_length not in KAPPA_BY_LENGTH:
        race_length = min(KAPPA_BY_LENGTH, key=lambda L: abs(L - race_length))
    return KAPPA_BY_LENGTH[race_length] * KAPPA_HEAT_MULT[race_length]


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
    if outcome == StanceOutcome.DRAW:
        return T_MAX * t
    return L_MAX * t


def stat_shares(pow_stat: float, en_stat: float, han_stat: float) -> tuple[float, float, float, float]:
    """(total, pow_share, en_share, han_share)."""
    tot = pow_stat + en_stat + han_stat
    if tot <= 0:
        return 0.0, 1 / 3, 1 / 3, 1 / 3
    return tot, pow_stat / tot, en_stat / tot, han_stat / tot


def stat_payoff_mult(share_played: float) -> float:
    """Stat weight on a clash: 1 + STAT_M_W x (share of the stance played - 1/3). Same for all three stats."""
    return 1.0 + STAT_M_W * (share_played - 1 / 3)


def stance_share(stance: Stance, pow_stat: float, en_stat: float, han_stat: float) -> float:
    """Build share of the stat that matches `stance`."""
    tot, pow_s, en_s, han_s = stat_shares(pow_stat, en_stat, han_stat)
    return pow_s if stance == Stance.POW else en_s if stance == Stance.EN else han_s


def clash_progress(
    outcome: StanceOutcome,
    stance: Stance,
    q_time: float,
    pow_stat: float,
    en_stat: float,
    han_stat: float,
    boss_total: float,
    kappa: float,
    heat_mult: float = 1.0,
) -> float:
    """g = V * Phi(o, q) * stat_payoff_mult(share of `stance`) * heat_mult.

    `stance` is the stance this side played. V = (stat total / boss_total)**kappa.
    q is clipped to [0, 1]; there is no HAN timing modifier and no knot_window
    factor (the player's q_time is already the raw score at the visible zone).
    `heat_mult` is overrun_mult(x) for an overrun clash, LIMP_MULT when all three
    gauges are locked, else 1.0.
    """
    tot = pow_stat + en_stat + han_stat
    r = tot / boss_total if boss_total else 1.0
    V = r ** kappa
    q = 0.0 if q_time < 0.0 else 1.0 if q_time > 1.0 else q_time
    m = stat_payoff_mult(stance_share(stance, pow_stat, en_stat, han_stat))
    return V * clash_payoff(outcome, q) * m * heat_mult


def heat_share_mult(shares: tuple[float, float, float]) -> tuple[float, float, float]:
    """Capacity / recovery multipliers (HEAT_ORDER) for build shares (POW, HAN, EN): 3 s**e / sum(s**e)."""
    se = [max(0.0, x) ** HEAT_SHARE_EXP for x in shares]
    tot = sum(se)
    if tot <= 0:
        return (1.0, 1.0, 1.0)
    return tuple(3.0 * x / tot for x in se)


def heat_capacity(
    shares: tuple[float, float, float],
    r: float,
    avg_demand: tuple[float, float, float],
    cap_turns: float = HEAT_CAP_TURNS,
    recovery: float = HEAT_RECOVERY,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """(capacity, recovery per turn), each in HEAT_ORDER.

    cap_s = cap_turns x avg_demand_s x heat_share_mult_s x r**HEAT_R_EXP; recovery the same with `recovery`.
    `avg_demand` is heat.avg_heat_demand() (the cross-track average per-turn load).
    """
    k = heat_share_mult(shares)
    rr = r ** HEAT_R_EXP
    cap = tuple(cap_turns * a * m * rr for a, m in zip(avg_demand, k))
    rec = tuple(recovery * a * m * rr for a, m in zip(avg_demand, k))
    return cap, rec


def overrun_mult(x: float) -> float:
    """Payoff multiplier for overrun fraction x = (load - cap) / cap after the stance is added; 1.0 if x <= 0."""
    if x <= 0.0:
        return 1.0
    return max(OVERRUN_FLOOR, 1.0 - OVERRUN_SLOPE * x)


def counter_stance(s: Stance) -> Stance:
    """The stance that beats `s` (EN > POW > HAN > EN)."""
    if s == Stance.POW:
        return Stance.EN
    if s == Stance.HAN:
        return Stance.POW
    return Stance.HAN


def loser_to_stance(s: Stance) -> Stance:
    """The stance that loses to `s`."""
    if s == Stance.POW:
        return Stance.HAN
    if s == Stance.HAN:
        return Stance.EN
    return Stance.POW


# Stance index order used by the heat gauges (HEAT_ORDER): POW, HAN, EN.
_STANCE_INDEX = {Stance.POW: 0, Stance.HAN: 1, Stance.EN: 2}
_INDEX_STANCE = (Stance.POW, Stance.HAN, Stance.EN)


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
