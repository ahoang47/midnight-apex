"""Sweep a pre-finale story arc so post-R3 XP is not a 25-34 wild grind.

Draft only, no live sim/ edits. T4 regular = $8,000 representative.
Story opponents are unnamed placeholders (Desmond / Nathaniel).
"""
from __future__ import annotations
import json, math, os, sys, time, copy
from itertools import product

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_betting_levers as L
from model import (
    FINALE_C, FINALE_L, FINALE_B, FINALE_DIST, power_at_level,
    grind_xp, apply_xp, xp_to_next,
)
from evaluate import wr_cell, hard_win, PROFILES

T4 = 8000.0
XP = L.XP
CAPS = (46, 63, 76, 95, 114)
STEPS = (
    dict(name="pre_F1", enter=46, cap=63, dist="touge", billed_i=0),
    dict(name="F1_F2", enter=63, cap=76, dist="wangan", billed_i=1),
    dict(name="F2_F3", enter=76, cap=95, dist="street", billed_i=2),
    dict(name="F3_F4", enter=95, cap=114, dist="touge", billed_i=3),
)
GRIND_R = 1.12  # 10-turn wilds in the step district; keeps 60/60 in the 65%+ band
GRIND_PAY = L.FINALE_GRIND_PAY  # $742.50
BILLED_PAY = L.FINALE_PURSE     # $10,800
PURSE_10, PURSE_20, PURSE_30 = 2500.0, 3375.0, 5000.0

_WR = {}
def wr_pack(pr, r, T, district):
    key = (pr, round(float(r), 5), T, district)
    if key not in _WR:
        _WR[key] = wr_cell(pr, r, T, district, True)
    return _WR[key]

def wr_hard(pr, r, T, district):
    return hard_win(wr_pack(pr, r, T, district)) / 100.0

def wr_dist(pr, r, T, district):
    return wr_pack(pr, r, T, district)["district"]["win"] / 100.0

def xp_range(a, b):
    return sum(xp_to_next(L, XP) for L in range(a, b))

GAP_XP = [xp_range(CAPS[i], CAPS[i+1]) for i in range(4)]

def t4_legal(s, unlock_done):
    return unlock_done and s.L >= L.FLOOR_T4

def shop_arc(s, unlock_done):
    # reuse T3/T2 shop; T4 only after the unlock beat and L47
    was = s.post_R3
    s.post_R3 = bool(t4_legal(s, unlock_done))
    L.shop(s)
    s.post_R3 = was
    # if T4 not legal, shop() would also skip T4 because post_R3 is False

def credit_arc(s, amount, unlock_done):
    if s.debt > 0:
        take = min(s.debt, L.DEBT_SHARE * amount)
        s.debt -= take
        s.money += amount - take
    else:
        s.money += amount
    shop_arc(s, unlock_done)

def combat_vs(s, content_C):
    return L.combat(s, content_C)

def entry_states():
    out = {}
    for pr in PROFILES:
        s = L.walk_pre_R3(pr, L.MODE[pr], T4)
        # official R3, no betting (reuse levers walk with policy none)
        cfg = dict(unlock="R2", elig="any", cap=None, odds="fair", policy="none")
        s = L.clone(s)
        s.t4_price = T4
        L.walk_R3(s, pr, L.MODE[pr], cfg, None)
        # walk_R3 already ends wholesale and sets post_R3 True; T4 floor may be unmet (L43/L46)
        # Hold T4 closed until the arc's unlock beat.
        s.post_R3 = False
        out[pr] = s
        print(f"  entry {pr} L={s.L} ${s.money:.0f} T3={s.n_t3_reg}+a{s.n_aero3} "
              f"wholesale={s.wholesale} post_R3={s.post_R3}", flush=True)
    return out

def length_pattern(n, kind="ladder"):
    if n == 0:
        return []
    if n == 1:
        return [20]
    if n == 2:
        return [10, 20] if kind != "gate" else [20, 30]
    if n == 3:
        return [10, 20, 30]
    if n == 4:
        return [10, 20, 20, 30]
    if n == 5:
        return [10, 10, 20, 20, 30]
    if n == 6:
        return [10, 10, 20, 20, 20, 30]
    raise ValueError(n)

def xp_weights(n):
    if n == 0:
        return []
    # slightly back-loaded, like the campaign ladder
    raw = {
        1: [1.0],
        2: [0.40, 0.60],
        3: [0.25, 0.35, 0.40],
        4: [0.18, 0.24, 0.26, 0.32],
        5: [0.12, 0.16, 0.20, 0.24, 0.28],
        6: [0.10, 0.12, 0.16, 0.18, 0.20, 0.24],
    }[n]
    s = sum(raw)
    return [w / s for w in raw]

def purse_of(T):
    return {10: PURSE_10, 20: PURSE_20, 30: PURSE_30}[T]

def r_targets(n, billed_r, style):
    """Descending r toward a gate a bit easier than the billed fight."""
    if n == 0:
        return []
    if style == "easy":
        hi, lo = 1.20, max(billed_r + 0.04, 1.10)
    elif style == "mid":
        hi, lo = 1.18, max(billed_r + 0.02, 1.06)
    else:  # tight — last non-billed aims at a mixed-wall band
        hi, lo = 1.16, billed_r  # last story as tight as billed (often too tight)
    if n == 1:
        return [lo]
    out = []
    for i in range(n):
        t = i / (n - 1)
        out.append(round(hi + (lo - hi) * t, 3))
    return out

def build_arc(n_pre, n_mid, fill, r_style, t4_unlock_idx, mid_kind="ladder"):
    races = []
    # pre F1
    lens = length_pattern(n_pre, "ladder")
    w = xp_weights(n_pre)
    rt = r_targets(n_pre, 1.066, r_style)
    for i, (T, wi, r) in enumerate(zip(lens, w, rt)):
        races.append(dict(
            id=f"P{i+1}",
            place="pre_F1",
            step=0,
            dist="touge",
            T=T,
            r_design=r,
            xp_share=wi,
            fill=fill,
            purse=purse_of(T),
            billed=False,
            unlock_t4=(i == t4_unlock_idx),
            placeholder=f"[placeholder — Desmond/Nathaniel] pre-finale {i+1}/{n_pre}",
        ))
    # billed F1 + inter-step + billed later
    mid_dists = ("wangan", "street", "touge")
    billed_r = (1.066, 1.040, 1.053, 1.066)
    for si, step in enumerate(STEPS):
        # billed at end of this step
        races.append(dict(
            id=f"F{si+1}",
            place=f"F{si+1}",
            step=si,
            dist=step["dist"],
            T=30,
            r_design=billed_r[si],
            xp_share=0.0,
            fill=fill,
            purse=BILLED_PAY,
            billed=True,
            unlock_t4=False,
            B=FINALE_B[si],
            placeholder=f"[placeholder — Desmond/Nathaniel] finale billed {si+1}",
        ))
        if si < 3:
            lens_m = length_pattern(n_mid, mid_kind)
            wm = xp_weights(n_mid)
            rtm = r_targets(n_mid, billed_r[si+1], r_style)
            for j, (T, wi, r) in enumerate(zip(lens_m, wm, rtm)):
                races.append(dict(
                    id=f"M{si+1}{j+1}",
                    place=f"F{si+1}_F{si+2}",
                    step=si + 1,
                    dist=mid_dists[si],
                    T=T,
                    r_design=r,
                    xp_share=wi,
                    fill=fill,
                    purse=purse_of(T),
                    billed=False,
                    unlock_t4=False,
                    placeholder=f"[placeholder — Desmond/Nathaniel] between F{si+1} and F{si+2}, {j+1}/{n_mid or 0}",
                ))
    return races

def set_budgets_from_8080(races, entry_8080):
    """First pass: walk 80/80 story-only with B set from arrival combat / r_design."""
    s = L.clone(entry_8080)
    unlock = False
    shop_arc(s, unlock)
    for rc in races:
        if rc["unlock_t4"]:
            # budget uses pre-unlock combat; unlock happens on WIN
            pass
        if rc.get("B") is None or rc["id"].startswith("P") or rc["id"].startswith("M"):
            c = combat_vs(s, FINALE_C[rc["step"]])
            rc["B"] = round(c / rc["r_design"], 2)
            rc["ref_L"] = s.L
            rc["ref_combat"] = round(c, 2)
        # apply official win XP/purse so next arrival is right
        if rc["unlock_t4"]:
            unlock = True
        credit_arc(s, rc["purse"], unlock)
        if not rc["billed"]:
            amt = rc["fill"] * rc["xp_share"] * GAP_XP[rc["step"]]
            cap = CAPS[rc["step"] + 1]
            s.L, s.bag = apply_xp(s.L, amt, s.bag, XP, cap)
            shop_arc(s, unlock)
    return races

def grind_to(s, pr, cap_L, dist, content_C, unlock, stop=None):
    """Grind 10-turn wilds. stop() -> True to halt. Returns grind wins."""
    n = 0
    guard = 0
    while s.L < cap_L and guard < 80:
        if stop is not None and stop(s):
            break
        c = combat_vs(s, content_C)
        B = c / GRIND_R if c > 0 else content_C / GRIND_R
        r = c / B
        # official win for grind counts (XP path)
        credit_arc(s, GRIND_PAY, unlock)
        g = grind_xp(s.L, cap_L, XP)
        s.L, s.bag = apply_xp(s.L, g, s.bag, XP, cap_L)
        shop_arc(s, unlock)
        n += 1
        guard += 1
        s.grind_wins = getattr(s, "grind_wins", 0) + 1
    return n

def walk_profile(pr, entry, races, grind_mode):
    s = L.clone(entry)
    s.t4_price = T4
    s.grind_wins = 0
    unlock = False
    shop_arc(s, unlock)
    log = []
    # per-step grind tallies
    step_g = {i: dict(wall=0, to_cap=0) for i in range(4)}
    current_step_wall_done = {i: False for i in range(4)}

    for rc in races:
        si = rc["step"]
        cap_L = CAPS[si + 1]
        content_C = FINALE_C[si]
        dist = rc["dist"]
        # wall grind before a non-billed story race if this profile is stuck
        wall_n = 0
        if grind_mode in ("mixed", "hard") and not rc["billed"] and s.L < cap_L:
            def stuck(st, race=rc):
                c = combat_vs(st, content_C)
                r = c / race["B"]
                hard = wr_hard(pr, r, race["T"], race["dist"])
                return hard < 0.50
            if stuck(s):
                wall_n = grind_to(
                    s, pr, cap_L, dist, content_C, unlock,
                    stop=lambda st: not stuck(st),
                )
                step_g[si]["wall"] += wall_n
                current_step_wall_done[si] = True
        # to-cap grind before billed fight
        to_cap_n = 0
        if rc["billed"] and grind_mode in ("mixed", "hard") and s.L < cap_L:
            to_cap_n = grind_to(s, pr, cap_L, dist, content_C, unlock, stop=None)
            step_g[si]["to_cap"] += to_cap_n
        c = combat_vs(s, content_C)
        r = c / rc["B"]
        pack = wr_pack(pr, r, rc["T"], rc["dist"])
        hard = hard_win(pack)
        distw = pack["district"]["win"]
        rec = dict(
            id=rc["id"], place=rc["place"], dist=rc["dist"], T=rc["T"],
            billed=rc["billed"], L=s.L, money=round(s.money, 1),
            combat=round(c, 2), B=rc["B"], r=round(r, 4),
            wr_dist=round(distw, 1), wr_hard=round(hard, 1),
            t4=s.n_t4_reg, aero4=s.n_aero4, unlock=unlock,
            wall_grinds=wall_n, to_cap_grinds=to_cap_n,
        )
        # win and rewards
        if rc["unlock_t4"]:
            unlock = True
        credit_arc(s, rc["purse"], unlock)
        if not rc["billed"]:
            amt = rc["fill"] * rc["xp_share"] * GAP_XP[rc["step"]]
            s.L, s.bag = apply_xp(s.L, amt, s.bag, XP, cap_L)
            shop_arc(s, unlock)
        rec["L_after"] = s.L
        rec["money_after"] = round(s.money, 1)
        rec["t4_after"] = s.n_t4_reg
        rec["aero4_after"] = s.n_aero4
        log.append(rec)
    return dict(
        pr=pr, mode=grind_mode, end_L=s.L, end_money=round(s.money, 1),
        t4=s.n_t4_reg, aero4=s.n_aero4, t4_done=s.n_t4_reg >= 5 and s.n_aero4 >= 1,
        log=log,
        grind={i: dict(wall=step_g[i]["wall"], to_cap=step_g[i]["to_cap"],
                       total=step_g[i]["wall"] + step_g[i]["to_cap"])
               for i in range(4)},
    )

def evaluate(walks):
    """Score criteria-facing checks."""
    w = {row["pr"]: row for row in walks}
    issues = []
    # 80/80 story-only: every story + billed hard WR >= 50
    bad_8080 = [x["id"] for x in w["c8080"]["log"] if x["wr_hard"] < 50.0]
    if bad_8080:
        issues.append(f"80/80 <50% hard on {bad_8080}")
    # mixed grind totals per step in <=10, wall 3-6 if a wall happened
    grind_ok = True
    walls = {}
    for pr in ("c6080", "c8060"):
        for i in range(4):
            g = w[pr]["grind"][i]
            if g["total"] > 10:
                issues.append(f"{pr} step{i+1} grind {g['total']} >10")
                grind_ok = False
            walls.setdefault(i, []).append(g)
    # 60/60 finishes billed: wr_hard > 0 and at cap preferably >=30
    for x in w["c6060"]["log"]:
        if x["billed"] and x["wr_hard"] < 30.0:
            issues.append(f"60/60 billed {x['id']} hard {x['wr_hard']}% <30 at L{x['L']}")
        if x["wr_hard"] <= 0.05 and not x["billed"]:
            issues.append(f"60/60 unwinnable mid-arc {x['id']}")
    # 80/80 T4 incremental by F2 (need 2 regulars) and F4 package eventually
    def t4_before(pr, billed_id):
        for x in w[pr]["log"]:
            if x["id"] == billed_id:
                return x["t4"], x["aero4"], x["L"]
        return 0, 0, None
    t4f2, a4f2, _ = t4_before("c8080", "F2")
    t4f3, _, _ = t4_before("c8080", "F3")
    t4f4, a4f4, _ = t4_before("c8080", "F4")
    if t4f2 < 2:
        issues.append(f"80/80 only {t4f2} T4 regulars at F2 (need 2)")
    if t4f3 < 3 and t4f2 < 3:
        # 2 may already fill F3 in this combat model; flag only if F3 WR suffered
        f3 = next(x for x in w["c8080"]["log"] if x["id"] == "F3")
        if f3["wr_hard"] < 50:
            issues.append(f"80/80 F3 hard {f3['wr_hard']}% with t4={t4f3}")
    if t4f4 < 5 or a4f4 < 1:
        f4 = next(x for x in w["c8080"]["log"] if x["id"] == "F4")
        if f4["wr_hard"] < 50:
            issues.append(f"80/80 F4 hard {f4['wr_hard']}% with t4={t4f4}+a{a4f4}")
    # mixed wall quality: prefer 3-6 on at least one race in a step, for at least one mixed
    wall_notes = []
    for i in range(4):
        for pr in ("c6080", "c8060"):
            ww = w[pr]["grind"][i]["wall"]
            if 3 <= ww <= 6:
                wall_notes.append(f"{pr} S{i+1} wall {ww}")
            elif ww > 6:
                issues.append(f"{pr} step{i+1} wall {ww} >6")
    billed_ok = all(
        next(x for x in w[pr]["log"] if x["id"] == f"F{i+1}")["wr_hard"] >= (30.0 if pr == "c6060" else 50.0)
        for pr in PROFILES for i in range(4)
        if not (pr == "c6060")
    )
    # simpler billed 80/80 already in bad_8080; mixed at cap should be in band
    return dict(issues=issues, wall_notes=wall_notes, pass_=len(issues) == 0)

def compact_row(cfg, ev, walks):
    w = {row["pr"]: row for row in walks}
    grind = {}
    for pr in PROFILES:
        grind[pr] = [w[pr]["grind"][i]["total"] for i in range(4)]
        grind[pr + "_wall"] = [w[pr]["grind"][i]["wall"] for i in range(4)]
    wr8080 = [x["wr_hard"] for x in w["c8080"]["log"]]
    ids = [x["id"] for x in w["c8080"]["log"]]
    return dict(
        n_pre=cfg["n_pre"], n_mid=cfg["n_mid"], fill=cfg["fill"],
        r_style=cfg["r_style"], mid_kind=cfg["mid_kind"],
        t4_unlock=cfg["t4_unlock_idx"],
        pass_=ev["pass_"], issues=ev["issues"], walls=ev["wall_notes"],
        grind=grind,
        min_8080=min(wr8080),
        wr_8080=dict(zip(ids, wr8080)),
        money_8080=w["c8080"]["end_money"],
        money_6060=w["c6060"]["end_money"],
        t4_8080=(w["c8080"]["t4"], w["c8080"]["aero4"]),
    )

def main():
    t0 = time.time()
    print("entries after official R3...", flush=True)
    entries = entry_states()
    grid = []
    for n_pre, n_mid, fill, r_style, t4_idx, mid_kind in product(
        (3, 4, 5, 6),
        (0, 1, 2),
        (0.80, 0.85),
        ("easy", "mid", "tight"),
        (0, 1),
        ("ladder", "gate"),
    ):
        if n_mid == 0 and mid_kind != "ladder":
            continue  # skip duplicate empty mid
        if t4_idx >= n_pre:
            continue
        races = build_arc(n_pre, n_mid, fill, r_style, t4_idx, mid_kind)
        set_budgets_from_8080(races, entries["c8080"])
        walks = []
        for pr in PROFILES:
            mode = L.MODE[pr]  # story / mixed / hard
            # 80/80 is story-only: no grind
            walks.append(walk_profile(pr, entries[pr], races, mode))
        ev = evaluate(walks)
        row = compact_row(
            dict(n_pre=n_pre, n_mid=n_mid, fill=fill, r_style=r_style,
                 t4_unlock_idx=t4_idx, mid_kind=mid_kind),
            ev, walks,
        )
        grid.append(dict(cfg=row, races=[{k: rc[k] for k in rc if k != "placeholder"} | {"placeholder": rc["placeholder"]} for rc in races],
                         walks={w["pr"]: {k: w[k] for k in w} for w in walks}, ev=ev))
        flag = "PASS" if ev["pass_"] else "fail"
        gmix = row["grind"]["c6080"], row["grind"]["c8060"]
        print(f"{flag} pre={n_pre} mid={n_mid}/{mid_kind} fill={fill} r={r_style} t4@{t4_idx} "
              f"min8080={row['min_8080']} grind6080={gmix[0]} grind8060={gmix[1]} "
              f"walls={ev['wall_notes'][:3]} issues={ev['issues'][:2]}", flush=True)

    passes = [g for g in grid if g["ev"]["pass_"]]
    print(f"\n{len(passes)} / {len(grid)} passed, {time.time()-t0:.1f}s", flush=True)

    out = dict(
        t4_reg=T4, grind_r=GRIND_R, fill_gaps=GAP_XP,
        entries={pr: L.snapshot_entry(entries[pr]) for pr in PROFILES},
        n_cfgs=len(grid), n_pass=len(passes),
        summary=[g["cfg"] for g in grid],
        elapsed_s=round(time.time() - t0, 1),
    )
    # keep full walks only for passes to cap file size; plus a preferred shortlist
    out["passes"] = [dict(cfg=g["cfg"], ev=g["ev"], races=g["races"],
                          walks={pr: dict(end_L=g["walks"][pr]["end_L"],
                                          end_money=g["walks"][pr]["end_money"],
                                          t4=g["walks"][pr]["t4"],
                                          aero4=g["walks"][pr]["aero4"],
                                          t4_done=g["walks"][pr]["t4_done"],
                                          grind=g["walks"][pr]["grind"],
                                          log=g["walks"][pr]["log"])
                                 for pr in PROFILES})
                     for g in passes]
    path = os.path.join(HERE, "finale_arc_sweep.json")
    with open(path, "w") as f:
        json.dump(out, f)
    print("wrote", path, "bytes", os.path.getsize(path), flush=True)

if __name__ == "__main__":
    main()
