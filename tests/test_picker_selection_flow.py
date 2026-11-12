"""Drive the actual SDL event loop without a GPU or changing the system cursor."""
import os,sys,tempfile,json
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['LOCALAPPDATA']=tempfile.mkdtemp(prefix='imp-selection-test-')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime/python/Lib/site-packages'))
sys.path.insert(0,str(ROOT/'runtime'))
import pygame,runpy,sdl_picker as p
from carousel_native import anchor_frame,crop_projection
class State:
    active=None; launches=0; stops=0; step=0; histories=[]; requests=[]
s=State()
def stop():s.active=None;s.stops+=1
runpy.run_path=lambda *a,**kw:{'stop':stop}
p.app_lifecycle.active_character=lambda:s.active
p.app_lifecycle.exit_requested=lambda:False
p.menu_music.start=lambda settings:None
p.menu_music.set_focus=lambda focus:None
p.menu_music.stop=lambda:None
p.named_handle=lambda name:False
class Window:
    hwnd=None;fullscreen=False
    def toggle_fullscreen(self):self.fullscreen=not self.fullscreen
    def close(self):pass
p.PickerWindow=Window
class Clouds:
    problem=None
    def __init__(self,*a):pass
    def take(self):return None
    def close(self):pass
p.CloudBackground=Clouds
class Hover:
    def publish(self,*a):pass
    def close(self):pass
p.HoverBounds=Hover
class Buttons:
    def __init__(self,*a):pass
    def request(self,**kw):s.histories.append(kw)
    def take(self):return None,None
    def close(self):pass
p.NativeButtons=Buttons
class Alive:
    def is_alive(self):return True
class Gallery:
    process=Alive()
    def __init__(self,*a,**kw):pass
    def request(self,ids,**kw):s.requests.append(list(ids))
    def take(self):return {},None
    def close(self):pass
p.GalleryClient=Gallery
class Worker:
    def poll(self):return None
def launch(args,**kw):
    s.active=args[args.index('--character')+1];s.launches+=1
    return Worker()
p.subprocess.Popen=launch

def events():
    step=s.step;s.step+=1
    buttons=p.native_button_layout(None,1280,720)
    def click(pos):
        return [pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos),pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=pos)]
    if step==0:return []
    if step==1:
        assert s.histories[-1]['mode'] is None and s.histories[-1]['selected_x'] is None
        assert not s.requests,'No carousel or hero renderer before choosing a tab'
        r=pygame.Rect(buttons['imps']);return click(r.center)
    if step in (3,5):
        _,centre=crop_projection(anchor_frame(0,item_index=0),1080*.334)
        return click((round(centre[0]*1280/1920),round(centre[1]*720/1080)))
    if step==4:
        assert s.launches==1 and s.active=='00_default'
        assert s.histories[-1]['selected_x'] is not None,'Selected running cursor needs checkmark'
    if step==6:
        assert s.active is None and s.launches==1,'Click selected Imp restores cursor without relaunch'
        assert s.histories[-1]['selected_x'] is None,'Unselected Imp must not have checkmark'
        return [pygame.event.Event(pygame.QUIT)]
    return []
pygame.event.get=events
p.main()
print('PASS initial blank state; no saved-selection checkmark; choose Imp; checkmark only while active; click again restores cursor')
