"""Rasterize the Dimensions.com SVG; colour each Illustrator layer differently (layer = line class proposal)."""
import xml.etree.ElementTree as ET, cairosvg, sys, re
ET.register_namespace('', 'http://www.w3.org/2000/svg')
COL = {'N-DIMENSIONS': '#bbbbbb', '_x32_D_x24_AG-DIAGRAM': '#00aa00', '_x32_D_x24_AG-DETAILS': '#0066ff',
       '_x32_D_x24_AG-TRANSPORT': '#000000', '_x32_D_x24_AG-OUTLINE': '#ff0000'}
def render(out, scale=3, only=None, colour=True):
    t = ET.parse('gr_dimensions.svg'); r = t.getroot()
    for g in r.iter('{http://www.w3.org/2000/svg}g'):
        i = g.get('id', '')
        if i in COL:
            for e in g.iter():
                for a in ('stroke', 'fill'):
                    if e.get(a) and e.get(a) not in ('none', '#fff'):
                        e.set(a, COL[i] if colour else '#000')
                if only and i not in only and e.tag.split('}')[1] != 'g': e.set('visibility', 'hidden')
    cairosvg.svg2png(bytestring=ET.tostring(r), write_to=out, scale=scale)
if __name__ == '__main__':
    render('work_layers.png', 2)
