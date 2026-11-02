"""Label + downsize the 4-car lineup: python3 lineup/finish_lineup_gr.py (after render_lineup_gr.py)"""
import os, re, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); VEH = next(p for p in (os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')), '/workspace/midnight-apex/art/vehicles') if os.path.isdir(os.path.join(p, 'lean_common')) and os.path.isdir(os.path.join(p, 'wrx_sti')))
def tris(p): return int(re.search(r'TOTAL\D*(\d+)', open(p).read()).group(1))
T = {'WRX': tris(f'{VEH}/wrx_sti/lean/tri_count.txt'), 'S2000': tris(f'{VEH}/s2000/lean/tri_count.txt'), 'BRZ': tris(f'{VEH}/brz/lean/tri_count.txt'),
     'GR Corolla': tris(os.path.join(HERE, '..', 'detail', 'tri_count.txt'))}
im = cv2.resize(cv2.imread(os.path.join(HERE, 'lineup_gr_raw.png')), (800, 400), interpolation=cv2.INTER_AREA)
t = 'lineup (.glb as Godot imports it): ' + ' | '.join(f'{c} {n:,}' for c, n in T.items()) + ' tris'
(w, h), _ = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
cv2.rectangle(im, (4, 4), (12 + w, 12 + h + 4), (255, 255, 255), -1)
cv2.putText(im, t, (8, 10 + h), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (20, 20, 20), 1, cv2.LINE_AA)
os.makedirs(os.path.join(HERE, '..', 'detail', 'renders'), exist_ok=True)
cv2.imwrite(os.path.join(HERE, '..', 'detail', 'renders', 'gr_corolla_detail_lineup_800.jpg'), im, [cv2.IMWRITE_JPEG_QUALITY, 92]); print(t)
