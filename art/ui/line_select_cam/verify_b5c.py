"""B.5c check for the approved line_select_cam and line_vs_line frames.  python3 verify_b5c.py
For each final 1280x960 frame: (1) every 2x2 block is uniform and the 640x480 decimation equals the saved native frame;
(2) overlay layers have binary alpha; (3) every pixel on the inside edge of a hard overlay equals RGB555+Bayer of the overlay
colour alone, and every pixel on the outside ring equals RGB555+Bayer of what is underneath alone (= no blended AA pixels);
(4) unique colours on those edges vs. the overlay palette. Contact sheets: every frame tile equals its final frame exactly."""
import os, sys, json, numpy as np
from PIL import Image
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5
def rgb555(a):
    h, w = a.shape[:2]; t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    return (np.clip(np.floor(a / 8 + t + 0.5), 0, 31) * 8.2258).clip(0, 255).astype(np.uint8)
def edges(m):
    p = np.pad(m, 1); n = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]; inner = m & ~n
    g = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]; ring = ~m & g; return inner, ring
# Paths are box working copies under /workspace/mockups/. The unapproved repo copy of line_clash/ was removed 2026-11-13 (git history); approved frames are in art/ui/line_vs_line/.
SETS = [('/workspace/mockups/line_select_cam', ['1_entry_pick', '2_apex_pick', '3_exit_pick', '4_line_locked'], 'line_select_cam_contact_sheet.png', 'sheet_layout.json'),
        ('/workspace/mockups/line_clash', ['a1_entry_line_vs_line', 'a2_apex_line_vs_line', 'a3_exit_line_vs_line'], 'line_vs_line_sheet.png', 'sheet_layout_line_vs_line.json')]
rep = {}; ok = True
for base, names, sheet, layout in SETS:
    for n in names:
        F = np.asarray(Image.open(f'{base}/out/{n}.png').convert('RGB')); r = {}
        blocks = F.reshape(480, 2, 640, 2, 3); uni = (blocks == blocks[:, :1, :, :1]).all(axis=(1, 3, 4))
        r['non_uniform_2x2_blocks'] = int((~uni).sum()); nat = F[::2, ::2]
        r['native_matches_saved'] = bool((nat == np.asarray(Image.open(f'{base}/raw/native_{n}.png').convert('RGB'))).all())
        L = np.load(f'{base}/raw/layers_{n}.npz'); so = L['solid']
        r['solid_alpha_values'] = sorted(np.unique(so[..., 3]).tolist()); r['semi_alpha_values'] = sorted(np.unique(L['semi_a']).tolist())
        m = so[..., 3] == 255; inner, ring = edges(m)
        exp_in = rgb555(so[..., :3].astype(np.float32)); exp_out = rgb555(L['under'])
        r['overlay_edge_px'] = int(inner.sum()); r['edge_px_not_pure_overlay'] = int((nat[inner] != exp_in[inner]).any(-1).sum())
        r['ring_px'] = int(ring.sum()); r['ring_px_not_pure_underlay'] = int((nat[ring] != exp_out[ring]).any(-1).sum())
        src = {tuple(c) for c in so[..., :3][inner]}
        r['edge_unique_colours'] = len({tuple(c) for c in nat[inner]}); r['overlay_source_colours_on_edges'] = len(src)
        allowed = set()
        for c in src:
            for t in BAYER.flatten(): allowed.add(tuple((np.clip(np.floor(np.array(c, np.float32) / 8 + t + .5), 0, 31) * 8.2258).clip(0, 255).astype(np.uint8)))
        r['edge_colours_outside_palette_x_bayer'] = len({tuple(c) for c in nat[inner]} - allowed)
        sm = L['semi_a'] > 0; si, sr = edges(sm)
        r['semi_edge_px'] = int(si.sum()); r['semi_edge_px_not_exact_5050'] = int((nat[si & ~m] != rgb555(L['comp'])[si & ~m]).any(-1).sum())
        bad = r['non_uniform_2x2_blocks'] or not r['native_matches_saved'] or r['edge_px_not_pure_overlay'] or r['ring_px_not_pure_underlay'] \
              or r['edge_colours_outside_palette_x_bayer'] or set(r['solid_alpha_values']) - {0, 255} or set(r['semi_alpha_values']) - {0, 255}
        r['PASS'] = not bad; ok &= r['PASS']; rep[n] = r
    S = np.asarray(Image.open(f'{base}/out/{sheet}').convert('RGB')); lay = json.load(open(f'{base}/raw/{layout}'))
    sb = S.reshape(S.shape[0] // 2, 2, S.shape[1] // 2, 2, 3); su = int((~(sb == sb[:, :1, :, :1]).all(axis=(1, 3, 4))).sum())
    tiles = {n: bool((S[y:y + 960, x:x + 1280] == np.asarray(Image.open(f'{base}/out/{n}.png').convert('RGB'))).all()) for n, (x, y) in lay.items() if n in names}
    rep[sheet] = {'size': list(S.shape[1::-1]), 'non_uniform_2x2_blocks': su, 'tiles_identical_to_final_frames': tiles, 'PASS': su == 0 and all(tiles.values()) and len(tiles) == len(names)}
    ok &= rep[sheet]['PASS']
print(json.dumps(rep, indent=1)); json.dump(rep, open('/workspace/mockups/line_select_cam/raw/verify_b5c.json', 'w'), indent=1)
print('ALL PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
