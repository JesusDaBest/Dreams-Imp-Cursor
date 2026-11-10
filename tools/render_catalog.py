"""Render the actual selectable appearances and exercise their native particle paths."""
import ctypes as C
import json
import runpy
import struct
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT/'runtime'
api = runpy.run_path(str(RUNTIME/'desktop-imp.py'))
catalog = json.loads((RUNTIME/'characters/catalog.json').read_text(encoding='utf-8'))
if len(sys.argv)>1:
    catalog = [c for c in catalog if c['id'] in sys.argv[1:]]
imp = api['Imp']()
out = RUNTIME/'thumbnails'
out.mkdir(exist_ok=True)
index = 0
per_variant = 24
summary = []

def particles():
    global index
    which, frame = divmod(index, per_variant)
    if which >= len(catalog):
        return None
    entry = catalog[which]
    if frame == 0:
        print(entry['id'], flush=True)
        imp.motion.set_character((RUNTIME/'characters'/entry['file']).read_bytes(),
                                 (RUNTIME/'characters'/(entry['id']+'.bindings')).read_bytes())
        imp.groups.clear()
        imp.last_clip = None
        imp.rest_face = imp.motion.eye_parameters(imp.motion.sample(imp.clips['idle'],0),())
    data = imp.frame('idle', frame/120, 0, 0, looping=True)
    if frame == per_variant-1:
        summary.append({'id':entry['id'],'particles':len(data)//136,'face_particles':imp.eye_count})
    return data

def present(raw,w,h):
    global index
    which, frame = divmod(index, per_variant)
    if frame == per_variant-1:
        pixels = api['decode'](raw)
        rgba = bytearray(pixels.raw[:w*h*4])
        # Layered windows consumes premultiplied BGRA; PNG needs straight RGBA.
        for p in range(0,len(rgba),4):
            b,g,r,a = rgba[p:p+4]
            rgba[p:p+4] = bytes((min(255,round(r*255/a)),min(255,round(g*255/a)),min(255,round(b*255/a)),a)) if a else b'\0\0\0\0'
        Image.frombytes('RGBA',(w,h),bytes(rgba)).save(out/(catalog[which]['id']+'.png'))
    index += 1
    return True

try:
    api['GPU']['render'](particles,present,lambda:(imp.stick,imp.antenna_path),lambda:imp.eye_count,
                         appearance=lambda:imp.motion.body_color)
finally:
    imp.close()
(ROOT/'tests/catalog-render.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('PASS',len(summary),'appearances',index,'GPU frames')
