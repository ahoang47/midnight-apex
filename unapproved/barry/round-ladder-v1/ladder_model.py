"""3-crew ceiling×k ladder (study only). Does not edit progression.py or live constants."""
from __future__ import annotations
import os, sys, json
sys.path.insert(0, os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")), "sim"))
from velocity_shift import equations as E
from velocity_shift import progression as P

SP, XC, X = P.curves()


def build_rounds(k_step: float, player_cap_frac: float):
    Lp = 0
    C_prev = None
    rounds = []
    for rnd, dist in ((1, "Street"), (2, "Wangan"), (3, "Touge")):
        BcA = (E.SABINE_BUDGET * E.OPTION_A_CREW_STEP) if rnd == 1 else (C_prev * k_step)
        Lc = P.nearest_level(SP, E.SP_CAP_FRACTION * BcA)
        Bc = SP[Lc] / E.SP_CAP_FRACTION
        C = player_cap_frac * Bc
        nlev = Lc - Lp
        a = P.alloc_levels(nlev, E.CAP_ALLOC_CREW)
        rounds.append(dict(
            rnd=rnd, district=dist, BcA=BcA, Bc=Bc, C=C, Lc=Lc, Lp=Lp, nlev=nlev, alloc=a,
            B_over_prev=(None if not rounds else Bc / rounds[-1]["Bc"]),
            C_over_prev=(None if not rounds else C / rounds[-1]["C"]),
            B_over_prev_C=(None if C_prev is None else Bc / C_prev),
        ))
        C_prev = C
        Lp = Lc
    return rounds


def _rungs(rounds, player_cap_frac):
    R = []
    for k in (2, 3):
        R.append(dict(k=k, kind="scripted", L=0, ro=False, j=-1, district="", rung=f"scripted {k}",
                      rnd=0, B=E.SCRIPTED_BUDGETS[k], ref=0.0))
    for rd in rounds:
        L = rd["Lp"]
        for j in range(7):
            L += rd["alloc"][j]
            ref = SP[L] / E.SP_CAP_FRACTION
            if j == 6:
                B = rd["Bc"]; kind = "boss"
            else:
                B = player_cap_frac * ref / E.LADDER_R[j]; kind = "lt"
            R.append(dict(k=10, kind=kind, L=L, ro=(rd["rnd"] > 1), j=j, district=rd["district"],
                          rung=E.LADDER_RUNGS[j], rnd=rd["rnd"], B=B, ref=ref, Bc=rd["Bc"], C=rd["C"]))
    return R


def n_grind(v, cap, j):
    n = 0
    while XC[cap] - v > 1e-9 and n <= 200:
        Ln = P._level(XC, v, cap) + 1
        v = min(v + E.grind_payout_fraction(Ln, j) * X[Ln], XC[cap]); n += 1
    return n, v


def walk(rounds, player_cap_frac, policy="never"):
    """policy: never | walls (grind at mature #2 and boss) | always (grind every rung).

    XP/economy is the STALE v8c curve. Combat r uses live fill (player_cap_frac * ref),
    not the 0.25 share that only reaches 1.05.
    """
    R = _rungs(rounds, player_cap_frac)
    xp = 0.0
    rows = []
    for i, x in enumerate(R):
        cap = x["L"]
        if xp > XC[cap] + 1e-9:
            xp = XC[cap]
        L = P._level(XC, xp, cap)
        g = 0
        if x["kind"] != "scripted":
            def p_at(Lv):
                return player_cap_frac * (SP[Lv] / E.SP_CAP_FRACTION)
            r_skip = p_at(L) / x["B"]
            r_tgt = p_at(cap) / x["B"]
            n, v2 = n_grind(xp, cap, max(0, x["j"]))
            arrive_L = L
            grind_here = (
                (policy == "always")
                or (policy == "walls" and x["j"] in (3, 6))
            )
            if grind_here and n:
                g = n
                xp = v2
                L = cap
            rows.append(dict(
                rnd=x["rnd"], district=x["district"], rung=x["rung"], j=x["j"], kind=x["kind"],
                B=round(x["B"], 2), level_cap=cap, story_level_arrive=arrive_L,
                races_to_cap_on_arrival=n, grind_races=g,
                r_tgt=round(r_tgt, 4), r_skip_arrive=round(r_skip, 4),
                r_after=round((p_at(cap) if g else p_at(P._level(XC, xp, cap))) / x["B"], 4),
                opp_over_player_at_cap=round(x["B"] / p_at(cap), 4),
                in_band_at_cap=0.8 - 1e-9 <= (x["B"] / p_at(cap)) <= 1.2 + 1e-9,
                player_at_cap=round(p_at(cap), 2),
                ro=x["ro"],
                r_tgt_stale_share=round((SP[cap] + E.MOD_SHARE_OF_REF * x["ref"]) / x["B"], 4),
            ))
            if g:
                L = cap
        nxt = R[i + 1]["L"] if i + 1 < len(R) else cap
        unl = XC[nxt] - XC[cap]
        if x["k"] == 2:
            add = 0.0
        elif x["kind"] == "boss" or x["k"] == 3:
            add = E.STORY_XP_BOSS * unl
        else:
            lam = E.STORY_XP_LT_ROUND_OPEN if x.get("ro") else E.STORY_XP_LT
            add = max(lam * unl, E.STORY_XP_LT_FLOOR * X[max(1, nxt)])
        xp = min(xp + add, XC[nxt])
    return rows


def pack(k_step, player_cap_frac, label):
    rounds = build_rounds(k_step, player_cap_frac)
    out = dict(
        label=label, k_step=k_step, player_cap_frac=player_cap_frac,
        stale_xp=True, cap_alloc="CAP_ALLOC_CREW (not ROUND_OPEN; 1.07/1.10 jumps are not the old 1.30 opener)",
        r1_anchor="SABINE_BUDGET * OPTION_A_CREW_STEP = 330, same as today's first campaign crew",
        boss_target_r=player_cap_frac,
        lieutenant_target_r=list(E.LADDER_R[:6]),
        rounds=[{k: (v if not hasattr(v, "__iter__") or isinstance(v, (str, list, int, float, type(None))) else list(v))
                 for k, v in rd.items()} for rd in rounds],
        walks={p: walk(rounds, player_cap_frac, p) for p in ("never", "walls", "always")},
    )
    # summarize grind
    summ = {}
    for p, rows in out["walks"].items():
        by = {}
        for r in rows:
            by.setdefault(r["rnd"], []).append(r)
        summ[p] = {
            str(rnd): dict(
                grind=sum(x["grind_races"] for x in rs),
                end_cap=rs[-1]["level_cap"],
                story_at_boss_arrival=next(x["story_level_arrive"] for x in rs if x["j"] == 6 and x.get("grind_races", 0) >= 0),
                boss_grind=next(x["grind_races"] for x in rs if x["j"] == 6),
                mature2_grind=next(x["grind_races"] for x in rs if x["j"] == 3),
            ) for rnd, rs in by.items()
        }
        # fix story at boss arrival: for walls/always, arrive maybe below then grind
        for rnd, rs in by.items():
            boss = next(x for x in rs if x["j"] == 6)
            # re-read: we stored story_level_arrive after grind if grind happened. Need arrival before grind.
            # I set story_level_arrive=L if g else L, and L was overwritten only after append... 
            # actually if g, I appended with L if g else L where L was still arrival level. Good.
            summ[p][str(rnd)]["story_at_boss_arrival"] = boss["story_level_arrive"]
            summ[p][str(rnd)]["r_skip_boss"] = boss["r_skip_arrive"]
            summ[p][str(rnd)]["r_tgt_boss"] = boss["r_tgt"]
    out["grind_summary"] = summ
    return out


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    packs = [
        pack(1.07, 1.07, "primary: step 1.07, player cap 1.07 (live MOD_CAP_FRACTION)"),
        pack(1.10, 1.07, "variant: step 1.10, player cap stays live 1.07 (at-cap boss r still 1.07)"),
        pack(1.10, 1.10, "variant: step 1.10 and player cap 1.10 (at-cap boss r = 1.10)"),
    ]
    json.dump(packs, open(os.path.join(HERE, "ladder.json"), "w"), indent=1)
    for p in packs:
        print("====", p["label"], "====")
        for rd in p["rounds"]:
            print(f"  R{rd['rnd']} {rd['district']}: intended B={rd['BcA']:.2f} snapped B={rd['Bc']:.2f} C={rd['C']:.2f} L {rd['Lp']}→{rd['Lc']} (+{rd['nlev']}) alloc={rd['alloc']}")
        print("  grind", p["grind_summary"])
