"""resources-v3: all-regenerating "heat/load" resource model with OVERRUN (no hard block), no card draw.
Barry, 2026-11-13. DRAFT, NOT APPROVED.

Austin's decisions (2026-11-13; these override the earlier whole-race-tank and hard-block briefs):
  * ALL THREE resources regenerate during the race: POW = engine heat, EN = brake/tire heat, HAN = suspension load.
  * Each stance ADDS LOAD to its resource. Each resource has a CAPACITY and a RECOVERY per turn. Both scale with
    that stat's share of the build (the stat mix sets the recovery rate).
  * SELECTABLE WHILE NOT FULL: a stance can be picked as long as its bar is not full, even if playing it pushes
    the load past capacity. That overrun is allowed, but the clash pays less (overrun-penalty curve, placeholder).
  * LOCK + HYSTERESIS: once a bar is full (load >= capacity) that stance is LOCKED, and stays locked until recovery
    brings the load below RELEASE x capacity (placeholder), not the moment it dips under full. Load carries over.
  * No fixed tanks, no race-length scaling, no refills. No card draw. Live misread rule (tie w.p. q_read, else lose).

Per clash: only unlocked stances are selectable. load_s += cost of the stance played. Overrun fraction
x = max(0, load_s - cap_s) / cap_s, measured after the stance is added; the clash's own payoff (V x Phi for the player,
Phi for the boss) is multiplied by pen(x) (see penalty()). If load_s >= cap_s the stance locks (also mid-turn).
After a turn's 3 clashes: load += passive corner load (can also lock), then load = max(0, load - rec), then any
locked stance with load < RELEASE x cap unlocks. If all three stances are locked the side "limps": it plays its
least-loaded stance at LIMP_MULT payoff.                                                     PLACEHOLDER
Load is NOT capped, so it carries over. The car starts the race cold (load 0).           PLACEHOLDER (start state)

Reuses resources-v2 (../resources-v2/resources_v2.py) for track-wear normalisation, demand calibration and boss
styles, and resources-v1 (via v2) for corner tables, line costs, tracks, tune grid and the live card-draw model.
Every tagged PLACEHOLDER is invented and needs Austin's decision.
"""
from __future__ import annotations
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "resources-v2"))
import resources_v2 as V2                       # noqa: E402
from resources_v2 import V1, E, C, P_, H_, E_, OUT, COUNTER, LOSER, parse, tracks, tune_grid, phi_vec, STYLES  # noqa: E402,F401

STYLE_W = V2.STYLE_W
DEFAULT_CFG = dict(
    CAP_TURNS=3.0,          # PLACEHOLDER: an even build's capacity = this x the cross-track average per-turn load
    REC_FACTOR=1.0,         # PLACEHOLDER: an even build's recovery per turn = this x the cross-track average per-turn load
    CAP_SHARE_EXP=1.5,      # PLACEHOLDER: capacity multiplier = 3*s**e / sum(s**e) (sums to 3: specialising adds no total)
    REC_SHARE_EXP=1.5,      # PLACEHOLDER: same curve for recovery
    CAP_R_EXP=1.0,          # PLACEHOLDER: capacity x r**CAP_R_EXP (stat total vs boss)
    REC_R_EXP=1.0,          # PLACEHOLDER: recovery x r**REC_R_EXP
    KAPPA_SCALE=1.0,        # PLACEHOLDER: x live KAPPA_BY_LENGTH
    PEN_SHAPE="linear",     # PLACEHOLDER: "linear" pen = max(FLOOR, 1 - SLOPE*x); "quadratic" pen = max(FLOOR, 1 - SLOPE*x**2)
    PEN_SLOPE=2.0,          # PLACEHOLDER
    PEN_FLOOR=0.4,          # PLACEHOLDER: the least an overrun clash can pay (share of normal payoff)
    RELEASE=0.7,            # PLACEHOLDER: a locked stance unlocks once load < RELEASE x capacity (hysteresis)
    LIMP_MULT=0.4,          # PLACEHOLDER: payoff when all three stances are locked
    AGG_STEP=0.25,          # PLACEHOLDER (v1): k-th repeat of a stance in one line costs 1 + AGG_STEP*(k-1)
    RATION_LAMBDA=0.6,      # PLACEHOLDER (player AI): price per unit of load when the lookahead says headroom is short
    RATION_H=3,             # PLACEHOLDER (player AI): lookahead in turns (the track is known: real upcoming corners)
    TRACK_NORMALIZE=True,   # PLACEHOLDER (v2): every track asks the same total load, in a different mix
    TANK_REF_Q=0.6,         # PLACEHOLDER (v2): loads are calibrated on a player who reads 60% of corners
    DEMAND_SLANT=1.0,       # PLACEHOLDER (v2): 1 = raw district mix
    STYLE_BETA=0.3,         # PLACEHOLDER (v2): boss style blend into 65/21/14
)


def cfg_of(cfg):
    c = dict(DEFAULT_CFG)
    if cfg:
        bad = set(cfg) - set(c)
        if bad:
            raise KeyError(bad)
        c.update(cfg)
    return c


def v2cfg(c):
    return V2.cfg_of(dict(AGG_STEP=c["AGG_STEP"], TANK_REF_Q=c["TANK_REF_Q"], TRACK_NORMALIZE=c["TRACK_NORMALIZE"],
                          DEMAND_SLANT=c["DEMAND_SLANT"], STYLE_BETA=c["STYLE_BETA"]))


def share_mult(shares, e):
    se = np.atleast_2d(shares) ** e
    return 3 * se / se.sum(axis=1, keepdims=True)


def capacity(shares, r, c):
    """(capacity (G,3), recovery per turn (G,3)). Same rule for all three resources; no race-length term."""
    a = V2.avg_demand(v2cfg(c))
    cap = c["CAP_TURNS"] * a[None, :] * share_mult(shares, c["CAP_SHARE_EXP"]) * r ** c["CAP_R_EXP"]
    rec = c["REC_FACTOR"] * a[None, :] * share_mult(shares, c["REC_SHARE_EXP"]) * r ** c["REC_R_EXP"]
    return cap, rec


def penalty(x, c):
    """Payoff multiplier for overrun fraction x >= 0 (0 = within capacity -> 1.0)."""
    if c["PEN_SHAPE"] == "linear":
        p = 1 - c["PEN_SLOPE"] * x
    elif c["PEN_SHAPE"] == "quadratic":
        p = 1 - c["PEN_SLOPE"] * x * x
    else:
        raise ValueError(c["PEN_SHAPE"])
    return np.where(x > 0, np.maximum(c["PEN_FLOOR"], p), 1.0)


_CD = {}


def corner_need(district, corner, c, q):
    k = (district, corner, c["AGG_STEP"], q)
    if k not in _CD:
        _CD[k] = V2.corner_demand_q(district, corner, c["AGG_STEP"], q)
    return _CD[k]


def run_new(shares, r, district, lap, T, style, q_read, q_time, n, seed, cfg=None,
            mode="read", ration=True, scouted=True, opp_shares=(1 / 3, 1 / 3, 1 / 3)):
    """Returns dict; arrays are (G,n) unless noted.
      win
      ov_clash      clashes played in overrun (count, of 3T);  ov_turns  turns with >= 1 overrun clash (of T)
      pen_loss      sum over clashes of (1 - payoff multiplier) from overrun
      lock_turns    turns where at least one stance was locked at some clash (of T)
      lock_clash    clashes where at least one stance was locked
      limp          clashes with all three locked
      n_locks, lock_dur_sum   (G,) lock episodes and their summed durations (summed over n). Duration = number of
                    later corners the stance stays locked after the corner it locked in (0 = free again next corner);
                    a lock still on at the finish counts to the finish (censored)
      lock_hist (G,T+1)  histogram of lock durations
      lock_streak   longest run of consecutive turns with any stance locked
      read_clash    clashes on correctly-read turns;  read_lock  ... where the read's counter was locked
      read_ov       read clashes where the counter was selectable but would overrun;  read_ov_play  ... played anyway
      read_switch   read clashes where the player did not play the counter
      lock_t (G,T)  share of races with a stance locked at turn t;  ov_t (G,T) same for overrun clashes
      lock_res (G,3) lock episodes by resource (summed over n);  boss_ov, boss_lock (n,)
    mode "read": live read model (q_read). Read turn: best selectable stance by immediate value (it sees its gauges,
      so the overrun penalty is included) minus, if ration, a lookahead price. Misread: the live rule's stance
      (tie w.p. q_read, else the losing stance) if selectable, else a random selectable stance.
    mode "random": a uniformly random selectable stance every clash (no reads).
    The boss plays its planned stance if selectable, else the selectable stance with the lowest load share, else limps.
    PLACEHOLDER (boss policy).
    """
    c = cfg_of(cfg); c2 = v2cfg(c)
    agg = c["AGG_STEP"]
    rng = np.random.default_rng(seed)
    shares = np.atleast_2d(np.asarray(shares, float)); G = shares.shape[0]
    V = r ** (V1.KAPPA[T] * c["KAPPA_SCALE"])
    php = phi_vec(q_time); pho = phi_vec(E.OPPONENT_QTE)
    wear = V2.track_wear(district, lap, c2)
    qd = min(max(q_read, 0.0), 1.0)
    H = c["RATION_H"]; REL = c["RELEASE"]; LM = c["LIMP_MULT"]
    need_c = np.array([corner_need(district, lap[t % len(lap)], c, qd) * wear for t in range(T + H)])
    cap, rec = capacity(shares, r, c)
    ocap, orec = capacity(np.array([opp_shares]), 1.0, c)
    capb = cap[:, None, :]; ocp = ocap[0]
    load = np.zeros((G, n, 3)); oload = np.zeros((n, 3))
    lock = np.zeros((G, n, 3), bool); olock = np.zeros((n, 3), bool)
    lstart = np.zeros((G, n, 3), int)
    gp = np.zeros((G, n)); go = np.zeros((G, n))
    z = lambda: np.zeros((G, n))
    ov_clash, ov_turns, pen_loss, lock_turns, lock_clash, limp = z(), z(), z(), z(), z(), z()
    lock_streak, cur = z(), z()
    read_clash = np.zeros(n); read_lock, read_ov, read_ov_play, read_switch = z(), z(), z(), z()
    n_locks = np.zeros(G); dur_sum = np.zeros(G); hist = np.zeros((G, T + 1)); lock_res = np.zeros((G, 3))
    lock_t = np.zeros((G, T)); ov_t = np.zeros((G, T)); boss_ov = np.zeros(n); boss_lock = np.zeros(n)
    ar = np.arange(n); gi = np.arange(G)

    def close_locks(mask, t_end):
        """Record durations for lock episodes in mask (G,n,3) ending after turn t_end."""
        d = np.where(mask, t_end - lstart, 0)
        n_locks[:] += mask.sum((1, 2)); dur_sum[:] += d.sum((1, 2))
        for g in range(G):
            hist[g] += np.bincount(d[g][mask[g]], minlength=T + 1)[:T + 1]

    def new_locks(t):
        nonlocal lock
        nl = (load >= capb - 1e-9) & ~lock
        lstart[nl] = t; lock |= nl
        lock_res[:] += nl.sum(1)

    for t in range(T):
        corner = lap[t % len(lap)]
        lines = np.array([parse(x) for x in C.line_triples(district, corner)])
        w = V2.style_weights(style, district, corner, t, T, c2)
        li = np.searchsorted(np.cumsum(w), rng.random(n), side="right").clip(0, 2)
        oline = lines[li]
        cost_tab = np.array(V1.CORNER_COST[corner]) * V1.BASE_COST * wear
        wg = w if scouted else STYLE_W
        guess = lines[int(np.argmax(wg))]
        read = rng.random(n) < q_read
        mis_tie = rng.random((n, 3)) < q_read
        rnd = rng.random((n, 3, 3))
        needH = need_c[t:t + H].sum(0)
        rep = np.zeros((G, n, 3)); orep = np.zeros((n, 3))
        turn_ov = np.zeros((G, n), bool); turn_lock = np.zeros((G, n), bool)
        for i in range(3):
            # ── boss
            ocs = cost_tab[None, :] * (1 + agg * orep)
            osel = ~olock
            os_ = oline[:, i].copy()
            ok_ = osel[ar, os_]
            alt = np.argmin(np.where(osel, oload / ocp, 1e9), axis=1)
            olimp = ~osel.any(1)
            os_ = np.where(ok_, os_, np.where(olimp, np.argmin(oload / ocp, 1), alt))
            oc = ocs[ar, os_]
            oload[ar, os_] += oc
            ox = np.maximum(0.0, oload[ar, os_] - ocp[os_]) / ocp[os_]
            om = np.where(olimp, LM, penalty(ox, c))[None, :]
            boss_ov += ox > 0; boss_lock += ~osel.all(1)
            orep[ar, os_] += 1
            olock |= oload >= ocp[None, :] - 1e-9
            # ── player
            sel = ~lock
            none = ~sel.any(2)
            turn_lock |= ~sel.all(2); lock_clash += ~sel.all(2)
            cc = cost_tab[None, None, :] * (1 + agg * rep)
            x_if = np.maximum(0.0, load + cc - capb) / capb
            m_if = penalty(x_if, c)
            if mode == "random":
                choice = np.argmax(np.where(sel, rnd[None, :, i, :], -1.0), axis=2)
            else:
                gs = guess[i]
                o_vs = OUT[:, gs]
                gain = (V * php[o_vs + 1])[None, None, :] * m_if - pho[-o_vs + 1][None, None, :]
                if ration:
                    head = capb - load + rec[:, None, :] * (H - 1)
                    rho = head / np.maximum(needH[None, None, :], 1e-9)
                    gain = gain - c["RATION_LAMBDA"] * np.clip(1 - rho, 0, 1) * cc
                choice_read = np.argmax(np.where(sel, gain, -1e9), axis=2)
                mis = np.where(mis_tie[:, i], oline[:, i], LOSER[oline[:, i]])
                mis_ok = np.take_along_axis(sel, np.broadcast_to(mis, (G, n))[..., None], 2)[..., 0]
                alt_p = np.argmax(np.where(sel, rnd[None, :, i, :], -1.0), axis=2)
                choice = np.where(read[None, :], choice_read, np.where(mis_ok, mis[None, :], alt_p))
                ctr = COUNTER[gs]
                ctr_lock = lock[..., ctr]
                ctr_ov = ~ctr_lock & (x_if[..., ctr] > 0)
                read_clash += read
                read_lock += read[None, :] & ctr_lock
                read_ov += read[None, :] & ctr_ov
                read_ov_play += read[None, :] & ctr_ov & (choice == ctr)
                read_switch += read[None, :] & (choice != ctr)
            choice = np.where(none, np.argmin(load / capb, 2), choice)
            limp += none
            x = np.take_along_axis(x_if, choice[..., None], 2)[..., 0]
            pm = np.where(none, LM, np.take_along_axis(m_if, choice[..., None], 2)[..., 0])
            o = OUT[choice, os_[None, :]]
            gp += V * php[o + 1] * pm
            go += pho[-o + 1] * om
            ovc = (x > 0) & ~none
            ov_clash += ovc; turn_ov |= ovc; pen_loss += 1 - pm
            cst = np.take_along_axis(cc, choice[..., None], 2)[..., 0]
            np.put_along_axis(load, choice[..., None], (np.take_along_axis(load, choice[..., None], 2)[..., 0] + cst)[..., None], 2)
            np.put_along_axis(rep, choice[..., None], np.take_along_axis(rep, choice[..., None], 2) + 1, 2)
            new_locks(t)
        pas = np.array(V1.CORNER_PASSIVE[corner]) * wear
        load = load + pas; new_locks(t)
        load = np.maximum(0.0, load - rec[:, None, :])
        rel = lock & (load < REL * capb - 1e-9)
        close_locks(rel, t); lock &= ~rel
        oload = np.maximum(0.0, oload + pas - orec[0])
        olock &= ~(oload < REL * ocp[None, :] - 1e-9)
        ov_turns += turn_ov; lock_turns += turn_lock
        cur = np.where(turn_lock, cur + 1, 0); lock_streak = np.maximum(lock_streak, cur)
        lock_t[:, t] = turn_lock.mean(1); ov_t[:, t] = turn_ov.mean(1)
    close_locks(lock, T - 1)
    win = (gp > go) + 0.5 * (gp == go)
    return dict(win=win, ov_clash=ov_clash, ov_turns=ov_turns, pen_loss=pen_loss, lock_turns=lock_turns, lock_clash=lock_clash,
                limp=limp, n_locks=n_locks, lock_dur_sum=dur_sum, lock_hist=hist, lock_streak=lock_streak,
                read_clash=np.broadcast_to(read_clash, (G, n)), read_lock=read_lock, read_ov=read_ov, read_ov_play=read_ov_play,
                read_switch=read_switch, lock_t=lock_t, ov_t=ov_t, lock_res=lock_res, boss_ov=boss_ov, boss_lock=boss_lock)
