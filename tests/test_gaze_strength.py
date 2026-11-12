from pathlib import Path
import runpy,sys,ctypes as C,struct,json,math
R=Path(__file__).resolve().parents[1]/'runtime';sys.path.insert(0,str(R));api=runpy.run_path(str(R/'desktop-imp.py'))
def measure(gain,dx,dy):
 api['Reactions'].update.__globals__['DESKTOP_GAZE_GAIN']=gain
 imp=api['Imp']('000_alpha');reaction=api['Reactions'](imp,0.,'idle');jobs=[];prepare=imp.motion.prepare_face
 def record(args):
  prepare(args);job=C.cast(args,C.POINTER(C.c_void_p))[0];jobs.append(struct.unpack('<3f',C.string_at(job+0x100,12)))
 imp.motion.prepare_face=record
 try:
  state=api['MouseState'](960,540,True,32512)
  for n in range(90):reaction.update(state,(n+1)/60)
  reaction.look_target=(960+dx,540-dy)
  reaction.update(state,91/60)
  return jobs[-2:]
 finally:imp.close()
rows=[]
for dx,dy in [(200,0),(-200,0),(0,200),(0,-200),(200,200),(-200,200),(200,-200),(-200,-200)]:
 center=measure(1,0,0);old=measure(1,dx,dy);new=measure(2,dx,dy)
 old_delta=[sum(p[k]-q[k] for p,q in zip(old,center))/2 for k in (0,1)]
 new_delta=[sum(p[k]-q[k] for p,q in zip(new,center))/2 for k in (0,1)]
 for axis,d in enumerate((dx,dy)):
  if d:assert new_delta[axis]*d>0 and abs(new_delta[axis])>abs(old_delta[axis])*1.5,(dx,dy,old_delta,new_delta)
 assert all(math.isfinite(x) for p in new for x in p)
 rows.append({'target_pixels':[dx,dy],'before':old_delta,'after':new_delta})
print(json.dumps(rows))
