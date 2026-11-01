"""Steering + suspension clearance check (inside Blender).  Every front corner is posed at full lock (both ways)
combined with full bump, static and full droop; rear corners at bump / droop.  The posed tyre is tested against the
body shell, cabin, wheel-well liners, underbody, mirrors and the STI lip with a BVH overlap test, and the smallest
tyre-vertex-to-body distance is reported (tyre vertices only, so it is an upper bound on the true gap)."""
import bpy, bmesh, math
from mathutils.bvhtree import BVHTree
from mathutils import Vector
STATIC = ('WRX_Body', 'WRX_Cabin', 'WRX_Under', 'WRX_Mirror_L', 'WRX_Mirror_R', 'STI_FrontLip',
          'WRX_Liner_FL', 'WRX_Liner_FR', 'WRX_Liner_RL', 'WRX_Liner_RR')
def bvh(ob):
    dg = bpy.context.evaluated_depsgraph_get(); bm = bmesh.new(); bm.from_object(ob, dg); bm.transform(ob.matrix_world)
    t = BVHTree.FromBMesh(bm); verts = [v.co.copy() for v in bm.verts]; bm.free(); return t, verts
def check(rig, set_pose, rel_travel, BUMP, DROOP, LOCK, ROLL, summary_only=False):
    rep = {'spec': dict(bump=BUMP, droop=DROOP, lock_deg=LOCK, roll_deg=ROLL), 'poses': []}
    poses = []
    for st in (-LOCK, 0.0, LOCK):
        for dz in (BUMP, 0.0, -DROOP):
            poses.append((f'steer {st:+.0f} deg, travel {dz:+.3f}', st, {k: dz for k in ('FL', 'FR', 'RL', 'RR')}))
    worst = None; wf = None
    for name, st, wdz in poses:
        set_pose(rig, steer=st, wheel_dz=wdz)
        stat = {n: bvh(bpy.data.objects[n])[0] for n in STATIC if n in bpy.data.objects}
        row = {'pose': name, 'corners': {}}
        for k in ('FL', 'FR', 'RL', 'RR'):
            w = bpy.data.objects['WRX_Wheel_' + k]; tw, tv = bvh(w)
            hits = {n: len(tw.overlap(t)) for n, t in stat.items()}; hits = {n: c for n, c in hits.items() if c}
            dmin = 9.0; who = ''
            for n, t in stat.items():
                for v in tv[::2]:
                    r = t.find_nearest(v, 0.2)
                    if r[0] is not None and r[3] < dmin: dmin, who = r[3], n
            row['corners'][k] = dict(overlaps=hits, min_gap_m=round(dmin, 4), nearest=who)
            if worst is None or dmin < worst[0]: worst = (dmin, name, k, who)
            if k[0] == 'F' and (wf is None or dmin < wf[0]): wf = (dmin, name, k, who)
        rep['poses'].append(row)
    rep['all_clear'] = all(not c['overlaps'] for r in rep['poses'] for c in r['corners'].values())
    rep['tightest'] = dict(gap_m=round(worst[0], 4), pose=worst[1], corner=worst[2], against=worst[3])
    rep['tightest_front'] = dict(gap_m=round(wf[0], 4), pose=wf[1], corner=wf[2], against=wf[3])
    if summary_only: rep = {k: rep[k] for k in ('all_clear', 'tightest', 'tightest_front')}
    set_pose(rig); print('CLEARANCE all_clear', rep['all_clear'], 'tightest', rep['tightest'], 'front', rep['tightest_front'])
    for r in rep.get('poses', []):
        bad = {k: c['overlaps'] for k, c in r['corners'].items() if c['overlaps']}
        if bad: print('  ', r['pose'], bad)
    return rep
