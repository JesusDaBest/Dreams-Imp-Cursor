"""Recorded Dreams carousel anchor frames, supplied to the original Imp solver."""
import json,math
from pathlib import Path
FRAMES=json.loads((Path(__file__).parent/'reference-state/carousel-frames.json').read_text(encoding='utf-8'))['frames']
CAMERA=json.loads((Path(__file__).parent/'reference-state/carousel-projection.json').read_text(encoding='utf-8'))
HERO_FRAME=tuple(CAMERA['hero_frame'])

def project(frame, point):
    """Original local-to-world transform followed by the captured view matrix."""
    x,y,z,w=frame[4:]
    rotation=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),
              (2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),
              (2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
    world=[frame[j]+frame[3]*sum(rotation[j][k]*point[k] for k in range(3)) for j in range(3)]+[1.]
    matrix=CAMERA['view_projection']
    clip=[sum(world[j]*matrix[j*4+k] for j in range(4)) for k in range(4)]
    return 960*(1+clip[0]/clip[3]),540*(1-clip[1]/clip[3])

def crop_projection(frame, side):
    """Crop the native perspective; the crop changes no Imp geometry or proportions."""
    centre=project(frame,(0.,.5,0.))
    left,top=centre[0]-side/2,centre[1]-side/2
    origin=CAMERA['projection']
    out=[]
    for j in range(4):
        x,y,z,w=origin[j*4:j*4+4]
        out.extend((1920/side*x+((1920-2*left)/side-1)*w,
                    -1080/side*y+((1080-2*top)/side-1)*w,z,w))
    return tuple(out),centre

def projective_matrix(frame):
    x,y,z,w=frame[4:];s=frame[3]
    columns=((s*(1-2*(y*y+z*z)),s*2*(x*y+z*w),s*2*(x*z-y*w),0),
             (s*2*(x*y-z*w),s*(1-2*(x*x+z*z)),s*2*(y*z+x*w),0),
             (s*2*(x*z+y*w),s*2*(y*z-x*w),s*(1-2*(x*x+y*y)),0),
             (*frame[:3],1))
    camera=CAMERA['view_projection']
    return tuple(sum(column[j]*camera[j*4+k] for j in range(4)) for column in columns for k in range(4))

def anchor_frame(slot, *, item_index=None):
    # Interpolate adjacent captured layout transforms, preserving unit rotation.
    i=max(0,min(len(FRAMES)-2,math.floor(slot)));t=slot-i
    a,b=FRAMES[i],FRAMES[i+1]
    position=[x+(y-x)*t for x,y in zip(a[:4],b[:4])]
    # Scrolling changes an item's horizontal location, not which captured
    # staggered row height belongs to it. Keep the native per-item Y value.
    if item_index is not None:position[1]=FRAMES[item_index % len(FRAMES)][1]
    qt=max(0,min(1,t));q=[x+(y-x)*qt for x,y in zip(a[4:],b[4:])]
    n=math.sqrt(sum(v*v for v in q))
    return (*position,*(v/n for v in q))
