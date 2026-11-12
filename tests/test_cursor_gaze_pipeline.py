from pathlib import Path
import sys,runpy,math,time,random,json,ctypes as C,struct
R=Path(__file__).resolve().parents[1]/'runtime'
sys.path.insert(0,str(R))
a=runpy.run_path(str(R/'desktop-imp.py'))
# The exact existing temporal-history fields, including first/replaced buffers.
f=a['Imp']._previous
class Store:pass
s=Store();s.groups={};rng=random.Random(7);checks=0
for count in (1,2,320,753,2048):
 for frame in range(3):
  data=rng.randbytes(count*136);old=s.groups.get('test',b'')
  if len(old)!=len(data):old=data
  expected=bytearray(data)
  for start in range(0,len(data),136):expected[start+48:start+96]=old[start:start+48]
  assert f(s,'test',data)==expected
  checks+=1
# Direct app hits must work while the external accessibility provider is blocked.
h=a['InteractiveHover'].__new__(a['InteractiveHover'])
class Bounds:
 value=None
 def hit(self,x,y):return self.value
h.bounds=Bounds();h.external_hit=None;h.hit=None;h.last_target=None;h.target_until=0
now=time.monotonic();h.bounds.value=(now,10,20,110,80)
assert h.target(50,50,True,now=now)==(60,50)
h.bounds.value=None
assert h.target(200,200,True,now=now+1.499)==(60,50)
assert h.target(200,200,True,now=now+1.5) is None
h.bounds.value=(time.monotonic(),10,20,110,80)
assert h.target(50,50,True,now=now+3)==(60,50)
assert h.target(50,50,False,now=now+3.1) is None
# Run the real spring solver, native gaze and real eye particle generator.
rows=[]
for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
 imp=a['Imp']('000_alpha');directions=[];jobs=[]
 original=imp.motion.gaze_rotation;prepare=imp.motion.prepare_face
 def gaze(direction):directions.append(direction);return original(direction)
 def record(args):
  prepare(args)
  job=C.cast(args,C.POINTER(C.c_void_p))[0]
  jobs.append(struct.unpack('<3f',C.string_at(job+0x100,12)))
 imp.motion.gaze_rotation=gaze;imp.motion.prepare_face=record
 reaction=a['Reactions'](imp,0.,'idle')
 try:
  for n in range(90):reaction.update(a['MouseState'](960,540,True,32512),(n+1)/60)
  before=jobs[-2:];directions.clear();jobs.clear()
  for n in range(12):reaction.update(a['MouseState'](960+dx*(n+1)*8,540-dy*(n+1)*8,True,32512),(91+n)/60)
  after=jobs[-2:]
  assert len(directions)==24 and imp.motion.eye_target is not None
  delta=[sum(v[k] for v in after)/2-sum(v[k] for v in before)/2 for k in (0,1)]
  if dx:assert dx*delta[0]>0,(dx,dy,delta)
  if dy:assert dy*delta[1]>0,(dx,dy,delta)
  rows.append({'movement':[dx,dy],'native_eye_direction_delta':delta})
  # A distant hovered target must reach the native gaze solver on both axes.
  state=a['MouseState'](960,540,True,32512)
  reaction.look_target=(1160,340)
  reaction.update(state,2.)
  target=imp.motion.eye_target
  assert target[0]>1 and target[1]>3 and all(math.isfinite(v) for v in target)
 finally:imp.close()
print(json.dumps({'exact_history_copy_cases':checks,'app_hover_independent_of_external_probe':True,'hold_until_1_5_seconds':True,'real_native_eye_jobs':rows},indent=2))
