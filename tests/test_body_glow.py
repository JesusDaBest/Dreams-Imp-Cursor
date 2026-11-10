"""Compare the captured and non-emissive native Imp draws offscreen."""
import hashlib
import json
from pathlib import Path
import runpy
import struct
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
api = runpy.run_path(str(ROOT/'runtime/desktop-imp.py'))
gpu = api['GPU']['render']
settings = gpu.__globals__
fixed_view = settings['cursor_view']
captured = (ROOT/'runtime/reference-state/eye-pass-2/stage-0-buffer1.bin').read_bytes()[:208]
corrected = fixed_view(captured)
assert corrected[:32] == captured[:32] and corrected[40:156] == captured[40:156]
assert corrected[160:188] == captured[160:188]
assert corrected[192:] == captured[192:]
assert captured[48:156] == bytes(108)
assert struct.unpack_from('<f', corrected, 156)[0] == 0
assert struct.unpack_from('<2f', corrected, 32) == (1,1)
assert struct.unpack_from('<f', captured, 188)[0] == 1.5
assert struct.unpack_from('<f', corrected, 188)[0] == 0


def render(character, correction):
    settings['cursor_view'] = fixed_view if correction else bytearray
    imp = api['Imp'](character)
    index, result, records = 0, None, hashlib.sha256()

    def particles():
        if index == 24:
            return None
        data = imp.frame('idle', index/120, 0, 0, looping=True)
        records.update(data)
        return data

    def present(raw, w, h):
        nonlocal index, result
        result = raw
        index += 1
        return True

    try:
        gpu(particles, present, lambda:(imp.stick,imp.antenna_path),
            lambda:imp.eye_count, appearance=lambda:imp.motion.body_color)
    finally:
        imp.close()
        settings['cursor_view'] = fixed_view
    return result, records.hexdigest()


def rgba(raw):
    result = bytearray(api['decode'](raw).raw[:api['WIDTH']*api['HEIGHT']*4])
    for p in range(0, len(result), 4):
        b,g,r,a = result[p:p+4]
        result[p:p+4] = bytes((min(255,round(r*255/a)),min(255,round(g*255/a)),
                              min(255,round(b*255/a)),a)) if a else bytes(4)
    return Image.frombytes('RGBA',(api['WIDTH'],api['HEIGHT']),bytes(result))


report = []
sheet = Image.new('RGB',(720,350),'#211433')
draw = ImageDraw.Draw(sheet)
for i, character in enumerate(('00_default','H21_Pag_Clown')):
    before, old_records = render(character, False)
    after, new_records = render(character, True)
    assert old_records == new_records, 'The appearance/motion particle stream changed'
    old = list(struct.iter_unpack('<4e', before))
    new = list(struct.iter_unpack('<4e', after))
    assert all(a[3] == b[3] for a,b in zip(old,new)), 'Fur/face coverage changed'
    assert sum(a[0] > b[0]+.001 for a,b in zip(old,new)) > 100, 'Body emission not removed'
    for j, data in enumerate((before,after)):
        x = i*360+j*176
        draw.text((x+12,15),character,fill='#ecdfff')
        draw.text((x+12,34),'Before' if j==0 else 'Body glow off',fill='#ccb7e2')
        sheet.paste(rgba(data),(x,64),rgba(data))
    report.append({'character':character,'frames':48,'same_particles':True,
                   'same_coverage':True,'emission_removed':True})
sheet.save(ROOT/'tests/body-glow-comparison.png')
(ROOT/'tests/body-glow-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
