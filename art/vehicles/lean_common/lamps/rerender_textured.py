"""Re-shoot the textured review frames (front34 / rear34 + textured compare orthos) of a lean car from its saved
.blend, with the same cameras as build_<car>_lean.py render_set (used after the headlamp molding post-step).
blender -b <car>_lean.blend -P rerender_textured.py -- xfwd|xleft raw_dir [s2000|brz]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import leanlib as LL, render_kit as RK
a = sys.argv[sys.argv.index('--') + 1:]; FR = LL.Frame(a[0]); rd = a[1]; MODE = a[2] if len(a) > 2 else 's2000'
for im in bpy.data.images:
    if im.source == 'FILE' and not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)):
        alt = os.path.join(os.path.dirname(bpy.data.filepath), 'tex', os.path.basename(im.filepath))
        if os.path.exists(alt): im.filepath = alt; im.reload()
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name.startswith('BP') or o.name.startswith('Blueprint') or o.name.startswith('orig_') or '_FX_' in o.name
shots = {'front34': ((5.6, 5.0, 1.35), (0.25, 0.0, 0.60), 55), 'rear34': ((-5.8, -4.8, 1.45), (-0.25, 0.0, 0.62), 55)}
RK.eevee()
for k, (loc, tg, lens) in shots.items(): RK.cam(FR, 'CAMt', loc, tg, lens); RK.shoot(os.path.join(rd, f'tex_{k}.png'), (640, 448))
if MODE == 's2000':
    CV = {"side": ((0, 9, .70), (0, 0, .70), 4.6, (1150, 375), None), "top": ((0, 0, 9), (0, 0, 0), 4.6, (550, 1150), (0, 1, 0)),
          "front": ((9, 0, .70), (0, 0, .70), 2.2, (550, 375), None), "rear": ((-9, 0, .70), (0, 0, .70), 2.2, (550, 375), None)}
    for k, (loc, tg, osc, res, ir) in CV.items():
        c_ = RK.cam(FR, 'CAMo', loc, tg, ortho=osc, image_right=ir); c_.data.sensor_fit = 'AUTO'; RK.shoot(os.path.join(rd, f'tex_cmp_{k}.png'), res)
else:   # BRZ build cameras
    ORTHO = {'side': ((0, 8, 0.65), (0, 0, 0.65), None), 'front': ((8, 0, 0.65), (0, 0, 0.65), None), 'rear': ((-8, 0, 0.65), (0, 0, 0.65), None),
             'top': ((0, 0, 8), (0, 0, 0), (-1, 0, 0))}
    for k, (loc, tg, ir) in ORTHO.items():
        RK.cam(FR, 'CAMo', loc, tg, ortho=5.0, image_right=ir); RK.shoot(os.path.join(rd, f'tex_{k}.png'), (1000, 1000))
    RK.clay(sil=True)
    for k, (loc, tg, ir) in ORTHO.items():
        RK.cam(FR, 'CAMs', loc, tg, ortho=5.0, image_right=ir); RK.shoot(os.path.join(rd, f'sil_{k}.png'), (1000, 1000))
