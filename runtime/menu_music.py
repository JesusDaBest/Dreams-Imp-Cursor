"""Stream the user's selected local track while the picker is open."""
from pathlib import Path
import pygame
from app_paths import ROOT,STATE,write_json
_active=False
_focused=None
_track=None

def start(settings):
    global _active,_focused,_track
    path = Path(settings.get('menu_music') or ROOT/'music/menu.mp3')
    if not path.is_file():
        path = ROOT/'music/menu.mp3'
    if not path.is_file():return
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.play(loops=-1)
        _active=True
        _focused=None
        _track=str(path)
        set_focus(pygame.key.get_focused())
    except pygame.error as error:
        write_json(STATE/'menu-music.json',dict(track=str(path),playing=False,error=str(error)))

def choose(settings,save):
    """Choose a local track without changing the cursor or carousel selection."""
    import tkinter as tk
    from tkinter import filedialog
    dialog=tk.Tk()
    dialog.withdraw()
    dialog.attributes('-topmost',True)
    try:
        path=filedialog.askopenfilename(parent=dialog,title='Choose menu music',
            filetypes=[('Audio files','*.mp3 *.ogg *.wav *.flac'),('All files','*.*')])
    finally:
        dialog.destroy()
    if path:
        settings['menu_music']=path
        save()
        start(settings)

def set_focus(focused):
    global _focused
    focused=bool(focused)
    if not _active or focused==_focused:
        return
    if focused:
        pygame.mixer.music.unpause()
    else:
        pygame.mixer.music.pause()
    _focused=focused
    write_json(STATE/'menu-music.json',dict(track=_track,loop=True,focused=focused,
        paused=not focused,playing=focused and pygame.mixer.music.get_busy()))

def stop():
    global _active,_focused
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    _active=False
    _focused=None
