"""Check the live skill-points-v1 code (sim/ equations.py + progression.py) against the draft retune study at B = 20 %.
Campaign and at-cap bosses: live progression only. Arc / finale: the draft econ-v1 arc walker (retune.walk_arc) driven
by the live build functions (P.retune, P.Build, P.track_win) and the live config/winrate_offtune_v1.json."""
import retune as R
P, E, camp, arc = R.P, R.E, R.camp, R.arc
assert P.add_points is not None and E.RETUNE_BUDGET_FRACTION == 0.20
R.win_at = lambda pr, r, T, name, p: P.track_win(pr, r, T, name, p)
class _Seg(P.Build):
    d = property(lambda self: self.district)
R.Seg = _Seg
R.retune = lambda a, B, d: P.retune(a, d, B)
res = camp.run_all(camp.uniform((1, 1, 1))); s = camp.summary(res)
print("story bosses", [(x["boss_L"], x["boss"]["c8080"]) for x in s["story"]], "min", [x["min8080"] for x in s["story"]])
print("mixed", [(x["wall"], x["wall_grind"], x["post"]) for x in s["mixed"]], "hard", [x["total"] for x in s["hard"]])
print("at cap", [(x["pow_share"], x["c6060"], x["c8080"], x["ok"]) for x in P.boss_check_at_cap()])
ent = arc.entries_for(s); raw = res["story"][2]; ent["c8080"].L = raw["L"]; ent["c8080"].bag = raw["bag"]
end = {"c8080": res["story"][2]["build"], "c6080": res["mixed"][2]["build"], "c8060": res["mixed"][2]["build"], "c6060": res["hard"][2]["build"]}
walks, ev, alog = R.walk_arc(ent, end, E.RETUNE_BUDGET_FRACTION)
for pr, a in arc.brief(walks).items():
    print("arc", pr, "grind", a["grind"], "billed", a["billed"], "min", a["min_story"])
print("arc splits", alog); print("issues", ev.get("issues"))
