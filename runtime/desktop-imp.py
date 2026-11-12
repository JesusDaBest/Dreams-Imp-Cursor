"""Drive the standalone Dreams Imp render loop with desktop input."""
import argparse
import ctypes as C
import json
from PIL import Image
from functools import lru_cache
import math
import os
from pathlib import Path
import runpy
import random
import struct
import threading
import time

ROOT = Path(__file__).resolve().parent
APP_PATHS = runpy.run_path(str(ROOT/'app_paths.py'))
ENGINE = runpy.run_path(str(ROOT/'native-imp-motion.py'))
GPU = runpy.run_path(str(ROOT/'live-imp-render.py'))
WINDOWS = runpy.run_path(str(ROOT/'win-imp-overlay.py'))
MouseState = WINDOWS['MouseState']
NATIVE, BODY = ENGINE['NATIVE'], ENGINE['BODY']
WIDTH, HEIGHT = GPU['WIDTH'], GPU['HEIGHT']
PROJECTION_SIZE = 320
# Physical-size baseline: the previous 160-sample projection displayed at
# 1.5x (the user's requested new 1x). More render samples must not enlarge it.
CURSOR_PROJECTION_SIZE = 160 * 1.5
CURSOR_BASE_SCALE = CURSOR_PROJECTION_SIZE / PROJECTION_SIZE
VERTICAL_PADDING = (HEIGHT - PROJECTION_SIZE) // 2
IDENTITY = (0.0, 0.0, 0.0, 1.0)
REQUEST = APP_PATHS['REQUEST']
CLIP_RATE = 30
PLAYBACK_SPEED = .5
# Original evaluator 0x75b2582..0x75b2592 converts seconds to 30 Hz
# frames (float at 0x77a6a1c). Morph-speed preference is independent.
ANIMATION_RATE = CLIP_RATE
PRESENT_STEP = 1 / 120
SOLVER_STEP = ENGINE['SOLVER_STEP']
EYE_BLEND_CHANNELS = ((0x10, 1), (0x14, 4), (0x18, 2), (0x1c, 5),
                      (0x20, 29), (0x24, 30), (0x28, 3), (0x2c, 6))
IDLE_EXPRESSIONS = (
    'idle bored', 'idle bored look', 'idle dizzy', 'idle frown', 'idle gasp',
    'idle gasp 2', 'idle happy', 'idle roll eye', 'idle sneeze', 'idle stretch',
    'idle stretch 2', 'idle wake up', 'idle wink', 'idle wink2', 'idle yawn',
    'idle 1', 'idle 3', 'idle 7', 'zzz',
    'old emote cry', 'oldemote happy', 'oldemote laugh',
)
VARIANTS = {
    'selectbutton': ('selectbutton', 'ui click', 'ui click 3', 'ui click 4',
                     'ui thing select', 'ui button 1', 'ui button 2', 'ui button 3',
                     'ui button 3A', 'ui button 4'),
    'selectbutton 2': ('selectbutton 2', 'selectbutton 21', 'selectbutton 22'),
    'hoveroverbutton': ('hoveroverbutton', 'ui menu hover', 'hoveroverdream'),
    'menu open': ('menu open', 'menu open 2', 'ui menu open', 'ui menu open 2',
                  'ui menu open 4', 'ui menu open 6', 'ui menuopen ',
                  'ui menuopen 2', 'ui menuopen 3', 'ui menuopen 4', 'ui menuopen 5'),
    'ui menu hold 2': ('ui menu hold 2', 'menu press', 'menu sub'),
    'ui move': ('ui move', 'ui move 3', 'ui move 4'),
    'ui move 2': ('ui move 2', 'ui move 5', 'ui move 6'),
    'ui menu hold': ('ui menu hold', 'ui hold', 'ui hold 3', 'ui hold 4'),
    'level load': ('level load', 'level load 3', 'level load 4', 'level load 5', 'level load OLD'),
    'can_possess': ('can_possess', 'can_possess 02'),
    'default_blink': ('default_blink',),
}
ROLE_CLIPS = {
    32513: 'look down hold',    # Text selection
    32514: 'level load',        # Busy
    32515: 'sculpt mode',       # Precision selection
    32516: 'look up hold',      # Alternate selection
    32642: 'sculpt resize',     # NW/SE resize
    32643: 'sculpt resize 1',   # NE/SW resize
    32644: 'sculpt resize 2',   # Horizontal resize
    32645: 'sculpt resize 3',   # Vertical resize
    32646: 'move object',       # Move
    32648: 'idle frown',        # Unavailable
    32649: 'hoveroverbutton',   # Link selection
    32650: 'level load 2',      # Working in background
    32651: 'curious pointer',   # Help
    32671: 'pointer light',     # Location selection
    32672: 'can_possess',      # Person selection
}

def clip_phase(header, seconds, looping):
    frame = max(0.0, seconds * ANIMATION_RATE)
    last, loop_start, loop_end = header[2:5]
    if not looping:
        return min(frame, last), False
    end = (loop_end or last) + 1
    if frame < end:
        return frame, False
    return loop_start + (frame - end) % (end - loop_start), True


class Imp:
    def __init__(self, character=None):
        _, faces = BODY['default_mesh']()
        guest = NATIVE['verified_bytes'](NATIVE['GUEST'], NATIVE['EXPECTED_TEXT'])
        self.motion = ENGINE['Motion'](guest, faces)
        if character:
            from character_store import catalog,load
            entry = next((entry for entry in catalog() if entry['id'] == character), None)
            if entry is None:
                raise ValueError('Unknown Imp appearance')
            data,bindings=load(entry)
            self.motion.set_character(data,bindings)
        parse = runpy.run_path(str(ROOT/'read-imp-animation.py'))['parse_bank']
        bank = NATIVE['verified_bytes'](NATIVE['ASSET'], NATIVE['EXPECTED_BANK'])
        self.clips = {clip['name']: clip for clip in parse(bank)}
        character_bytes=self.motion.character_data
        # Dreams 0x75f7f9d-0x75f8007 indexes four ordered appearance slots.
        # Keep repeated and empty entries in that table; they are not a shuffle bag.
        self.character_emote_slots=tuple(
            character_bytes[o:o+16].split(b'\0',1)[0].decode('ascii')
            for o in range(0x41e0,0x4220,16)) if character_bytes else ('emote happy','emote sad','emote angry','emote confused')
        self.character_emotes=tuple(dict.fromkeys(name for name in self.character_emote_slots if name in self.clips))
        self.channels = {name: {track[0]&255 for track in clip['descriptors']}
                         for name, clip in self.clips.items()}
        self.groups = {}
        self.hotspot = (WIDTH//2, 8 + VERTICAL_PADDING)
        self.stick = b''
        self.eye_count = 0
        self.last_clip = None
        self.last_phase = 0.0
        self.last_parameters = None
        self.fade_track = None
        self.fade_in = 0.0
        self.fade_out = 0.0
        self.fade_from = None
        rest = self.motion.sample(self.clips['idle'], 0)
        self.rest_face = self.motion.eye_parameters(rest, ())
        self.rest_squash, = struct.unpack_from('<f', rest, 0x20f0)
        if self.motion.character_data is not None:
            self.rest_squash, = struct.unpack_from('<f', self.motion.character_data, 0x90)
        self.rest_tip = struct.unpack_from('<2f', rest, 0x20e8)
        # Dreams submits two flecks at the pointer, using the same vertex
        # shader and particle layout as the face. Keep their native records.
        self.tip_records = (ROOT/'reference-state'/'tip-particles.bin').read_bytes()
        if len(self.tip_records) != 2 * 136:
            raise ValueError('Incomplete original Imp tip flecks')
        self.tip_origin = struct.unpack_from('<3f', self.tip_records, 36)
        self.tip_bases = tuple(struct.unpack_from('<9f', self.tip_records, offset)
                               for offset in (0, 136))
        self.tip_base_radii = tuple(math.hypot(*basis[:3]) for basis in self.tip_bases)
        self.tip_color = struct.unpack_from('<3f', self.tip_records, 108)
        self.player = 2
        palette = (ROOT/'reference-state'/'player-tip-colors.bin').read_bytes()
        if len(palette) != 16:
            raise ValueError('Incomplete Dreams player colour table')
        self.player_tip_colors = tuple(tuple(v / 255 for v in palette[i:i+3]) for i in range(0,16,4))
        self.tip_radius, self.tip_core_radius = self.tip_base_radii
        self.tip_seed = 42
        self.tip_step = 0
        self.sparks = None
        self.hover_interactable = False

    def enable_sparks(self):
        from native_sparks import Sparks
        guest=NATIVE['verified_bytes'](NATIVE['GUEST'],NATIVE['EXPECTED_TEXT'])
        self.sparks=Sparks(self.motion,guest)
        self.sparks.emission_init(guest)

    def close(self):
        self.motion.close()

    def _previous(self, name, data):
        old = self.groups.get(name, b'')
        self.groups[name] = data
        if len(old) != len(data):
            old = data
        adjusted = bytearray(data)
        for start in range(0, len(data), 136):
            adjusted[start+48:start+96] = old[start:start+48]
        return adjusted

    def _blend_parameters(self, face, squash, tip, channels, time):
        incoming = min(time / self.fade_in, 1.0) if self.fade_in else 1.0
        outgoing = max(1.0 - time / self.fade_out, 0.0) if self.fade_out else 0.0
        old_squash, old_face, old_tip = self.rest_squash, self.rest_face, self.rest_tip
        if outgoing and self.fade_from is not None:
            old_squash, old_face, old_tip = self.fade_from
            if self.fade_track is not None:
                clip, start_frame = self.fade_track
                frame = min(clip['header'][2], start_frame + time * ANIMATION_RATE)
                pose = self.motion.sample(clip, frame)
                old_squash, = struct.unpack_from('<f', pose, 0x20f0)
                old_face = self.motion.eye_parameters(pose, self.channels[clip['name']])
                old_tip = struct.unpack_from('<2f', pose, 0x20e8)
        base = self.rest_squash + (old_squash - self.rest_squash) * outgoing
        squash = base + (squash - base) * incoming if 18 in channels else base
        for offset, channel in EYE_BLEND_CHANNELS:
            rest, = struct.unpack_from('<f', self.rest_face, offset)
            old, = struct.unpack_from('<f', old_face, offset)
            base = rest + (old - rest) * outgoing
            if channel in channels:
                value, = struct.unpack_from('<f', face, offset)
                base += (value - base) * incoming
            struct.pack_into('<f', face, offset, base)
        blended_tip = []
        for channel, rest, old, value in zip((16, 17), self.rest_tip, old_tip, tip):
            base = rest + (old - rest) * outgoing
            blended_tip.append(base + (value - base) * incoming if channel in channels else base)
        return squash, tuple(blended_tip)

    def _tip_particles(self, point, controls):
        size, brightness = controls
        # Dreams 0x75adac1 and 0x75aedab. Standard Imp mode at the native solver rate.
        goal = 0.24 * size
        while self.tip_step < self.motion.step_count:
            self.tip_step += 1
            self.tip_radius += (goal - self.tip_radius) * min(SOLVER_STEP * 10, 1)
            if self.tip_radius > 0.001:
                # Dreams 0x75af005. The bright core changes size on each native update.
                self.tip_seed = (self.tip_seed * 0x2e90edd + 0xe908fc1) & 0x3fffffff
                upper = max(0.0, self.tip_radius - 0.025)
                lower = max(0.0, upper - 0.015)
                fraction = (self.tip_seed >> 16) / 16383
                self.tip_core_radius = lower + (upper - lower) * fraction
        if self.tip_radius <= 0.001:
            return b''
        tip = bytearray(self.tip_records)
        color = self.player_tip_colors[self.player - 1]
        struct.pack_into('<3f', tip, 108, *color)
        radii = self.tip_radius, self.tip_core_radius
        for offset, basis, radius, original in zip((0, 136), self.tip_bases,
                                                   radii, self.tip_base_radii):
            scale = radius / original
            struct.pack_into('<9f', tip, offset, *(value * scale for value in basis))
            position = struct.unpack_from('<3f', tip, offset + 36)
            struct.pack_into('<3f', tip, offset + 36, *(
                value + target - origin
                for value, target, origin in zip(position, point, self.tip_origin)
            ))
        # Dreams 0x75ae353. Only the core receives the animated HDR multiplier.
        energy = 50 + 950 * min(brightness * brightness, 1.0)
        struct.pack_into('<3f', tip, 136 + 108, *(value * energy for value in color))
        return tip

    def frame(self, clip_name, animation_time, aim_x, aim_y, dt=PRESENT_STEP, *, looping=False,
              restarted=False, edge_distances=None, menu_translation=None, menu_transform=None, gaze_offset=None):
        clip = self.clips[clip_name]
        header = clip['header']
        phase, wrapped = clip_phase(header, animation_time, looping)
        pose = self.motion.sample(clip, phase, looping=looping, wrapped=wrapped)
        squash, = struct.unpack_from('<f', pose, 0x20f0)
        tip_controls = struct.unpack_from('<2f', pose, 0x20e8)
        channels = self.channels[clip_name]
        if 18 not in channels:
            squash = self.rest_squash
        face = self.motion.eye_parameters(pose, channels)
        if self.last_clip != clip_name or restarted:
            previous = self.clips.get(self.last_clip)
            self.fade_in = header[0] / ANIMATION_RATE
            self.fade_out = previous['header'][1] / ANIMATION_RATE if previous else 0.0
            # An interrupted blend has no single outgoing clip to resample.
            self.fade_track = ((previous, self.last_phase + dt * ANIMATION_RATE)
                               if self.fade_out and self.fade_from is None else None)
            self.fade_from = self.last_parameters if self.fade_out else None
        if animation_time < self.fade_in or animation_time < self.fade_out:
            squash, tip_controls = self._blend_parameters(face, squash, tip_controls,
                                                          channels, animation_time)
        else:
            self.fade_from = self.fade_track = None
        self.last_clip = clip_name
        self.last_phase = phase
        self.last_parameters = squash, face, tip_controls
        bounds = None
        if edge_distances is not None:
            left, bottom, right, top = (pixels / (PROJECTION_SIZE * 0.245)
                                        for pixels in edge_distances)
            tip = self.motion.tip_height
            bounds = -left, tip - bottom, right, tip + top
        points = self.motion.advance(aim_x, aim_y, dt, squash=squash,
                                     speed=PLAYBACK_SPEED, bounds=bounds, menu_translation=menu_translation,
                                     menu_transform=menu_transform)
        body = self.motion.body_particles(points)
        self.motion.eye_target = (points[165][0] + gaze_offset[0],
                                 points[165][1] + gaze_offset[1],
                                 ENGINE['AIM_DEPTH'] / self.motion.rest_frame[3]) if gaze_offset is not None else None
        eyes = self.motion.eyes(pose, points, parameters=face)
        mouth = self.motion.mouth_particles(pose, channels)
        decorations = self.motion.stroke_particles(pose, 0x2190,
                            color=struct.unpack_from('<3f', pose, 0x2174))
        decorations += self.motion.character_strokes()
        antenna_mesh, antenna_flecks, self.antenna_path = self.motion.antenna_particles(points)
        tip_x, tip_y, _ = points[165]
        self.hotspot = (round(WIDTH/2 + PROJECTION_SIZE*0.245*tip_x),
                        round(PROJECTION_SIZE*(0.66-0.245*tip_y)) + VERTICAL_PADDING)
        self.stick = self._previous('antenna-mesh', antenna_mesh)
        tip = self._tip_particles(points[165], tip_controls)
        if self.sparks is not None:
            tip+=self.sparks.advance(points[165],tip_controls,
                                    self.player_tip_colors[self.player-1],
                                    self.hover_interactable,dt,self.player)
        self.tip_count = len(tip)//136
        self.eye_count = (len(eyes)+len(mouth)+len(decorations)+len(tip))//136
        return (body + self._previous('antenna-flecks', antenna_flecks)
                + self._previous('eyes', eyes) + self._previous('mouth', mouth)
                + self._previous('decorations', decorations) + self._previous('tip', tip))


@lru_cache(maxsize=1)
def _renderer():
    return C.CDLL(str(ROOT/'imp-renderer.dll'))


@lru_cache(maxsize=2)
def _cursor_decoder(glow):
    lib = _renderer()
    convert = lib.imp_decode_cursor_bgra if glow else lib.imp_decode_bgra
    convert.argtypes = (C.c_void_p, C.c_void_p, C.c_void_p, C.c_uint, C.c_uint) if glow else (
        C.c_void_p, C.c_void_p, C.c_uint)
    convert.restype = None
    return convert


def decode(raw, *, glow=False, tip=None):
    pixels = C.create_string_buffer(WIDTH * HEIGHT * 4)
    if glow and tip is not None:
        _cursor_decoder(True)(raw, tip, pixels, WIDTH, HEIGHT)
    else:
        _cursor_decoder(False)(raw, pixels, WIDTH * HEIGHT)
    return pixels


class InteractiveHover:
    def __init__(self):
        self.point = None
        self.hit = None
        self.bounds = runpy.run_path(str(ROOT/'hover_bounds.py'))['HoverBounds']()
        self.last_target = None
        self.target_until = 0.0
        self.stop = threading.Event()
        self.probe = _renderer().imp_interactive_at
        self.probe.argtypes = C.c_long, C.c_long, C.POINTER(C.c_long * 4)
        self.probe.restype = C.c_bool
        # Accessibility providers can block. Query them off the rendering thread.
        threading.Thread(target=self._poll, daemon=True).start()

    def _poll(self):
        bounds = (C.c_long * 4)()
        while not self.stop.wait(1 / 30):
            point = self.point
            hit = self.bounds.hit(*point) if point else None
            self.hit = hit or ((time.monotonic(), *bounds) if point and self.probe(*point, C.byref(bounds))
                               else None)

    def at(self, x, y, visible):
        self.point = (x, y) if visible else None
        hit = self.hit
        if not visible or hit is None:
            return False
        sampled, left, top, right, bottom = hit
        return left <= x < right and top <= y < bottom and time.monotonic() - sampled < 0.20

    def target(self, x, y, visible, now=None):
        now = time.monotonic() if now is None else now
        if not visible:
            self.last_target = None
            self.target_until = 0.0
            return None
        active = self.at(x, y, visible)
        hit = self.hit
        if active and hit is not None:
            _, left, top, right, bottom = hit
            self.last_target = ((left+right)/2, (top+bottom)/2)
            self.target_until = now + 1.5
        return self.last_target if now < self.target_until else None


def preview(clip, output, character=None):
    from PIL import Image
    imp = Imp(character)
    index = 0
    frames = []

    def particles():
        return imp.frame(clip, index / CLIP_RATE, 0.0, 0.0, 1 / CLIP_RATE)

    def present(raw, width, height):
        nonlocal index
        index += 1
        pixels = decode(raw, glow=clip in (*VARIANTS['hoveroverbutton'], 'pointer_glow')).raw
        alpha = pixels[3::4]
        if sum(x > 3 for x in alpha) < 400:
            raise ValueError('The rendered Imp is empty')
        if index in (1, 8, 16, 30):
            # Convert the premultiplied overlay pixels to straight-alpha PNG.
            straight = bytearray(pixels)
            for i in range(0, len(straight), 4):
                a = straight[i+3]
                if a:
                    for ch in range(3):
                        straight[i+ch] = min(255, round(255*straight[i+ch]/a))
            frames.append(Image.frombytes('RGBA', (width, height), bytes(straight), 'raw', 'BGRA'))
        return index < 30

    try:
        GPU['render'](particles, present, lambda: (imp.stick, imp.antenna_path), lambda: imp.eye_count)
    finally:
        imp.close()
    sheet = Image.new('RGBA', (WIDTH*len(frames), HEIGHT))
    for i, frame in enumerate(frames):
        sheet.paste(frame, (i*WIDTH, 0))
    sheet.save(output)
    print(f'Rendered {index} complete frames at {WIDTH}×{HEIGHT}: {output}')


class Reactions:
    def __init__(self, imp, now, expression, double_click=(.5, 2, 2),
                 viewport=(0, 0, 1920, 1080)):
        self.imp = imp
        self.fixed = expression
        self.clip = expression or 'idle'
        self.started = now
        self.idle_clock = runpy.run_path(str(ROOT/'native_idle.py'))['NativeIdle']()
        self.next_blink = now + self.idle_clock.blink_delay()
        self.next_emote = now + self.idle_clock.delay()
        self.next_rare_idle = now + self.idle_clock.delay(rare=True)
        self.was_moving = False
        self.last_motion = now
        self.last_update = now - PRESENT_STEP
        self.previous = None
        self.random = random.Random()
        self.emotes = imp.character_emotes
        self.emote_queue = []
        self.variant_index = {}
        self.last_emote = None
        self.poll_after = now
        self.playing_requested = False
        self.press = None
        self.last_click = None
        self.double_click = double_click
        self.viewport = viewport
        self.cursor_scale = 1.0
        self.grabbing = False
        self.pan = None
        self.gesture = None
        self.gesture_clip = False
        self.direction = None
        self.look_target = None
        self.menu_transform = None

    def update(self, state, now):
        prior = self.previous or MouseState(state.x, state.y, False, 0)
        dx, dy = state.x-prior.x, state.y-prior.y
        self.previous = state
        moving = abs(dx)+abs(dy)
        if moving or state.role != prior.role or state.menu_event or any(state[4:14]):
            self.last_motion = now
            self.was_moving = True
        elif self.was_moving:
            self.next_emote = now + self.idle_clock.delay()
            self.was_moving = False
        last_frame = self.imp.clips[self.clip]['header'][2]
        duration = (last_frame + 1) / ANIMATION_RATE
        if self.gesture_clip and last_frame <= 1:
            duration = max(duration, .3)
        done = now-self.started >= duration
        dt = max(.001, min(now-self.last_update, .1))
        self.last_update = now
        clip = None
        gesture_active = False
        if not self.fixed and now >= self.poll_after:
            self.poll_after = now + .2
            try:
                requested = REQUEST.read_text(encoding='utf-8')
                REQUEST.unlink(missing_ok=True)
                if requested in self.imp.clips:
                    clip = requested
                    self.playing_requested = True
            except FileNotFoundError:
                pass
        if self.fixed:
            if done:
                clip = self.fixed
        elif not clip and (not self.playing_requested or done):
            self.playing_requested = False
            # Desktop Alt-drags are not Dreams sculpt/paint/audio-tool events.
            # Tool clips remain available through explicit animation requests.
            clip = self.automatic(now, state, prior, dx, dy, moving, done)
        if clip:
            self.clip, self.started = clip, now
            self.gesture_clip = gesture_active
        left, top, width, height = self.viewport
        aim_x = 2 * (state.x - left) / max(1, width - 1) - 1
        aim_y = 1 - 2 * (state.y - top) / max(1, height - 1)
        distances = tuple(d / self.cursor_scale for d in
                    (state.x - left + .5, top + height - state.y - .5,
                     left + width - state.x - .5, state.y - top + .5))
        looping = (not self.gesture_clip and not self.fixed and not self.playing_requested and
                   ((state.primary and self.grabbing and self.clip in VARIANTS['ui menu hold']) or
                    (state.secondary and self.pan is None and self.clip in VARIANTS['ui menu hold 2']) or
                    (self.clip.startswith('look ') and self.clip.endswith(' hold') and
                     now - self.last_motion < .15)))
        return self.imp.frame(self.clip, now-self.started, aim_x, aim_y, dt, looping=looping,
                              restarted=clip is not None,
                              menu_transform=self.menu_transform,
                              edge_distances=distances if min(distances) < PROJECTION_SIZE else None,
                              gaze_offset=((self.look_target[0]-state.x)/(PROJECTION_SIZE*.245*self.cursor_scale),
                                           (state.y-self.look_target[1])/(PROJECTION_SIZE*.245*self.cursor_scale))
                                          if self.look_target is not None else None)

    def next_expression(self):
        if not self.emote_queue:
            self.emote_queue = list(self.emotes)
            self.random.shuffle(self.emote_queue)
            if len(self.emote_queue) > 1 and self.emote_queue[-1] == self.last_emote:
                self.emote_queue[0], self.emote_queue[-1] = self.emote_queue[-1], self.emote_queue[0]
        self.last_emote = self.emote_queue.pop()
        return self.last_emote

    def primary_click(self, now, x, y):
        if self.last_click:
            previous, px, py = self.last_click
            delay, width, height = self.double_click
            if now-previous <= delay and abs(x-px) <= width and abs(y-py) <= height:
                self.last_click = None
                return self.next_variant('selectbutton 2')
        self.last_click = now, x, y
        return self.next_variant('selectbutton')

    def next_variant(self, action):
        # Native clip identity is an event choice, not a round-robin playlist.
        # Do not substitute unrelated UI/tool/legacy clips on repeated actions.
        return action if isinstance(action, str) and action in self.imp.clips else None

    def appearance_emote(self, selector):
        # Exact four-slot selection from Dreams' native update routine.
        index = (selector >> 4) - 1
        if not 0 <= index < 4:
            return None
        clip = self.imp.character_emote_slots[index]
        return clip if clip in self.imp.clips else None


    def automatic(self, now, state, prior, dx, dy, moving, done):
        x, y, _, role = state[:4]
        role_clip = ROLE_CLIPS.get(role)
        if state.primary and not prior.primary:
            self.press = now, x, y
            self.grabbing = False
            if 32642 <= role <= 32646:
                self.last_click = None
                return role_clip
            return self.primary_click(now, x, y)
        if prior.primary and not state.primary:
            self.press = None
            if self.grabbing:
                self.grabbing = False
                return 'drop object'
        if state.back:
            return 'ui undo'
        if state.forward:
            return 'ui redo'
        if state.wheel or state.wheel_horizontal:
            if abs(state.wheel) >= abs(state.wheel_horizontal):
                if state.ctrl:
                    clip = 'sculpt resize 2' if state.wheel > 0 else 'sculpt resize 3'
                else:
                    clip = 'look up curi' if state.wheel > 0 else 'look down curi'
            else:
                clip = 'look right curi' if state.wheel_horizontal > 0 else 'look left curi'
            return clip if done or self.clip != clip else None
        if state.primary:
            if 32642 <= role <= 32646:
                if self.clip != role_clip:
                    return role_clip
                return None
            if self.press:
                started, start_x, start_y = self.press
                dragged = abs(x-start_x)+abs(y-start_y) > 4
                move_clip = ('pull heavy' if moving >= 22 else
                             'pull light' if moving >= 8 else 'move object')
                modifier = ('ui hold 2' if role == 32513 else
                            'ui shift clone' if state.ctrl and state.shift else
                            'ui clone mode' if state.ctrl else
                            'ui shift hold' if state.shift else None)
                if not self.grabbing and (dragged or now-started >= .18):
                    self.grabbing = True
                    self.last_click = None
                    return modifier or (move_clip if dragged and moving else 'grab object')
                if self.grabbing:
                    if modifier:
                        return modifier if self.clip != modifier else None
                    holding = self.clip in VARIANTS['ui menu hold']
                    if moving and (done or holding or self.clip == 'grab object'):
                        return move_clip
                    if done and not holding:
                        return self.next_variant('ui menu hold')
            return None
        if state.primary_down and not prior.primary:
            return self.primary_click(now, x, y)
        if state.secondary_down or state.secondary and not prior.secondary:
            self.pan = None
            return self.next_variant('menu open')
        if state.middle_down or state.middle and not prior.middle:
            self.pan = None
            return 'ui click 2'
        if state.secondary or state.middle:
            button = 'secondary' if state.secondary else 'middle'
            if moving >= 2 and self.pan != button:
                self.pan = button
                return self.next_variant('ui move 2' if state.secondary else 'ui move')
            if self.pan is None and state.secondary and done and self.clip not in VARIANTS['ui menu hold 2']:
                return self.next_variant('ui menu hold 2')
            return None
        if self.pan:
            self.pan = None
            return 'drop object'
        if state.menu_event < 0:
            return 'menu close'
        if state.menu_event > 0 and (done or self.clip not in VARIANTS['menu open']):
            return self.next_variant('menu open')
        if role_clip:
            role_clips = VARIANTS.get(role_clip, (role_clip,))
            if role != prior.role or done and (self.clip not in role_clips or role in (32514, 32650)):
                return self.next_variant(role_clip)
            return None
        looking = self.clip.startswith('look ')
        can_look = (done or self.clip == 'idle' or looking or self.clip in self.emotes
                    or prior.role in ROLE_CLIPS and role != prior.role)
        # Pointer travel deforms the native spring mesh. Do not turn its
        # largest axis into a four-direction eye-animation selector: that loses
        # diagonal gaze and makes the eyes jump when the larger axis changes.
        if looking and self.clip not in ROLE_CLIPS.values():
            return 'idle'
        if done or self.clip == 'idle' or prior.role in ROLE_CLIPS and role != prior.role:
            if not moving and now >= self.next_rare_idle:
                self.next_rare_idle = now + self.idle_clock.delay(rare=True)
                return self.idle_clock.clip(rare=True)
            if not moving and now >= self.next_emote:
                self.next_emote = now + self.idle_clock.delay()
                return self.idle_clock.clip()
            if now >= self.next_blink:
                self.next_blink = now+self.idle_clock.blink_delay()
                return self.next_variant('default_blink')
            if self.clip != 'idle' or done:
                return 'idle'


def expression_picker():
    import tkinter as tk
    from tkinter import ttk
    parse = runpy.run_path(str(ROOT/'read-imp-animation.py'))['parse_bank']
    bank = NATIVE['verified_bytes'](NATIVE['ASSET'], NATIVE['EXPECTED_BANK'])
    names = sorted({clip['name'] for clip in parse(bank)}, key=str.casefold)
    panel = tk.Tk()
    panel.title('Dreams Imp Expressions')
    panel.geometry('410x450')
    query = tk.StringVar()
    search = ttk.Entry(panel, textvariable=query)
    search.pack(fill='x', padx=10, pady=(10, 5))
    entries = tk.Listbox(panel, exportselection=False)
    entries.pack(fill='both', expand=True, padx=10, pady=4)
    result = tk.StringVar(value=f'{len(names)} original Dreams animations')
    ttk.Label(panel, textvariable=result).pack(pady=4)

    def filter_names(*_):
        entries.delete(0, 'end')
        entries.insert('end', *(n for n in names if query.get().casefold() in n.casefold()))

    def play(*_):
        selection = entries.curselection()
        if selection:
            name = entries.get(selection[0])
            temp = REQUEST.with_name(f'expression-{os.getpid()}.tmp')
            temp.write_text(name, encoding='utf-8')
            temp.replace(REQUEST)
            result.set(f'Playing {name}')

    query.trace_add('write', filter_names)
    filter_names()
    entries.bind('<Double-Button-1>', play)
    entries.bind('<Return>', play)
    ttk.Button(panel, text='Play expression', command=play).pack(pady=(1, 10))
    search.focus_set()
    panel.mainloop()

def desktop(seconds, expression, replace_arrow=False, character=None, owner_pid=None):
    os.environ.setdefault('VK_LOADER_LAYERS_DISABLE', '~implicit~')
    window = WINDOWS['Overlay'](replace_arrow, WIDTH, HEIGHT)
    deadline = None
    hover = None
    imp = None
    index = 0
    state = None
    presented = []
    tip_frame = None
    tray = None
    resize_pad = None
    cursor_scale = 1.0
    next_size_read = 0.0
    try:
        if owner_pid:
            # An unexpected picker exit must not leave a hidden system cursor behind.
            def owner_guard():
                kernel = C.WinDLL('kernel32')
                kernel.OpenProcess.argtypes = (C.c_ulong, C.c_int, C.c_ulong)
                kernel.OpenProcess.restype = C.c_void_p
                kernel.WaitForSingleObject.argtypes = (C.c_void_p, C.c_ulong)
                kernel.CloseHandle.argtypes = (C.c_void_p,)
                handle = kernel.OpenProcess(0x100000, False, owner_pid)
                if handle:
                    kernel.WaitForSingleObject(handle, 0xffffffff)
                    kernel.CloseHandle(handle)
                WINDOWS['stop']()
            threading.Thread(target=owner_guard, daemon=True).start()
        imp = Imp(character)
        imp.enable_sparks()
        if replace_arrow:
            from cursor_tray import CursorTray
            tray = CursorTray(ROOT, WINDOWS['stop'])
        hover = InteractiveHover()
        if expression and expression not in imp.clips:
            raise ValueError(f'Unknown native expression {expression!r}')
        started = time.perf_counter()
        viewport = tuple(window.win.GetSystemMetrics(metric) for metric in (76, 77, 78, 79))
        reaction = Reactions(imp, started, expression, window.double_click, viewport)
        from cursor_resize import CursorResize, DpadResize
        resize_keys = CursorResize(APP_PATHS['STATE']/'settings.json')
        if replace_arrow:
            try:
                resize_settings=json.loads((APP_PATHS['STATE']/'settings.json').read_text(encoding='utf-8-sig'))
            except (OSError,ValueError):resize_settings={}
            if resize_settings.get('dpad_resize_enabled',False):resize_pad = DpadResize()

        def particles():
            nonlocal state, next_size_read
            state = window.state()
            while state is not None and not window.input_available:
                # Leave the GPU idle while Windows withholds desktop input.
                # state() still processes quit/stop events every 100 ms.
                hover.point = None
                if seconds and time.perf_counter()-started >= seconds:
                    return None
                time.sleep(.1)
                state = window.state()
            now = time.perf_counter()
            if state is None or (seconds and now-started >= seconds):
                return None
            if resize_pad:
                up, down = resize_pad.poll()
                if resize_keys.update(now, True, up, down):next_size_read = 0.
            reaction.look_target = hover.target(*state[:3], now=now)
            imp.hover_interactable = hover.at(*state[:3])
            return reaction.update(state, now)

        def present(raw, width, height):
            nonlocal index, deadline, cursor_scale, next_size_read
            pixels = decode(raw, glow=tip_frame is not None, tip=tip_frame)
            if not index and max(pixels.raw[3::4]) < 20:
                raise ValueError('The first cursor frame was empty')
            now=time.perf_counter()
            if now >= next_size_read:
                next_size_read=now+.2
                try:
                    settings=json.loads((APP_PATHS['STATE']/'settings.json').read_text(encoding='utf-8'))
                    # Preserve the established physical size at twice the
                    # internal sample density. Both axes share this one factor.
                    cursor_scale=CURSOR_BASE_SCALE*max(.5,min(2,float(settings.get('cursor_size',APP_PATHS['DEFAULT_CURSOR_SIZE']))))
                    reaction.cursor_scale=cursor_scale
                    imp.player=max(1,min(4,int(settings.get('player',2))))
                except (OSError,ValueError,TypeError):pass
            target=(max(1,round(width*cursor_scale)),max(1,round(height*cursor_scale)))
            window.resize(*target)
            hotspot=tuple(round(v*cursor_scale) for v in imp.hotspot)
            if target!=(width,height):
                resized=Image.frombytes('RGBa',(width,height),pixels.raw,'raw','BGRa').resize(target,Image.Resampling.BILINEAR)
                pixels=C.create_string_buffer(resized.tobytes('raw','BGRa'))
            window.present(pixels, state[:2], hotspot, state[2])
            if not index:
                APP_PATHS['write_json'](APP_PATHS['READY'], {'pid': os.getpid(), 'character': character})
            index += 1
            now = time.perf_counter()
            if seconds:
                presented.append(now)
            deadline = now + PRESENT_STEP if deadline is None else max(now, deadline + PRESENT_STEP)
            remaining = deadline - now
            if remaining > 0:
                time.sleep(remaining)
            return True

        def receive_tip(raw):
            nonlocal tip_frame
            tip_frame = raw

        GPU['render'](particles, present, lambda: (imp.stick, imp.antenna_path), lambda: imp.eye_count,
                      appearance=lambda: imp.motion.body_color,
                      tip_count=lambda: imp.tip_count if hover.at(*state[:3]) else 0,
                      present_tip=receive_tip,
                      responsive_history=lambda: (reaction.clip != 'idle' or
                          reaction.last_update - reaction.last_motion <= .10))
    finally:
        if resize_pad:resize_pad.close()
        if tray:
            tray.close()
        if hover:
            hover.stop.set()
        if imp:
            imp.close()
        window.close()
    if seconds:
        if len(presented) < 2:
            raise ValueError('Cursor test did not present frames')
        elapsed = presented[-1]-presented[0]
        print(f'Windows layer presented {index} frames at {WIDTH}×{HEIGHT}; '
              f'{(index-1)/elapsed:.1f} frames per second after initialization.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preview', type=Path)
    mode.add_argument('--desktop-test', type=float, metavar='SECONDS')
    mode.add_argument('--run', action='store_true')
    mode.add_argument('--watch', nargs=2)
    mode.add_argument('--stop', action='store_true')
    mode.add_argument('--expressions', action='store_true')
    parser.add_argument('--expression')
    parser.add_argument('--character', default='00_default')
    parser.add_argument('--owner-pid', type=int)
    args = parser.parse_args()
    if args.watch:
        runpy.run_path(str(ROOT/'win-imp-overlay.py'))['watch'](int(args.watch[0]), args.watch[1])
    elif args.preview:
        preview(args.expression or 'default_blink2', args.preview, args.character)
    elif args.stop:
        runpy.run_path(str(ROOT/'win-imp-overlay.py'))['stop']()
    elif args.expressions:
        expression_picker()
    else:
        try:
            desktop(args.desktop_test, args.expression, replace_arrow=args.run, character=args.character,
                    owner_pid=args.owner_pid)
        except Exception:
            if args.run:
                import traceback
                APP_PATHS['ERROR'].write_text(traceback.format_exc(), encoding='utf-8')
            raise
