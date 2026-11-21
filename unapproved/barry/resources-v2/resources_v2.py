"""resources-v2: hard-block resource model, no card draw, refit. Barry, 2026-11-13. DRAFT, NOT APPROVED.

Austin's decisions on v1 (2026-11-13): an empty resource is a HARD BLOCK on that stance, the card draw is deleted,
the equations get refit. Reads stay the core skill; retuning the car to track and opponent is the meta.

Reuses resources-v1 (../resources-v1/resources_v1.py) for the corner tables, line costs, tracks, tune grid and the
vectorised live (card-draw) model. New here:
  * hard block for BOTH sides; if no stance is affordable the car "limps" (plays its fullest resource at
    EMPTY_MULT payoff)                                                     PLACEHOLDER
  * TANK_MODE "race" (one tank for the whole race, v1) or "lap" (one lap's tank + REFILL share back between laps)
  * TRACK_NORMALIZE: every track asks for the same TOTAL wear, in a different mix (brings Street in line)
  * STYLE_BETA: boss styles only lean on the district lines instead of reordering them
  * diagnostics: share of races where the player's wanted stance was blocked at least once, and share of
    correctly-read corners where the read's counter was blocked
  * a random-read player (uniform among affordable stances) and a no-rationing player
Every tagged PLACEHOLDER is invented and needs Austin's decision.
"""
from __future__ import annotations
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "resources-v1"))
import resources_v1 as V1                     # noqa: E402  (corner tables, lines, tracks, live model)
from resources_v1 import E, C, P_, H_, E_, OUT, COUNTER, LOSER, parse, tracks, tune_grid, phi_vec, STYLES  # noqa: E402,F401

LAP = 10
STYLE_W = np.array(V1.STYLE_W)
DEFAULT_CFG = dict(
    TANK_MODE="lap",        # PLACEHOLDER: "race" = whole-race tank, no refill; "lap" = one lap's tank + REFILL between laps
    REFILL=0.5,             # PLACEHOLDER: share of the fuel/brake tank put back at the end of each lap (lap mode)
    TANK_FACTOR=1.0,        # PLACEHOLDER: even build's fuel/brake tank = this x the tank-period's average demand
    SUSP_TANK_TURNS=3.0,    # PLACEHOLDER (v1)
    SUSP_REC_FACTOR=0.8,    # PLACEHOLDER: suspension recovery per turn, x average per-turn demand (v1 was 0.6)
    SHARE_EXPONENT=1.5,     # PLACEHOLDER: tank multiplier = 3*share**e / sum(share**e) (v1 was 2)
    TANK_R_EXP=1.0,         # PLACEHOLDER: tanks x r**TANK_R_EXP (stat total vs boss)
    KAPPA_SCALE=1.0,        # PLACEHOLDER: x KAPPA_BY_LENGTH
    AGG_STEP=0.25,          # PLACEHOLDER (v1)
    EMPTY_MULT=0.4,         # PLACEHOLDER: payoff of a limp clash (nothing affordable)
    RATION_LAMBDA=0.6,      # PLACEHOLDER (player AI, v1)
    TRACK_NORMALIZE=True,   # PLACEHOLDER: scale each track's costs + passive wear to the cross-track average total
    TANK_REF_Q=0.6,         # PLACEHOLDER: tanks are sized on the demand of a player who reads 60% of corners
    DEMAND_SLANT=1.0,       # PLACEHOLDER: 1 = raw district mix, 0 = every track identical (see track_wear)
    MISREAD="random",       # PLACEHOLDER: "random" = an unread corner is a random guessed line, countered with the
                            #   same resource-aware choice; "live" = the live/v1 rule (tie w.p. q_read, else lose)
    STYLE_BETA=0.3,         # PLACEHOLDER: boss line weights = (1-b) x 65/21/14 + b x style order (v1 was b = 1)
    HOT_SWITCH=0.5, CONS_SWITCH=2 / 3,   # PLACEHOLDER (v1)
)


def cfg_of(cfg):
    c = dict(DEFAULT_CFG)
    if cfg:
        bad = set(cfg) - set(c)
        if bad:
            raise KeyError(bad)
        c.update(cfg)
    return c


def corner_demand_q(district, corner, agg, q):
    """Expected per-turn (fuel, susp, brakes) one corner costs a player with read skill q vs the 65/21/14 boss
    (live read model: correct read -> counters of the main line; misread -> each clash ties with prob q, else loses),
    plus passive wear. Exact over the 2^3 misread combinations, with the repeat rule."""
    import itertools
    tris = [parse(t) for t in C.line_triples(district, corner)]
    d = np.array(V1.CORNER_PASSIVE[corner], float)
    main = tris[0]
    rd = [int(COUNTER[s]) for s in main]
    for s, cc in zip(rd, V1.line_cost(rd, corner, agg)):
        d[s] += q * cc
    for w, ln in zip(STYLE_W, tris):
        for combo in itertools.product((0, 1), repeat=3):
            p = np.prod([q if b else 1 - q for b in combo])
            mine = [int(s) if b else int(LOSER[s]) for s, b in zip(ln, combo)]
            for s, cc in zip(mine, V1.line_cost(mine, corner, agg)):
                d[s] += (1 - q) * w * p * cc
    return d


def raw_demand(district, lap, agg, q=0.6):
    """Per-turn demand of a lap before normalisation, for read skill q."""
    return sum(corner_demand_q(district, x, agg, q) for x in lap) / len(lap)


_AVG = {}


def avg_raw(agg, q):
    if (agg, q) not in _AVG:
        _AVG[(agg, q)] = np.mean([raw_demand(d, lap, agg, q) for (d, _), lap in tracks().items()], axis=0)
    return _AVG[(agg, q)]


_W = {}


def track_wear(district, lap, c):
    """Per-resource multiplier (3,) on a track's stance costs and passive wear.

    TRACK_NORMALIZE: every track asks the same TOTAL wear (cross-track average), for the reference player.
    DEMAND_SLANT g: the track's mix is pulled toward even: target_s = total x ((1-g)/3 + g x raw_s/raw_total).
    g = 1 keeps the raw mix that falls out of the district lines; g = 0 makes every track identical.
    """
    k = (district, tuple(lap), c["AGG_STEP"], c["TANK_REF_Q"], c["TRACK_NORMALIZE"], c["DEMAND_SLANT"])
    if k not in _W:
        raw = raw_demand(district, lap, c["AGG_STEP"], c["TANK_REF_Q"])
        tot = avg_raw(c["AGG_STEP"], c["TANK_REF_Q"]).sum() if c["TRACK_NORMALIZE"] else raw.sum()
        g = c["DEMAND_SLANT"]
        target = tot * ((1 - g) / 3 + g * raw / raw.sum())
        _W[k] = target / raw
    return _W[k]


def track_demand(district, lap, c, q=None):
    q = c["TANK_REF_Q"] if q is None else q
    return raw_demand(district, lap, c["AGG_STEP"], q) * track_wear(district, lap, c)


def matched_tune(district, lap, c, grid):
    """Index of the grid tune closest (L1) to the track's demand mix: the 'tuned for the track' car."""
    d = track_demand(district, lap, c)
    s = d / d.sum()
    order = np.array([s[P_], s[H_], s[E_]])        # grid order is (POW, HAN, EN) = (fuel, susp, brakes)
    return int(np.argmin(np.abs(grid - order).sum(1)))


_AD = {}


def avg_demand(c):
    k = (c["AGG_STEP"], c["TANK_REF_Q"], c["TRACK_NORMALIZE"])
    if k not in _AD:
        _AD[k] = np.mean([track_demand(d, lap, c) for (d, _), lap in tracks().items()], axis=0)
    return _AD[k]


def tanks(shares, T, r, c):
    shares = np.atleast_2d(shares)
    a = avg_demand(c)
    se = shares ** c["SHARE_EXPONENT"]
    k = 3 * se / se.sum(axis=1, keepdims=True) * r ** c["TANK_R_EXP"]
    period = T if c["TANK_MODE"] == "race" else min(T, LAP)
    tank = np.empty_like(shares); rec = np.zeros_like(shares)
    tank[:, P_] = c["TANK_FACTOR"] * a[P_] * period * k[:, P_]
    tank[:, E_] = c["TANK_FACTOR"] * a[E_] * period * k[:, E_]
    tank[:, H_] = c["SUSP_TANK_TURNS"] * a[H_] * k[:, H_]
    rec[:, H_] = c["SUSP_REC_FACTOR"] * a[H_] * k[:, H_]
    return tank, rec


def style_weights(style, district, corner, t, T, c):
    w0 = V1.style_weights(style, district, corner, t, T, c["AGG_STEP"])   # v1 full reorder
    if style == "balanced":
        return STYLE_W.copy()
    # v1 used HOT_SWITCH / CONS_SWITCH module constants; same defaults
    return (1 - c["STYLE_BETA"]) * STYLE_W + c["STYLE_BETA"] * w0


def run_new(shares, r, district, lap, T, style, q_read, q_time, n, seed, cfg=None,
            mode="read", ration=True, scouted=True, opp_shares=(1 / 3, 1 / 3, 1 / 3)):
    """Returns dict: win (G,n) in {0,.5,1}; blocked_race (G,n) bool (any wanted stance blocked at least once);
    blocked_read_race (G,n) bool (the counter of a correct read blocked at least once); read_turns, read_blocked (G,n) counts; limp (G,n).

    mode "read": live read model (q_read) + resource-aware choice among affordable stances.
    mode "random": a uniformly random affordable stance every clash (no reads).
    """
    c = cfg_of(cfg)
    agg = c["AGG_STEP"]
    rng = np.random.default_rng(seed)
    shares = np.atleast_2d(np.asarray(shares, float)); G = shares.shape[0]
    V = r ** (V1.KAPPA[T] * c["KAPPA_SCALE"])
    php = phi_vec(q_time); pho = phi_vec(E.OPPONENT_QTE)
    em = c["EMPTY_MULT"]
    wear = track_wear(district, lap, c)
    dem = track_demand(district, lap, c, q=min(max(q_read, 0.0), 1.0))   # the AI plans with its own read skill
    tank, rec = tanks(shares, T, r, c)
    otank, orec = tanks(np.array([opp_shares]), T, 1.0, c)
    left = np.repeat(tank[:, None, :], n, axis=1)
    oleft = np.repeat(otank, n, axis=0)                     # (n,3)
    gp = np.zeros((G, n)); go = np.zeros((G, n))
    blocked = np.zeros((G, n), bool); blocked_read = np.zeros((G, n), bool); rturns = np.zeros(n); rblock = np.zeros((G, n)); limp = np.zeros((G, n))
    ar = np.arange(n)
    for t in range(T):
        corner = lap[t % len(lap)]
        tris = [parse(x) for x in C.line_triples(district, corner)]
        lines = np.array(tris)
        w = style_weights(style, district, corner, t, T, c)
        li = np.searchsorted(np.cumsum(w), rng.random(n), side="right").clip(0, 2)
        oline = lines[li]
        cost_tab = np.array(V1.CORNER_COST[corner]) * V1.BASE_COST * wear
        wg = w if scouted else STYLE_W
        guess = lines[int(np.argmax(wg))]
        read = rng.random(n) < q_read
        mis_tie = rng.random((n, 3)) < q_read
        rnd = rng.random((n, 3, 3))
        rturns += read
        rem = T - t
        # planned need until the next refill (lap mode) or the end (race mode)
        if c["TANK_MODE"] == "lap":
            horizon = min(rem, LAP - (t % LAP))
        else:
            horizon = rem
        need = dem * horizon
        rep = np.zeros((G, n, 3)); orep = np.zeros((n, 3))
        turn_rblock = np.zeros((G, n), bool)
        for i in range(3):
            # ── boss: planned stance, hard block -> most-remaining affordable, else limp
            ocs = cost_tab[None, :] * (1 + agg * orep)               # (n,3)
            oaff = oleft + 1e-9 >= ocs
            os_ = oline[:, i].copy()
            ok_ = oaff[ar, os_]
            alt = np.argmax(np.where(oaff, oleft - ocs, -1e9), axis=1)
            olimp = ~oaff.any(1)
            os_ = np.where(ok_, os_, np.where(olimp, np.argmax(oleft, 1), alt))
            oc = ocs[ar, os_]
            oleft[ar, os_] = np.maximum(0.0, oleft[ar, os_] - oc)
            orep[ar, os_] += 1
            # ── player
            cc = cost_tab[None, None, :] * (1 + agg * rep)           # (G,n,3)
            aff = left + 1e-9 >= cc
            none = ~aff.any(2)
            if mode == "random":
                key = np.where(aff, rnd[None, :, i, :], -1.0)
                choice = np.argmax(key, axis=2)
                want = choice
            else:
                # belief: a correct read -> the most likely line; no read -> a random guessed line (MISREAD="random").
                # MISREAD="live" keeps the live rule (tie with prob q_read, else the losing stance).
                if c["MISREAD"] == "random":
                    bel = np.where(read, guess[i], np.floor(rnd[:, i, 0] * 3).astype(int))      # (n,)
                    o_vs = OUT[:, bel]                                                         # (3,n)
                    gain = (V * php[o_vs + 1] - pho[-o_vs + 1]).T[None, :, :] + np.zeros((G, n, 3))
                    if ration:
                        rho = (left + rec[:, None, :] * horizon) / np.maximum(need[None, None, :], 1e-9)
                        gain = gain - c["RATION_LAMBDA"] * np.clip(1 - rho, 0, 1) * cc
                    choice = np.argmax(np.where(aff, gain, -1e9), axis=2)
                    want = np.broadcast_to(COUNTER[bel], (G, n))
                    want_ok = np.take_along_axis(aff, want[..., None], 2)[..., 0]
                    turn_rblock |= read[None, :] & ~want_ok
                    blocked_read |= read[None, :] & ~want_ok
                else:
                    gs = guess[i]
                    o_vs = OUT[:, gs]
                    gain = (V * php[o_vs + 1] - pho[-o_vs + 1])[None, None, :] + np.zeros((G, n, 3))
                    if ration:
                        rho = (left + rec[:, None, :] * horizon) / np.maximum(need[None, None, :], 1e-9)
                        gain = gain - c["RATION_LAMBDA"] * np.clip(1 - rho, 0, 1) * cc
                    choice_read = np.argmax(np.where(aff, gain, -1e9), axis=2)
                    mis = np.where(mis_tie[:, i], oline[:, i], LOSER[oline[:, i]])   # live misread rule (vs planned card)
                    want = np.where(read[None, :], COUNTER[gs], mis[None, :])
                    want_ok = np.take_along_axis(aff, want[..., None], 2)[..., 0]
                    alt_p = np.argmax(np.where(aff, rnd[None, :, i, :], -1.0), axis=2)
                    choice = np.where(read[None, :], choice_read, np.where(want_ok, want, alt_p))
                    turn_rblock |= read[None, :] & ~want_ok
                    blocked_read |= read[None, :] & ~want_ok
            want_ok = np.take_along_axis(aff, want[..., None], 2)[..., 0]
            blocked |= ~want_ok
            choice = np.where(none, np.argmax(left, 2), choice)
            limp += none
            o = OUT[choice, os_[None, :]]
            pm = np.where(none, em, 1.0); om = np.where(olimp, em, 1.0)[None, :]
            gp += V * php[o + 1] * pm
            go += pho[-o + 1] * om
            cst = np.take_along_axis(cc, choice[..., None], 2)[..., 0]
            lsel = np.take_along_axis(left, choice[..., None], 2)[..., 0]
            np.put_along_axis(left, choice[..., None], np.maximum(0.0, lsel - cst)[..., None], 2)
            np.put_along_axis(rep, choice[..., None], np.take_along_axis(rep, choice[..., None], 2) + 1, 2)
        rblock += turn_rblock
        pas = V1.CORNER_PASSIVE[corner]
        pas = np.array(pas) * wear
        left = np.minimum(np.maximum(0.0, left - pas) + rec[:, None, :], tank[:, None, :])
        oleft = np.minimum(np.maximum(0.0, oleft - pas) + orec[0], otank[0])
        if c["TANK_MODE"] == "lap" and (t + 1) % LAP == 0 and t + 1 < T:
            add = np.zeros(3); add[[P_, E_]] = 1.0
            left = np.minimum(left + c["REFILL"] * tank[:, None, :] * add, tank[:, None, :])
            oleft = np.minimum(oleft + c["REFILL"] * otank[0] * add, otank[0])
    win = (gp > go) + 0.5 * (gp == go)
    return dict(win=win, blocked_race=blocked, blocked_read_race=blocked_read, read_turns=np.broadcast_to(rturns, (G, n)), read_blocked=rblock, limp=limp)


def run_old(shares, r, district, lap, T, q_read, q_time, n, seed, random_read=False):
    """Live card-draw model (V1.run_old). random_read=True: the player plays random cards from the hand (live q=0
    'random player': every slot goes to a random leftover card)."""
    if not random_read:
        return V1.run_old(shares, r, district, lap, T, q_read, q_time, n, seed)
    return _run_old_random(shares, r, district, lap, T, q_time, n, seed)


def _run_old_random(shares, r, district, lap, T, q_time, n, seed):
    rng = np.random.default_rng(seed)
    shares = np.atleast_2d(np.asarray(shares, float)); G = shares.shape[0]
    V = r ** V1.KAPPA[T]
    ps, hs, es = shares[:, 0], shares[:, 1], shares[:, 2]
    qe = np.clip(q_time * (1 + E.ETA * (hs - 1 / 3)), 0, 1)
    Mw = 1 + E.MU * (ps - 1 / 3); Mo = 1 + E.MU * (es - 1 / 3)
    tq = np.array([V1.tau(x) for x in qe])
    PH = np.stack([E.L_MAX * tq * Mo, E.T_MAX * tq * Mo, (E.W0 + (1 - E.W0) * tq) * Mw], axis=1)
    pho = phi_vec(E.OPPONENT_QTE)
    raw = shares * E.DECK_ALPHA + (1 - E.DECK_ALPHA) / 3; dw = raw / raw.sum(1, keepdims=True)
    pr = np.array([E.LINE_ADHERENCE, (1 - E.LINE_ADHERENCE) * E.LINE_ALT_WEIGHTS["alt1"], (1 - E.LINE_ADHERENCE) * E.LINE_ALT_WEIGHTS["alt2"]])
    gp = np.zeros((G, n)); go = np.zeros((G, n))
    for t in range(T):
        corner = lap[t % len(lap)]
        lines = np.array([parse(x) for x in C.line_triples(district, corner)])
        li = np.searchsorted(np.cumsum(pr), rng.random(n), side="right").clip(0, 2); oline = lines[li]
        u = rng.random((G, n, 6)); cdf = np.cumsum(dw, axis=1)
        draws = (u[..., None] > cdf[:, None, None, :]).sum(-1).clip(0, 2)
        # 3 random cards out of the 6 (without replacement) = the first 3 of a random permutation; draws are iid,
        # so the first 3 draws are already a uniformly random 3-subset
        for i in range(3):
            o = OUT[draws[..., i], oline[None, :, i]]
            gp += V * np.take_along_axis(np.broadcast_to(PH[:, None, :], (G, n, 3)), (o + 1)[..., None], 2)[..., 0]
            go += pho[-o + 1]
    win = (gp > go) + 0.5 * (gp == go)
    return win.mean(1), win
