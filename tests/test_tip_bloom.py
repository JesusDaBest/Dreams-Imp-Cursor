"""Original tip draws and bloom isolation, without taking over the desktop."""
import ctypes as C
import json
from pathlib import Path
import runpy
import struct

RUNTIME=Path(__file__).resolve().parents[1]/'runtime'
api=runpy.run_path(str(RUNTIME/'desktop-imp.py'))
w,h=api['WIDTH'],api['HEIGHT']
blank=bytes(w*h*8)
body=bytearray(blank)
for y in range(h//2,h//2+15):
    for x in range(w//2,w//2+15):
        struct.pack_into('<4e',body,8*(y*w+x),.98,0,0,1)
body=bytes(body)
assert api['decode'](body,glow=True,tip=blank).raw==api['decode'](body).raw

imp=api['Imp']('H21_Pag_Clown')
index=0
tip=None
coverage=[]
halo_pixels=[]

def enabled():return index<24 or index>=40

def particles():
    if index>=64:return None
    return imp.frame('hoveroverbutton',index/120,0,0,looping=True)

def receive_tip(raw):
    global tip
    tip=raw

def present(raw,width,height):
    global index
    assert (tip is not None)==enabled(),f'Stale hover bloom at frame {index}'
    base=api['decode'](raw).raw[:w*h*4]
    result=api['decode'](raw,glow=True,tip=tip).raw[:w*h*4]
    if tip is None:
        assert result==base
    else:
        assert imp.tip_count==2
        all_covered=sum(a>0 for _,_,_,a in struct.iter_unpack('<4e',raw))
        tip_covered=sum(a>0 for _,_,_,a in struct.iter_unpack('<4e',tip))
        assert 0<tip_covered<all_covered/2,(tip_covered,all_covered)
        coverage.append((tip_covered,all_covered))
        halo_pixels.append(sum(result[p+3]>base[p+3] for p in range(0,len(base),4)))
        # Brightening an unrelated body patch must not generate another halo.
        halo=api['decode'](blank,glow=True,tip=tip).raw[:w*h*4]
        mixed=api['decode'](body,glow=True,tip=tip).raw[:w*h*4]
        for p in range(w*h):
            if body[p*8:p*8+8]==b'\0'*8:
                assert halo[p*4:p*4+4]==mixed[p*4:p*4+4]
    index+=1
    return True

try:
    api['GPU']['render'](particles,present,lambda:(imp.stick,imp.antenna_path),lambda:imp.eye_count,
        appearance=lambda:imp.motion.body_color,tip_count=lambda:imp.tip_count if enabled() else 0,
        present_tip=receive_tip)
finally:imp.close()
assert index==64 and max(halo_pixels)>0
print(json.dumps({'frames':index,'hover_frames':len(coverage),'tip_max_pixels':max(x[0] for x in coverage),
    'whole_imp_min_pixels':min(x[1] for x in coverage),'halo_pixels_max':max(halo_pixels),
    'bright_body_creates_no_bloom':True,'glow_off_matches_base':True}))
