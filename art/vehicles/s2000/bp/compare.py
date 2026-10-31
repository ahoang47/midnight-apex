"""Composite blueprint crops vs ortho renders (4 mm/px world frames) -> renders/compare_*.png + IoU."""
import numpy as np, sys
from PIL import Image, ImageDraw
import os as _os; _B = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))) + '/'
R = _B + 'ref/'; RD = _B + 'renders/'; M = .004
def crop(n): return Image.open(R + f'bp_{n}.png').convert('RGB')
def frame_info(n):
    a = np.asarray(crop(n)).max(2); rows = np.where((a > 40).any(1))[0]; cols = np.where((a > 40).any(0))[0]
    return a, rows, cols
# side (side_left: nose left)
a, rows, cols = frame_info('side_left'); s = 4.14 / (cols.max() - cols.min() + 1); c0 = cols.min()
A = {'side': ((M / s, 0, c0 - .23 / s, 0, M / s, 209.5 - 1.45 / s), 'side_left', (1150, 375))}
a, rows, cols = frame_info('top'); st = 4.14 / (rows.max() - rows.min() + 1)
cx = (cols.min() + cols.max()) / 2
A['top'] = ((M / st, 0, cx - 1.1 / st, 0, M / st, rows.min() - .23 / st), 'top', (550, 1150))
for n in ('front', 'rear'):
    a, rows, cols = frame_info(n); rb = rows.max() + .5; ccx = (cols.min() + cols.max()) / 2
    A[n] = ((M / s, 0, ccx - 1.1 / s, 0, M / s, rb - 1.45 / s), n, (550, 375))
tag = sys.argv[1] if len(sys.argv) > 1 else ''
for v, (aff, src, size) in A.items():
    bp = crop(src).transform(size, Image.AFFINE, aff, resample=Image.BILINEAR)
    bpa = np.asarray(bp).astype(int); bmask = bpa.max(2) > 40
    rn = Image.open(RD + f'cmp_{v}{tag}.png').convert('RGBA'); ra = np.asarray(rn)
    mmask = ra[..., 3] > 128
    inter = (bmask & mmask).sum(); uni = (bmask | mmask).sum(); iou = inter / max(uni, 1)
    ov = np.zeros(bpa.shape, np.uint8) + 255
    ov[bmask & mmask] = (170, 170, 170); ov[bmask & ~mmask] = (40, 90, 255); ov[mmask & ~bmask] = (235, 40, 40)
    # blueprint line work on top of the diff
    g = bpa.mean(2); lines = (g < 120) & bmask
    ov[lines & mmask] = (60, 60, 60)
    render_on_white = Image.new('RGB', size, (255, 255, 255)); render_on_white.paste(rn, (0, 0), rn)
    W, H = size; pad = 10
    if W > H * 1.6:  # stack vertically for wide views
        out = Image.new('RGB', (W, H * 3 + pad * 2), (255, 255, 255))
        for i, im in enumerate((bp, render_on_white, Image.fromarray(ov))): out.paste(im, (0, i * (H + pad)))
    else:
        out = Image.new('RGB', (W * 3 + pad * 2, H), (255, 255, 255))
        for i, im in enumerate((bp, render_on_white, Image.fromarray(ov))): out.paste(im, (i * (W + pad), 0))
    d = ImageDraw.Draw(out); d.text((6, 4), f'{v}{tag}  IoU {iou:.3f}  (blue = blueprint only, red = model only)', fill=(255, 0, 0))
    out.save(RD + f'compare_{v}{tag}.png'); print(v + tag, 'IoU %.3f' % iou, 'bp-only px', (bmask & ~mmask).sum(), 'model-only px', (mmask & ~bmask).sum())
if '--rows' in sys.argv:
    for v in ('front', 'rear'):
        aff, src, size = A[v]
        bm = np.asarray(crop(src).transform(size, Image.AFFINE, aff, resample=Image.BILINEAR)).max(2) > 40
        mm = np.asarray(Image.open(RD + f'cmp_{v}{tag}.png'))[..., 3] > 128
        print(v)
        for z in np.arange(.1, 1.3, .05):
            r = int((1.45 - z) / M)
            def hw(m):
                c = np.where(m[r])[0]; return (c.max() - c.min()) / 2 * M if len(c) else 0
            print('  z %.2f bp %.3f model %.3f' % (z, hw(bm), hw(mm)))
