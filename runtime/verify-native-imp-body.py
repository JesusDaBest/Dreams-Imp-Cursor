"""Exercise Dreams' original body particle generator against its Imp mesh."""

import ctypes as C
from functools import lru_cache
import math
import runpy
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NATIVE = runpy.run_path(str(ROOT / 'verify-native-imp-animation.py'))
RECORD_BYTES = 0x88
STOCK_CHARACTER = ROOT / 'standalone-assets' / '00_default.unpacked.bin'


@lru_cache(maxsize=1)
def native_sincos():
    library = C.CDLL(str(ROOT/'imp-renderer.dll'))
    function = library.imp_sincos
    function.argtypes = (C.POINTER(C.c_float), C.POINTER(C.c_float), C.c_float)
    function.restype = None
    return function


def stock_body_parameters():
    raw = NATIVE['verified_bytes'](STOCK_CHARACTER,
        '00a76af8a07e685dfaafd343dff74ffb81554cbe7187dfd56eaf89627fc103ac')
    if raw[:8] != b'pmI_\xa0\x04\x00\x00':
        raise ValueError('Unsupported character version')
    # Fields serialized by 0x75c6d60 for version 0x4a0. The extra layer
    # and sizing fields use the defaults in the load path at 0x75c9830.
    params = bytearray(0xb4)
    for disk, memory, size in ((0x30, 0x30, 8), (0x38, 0x3c, 4),
                               (0x3c, 0x38, 4), (0x40, 0x40, 12),
                               (0x4c, 0x50, 4), (0x50, 0x60, 12),
                               (0x5c, 0x70, 12), (0x68, 0x80, 12),
                               (0x74, 0x90, 12), (0x80, 0x9c, 1),
                               (0x81, 0xb0, 4)):
        params[memory:memory+size] = raw[disk:disk+size]
    params[0x9d] = 0xd0
    struct.pack_into('<4f', params, 0xa0, 0.15, 0.5, 0.8, 1.0)
    return params


def default_mesh():
    filename = ROOT / 'standalone-assets' / 'imp_shapes.obj'
    asset = NATIVE['verified_bytes'](filename, '90f34d1a6501fa957743e4a1b4afe860951a9c29d9e63f101e8e202056f703d9')
    points = []
    indices = []
    for line in asset.decode('ascii').splitlines():
        if line.startswith('# object ') and points:
            break
        if line.startswith('v '):
            points.append(tuple(map(float, line.split()[1:])))
        if line.startswith('f '):
            indices.extend(int(i.split('/')[0]) - 1 for i in line.split()[1:])
    if len(points) != 162 or len(indices) != 960 or not all(0 <= i < len(points) for i in indices):
        raise ValueError('Unexpected Imp mesh layout')
    return points, indices


class BodyTest(NATIVE['NativeEvaluator']):
    def __init__(self, text, faces, last_page=0xebd4000):
        super().__init__(text, last_page=last_page)
        try:
            self._body_init(text, faces)
        except BaseException:
            self.close()
            raise

    def _body_init(self, text, faces):
        for begin, end, executable in ((0x75c1000, 0x75c3000, True),
                                       (0x75cc000, 0x75ce000, True),
                                       (0x7809000, 0x780a000, False),
                                       (0xebd2000, 0xebd4000, False)):
            self.pages(begin, end)
            base = NATIVE['BASE']
            if end - base <= len(text):
                self.put(begin, text[begin-base:end-base])
            if begin == 0xebd2000:
                self.put(0xebd29e0, struct.pack('<960i', *faces))
            self.protect(begin, end, 0x20 if executable else 0x02)

        sincos = native_sincos()
        self.sincos = sincos
        self.protect(0x75b3000, 0x75b4000, 0x04)
        self.protect(0x7de6000, 0x7de9000, 0x04)
        self.pages(0x75b6000, 0x75b7000)
        # The original System V sincosf receives pointers in RDI/RSI and its angle in XMM0.
        sincos_stub = 0x75b6000
        sincos_code = bytes.fromhex('48 89 f9 48 89 f2 0f 28 d0 48 83 ec 28 48 b8')
        sincos_code += struct.pack('<Q', C.cast(sincos, C.c_void_p).value)
        self.put(sincos_stub, sincos_code + bytes.fromhex('ff d0 48 83 c4 28 c3'))
        isnan_stub = 0x75b6040
        self.put(isnan_stub, bytes.fromhex('0f 2e c0 0f 9a c0 0f b6 c0 c3'))
        base = NATIVE['BASE']
        for plt, stub in ((0x778afb0, sincos_stub), (0x7788170, isnan_stub)):
            off = plt - base
            if text[off:off+2] != b'\xff\x25':
                raise ValueError('Unexpected guest import thunk')
            got = plt + 6 + struct.unpack_from('<i', text, off+2)[0]
            self.put(got, struct.pack('<Q', self.addr(stub)))
        # Reuse the tested one-argument ABI bridge, with worker number zero in RSI.
        wrapper = 0x75b3d00
        code = NATIVE['to_guest'](self.addr(0x75c1690))
        call = code.index(bytes.fromhex('48 89 cf 48 b8'))
        code[call:call] = bytes.fromhex('31 f6')
        self.put(wrapper, code)
        self.protect(0x75b3000, 0x75b4000, 0x20)
        self.protect(0x75b6000, 0x75b7000, 0x20)
        self.protect(0x7de6000, 0x7de9000, 0x02)
        if not self.win.FlushInstructionCache(self.win.GetCurrentProcess(), self.start, 0):
            raise C.WinError(C.get_last_error())
        self.body = C.CFUNCTYPE(None, C.c_void_p)(self.addr(wrapper))

    def generate(self, points, seed, stock=False):
        # A one-fleck-per-triangle fixture for checking this routine in isolation.
        # These parameters are test inputs, separate from the game's live Imp state.
        params = C.create_string_buffer(0xb0)
        struct.pack_into('<I', params, 0x30, seed)
        for offset, value in ((0x50, 1), (0x94, 1), (0xa4, 0.04), (0xa8, 0.06)):
            struct.pack_into('<f', params, offset, value)
        if stock:
            params = C.create_string_buffer(bytes(stock_body_parameters()))
        position_bytes = b''.join(struct.pack('<4f', *p, 0) for p in points)
        mesh = C.create_string_buffer(position_bytes)
        job = C.create_string_buffer(0x1400)
        imp = C.create_string_buffer(0x7100)
        out = C.create_string_buffer(RECORD_BYTES * 320 + 64)
        out[RECORD_BYTES * 320:] = b'\xa5' * 64
        for offset, buf in ((0x20, params), (0x90, imp), (0xe10, out),
                            (0x1020, mesh), (0x1028, mesh)):
            struct.pack_into('<Q', job, offset, C.addressof(buf))
        struct.pack_into('<I', job, 0xe18, 320)
        rgb = struct.unpack_from('<3f', params, 0x40) if stock else (1, 0.4, 0.1)
        struct.pack_into('<4f', job, 0x60, *rgb, 1)
        struct.pack_into('<f', job, 0x74, 1)
        for index in range(162):
            struct.pack_into('<f', job, 0x1030 + 4*index, 1)
        self.body(C.addressof(job))
        count, = struct.unpack_from('<H', imp, 0x70f4)
        if count != 320 or out[RECORD_BYTES * 320:] != b'\xa5' * 64:
            raise ValueError(f'Unexpected particle count or write range: {count}')
        return out[:RECORD_BYTES * count]


def main():
    mesh, faces = default_mesh()
    source = NATIVE['verified_bytes'](NATIVE['GUEST'], NATIVE['EXPECTED_TEXT'])
    runner = BodyTest(source, faces)
    try:
        first = runner.generate(mesh, 1)
        if first != runner.generate(mesh, 1) or first == runner.generate(mesh, 2):
            raise ValueError('Unexpected native particle seed behavior')
        if first == runner.generate([(x, y * 0.75, z) for x, y, z in mesh], 1):
            raise ValueError('Native particles did not react to deformation')
        print('Original body generator placed 320 particles on the original Imp mesh. '
              'Output was repeatable and responded to mesh deformation.')
    finally:
        runner.close()


if __name__ == '__main__':
    main()
