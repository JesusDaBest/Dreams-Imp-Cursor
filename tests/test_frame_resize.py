import sys,ctypes as C,random,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'runtime';sys.path.insert(0,str(root))
from PIL import Image
from frame_helpers import library
lib=library();rng=random.Random(91218);cases=0
sizes=[(1,1),(1,13),(19,1),(7,11),(24,36),(63,65),(128,256),(512,512)]
outputs=[(1,1),(1,21),(17,1),(7,11),(32,48),(63,65),(361,361),(818,818)]
for sw,sh in sizes:
 raw=rng.randbytes(sw*sh*4)
 for dw,dh in outputs:
  expected=Image.frombytes('RGBa',(sw,sh),raw,'raw','BGRa').resize((dw,dh),Image.Resampling.BILINEAR).tobytes()
  out=C.create_string_buffer(dw*dh*4+32);C.memset(out,0x51,len(out))
  assert lib.imp_resize_rgba(raw,sw,sh,out,dw,dh)==1
  actual=out.raw[:dw*dh*4]
  if actual!=expected:
   at=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
   raise AssertionError(((sw,sh),(dw,dh),at,actual[at],expected[at]))
  assert out.raw[dw*dh*4:]==b'Q'*32
  cases+=1
print('Exact random BGRA resize cases:',cases)
