"""Scrolling cropped previews must preserve independent temporal histories."""
import ctypes as C
import hashlib
import json, math
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]/'runtime'
import sys
sys.path.insert(0,str(ROOT))
from carousel_native import HERO_FRAME,CAMERA,crop_projection,anchor_frame
api=runpy.run_path(str(ROOT/'desktop-imp.py'))
IDS=('00_default','33_clown','H21_Pag_Clown')
FRAMES=10

def render(ids, multiplex):
    imps=[api['Imp'](ident) for ident in ids]
    out=[[] for _ in ids];step=0;index=0;actor=HERO_FRAME
    active=(C.c_uint8*len(ids))(*([1]*len(ids)))
    def particles():
        nonlocal index,actor
        if step>=FRAMES*len(ids):return None
        index=step%len(ids);frame=step//len(ids)
        actor=anchor_frame(math.sin(frame*.12),item_index=0)
        return imps[index].frame('idle',frame/30,0,0,1/30,looping=True,menu_transform=actor)
    def present(raw,w,h):
        nonlocal step
        out[index].append(hashlib.sha256(raw).hexdigest());step+=1
        return True
    try:
        api['GPU']['render'](particles,present,lambda:(imps[index].stick,imps[index].antenna_path),
                             lambda:imps[index].eye_count,appearance=lambda:imps[index].motion.body_color,
                             gallery=(active,lambda:index),projection=lambda:(*crop_projection(actor,1080*.757)[0],*actor,*CAMERA['camera_frame']))
    finally:
        for imp in imps:imp.close()
    return out

if __name__=='__main__':
    reference=[render([ident],False)[0] for ident in IDS]
    interleaved=render(IDS,True)
    assert reference==interleaved, 'Gallery changed original shader pixels or mixed histories'
    result={'exact_gpu_frame_matches':len(IDS)*FRAMES,'independent_histories':True,'cropped_projection_motion_tested':True}
    Path(__file__).with_name('gallery-projection-report.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
