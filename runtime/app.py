"""Portable Windows appearance picker for the original Dreams Imp renderer."""
import ctypes as C
from ctypes import wintypes as W
import json
import os
import re
import runpy
import subprocess
import sys
import time
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from app_paths import ROOT, STATE, READY, ERROR, write_json
from space_preview import space_image
from picker_controls import GROUPS, pill, category_panel
from gallery_client import GalleryClient

TITLE = 'Dreams Imp'
VERSION = '1.0.6'
BG, PANEL, FG, MUTED, ACCENT = '#170f26', '#291a40', '#f4edff', '#bfafd2', '#d8b3ff'

def named_handle(name):
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.OpenMutexW.argtypes = (W.DWORD, W.BOOL, W.LPCWSTR)
    kernel.OpenMutexW.restype = W.HANDLE
    handle = kernel.OpenMutexW(0x100000, False, name)
    if handle:
        kernel.CloseHandle.argtypes = (W.HANDLE,)
        kernel.CloseHandle(handle)
    return bool(handle)

def display_name(item):
    ident = item['id']
    known = {'00_default': 'Original Imp', '000_alpha': 'Alpha', '000_beta': 'Beta',
             'MM_dreamqueen': 'Dream Queen', 'MM_earlyaccess': 'Early Access',
             'MM_IMP': 'Media Molecule', 'MM_impygold': 'Golden Impy',
             'MM_impysilver': 'Silver Impy', 'H21_Pag_Clown': 'Halloween Clown',
             'zzz_delete': 'Internal preset: delete', 'zzz_temp': 'Internal preset: temp'}
    if ident in known:
        return known[ident]
    name = re.sub(r'^(?:\d+|AD|H20|H21|Impys21|MM)_', '', ident)
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name).replace('_', ' ')
    return name.title()

def category(ident):
    if ident.startswith('zzz_'): return 'Internal presets'
    if ident.startswith('AD_'): return "Art’s Dream"
    if ident.startswith(('H20_', 'H21_')): return 'Halloween'
    if ident.startswith(('MM_', 'Impys', 'impys')): return 'Special editions'
    return 'Classic Imps'

class App:
    def __init__(self, root):
        self.root, self.worker, self.log = root, None, None
        self.closing = self.changing = False
        self.active_character = None
        self.pending_character = None
        self.ready_seen = False
        self.cards = {}
        self.card_images = {}
        self.card_layout_job = None
        self.press_position = None
        self.pressed_character = None
        self.dragging = False
        self.pressed_control = None
        self.menu_open = False
        self.chrome_items = []
        self.chrome_images = []
        self.control_bounds = []
        self.snap_job = None
        self.image_size = None
        self.preview = None
        self.preview_job = None
        self.preview_failed = False
        self.items = json.loads((ROOT/'characters/catalog.json').read_text(encoding='utf-8'))
        self.by_id = {i['id']: i for i in self.items}
        self.config_path = STATE/'settings.json'
        try:
            self.settings = json.loads(self.config_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.settings = {}
        self.selected = self.settings.get('character', '00_default')
        if self.selected not in self.by_id: self.selected = '00_default'
        self.grid_size=self.settings.get('grid_size',1)
        if self.grid_size not in (1,2,3,4):self.grid_size=1
        root.title(TITLE)
        root.geometry('970x700')
        root.minsize(340, 360)
        root.configure(bg=BG)
        root.protocol('WM_DELETE_WINDOW', self.close)
        try: root.iconbitmap(str(ROOT/'app.ico'))
        except tk.TclError: pass
        self.group = tk.StringVar(value='All Imps')
        self.gallery = tk.Canvas(root,bg=BG,highlightthickness=0,yscrollincrement=1,xscrollincrement=1)
        self.gallery.pack(fill='both',expand=True)
        self.background_item=self.gallery.create_image(0,0,anchor='nw')
        self.background_size=None
        self.gallery.configure(yscrollcommand=self.scroll_changed,xscrollcommand=self.scroll_changed)
        self.gallery.bind('<Configure>',self.resize_cards)
        self.gallery.bind('<MouseWheel>',self.scroll_cards)
        self.gallery.bind('<Shift-MouseWheel>',self.scroll_cards)
        # Windows promotes single-finger touch to these mouse events. Begin
        # scrolling after a small movement; activate an Imp only on a tap.
        self.gallery.bind('<ButtonPress-1>',self.press_gallery)
        self.gallery.bind('<B1-Motion>',self.drag_gallery)
        self.gallery.bind('<ButtonRelease-1>',self.release_gallery)
        self.gallery.tag_bind('imp','<Enter>',lambda _:self.gallery.configure(cursor='hand2'))
        self.gallery.tag_bind('imp','<Leave>',lambda _:self.gallery.configure(cursor=''))
        self.group.trace_add('write',self.refresh)
        self.refresh()
        root.after(200,self.poll)
        self.preview_job=root.after(33,self.poll_previews)

    def refresh(self,*_):
        self.cancel_snap()
        self.menu_open=False
        for card in self.cards.values():self.gallery.delete(card)
        self.cards.clear()
        self.press_position=None
        self.pressed_character=None
        group = self.group.get()
        visible = [i for i in self.items if group=='All Imps' or category(i['id'])==group]
        visible.sort(key=lambda i:(i['id']!='00_default',display_name(i).casefold()))
        for item in visible:
            ident=item['id']
            self.cards[ident]=self.gallery.create_image(0,0,tags='imp')
        self.imp_ids={item:ident for ident,item in self.cards.items()}
        self.layout_cards()
        self.gallery.xview_moveto(0)
        self.gallery.yview_moveto(0)

    def select(self,ident):
        if self.changing or self.closing:return
        self.show(ident)
        self.start()
        if self.grid_size==1:self.snap_to(list(self.cards).index(ident))

    def cycle_grid(self):
        self.cancel_snap()
        self.grid_size=self.grid_size%4+1
        self.settings['grid_size']=self.grid_size
        write_json(self.config_path,self.settings)
        self.menu_open=False
        self.gallery.xview_moveto(0);self.gallery.yview_moveto(0)
        self.layout_cards()

    def resize_cards(self,event):
        if self.card_layout_job:self.root.after_cancel(self.card_layout_job)
        self.card_layout_job=self.root.after(100,self.layout_cards)

    def layout_cards(self):
        self.card_layout_job=None
        self.cancel_snap()
        width,height=max(340,self.gallery.winfo_width()),max(360,self.gallery.winfo_height())
        area_height=height-94
        imp_height=round(min(440,area_height-64) if self.grid_size==1 else max(48,area_height/self.grid_size-24))
        imp_width=round(imp_height*176/256)
        size=(imp_width,imp_height)
        if self.image_size!=size:
            self.card_images.clear();self.image_size=size
            self.empty_image=ImageTk.PhotoImage(Image.new('RGBA',size))
        self.spacing=imp_width+90
        columns=max(1,int((width-24)/(imp_width+28)))
        step=area_height/self.grid_size
        for index,(ident,card) in enumerate(self.cards.items()):
            self.gallery.itemconfigure(card,image=self.card_images.get(ident,self.empty_image))
            if self.grid_size==1:
                self.gallery.coords(card,width/2+index*self.spacing,80+area_height/2)
            else:self.gallery.coords(card,(index%columns+.5)*width/columns,80+step/2+(index//columns)*step)
        rows=(len(self.cards)+columns-1)//columns
        self.content_width=width+max(0,len(self.cards)-1)*self.spacing if self.grid_size==1 else width
        self.gallery.configure(scrollregion=(0,0,self.content_width,height if self.grid_size==1 else max(height,rows*step+94)))
        if width>10 and height>10 and self.background_size!=(width,height):
            self.background=ImageTk.PhotoImage(space_image(width,height))
            self.gallery.itemconfigure(self.background_item,image=self.background)
            self.background_size=(width,height)
        self.draw_controls(width)
        self.scroll_changed()

    def draw_controls(self,width=None):
        width=width or max(340,self.gallery.winfo_width())
        for item,_,_ in self.chrome_items:self.gallery.delete(item)
        self.chrome_items=[];self.chrome_images=[];self.control_bounds=[]
        category_width=min(284,width-112)
        left=(width-category_width-94)/2
        self.add_control(pill(category_width,56,self.group.get(),expanded=self.menu_open),left,14,('category',None))
        self.add_control(pill(84,56,grid=self.grid_size),left+category_width+10,14,('grid',None))
        if self.menu_open:
            panel=category_panel(category_width,self.group.get())
            self.add_control(panel,left,76,None)
            for index,label in enumerate(GROUPS):
                self.control_bounds.append(((left+8,84+index*46,left+category_width-8,126+index*46),('group',label)))
        self.scroll_changed()

    def add_control(self,image,x,y,action):
        photo=ImageTk.PhotoImage(image);self.chrome_images.append(photo)
        item=self.gallery.create_image(0,0,image=photo,anchor='nw',tags='control')
        self.chrome_items.append((item,x,y))
        if action:self.control_bounds.append(((x,y,x+image.width,y+image.height),action))

    def control_at(self,x,y):
        for (left,top,right,bottom),action in reversed(self.control_bounds):
            if left<=x<=right and top<=y<=bottom:return action
        return None

    def activate_control(self,action):
        kind,value=action
        if kind=='category':self.menu_open=not self.menu_open;self.draw_controls()
        elif kind=='grid':self.cycle_grid()
        elif kind=='group':self.group.set(value)

    def scroll_changed(self,*_):
        x,y=self.gallery.canvasx(0),self.gallery.canvasy(0)
        self.gallery.coords(self.background_item,x,y)
        for item,px,py in self.chrome_items:self.gallery.coords(item,x+px,y+py)

    def scroll_cards(self,event):
        if event.delta:
            self.cancel_snap()
            if self.grid_size==1:self.snap_to(self.nearest_imp()+(-1 if event.delta>0 else 1))
            else:self.gallery.yview_scroll(-round(event.delta/120*72),'units')
        return 'break'

    def cancel_snap(self):
        if self.snap_job:self.root.after_cancel(self.snap_job);self.snap_job=None

    def nearest_imp(self):
        return round(self.gallery.canvasx(0)/max(1,self.spacing))

    def snap_to(self,index):
        self.cancel_snap()
        if self.grid_size!=1 or not self.cards:return
        index=max(0,min(len(self.cards)-1,index))
        start=self.gallery.canvasx(0);target=index*self.spacing;began=time.monotonic()
        def step():
            self.snap_job=None
            if self.closing:return
            t=min(1,(time.monotonic()-began)/.18)
            value=start+(target-start)*(1-(1-t)**3)
            self.gallery.xview_moveto(value/self.content_width)
            if t<1:self.snap_job=self.root.after(16,step)
        step()

    def imp_at(self,x,y):
        x,y=self.gallery.canvasx(x),self.gallery.canvasy(y)
        for item in reversed(self.gallery.find_overlapping(x,y,x,y)):
            if item in self.imp_ids:return self.imp_ids[item]
        return None

    def press_gallery(self,event):
        self.cancel_snap()
        self.press_position=(event.x,event.y)
        self.pressed_control=self.control_at(event.x,event.y)
        self.pressed_character=None if self.pressed_control else self.imp_at(event.x,event.y)
        if self.menu_open and not self.pressed_control:
            self.menu_open=False;self.draw_controls();self.pressed_character=None
            self.pressed_control=('dismiss',None)
        self.dragging=False
        self.gallery.scan_mark(event.x,event.y)
        return 'break'

    def drag_gallery(self,event):
        if self.press_position is None:return 'break'
        x,y=self.press_position
        if max(abs(event.x-x),abs(event.y-y))>8:self.dragging=True
        if self.dragging and not self.pressed_control:
            if self.grid_size==1:self.gallery.scan_dragto(event.x,y,gain=1)
            else:self.gallery.scan_dragto(x,event.y,gain=1)
        return 'break'

    def release_gallery(self,event):
        if self.press_position is None:return 'break'
        x,y=self.press_position
        is_tap=not self.dragging and max(abs(event.x-x),abs(event.y-y))<=8
        ident=self.pressed_character
        control=self.pressed_control
        self.press_position=self.pressed_character=None
        self.pressed_control=None
        if is_tap and control and self.control_at(event.x,event.y)==control:self.activate_control(control)
        elif is_tap and ident is not None and self.imp_at(event.x,event.y)==ident:
            self.select(ident)
        elif self.dragging and not control and self.grid_size==1:self.snap_to(self.nearest_imp())
        return 'break'

    def show(self,ident):
        self.selected=ident

    def poll_previews(self):
        self.preview_job=None
        if self.closing or self.preview_failed:return
        visible=[];aim={}
        if self.root.winfo_viewable() and self.root.state()!='iconic':
            left,top=self.gallery.canvasx(0),self.gallery.canvasy(0)
            width,height=self.gallery.winfo_width(),self.gallery.winfo_height()
            iw,ih=self.image_size
            mx=self.root.winfo_pointerx()-self.gallery.winfo_rootx()+left
            my=self.root.winfo_pointery()-self.gallery.winfo_rooty()+top
            for ident,item in self.cards.items():
                x,y=self.gallery.coords(item)
                if x+iw/2>left and x-iw/2<left+width and y+ih/2>top+74 and y-ih/2<top+height:
                    visible.append(ident)
                    # Original menu-aim simulation, with restrained picker movement.
                    aim[ident]=(max(-.15,min(.15,(mx-x)/width)),max(-.15,min(.15,(y-my)/height)))
        if visible and self.preview is None:
            try:self.preview=GalleryClient(STATE/'gallery.log')
            except Exception as error:
                self.preview_failed=True
                (STATE/'gallery.log').write_text(traceback.format_exc(),encoding='utf-8')
                messagebox.showerror(TITLE,'The live Imp renderer could not start.\n\n'+str(error)+
                    '\n\nLog: '+str(STATE/'gallery.log'),parent=self.root)
                return
        if self.preview is not None:
            self.preview.request(visible,aim)
            frames,error=self.preview.take()
            for ident in list(self.card_images):
                if ident not in visible:
                    if ident in self.cards:self.gallery.itemconfigure(self.cards[ident],image=self.empty_image)
                    del self.card_images[ident]
            for ident,(width,height,pixels) in frames.items():
                if ident not in visible:continue
                image=Image.frombytes('RGBA',(width,height),pixels).resize(self.image_size,Image.Resampling.LANCZOS)
                if ident in self.card_images:self.card_images[ident].paste(image)
                else:
                    self.card_images[ident]=ImageTk.PhotoImage(image)
                    self.gallery.itemconfigure(self.cards[ident],image=self.card_images[ident])
            if error or not self.preview.process.is_alive():
                self.preview_failed=True
                self.preview.close();self.preview=None
                messagebox.showerror(TITLE,'The live Imp renderer could not continue.\n\n'+
                    (error.strip().splitlines()[-1] if error else 'Renderer process exited.')+
                    '\n\nLog: '+str(STATE/'gallery.log'),parent=self.root)
                return
        self.preview_job=self.root.after(33,self.poll_previews)

    def signal_stop(self):
        return runpy.run_path(str(ROOT/'win-imp-overlay.py'))['stop']()

    def start(self):
        if self.changing or self.closing:return
        if self.worker and self.worker.poll() is None and self.selected==self.active_character:return
        self.changing=True;self.ready_seen=False
        self.pending_character=self.selected
        self.signal_stop()
        self.wait_then_launch(time.monotonic()+10)

    def wait_then_launch(self,deadline):
        if self.closing:return
        if named_handle('Local\\DreamsStandaloneImp.Active'):
            if time.monotonic()<deadline:
                self.root.after(100,lambda:self.wait_then_launch(deadline));return
            self.fail('The previous Imp is still closing. Select the Imp again to retry.');return
        # Reap the previous renderer before replacing its process handle.
        if self.worker and self.worker.poll() is None:
            if time.monotonic()<deadline:
                self.root.after(100,lambda:self.wait_then_launch(deadline));return
            self.fail('The previous Imp is still closing. Select the Imp again to retry.');return
        if self.log:self.log.close()
        self.log=(STATE/'renderer.log').open('w',encoding='utf-8')
        READY.unlink(missing_ok=True);ERROR.unlink(missing_ok=True)
        character=self.pending_character
        try:
            self.worker=subprocess.Popen([sys.executable,str(ROOT/'desktop-imp.py'),'--run',
                '--character',character,'--owner-pid',str(os.getpid())],cwd=ROOT,
                stdout=self.log,stderr=self.log,creationflags=subprocess.CREATE_NO_WINDOW)
            self.active_character=character
            self.settings['character']=character;write_json(self.config_path,self.settings)
        except OSError as error:
            self.fail(str(error));return
        self.changing=False
        self.pending_character=None

    def fail(self,detail):
        self.changing=False;self.active_character=None
        self.pending_character=None
        summary=detail.strip().splitlines()[-1] if detail.strip() else 'The cursor renderer exited unexpectedly.'
        messagebox.showerror(TITLE,summary[:600]+'\n\nLog folder: '+str(STATE),parent=self.root)

    def poll(self):
        if self.closing:return
        if self.worker:
            result=self.worker.poll()
            if result is not None:
                self.worker=None;self.ready_seen=False;self.active_character=None
                if self.log:self.log.close();self.log=None
                if result:
                    detail=ERROR.read_text(encoding='utf-8') if ERROR.exists() else (STATE/'renderer.log').read_text(encoding='utf-8')
                    self.fail(detail[-2500:] or f'Renderer exited with code {result}.')
            elif not self.ready_seen and READY.exists():
                try:
                    ready=json.loads(READY.read_text(encoding='utf-8'))
                    if ready['pid']==self.worker.pid:
                        self.ready_seen=True
                except (ValueError,OSError,KeyError):pass
        self.root.after(200,self.poll)

    def expressions(self):
        subprocess.Popen([sys.executable,str(ROOT/'desktop-imp.py'),'--expressions'],cwd=ROOT,
                         creationflags=subprocess.CREATE_NO_WINDOW)

    def close(self):
        self.closing=True
        self.cancel_snap()
        if getattr(self,'preview_job',None):self.root.after_cancel(self.preview_job)
        if getattr(self,'preview',None):self.preview.close();self.preview=None
        if self.worker and self.worker.poll() is None:
            self.signal_stop()
            try:self.worker.wait(timeout=4)
            except subprocess.TimeoutExpired:
                self.worker.terminate();self.worker.wait(timeout=4)
        if self.log:self.log.close()
        self.root.destroy()

def main():
    C.windll.user32.SetProcessDPIAware()
    kernel=C.WinDLL('kernel32',use_last_error=True)
    kernel.CreateMutexW.argtypes=(C.c_void_p,W.BOOL,W.LPCWSTR);kernel.CreateMutexW.restype=W.HANDLE
    mutex=kernel.CreateMutexW(None,False,'Local\\DreamsImp.Picker')
    if not mutex:raise C.WinError(C.get_last_error())
    if C.get_last_error()==183:
        user=C.WinDLL('user32');user.FindWindowW.argtypes=(W.LPCWSTR,W.LPCWSTR);user.FindWindowW.restype=W.HWND
        hwnd=user.FindWindowW(None,TITLE)
        if hwnd:
            user.ShowWindow.argtypes=(W.HWND,C.c_int);user.SetForegroundWindow.argtypes=(W.HWND,)
            user.ShowWindow(hwnd,9);user.SetForegroundWindow(hwnd)
        return
    try:
        root=tk.Tk();App(root);root.mainloop()
    finally:
        kernel.CloseHandle.argtypes=(W.HANDLE,);kernel.CloseHandle(mutex)

if __name__=='__main__':
    try:main()
    except Exception:
        ERROR.write_text(traceback.format_exc(),encoding='utf-8')
        C.windll.user32.MessageBoxW(None,'Dreams Imp could not open.\n\n'+str(ERROR),TITLE,0x10)
        raise
