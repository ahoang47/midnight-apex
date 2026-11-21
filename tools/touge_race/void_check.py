#!/usr/bin/env python3
"""VOID check (Austin pt137u pic 5: ground / slope / trees missing past the guardrail).

COURSE poses (Austin 2026-11-20, authored terrain): the expected ground is Arthur's terrain itself (assets/env/touge/*.glb: the
turn sections, lot, galleries, backdrop) plus the code road (unapproved/gordon/road_export/road_surface.glb, the live strip).
A magenta pixel whose ray meets that geometry inside the fog (<= fog_near + FOG_K * (fog_far - fog_near)) is a VOID: geometry
that exists but was not drawn (section draw distance, a culled or missing surface). Below-horizon magenta pixels whose ray
meets nothing inside the fog are counted as HOLES (informational, asset coverage: a gap in the authored ground or open sky
past it) and listed per pose so Arthur can see them; they do not fail the check.
SCROLL STRAIGHT poses (plan Entry, the treadmill between corners, still the code roadside): the profile model below.

main.gd --void-sweep renders every race camera pose (plan stops E/A/X, the three QTE cameras at each QTE, RESULT, turnout +
lot views) with the clear colour set to magenta and the far plane at the district fog_far, and saves the raw frame, the camera
and the course samples. A magenta pixel means the ray met nothing inside the fog distance. That is only a VOID when the ray
passes through ground that must be there: the approved roadside profile (course.gd terrain_profile; verge / slope / cut / hill)
of the nearest leg, inside that leg's room (course.cap_at), extended out to what the cameras can see (fog_far + the furthest
camera offset from the road edge), at a distance where the fog has not yet hidden it (<= fog_near + FOG_K * (fog_far - fog_near)).
Ground deeper than the fog is fog-coloured in game, so it is not counted.
A ray counts only when it ENTERS that ground from above: the course crosses itself (turn 10 runs 25.7 m under turn 5), so a
camera on the lower leg sits below the upper leg's surface; starting under an overhang is not a hole, entering ground is.
Each turn's plan-Entry pose sits on that turn's own straight (pose["path"] = straight_NN; void_course.json has each).

usage: python3 tools/touge_race/void_check.py SHOTS_DIR [--masks OUT_DIR] [--max N]
prints VOID_CHECK ... PASS/FAIL (PASS = 0 void pixels) and REACH (required vs configured terrain reach)."""
import argparse, json, os, sys, math
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

FOG_K = 0.85      # count a hole only where the fog is < 85 %
TOL = 0.75        # the ray must be this far inside the expected ground (m)
STEP_PX = 2
ap = argparse.ArgumentParser(); ap.add_argument("shots"); ap.add_argument("--masks", default=""); ap.add_argument("--max", type=int, default=0)
ap.add_argument("--display", default=os.path.join(os.path.dirname(__file__), "..", "..", "spec", "display.json")); a = ap.parse_args()
disp = json.load(open(a.display)); D = disp["districts"]["touge"]; T = D.get("terrain", {})
course = json.load(open(os.path.join(a.shots, "void_course.json")))
poses = json.load(open(os.path.join(a.shots, "void_check.json")))
W = float(course["W"]); F = float(course["fog_far"]); fog_near = float(D.get("fog_near", 9.0))
t_fog = fog_near + FOG_K * (F - fog_near)
gw = float(D.get("gravel_w_m", 0.7)); ROAD_CLEAR = float(T.get("road_clear_m", 8.0)); GWALL = float(T.get("gallery_wall_m", 3.5))

def profiles(reach):
    so = float(T.get("out_slope", 7.5 / 8.45)); si = float(T.get("in_slope", 0.35))
    out = [(0.0, 0.0), (0.55, 0.0), (9.0, -7.5), (reach, -7.5 - so * (reach - 9.0))]
    ins = [(0.0, 0.02), (gw, 0.02), (8.7, 7.6), (18.0, 10.0), (reach, 10.0 + si * (reach - 18.0))]
    return [np.array(out), np.array(ins)]

paths = {}
for nm, arr in course["paths"].items():
    A = np.array(arr, dtype=float)   # s, x, z, y, tx, tz, drop, cap_l, cap_r (+ col 9: drop side flips within 1 m)
    fl = np.zeros(len(A)); dr = A[:, 6]
    fl[1:] = np.maximum(fl[1:], dr[1:] != dr[:-1]); fl[:-1] = np.maximum(fl[:-1], dr[:-1] != dr[1:])
    A = np.column_stack([A, fl])
    paths[nm] = (A, cKDTree(A[:, 1:3]))
lot = course.get("lot")

ENV = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "env", "touge")
ROAD = os.path.join(os.path.dirname(__file__), "..", "..", "unapproved", "gordon", "road_export", "road_surface.glb")
_rays = None
THIN_MATS = ("touge_guardrail", "emit_reflector", "lamp_post")   # = scripts/touge_env.gd THIN_MATS
def env_rays():
    """embree ray intersector over the authored terrain + the code road (world space, +Y up: glTF and Godot agree)"""
    global _rays
    if _rays is None:
        import trimesh
        parts = []
        for f in sorted(os.listdir(ENV)):
            if f.endswith(".glb") and not f.endswith("_col.glb"):
                sc = trimesh.load(os.path.join(ENV, f), force="scene")
                for node in sc.graph.nodes_geometry:   # ground only: thin parts (rails, reflectors, lamp posts) are not ground and
                    T_, g = sc.graph[node]             # their 1-2 px silhouettes do not line up with the pixel-centre rays
                    m = sc.geometry[g]
                    if g.endswith("_lamps") or getattr(getattr(m.visual, "material", None), "name", "") in THIN_MATS: continue
                    m = m.copy(); m.apply_transform(T_); parts.append(m)
        parts.append(trimesh.load(ROAD, force="scene").to_geometry())
        m = trimesh.util.concatenate(parts)
        try:
            from trimesh.ray.ray_pyembree import RayMeshIntersector
            _rays = RayMeshIntersector(m)
        except Exception:
            _rays = trimesh.ray.ray_triangle.RayMeshIntersector(m)
    return _rays

def first_hit(o, d):
    """distance along each unit ray d (N,3) from o to the first authored surface (inf = none)"""
    r = env_rays()
    O = np.repeat(o[None, :], len(d), 0)
    loc, ir, _ = r.intersects_location(O, d, multiple_hits=False)
    t = np.full(len(d), np.inf)
    if len(ir): t[ir] = np.linalg.norm(loc - O[ir], axis=1)
    return t

def cam_rays(p, img):
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h:STEP_PX, 0:w:STEP_PX]
    sub = img[0:h:STEP_PX, 0:w:STEP_PX]
    mag = (sub[..., 0] > 230) & (sub[..., 1] < 40) & (sub[..., 2] > 230)
    bx, by, bz = np.array(p["bx"]), np.array(p["by"]), np.array(p["bz"])
    tv = math.tan(math.radians(p["fov"]) / 2); asp = w / h
    xn = (2 * (xs + 0.5) / w - 1) * tv * asp; yn = (1 - 2 * (ys + 0.5) / h) * tv
    d = -bz[None, None, :] + xn[..., None] * bx + yn[..., None] * by
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    sel = mag & (d[..., 1] < 0)
    return xs[sel], ys[sel], d[sel]

def expected_ground(P, nm, prof):
    """for points P (N,3): height of the ground the approved roadside puts there (nan = none expected)"""
    A, tree = paths[nm]
    reach = prof[0][-1, 0]
    dist, idx = tree.query(P[:, [0, 2]], k=24, distance_upper_bound=reach + W + 2.0)   # 24: stacked legs (1 m samples) both in reach
    best = np.full(len(P), np.nan); open_ = np.zeros(len(P), bool)
    for k in range(idx.shape[1]):
        ok = np.isfinite(dist[:, k])
        if not ok.any(): continue
        ii = idx[ok, k]; c = A[ii]; q = P[ok]
        vx = q[:, 0] - c[:, 1]; vz = q[:, 2] - c[:, 2]
        along = vx * c[:, 4] + vz * c[:, 5]
        dlat = vx * (-c[:, 5]) + vz * c[:, 4]
        side = np.where(dlat >= 0, 1.0, -1.0)
        e = np.abs(dlat) - W
        room = np.where(side > 0, c[:, 8], c[:, 7]) - W - 0.4
        good = (np.abs(along) <= 0.75) & (e <= room)
        outside = side == c[:, 6]
        yo = np.interp(np.maximum(e, 0), prof[0][:, 0], prof[0][:, 1])
        yi = np.interp(np.maximum(e, 0), prof[1][:, 0], prof[1][:, 1])
        if lot is not None and nm == "course":   # turnout pocket: the lot floor out to its depth, then the cut steps back
            s = c[:, 0] + along; inl = (side == lot["ins"]) & (s >= lot["s0"]) & (s <= lot["s1"])
            u = np.clip(np.minimum(s - lot["s0"], lot["s1"] - s) / max(lot["taper"], 1e-3), 0, 1)
            Ld = lot["w"] * u
            yl = np.where(e <= Ld + 0.7, 0.03, np.interp(np.maximum(e - Ld, 0), prof[1][:, 0], prof[1][:, 1]))
            yi = np.where(inl, yl, yi)
            # the flanks: lattice modules yawed along the taper diagonal (touge_dressing _lot BackWall), so near each end the cut
            # rises from that diagonal, not across the road; the lower of the two models is expected (never a false void)
            tp, LW = lot["taper"], lot["w"]; dl = math.hypot(tp, LW)
            for s_a, dr_, lo, hi in ((lot["s0"], 1.0, lot["s0"] - 8.0, lot["s0"] + tp + 1.0), (lot["s1"], -1.0, lot["s1"] - tp - 1.0, lot["s1"] + 8.0)):
                h = ((s - s_a) * (-dr_ * LW) + (e - 0.7) * tp) / dl
                yd = np.where(h <= 0, 0.03, np.interp(h + 0.7, prof[1][:, 0], prof[1][:, 1]))
                zone = (side == lot["ins"]) & (s >= lo) & (s <= hi)
                yi = np.where(zone, np.minimum(yi, yd), yi)
        # 1 m samples cannot place a drop-side flip (course.drop_runs) closer than 1 m: next to one either profile is right
        y = c[:, 3] + np.where(e < 0, 0.0, np.where(c[:, 9] > 0, np.minimum(yo, yi), np.where(outside, yo, yi)))
        # a road keeps its clear space (road + rail line out to gallery_wall_m) even under another leg: turn 5 runs ~20 m right
        # over turn 10, which runs in a gallery there (course.gd groof walls at gallery_wall_m, tskmax keeps turn 5's skirts
        # road_clear_m up); air above a road's own ground inside its gallery line is open, not missing ground
        clr = (np.abs(along) <= 0.75) & (e <= GWALL) & (q[:, 1] >= y - TOL)
        opn = open_[ok]; opn |= clr; open_[ok] = opn
        y = np.where(good, y, np.nan)
        cur = best[ok]
        best[ok] = np.where(np.isnan(cur), y, np.where(np.isnan(y), cur, np.maximum(cur, y)))
    best[open_] = np.nan
    return best

# reach the cameras need: fog distance + the furthest any pose sits from its road edge
max_e = 0.0
def pname(p):
    nm = p.get("path") or ("straight" if p.get("st") else "course")
    return nm if nm in paths else ("straight" if p.get("st") else "course")
for p in poses:
    A, tree = paths[pname(p)]
    dd, ii = tree.query([p["pos"][0], p["pos"][2]]); max_e = max(max_e, dd - W)
need_reach = F + max_e
cfg_reach = float(T.get("reach_m", 18.0))
prof = profiles(max(need_reach, cfg_reach))
print("REACH required %.1f m (fog_far %.0f + furthest camera %.1f m beyond the road edge), configured %.1f m %s" % (need_reach, F, max_e, cfg_reach, "OK" if cfg_reach >= need_reach else "SHORT"))
tot = 0; bad = []; holes = []
if a.masks: os.makedirs(a.masks, exist_ok=True)
for n, p in enumerate(poses):
    if a.max and n >= a.max: break
    f = os.path.join(a.shots, "void_raw", p["tag"] + ".png")
    if not os.path.exists(f): continue
    img = np.array(Image.open(f).convert("RGB"))
    xs, ys, d = cam_rays(p, img)
    o = np.array(p["pos"]); nm = pname(p)
    hit = np.zeros(len(d), bool)
    if len(d) and nm == "course":   # authored terrain: met inside the fog = not drawn = VOID; met nothing = HOLE (info)
        dz = d @ (-np.array(p["bz"]))
        tmax = np.minimum(t_fog, p["far"] / np.maximum(dz, 1e-3))
        t = first_hit(o, d)
        hit = t <= tmax
        # not on a silhouette: the rays one pixel left / right / up / down must meet the ground inside the fog too. A crack or a
        # culled section is surrounded by ground on every side; an edge pixel (deck lip, cut crest against the sky) is not, and
        # there the pixel-centre ray and the rasteriser can disagree by one pixel
        if hit.any():
            bx_, by_, bz_ = np.array(p["bx"]), np.array(p["by"]), np.array(p["bz"])
            h_, w_ = img.shape[:2]; tv = math.tan(math.radians(p["fov"]) / 2); asp = w_ / h_
            hi = np.where(hit)[0]
            for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                xn = (2 * (xs[hi] + ox + 0.5) / w_ - 1) * tv * asp; yn = (1 - 2 * (ys[hi] + oy + 0.5) / h_) * tv
                dn = -bz_[None, :] + xn[:, None] * bx_ + yn[:, None] * by_
                dn /= np.linalg.norm(dn, axis=1, keepdims=True)
                tn = first_hit(o, dn)
                hit[hi[~(tn <= np.minimum(t_fog, p["far"] / np.maximum(dn @ (-bz_), 1e-3)))]] = False
        nh = int(np.sum(~np.isfinite(t))) * STEP_PX * STEP_PX
        if nh: holes.append((p["tag"], nh))
    elif len(d):
        dz = d @ (-np.array(p["bz"]))
        tmax = np.minimum(t_fog, p["far"] / np.maximum(dz, 1e-3))
        g0 = expected_ground(o[None, :], nm, prof)[0]
        above = np.full(len(d), bool(np.isnan(g0) or o[1] >= g0 - TOL))   # under an overhang (lower leg): not above yet
        for t in np.arange(0.5, t_fog + 0.01, 1.0):
            live = (~hit) & (t <= tmax)
            if not live.any(): break
            P = o + d[live] * t
            g = expected_ground(P, nm, prof)
            gg = np.nan_to_num(g, nan=-1e9)
            idx = np.where(live)[0]
            inside = (gg - TOL > P[:, 1]) & above[idx]
            hit[idx[inside]] = True
            above[idx] |= P[:, 1] >= gg
    nv = int(hit.sum()) * STEP_PX * STEP_PX
    tot += nv
    if nv: bad.append((p["tag"], nv))
    if a.masks and nv:
        m = img.copy()
        for x, y in zip(xs[hit], ys[hit]): m[y:y + STEP_PX, x:x + STEP_PX] = (255, 0, 0)
        Image.fromarray(m).save(os.path.join(a.masks, p["tag"] + ".png"))
bad.sort(key=lambda v: -v[1]); holes.sort(key=lambda v: -v[1])
print("HOLES (course, below-horizon magenta meeting no authored surface; asset coverage, info) poses=%d px=%d worst=[%s]" % (len(holes), sum(h[1] for h in holes), ", ".join("%s=%d" % h for h in holes[:10])))
print("VOID_CHECK poses=%d void_poses=%d void_px=%d worst=[%s] %s" % (len(poses), len(bad), tot, ", ".join("%s=%d" % b for b in bad[:10]), "PASS" if tot == 0 and cfg_reach >= need_reach else "FAIL"))
sys.exit(0 if tot == 0 and cfg_reach >= need_reach else 1)
