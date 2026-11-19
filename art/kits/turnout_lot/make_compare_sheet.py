#!/usr/bin/env python3
"""11 m (1-row, comparison only) vs approved 16 m (2-row) turnout sheet."""
import os, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RND = os.path.join(HERE, 'renders')
OUT = os.path.join(RND, 'turnout_11_vs_16.png')
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

def layout(tag):
    if tag in ('', 'w16'):
        candidates = [
            os.path.join(HERE, 'layout.json'),
            os.path.join(HERE, 'glb', 'layout.json'),
            os.path.join(HERE, 'glb', 'w16', 'layout.json'),
        ]
    else:
        candidates = [
            os.path.join(RND, '%s_layout.json' % tag),
            os.path.join(HERE, 'glb', tag, 'layout.json'),
        ]
    for p in candidates:
        if os.path.exists(p):
            return json.load(open(p))
    return {}

def tri_line(lay):
    pieces = lay.get('piece_tris') or []
    slots = [p for p in pieces if p['name'] != 'lot_assembled_preview']
    total = lay.get('total_tris') or sum(p['tris'] for p in slots)
    bits = ',  '.join('%s %s' % (p['name'].replace('lot_', ''), p['tris']) for p in slots)
    return total, bits

def main():
    a, b = layout('w11'), layout('w16')
    race11 = load('w11_race_cam_640.png', 2)
    race16 = load('w16_race_cam_640.png', 2)
    over11 = load('w11_overhead_640.png', 2)
    over16 = load('w16_overhead_640.png', 2)
    closes = []
    for lab, fn in (
        ('11 m  ·  stall lines', 'w11_close_paint_640.png'),
        ('11 m  ·  P sign', 'w11_close_sign_640.png'),
        ('16 m  ·  two-row stalls', 'w16_close_paint_640.png'),
        ('16 m  ·  P sign', 'w16_close_sign_640.png'),
    ):
        closes.append((lab, load(fn, 1)))

    pad, gap, header, footer = 24, 16, 96, 210
    W = pad + race11.width + gap + race16.width + pad
    cw, ch = closes[0][1].size
    H = header + race11.height + 22 + gap + over11.height + 22 + gap + ch + 22 + footer
    im = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, header - 8], fill=(8, 12, 22))
    d.text((pad, 16), 'TOUGE TURNOUT  ·  11 m vs approved 16 m  ·  LotArt frame  ·  Cel A soft', font=F(28, True), fill=ACC)
    d.text((pad, 56),
           'art/kits/turnout_lot  ·  Godot Y-up, +X into lot, +Z along travel  ·  inside of the bend  ·  640×480 RGB555+Bayer',
           font=F(16), fill=DIM)

    x, y = pad, header
    im.paste(race11, (x, y))
    d.text((x, y + race11.height + 2),
           '11 m  ·  one angled back row + through-aisle  ·  race cam 2.45 m / 47°  ·  comparison only',
           font=F(15), fill=INK)
    im.paste(race16, (x + race11.width + gap, y))
    d.text((x + race11.width + gap, y + race16.height + 2),
           '16 m  ·  two angled rows  ·  same camera  ·  approved kit',
           font=F(15), fill=INK)

    y = header + race11.height + 22 + gap
    im.paste(over11, (pad, y))
    d.text((pad, y + over11.height + 2),
           '11 m overhead  ·  lot on the INSIDE (cut / lattice)  ·  road in the foreground',
           font=F(15), fill=INK)
    im.paste(over16, (pad + over11.width + gap, y))
    d.text((pad + over11.width + gap, y + over16.height + 2),
           '16 m overhead  ·  same frame, two stall rows  ·  approved kit',
           font=F(15), fill=INK)

    y = y + over11.height + 22 + gap
    for i, (lab, cim) in enumerate(closes):
        xx = pad + i * (cw + gap)
        im.paste(cim, (xx, y))
        d.text((xx, y + ch + 2), lab, font=F(14), fill=INK)

    y = y + ch + 28
    t11, s11 = tri_line(a)
    t16, s16 = tri_line(b)
    n11 = a.get('n_stalls_per_row', '?')
    n16 = b.get('n_stalls_per_row', '?')
    r11 = a.get('pool_radius_m', 6)
    r16 = b.get('pool_radius_m', 6)
    lines = [
        'Slot  62 m pocket × 11 or 16 m deep, 14 m tapers, 30 m approach, 110 m total  ·  stalls 2.5 × 5.0 m at 70°  ·  curb 0.15 m  ·  2 sodium lamps, pools r = %s m (no overlap)' % r11,
        '11 m  1 angled row along the back + through-aisle  ·  %s stalls  ·  %s tris   [%s]   ·  comparison only, not the approved kit' % (n11, t11, s11),
        '16 m  2 angled rows (approved)  ·  %s stalls / row  ·  %s tris   [%s]' % (n16, t16, s16),
        'Mapping  lot_floor→Floor  lot_curbs→Curbs  lot_stall_lines→StallLines  lot_wheel_stops→WheelStops  lot_back_wall→BackWall  lot_hill_top→HillTop  lot_lamps→Lamps  lot_props→Props  lot_road_paint→LotArt',
        'Drop-in  instance each glb as a child of the matching TurnoutLot slot. Copy LotArt.transform onto Floor, Curbs, StallLines, WheelStops, BackWall, HillTop, Lamps and Props (Gordon currently only moves LotArt). Rebuild: ./run.sh',
    ]
    for i, line in enumerate(lines):
        d.text((pad, y + i * 22), line, font=F(13), fill=INK if i < 3 else DIM)

    im.save(OUT)
    print('sheet', OUT, im.size)

if __name__ == '__main__':
    main()
