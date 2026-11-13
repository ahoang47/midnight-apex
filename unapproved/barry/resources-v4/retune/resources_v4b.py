"""resources-v4b (retune pass; copied from ../resources_v4.py, which is unchanged).
v4b adds: STAT_M_W (stat share of the played stance scales its clash payoff), DIST_SIG (per-district load
signature on top of the track wear), and fixes the avg_demand cache so DEMAND_SLANT / DIST_SIG changes recalibrate capacity.

resources-v4 (copied from resources-v3/resources_v3.py; v3 itself untouched):
v4 adds per-length kappa, a planned-pacing player, a random-guess reader, and heat-stakes knobs.

resources-v3: all-regenerating "heat/load" resource model with OVERRUN (no hard block), no card draw.
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
sys.path.insert(0, os.path.join(HERE, "..", "..", "resources-v2"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "resources-v3"))
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
    # ── v4 additions
    KAPPA_10=None,          # PLACEHOLDER: per-length multiplier on live kappa (None -> KAPPA_SCALE)
    KAPPA_20=None,
    KAPPA_30=None,
    PLAN_LAMBDA=1.0,        # PLACEHOLDER (player AI): weight on the planner's forecast loss
    PLAN_H=5,               # PLACEHOLDER (player AI): planner lookahead in turns (real upcoming corners, scouted boss)
    RES_T=0.8,              # PLACEHOLDER (player AI, "reserve"): soft ceiling on the bar, as a share of capacity
    RES_K=1.0,              # PLACEHOLDER (player AI, "reserve"): price at full capacity, in clash-edges (win vs tie)
    BOSS_REC_FACTOR=None,   # PLACEHOLDER: boss heat recovery (None = same as player). v4 holds the boss at v3 rules so a
    BOSS_RELEASE=None,      #   harsher player gauge does not make the boss overheat and hand over the race (story flag)
    BOSS_CAP_TURNS=None,
    STAT_M_W=0.0,           # PLACEHOLDER (v4b): player clash payoff x (1 + STAT_M_W x (share of the stance played - 1/3));
                            #   live M uses 0.5 on POW/EN share. Boss is even (x1).
    DIST_SIG=0.0,           # PLACEHOLDER (v4b): strength of a per-district load signature (see DIST_SIG_MIX); 0 = off
    PACE_Q=1.0,             # PLACEHOLDER (player AI, "mix"): share of turns the player paces with the reserve rule;
                            #   the other turns it plays greedy (the pacing analogue of read skill q)
    RES_LOOK=0.0,           # PLACEHOLDER (player AI, "reserve"): lowers the ceiling by this x (next-PLAN_H-turn
                            #   planned load - recovery) / capacity when the upcoming corners need that bar
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


# PLACEHOLDER (v4b): district load signatures, order (POW/engine, HAN/suspension, EN/brakes). The wear multiplier is
# 1 + DIST_SIG x 3 x (sig - 1/3), then renormalised so the track's total load is unchanged.
DIST_SIG_MIX = {"street": (0.25, 0.25, 0.50),   # stop-start grid: brakes cook
                "touge": (0.25, 0.50, 0.25),    # switchbacks: suspension works
                "wangan": (0.50, 0.25, 0.25)}   # flat-out highway: engine heat


def wear_of(district, lap, c):
    w = V2.track_wear(district, lap, v2cfg(c))
    if c["DIST_SIG"]:
        raw = V2.raw_demand(district, lap, c["AGG_STEP"], c["TANK_REF_Q"]) * w
        m = 1 + c["DIST_SIG"] * 3 * (np.array(DIST_SIG_MIX[district]) - 1 / 3)
        m = np.maximum(m, 0.05)
        w = w * m * raw.sum() / (raw * m).sum()
    return w


_ADV = {}


def avg_demand_v(c):
    k = (c["AGG_STEP"], c["TANK_REF_Q"], c["TRACK_NORMALIZE"], c["DEMAND_SLANT"], c["DIST_SIG"])
    if k not in _ADV:
        _ADV[k] = np.mean([V2.raw_demand(d, lap, c["AGG_STEP"], c["TANK_REF_Q"]) * wear_of(d, lap, c)
                           for (d, _), lap in tracks().items()], axis=0)
    return _ADV[k]


def capacity(shares, r, c):
    """(capacity (G,3), recovery per turn (G,3)). Same rule for all three resources; no race-length term."""
    a = avg_demand_v(c)
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


def kappa_scale(T, c):
    v = c.get(f"KAPPA_{T}")
    return c["KAPPA_SCALE"] if v is None else v


def run_new(shares, r, district, lap, T, style, q_read, q_time, n, seed, cfg=None,
            mode="read", pacing="ration", scouted=True, opp_shares=(1 / 3, 1 / 3, 1 / 3), ration=None):
    """v4 race batch. Same rules and outputs as resources_v3.run_new, plus:
      pacing  "greedy": best selectable stance by immediate value (sees its gauges, so the overrun penalty counts)
              "ration": v3 rationer (price per unit load when the RATION_H-turn headroom is short)
              "plan"  : planned pacing. For the read's counter and the tie stance (the guessed boss stance) it
                        forecasts the next PLAN_H turns of its own gauges (rest of this turn's planned counters,
                        then each upcoming corner's planned counters at belief q, the misread load, passive wear,
                        recovery, lock + hysteresis release) and prices the clash value it expects to lose to
                        locked counters (win->tie) and to overrun penalties. Picks argmax(immediate - PLAN_LAMBDA x
                        forecast loss). The forecast stops at the finish line, so it spends freely at the end.
      mode    "read"     : live read model (q_read) as v3.
              "random"   : uniformly random selectable stance (v3).
              "randguess": guesses each boss stance uniformly at random and plays its counter with the chosen
                           pacing (the 'no reads, same pacing' player). Outcomes come straight from the stances.
              "randline" : guesses one of the corner's 3 district lines uniformly at random (knows the line set,
                           no read). Diagnostic only.
      kappa   per race length via KAPPA_10/20/30 (multiplier on live KAPPA_BY_LENGTH).
    Extra outputs: dur_sum_race (G,n) and nlock_race (G,n) for per-race lock length."""
    if ration is not None:                       # v3 call compatibility
        pacing = "ration" if ration else "greedy"
    c = cfg_of(cfg); c2 = v2cfg(c)
    agg = c["AGG_STEP"]
    rng = np.random.default_rng(seed)
    shares = np.atleast_2d(np.asarray(shares, float)); G = shares.shape[0]
    V = r ** (V1.KAPPA[T] * kappa_scale(T, c))
    php = phi_vec(q_time); pho = phi_vec(E.OPPONENT_QTE)
    wear = wear_of(district, lap, c)
    qd = min(max(q_read, 0.0), 1.0)
    H = c["RATION_H"]; REL = c["RELEASE"]; LM = c["LIMP_MULT"]; PH = c["PLAN_H"]; PL = c["PLAN_LAMBDA"]
    need_c = np.array([corner_need(district, lap[t % len(lap)], c, qd) * wear for t in range(T + max(H, PH))])
    cap, rec = capacity(shares, r, c)
    cb = dict(c)
    for k_ in ("REC_FACTOR", "CAP_TURNS"):
        if c[f"BOSS_{k_}"] is not None:
            cb[k_] = c[f"BOSS_{k_}"]
    OREL = REL if c["BOSS_RELEASE"] is None else c["BOSS_RELEASE"]
    ocap, orec = capacity(np.array([opp_shares]), 1.0, cb)
    capb = cap[:, None, :]; ocp = ocap[0]; recb = rec[:, None, :]
    # ── per-turn plan tables (corner, lines, scouted boss weights, guessed line, planned counter costs)
    TT = T + PH
    corners = [lap[t % len(lap)] for t in range(TT)]
    LINES = [np.array([parse(x) for x in C.line_triples(district, k)]) for k in corners]
    W = [V2.style_weights(style, district, corners[t], t, T, c2) if t < T else STYLE_W for t in range(TT)]
    COST = [np.array(V1.CORNER_COST[k]) * V1.BASE_COST * wear for k in corners]
    PAS = [np.array(V1.CORNER_PASSIVE[k]) * wear for k in corners]
    GUESS = [LINES[t][int(np.argmax(W[t] if scouted else STYLE_W))] for t in range(TT)]
    RG = mode in ("randguess", "randline")
    belief = 1.0 if RG else qd
    # future-clash want distribution pi[t][j] (3,) and planned cost per stance cpl[t][j] (3,), misread load mis[t][j] (3,)
    PI, CPL, MIS = [], [], []
    for t in range(TT):
        pis, cps, mss = [], [], []
        if mode == "randguess":
            for j in range(3):
                pis.append(np.full(3, 1 / 3)); cps.append(COST[t].copy()); mss.append(np.zeros(3))
        elif mode == "randline":
            lines_ = LINES[t]
            ctr_lines = [[int(COUNTER[s]) for s in ln] for ln in lines_]
            costs_l = [V1.line_cost(cl, corners[t], agg) for cl in ctr_lines]
            for j in range(3):
                pi = np.zeros(3); cp = np.zeros(3)
                for cl, cs in zip(ctr_lines, costs_l):
                    pi[cl[j]] += 1 / 3; cp[cl[j]] += cs[j] * wear[cl[j]] / 3
                cp = np.where(pi > 0, cp / np.maximum(pi, 1e-12), 0)
                pis.append(pi); cps.append(cp); mss.append(np.zeros(3))
        else:
            cl = [int(COUNTER[s]) for s in GUESS[t]]
            cs = V1.line_cost(cl, corners[t], agg)
            readpart = np.zeros(3)
            for s, x in zip(cl, cs):
                readpart[s] += qd * x * wear[s]
            tris0 = [int(COUNTER[s]) for s in LINES[t][0]]
            read0 = np.zeros(3)
            for s, x in zip(tris0, V1.line_cost(tris0, corners[t], agg)):
                read0[s] += qd * x * wear[s]
            misload = np.maximum(0.0, need_c[t] - PAS[t] - read0) / 3
            for j in range(3):
                pi = np.zeros(3); cp = np.zeros(3); pi[cl[j]] = belief; cp[cl[j]] = cs[j] * wear[cl[j]]
                pis.append(pi); cps.append(cp); mss.append(misload)
        PI.append(pis); CPL.append(cps); MIS.append(mss)
    MF = 1 + c["STAT_M_W"] * (shares - 1 / 3)                  # (G,3) payoff multiplier by stance played
    d_lock = V * (php[2] - php[1]) + (pho[1] - pho[0])     # value lost when a correct counter is forced to a tie
    d_ov = V * php[2]                                       # value at stake in a winning clash (x (1-pen))

    def forecast(L, LK, rep_cur, t, i, plan_rest):
        """L, LK (K,G,n,3) after the candidate stance at clash i of turn t; plan_rest (n,3) planned stance per clash
        this turn. Returns expected forecast loss (K,G,n)."""
        L = L.copy(); LK = LK.copy(); rep = rep_cur.copy()
        loss = np.zeros(L.shape[:3])
        ct = COST[t]
        for j in range(i + 1, 3):
            s = plan_rest[:, j]                                       # (n,)
            sidx = np.broadcast_to(s[None, None, :, None], L.shape[:3] + (1,))
            Ls = np.take_along_axis(L, sidx, 3)[..., 0]
            lk = np.take_along_axis(LK, sidx, 3)[..., 0]
            cs = ct[s][None, None, :] * (1 + agg * np.take_along_axis(rep, sidx, 3)[..., 0])
            cps = np.take_along_axis(np.broadcast_to(capb[None], L.shape), sidx, 3)[..., 0]
            x = np.maximum(0.0, Ls + cs - cps) / cps
            loss += np.where(lk, d_lock, d_ov * (1 - penalty(x, c)))
            np.put_along_axis(L, sidx, (Ls + np.where(lk, 0.0, cs))[..., None], 3)
            fidx = np.broadcast_to(LOSER[s][None, None, :, None], L.shape[:3] + (1,))
            fl_ = np.take_along_axis(LK, fidx, 3)[..., 0]
            np.put_along_axis(L, fidx, (np.take_along_axis(L, fidx, 3)[..., 0] + np.where(lk & ~fl_, ct[LOSER[s]][None, None, :], 0.0))[..., None], 3)
            np.put_along_axis(rep, sidx, np.take_along_axis(rep, sidx, 3) + 1, 3)
            LK |= L >= capb[None] - 1e-9
        L += PAS[t]; LK |= L >= capb[None] - 1e-9
        L = np.maximum(0.0, L - recb[None]); LK &= ~(L < REL * capb[None] - 1e-9)
        for h in range(1, PH + 1):
            tt = t + h
            if tt >= T:
                break
            for j in range(3):
                pi = PI[tt][j]; cp = CPL[tt][j]
                add = np.zeros(L.shape)
                for s in range(3):
                    if pi[s] <= 0:
                        continue
                    x = np.maximum(0.0, L[..., s] + cp[s] - capb[None, :, :, s]) / capb[None, :, :, s]
                    lk = LK[..., s]
                    loss += pi[s] * np.where(lk, d_lock, d_ov * (1 - penalty(x, c)))
                    add[..., s] += pi[s] * np.where(lk, 0.0, cp[s])
                    f = int(LOSER[s])                                  # forced to the tie stance: its bar takes the load
                    add[..., f] += pi[s] * np.where(lk & ~LK[..., f], COST[tt][f], 0.0)
                L += add + MIS[tt][j]
                LK |= L >= capb[None] - 1e-9
            L += PAS[tt]; LK |= L >= capb[None] - 1e-9
            L = np.maximum(0.0, L - recb[None]); LK &= ~(L < REL * capb[None] - 1e-9)
        return loss

    load = np.zeros((G, n, 3)); oload = np.zeros((n, 3))
    lock = np.zeros((G, n, 3), bool); olock = np.zeros((n, 3), bool)
    lstart = np.zeros((G, n, 3), int)
    gp = np.zeros((G, n)); go = np.zeros((G, n))
    z = lambda: np.zeros((G, n))
    ov_clash, ov_turns, pen_loss, lock_turns, lock_clash, limp = z(), z(), z(), z(), z(), z()
    lock_streak, cur = z(), z()
    read_clash = np.zeros(n); read_lock, read_ov, read_ov_play, read_switch = z(), z(), z(), z()
    n_locks = np.zeros(G); dur_sum = np.zeros(G); hist = np.zeros((G, T + 1)); lock_res = np.zeros((G, 3))
    nl_race = z(); dur_race = z()
    lock_t = np.zeros((G, T)); ov_t = np.zeros((G, T)); boss_ov = np.zeros(n); boss_lock = np.zeros(n)
    ar = np.arange(n)

    def close_locks(mask, t_end):
        d = np.where(mask, t_end - lstart, 0)
        n_locks[:] += mask.sum((1, 2)); dur_sum[:] += d.sum((1, 2))
        nl_race[:] += mask.sum(2); dur_race[:] += d.sum(2)
        for g in range(G):
            hist[g] += np.bincount(d[g][mask[g]], minlength=T + 1)[:T + 1]

    def new_locks(t):
        nonlocal lock
        nl = (load >= capb - 1e-9) & ~lock
        lstart[nl] = t; lock |= nl
        lock_res[:] += nl.sum(1)

    for t in range(T):
        corner = corners[t]
        lines = LINES[t]
        w = W[t]
        li = np.searchsorted(np.cumsum(w), rng.random(n), side="right").clip(0, 2)
        oline = lines[li]
        cost_tab = COST[t]
        read = rng.random(n) < q_read
        mis_tie = rng.random((n, 3)) < q_read
        rnd = rng.random((n, 3, 3))
        if mode == "randline":                                       # random guess of one of the corner's 3 lines
            guess_n = lines[rng.integers(0, 3, n)]                   # (n,3)
            read = np.ones(n, bool)
        elif mode == "randguess":                                    # random guess of each boss stance
            guess_n = rng.integers(0, 3, (n, 3))
            read = np.ones(n, bool)
        else:
            guess_n = np.broadcast_to(GUESS[t][None, :], (n, 3))
        plan_turn = COUNTER[guess_n]                                 # (n,3) planned counters
        if pacing == "mix":
            pace_on = (rng.random(n) < c["PACE_Q"]).astype(float)
        needH = need_c[t:t + H].sum(0)
        rep = np.zeros((G, n, 3)); orep = np.zeros((n, 3))
        turn_ov = np.zeros((G, n), bool); turn_lock = np.zeros((G, n), bool)
        for i in range(3):
            # ── boss (v3 policy)
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
                gs = guess_n[:, i]                                     # (n,)
                o_vs = OUT[:, gs].T                                    # (n,3) outcome of each of my stances vs guess
                gain = V * php[o_vs + 1][None] * m_if * MF[:, None, :] - pho[-o_vs + 1][None]
                if pacing == "ration":
                    head = capb - load + rec[:, None, :] * (H - 1)
                    rho = head / np.maximum(needH[None, None, :], 1e-9)
                    gain = gain - c["RATION_LAMBDA"] * np.clip(1 - rho, 0, 1) * cc
                if pacing in ("reserve", "mix"):
                    T_eff = c["RES_T"]
                    if c["RES_LOOK"] > 0:
                        fut = np.zeros(3)
                        for tt in range(t + 1, min(T, t + 1 + PH)):
                            for j in range(3):
                                fut += PI[tt][j] * CPL[tt][j] + MIS[tt][j]
                            fut += PAS[tt]
                        nf = max(1, min(T, t + 1 + PH) - (t + 1))
                        short = np.maximum(0.0, fut[None, None, :] - rec[:, None, :] * nf) / capb
                        T_eff = c["RES_T"] - c["RES_LOOK"] * short
                    over = ((load + cc) / capb - T_eff) / np.maximum(1 - T_eff, 0.05)
                    pricey = c["RES_K"] * d_lock * np.maximum(0.0, over)
                    if pacing == "mix":
                        pricey = pricey * pace_on[None, :, None]
                    gain = gain - pricey
                elif pacing == "plan":
                    ctr = COUNTER[gs]                                  # (n,)
                    cand = np.stack([ctr, gs])                         # K=2: counter, tie (guessed boss stance)
                    Lk = np.broadcast_to(load[None], (2,) + load.shape).copy()
                    LKk = np.broadcast_to(lock[None], (2,) + lock.shape).copy()
                    repk = np.broadcast_to(rep[None], (2,) + rep.shape).copy()
                    for k in range(2):
                        idx = np.broadcast_to(cand[k][None, :, None], (G, n, 1))
                        add = np.take_along_axis(cc, idx, 2)
                        np.put_along_axis(Lk[k], idx, np.take_along_axis(Lk[k], idx, 2) + add, 2)
                        np.put_along_axis(repk[k], idx, np.take_along_axis(repk[k], idx, 2) + 1, 2)
                    LKk |= Lk >= capb[None] - 1e-9
                    fl = forecast(Lk, LKk, repk, t, i, plan_turn)      # (2,G,n)
                    pen_ = np.zeros((G, n, 3))
                    for k in range(2):
                        idx = np.broadcast_to(cand[k][None, :, None], (G, n, 1))
                        np.put_along_axis(pen_, idx, (PL * fl[k])[..., None], 2)
                    # loser stance: never preferred by the planner (dominated); keep it last-resort
                    other = np.ones((G, n, 3), bool)
                    for k in range(2):
                        np.put_along_axis(other, np.broadcast_to(cand[k][None, :, None], (G, n, 1)), False, 2)
                    pen_ = np.where(other, PL * fl.max(0)[..., None], pen_)
                    gain = gain - pen_
                choice_read = np.argmax(np.where(sel, gain, -1e9), axis=2)
                if RG:
                    choice = choice_read
                else:
                    mis = np.where(mis_tie[:, i], oline[:, i], LOSER[oline[:, i]])
                    mis_ok = np.take_along_axis(sel, np.broadcast_to(mis, (G, n))[..., None], 2)[..., 0]
                    alt_p = np.argmax(np.where(sel, rnd[None, :, i, :], -1.0), axis=2)
                    choice = np.where(read[None, :], choice_read, np.where(mis_ok, mis[None, :], alt_p))
                ctr = COUNTER[gs]
                ctr_lock = np.take_along_axis(lock, np.broadcast_to(ctr[None, :, None], (G, n, 1)), 2)[..., 0]
                ctr_x = np.take_along_axis(x_if, np.broadcast_to(ctr[None, :, None], (G, n, 1)), 2)[..., 0]
                ctr_ov = ~ctr_lock & (ctr_x > 0)
                read_clash += read
                read_lock += read[None, :] & ctr_lock
                read_ov += read[None, :] & ctr_ov
                read_ov_play += read[None, :] & ctr_ov & (choice == ctr[None, :])
                read_switch += read[None, :] & (choice != ctr[None, :])
            choice = np.where(none, np.argmin(load / capb, 2), choice)
            limp += none
            x = np.take_along_axis(x_if, choice[..., None], 2)[..., 0]
            pm = np.where(none, LM, np.take_along_axis(m_if, choice[..., None], 2)[..., 0])
            o = OUT[choice, os_[None, :]]
            gp += V * php[o + 1] * pm * np.take_along_axis(MF, choice, 1)
            go += pho[-o + 1] * om
            ovc = (x > 0) & ~none
            ov_clash += ovc; turn_ov |= ovc; pen_loss += 1 - pm
            cst = np.take_along_axis(cc, choice[..., None], 2)[..., 0]
            np.put_along_axis(load, choice[..., None], (np.take_along_axis(load, choice[..., None], 2)[..., 0] + cst)[..., None], 2)
            np.put_along_axis(rep, choice[..., None], np.take_along_axis(rep, choice[..., None], 2) + 1, 2)
            new_locks(t)
        load = load + PAS[t]; new_locks(t)
        load = np.maximum(0.0, load - rec[:, None, :])
        rel = lock & (load < REL * capb - 1e-9)
        close_locks(rel, t); lock &= ~rel
        oload = np.maximum(0.0, oload + PAS[t] - orec[0])
        olock &= ~(oload < OREL * ocp[None, :] - 1e-9)
        ov_turns += turn_ov; lock_turns += turn_lock
        cur = np.where(turn_lock, cur + 1, 0); lock_streak = np.maximum(lock_streak, cur)
        lock_t[:, t] = turn_lock.mean(1); ov_t[:, t] = turn_ov.mean(1)
    close_locks(lock, T - 1)
    win = (gp > go) + 0.5 * (gp == go)
    return dict(win=win, ov_clash=ov_clash, ov_turns=ov_turns, pen_loss=pen_loss, lock_turns=lock_turns, lock_clash=lock_clash,
                limp=limp, n_locks=n_locks, lock_dur_sum=dur_sum, lock_hist=hist, lock_streak=lock_streak,
                read_clash=np.broadcast_to(read_clash, (G, n)), read_lock=read_lock, read_ov=read_ov, read_ov_play=read_ov_play,
                read_switch=read_switch, lock_t=lock_t, ov_t=ov_t, lock_res=lock_res, boss_ov=boss_ov, boss_lock=boss_lock,
                nlock_race=nl_race, dur_sum_race=dur_race)
