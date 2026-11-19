#!/usr/bin/env python3
"""Contact sheet for the approved 16 m two-row turnout lot kit."""
import os, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RND = os.path.join(HERE, 'renders')
OUT = os.path.join(RND, 'turnout_sheet.png')

PAPER = (10, 16, 28)
INK = (220, 226, 232)
DIM = (140, 155, 175)
ACC = (240, 200, 148)

def F(sz, bold=False):
    p = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if os.path.exists(p):
        return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

def load(name, scale=1):
    p = os.path.join(RND, name)
    im = Image.open(p).convert('RGB')
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    return im

def main():
    layout = {}
    tris = {}
    lp = os.path.join(HERE, 'layout.json')
    tp = os.path.join(HERE, 'tri_counts.json')
    if os.path.exists(lp):
        layout = json.load(open(lp))
    if os.path.exists(tp):
        tris = json.load(open(tp))

    # prefer Godot Cel A-soft frames; fall back to Blender stand-ins
    race_name = 'godot_cel_race_cam_640.png' if os.path.exists(os.path.join(RND, 'godot_cel_race_cam_640.png')) else 'w16_race_cam_640.png'
    over_name = 'godot_cel_lot_overview_640.png' if os.path.exists(os.path.join(RND, 'godot_cel_lot_overview_640.png')) else 'w16_overhead_640.png'
    race = load(race_name, 2)
    over = load(over_name, 2)
    closes = [
        ('16 m  ·  two-row stalls', 'w16_close_paint_640.png'),
        ('16 m  ·  P sign', 'w16_close_sign_640.png'),
        ('16 m  ·  Blender race cam', 'w16_race_cam_640.png'),
        ('16 m  ·  Blender overhead', 'w16_overhead_640.png'),
    ]
    close_ims = [(lab, load(fn, 1)) for lab, fn in closes if os.path.exists(os.path.join(RND, fn))]

    pad, gap, header, footer = 24, 16, 92, 180
    W = pad + race.width + gap + over.width + pad
    cw, ch = close_ims[0][1].size if close_ims else (640, 480)
    body_h = header + race.height + gap + 22 + ch + footer
    H = body_h + pad
    im = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(im)

    d.rectangle([0, 0, W, header - 8], fill=(8, 12, 22))
    d.text((pad, 14), 'TOUGE TURNOUT  ·  approved 16 m two-row kit  ·  Cel A soft', font=F(28, True), fill=ACC)
    d.text((pad, 52), 'art/kits/turnout_lot  ·  LotArt frame  ·  640×480, RGB555 + Bayer  ·  night navy/teal + #F0C894',
           font=F(16), fill=DIM)

    x, y = pad, header
    im.paste(race, (x, y))
    d.text((x, y + race.height + 2),
           'Godot race camera  ·  Cel A soft (CEL ON SOFT ON)  ·  640×480 nearest 2×',
           font=F(15), fill=INK)
    im.paste(over, (x + race.width + gap, y))
    d.text((x + race.width + gap, y + over.height + 2),
           'Godot lot overview  ·  lot on the INSIDE of the bend (cut / lattice)',
           font=F(15), fill=INK)

    y2 = header + race.height + gap + 22
    for i, (lab, cim) in enumerate(close_ims):
        xx = pad + i * (cw + gap)
        im.paste(cim, (xx, y2))
        d.text((xx, y2 + ch + 2), lab, font=F(14), fill=INK)

    y3 = y2 + ch + 28
    pocket = layout.get('pocket_m', 62)
    taper = layout.get('taper_m', 14)
    width = layout.get('pocket_w_m', 16)
    n_lamps = layout.get('n_lamps', 2)
    n_st = layout.get('n_stalls_per_row', 11)
    ang = layout.get('stall_angle_deg', 70)
    rows = layout.get('rows', 2)
    total = tris.get('total_tris', layout.get('total_tris', 1444))
    pieces = tris.get('piece_tris') or layout.get('piece_tris') or []
    piece_s = ',  '.join('%s %s' % (p['name'].replace('lot_', ''), p['tris']) for p in pieces)

    lines = [
        'Approved layout  %g m pocket along the road (incl. %g m entry / exit tapers)  ·  %g m deep  ·  %s angled stall rows  ·  7.5 m road  ·  %s stalls / row at %g°  ·  %s sodium lamps'
        % (pocket, taper, width, rows, n_st, ang, n_lamps),
        'Contents  dry-matte asphalt (smooth, no toon, painted soft 6 m pools)  ·  white stall lines, arrows, edge line (flat, no ink)  ·  orange-red chevron rumble + yellow centre line in LotArt (x < 0)',
        'Props (toon bands + 1 px #040810 ink)  curbs, wheel stops, lamp poles, entry P-sign, vending  ·  mid back lattice + cut-slope tapers  ·  cedar cards on the hill top',
        'Rebuild  ./run.sh    ·  length: POCKET_M  TAPER_M  POCKET_W  ROWS  N_LAMPS    ·  per-child glbs in glb/; copy LotArt.transform onto the other TurnoutLot slots',
        'Tris  %s total   [%s]' % (total, piece_s),
    ]
    for i, line in enumerate(lines):
        d.text((pad, y3 + i * 22), line, font=F(13), fill=INK if i == 0 or i == 4 else DIM)

    im.save(OUT)
    print('sheet', OUT, im.size)

if __name__ == '__main__':
    main()
