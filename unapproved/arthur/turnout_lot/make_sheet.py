#!/usr/bin/env python3
"""Contact sheet for the turnout lot kit: race cam, overhead, close-ups, notes."""
import os, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RND = os.path.join(HERE, 'renders')
OUT = os.path.join(RND, 'turnout_sheet.png')

FOG = (0x0B, 0x17, 0x2B)
PAPER = (10, 16, 28)
INK = (220, 226, 232)
DIM = (140, 155, 175)
ACC = (240, 200, 148)

def font(sz):
    for p in (
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

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

    race = load('race_cam_640.png', 2)       # 1280x960
    over = load('overhead_640.png', 2)
    closes = [
        ('island / edge line / chevrons', 'close_island_640.png'),
        ('angled stalls, arrows, wheel stops', 'close_stalls_640.png'),
        ('sodium lamp + soft pool', 'close_lamp_640.png'),
        ('entry taper + sign', 'close_entry_640.png'),
    ]
    close_ims = [(lab, load(fn, 1)) for lab, fn in closes]  # 640x480

    pad = 24
    gap = 16
    header = 92
    footer = 200
    W = pad + race.width + gap + over.width + pad
    # closes in a row of 4 under the two heroes
    cw, ch = close_ims[0][1].size
    body_h = header + race.height + gap + 22 + ch + footer
    H = body_h + pad
    im = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(im)

    d.rectangle([0, 0, W, header - 8], fill=(8, 12, 22))
    d.text((pad, 14), 'TOUGE TURNOUT  ·  parking-lot kit  ·  Cel A soft', font=F(28, True), fill=ACC)
    d.text((pad, 52), 'unapproved / arthur  ·  640×480, RGB555 + Bayer  ·  night navy/teal + #F0C894  ·  not committed',
           font=F(16), fill=DIM)

    x, y = pad, header
    im.paste(race, (x, y))
    d.text((x, y + race.height + 2), 'Race camera  ·  2.45 m up, 47° lens, passing the lot  ·  640×480 nearest 2×',
           font=F(15), fill=INK)
    im.paste(over, (x + race.width + gap, y))
    d.text((x + race.width + gap, y + over.height + 2),
           'Overhead layout  ·  lot on the outside of a bend  ·  Hakone-style reference',
           font=F(15), fill=INK)

    y2 = header + race.height + gap + 22
    for i, (lab, cim) in enumerate(close_ims):
        xx = pad + i * (cw + gap)
        im.paste(cim, (xx, y2))
        d.text((xx, y2 + ch + 2), lab, font=F(14), fill=INK)

    # notes
    y3 = y2 + ch + 28
    pocket = layout.get('pocket_m', 62)
    taper = layout.get('taper_m', 14)
    width = layout.get('pocket_w_m', 16)
    n_lamps = layout.get('n_lamps', 3)
    n_st = layout.get('n_stalls_per_row', '?')
    ang = layout.get('stall_angle_deg', 70)
    total = tris.get('assembled_tris_total', '?')
    byk = tris.get('assembled_tris_by_kind', {})
    pieces = tris.get('piece_tris', [])
    piece_s = ',  '.join('%s %s' % (p['name'].replace('lot_', ''), p['tris']) for p in pieces[:12])
    piece_s2 = ',  '.join('%s %s' % (p['name'].replace('lot_', ''), p['tris']) for p in pieces[12:])

    lines = [
        'Default layout  %g m pocket along the road (incl. %g m entry / exit tapers)  ·  %g m deep  ·  7.5 m road  ·  %s angled stalls / row at %g°  ·  %s sodium lamps' %
        (pocket, taper, width, n_st, ang, n_lamps),
        'Contents  dry-matte asphalt (smooth, no toon, painted soft pools — no rings)  ·  white stall lines, arrows, edge line (flat decals, no ink)  ·  orange-red chevron rumble + yellow centre line (flat, no ink)',
        'Props (toon bands + 1 px #040810 ink)  raised island curb, wheel stops, white W-beam guardrail on the outer edge, lamp poles, entry P-sign, vending  ·  cedar wall behind the rail',
        'Length  POCKET_M  TAPER_M  POCKET_W  N_LAMPS  CURVE_R  STALL_W  STALL_ANGLE  ./run.sh    ·  mid-section length = POCKET_M − 2×TAPER_M; stall count follows that run. Modular 5 m asphalt / 4 m curb / 4 m rail pieces in glb/.',
        'Tris  assembled preview %s  (%s)  ·  pieces: %s' % (total, ', '.join('%s %s' % (k, v) for k, v in byk.items()), piece_s),
        (piece_s2 if piece_s2 else ''),
    ]
    for i, line in enumerate(lines):
        if not line:
            continue
        d.text((pad, y3 + i * 22), line, font=F(13), fill=DIM if i else INK)

    im.save(OUT)
    # also drop copies of the two hero frames at the renders root with the requested names
    print('sheet', OUT, im.size)

if __name__ == '__main__':
    main()
