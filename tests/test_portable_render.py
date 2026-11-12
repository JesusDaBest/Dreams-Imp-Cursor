"""Exercise the packaged native shaders from an arbitrary working directory, without a desktop overlay."""
import json
from pathlib import Path
import runpy
import struct
import sys
import hashlib

runtime=Path(sys.argv[1]).resolve()
api=runpy.run_path(str(runtime/'desktop-imp.py'))
imp=api['Imp']('33_clown')
clips=('idle','selectbutton','hoveroverbutton','grab object','pull heavy','drop object','squash','emote happy')
clips=tuple(c for c in clips if c in imp.clips)
count=0
visible=[]
digest=hashlib.sha256()
display_digest=hashlib.sha256()

def particles():
    if count>=len(clips)*12:return None
    clip=clips[count//12]
    return imp.frame(clip,(count%12)/60,.2,-.2,1/60,restarted=count%12==0,
                     edge_distances=(2,900,1900,180) if clip=='squash' else None)

def present(raw,w,h):
    global count
    digest.update(raw)
    pixels=api['decode'](raw,glow=clips[count//12]=='hoveroverbutton').raw[:w*h*4]
    from PIL import Image
    expected=Image.frombytes('RGBa',(w,h),pixels,'raw','BGRa').convert('RGBA').tobytes()
    display_digest.update(expected)
    if 'decode_rgba' in api:
        assert api['decode_rgba'](raw)==expected,'Native RGBA conversion changed display pixels'
    visible.append(sum(v>3 for v in pixels[3::4]))
    if max(pixels[3::4])<20:raise ValueError('Empty portable frame')
    count+=1
    return True

try:
    api['GPU']['render'](particles,present,lambda:(imp.stick,imp.antenna_path),lambda:imp.eye_count,
                         appearance=lambda:imp.motion.body_color)
finally:imp.close()
print(json.dumps({'status':'passed','frames':count,'clips':clips,'minimum_visible_pixels':min(visible),
                  'external_game_dependency':False,'raw_sha256':digest.hexdigest(),'display_sha256':display_digest.hexdigest()}))
