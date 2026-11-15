"""Mod unlock timing and purchase counts per scheme (draft, Barry 2026-11-14).
Unlock schedule = live sim: tier level floors (MOD_TIER_LEVEL_FLOOR T1 0 / T2 13 / T3 30 / T4 47 + the P1 win),
aero after the R1 boss (AERO_UNLOCK_AFTER), wholesale R1 end -> R3 end. Bought mods keep their stat (Austin
2026-11-14); the player rebalances by buying new mods of the needed stat and swapping them in.
Also: the races played before a new tier's floor (R2 kid1 at L12, R3 kid1 at L29) carry the previous round's set;
option (a) keep it, option (b) buy extra old-tier mods to rebalance for those races."""
import os, sys, json, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
import mod_schemes as S
import mods_eval as M
P, E = M.P, M.E
STAT = ("POW", "HAN", "EN")

def counts(lab):
    base = lab.split("+")[0]; return {k: base.count(k[0]) for k in STAT}

def pre_floor(scheme):
    """Car split for the R2 / R3 races before the new tier's floor: previous set + SP retuned at entry."""
    rows = S.walk(scheme); out = {}
    for i, nxt in ((0, 1), (1, 2)):
        prev, row = rows[i], rows[nxt]
        L = row["cap"] if False else S.SEGS[nxt][2]                    # entry level (prev cap)
        al = S.retune(row["sp_prev"], row["q"])                        # the retune done at the district change
        al = S.add_points(al, E.skill_points(L) - E.skill_points(prev["cap"]), row["q"])
        sp = sum(al); gap = min(S.SEGS[nxt][4], 1.3375 * sp) - sp; m = sum(prev["mod_pts"]); k = min(1.0, gap / m)
        keep = [a + k * b for a, b in zip(al, prev["mod_pts"])]; t = sum(keep)
        # option (b): best set of the OLD tier (any stats) for the new district
        best = None
        for lab, mv in S.mod_vectors(S.SCHEMES[scheme], prev["tier"]):
            c = [a + min(1.0, gap / sum(mv)) * b for a, b in zip(al, mv)]; sh = [x / sum(c) for x in c]
            if min(sh) < 0.25 - 1e-9 or max(sh) > 0.5 + 1e-9: continue
            dd = S.dist(sh, row["district"])
            if best is None or dd < best[0]: best = (dd, lab, sh)
        out[row["seg"]] = dict(level=L, kept_set=prev["mods"], keep_split=tuple(round(x / t, 4) for x in keep),
                               rebalanced_set=best[1], rebalanced_split=tuple(round(x, 4) for x in best[2]),
                               extra_old_tier={k: max(0, counts(best[1])[k] - counts(prev["mods"])[k]) for k in STAT})
    return rows, out

def purchases(scheme, rows, pre):
    """Mods bought per tier (regular), with bought mods keeping their stat: per stat, the most any equipped set needs."""
    by = {}
    for r in rows:
        c = counts(r["mods"]); t = by.setdefault(r["tier"], {k: 0 for k in STAT})
        for k in STAT: t[k] = max(t[k], c[k])
    out = {t: dict(v, total=sum(v.values())) for t, v in by.items()}
    extra_b = {}
    for seg, x in pre.items():
        tier = "T1" if seg == "R2" else "T2"; extra_b[tier] = sum(x["extra_old_tier"].values())
    return out, extra_b

def eval_prefloor(scheme, rows, pre, option):
    """Campaign + at-cap with the pre-floor races at their real split (option 'a' keep or 'b' rebalanced)."""
    seg = {x["seg"]: tuple(round(v, 3) for v in x["car_split"]) for x in rows}
    pres = {k: tuple(round(v, 3) for v in (x["keep_split"] if option == "a" else x["rebalanced_split"])) for k, x in pre.items()}
    cur = {"rnd": 0, "L": 0}
    ow, ot, oc = P._walk_round, P.track_win, P.combat_power
    def wh(rnd, *a, **k): cur["rnd"] = rnd; return ow(rnd, *a, **k)
    def ch(level, rnd, mods=True): cur["L"] = int(level); return oc(level, rnd, mods)
    def th(pr, r, T, name, pow_share=None):
        rnd = cur["rnd"]; name_seg = ("R1", "R2", "R3")[rnd]
        floor = {1: 13, 2: 30}.get(rnd)
        sp = pres[name_seg] if floor is not None and cur["L"] < floor else seg[name_seg]
        return M.win(pr, r, T, name, sp)
    P._walk_round, P.track_win, P.combat_power = wh, th, ch
    try:
        res = M.camp.run_all(M.camp.uniform((1, 1, 1))); s = M.camp.summary(res)
    finally:
        P._walk_round, P.track_win, P.combat_power = ow, ot, oc
    kid1 = {m: [res[m][i]["rows"][0]["wr"] for i in (1, 2)] for m in res}
    return dict(story_boss=[x["boss"]["c8080"] for x in s["story"]], story_min=[x["min8080"] for x in s["story"]],
                mixed=[(x["wall"], x["wall_grind"], x["post"]) for x in s["mixed"]], hard=[x["total"] for x in s["hard"]],
                kid1_R2_R3={m: [{pr: v[pr]["district"] for pr in P.PROFILES} for v in kid1[m]] for m in kid1})

if __name__ == "__main__":
    out = {}
    with contextlib.redirect_stdout(io.StringIO()):
        import verify_live as V
    out["arc_t4_timing"] = {w["pr"]: [(x["id"], x["L"], x["L_after"], x["t4_after"], x["aero4_after"]) for x in w["log"]] for w in V.walks}
    out["campaign_levels"] = {m: [[(x["rung"], x["arrive_L"]) for x in w["rows"]] for w in P.run(m)] for m in ("story", "mixed", "hard")}
    for k in S.SCHEMES:
        rows, pre = pre_floor(k); buy, extra = purchases(k, rows, pre)
        o = dict(sets={r["seg"]: r["mods"] for r in rows}, buy=buy, extra_old_tier_option_b=extra, pre_floor=pre)
        if k in ("C_4free", "D_8free"):
            try:
                o["eval_a"] = eval_prefloor(k, rows, pre, "a"); o["eval_b"] = eval_prefloor(k, rows, pre, "b")
            except KeyError as ex:
                o["eval_err"] = str(ex)
        out[k] = o
        print("==", k, "sets", o["sets"]); print("   buy", buy, "extra(b)", extra)
        for sg, x in pre.items(): print("   pre-floor", sg, "L", x["level"], x["kept_set"], x["keep_split"], "| rebalanced", x["rebalanced_set"], x["rebalanced_split"], x["extra_old_tier"])
        for opt in ("a", "b"):
            if f"eval_{opt}" in o:
                e = o[f"eval_{opt}"]; print(f"   option {opt}: story bosses", e["story_boss"], "min", e["story_min"], "mixed", e["mixed"], "hard", e["hard"])
                print("      kid1 R2/R3 mixed", e["kid1_R2_R3"]["mixed"])
        if "eval_err" in o: print("   eval skipped (no sweep):", o["eval_err"])
    json.dump(out, open(os.path.join(HERE, "unlocks.json"), "w"), indent=1, default=str)
