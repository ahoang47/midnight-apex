"""resources-v1: a raw first-pass model of the fuel / brakes / suspension resource system.

Barry, 2026-11-12. DRAFT, NOT APPROVED. Reads the live sim (sim/velocity_shift) read-only; changes nothing there.

New rules being tested (Austin, 2026-11-12):
  * No card draw. Every turn the player may pick ANY 3-stance line (Entry/Apex/Exit).
  * Each stance spends a resource: POW = fuel (no recovery), EN = brakes (no recovery),
    HAN = suspension (recovers every turn).
  * A tank's size (and suspension's recovery) scales with that stat's share of the build.
  * An empty / overdrawn resource weakens that stance's payoff (soft); a hard-block variant is also tested.
  * Tracks demand different resources through their corner mix.

Kept from the live model (sim/velocity_shift/equations.py): rock-paper-scissors POW>HAN>EN>POW, 3 clashes per turn,
Phi/tau clash payoff (W0, T_MAX, L_MAX, TAU_*), V = r**kappa with KAPPA_BY_LENGTH, opponent QTE 1.0, LINE_SET_C
and its 65/21/14 split, the q_read read model, the visible QTE zone for average play, and progress-total win rule.
Dropped: the deck/hand (DECK_ALPHA, HAND_SIZE, assign_hand) and the MU / ETA share multipliers (resources replace them).

Every number tagged PLACEHOLDER below is invented for this first pass and needs Austin's decision.
Vectorised over (tunes G) x (runs N). Stance index order everywhere: 0 = POW (fuel), 1 = HAN (suspension), 2 = EN (brakes).
"""
from __future__ import annotations
import os, sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "sim")))
from velocity_shift import equations as E          # noqa: E402  (read-only)
from velocity_shift import combat as C             # noqa: E402  (read-only: official_tracks, line_triples)

P_, H_, E_ = 0, 1, 2
LET = {"P": P_, "H": H_, "E": E_}
STANCE_NAMES = ("POW/fuel", "HAN/suspension", "EN/brakes")
# outcome[a, b] for player stance a vs opponent stance b: +1 win, 0 tie, -1 loss (POW>HAN>EN>POW)
OUT = np.array([[0, 1, -1],
                [-1, 0, 1],
                [1, -1, 0]])
COUNTER = np.array([E_, P_, H_])   # stance that beats POW, HAN, EN
LOSER = np.array([H_, E_, P_])     # stance that loses to POW, HAN, EN

# ───────────────────────────── PLACEHOLDERS (all invented, need Austin) ─────────────────────────────
# Corner demand: multiplier on what each stance costs at that corner type, order (fuel, suspension, brakes).
CORNER_COST = {   # PLACEHOLDER
    "HP":  (0.8, 1.2, 1.4),   # hairpin: heavy braking, big weight transfer
    "CR":  (1.0, 1.2, 0.8),   # constant radius: sustained load
    "DR":  (0.8, 1.1, 1.3),   # decreasing radius: trail braking
    "IR":  (1.3, 0.9, 0.7),   # increasing radius: on the throttle early
    "N90": (1.0, 0.8, 1.4),   # 90-degree street corner: hard stop
    "CH":  (0.9, 1.3, 1.1),   # chicane: quick direction changes
    "ES":  (0.8, 1.4, 0.9),   # esses: suspension working constantly
    "SW":  (1.4, 0.9, 0.6),   # sweeper: flat out
}
# Passive wear: what the corner itself drains each turn, whatever line is driven, order (fuel, suspension, brakes).
CORNER_PASSIVE = {  # PLACEHOLDER
    "HP":  (0.0, 0.3, 0.3),
    "CR":  (0.1, 0.2, 0.0),
    "DR":  (0.0, 0.2, 0.3),
    "IR":  (0.3, 0.1, 0.0),
    "N90": (0.1, 0.0, 0.4),
    "CH":  (0.0, 0.3, 0.2),
    "ES":  (0.0, 0.4, 0.1),
    "SW":  (0.4, 0.1, 0.0),
}
BASE_COST = 1.0            # PLACEHOLDER: cost of one stance at a demand-1.0 corner
AGG_STEP = 0.25            # PLACEHOLDER: "aggressive lines cost more": the k-th use of the same stance in one line
                           #   costs 1 + AGG_STEP*(k-1)  (so PPP costs 1+1.25+1.5 = 3.75 vs PHE 3.0)
TANK_FACTOR = 0.5          # PLACEHOLDER: an even-spread (1/3) build's fuel and brake tanks hold TANK_FACTOR x the
                           #   cross-track average race demand (perfect counter play vs a 65/21/14 opponent + passive wear)
SUSP_TANK_TURNS = 3.0      # PLACEHOLDER: even-spread suspension tank = this many turns of average suspension demand
SUSP_REC_FACTOR = 0.6      # PLACEHOLDER: even-spread suspension recovers this x the average per-turn demand each turn
SHARE_EXPONENT = 2.0       # PLACEHOLDER: tank (and recovery) = even-spread size x 3*share**e / sum(share**e)
EMPTY_MULT = 0.40          # PLACEHOLDER: payoff multiplier for the part of a stance the resource could not pay for
                           #   (soft rule: mult = EMPTY + (1-EMPTY)*min(1, left/cost))
RATION_LAMBDA = 0.6        # PLACEHOLDER (player AI): value given up per unit of a resource that is behind pace
# Opponent styles: weights over the district's three lines ranked by THIS corner's cost.
STYLE_W = (0.65, 0.21, 0.14)   # reuses LINE_ADHERENCE / LINE_ALT_WEIGHTS split (live)
STYLES = ("balanced", "hot_early", "conserver")
HOT_SWITCH = 0.5           # PLACEHOLDER: hot-early burns (costliest line first) for the first half, then saves
CONS_SWITCH = 2 / 3        # PLACEHOLDER: conserver saves (cheapest first) for the first 2/3, then dumps
# ────────────────────────────────────────────────────────────────────────────────────────────────

KAPPA = dict(E.KAPPA_BY_LENGTH)

# Model switches (defaults = the "v1 base" settings picked from calibrate.json / calibrate2.json; the runner
# overrides them per variant). All PLACEHOLDER.
DEFAULT_CFG = dict(
    TANK_FACTOR=TANK_FACTOR, SUSP_TANK_TURNS=SUSP_TANK_TURNS, SUSP_REC_FACTOR=SUSP_REC_FACTOR,
    SHARE_EXPONENT=SHARE_EXPONENT, EMPTY_MULT=EMPTY_MULT, RATION_LAMBDA=RATION_LAMBDA, AGG_STEP=AGG_STEP,
    EMPTY_RULE="payoff",        # "payoff": a dry stance's payoff x EMPTY_MULT (scaled by the unpaid share)
                                # "downgrade": the unpaid share of a dry stance drops one outcome step
                                #   (win->tie, tie->loss, loss->loss at EMPTY_MULT payoff), opponent mirrored
    TANK_WITH_R=True,           # True: tanks also scale with r (absolute stat vs the boss's matching stat)
    TANK_R_EXP=1.0,             # tank x r**TANK_R_EXP when TANK_WITH_R
    KAPPA_SCALE=1.0,            # multiplies every KAPPA_BY_LENGTH value (1.0 = live)
    PASSIVE_SCALE=1.0,          # multiplies CORNER_PASSIVE
)


def tau(q):
    return E.timing_value(q)


def phi_vec(q):
    """Player payoff by outcome index (loss, tie, win) at timing q (live Phi)."""
    t = tau(q)
    return np.array([E.L_MAX * t, E.T_MAX * t, E.W0 + (1 - E.W0) * t])


def line_cost(line, corner, agg=None):
    """Per-clash costs (3,) of a 3-stance line (stance indices) at a corner, with the repeat (aggression) rule."""
    agg = AGG_STEP if agg is None else agg
    seen = [0, 0, 0]
    out = []
    for s in line:
        out.append(BASE_COST * CORNER_COST[corner][s] * (1 + agg * seen[s]))
        seen[s] += 1
    return out


def parse(tri):
    return [LET[c] for c in tri]


def tracks():
    """All 15 official stand-in laps: {(district, name): [10 corner codes]}."""
    out = {}
    for d, tr in C.official_tracks().items():
        for name, seq in tr.items():
            out[(d, name)] = list(seq)
    return out


def tune_grid(step=0.05):
    """Stat-share builds (POW, HAN, EN) in the live build bounds (each 25-50%), step 5 pp."""
    g = []
    n = int(round(1 / step))
    for p in range(n + 1):
        for h in range(n + 1 - p):
            e = n - p - h
            sh = (p / n, h / n, e / n)
            if all(E.BUILD_STAT_MIN_SHARE - 1e-9 <= x <= E.BUILD_STAT_MAX_SHARE + 1e-9 for x in sh):
                g.append(sh)
    return np.array(g)


def cfg_of(cfg):
    c = dict(DEFAULT_CFG)
    if cfg:
        bad = set(cfg) - set(c)
        if bad:
            raise KeyError(bad)
        c.update(cfg)
    return c


# ─────────────────────────── demand calibration (sets tank sizes from the tracks themselves) ───────────────
def corner_demand(district, corner, cfg=None):
    """Expected (fuel, susp, brakes) one turn costs a perfect counter-player vs the 65/21/14 opponent, plus passive."""
    c = cfg_of(cfg)
    tris = [parse(t) for t in C.line_triples(district, corner)]
    d = c["PASSIVE_SCALE"] * np.array(CORNER_PASSIVE[corner], float)
    for w, ln in zip(STYLE_W, tris):
        mine = [int(COUNTER[s]) for s in ln]
        for s, cc in zip(mine, line_cost(mine, corner, c["AGG_STEP"])):
            d[s] += w * cc
    return d


def track_demand(district, lap, cfg=None):
    """Per-turn (fuel, susp, brakes) demand of a lap for a perfect counter-player vs a 65/21/14 opponent."""
    return sum(corner_demand(district, x, cfg) for x in lap) / len(lap)


def avg_demand(cfg=None):
    """Cross-track average per-turn demand (all 15 laps, equal weight). Sets the even-spread tank sizes."""
    tr = tracks()
    return np.mean([track_demand(d, lap, cfg) for (d, _), lap in tr.items()], axis=0)


def tanks(shares, T, r=1.0, cfg=None):
    """(tank (G,3), recovery (G,3)) for builds `shares` (G,3) in a T-turn race."""
    c = cfg_of(cfg)
    shares = np.atleast_2d(shares)
    a = avg_demand(c)
    # tank multiplier per resource; the three multipliers always sum to 3 (an even build gets 1, 1, 1), so a
    # SHARE_EXPONENT above 1 makes specialising steeper without creating extra total tank.
    se = shares ** c["SHARE_EXPONENT"]
    k = 3 * se / se.sum(axis=1, keepdims=True)
    if c["TANK_WITH_R"]:
        k = k * r ** c["TANK_R_EXP"]
    tank = np.empty_like(shares)
    rec = np.zeros_like(shares)
    tank[:, P_] = c["TANK_FACTOR"] * a[P_] * T * k[:, P_]
    tank[:, E_] = c["TANK_FACTOR"] * a[E_] * T * k[:, E_]
    tank[:, H_] = c["SUSP_TANK_TURNS"] * a[H_] * k[:, H_]
    rec[:, H_] = c["SUSP_REC_FACTOR"] * a[H_] * k[:, H_]
    return tank, rec


# ─────────────────────────── opponent line policy ───────────────────────────
def style_weights(style, district, corner, t, T, agg=None):
    """Weights over LINE_SET_C [main, alt1, alt2] for this corner and turn (0-based t)."""
    tris = C.line_triples(district, corner)
    if style == "balanced":
        return np.array(STYLE_W)
    costs = np.array([sum(line_cost(parse(x), corner, agg)) for x in tris])
    order_cheap = np.argsort(costs, kind="stable")
    order_dear = order_cheap[::-1]
    frac = t / T
    if style == "hot_early":
        order = order_dear if frac < HOT_SWITCH else order_cheap
    elif style == "conserver":
        order = order_cheap if frac < CONS_SWITCH else order_dear
    else:
        raise ValueError(style)
    w = np.zeros(3)
    w[order] = STYLE_W
    return w


# ─────────────────────────── one batch of races (new model) ───────────────────────────
def coverage(left, cost):
    """Share of a stance's cost the resource can pay (0..1)."""
    return np.where(cost > 0, np.clip(left / np.maximum(cost, 1e-12), 0, 1), 1.0)


def payoffs(o, cov, php, pho, V, c):
    """(player progress, opponent progress) for player outcome o (-1/0/1) and coverage of each side's stance.

    cov_p / cov_o are the player's / opponent's coverage. payoff rule: unpaid share x EMPTY_MULT on that side's own
    payoff. downgrade rule: the unpaid share of a side's stance plays one outcome step worse for that side.
    """
    cov_p, cov_o = cov
    em = c["EMPTY_MULT"]
    if c["EMPTY_RULE"] == "payoff":
        mp = em + (1 - em) * cov_p
        mo = em + (1 - em) * cov_o
        return V * php[o + 1] * mp, pho[-o + 1] * mo
    # downgrade: effective outcome is a mix; each side's dryness shifts the outcome against that side
    # player-side shift: o -> o-1 with prob (1-cov_p); opponent-side shift: o -> o+1 with prob (1-cov_o)
    gp = 0.0; go = 0.0
    for sp, wp in ((0, cov_p), (-1, 1 - cov_p)):
        for so, wo in ((0, cov_o), (1, 1 - cov_o)):
            oo = o + sp + so
            w = wp * wo
            extra_p = np.where(oo < -1, em, 1.0)   # below loss: loss at reduced payoff for the player
            extra_o = np.where(oo > 1, em, 1.0)    # above win (opponent below loss): reduced for opponent
            oc = np.clip(oo, -1, 1)
            gp = gp + w * V * php[oc + 1] * extra_p
            go = go + w * pho[-oc + 1] * extra_o
    return gp, go


def run_new(shares, r, district, lap, T, style, q_read, q_time, n, seed,
            hard_block=False, scouted=True, ration=True, opp_shares=(1 / 3, 1 / 3, 1 / 3), cfg=None):
    """Win rate (G,) and per-run wins (G,n) for builds `shares` vs a boss with r = player total / boss total.

    q_time: player's raw QTE for the race (already the visible-zone value). Opponent QTE = E.OPPONENT_QTE.
    Common random numbers: all builds see the same opponent lines and read rolls.
    """
    c = cfg_of(cfg)
    agg = c["AGG_STEP"]
    rng = np.random.default_rng(seed)
    shares = np.atleast_2d(np.asarray(shares, float))
    G = shares.shape[0]
    V = r ** (KAPPA[T] * c["KAPPA_SCALE"])
    php = phi_vec(q_time)          # player (loss, tie, win)
    pho = phi_vec(E.OPPONENT_QTE)  # opponent
    tank, rec = tanks(shares, T, r, c)
    otank, orec = tanks(np.array([opp_shares]), T, 1.0, c)
    left = np.repeat(tank[:, None, :], n, axis=1)          # (G,n,3)
    oleft = np.repeat(otank[:, None, :], n, axis=1)[0]     # (n,3)  opponent spending does not depend on the player
    gp = np.zeros((G, n)); go = np.zeros((G, n))
    dem = track_demand(district, lap, c)
    ar = np.arange(n)
    for t in range(T):
        corner = lap[t % len(lap)]
        tris = [parse(x) for x in C.line_triples(district, corner)]
        w = style_weights(style, district, corner, t, T, agg)
        u = rng.random(n)
        li = np.searchsorted(np.cumsum(w), u, side="right").clip(0, 2)   # opponent line index per run
        lines = np.array(tris)                                        # (3,3)
        oline = lines[li]                                             # (n,3) opponent stances
        ocost = np.array([line_cost(tr, corner, agg) for tr in tris])[li]  # (n,3)
        # player's guess (all three LINE_SET_C lines share Entry, so a correct Entry read = most likely line)
        wg = w if scouted else np.array(STYLE_W)
        guess = lines[int(np.argmax(wg))]
        read = rng.random(n) < q_read                                 # (n,)
        mis_tie = rng.random((n, 3)) < q_read
        remaining_turns = T - t
        need = dem * remaining_turns          # planned need for the shadow price
        rep = np.zeros((G, n, 3))
        for i in range(3):
            os_ = oline[:, i]
            oc = ocost[:, i]
            ol = oleft[ar, os_]
            ocov = coverage(ol, oc)                                    # (n,)
            oleft[ar, os_] = np.maximum(0.0, ol - oc)
            cc = BASE_COST * np.array(CORNER_COST[corner])[None, None, :] * (1 + agg * rep)   # (G,n,3)
            cov = coverage(left, cc)                                   # (G,n,3)
            gs = guess[i]
            gain = np.empty((G, n, 3))
            for s in range(3):
                o_s = OUT[s, gs]
                gpp, gop = payoffs(np.full((G, n), o_s), (cov[..., s], np.ones((G, n))), php, pho, V, c)
                gain[..., s] = gpp - gop
            if ration:
                rho = np.where(need[None, None, :] > 0,
                               (left + rec[:, None, :] * remaining_turns) / np.maximum(need[None, None, :], 1e-9), 9.0)
                lam = c["RATION_LAMBDA"] * np.clip(1 - rho, 0, 1)
                gain = gain - lam * cc
            if hard_block:
                gain = np.where(left + 1e-9 < cc, -1e9, gain)
            choice_read = np.argmax(gain, axis=2)                     # (G,n)
            mis = np.where(mis_tie[:, i], os_, LOSER[os_])            # (n,)  live misread rule
            choice = np.where(read[None, :], choice_read, mis[None, :])
            if hard_block:
                blocked = np.take_along_axis(left + 1e-9 < cc, choice[..., None], 2)[..., 0]
                alt = np.argmax(left - cc, axis=2)
                choice = np.where(blocked, alt, choice)
            o = OUT[choice, os_[None, :]]                             # (G,n)
            cv = np.take_along_axis(cov, choice[..., None], 2)[..., 0]
            cst = np.take_along_axis(cc, choice[..., None], 2)[..., 0]
            a_, b_ = payoffs(o, (cv, np.broadcast_to(ocov, (G, n))), php, pho, V, c)
            gp += a_; go += b_
            l_sel = np.take_along_axis(left, choice[..., None], 2)[..., 0]
            np.put_along_axis(left, choice[..., None], np.maximum(0.0, l_sel - cst)[..., None], 2)
            np.put_along_axis(rep, choice[..., None], (np.take_along_axis(rep, choice[..., None], 2) + 1), 2)
        pas = c["PASSIVE_SCALE"] * np.array(CORNER_PASSIVE[corner])
        left = np.minimum(np.maximum(0.0, left - pas) + rec[:, None, :], tank[:, None, :])
        oleft = np.minimum(np.maximum(0.0, oleft - pas) + orec[0], otank[0])
    win = (gp > go) + 0.5 * (gp == go)
    return win.mean(axis=1), win


# ─────────────────────────── the live (old) model, vectorised, for comparison ───────────────────────────
def run_old(shares, r, district, lap, T, q_read, q_time, n, seed):
    """Live model: 6-card stat-weighted hand, v4 read + assign_hand, Phi/tau with MU/ETA; balanced boss, QTE 1.0.

    Same rules as combat.plan_player_cards / equations.assign_hand / clash_progress (validated in validate_old.py).
    Stance order here (POW, HAN, EN) matches deck_weights.
    """
    rng = np.random.default_rng(seed)
    shares = np.atleast_2d(np.asarray(shares, float))
    G = shares.shape[0]
    kap = KAPPA[T]
    V = r ** kap
    ps, hs, es = shares[:, 0], shares[:, 1], shares[:, 2]
    qe = np.clip(q_time * (1 + E.ETA * (hs - 1 / 3)), 0, 1)
    Mw = 1 + E.MU * (ps - 1 / 3); Mo = 1 + E.MU * (es - 1 / 3)
    tq = np.array([tau(x) for x in qe])
    phw = (E.W0 + (1 - E.W0) * tq) * Mw; pht = E.T_MAX * tq * Mo; phl = E.L_MAX * tq * Mo
    PH = np.stack([phl, pht, phw], axis=1)                   # (G,3) by outcome+1
    pho = phi_vec(E.OPPONENT_QTE)
    raw = shares * E.DECK_ALPHA + (1 - E.DECK_ALPHA) / 3
    dw = raw / raw.sum(1, keepdims=True)                     # (G,3) POW,HAN,EN
    gp = np.zeros((G, n)); go = np.zeros((G, n))
    pr = np.array(E.LINE_ADHERENCE * np.array([1, 0, 0]) + (1 - E.LINE_ADHERENCE) *
                  np.array([0, E.LINE_ALT_WEIGHTS["alt1"], E.LINE_ALT_WEIGHTS["alt2"]]))
    for t in range(T):
        corner = lap[t % len(lap)]
        lines = np.array([parse(x) for x in C.line_triples(district, corner)])
        li = np.searchsorted(np.cumsum(pr), rng.random(n), side="right").clip(0, 2)
        oline = lines[li]
        guess = lines[0]                                     # all share Entry -> main is the most likely
        read = rng.random(n) < q_read
        mis_tie = rng.random((n, 3)) < q_read
        # hand: 6 i.i.d. draws per build (independent per build; CRN on lines/read only)
        u = rng.random((G, n, 6))
        cdf = np.cumsum(dw, axis=1)
        draws = (u[..., None] > cdf[:, None, None, :]).sum(-1).clip(0, 2)   # (G,n,6)
        cnt = np.stack([(draws == k).sum(-1) for k in range(3)], axis=-1)   # (G,n,3)
        want = np.where(read[:, None], COUNTER[guess][None, :], np.where(mis_tie, oline, LOSER[oline]))  # (n,3)
        fb = np.where(read[:, None], guess[None, :], -1)                                                 # (n,3)
        out = -np.ones((G, n, 3), int)
        for i in range(3):
            wi = np.broadcast_to(want[:, i], (G, n))
            have = np.take_along_axis(cnt, wi[..., None], 2)[..., 0] > 0
            out[..., i] = np.where(have, wi, -1)
            np.put_along_axis(cnt, wi[..., None], (np.take_along_axis(cnt, wi[..., None], 2) - have[..., None]), 2)
        for i in range(3):
            fi = np.broadcast_to(fb[:, i], (G, n))
            ok = (out[..., i] < 0) & (fi >= 0)
            fi2 = np.where(fi >= 0, fi, 0)
            have = ok & (np.take_along_axis(cnt, fi2[..., None], 2)[..., 0] > 0)
            out[..., i] = np.where(have, fi2, out[..., i])
            np.put_along_axis(cnt, fi2[..., None], (np.take_along_axis(cnt, fi2[..., None], 2) - have[..., None]), 2)
        for i in range(3):
            need = out[..., i] < 0
            tot = cnt.sum(-1)
            pick = np.floor(rng.random((G, n)) * np.maximum(tot, 1)).astype(int)
            s = (pick[..., None] >= np.cumsum(cnt, -1)).sum(-1).clip(0, 2)
            out[..., i] = np.where(need, s, out[..., i])
            np.put_along_axis(cnt, s[..., None], (np.take_along_axis(cnt, s[..., None], 2) - need[..., None]), 2)
        for i in range(3):
            o = OUT[out[..., i], oline[None, :, i]]
            gp += V * np.take_along_axis(PH[:, None, :].repeat(n, 1), (o + 1)[..., None], 2)[..., 0]
            go += pho[(-o) + 1]
    win = (gp > go) + 0.5 * (gp == go)
    return win.mean(axis=1), win
