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

TITLE = 'Dreams Imp'
VERSION = '1.0.0'
BG, PANEL, FG, MUTED, ACCENT = '#10141f', '#1b2333', '#edf2fc', '#9eabc2', '#87ebcf'

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
        root.minsize(800, 620)
        root.configure(bg=BG)
        root.protocol('WM_DELETE_WINDOW', self.close)
        try: root.iconbitmap(str(ROOT/'app.ico'))
        except tk.TclError: pass
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 11), background=BG, foreground=FG)
        style.configure('TButton', padding=(15, 10), background='#2d3b53', borderwidth=0)
        style.map('TButton', background=[('active', '#3c4e6b'), ('disabled', '#242b38')])
        style.configure('Accent.TButton', background=ACCENT, foreground='#12251e', font=('Segoe UI Semibold',11))
        style.map('Accent.TButton', background=[('active','#b0f5df'),('disabled','#425e58')])
        style.configure('TEntry', fieldbackground=PANEL, foreground=FG, padding=8)
        style.configure('TCombobox', fieldbackground=PANEL, foreground=FG, padding=8)
        style.map('TCombobox', fieldbackground=[('readonly',PANEL)], foreground=[('readonly',FG)])
        head = tk.Frame(root,bg=BG)
        head.pack(fill='x',padx=26,pady=(22,18))
        tk.Label(head,text='Dreams Imp',font=('Segoe UI Semibold',25),fg=FG,bg=BG).pack(anchor='w')
        tk.Label(head,text='Choose your Imp, then click Set as cursor.',font=('Segoe UI',12),
                 fg=MUTED,bg=BG).pack(anchor='w',pady=(5,0))
        body = tk.Frame(root,bg=BG)
        body.pack(fill='both',expand=True,padx=26)
        body.columnconfigure(0,weight=1); body.columnconfigure(1,weight=1)
        body.rowconfigure(2,weight=1)
        self.query = tk.StringVar()
        self.group = tk.StringVar(value='All Imps')
        self.search = ttk.Entry(body,textvariable=self.query)
        self.search.grid(row=0,column=0,sticky='ew',padx=(0,22))
        self.search.insert(0,'')
        groups = ['All Imps','Classic Imps','Halloween',"Art’s Dream",'Special editions','Internal presets']
        ttk.Combobox(body,textvariable=self.group,values=groups,state='readonly').grid(
            row=1,column=0,sticky='ew',pady=(8,10),padx=(0,22))
        listframe = tk.Frame(body,bg=PANEL)
        listframe.grid(row=2,column=0,sticky='nsew',padx=(0,22))
        self.gallery = tk.Canvas(listframe,bg=BG,highlightthickness=0)
        scrollbar = ttk.Scrollbar(listframe,orient='vertical',command=self.gallery.yview)
        self.gallery.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right',fill='y');self.gallery.pack(fill='both',expand=True)
        self.card_frame=tk.Frame(self.gallery,bg=BG)
        self.gallery_window=self.gallery.create_window((0,0),window=self.card_frame,anchor='nw')
        self.gallery.bind('<Configure>',self.resize_cards)
        self.card_frame.bind('<Configure>',lambda _:self.gallery.configure(scrollregion=self.gallery.bbox('all')))
        self.gallery.bind('<MouseWheel>',self.scroll_cards)
        preview = tk.Frame(body,bg=PANEL)
        preview.grid(row=0,column=1,rowspan=3,sticky='nsew')
        self.name = tk.Label(preview,text='',bg=PANEL,fg=FG,font=('Segoe UI Semibold',18),wraplength=350)
        self.name.pack(padx=18,pady=(22,3))
        self.collection = tk.Label(preview,text='',bg=PANEL,fg=ACCENT,font=('Segoe UI',10))
        self.collection.pack()
        self.picture = tk.Label(preview,bg=PANEL)
        self.picture.pack(expand=True,pady=8)
        tk.Label(preview,text='Live native animation · 5× cursor\n50% animation speed · 120 Hz drawing',
                 bg=PANEL,fg=MUTED,font=('Segoe UI',10),justify='center').pack(pady=(0,18))
        self.use_button=ttk.Button(preview,text='Set as cursor',style='Accent.TButton',command=self.start)
        self.use_button.pack(fill='x',padx=24,pady=(0,24))
        self.count = tk.StringVar()
        tk.Label(root,textvariable=self.count,bg=BG,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',padx=26,pady=(8,10))
        self.status = tk.StringVar(value='Choose an Imp above. Your cursor changes only when you click Set as cursor.')
        tk.Label(root,textvariable=self.status,bg=BG,fg=MUTED,font=('Segoe UI',10),wraplength=900,
                 justify='left').pack(fill='x',padx=26,pady=(0,18),anchor='w')
        self.query.trace_add('write',self.refresh)
        self.group.trace_add('write',self.refresh)
        self.refresh();self.show(self.selected)
        root.after(200,self.poll)

    def refresh(self,*_):
        for card in self.cards.values():card.destroy()
        self.cards.clear()
        q = self.query.get().casefold().strip(); group = self.group.get()
        visible = [i for i in self.items if (group=='All Imps' or category(i['id'])==group)
                   and (q in display_name(i).casefold() or q in i['id'].casefold())]
        visible.sort(key=lambda i:(i['id']!='00_default',display_name(i).casefold()))
        for item in visible:
            ident=item['id']
            if ident not in self.card_images:
                with Image.open(ROOT/'thumbnails'/(ident+'.png')) as image:
                    self.card_images[ident]=ImageTk.PhotoImage(image.resize((110,160),Image.Resampling.LANCZOS))
            card=tk.Button(self.card_frame,text=display_name(item),image=self.card_images[ident],compound='top',
                command=lambda ident=ident:self.select(ident),bg=PANEL,fg=FG,activebackground='#304f61',
                activeforeground=FG,font=('Segoe UI',10),wraplength=118,relief='flat',borderwidth=0,
                highlightthickness=2,highlightbackground=PANEL,highlightcolor=ACCENT,padx=6,pady=8,
                cursor='hand2',takefocus=True)
            card.bind('<MouseWheel>',self.scroll_cards)
            self.cards[ident]=card
        self.count.set(f'{len(visible)} shown · {len(self.items)} game presets, including 2 internal presets')
        self.layout_cards()
        self.highlight_selected()
        self.gallery.yview_moveto(0)

    def select(self,ident):
        self.show(ident)

    def highlight_selected(self):
        for ident,card in self.cards.items():
            card.configure(highlightbackground=ACCENT if ident==self.selected else PANEL,
                           bg='#263c49' if ident==self.selected else PANEL)

    def resize_cards(self,event):
        self.gallery.itemconfigure(self.gallery_window,width=event.width)
        if self.card_layout_job:self.root.after_cancel(self.card_layout_job)
        self.card_layout_job=self.root.after(100,self.layout_cards)

    def layout_cards(self):
        self.card_layout_job=None
        columns=max(1,self.gallery.winfo_width()//142)
        for column in range(max(columns,self.card_frame.grid_size()[0])):
            self.card_frame.columnconfigure(column,weight=1 if column<columns else 0)
        for index,card in enumerate(self.cards.values()):
            card.grid(row=index//columns,column=index%columns,sticky='nsew',padx=4,pady=4)

    def scroll_cards(self,event):
        if event.delta:self.gallery.yview_scroll(-int(event.delta/120 or (1 if event.delta>0 else -1)),'units')
        return 'break'

    def show(self,ident):
        self.selected=ident
        self.highlight_selected()
        self.name.configure(text=display_name(self.by_id[ident]))
        self.collection.configure(text=category(ident))
        with Image.open(ROOT/'thumbnails'/(ident+'.png')) as image:
            self.image=ImageTk.PhotoImage(image.resize((220,320),Image.Resampling.LANCZOS))
        self.picture.configure(image=self.image)

    def signal_stop(self):
        return runpy.run_path(str(ROOT/'win-imp-overlay.py'))['stop']()

    def start(self):
        if self.changing or self.closing:return
        if self.worker and self.worker.poll() is None and self.selected==self.active_character:return
        self.changing=True;self.ready_seen=False
        self.pending_character=self.selected
        self.use_button.configure(state='disabled')
        self.status.set('Starting '+display_name(self.by_id[self.pending_character])+'…')
        self.signal_stop()
        self.wait_then_launch(time.monotonic()+10)

    def wait_then_launch(self,deadline):
        if self.closing:return
        if named_handle('Local\\DreamsStandaloneImp.Active'):
            if time.monotonic()<deadline:
                self.root.after(100,lambda:self.wait_then_launch(deadline));return
            self.changing=False
            self.use_button.configure(state='normal')
            self.status.set('The previous Imp is still closing. Click Set as cursor to retry.');return
        # Reap the previous renderer before replacing its process handle.
        if self.worker and self.worker.poll() is None:
            if time.monotonic()<deadline:
                self.root.after(100,lambda:self.wait_then_launch(deadline));return
            self.changing=False
            self.use_button.configure(state='normal')
            self.status.set('The previous Imp is still closing. Click Set as cursor to retry.');return
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
        self.use_button.configure(state='normal')

    def fail(self,detail):
        self.changing=False;self.active_character=None
        self.pending_character=None
        self.use_button.configure(state='normal')
        self.status.set('The Imp could not start. Details are saved in '+str(STATE))
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
                elif not self.changing:self.status.set('Stopped. Your Windows cursor is restored.')
            elif not self.ready_seen and READY.exists():
                try:
                    ready=json.loads(READY.read_text(encoding='utf-8'))
                    if ready['pid']==self.worker.pid:
                        self.ready_seen=True
                        self.status.set(display_name(self.by_id[ready['character']])+' is your cursor. Minimize this window to keep it; close it to quit.')
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
