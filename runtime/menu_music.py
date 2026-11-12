"""Stream the user's selected local track while the picker is open."""
from pathlib import Path
import pygame
from app_paths import STATE,write_json
_active=False
_focused=None
_track=None

def start(settings):
    global _active,_focused,_track
    path = settings.get('menu_music')
    if not path:
        return
    path = Path(path)
    if not path.is_file():
        return
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
