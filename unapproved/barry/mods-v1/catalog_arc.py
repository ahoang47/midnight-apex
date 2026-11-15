"""Pre-finale arc + finale with the staged catalog buyer (draft econ-v1 arc walker, hooked; in memory only).
Win cells: on-tune table (wr_cell, no cache). Entry: each profile's catalog campaign end (L, bag, money, debt, garage)."""
import sys, copy, json
import retune as R                                   # skill-points-v1 machinery: arc walker modules
import catalog as C, catalog_walk as W
P, E, camp, arc, A, core = R.P, R.E, R.camp, R.arc, R.A, R.core
DIST = ("touge", "wangan", "street", "touge")
MODE_OF = {"c8080": "story", "c6080": "mixed", "c8060": "mixed", "c6060": "hard"}

def run(slots, cat=None, full=False):
    cat = cat or C.build(slots)
    camp_out = {m: W.run(m, slots, cat) for m in ("story", "mixed", "hard")}
    res = camp.run_all(camp.uniform((1, 1, 1))); s = camp.summary(res); ent = arc.entries_for(s)
    races = core.arc_races(core.LIVE_ARC, arc.M, fill=core.LIVE.ARC_STORY_FILL)
    story_ids = [rc["id"] for rc in races]
    orig = (A.combat_vs, A.shop_arc, A.credit_arc, A.wr_pack)
    CUR = {}
    def step_of(content_C):
        return min(range(4), key=lambda i: abs(A.FINALE_C[i] - content_C))
    def shop_hook(s_, unlock_done):
        st = CUR["step"]; s_.money = s_.G.shop(s_.money, int(s_.L), 3 + st, DIST[st], s_.done, False, f"arc {CUR['last']}")
    def cvs_hook(s_, content_C):
        CUR["step"] = step_of(content_C); shop_hook(s_, None)
        return s_.G.power(int(s_.L), 3 + CUR["step"], DIST[CUR["step"]])
    def credit_hook(s_, amount, unlock_done):
        if abs(amount - A.GRIND_PAY) > 1e-6:
            rid = story_ids[CUR["i"]]; CUR["i"] += 1; s_.done.add(("arc", rid)); CUR["last"] = rid
            CUR["log"].append(dict(id=rid, L=int(s_.L), money_before=round(s_.money, 0), owned=len(s_.G.owned),
                                   fill=round(100 * s_.G.fill(int(s_.L), 3 + CUR["step"], DIST[CUR["step"]]), 1),
                                   equipped=[m["id"] if m else "stock" for m in s_.G.equipped(DIST[CUR["step"]])]))
        if s_.debt > 0:
            take = min(s_.debt, E.DEBT_SHARE * amount); s_.debt -= take; s_.money += amount - take
        else: s_.money += amount
        shop_hook(s_, unlock_done)
    A.combat_vs, A.shop_arc, A.credit_arc = cvs_hook, shop_hook, credit_hook
    A.wr_pack = lambda pr, r, T, district: A.wr_cell(pr, r, T, district, True)
    walks, logs = [], {}
    try:
        for pr in P.PROFILES:
            out, G, done = camp_out[MODE_OF[pr]]; G = copy.deepcopy(G); done = set(done); last = out[-1]
            e = ent[pr]; e.L, e.bag, e.money, e.debt = last["L"], last["bag"], last["money"], last["debt"]
            if full:   # control: unlimited cash, everything unlocked = full fill = the live combat model
                e.money = 1e12; done |= {tuple(m["unlock"]) for m in cat}
            e.G, e.done = G, done
            CUR.update(step=0, i=0, last="entry", log=[])
            walks.append(A.walk_profile(pr, e, races, MODE_OF[pr])); logs[pr] = CUR["log"]
            walks[-1]["spent_arc"] = None
        ev = A.evaluate(walks)
    finally:
        A.combat_vs, A.shop_arc, A.credit_arc, A.wr_pack = orig
    return camp_out, walks, ev, logs

if __name__ == "__main__":
    slots = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    for full in (True, False):
        co, walks, ev, logs = run(slots, full=full)
        print("== control (full fill)" if full else "== buyer", slots, "slots")
        for w in walks:
            fin = [x for x in w["log"] if x["billed"]]
            print(" ", w["pr"], "grind", [w["grind"][i]["total"] for i in range(4)], "billed hard", [x["wr_hard"] for x in fin],
                  "min story hard", min(x["wr_hard"] for x in w["log"] if not x["billed"]), "end $", w["end_money"], "L", w["end_L"])
        print("  issues", ev.get("issues"))
