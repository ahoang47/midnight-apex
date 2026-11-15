"""planner-v1: Python reference walks for the JS-port check (live sim; leftover XP carry-over fix C is live since 2026-11-14). Run from sim/:
PYTHONPATH=.:../unapproved/barry/mods-v1:../unapproved/barry/skill-points-v1 python3 ../unapproved/barry/planner-v1/py_reference.py
Writes py_reference.json (campaign rows per policy, at-cap boss check, arc + finale logs per profile)."""
import json, os, copy, io, contextlib
import verify_live as V
from velocity_shift import equations as E, progression as P
HERE = os.path.dirname(os.path.abspath(__file__))
out = {}
if True:   # live sim, no patches
    camp = {}; raw = {}
    for mode in ("story", "mixed", "hard"):
        rounds, G, done = P.run_with_garage(mode); raw[mode] = (rounds, G, done)
        camp[mode] = [dict(rung=f"R{r['rnd']}{r['rung']}", L=r["arrive_L"], r=r["arrive_r"], ps=r["pow_share"],
                           wr={pr: [r["wr"][pr]["district"], P.hard_win(r["wr"][pr])] for pr in P.PROFILES},
                           grind=r["grind_here"] + r["pre_boss_grind"], money=r["money"], equipped=r["equipped"], build=list(r["build"]))
                      for w in rounds for r in w["rows"]]
    out["campaign"] = camp
    out["at_cap"] = [(c["c6060"], c["c8080"]) for c in P.boss_check_at_cap()]
    # arc walk: copy of mods-v1/verify_live.arc_walk returning the logs
    A, core, arc, camp_m = V.A, V.core, V.arc, V.camp
    with contextlib.redirect_stdout(io.StringIO()):
        res = camp_m.run_all(camp_m.uniform((1, 1, 1)))
    ent = arc.entries_for(camp_m.summary(res))
    races = core.arc_races(core.LIVE_ARC, arc.M, fill=core.LIVE.ARC_STORY_FILL); ids = [rc["id"] for rc in races]
    orig = (A.combat_vs, A.shop_arc, A.credit_arc, A.wr_pack); CUR = {}
    step_of = lambda Cc: min(range(4), key=lambda i: abs(A.FINALE_C[i] - Cc))
    def shop(s_, u):
        st = CUR["step"]; s_.money = s_.G.shop(s_.money, int(s_.L), 3 + st, V.DIST[st], s_.done, False, "arc")
    def cvs(s_, Cc):
        CUR["step"] = step_of(Cc); shop(s_, None); return s_.G.power(int(s_.L), 3 + CUR["step"], V.DIST[CUR["step"]])
    def credit(s_, amount, u):
        if abs(amount - A.GRIND_PAY) > 1e-6:
            s_.done.add(P.arc_unlock_token(ids[CUR["i"]])); CUR["i"] += 1
        if s_.debt > 0:
            take = min(s_.debt, E.DEBT_SHARE * amount); s_.debt -= take; s_.money += amount - take
        else:
            s_.money += amount
        shop(s_, u)
    A.combat_vs, A.shop_arc, A.credit_arc = cvs, shop, credit
    A.wr_pack = lambda pr, r, T, district: A.wr_cell(pr, r, T, district, True)
    arcs = {}
    try:
        for pr in P.PROFILES:
            rounds, G, done = raw[V.MODE_OF[pr]]; last = rounds[-1]; e = ent[pr]
            e.L, e.bag, e.money, e.debt = last["L"], last["bag"], last["money"], last["debt"]
            e.G, e.done = copy.deepcopy(G), set(done); CUR.update(step=0, i=0)
            w = A.walk_profile(pr, e, races, V.MODE_OF[pr])
            arcs[pr] = dict(mode=V.MODE_OF[pr], log=[dict(id=x["id"], L=x["L"], r=x["r"], wr=[x["wr_dist"], x["wr_hard"]], g=x["wall_grinds"] + x["to_cap_grinds"],
                                                          money=x["money"]) for x in w["log"]], end_money=w["end_money"])
    finally:
        A.combat_vs, A.shop_arc, A.credit_arc, A.wr_pack = orig
    out["arc"] = arcs
json.dump(out, open(os.path.join(HERE, "py_reference.json"), "w"), indent=0)
s = out["campaign"]["story"]
print("story 80/80 rows", [(x["rung"], x["L"], x["wr"]["c8080"]) for x in s])
print("at cap", out["at_cap"])
for pr, a in arcs.items(): print(pr, a["mode"], [(x["id"], x["L"], x["wr"][1], x["g"]) for x in a["log"]])
