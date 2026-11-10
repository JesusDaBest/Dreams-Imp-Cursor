"""Run the original Imp eye setup and particle generator on a pose fixture."""

import ctypes as C
from io import BytesIO
import math
import runpy
import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
BODY = runpy.run_path(str(ROOT / 'verify-native-imp-body.py'))
NATIVE = BODY['NATIVE']
PARTICLE_BYTES = BODY['RECORD_BYTES']
MAX_PARTICLES = 4096


class FaceTest(BODY['BodyTest']):
    def __init__(self, text, faces, last_page=0xebf7000):
        super().__init__(text, faces, last_page=last_page)
        try:
            self._face_init(text)
        except BaseException:
            self.close()
            raise

    def _face_init(self, text):
        base = NATIVE['BASE']
        for begin, end, permission in ((0x75eb000, 0x75ef000, 0x20),
                                       (0x75c3000, 0x75c4000, 0x20),
                                       (0x77fe000, 0x77ff000, 0x02),
                                       (0xebd4000, 0xebd5000, 0x04),
                                       (0xebf6000, 0xebf7000, 0x04)):
            self.pages(begin, end)
            if end - base <= len(text):
                self.put(begin, text[begin-base:end-base])
            if begin == 0x75eb000:
                # The remaining setup code allocates from the game's particle
                # ring. The fixture provides an independent bounded buffer.
                self.put(0x75ec156, b'\xc5\xf8\x77\xc3')
            self.protect(begin, end, permission)
        # The stock initializer at 0x6c081c3 builds both one-degree tables.
        radians, = struct.unpack_from('<f', text, 0x77cd0c0 - base)
        angles = [C.c_float(i*radians).value for i in range(360)]
        self.protect(0xebd3000, 0xebd4000, 0x04)
        for address, trig in ((0xebd3b80, math.sin), (0xebd4130, math.cos)):
            self.put(address, struct.pack('<360f', *(trig(a) for a in angles)))
        self.put(0xebd4120, struct.pack('<I', 0x343bbd2e))
        self.put(0xebd46d0, struct.pack('<fB', 1, 1))
        self.protect(0xebd3000, 0xebd5000, 0x02)
        self.atlases = []
        for address, name, digest in (
            (0xebf6b00, 'imp_eyes.png', '68c5f3660ae6b748c113ba5daee53eaddb869bc593326153e43e6885c85ed21a'),
            (0xebf6c20, 'imp_pupils.png', '844dd04a7522c078ff75e20ad2918aee062eae3bac1f7b7919a581644115f9e6'),
        ):
            raw = NATIVE['verified_bytes'](ROOT / 'standalone-assets' / name, digest)
            image = Image.open(BytesIO(raw)).convert('L')
            if image.size != (256, 256):
                raise ValueError(f'Unexpected atlas size: {name}')
            pixels = image.tobytes()
            atlas = C.create_string_buffer(pixels)
            self.atlases.append(atlas)
            radii = []
            mask = 0
            for cell in range(16):
                left, top = 64*(cell % 4), 64*(cell // 4)
                distance_sq = max(((x - 32)**2 + (y - 32)**2
                                   for y in range(64) for x in range(64)
                                   if pixels[(top+y)*256+left+x] != 255), default=-1)
                if distance_sq >= 0:
                    mask |= 1 << cell
                radii.append(math.sqrt(distance_sq)/32 if distance_sq >= 0 else 1)
            self.put(address, struct.pack('<QIII4x16f', C.addressof(atlas), 256, 256, 1, *radii))
            self.put(address + 0x118, struct.pack('<Q', mask))
        self.protect(0xebf6000, 0xebf7000, 0x02)
        self.protect(0x75b3000, 0x75b4000, 0x04)
        self.protect(0x75b6000, 0x75b7000, 0x04)
        self.protect(0x7de6000, 0x7de9000, 0x04)
        # SELF relocation at 0x7de7380 uses NID EH-x713A99c (atan2f).
        atan2_stub = 0x75b6060
        host = C.cast(self.runtime.atan2f, C.c_void_p).value
        self.put(atan2_stub, bytes.fromhex('48 83 ec 28 48 b8') +
                 struct.pack('<Q', host) + bytes.fromhex('ff d0 48 83 c4 28 c3'))
        plt = 0x7788a70
        off = plt - base
        if text[off:off+2] != b'\xff\x25':
            raise ValueError('Unexpected eye math import thunk')
        got = plt + 6 + struct.unpack_from('<i', text, off+2)[0]
        self.put(got, struct.pack('<Q', self.addr(atan2_stub)))
        prepare = NATIVE['to_guest'](self.addr(0x75ebd60))
        index = prepare.index(bytes.fromhex('48 89 cf 48 b8'))
        prepare[index:index+3] = bytes.fromhex(
            '48 89 c8 48 8b 38 48 8b 70 08 48 8b 50 10 48 8b 48 18 4c 8b 40 20')
        self.put(0x75b3900, prepare)
        self.put(0x75b3a00, NATIVE['to_guest'](self.addr(0x75ec270)))
        stick = NATIVE['to_guest'](self.addr(0x75c2600))
        index = stick.index(bytes.fromhex('48 89 cf 48 b8'))
        stick[index:index] = bytes.fromhex('31 f6')
        self.put(0x75b3b00, stick)
        self.protect(0x75b3000, 0x75b4000, 0x20)
        self.protect(0x75b6000, 0x75b7000, 0x20)
        self.protect(0x7de6000, 0x7de9000, 0x02)
        if not self.win.FlushInstructionCache(self.win.GetCurrentProcess(), self.start, 0):
            raise C.WinError(C.get_last_error())
        self.prepare_face = C.CFUNCTYPE(None, C.c_void_p)(self.addr(0x75b3900))
        self.face = C.CFUNCTYPE(None, C.c_void_p)(self.addr(0x75b3a00))
        self.stick = C.CFUNCTYPE(None, C.c_void_p)(self.addr(0x75b3b00))

    def antenna(self, path):
        if not 3 <= len(path) <= 192:
            raise ValueError('Antenna path outside the job buffer')
        job = C.create_string_buffer(0x1400)
        owner = C.create_string_buffer(0x7200)
        params = C.create_string_buffer(bytes(BODY['stock_body_parameters']()))
        control = C.create_string_buffer(MAX_PARTICLES*PARTICLE_BYTES + 64)
        output = C.create_string_buffer(MAX_PARTICLES*PARTICLE_BYTES + 64)
        for buffer in (control, output):
            buffer[-64:] = b'\xa5'*64
        for off, buf in ((0x20, params), (0x90, owner), (0xdd8, control), (0xde0, output)):
            struct.pack_into('<Q', job, off, C.addressof(buf))
        struct.pack_into('<I', job, 0xdb0, len(path))
        struct.pack_into('<2I', job, 0xde8, MAX_PARTICLES, MAX_PARTICLES)
        rgb = struct.unpack_from('<3f', params, 0x40)
        struct.pack_into('<4f', job, 0x60, *rgb, 1)
        struct.pack_into('<f', job, 0x74, 1)
        struct.pack_into('<4f', job, 0xc0, 0, 0, 1, 1)
        struct.pack_into('<4f', job, 0xd0, 0, 0, 1, 1)
        distance = 0
        last = path[0]
        for i, point in enumerate(path):
            distance += math.dist(point, last)
            struct.pack_into('<4f', job, 0x130 + i*16, *point, distance)
            last = point
        struct.pack_into('<5f', job, 0xdc0, distance, 0, 0.035, 1, distance)
        self.stick(C.addressof(job))
        mesh_count, = struct.unpack_from('<H', owner, 0x70e0)
        fleck_count, = struct.unpack_from('<H', owner, 0x70ea)
        if any(buffer[-64:] != b'\xa5'*64 for buffer in (control, output)):
            raise ValueError('Native antenna job overran its buffers')
        if mesh_count != len(path) - 1 or fleck_count > MAX_PARTICLES:
            raise ValueError(f'Unexpected antenna mesh record count: {mesh_count}')
        return control[:mesh_count * PARTICLE_BYTES], output[:fleck_count * PARTICLE_BYTES]

    def eye(self, side, blink, *, lighting=1, projection_sign=0xffffffff, aim=(0, 0, 1)):
        job = C.create_string_buffer(0x1a0)
        pose = C.create_string_buffer(0x50)
        owner = C.create_string_buffer(0x7200)
        config = C.create_string_buffer(0xe8)
        character = C.create_string_buffer(0x200)
        output = C.create_string_buffer(MAX_PARTICLES * PARTICLE_BYTES + 64)
        output[-64:] = b'\xa5'*64
        for off, buf in ((0x10, character), (0x80, owner)):
            struct.pack_into('<Q', config, off, C.addressof(buf))
        struct.pack_into('<2f', pose, 0x18, blink, blink)
        struct.pack_into('<2f', pose, 0x28, 1, 1)
        for offset in (0x30, 0x40):
            struct.pack_into('<4f', pose, offset, 0, 0, 0, 1)
        # Camera and transforms are a deterministic fixture in Imp mesh space.
        for offset in (0xc0,):
            struct.pack_into('<4f', config, offset, 0, 0, 0, 1)
        struct.pack_into('<4f', config, 0xb0, 0, 0, 0, 1)
        struct.pack_into('<f', config, 0x6c, 1)
        struct.pack_into('<f', config, 0xd0, lighting)
        struct.pack_into('<2f', config, 0xd8, 0.1, 0.1)
        struct.pack_into('<f', config, 0xdc, 0.1)
        struct.pack_into('<2f', character, 0xe8, 0.1, 0.1)
        struct.pack_into('<6f', character, 0x124, 0, 0, 0, 0, 0, 0)
        direction = C.create_string_buffer(struct.pack('<3fI4f', *aim, projection_sign,
                                                       1, 1, 1, 1))
        transform = C.create_string_buffer(struct.pack('<8f', (-1 if side else 1)*0.22,
                                                       0.1, 0.7, 0.28, 0, 0, 0, 1))
        struct.pack_into('<I', job, 0x190, side)
        arguments = (C.c_void_p * 5)(*(C.addressof(buf)
            for buf in (job, direction, transform, pose, config)))
        self.prepare_face(C.addressof(arguments))
        struct.pack_into('<QI', job, 0, C.addressof(output), MAX_PARTICLES)
        self.face(C.addressof(job))
        count, = struct.unpack_from('<H', owner, 0x7112 if side else 0x7108)
        if count > MAX_PARTICLES or output[-64:] != b'\xa5'*64:
            raise ValueError(f'Unexpected eye particle write range: {count}')
        return output[:count*PARTICLE_BYTES]


if __name__ == '__main__':
    _, faces = BODY['default_mesh']()
    text = NATIVE['verified_bytes'](NATIVE['GUEST'], NATIVE['EXPECTED_TEXT'])
    test = FaceTest(text, faces)
    try:
        states = []
        for blink in (0.0, 0.5, 1.0):
            eyes = tuple(test.eye(side, blink) for side in (0, 1))
            if not all(eyes):
                raise ValueError('An eye produced no particles')
            states.append(eyes)
            print(blink, *(len(eye)//PARTICLE_BYTES for eye in eyes), flush=True)
        for side in (0, 1):
            if len({state[side] for state in states}) != len(states):
                raise ValueError('The eye particles did not respond to blinking')
        path = [(0, 0.55, 0.13), (0.04, 0.7, 0.13), (0.06, 0.84, 0.13), (0.08, 1.1, 0.13)]
        control, stick = test.antenna(path)
        if not any(control) or not any(stick):
            raise ValueError('Native antenna emitted empty data')
        moved = [(x + y * 0.1, y, z) for x, y, z in path]
        if (control, stick) == test.antenna(moved):
            raise ValueError('Native antenna did not respond to its path')
        print(f'Original antenna generator produced {len(control)//PARTICLE_BYTES} '
              'mesh records and responded to path movement.', flush=True)
    finally:
        test.close()
