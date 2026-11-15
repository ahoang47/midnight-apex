"""Shared draft driver: live-track oracle + econ-v1 draft walks/criteria with a given constant set. Draft only."""
from __future__ import annotations
import json, os, sys, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "sim"))
import oracle, econ_patch
from velocity_shift import equations as LIVE   # read-only: current live constants

LIVE_LADDER = {d: tuple(v) for d, v in LIVE.LADDER_TARGET_R.items()}
LIVE_FINALE_R = tuple(LIVE.FINALE_TARGET_R)
LIVE_ARC = [dict(id=a[0], place=a[1], dist=a[2], T=a[3], r_design=a[4], xp_share=a[5], purse=a[6], B=a[7])
            for a in LIVE.FINALE_ARC]
PROFILES = ("c6060", "c6080", "c8060", "c8080")


def setup(ladder=None, finale_r=None, finale_B=None):
    return econ_patch.apply(ladder_r=ladder or LIVE_LADDER, finale_r=finale_r or LIVE_FINALE_R, finale_B=finale_B)


def boss_cells(r, district, T=30):
    out = {}
    hard = {"street": "S1_Shibuya_Grid", "touge": oracle.HARD_TOUGE,
            "wangan": os.environ.get("HARD_WANGAN")}.get(district)
    for pr in PROFILES:
        d = oracle.district_wr(pr, r, T, district)
        h = oracle.track_wr(pr, r, T, hard) if hard and hard != "mean" else d
        w, wn = oracle.worst_track(pr, r, T, district)
        out[pr] = dict(district=round(d, 1), hard=round(h, 1), worst=round(w, 1), worst_track=wn)
    return out


def campaign(M, mods):
    E = mods["evaluate"]
    with contextlib.redirect_stdout(io.StringIO()):
        res = E.score_params(M.EconParams())
    return res


def grind_summary(res):
    out = {}
    for mode, rnds in res["results_summary"].items():
        out[mode] = [dict(wall=w["wall"], wall_grind=w["wall_grind"], post=w["post"], total=w["total_grind"],
                          L=w["L"], money_usd=round(100 * w["money"]), debt_usd=round(100 * w["debt"]))
                     for w in rnds]
    return out


def arc_races(spec, M, fill=0.8):
    """spec: list of dicts (id, place, dist, T, r_design, xp_share, purse, B) for P/M races. Billed F races
    inserted from model FINALE_B / FINALE_R_C. Same order as econ-v1 build_arc."""
    by = {x["id"]: x for x in spec}
    order = ["P1", "P2", "P3", "P4", "F1", "M11", "M12", "F2", "M21", "M22", "F3", "M31", "M32", "F4"]
    dist_F = ("touge", "wangan", "street", "touge")
    races = []
    for rid in order:
        if rid.startswith("F"):
            i = int(rid[1]) - 1
            races.append(dict(id=rid, place=rid, step=i, dist=dist_F[i], T=30, r_design=M.FINALE_R_C[i],
                              xp_share=0.0, fill=fill, purse=10800.0, billed=True, unlock_t4=False,
                              B=M.FINALE_B[i], placeholder=""))
        else:
            x = by[rid]; step = 0 if rid.startswith("P") else int(rid[1])
            races.append(dict(id=rid, place=x["place"], step=step, dist=x["dist"], T=x["T"], r_design=x["r_design"],
                              xp_share=x["xp_share"], fill=fill, purse=x["purse"], billed=False,
                              unlock_t4=(rid == "P1"), B=x["B"], placeholder=""))
    return races


def run_arc(mods, races, entries=None):
    A = mods["run_finale_arc"]; L = mods["run_betting_levers"]
    with contextlib.redirect_stdout(io.StringIO()):
        if entries is None:
            entries = A.entry_states()
        walks = [A.walk_profile(pr, entries[pr], races, L.MODE[pr]) for pr in PROFILES]
        ev = A.evaluate(walks)
    return entries, walks, ev
