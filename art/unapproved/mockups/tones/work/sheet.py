"""Contact sheets: one row of tones per scene, small plain labels."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from tones import TONES
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
F = ImageFont.truetype('/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf', 22)
for scene, fname in (('overworld', 'tones_overworld_sheet.png'), ('entry', 'tones_entry_sheet.png')):
    names = [n for n in ('sodium', 'mercury', 'txr', 'rain', 'dawn') if os.path.exists(os.path.join(OUT, f'{scene}_{n}.png'))]
    tw, th = 640, 480; cols = 3; rows = (len(names) + cols - 1) // cols; pad = 10; lab = 30
    sh = Image.new('RGB', (cols * tw + (cols + 1) * pad, rows * (th + lab) + (rows + 1) * pad), (16, 16, 20)); d = ImageDraw.Draw(sh)
    for k, n in enumerate(names):
        im = Image.open(os.path.join(OUT, 'work', 'ow' if scene == 'overworld' else 'lane', 'raw', f'native_{scene}_{n}.png'))
        x = pad + (k % cols) * (tw + pad); y = pad + (k // cols) * (th + lab + pad)
        d.text((x, y + 3), TONES[n]['label'], font=F, fill=(220, 220, 225)); sh.paste(im, (x, y + lab))
    sh.save(os.path.join(OUT, fname)); print('wrote', fname, names)
# blend sheet: TXR + Mercury originals and the blends, both scenes
names = [n for n in ('txr', 'mercury', 'blend25', 'blend50', 'blend75') if os.path.exists(os.path.join(OUT, f'overworld_{n}.png'))]
tw, th, pad, lab = 640, 480, 10, 30
sh = Image.new('RGB', (len(names) * tw + (len(names) + 1) * pad, 2 * (th + lab) + 3 * pad), (16, 16, 20)); d = ImageDraw.Draw(sh)
for r, (scene, sub) in enumerate((('overworld', 'ow'), ('entry', 'lane'))):
    for k, n in enumerate(names):
        x = pad + k * (tw + pad); y = pad + r * (th + lab + pad)
        d.text((x, y + 3), TONES[n]['label'], font=F, fill=(220, 220, 225))
        sh.paste(Image.open(os.path.join(OUT, 'work', sub, 'raw', f'native_{scene}_{n}.png')), (x, y + lab))
sh.save(os.path.join(OUT, 'tones_blend_sheet.png')); print('wrote tones_blend_sheet.png', names)
