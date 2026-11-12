"""Persistent native Dreams particle draw and temporal resolve."""
import ctypes as C
import os
from pathlib import Path
import runpy
import struct
import time

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 512, 512
SHADERS = ROOT/'shader-inputs'
ORIGINAL = SHADERS
NextParticles = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_uint, C.c_void_p)
StickParticles = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_uint, C.c_void_p, C.c_void_p)
Present = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_uint, C.c_uint, C.c_void_p)
Eyes = C.CFUNCTYPE(C.c_int, C.c_void_p)


class LiveFrames(C.Structure):
    _fields_ = [
        ('shader', C.c_char_p), ('constants', C.c_void_p), ('push', C.c_void_p),
        ('next', NextParticles), ('present', Present), ('user', C.c_void_p),
        ('draw_constants', C.c_void_p), ('light_parameters', C.c_void_p),
        ('stick_shader', C.c_char_p), ('stick_constants', C.c_void_p), ('stick', StickParticles),
        ('eye_shader', C.c_char_p), ('vertex_constants', C.c_void_p),
        ('eye_constants', C.c_void_p), ('eyes', Eyes),
        ('appearance_rgb', C.POINTER(C.c_float)),
        ('bloom_particles', Eyes), ('bloom_present', Present),
    ]

class GalleryFrames(C.Structure):
    _fields_ = [('active', C.POINTER(C.c_uint8)), ('count', C.c_uint), ('index', Eyes),
                ('projection', C.POINTER(C.c_float))]


def render(particles, present, stick_particles=lambda: (b'', b''), eye_count=lambda: 0,
           *, responsive_history=None, appearance=lambda: (1., 1., 1.),
           tip_count=None, present_tip=None, gallery=None, projection=None,pointer_present=False):
    errors = []
    rgb = (C.c_float * 3)()
    matrix = (C.c_float * 32)() if projection is not None else None

    @NextParticles
    def next_frame(destination, capacity, _):
        try:
            data = particles()
            if data is None:
                return 0
            if matrix is not None:matrix[:] = projection()
            rgb[:] = tuple(value * 0.5 for value in appearance())
            if len(data) % 136 or len(data) > capacity * 136 or not data:
                raise ValueError('Invalid particle frame from the native runtime')
            if responsive_history is not None:
                struct.pack_into('<f', constants, 48 * 4, .25 if responsive_history() else resting_history)
            C.memmove(destination, bytes(data), len(data))
            return len(data)//136
        except BaseException as exc:
            errors.append(exc)
            return 0

    @Present
    def frame_ready(pixels, width, height, _):
        try:
            if (width, height) != (WIDTH, HEIGHT):
                raise ValueError(f'Unexpected Imp render surface: {width}x{height}')
            return int(present(pixels if pointer_present else C.string_at(pixels,width*height*8),width,height))
        except BaseException as exc:
            errors.append(exc)
            return 0

    @StickParticles
    def next_stick(destination, capacity, path_buffer, _):
        try:
            data, path_data = stick_particles()
            if len(data) % 136 or len(data) > capacity * 136 or len(path_data) > 4096:
                raise ValueError('Invalid original antenna records')
            if data:
                C.memmove(destination, bytes(data), len(data))
                C.memmove(path_buffer, path_data, len(path_data))
            return len(data)//136
        except BaseException as exc:
            errors.append(exc)
            return -1

    def path(p):
        return os.fsencode(p.resolve())

    @Eyes
    def number_of_eyes(_):
        return eye_count()

    @Eyes
    def number_of_tips(_):
        try:return tip_count()
        except BaseException as exc:
            errors.append(exc)
            return -1

    @Present
    def tip_ready(pixels,width,height,_):
        try:
            present_tip(C.string_at(pixels,width*height*8) if pixels else None)
            return 1
        except BaseException as exc:
            errors.append(exc)
            return 0

    flat = (ORIGINAL/'e0002-flat.bin').read_bytes()
    if len(flat) != 212:
        raise ValueError('Unrecognized resolve constant layout')
    constants = C.create_string_buffer(flat, 256)
    resting_history, = struct.unpack_from('<f', flat, 48 * 4)
    push = C.create_string_buffer((ORIGINAL/'e0002-push-data.bin').read_bytes())
    if len(push) != 129:
        raise ValueError('Unrecognized resolve push constant layout')
    captures = ROOT/'reference-state'/'eye-pass-2'
    eye_draw = ROOT/'reference-state'/'body-pass'
    draw = C.create_string_buffer((captures/'stage-0-srt.bin').read_bytes())
    anatomy = C.create_string_buffer((captures/'stage-0-buffer2.bin').read_bytes()[:200])
    antenna = ROOT/'reference-state'/'antenna-pass'
    stick = C.create_string_buffer((antenna/'stage-3-srt.bin').read_bytes())
    vertex = C.create_string_buffer((captures/'stage-3-srt.bin').read_bytes())
    eye = C.create_string_buffer((eye_draw/'stage-3-srt.bin').read_bytes())
    f = LiveFrames(path(SHADERS/'PrimImpTAAUpdate-desktop-resolve.spv'),
                   C.addressof(constants), C.addressof(push), next_frame, frame_ready, None,
                   C.addressof(draw), C.addressof(anatomy), path(ROOT/'stick-desktop.spv'),
                   C.addressof(stick), next_stick, path(ROOT/'eye-desktop.spv'),
                   C.addressof(vertex), C.addressof(eye), number_of_eyes, rgb,
                   number_of_tips if tip_count and present_tip else Eyes(),
                   tip_ready if tip_count and present_tip else Present())
    import tempfile
    view = Path(tempfile.gettempdir())/f'dreams-imp-lighting-{os.getpid()}.bin'
    # Use the complete, captured lit-body parameters. The eye-pass capture
    # contains zero scene-light coefficients and cannot represent this pass.
    # Keep Dreams' own fur ramp and body-light contribution unchanged.
    view_bytes = bytearray((ROOT/'reference-state'/'scene-lighting.bin').read_bytes()[:208])
    body = runpy.run_path(str(ROOT/'verify-native-imp-body.py'))
    view_bytes[16:28] = body['stock_body_parameters']()[0x40:0x4c]
    view.write_bytes(view_bytes)
    lib = C.CDLL(str(ROOT/'imp-renderer.dll'))
    loop = lib.imp_gallery_render_loop if gallery is not None else lib.imp_render_loop
    extra = ()
    if gallery is not None:
        active, index = gallery
        get_index = Eyes(lambda _: index())
        gallery_frames = GalleryFrames(active, len(active), get_index, matrix)
        extra = (C.byref(gallery_frames),)
    loop.argtypes = (C.c_char_p,)*5 + (C.POINTER(LiveFrames),) + (
        (C.POINTER(GalleryFrames),) if gallery is not None else ()) + (C.c_void_p, C.c_size_t)
    loop.restype = C.c_int
    error = C.create_string_buffer(512)
    try:
        result = loop(path(SHADERS/'PrimImpVS-0.spv'), path(SHADERS/'PrimImpOverBokehPS-desktop-draw.spv'),
                      path(ROOT/'standalone-assets'/'imp_alpha_texture.dds'),
                      path(ROOT/'test-blue-noise-r8.bin'), path(view), C.byref(f), *extra, error, len(error))
    finally:
        view.unlink(missing_ok=True)
    if errors:
        raise errors[0]
    if result:
        message = error.value.decode(errors='replace')
        raise RuntimeError(message)


def check():
    import math
    body = runpy.run_path(str(ROOT/'verify-native-imp-body.py'))
    native = body['NATIVE']
    points, faces = body['default_mesh']()
    guest = native['verified_bytes'](native['GUEST'], native['EXPECTED_TEXT'])
    generator = body['BodyTest'](guest, faces)
    timings = []

    def particles():
        scale = 1 + 0.15 * math.sin(len(timings) / 7)
        return generator.generate([(x, y * scale, z) for x, y, z in points], 1, stock=True)

    def present(data, width, height):
        nonempty = sum(alpha > 0.05 and y > 0.005
                       for y, co, cg, alpha in struct.iter_unpack('<4e', data))
        if nonempty < 400:
            raise ValueError(f'Unexpected resolved frame: {width=} {height=} {nonempty=}')
        timings.append(time.perf_counter())
        return len(timings) < 120

    try:
        render(particles, present)
    finally:
        generator.close()
    if len(timings) != 120:
        raise ValueError('Incomplete live frame test')
    elapsed = timings[-1] - timings[0]
    print(f'Original GPU draw and temporal resolve presented {len(timings)} live {WIDTH}x{HEIGHT} frames '
          f'at {(len(timings)-1)/elapsed:.1f} FPS with Dreams closed.')


if __name__ == '__main__':
    check()
