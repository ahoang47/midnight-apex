"""Label + downsize the lineup render: python3 finish_lineup.py (after blender -b -P render_lineup.py)"""
import os, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); VEH = os.path.dirname(os.path.dirname(HERE))
CANDS = {'WRX': ['wrx_sti', 'wrx'], 'S2000': ['s2000'], 'BRZ': ['brz']}
def tris(c):
    for d in CANDS[c]:
        p = os.path.join(VEH, d, 'lean', 'tri_count.txt')
        if os.path.exists(p): return int([l for l in open(p) if l.startswith('TOTAL')][0].split()[2])
im = cv2.resize(cv2.imread(os.path.join(HERE, 'lean_lineup_raw.png')), (800, 400), interpolation=cv2.INTER_AREA)
t = 'lean lineup (.glb as Godot imports it): ' + ' | '.join(f'{c} {tris(c):,}' for c in CANDS) + ' tris'
(w, h), _ = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
cv2.rectangle(im, (4, 4), (12 + w, 12 + h + 4), (255, 255, 255), -1)
cv2.putText(im, t, (8, 10 + h), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 20, 20), 1, cv2.LINE_AA)
cv2.imwrite(os.path.join(HERE, 'lean_lineup_800.jpg'), im, [cv2.IMWRITE_JPEG_QUALITY, 92]); print(t)
