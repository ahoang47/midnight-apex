"""Build a 3-lane hairpin road texture from the urban stacked pack's road1_alt.

road1_alt is a 256x128 (along x across) two-lane tile with worn yellow edge lines
and faded white centre dashes already painted in. This script:

  1. Fills the carriageway by tiling a native crop of that pack's asphalt
     (no upscaling, no added noise, no lettering). Repeats are meant to show.
  2. Stamps the pack's own painted yellow edges and white dashes onto a 3-lane
     layout that matches the existing hairpin (10 m wide, dividers at +/-1.65 m,
     edges at +/-4.72 m).

Writes a 192x256 texture (U = across, V = along). Also writes a cropped concrete
tile from concrete_bare.jpg for the kerb/shoulder.

Sources stay in /workspace/asset_packs (CC0). The composed files are derivatives
of that CC0 pack, built at run time and also saved under tex/.
"""
import os
from PIL import Image
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'tex')
os.makedirs(TEX, exist_ok=True)

PACK = '/workspace/asset_packs/psx-style-urban-stacked-pack/x/URBAN/textures'
SRC_ROAD = os.path.join(PACK, 'road1_alt.png')
SRC_CONC = os.path.join(PACK, 'concrete_bare.jpg')

ROAD_W = 10.0
EDGE = 4.72
DST_W, DST_H = 192, 256  # U across, V along


def u_for(off):
    return (off + ROAD_W / 2.0) / ROAD_W * DST_W


def compose_road():
    src = Image.open(SRC_ROAD).convert('RGB')
    assert src.size == (256, 128), src.size
    a = np.asarray(src)  # [y=across 128, x=along 256, 3]

    # Native pack asphalt with no line paint. Rows 16-58 sit between the top
    # yellow edge and the centre dashes; 42x256 is the full along-track run,
    # tiled 1:1 so pack pixels stay pack pixels and the repeat is visible.
    tile = a[16:58, 0:256]          # (42 across, 256 along, 3)
    th, tw = tile.shape[0], tile.shape[1]

    dst = np.zeros((DST_H, DST_W, 3), np.uint8)
    for u in range(DST_W):
        # Phase-shift each third of the width by a pack-sized offset so the three
        # lanes do not clone the same tile phase (still only pack pixels).
        phase = (0, 40, 80)[min(2, u * 3 // DST_W)]
        tu = u % th
        for v in range(DST_H):
            dst[v, u] = tile[tu, (v + phase) % tw]

    def stamp_rows(src_ys, dest_u_center):
        rows = [a[y] for y in src_ys]  # each (256, 3) along-track, already painted
        n = len(rows)
        u0 = int(round(dest_u_center)) - n // 2
        for i, row in enumerate(rows):
            u = u0 + i
            if 0 <= u < DST_W:
                # Source is 256 along; dest V is 256, so this is a 1:1 copy of the
                # pack's painted pixels (the 256-wide source maps straight to V).
                dst[:, u] = row

    # Yellow edge paint: source rows 2-6 and 121-125 (pack pixels, worn yellow).
    stamp_rows([2, 3, 4, 5, 6], u_for(-EDGE))
    stamp_rows([121, 122, 123, 124, 125], u_for(+EDGE))
    # White dashes at the two 3-lane dividers: source rows 61-65.
    stamp_rows([61, 62, 63, 64, 65], u_for(-1.65))
    stamp_rows([61, 62, 63, 64, 65], u_for(+1.65))

    im = Image.fromarray(dst, 'RGB')
    path = os.path.join(TEX, 'road_3lane.png')
    im.save(path)
    print('wrote', path, im.size, 'vscale_m', ROAD_W * DST_H / DST_W)
    return im


def compose_concrete():
    src = Image.open(SRC_CONC).convert('RGB')
    # 256x92; top ~64 px is usable stained concrete (the bottom third is a moss
    # fringe that would stripe if tiled on a kerb).
    crop = src.crop((0, 0, 256, 64))
    path = os.path.join(TEX, 'concrete_kerb.png')
    crop.save(path)
    print('wrote', path, crop.size)
    return crop


if __name__ == '__main__':
    road = compose_road()
    compose_concrete()
    road.resize((road.width * 4, road.height * 4), Image.NEAREST).save(os.path.join(TEX, 'road_3lane_preview.png'))
    print('compose ok')
