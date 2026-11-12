"""Live cursor-size keys; preserve all other saved preferences."""
import json
import os
import time
from app_paths import write_json, DEFAULT_CURSOR_SIZE


class CursorResize:
    def __init__(self, path):
        self.path = path
        self.direction = 0
        self.next_repeat = 0.

    def update(self, now, enabled, up, down):
        direction = int(bool(up)) - int(bool(down)) if enabled else 0
        if not direction:
            self.direction = 0
            return False
        first = direction != self.direction
        if not first and now < self.next_repeat:
            return False
        self.direction = direction
        self.next_repeat = now + (.3 if first else .08)
        try:
            settings = json.loads(self.path.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError):
            return False
        old = float(settings.get('cursor_size', DEFAULT_CURSOR_SIZE))
        size = round(max(.5, min(2., old + direction * .02)), 2)
        if size == old:
            return False
        settings['cursor_size'] = size
        write_json(self.path, settings)
        return True


class DpadResize:
    def __init__(self):
        os.environ['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = '1'
        os.environ['SDL_GAMECONTROLLER_ALLOW_BACKGROUND_EVENTS'] = '1'
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
        import pygame
        from pygame._sdl2 import controller
        self.pygame, self.api = pygame, controller
        pygame.display.init()
        pygame.joystick.init()
        controller.init()
        self.pad = None
        self.joystick = None
        self.next_scan = 0.

    def poll(self):
        try:
            return self._poll()
        except self.pygame.error:
            for device in (self.pad, self.joystick):
                if device:
                    try:device.quit()
                    except self.pygame.error:pass
            self.pad = self.joystick = None
            self.next_scan = time.monotonic() + 1.
            return False, False

    def _poll(self):
        pg = self.pygame
        pg.event.pump()
        now = time.monotonic()
        if self.pad is not None and not self.pad.attached():
            self.pad.quit()
            self.pad = None
        if self.joystick is not None and not self.joystick.get_init():
            self.joystick = None
        if self.pad is None and self.joystick is None and now >= self.next_scan:
            self.next_scan = now + 1.
            for index in range(pg.joystick.get_count()):
                if self.api.is_controller(index):
                    self.pad = self.api.Controller(index)
                    break
                stick = pg.joystick.Joystick(index)
                if stick.get_numhats():
                    self.joystick = stick
                    break
                stick.quit()
        if self.pad:
            return (self.pad.get_button(pg.CONTROLLER_BUTTON_DPAD_UP),
                    self.pad.get_button(pg.CONTROLLER_BUTTON_DPAD_DOWN))
        if self.joystick:
            vertical = self.joystick.get_hat(0)[1]
            return vertical > 0, vertical < 0
        return False, False

    def close(self):
        if self.pad:self.pad.quit()
        if self.joystick:self.joystick.quit()
        self.api.quit()
        self.pygame.joystick.quit()
        self.pygame.display.quit()
