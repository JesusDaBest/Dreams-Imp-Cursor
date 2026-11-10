"""Execute the original Imp simulation from its initialized particle state."""
import ctypes as C
from bisect import bisect_right
import hashlib
import math
from pathlib import Path
import runpy
import struct

ROOT = Path(__file__).resolve().parent
FACE = runpy.run_path(str(ROOT/'verify-native-imp-face.py'))
BODY, NATIVE = FACE['BODY'], FACE['NATIVE']
REFERENCE = ROOT/'reference-state'
LAYERS = (0x75b86b0, 0x75b8580, 0x75b8710, 0x75b8a70, 0x75b8c70,
          0x75b8dc0, 0x75b8590, 0x75b93d0, 0x75b9000)
STATE_BYTES = 0xb410
POINT_COUNT = 162
IDENTITY = (0.0, 0.0, 0.0, 1.0)
SOLVER_STEP = 1 / 60
SURFACE_START, SURFACE_END = 0x91c0, 0xa600
SURFACE_FLOATS = struct.Struct(f'<{(SURFACE_END - SURFACE_START) // 4}f')
COLLISION_GRID = struct.Struct('<512f')
COLLISION_START, COLLISION_END = 0xab38, 0xb360
# Menu motion-control capture. Position limits come from the guest's
# +/-0.4 projection clamp, converted back into its view plane.
AIM_DEPTH = 0.4
AIM_LIMIT_X = AIM_DEPTH / 0.9343093633651733
AIM_LIMIT_Y = AIM_DEPTH / 1.6609944105148315
PITCH_POSITIONS = (0.0, .02793661, .05594143, .08408336, .11243265,
                   .14106156, .17004521, .19946235, .22939625, AIM_LIMIT_Y)
PITCH_ROTATION_X = (0.0, .03483590, .06925262, .10285481, .13529158,
                    .16627178, .19557229, .22303978, .24858695, .25770122)


def multiply_rotation(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by,
            aw*by - ax*bz + ay*bw + az*bx,
            aw*bz + ax*by - ay*bx + az*bw,
            aw*bw - ax*bx - ay*by - az*bz)


def menu_aim_frame(rest, x, y):
    # A mouse supplies two axes. Use the native axis curves without adding
    # a controller roll component.
    view_x, view_y = -AIM_LIMIT_X*x, AIM_LIMIT_Y*y
    yaw = math.atan2(-view_x, AIM_DEPTH) / 2
    height = abs(view_y)
    i = min(bisect_right(PITCH_POSITIONS, height), len(PITCH_POSITIONS) - 1)
    amount = (height - PITCH_POSITIONS[i-1]) / (PITCH_POSITIONS[i] - PITCH_POSITIONS[i-1])
    pitch_x = math.copysign(PITCH_ROTATION_X[i-1] +
                            amount * (PITCH_ROTATION_X[i] - PITCH_ROTATION_X[i-1]), view_y)
    direction = multiply_rotation((0.0, math.sin(yaw), 0.0, math.cos(yaw)),
                                  (pitch_x, 0.0, 0.0, math.sqrt(1 - pitch_x*pitch_x)))
    # Dreams offsets the Imp origin down along its rotated up axis.
    ox, oy, oz, scale = rest[:4]
    up = multiply_rotation(multiply_rotation(direction, (0.0, -oy, 0.0, 0.0)),
                           (-direction[0], -direction[1], -direction[2], direction[3]))
    return ox + view_x - up[0], view_y - up[1], oz - up[2], scale, *direction


def relative_frame(previous, current):
    inverse = (-current[4], -current[5], -current[6], current[7])
    # The menu projects pointer travel onto the view plane before rotating it.
    distance = ((previous[0] - current[0]) / current[3],
                (previous[1] - current[1]) / current[3], 0.0)
    rotation = multiply_rotation(inverse, previous[4:])
    offset = multiply_rotation(multiply_rotation(inverse, (*distance, 0.0)), current[4:])[:3]
    limit = max(1.0, math.hypot(*offset) / 4.0)
    return (*(value / limit for value in offset), 1.0), rotation


class Motion(FACE['FaceTest']):
    def __init__(self, text, faces):
        super().__init__(text, faces, last_page=0x119e8000)
        try:
            self._motion_init(text)
        except BaseException:
            self.close()
            raise

    def _motion_init(self, text):
        base = NATIVE['BASE']
        for begin, end, permission in ((0x75b7000, 0x75c1000, 0x20),
                                       (0x8a75000, 0x8a76000, 0x02)):
            self.pages(begin, end)
            if end - base <= len(text):
                self.put(begin, text[begin-base:end-base])
            else:
                memory = NATIVE['GUEST'].with_name('guest-data.bin').read_bytes()
                self.put(begin, memory[begin-0x7f90000:end-0x7f90000])
            self.protect(begin, end, permission)

        tables = (REFERENCE/'mesh-tables.bin').read_bytes()
        if len(tables) != 0x5000:
            raise ValueError('Incomplete original Imp mesh tables')
        self.pages(0xebd0000, 0xebd2000)
        self.protect(0xebd2000, 0xebd5000, 0x04)
        self.put(0xebd0000, tables)
        self.surface_data = []
        surface = bytearray()
        for level, expected in enumerate((20, 80, 320)):
            raw_level = (REFERENCE/f'surface-{level}.bin').read_bytes()
            if len(raw_level) != expected * 64:
                raise ValueError('Unexpected subdivision lookup')
            block = C.create_string_buffer(raw_level)
            self.surface_data.append(block)
            surface.extend(struct.pack('<3Q', C.addressof(block), expected, expected))
        descriptor = C.create_string_buffer(bytes(surface))
        self.surface_data.append(descriptor)
        self.put(0xebd0d50, struct.pack('<Q', C.addressof(descriptor)))
        self.protect(0xebd0000, 0xebd5000, 0x02)
        scalar = (REFERENCE/'motion-scalar.bin').read_bytes()
        if len(scalar) != 4:
            raise ValueError('Incomplete original Imp motion scalar')
        self.protect(0x8a75000, 0x8a76000, 0x04)
        self.put(0x8a75c6c, scalar)
        self.solver_step = C.c_float.from_address(self.addr(0x8a75c6c))

        self.protect(0x75b3000, 0x75b4000, 0x04)
        self.protect(0x75b6000, 0x75b7000, 0x04)
        self.protect(0x7de6000, 0x7de9000, 0x04)
        for plt, stub, name in ((0x7788100, 0x75b3c00, None),
                                (0x7788190, 0x75b3c20, 'acosf'),
                                (0x778ae70, 0x75b3c40, 'sinf'),
                                (0x778af90, 0x75b3c60, 'powf')):
            if name:
                host = C.cast(getattr(self.runtime, name), C.c_void_p).value
                code = bytes.fromhex('48 83 ec 28 48 b8') + struct.pack('<Q', host)
                code += bytes.fromhex('ff d0 48 83 c4 28 c3')
            else:
                # libSceLibcInternal's finite-float predicate.
                code = bytes.fromhex('66 0f 7e c0 25 ff ff ff 7f 3d 00 00 80 7f 0f 92 c0 0f b6 c0 c3')
            self.put(stub, code)
            off = plt - base
            if text[off:off+2] != b'\xff\x25':
                raise ValueError('Unexpected motion math import thunk')
            got = plt + 6 + struct.unpack_from('<i', text, off+2)[0]
            self.put(got, struct.pack('<Q', self.addr(stub)))
        wrapper = 0x75b6100
        bridge = NATIVE['to_guest'](self.addr(0x75bd190))
        start = bridge.index(bytes.fromhex('48 89 cf 48 b8'))
        # RCX points to six integer/pointer arguments and five unaligned
        # 16-byte SIMD arguments in the original System V call order.
        args = bytes.fromhex(
            '48 89 c8 48 8b 38 48 8b 70 08 48 8b 50 10 48 8b 48 18 4c 8b 40 20 4c 8b 48 28')
        for reg in range(5):
            args += bytes((0x0f, 0x10, 0x40 | reg << 3, 0x30+16*reg))
        bridge[start:start+3] = args
        self.put(wrapper, bridge)
        self.protect(0x75b3000, 0x75b4000, 0x20)
        self.protect(0x75b6000, 0x75b7000, 0x20)
        self.protect(0x7de6000, 0x7de9000, 0x02)
        if not self.win.FlushInstructionCache(self.win.GetCurrentProcess(), self.start, 0):
            raise C.WinError(C.get_last_error())
        self.update = C.CFUNCTYPE(None, C.c_void_p)(self.addr(wrapper))

        raw = (REFERENCE/'solver.bin').read_bytes()
        if len(raw) != STATE_BYTES or struct.unpack_from('<I', raw, 0x67a4)[0] != POINT_COUNT:
            raise ValueError('Unexpected original solver layout')
        if struct.unpack_from('<I', raw, 0x5ff0)[0] != 480:
            raise ValueError('Unexpected spring table')
        self.pages(0xebb1000, 0xebb4000)
        rest = (REFERENCE/'face-rest.bin').read_bytes()
        if len(rest) != 0x2c40:
            raise ValueError('Original Imp rest mesh is incomplete')
        self.put(0xebb13c0, rest)
        self.face_tree = C.create_string_buffer((REFERENCE/'face-tree.bin').read_bytes())
        self.face_tree_indices = C.create_string_buffer((REFERENCE/'face-tree-indices.bin').read_bytes())
        count, index_count = (len(self.face_tree)-1)//48, (len(self.face_tree_indices)-1)//4
        self.put(0xebb1390, struct.pack('<6Q', C.addressof(self.face_tree), count, count,
                                       C.addressof(self.face_tree_indices), index_count, index_count))
        self.protect(0xebb1000, 0xebb4000, 0x02)
        self.state = C.create_string_buffer(raw, STATE_BYTES + 64)
        self.state[-64:] = b'\xa5' * 64
        self.render_state = self.state
        self.interpolated_state = C.create_string_buffer(STATE_BYTES)
        self.motion_phase = SOLVER_STEP
        self.step_count = 0
        self.current_sample = None
        self.previous_sample = None
        for layer, entry in enumerate(LAYERS):
            struct.pack_into('<3Q', self.state, 0x6630+layer*0x28, 0, self.addr(entry), 0)
        self.rest_transform = raw[0xaa10:0xaa30]
        self.rest_frame = struct.unpack('<8f', self.rest_transform)
        self.free_collision = bytes(self.state[COLLISION_START:COLLISION_END])
        self.collision_bounds = None
        self.previous_frame = None
        self.previous_aim = (0.0, 0.0)
        self.head_pose = raw[0xaa30:0xaa50]
        self.tip_height, = struct.unpack_from('<f', raw, 0)
        self.stock_positions = self.positions()
        self.eye_state = [(REFERENCE/f'eye-{side}.bin').read_bytes() for side in range(2)]
        character = self._stock_character(text)
        self.eye_character = [character, character]
        self.body_job = (REFERENCE/'body-job.bin').read_bytes()
        if len(self.body_job) != 0x12c0:
            raise ValueError('Incomplete original body particle job')
        self.body_config = C.create_string_buffer(self.eye_character[0].raw, 0x210)
        default = BODY['stock_body_parameters']()
        C.memmove(C.addressof(self.body_config), bytes(default), len(default))
        self.body_color = struct.unpack_from('<3f', default, 0x40)
        self.previous_body = None
        self.mouth_rest = (REFERENCE/'mouth-rest.bin').read_bytes()
        self.face_head = (REFERENCE/'face-head-frame.bin').read_bytes()
        self._mouth_init(text)
        self._eye_binding_init(text)
        self.character_data = None
        self.character_mouth = None

    def set_character(self, data, bindings=None):
        if len(data) != 0x4500:
            raise ValueError('Invalid decoded Imp appearance')
        self.character_data = bytes(data)
        character = C.create_string_buffer(data, len(data))
        self.eye_character = [character, character]
        self.body_config = character
        self.body_color = struct.unpack_from('<3f', data, 0x40)
        struct.pack_into('<Q', self.eye_object, 0x3f0, C.addressof(character))
        if bindings is not None:
            if len(bindings) != 0x2040:
                raise ValueError('Invalid native character bindings')
            self.eye_object[0x2c340:0x2c370] = bindings[:0x30]
            self.character_mouth = bytes(bindings[0x30:])
        self.previous_body = None

    def mouth_particles(self, pose, channels):
        if self.character_mouth is not None and 0 not in channels:
            count, = struct.unpack_from('<I', self.character_mouth, 0x2000)
            if not count:
                return b''
            return self.stroke_particles(self.character_mouth, 0, mouth=True)
        return self.stroke_particles(pose, 0xb0, mouth=True)

    def character_strokes(self):
        if self.character_data is None:
            return b''
        data = self.character_data
        total, = struct.unpack_from('<I', data, 0x41d0)
        if total > 512:
            raise ValueError('Invalid character decoration count')
        result, position = [], 0
        while position < total:
            offset = 0x21d0 + position * 16
            count, = struct.unpack_from('<H', data, offset + 12)
            if position + 1 + count > total:
                raise ValueError('Character decoration exceeds its stored range')
            if count:
                result.append(self.stroke_particles(data, offset))
            position += 1 + count
        return b''.join(result)

    def _eye_binding_init(self, text):
        base = NATIVE['BASE']
        for begin, end, permission in ((0x75a2000, 0x75a4000, 0x20),
                                      (0x75cd000, 0x75ce000, 0x20),
                                      (0x77fc000, 0x77fd000, 0x02)):
            self.pages(begin, end)
            self.put(begin, text[begin-base:end-base])
            self.protect(begin, end, permission)
        wrapper = 0x75b6690
        self.protect(0x75b6000, 0x75b7000, 0x04)
        bridge = NATIVE['to_guest'](self.addr(0x75a2f30))
        at = bridge.index(bytes.fromhex('48 89 cf 48 b8'))
        args = bytes.fromhex('48 89 c8 48 8b 38 48 8b 70 08 48 8b 50 10')
        self.put(wrapper, bridge[:at]+args+bridge[at+3:])
        self.protect(0x75b6000, 0x75b7000, 0x20)
        self.win.FlushInstructionCache(self.win.GetCurrentProcess(), self.start, 0)
        self.bind_eye = C.CFUNCTYPE(None, C.c_void_p)(self.addr(wrapper))
        self.eye_object = C.create_string_buffer(0x3a200)
        self.eye_object[0x2c340:0x2c370] = (REFERENCE/'face-bindings.bin').read_bytes()
        struct.pack_into('<Q', self.eye_object, 0x3f0, C.addressof(self.eye_character[0]))
        struct.pack_into('<4f', self.eye_object, 0x29c40, 0, 0, 1, 1)

    def _mouth_init(self, text):
        base = NATIVE['BASE']
        self.mouth_capacity = 1024
        self.mouth_ring = C.create_string_buffer(self.mouth_capacity*136+64)
        self.mouth_ring[-64:] = b'\xa5'*64
        for begin, end, permission in (
            (0x760a000, 0x760c000, 0x20), (0x77a7000, 0x77a8000, 0x02),
            (0x77ff000, 0x7800000, 0x02),
            (0xebfb000, 0xebfc000, 0x02), (0x119e7000, 0x119e8000, 0x02),
        ):
            self.pages(begin, end)
            if end-base <= len(text):
                self.put(begin, text[begin-base:end-base])
            if begin == 0xebfb000:
                self.put(0xebfb328, struct.pack('<Q', C.addressof(self.mouth_ring)))
            self.protect(begin, end, permission)
        self.protect(0x75b6000, 0x75b7000, 0x04)
        jobs = (
            (0x75b6400, 0x760a980,
             '48 89 c8 48 8b 38 48 8b 70 08 48 8b 50 10 48 8b 48 18 f3 0f 6f 40 20'),
            (0x75b6540, 0x760ae00,
             '48 89 c8 48 8b 38 48 8b 70 08 48 8b 50 10 48 8b 48 18 4c 8b 40 20 '
             'f3 0f 6f 40 30 f3 0f 6f 48 40 f3 0f 6f 50 50'),
        )
        for wrapper, entry, arguments in jobs:
            code = NATIVE['to_guest'](self.addr(entry))
            at = code.index(bytes.fromhex('48 89 cf 48 b8'))
            self.put(wrapper, code[:at]+bytes.fromhex(arguments)+code[at+3:])
        self.protect(0x75b6000, 0x75b7000, 0x20)
        self.win.FlushInstructionCache(self.win.GetCurrentProcess(), self.start, 0)
        self.mouth_create, self.mouth_draw = (
            C.CFUNCTYPE(None, C.c_void_p)(self.addr(wrapper)) for wrapper, _, _ in jobs)

    def stroke_particles(self, pose, offset, *, mouth=False, color=None):
        header, = struct.unpack_from('<I', pose, offset+12)
        count, brush = header & 0xffff, (header >> 16) & 0xfff
        if not mouth and not count:
            return b''
        if count > 511:
            raise ValueError('Original Imp stroke has too many points')
        stroke = C.create_string_buffer(self.mouth_rest if mouth else b'', 0xa100)
        struct.pack_into('<I', stroke, 0xa014, 0)
        if not mouth:
            # Original decoration initialization, Dreams 0x75a5391–0x75a53cd.
            stroke[0x9fc4] = b'\x01'
            struct.pack_into('<f', stroke, 0xa018, .15)
            struct.pack_into('<f', stroke, 0xa01c, .375)
        if count:
            points = C.create_string_buffer(pose[offset+16:offset+16+count*16])
            point_range = (C.c_void_p*2)(C.addressof(points), C.addressof(points)+count*16)
            struct.pack_into('<I', stroke, 0x9fc0, 0)
            radius, = struct.unpack_from('<f', self.eye_character[0], 0xb0)
            if not mouth:
                radius = 1.0
            struct.pack_into('<f', stroke, 0xa010, radius)
            rgba = pose[offset:offset+16] if color is None else struct.pack('<4f', *color, 0)
            build = C.create_string_buffer(struct.pack('<4Q', C.addressof(stroke), brush,
                                          C.addressof(point_range), int(mouth))+rgba)
            self.mouth_create(C.addressof(build))
        owner = C.create_string_buffer(0x7200)
        struct.pack_into('<H', owner, 0x70de, self.mouth_capacity)
        config = C.create_string_buffer(self.body_job[0x10:0xf8])
        struct.pack_into('<Q', config, 0x10, C.addressof(self.eye_character[0]))
        struct.pack_into('<Q', config, 0x80, C.addressof(owner))
        transform = C.create_string_buffer(self.face_head[:32])
        draw = C.create_string_buffer(struct.pack('<5Q8x', C.addressof(stroke), C.addressof(self.render_state),
                    C.addressof(transform), C.addressof(config), 1)
                    + self.face_head[32:] + struct.pack('<4f', 1, 0, 0, 0))
        self.mouth_draw(C.addressof(draw))
        length, = struct.unpack_from('<H', owner, 0x70e0)
        if length > self.mouth_capacity or self.mouth_ring[-64:] != b'\xa5'*64:
            raise ValueError('Original stroke generator exceeded its ring buffer')
        return self.mouth_ring[:length*136]

    def _stock_character(self, text):
        base = NATIVE['BASE']
        for begin, end in ((0x75c6000, 0x75ca000), (0x6f42000, 0x6f44000),
                           (0x6f5a000, 0x6f5b000), (0x6f12000, 0x6f13000)):
            self.pages(begin, end)
            self.put(begin, text[begin-base:end-base])
            if begin == 0x75c6000:
                # End this read after the serialized eye palette. The tail
                # builds the game's character inventory and decoration data.
                self.put(0x75c7ce5, bytes.fromhex('c5 f8 77 48 8d 65 d8 5b 41 5c 41 5d 41 5e 41 5f 5d c3'))
            self.protect(begin, end, 0x20)
        wrapper = 0x75b6250
        self.protect(0x75b6000, 0x75b7000, 0x04)
        bridge = NATIVE['to_guest'](self.addr(0x75c6d60))
        index = bridge.index(bytes.fromhex('48 89 cf 48 b8'))
        bridge = bridge[:index] + bytes.fromhex('48 8b 39 48 8b 71 08') + bridge[index+3:]
        self.put(wrapper, bridge)
        self.protect(0x75b6000, 0x75b7000, 0x20)
        self.win.FlushInstructionCache(self.win.GetCurrentProcess(), self.start, 0)
        raw = NATIVE['verified_bytes'](BODY['STOCK_CHARACTER'],
            '00a76af8a07e685dfaafd343dff74ffb81554cbe7187dfd56eaf89627fc103ac')
        input_bytes = C.create_string_buffer(raw)
        reader = C.create_string_buffer(0x108)
        struct.pack_into('<I', reader, 0x14, 0x4a0)
        struct.pack_into('<QQ', reader, 0x88, C.addressof(input_bytes)+8,
                         C.addressof(input_bytes)+len(raw))
        output = C.create_string_buffer((REFERENCE/'character-0.bin').read_bytes(), 0x210)
        args = (C.c_void_p*2)(C.addressof(reader), C.addressof(output))
        C.CFUNCTYPE(None, C.c_void_p)(self.addr(wrapper))(C.addressof(args))
        cursor, = struct.unpack_from('<Q', reader, 0x88)
        if output[0x10:0x17] != b'default' or not 0x110 <= cursor-C.addressof(input_bytes) < len(raw):
            raise ValueError('The original character decoder did not produce the stock eye data')
        return output

    def body_particles(self, points, alpha=1.0):
        job = C.create_string_buffer(self.body_job, 0x1400)
        owner = C.create_string_buffer(0x7200)
        current = C.create_string_buffer(b''.join(struct.pack('<4f', *p, 0) for p in points[:POINT_COUNT]))
        previous = self.previous_body or current
        self.previous_body = current
        limit = 640
        out = C.create_string_buffer(limit*136+64)
        out[-64:] = b'\xa5'*64
        for off, buffer in ((0x20, self.body_config), (0x90, owner), (0xe10, out),
                            (0x1020, current), (0x1028, previous)):
            struct.pack_into('<Q', job, off, C.addressof(buffer))
        struct.pack_into('<3f', job, 0x40, *self.body_color)
        struct.pack_into('<3f', job, 0x50, *self.body_color)
        struct.pack_into('<3f', job, 0x60, *self.body_color)
        struct.pack_into('<f', job, 0x74, alpha)
        struct.pack_into('<I', job, 0xe18, limit)
        self.body(C.addressof(job))
        count, = struct.unpack_from('<H', owner, 0x70f4)
        if count != 320 or out[-64:] != b'\xa5'*64:
            raise ValueError(f'Invalid original body output count: {count}')
        return out[:count*136]

    def positions(self):
        return tuple(struct.unpack_from('<3f', self.state, 0x1560+i*80)
                     for i in range(POINT_COUNT+5))

    def antenna_particles(self, points):
        job = C.create_string_buffer(self.body_job, 0x1400)
        owner = C.create_string_buffer(0x7200)
        mesh_capacity, fleck_capacity = struct.unpack_from('<2I', job, 0xde8)
        if not 0 < mesh_capacity <= 1024 or not 0 < fleck_capacity <= 4096:
            raise ValueError('Invalid original antenna buffer sizes')
        mesh = C.create_string_buffer(mesh_capacity*136+64)
        flecks = C.create_string_buffer(fleck_capacity*136+64)
        for buffer in (mesh, flecks):
            buffer[-64:] = b'\xa5'*64
        for off, buffer in ((0x20, self.body_config), (0x90, owner), (0xdd8, mesh), (0xde0, flecks)):
            struct.pack_into('<Q', job, off, C.addressof(buffer))
        for offset in (0x40, 0x50, 0x60):
            struct.pack_into('<3f', job, offset, *self.body_color)
        samples, = struct.unpack_from('<I', job, 0xdb0)
        if samples != 21:
            raise ValueError('Unexpected original antenna sample count')
        nodes = (56, 162, 163, 164, 165)
        offsets = [tuple(a-b for a, b in zip(points[i], self.stock_positions[i])) for i in nodes]
        lengths = []
        last = None
        for i in range(samples):
            offset = 0x130+16*i
            a, b, c, _ = struct.unpack_from('<4f', job, offset)
            if i < 8:
                t = i/8
                delta = tuple(t*v for v in offsets[0])
            else:
                section = min((i-8)//3, 3)
                t = min((i-8-3*section)/3, 1)
                delta = tuple(v+(w-v)*t for v, w in zip(offsets[section], offsets[section+1]))
            point = tuple(v+d for v, d in zip((a, b, c), delta))
            lengths.append(lengths[-1]+math.dist(last, point) if last else 0.0)
            struct.pack_into('<4f', job, offset, *point, lengths[-1])
            last = point
        struct.pack_into('<3f', job, 0xdc0, lengths[-1], lengths[4], lengths[8])
        self.stick(C.addressof(job))
        mesh_count, = struct.unpack_from('<H', owner, 0x70e0)
        fleck_count, = struct.unpack_from('<H', owner, 0x70ea)
        if (not 0 < mesh_count <= mesh_capacity or not 0 < fleck_count <= fleck_capacity
                or any(buf[-64:] != b'\xa5'*64 for buf in (mesh, flecks))):
            raise ValueError('Original antenna particles exceeded the allocated buffers')
        return mesh[:mesh_count*136], flecks[:fleck_count*136], job[0x130:0x130+16*samples]

    def eye_parameters(self, pose, channels):
        face = bytearray(pose[0x20:0x70])
        for eye, track in enumerate((2, 5)):
            off = eye * 4
            defaults = self.eye_state[eye]
            stock_blink, stock_lower, stock_angle, _ = struct.unpack_from('<4f', defaults, 0x170)
            stock_scale, = struct.unpack_from('<f', self.eye_character[eye], 0x120)
            if track not in channels:
                # Original appearance defaults, Dreams 0x75a54c1–0x75a552d.
                blink = (struct.unpack_from('<f', self.character_data, 0x184+off)[0]
                         if self.character_data is not None else stock_blink / 0.9)
                struct.pack_into('<f', face, 0x18+off, blink)
            if 29 + eye not in channels:
                struct.pack_into('<f', face, 0x20+off, 1.0-stock_lower)
            if track-1 not in channels:
                if self.character_data is not None:
                    stock_angle, = struct.unpack_from('<f', self.character_data, 0x18c+off)
                struct.pack_into('<f', face, 0x10+off, stock_angle)
            if track+1 not in channels:
                struct.pack_into('<f', face, 0x28+off, stock_scale)
            if 23 + 2*eye not in channels:
                face[8+off:9+off] = self.eye_character[eye][0xe1:0xe2]
            face[off:off+1] = self.eye_character[eye][0xe0:0xe1]
        return face

    def eyes(self, pose=None, motion=None, channels=(), *, parameters=None):
        """Use the original eye job state and regenerate its particles for each pose."""
        records = []
        if pose:
            self.eye_object[0x35870:0x36cb0] = self.render_state[SURFACE_START:SURFACE_END]
            self.eye_object[0x29c50:0x29c60] = pose[0x70:0x80]
            face_bytes = bytes(parameters if parameters is not None else
                               self.eye_parameters(pose, channels))
        for side, raw in enumerate(self.eye_state):
            job = C.create_string_buffer(raw)
            owner = C.create_string_buffer(0x7200)
            out = C.create_string_buffer(136*753 + 64)
            out[-64:] = b'\xa5'*64
            struct.pack_into('<QI', job, 0, C.addressof(out), 753)
            struct.pack_into('<Q', job, 0x20, C.addressof(self.eye_character[side]))
            struct.pack_into('<Q', job, 0x90, C.addressof(owner))
            if pose:
                face = C.create_string_buffer(face_bytes)
                transform = C.create_string_buffer(32)
                bind_args = (C.c_void_p*3)(C.addressof(self.eye_object), side, C.addressof(transform))
                self.bind_eye(C.addressof(bind_args))
                previous = C.create_string_buffer(raw[0x150:0x170])
                config = C.create_string_buffer(job[0x10:0xf8])
                args = (C.c_void_p * 5)(*(C.addressof(buf)
                    for buf in (job, previous, transform, face, config)))
                self.prepare_face(C.addressof(args))
            self.face(C.addressof(job))
            count, = struct.unpack_from('<H', owner, 0x7112 if side else 0x7108)
            if not 0 <= count <= 753 or out[-64:] != b'\xa5'*64:
                raise ValueError('Native eye job exceeded its particle buffer')
            records.append(out[:count*136])
        return b''.join(records)

    def update_screen_collision(self, frame, bounds):
        if bounds is None:
            if self.collision_bounds is not None:
                self.state[COLLISION_START:COLLISION_END] = self.free_collision
                self.collision_bounds = None
            return
        key = frame, bounds
        if key == self.collision_bounds:
            return
        self.collision_bounds = key
        x, y, z, scale, *q = frame
        spacing = 6 * scale / 7
        inverse = (-q[0], -q[1], -q[2], q[3])
        right = multiply_rotation(multiply_rotation(q, (1, 0, 0, 0)), inverse)[:3]
        up = multiply_rotation(multiply_rotation(q, (0, 1, 0, 0)), inverse)[:3]
        left_edge, bottom_edge, right_edge, top_edge = (
            value * scale for value in bounds
        )
        offsets = tuple(i * spacing - 3 * scale for i in range(8))
        # Dreams' four view planes feed the 8x8x8 collision grid in world
        # distance units. The desktop renderer uses an orthographic projection.
        distances = []
        for dz in offsets:
            for dy in offsets:
                rx = dz * right[2] + dy * right[1]
                uy = dz * up[2] + dy * up[1]
                for dx in offsets:
                    screen_x = rx + dx * right[0]
                    screen_y = uy + dx * up[0]
                    distances.append(min(screen_x-left_edge, right_edge-screen_x,
                                         screen_y-bottom_edge, top_edge-screen_y))
        struct.pack_into('<f', self.state, 0xab38, 1.0)
        struct.pack_into('<7f', self.state, 0xab40, x, y, z, scale, spacing,
                         1 / spacing, 3 * scale)
        COLLISION_GRID.pack_into(self.state, 0xab60, *distances)

    def move(self, x, y, dt, *, squash=0.0, bounds=None):
        # Map normalized desktop aim to the range of the captured Dreams menu Imp.
        x, y = max(-1.0, min(1.0, x)), max(-1.0, min(1.0, y))
        frame = menu_aim_frame(self.rest_frame, x, y)
        self.update_screen_collision(frame, bounds)
        # A jump across almost half the viewport in one frame can happen when
        # Windows relocates the pointer. Use the solver's recenter path for it.
        recenter = self.previous_frame is None or math.dist(self.previous_aim, (x, y)) > .9
        if recenter:
            self.state[0xb400:0xb402] = b'\x01\x01'
        translation, rotation = relative_frame(frame if recenter else self.previous_frame, frame)
        self.previous_frame = frame
        self.previous_aim = x, y
        camera = C.create_string_buffer(struct.pack('<8f', *frame))
        head = C.create_string_buffer(self.head_pose)
        target = 0.0, self.tip_height, 0.0, 1.0
        transform = C.create_string_buffer(struct.pack('<8f', *target, *IDENTITY))
        self.solver_step.value = min(.1, dt)
        # The game queues a pair of opposing forces for the authored squash track.
        if squash:
            force = max(-1.0, min(1.0, squash)) * (.1 if squash > 0 else .05)
            struct.pack_into('<8f', self.state, 0x6000, 0, force, 0, 0, 0, -force, 0, 0)
            struct.pack_into('<I', self.state, 0x6200, 2)
        args = C.create_string_buffer(128)
        # Dreams uses solver mode 1 for its on-screen Imp. This keeps the
        # pointer tip attached to the aim while the body trails behind it.
        struct.pack_into('<6Q', args, 0, C.addressof(self.state), C.addressof(transform),
                         1, C.addressof(camera), C.addressof(head), 0)
        struct.pack_into('<4f', args, 0x40, *target)
        struct.pack_into('<8f', args, 0x60, *translation, *rotation)
        self.update(C.addressof(args))
        self.render_state = self.state
        if self.state[-64:] != b'\xa5'*64:
            raise ValueError('Original motion solver wrote outside its state')
        points = self.positions()
        if not all(math.isfinite(a) and abs(a) < 50 for p in points for a in p):
            raise ValueError('Invalid position in the original motion solver')
        self.step_count += 1
        return points

    def advance(self, x, y, elapsed, *, squash, speed, bounds=None):
        # The native solve performs a fixed number of spring iterations per
        # call. Advance it on the playback clock and draw between its samples.
        if self.current_sample is None:
            points = self.move(x, y, SOLVER_STEP, squash=squash, bounds=bounds)
            self.current_sample = points, SURFACE_FLOATS.unpack_from(self.state, SURFACE_START)
            return points
        self.motion_phase += elapsed * speed
        while self.motion_phase > SOLVER_STEP + 1e-8:
            self.motion_phase -= SOLVER_STEP
            self.previous_sample = self.current_sample
            points = self.move(x, y, SOLVER_STEP, squash=squash, bounds=bounds)
            self.current_sample = points, SURFACE_FLOATS.unpack_from(self.state, SURFACE_START)
        amount = min(1.0, self.motion_phase / SOLVER_STEP)
        current_points, current_surface = self.current_sample
        if amount >= 1.0 - 1e-6:
            self.render_state = self.state
            return current_points
        previous_points, previous_surface = self.previous_sample
        C.memmove(self.interpolated_state, self.state, STATE_BYTES)
        SURFACE_FLOATS.pack_into(self.interpolated_state, SURFACE_START, *(
            a + (b - a) * amount for a, b in zip(previous_surface, current_surface)))
        self.render_state = self.interpolated_state
        return tuple(tuple(a + (b - a) * amount for a, b in zip(previous, current))
                     for previous, current in zip(previous_points, current_points))


def main():
    _, faces = BODY['default_mesh']()
    text = NATIVE['verified_bytes'](NATIVE['GUEST'], NATIVE['EXPECTED_TEXT'])
    motion = Motion(text, faces)
    try:
        sequence = []
        for i in range(120):
            x, y = 0.45*math.sin(i/13), 0.30*math.cos(i/11)
            sequence.extend(motion.move(x, y, 1/60, squash=0.1))
        result = b''.join(struct.pack('<3f', *point) for point in sequence)
        if len(set(sequence)) < 1000:
            raise ValueError('Original particle simulation did not evolve')
        print(f'Original Imp solver stepped 120 frames with 480 original springs. '
              f'Output SHA256 {hashlib.sha256(result).hexdigest()}.')
    finally:
        motion.close()


if __name__ == '__main__':
    main()
