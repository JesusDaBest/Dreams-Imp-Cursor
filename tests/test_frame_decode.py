import ctypes as C,random,struct,time,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'runtime'
a=C.CDLL(str(R/'imp-renderer.dll'));b=C.CDLL(str(R/'imp-frame-helpers.dll'))
old=a.imp_decode_bgra;new=b.imp_decode_bgra
for f in (old,new):f.argtypes=(C.c_void_p,C.c_void_p,C.c_uint);f.restype=None
cases=0;pixels=0;last=None

def check(raw):
 global cases,pixels,last
 n=len(raw)//8;x=C.create_string_buffer(n*4+64);y=C.create_string_buffer(n*4+64)
 x[n*4:]=y[n*4:]=b'\xa5'*64
 old(raw,x,n);new(raw,y,n)
 ex=x.raw[:n*4];ac=y.raw[:n*4]
 if ex!=ac:
  at=next(i for i,(u,v) in enumerate(zip(ex,ac)) if u!=v);p=at//4
  raise AssertionError({'case':cases,'pixel':p,'input':struct.unpack_from('<4e',raw,p*8),'half_bits':struct.unpack_from('<4H',raw,p*8),'old':list(ex[p*4:p*4+4]),'new':list(ac[p*4:p*4+4])})
 assert x[n*4:]==y[n*4:]==b'\xa5'*64
 cases+=1;pixels+=n;last=raw

rng=random.Random(19)
for n in (1,2,3,4,5,7,511,1025,262144):check(rng.randbytes(n*8))
for channel in range(4):
 raw=bytearray(struct.pack('<4e',.2,.1,.1,.5)*65536)
 for value in range(65536):struct.pack_into('<H',raw,value*8+channel*2,value)
 check(bytes(raw))
for _ in range(8):check(rng.randbytes(262144*8))
# Exercise correlated finite HDR values near colour/rounding boundaries.
for _ in range(4):
 raw=bytearray()
 for _ in range(65536):
  raw+=struct.pack('<4e',rng.uniform(-.9,.99),rng.uniform(-.5,.5),rng.uniform(-.5,.5),rng.random())
 check(bytes(raw))
frame=rng.randbytes(512*512*8);output=C.create_string_buffer(512*512*4)
timing={}
for name,f in [('old',old),('new',new)]:
 begin=time.perf_counter()
 for _ in range(80):f(frame,output,512*512)
 timing[name]=(time.perf_counter()-begin)/80*1000
print(json.dumps({'cases':cases,'pixel_comparisons':pixels,'identical':True,'decode_ms':timing}))
