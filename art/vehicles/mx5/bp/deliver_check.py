"""Review sheet: clay 3/4 front + rear (Workbench) over the blueprint checks (silhouette overlay with IoU, side/front/rear
feature-line overlays).  Contains the licensed drawing -> local only (gitignored).  Run from bp/ after deliver.py and
feature_check.py.  Writes renders/mx5_clay_34_bpcheck_800.jpg (+ _full.png)."""
import cv2, numpy as np, json
R = '../out/renders/raw'; iou = json.load(open('../out/bp/iou.json'))
def fitw(a, w): return cv2.resize(a, (w, round(a.shape[0] * w / a.shape[1])), interpolation=cv2.INTER_AREA)
def lab(im, t, s=0.8): cv2.putText(im, t, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, s, (30, 30, 30), 2, cv2.LINE_AA); return im
W = 1600
f34 = lab(fitw(cv2.imread(f'{R}/clay_front34.png')[120:900, 150:1450], W // 2), 'clay 3/4 front')
r34 = lab(fitw(cv2.imread(f'{R}/clay_rear34.png')[120:900, 150:1450], W // 2), 'clay 3/4 rear')
ov = cv2.imread('../renders/mx5_bp_overlay_full.png')
fs = lab(fitw(cv2.imread('../renders/raw/feature_side.png')[300:720, 60:940], W // 2), 'feature lines: side (clay L, drawing mirrored)', 0.6)
ff = cv2.imread('../renders/raw/feature_front.png')[300:720, 230:770]; fr = cv2.imread('../renders/raw/feature_rear.png')[300:720, 230:770]
fb = fitw(np.hstack([ff, fr]), W // 2); fb = lab(fb, 'feature lines: front | rear', 0.6)
h = max(fs.shape[0], fb.shape[0]); row3 = np.full((h, W, 3), 255, np.uint8); row3[:fs.shape[0], :W // 2] = fs; row3[:fb.shape[0], W // 2:] = fb
head = np.full((56, W, 3), 255, np.uint8)
cv2.putText(head, f"MX-5 ND soft top CLAY vs Dimensions.com SVG   IoU side {iou['side']:.3f}  top {iou['top']:.3f}  front {iou['front']:.3f}  rear {iou['rear']:.3f}  (gate .95/.95/.92/.92)",
            (10, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2, cv2.LINE_AA)
sheet = np.vstack([head, np.hstack([f34, r34]), row3, fitw(ov, W)])
cv2.imwrite('../renders/mx5_clay_34_bpcheck_full.png', sheet)
cv2.imwrite('../renders/mx5_clay_34_bpcheck_800.jpg', fitw(sheet, 800), [cv2.IMWRITE_JPEG_QUALITY, 92]); print(sheet.shape)
