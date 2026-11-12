"""Standalone Dreams UI shader worker: latest-state queue, bounded shared frame."""
from pathlib import Path
from functools import lru_cache
import json,mmap,os,secrets,struct,subprocess,threading,time
from native_ui_style import ROOT as ASSETS
from native_ui_pack import NativeUIPack
from native_widget_input import build,f32
ROOT=Path(__file__).resolve().parent
KEYS={'shuffle':'e8da09244bb6','imps':'e6a68fe0c72d','favorites':'977ba979fcbf','back':'9415844be9c0','settings':'8c199a74daa9','previous':'e3fbc8ced301','selected':'e4635763d6837481'}
@lru_cache(maxsize=32)
def layout(mode='imps',width=1920,height=1080):
 """Project the captured unrotated native control frames, using their actual camera."""
 data=(ASSETS/'draw/stage-3-srt.bin').read_bytes();fx,fy=struct.unpack_from('<f',data,16*4)[0],struct.unpack_from('<f',data,21*4)[0];out={}
 for key,ident in KEYS.items():
  if key=='selected':continue
  b=(ASSETS/f'widgets/{ident}.bin').read_bytes();root=struct.unpack_from('<8f',b,0x40);local=struct.unpack_from('<4f',b,0x130)
  assert root[4:]==(0.,0.,0.,1.),'Unsupported native control root rotation'
  world=[root[i]+root[3]*local[i] for i in range(3)];depth=-world[2];assert depth>0
  active=(key=='shuffle' and mode=='surprise') or key==mode
  radius=f32(f32(.2)*f32(1.1)) if active and key in ('shuffle','imps','favorites') else f32(.2) if key in ('shuffle','imps','favorites') else local[3]
  cx=(1+fx*world[0]/depth)*width/2;cy=(1-fy*world[1]/depth)*height/2
  rx=fx*root[3]*radius/depth*width/2;ry=fy*root[3]*radius/depth*height/2
  out[key]=(round(cx-rx),round(cy-ry),round(2*rx),round(2*ry))
 return out

class NativeButtons:
 def __init__(self,log_path,*,validation=False):
  self.log_path=Path(log_path);self.validation=validation;self.condition=threading.Condition();self.latest=None;self.frame=None;self.problem=None;self.stopping=False;self.process=None
  self.thread=threading.Thread(target=self.run,name='Dreams native UI',daemon=True);self.thread.start()
 def request(self,*,hovered=None,mode='imps',previous=False,selected_x=None,selected_button=None):
  with self.condition:self.latest=(hovered,mode,bool(previous),selected_x,selected_button);self.condition.notify()
 def take(self):
  with self.condition:frame=self.frame;self.frame=None;return frame,self.problem
 def close(self):
  with self.condition:self.stopping=True;self.condition.notify()
  self.thread.join(2)
  if self.thread.is_alive() and self.process is not None and self.process.poll() is None:self.process.terminate();self.thread.join(2)
 def run(self):
  vm=None;process=None;shared=None;log=None
  try:
   camera=(ASSETS/'draw/stage-3-srt.bin').read_bytes();marker_fx=struct.unpack_from('<f',camera,16*4)[0]
   widgets={k:bytearray((ASSETS/f'widgets/{v}.bin').read_bytes()) for k,v in KEYS.items()}
   # The three tabs share the native orange face colours. Type 104 is the
   # captured white variant, not a generic selected-state switch.
   orange=bytes(widgets['shuffle'][0x1a0:0x1c0])
   for key in ('shuffle','imps','favorites'):
    widgets[key][0x1a0:0x1c0]=orange
   config=json.loads((ASSETS/'renderer.json').read_text())
   config['capture']=str(ASSETS/config['capture'])
   for field in ('fragment_shader','vertex_shader'):config[field]=str(ASSETS/config[field])
   for section,fields in (('postprocess',('flat','push','vs','fs')),('native_bloom',('down_flat','down_rest_flat','up_flat','down_shader','up_shader'))):
    for field in fields:config[section][field]=str(ASSETS/config[section][field])
   for texture in config['textures']:
    for sub in texture['subresources']:sub['file']=str(ASSETS/sub['file'])
   name='Local\\DreamsImpUI-'+str(os.getpid())+'-'+secrets.token_hex(12)
   shared=mmap.mmap(-1,1920*1080*4,tagname=name);config.update(output_mapping=name,validation=self.validation)
   self.log_path.parent.mkdir(parents=True,exist_ok=True)
   config_path=self.log_path.with_suffix('.renderer.json');config_path.write_text(json.dumps(config))
   log=self.log_path.open('wb');vm=NativeUIPack()
   process=subprocess.Popen([str(ROOT/'imp-ui-renderer.exe'),str(config_path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW);self.process=process
   state={k:[0.,1.] for k in KEYS};phase=0.;last=time.perf_counter();deadline=last;current=None
   while True:
    with self.condition:
     if self.stopping:break
     if self.latest is not None:current=self.latest;self.latest=None
     if current is None:self.condition.wait(.05);continue
    now=time.perf_counter();dt=min(.1,max(0.,now-last));last=now;phase+=dt
    hovered,mode,previous,selected_x,selected_button=current
    while phase>=1/30:
     phase-=1/30
     for name_key,values in state.items():
      target=float(name_key==hovered);old=values[0];direction=1 if target>old else -1 if target<old else 0
      pre=f32(old+f32(direction*f32(.001)));values[0]=min(1,max(0,f32(pre+f32(f32(target-pre)*f32(.2)))))
      active=(name_key=='shuffle' and mode=='surprise') or name_key==mode;base_radius=.22 if active else .2;target_scale=1+.005/base_radius if name_key==hovered else 1.
      values[1]=f32(values[1]+f32(f32(target_scale-values[1])*f32(.2)))
    records=[]
    for key,widget in widgets.items():
     if key=='previous' and not previous:continue
     if key=='selected':
      if selected_x is None:continue
      # Invert the captured native UI projection at the marker's own depth.
      struct.pack_into('<f',widget,0x130,f32((selected_x/960-1)*.5/marker_fx))
     flags=struct.unpack_from('<Q',widget,0x228)[0];selected=key==mode and key in ('shuffle','imps','favorites')
     # Retain Dreams' orange square style; use its material transition for
     # highlighting rather than replacing the button with the white style.
     if key in ('shuffle','imps','favorites'):
      selected=(key=='shuffle' and mode=='surprise') or key==mode
      flags=(flags&~255)|100;struct.pack_into('<Q',widget,0x228,flags)
      radius=f32(f32(.2)*f32(1.1)) if selected else f32(.2);struct.pack_into('<f',widget,0x13c,radius)
     struct.pack_into('<f',widget,0x190,state[key][1]);struct.pack_into('<f',widget,0x1fc,state[key][0])
     # Plus and Back retain their captured colours, including on hover.
     # Their native scale response is independent of this material transition.
     material_hover=0. if key in ('settings','back') else state[key][0]
     if key in ('shuffle','imps','favorites'):
      chosen=key==selected_button
      struct.pack_into('<f',widget,0x208,float(chosen))
      if chosen:material_hover=1.
     records.append(vm.pack(build(widget),material_hover,dt=dt))
    data=struct.pack('<I',len(records))+b''.join(records);process.stdin.write(data);process.stdin.flush()
    ack=process.stdout.read(4)
    if ack!=b'UIOK':raise RuntimeError('Native UI renderer stopped: '+str(process.poll()))
    shared.seek(0);pixels=shared.read(1920*1080*4)
    with self.condition:self.frame=(1920,1080,pixels)
    deadline=max(deadline+1/60,time.perf_counter())
    with self.condition:
     if not self.stopping:self.condition.wait(max(0,deadline-time.perf_counter()))
   process.stdin.write(b'\0'*4);process.stdin.flush();process.stdin.close();process.wait(timeout=2)
   if process.returncode:raise RuntimeError('Native UI renderer exit '+str(process.returncode))
  except BaseException as exc:
   with self.condition:self.problem=str(exc)
  finally:
   if process is not None and process.poll() is None:process.terminate();process.wait(timeout=2)
   if vm is not None:vm.close()
   if shared is not None:shared.close()
   if log is not None:log.close()
