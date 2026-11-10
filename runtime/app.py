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
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from app_paths import ROOT, STATE, READY, ERROR, write_json
from space_preview import space_image

TITLE = 'Dreams Imp'
VERSION = '1.0.5'
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
        self.items = json.loads((ROOT/'characters/catalog.json').read_text(encoding='utf-8'))
        self.by_id = {i['id']: i for i in self.items}
        self.config_path = STATE/'settings.json'
        try:
            self.settings = json.loads(self.config_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.settings = {}
        self.selected = self.settings.get('character', '00_default')
        if self.selected not in self.by_id: self.selected = '00_default'
        root.title(TITLE)
        root.geometry('970x700')
        root.minsize(340, 360)
        root.configure(bg=BG)
        root.protocol('WM_DELETE_WINDOW', self.close)
        try: root.iconbitmap(str(ROOT/'app.ico'))
        except tk.TclError: pass
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 11), background=BG, foreground=FG)
        style.configure('TCombobox', fieldbackground=PANEL, foreground=FG, padding=8)
        style.map('TCombobox', fieldbackground=[('readonly',PANEL)], foreground=[('readonly',FG)])
        head = tk.Frame(root,bg=BG)
        head.pack(fill='x',padx=18,pady=(14,10))
        self.group = tk.StringVar(value='All Imps')
        groups = ['All Imps','Classic Imps','Halloween',"Art’s Dream",'Special editions','Internal presets']
        ttk.Combobox(head,textvariable=self.group,values=groups,state='readonly').pack(fill='x')
        self.gallery = tk.Canvas(root,bg=BG,highlightthickness=0,yscrollincrement=1)
        self.gallery.pack(fill='both',expand=True)
        self.background_item=self.gallery.create_image(0,0,anchor='nw')
        self.background_size=None
        self.gallery.configure(yscrollcommand=self.scroll_changed)
        self.gallery.bind('<Configure>',self.resize_cards)
        self.gallery.bind('<MouseWheel>',self.scroll_cards)
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

    def refresh(self,*_):
        for card in self.cards.values():self.gallery.delete(card)
        self.cards.clear()
        self.press_position=None
        self.pressed_character=None
        group = self.group.get()
        visible = [i for i in self.items if group=='All Imps' or category(i['id'])==group]
        visible.sort(key=lambda i:(i['id']!='00_default',display_name(i).casefold()))
        for item in visible:
            ident=item['id']
            if ident not in self.card_images:
                with Image.open(ROOT/'thumbnails'/(ident+'.png')) as image:
                    artwork=image.convert('RGBA')
                    artwork.thumbnail((110,160),Image.Resampling.LANCZOS)
                    self.card_images[ident]=ImageTk.PhotoImage(artwork)
            self.cards[ident]=self.gallery.create_image(0,0,image=self.card_images[ident],tags='imp')
        self.imp_ids={item:ident for ident,item in self.cards.items()}
        self.layout_cards()
        self.gallery.yview_moveto(0)

    def select(self,ident):
        if self.changing or self.closing:return
        self.show(ident)
        self.start()

    def resize_cards(self,event):
        if self.card_layout_job:self.root.after_cancel(self.card_layout_job)
        self.card_layout_job=self.root.after(100,self.layout_cards)

    def layout_cards(self):
        self.card_layout_job=None
        width,height=self.gallery.winfo_width(),self.gallery.winfo_height()
        columns=max(1,width//150)
        for index,card in enumerate(self.cards.values()):
            self.gallery.coords(card,(index%columns+.5)*width/columns,100+(index//columns)*184)
        rows=(len(self.cards)+columns-1)//columns
        self.gallery.configure(scrollregion=(0,0,width,max(height,rows*184+32)))
        if width>10 and height>10 and self.background_size!=(width,height):
            self.background=ImageTk.PhotoImage(space_image(width,height))
            self.gallery.itemconfigure(self.background_item,image=self.background)
            self.background_size=(width,height)
        self.scroll_changed()

    def scroll_changed(self,*_):
        self.gallery.coords(self.background_item,0,self.gallery.canvasy(0))

    def scroll_cards(self,event):
        if event.delta:self.gallery.yview_scroll(-round(event.delta/120*72),'units')
        return 'break'

    def imp_at(self,x,y):
        x,y=self.gallery.canvasx(x),self.gallery.canvasy(y)
        for item in reversed(self.gallery.find_overlapping(x,y,x,y)):
            if item in self.imp_ids:return self.imp_ids[item]
        return None

    def press_gallery(self,event):
        self.press_position=(event.x,event.y)
        self.pressed_character=self.imp_at(event.x,event.y)
        self.dragging=False
        self.gallery.scan_mark(event.x,event.y)
        return 'break'

    def drag_gallery(self,event):
        if self.press_position is None:return 'break'
        x,y=self.press_position
        if max(abs(event.x-x),abs(event.y-y))>8:self.dragging=True
        if self.dragging:self.gallery.scan_dragto(x,event.y,gain=1)
        return 'break'

    def release_gallery(self,event):
        if self.press_position is None:return 'break'
        x,y=self.press_position
        is_tap=not self.dragging and max(abs(event.x-x),abs(event.y-y))<=8
        ident=self.pressed_character
        self.press_position=self.pressed_character=None
        if is_tap and ident is not None and self.imp_at(event.x,event.y)==ident:
            self.select(ident)
        return 'break'

    def show(self,ident):
        self.selected=ident

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
            self.fail('The previous Imp is still closing. Click its card to retry.');return
        # Reap the previous renderer before replacing its process handle.
        if self.worker and self.worker.poll() is None:
            if time.monotonic()<deadline:
                self.root.after(100,lambda:self.wait_then_launch(deadline));return
            self.fail('The previous Imp is still closing. Click its card to retry.');return
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
