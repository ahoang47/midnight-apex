"""Evaluate the mod schemes (draft, Barry 2026-11-14). Live total power (mods fill to min(ceiling, 1.07 x P), every
scheme fills it, see mod_schemes.check_fill), so only the car split moves. Per segment (R1-R3, arc steps F1-F4) the car
split at the segment cap (mod_schemes.walk) is applied to every race of that segment:
  win = live table + [win(split) - win_rt1(tune)]      (splits.json for HAN != 25 %, rt1 sweep for HAN = 25 %).
Campaign: live sim/ progression walk. Arc / finale: draft econ-v1 arc walker (as skill-points-v1 verify_live.py)."""
import os, sys, json, bisect
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skill-points-v1"))
import mod_schemes as S
import retune as R                       # draft arc walker machinery (oracle / run_finale_arc hooks)
P, E, camp, arc, A, oracle, core = R.P, R.E, R.camp, R.arc, R.A, R.oracle, R.core
SPL = json.load(open(os.path.join(HERE, "splits.json")))
RS = [0.97, 1.00, 1.02, 1.04, 1.06, 1.08, 1.12, 1.18]
TRACK_D = {n: d for d, n in P._table()["tracks"]}
ORIG_TW = P._track_win

def _lin(cell, r):
    xs = RS; ys = [cell[f"{x:.3f}"] for x in xs]
    if r <= xs[0]: return ys[0]
    if r >= xs[-1]: return ys[-1]
    i = bisect.bisect_right(xs, r); f = (r - xs[i - 1]) / (xs[i] - xs[i - 1]); return ys[i - 1] * (1 - f) + ys[i] * f

def delta(pr, r, T, track, split):
    d = TRACK_D[track]; p0 = E.DISTRICT_TUNE[d][0]
    base = P._off_win(pr, r, T, track, p0)
    if abs(split[1] - 0.25) < 1e-3:
        return P._off_win(pr, r, T, track, split[0]) - base
    key = f"{d}:{split[0]:.3f}/{split[1]:.3f}/{split[2]:.3f}"
    cell = SPL[key][pr][str(int(T))][track]
    return _lin(cell, r) - base

def win(pr, r, T, track, split):
    return min(100.0, max(0.0, ORIG_TW(pr, r, T, track) + delta(pr, r, T, track, split)))

def run(rows):
    """rows: schemes.walk() output (7 segments) or None for the live baseline (SP split)."""
    seg = {x["seg"]: tuple(round(v, 3) for v in x["car_split"]) for x in rows} if rows else None
    cur = {"rnd": 0}
    orig_walk, orig_track = P._walk_round, P.track_win
    def walk_hook(rnd, *a, **k):
        cur["rnd"] = rnd; return orig_walk(rnd, *a, **k)
    def track_hook(pr, r, T, name, pow_share=None):
        return win(pr, r, T, name, seg[("R1", "R2", "R3")[cur["rnd"]]])
    if seg:
        P._walk_round = walk_hook; P.track_win = track_hook
    try:
        res = camp.run_all(camp.uniform((1, 1, 1))); s = camp.summary(res)
        caps = []
        for rnd, d in enumerate(E.ROUND_DISTRICTS):
            capL = E.CAP_LEVEL[rnd]; r = P.combat_power(capL, rnd) / E.opponent_budget(rnd, 6); trk = E.BOSS_HARD_TRACK[d.lower()]
            if seg:
                caps.append({pr: round(win(pr, r, 30, trk, seg[("R1", "R2", "R3")[rnd]]), 1) for pr in P.PROFILES})
            else:
                b = P.cap_builds()[rnd]; ps = b.pow_share(capL)
                caps.append({pr: round(P.track_win(pr, r, 30, trk, ps), 1) for pr in P.PROFILES})
    finally:
        P._walk_round, P.track_win = orig_walk, orig_track
    # arc
    ent = arc.entries_for(s); raw = res["story"][2]; ent["c8080"].L = raw["L"]; ent["c8080"].bag = raw["bag"]
    st = {"L": 46}
    orig_ot, orig_cvs, orig_pack = oracle.track_wr, A.combat_vs, A.wr_pack
    def step_of(d, L):
        if d == "wangan": return "F2"
        if d == "street": return "F3"
        return "F1" if L <= 64 else "F4"
    def ot_hook(pr, r, T, name):
        d = TRACK_D[name]
        if seg: return win(pr, r, T, name, seg[step_of(d, st["L"])])
        return orig_ot(pr, r, T, name)
    def cvs_hook(s_, C):
        st["L"] = int(s_.L); return orig_cvs(s_, C)
    if seg:
        oracle.track_wr = ot_hook; A.combat_vs = cvs_hook
        A.wr_pack = lambda pr, r, T, district: A.wr_cell(pr, r, T, district, True)
    try:
        if seg:
            races = core.arc_races(core.LIVE_ARC, arc.M, fill=core.LIVE.ARC_STORY_FILL)
            walks = [A.walk_profile(pr, ent[pr], races, arc.MODE[pr]) for pr in P.PROFILES]; ev = A.evaluate(walks)
        else:   # live baseline: the skill-points-v1 verify path (SP split per district change)
            import verify_live  # noqa: prints; recomputes the live arc
            walks, ev = verify_live.walks, verify_live.ev
    finally:
        oracle.track_wr, A.combat_vs, A.wr_pack = orig_ot, orig_cvs, orig_pack
    return dict(story_boss=[x["boss"]["c8080"] for x in s["story"]], story_min=[x["min8080"][0] for x in s["story"]],
                mixed=[(x["wall_grind"], x["post"]) for x in s["mixed"]], hard=[x["total"] for x in s["hard"]],
                at_cap=caps, arc=arc.brief(walks), issues=ev.get("issues"))

def fmt(name, o):
    print(f"== {name}")
    print("  story bosses 80/80", o["story_boss"], "min", o["story_min"], "| mixed", o["mixed"], "| 60/60", o["hard"])
    print("  at cap (60/60, 60/80, 80/60, 80/80)", [tuple(c[p] for p in P.PROFILES) for c in o["at_cap"]])
    for pr, a in o["arc"].items():
        print("  arc", pr, "grind", a["grind"], "billed", a["billed"], "min", a["min_story"])
    print("  issues", o["issues"])

def aero_check(k):
    """Aero vs the regular set it replaces, at every boss / billed finale race at its cap r on the hardest track (30 turns)."""
    base, aer = S.walk(k, False), S.walk(k, True)
    rs = [P.combat_power(E.CAP_LEVEL[i], i) / E.opponent_budget(i, 6) for i in range(3)] + list(E.FINALE_TARGET_R)
    out = []
    for x, y, r in zip(base, aer, rs):
        d = x["district"]; trk = E.BOSS_HARD_TRACK[d]
        sb = tuple(round(v, 3) for v in x["car_split"]); sa = tuple(round(v, 3) for v in y["car_split"])
        try:
            g = {pr: round(win(pr, r, 30, trk, sa) - win(pr, r, 30, trk, sb), 1) for pr in P.PROFILES}
        except KeyError:
            g = None
        out.append(dict(seg=x["seg"], r=round(r, 4), base=x["car_share"], aero=y["car_share"], aero_mods=y["mods"], gain_pp=g))
    return out

if __name__ == "__main__":
    out = {}
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        out["live"] = run(None)
    fmt("live (SP split, B=20%)", out["live"])
    for k in S.SCHEMES:
        for aero, lk in ((False, False), (False, True)):
            name = k + ("+aero" if aero else "") + (" T4-locked" if lk else "")
            rows = S.walk(k, aero, lock_t4=lk)
            try:
                o = run(rows); o["splits"] = {x["seg"]: x["car_share"] for x in rows}; o["mods"] = {x["seg"]: x["mods"] for x in rows}
            except KeyError as ex:
                print("==", name, "skipped: no sweep for", ex); continue
            out[name] = o; fmt(name, o)
    for k in S.SCHEMES:
        out[k + " aero_check"] = aero_check(k)
        print("== aero", k); [print("  ", x["seg"], "r", x["r"], x["base"], "->", x["aero"], x["gain_pp"]) for x in out[k + " aero_check"]]
    json.dump(out, open(os.path.join(HERE, "mods_eval.json"), "w"), indent=1, default=str)
