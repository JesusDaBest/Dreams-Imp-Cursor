"""Run the original Dreams animation evaluator in a separate Windows process."""

import ctypes as C
import hashlib
import math
import runpy
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GUEST = ROOT / 'native-code' / 'guest-text.bin'
ASSET = ROOT / 'standalone-assets' / 'imp_anim.unpacked.bin'
EXPECTED_TEXT = 'f7c96085d535355d5bbbe0bc90d0c668e1191acc02efe8ee0027fc059119ca0d'
EXPECTED_BANK = '822b4600926c8f7ec65d42471c782966dcf880029c5852d6c7ffc09dbcefe8e5'
BASE = 102301696
ENTRY = 0x75b2560
TYPE_AND_OFFSET = (
    (6, 144), (0, 16), (1, 24), (1, 40), (0, 20), (1, 28),
    (1, 44), (1, 96), (5, 80), (5, 48), (5, 64), (1, 8384),
    (1, 8388), (1, 8512), (1, 8516), (1, 8520), (1, 8392),
    (1, 8396), (1, 8400), (1, 8404), (1, 8408), (9, 8416),
    (0, 0), (11, 8), (0, 0), (11, 12), (1, 100), (10, 112),
    (9, 8448), (1, 32), (1, 36), (7, 8480), (7, 8484),
    (7, 8488), (1, 8412), (8, 16784), (8, 16800), (8, 8496),
    (12, 8560), (4, 8528), (2, 128), (1, 8544),
)
CURVES = (0x75b2130, 0x75b2140, 0x75b2160, 0x75b21b0, 0x75b2200,
          0x75b2220, 0x75b2240, 0x75b2270, 0x75b2280, 0x75b2290, 0x75b22b0)


def verified_bytes(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f'Unsupported revision of {path.name}')
    return raw


def to_guest(target):
    # Windows preserves RDI, RSI and XMM6–15 across calls. SysV doesn't.
    code = bytearray.fromhex('57 56 48 81 ec a8 00 00 00')
    for opcode in (0x7f, 0x6f):
        for i, reg in enumerate(range(6, 16)):
            code += bytes([0xf3])
            if reg >= 8:
                code += bytes([0x44])
            code += bytes([0x0f, opcode, 0x84 | ((reg & 7) << 3), 0x24])
            code += struct.pack('<I', 16 * i)
        if opcode == 0x7f:
            code += bytes.fromhex('48 89 cf 48 b8') + struct.pack('<Q', target)
            code += bytes.fromhex('ff d0')
    return code + bytes.fromhex('c5 f8 77 48 81 c4 a8 00 00 00 5e 5f c3')


class NativeEvaluator:
    def __init__(self, text, last_page=0xe75b000):
        self.win = C.WinDLL('kernel32', use_last_error=True)
        self.win.VirtualAlloc.argtypes = (C.c_void_p, C.c_size_t, C.c_ulong, C.c_ulong)
        self.win.VirtualAlloc.restype = C.c_void_p
        self.win.VirtualProtect.argtypes = (C.c_void_p, C.c_size_t, C.c_ulong,
                                            C.POINTER(C.c_ulong))
        self.win.VirtualFree.argtypes = (C.c_void_p, C.c_size_t, C.c_ulong)
        self.win.GetCurrentProcess.restype = C.c_void_p
        self.win.FlushInstructionCache.argtypes = (C.c_void_p, C.c_void_p, C.c_size_t)
        self.runtime = C.CDLL('ucrtbase.dll')
        self.start = self.win.VirtualAlloc(None, last_page - BASE, 0x2000, 0x01)
        if not self.start:
            raise C.WinError(C.get_last_error())
        try:
            self._init(text)
        except BaseException:
            self.close()
            raise

    def addr(self, guest):
        return self.start + guest - BASE

    def pages(self, begin, end):
        start = self.addr(begin)
        if self.win.VirtualAlloc(start, end - begin, 0x1000, 0x04) != start:
            raise C.WinError(C.get_last_error())

    def put(self, guest, data):
        C.memmove(self.addr(guest), bytes(data), len(data))

    def protect(self, begin, end, permission):
        previous = C.c_ulong()
        if not self.win.VirtualProtect(self.addr(begin), end - begin, permission,
                                       C.byref(previous)):
            raise C.WinError(C.get_last_error())

    def _init(self, text):
        # Map only the evaluator, its easing functions and referenced constants.
        # The synthetic data table comes from the game's registration routine.
        regions = [(0x75b2000, 0x75b4000), (0x7788000, 0x7789000),
                   (0x778a000, 0x778b000), (0x77a6000, 0x77a7000),
                   (0x77fd000, 0x77fe000), (0x7805000, 0x7806000),
                   (0x7866000, 0x7867000),
                   (0x7de6000, 0x7de9000), (0xe758000, 0xe75b000)]
        for begin, end in regions:
            self.pages(begin, end)
            if end - BASE <= len(text):
                self.put(begin, text[begin-BASE:end-BASE])
        self.put(0x7de6cb8, struct.pack('<Q', self.addr(0x7de6cc0)))
        for table in (0xe758250, 0xe7582a8):
            self.put(table, struct.pack('<11Q', *(self.addr(a) for a in CURVES)))
        for i, (kind, offset) in enumerate(TYPE_AND_OFFSET):
            self.put(0xe7592c0 + 96*i, struct.pack('<I12xQ', kind, offset))

        # Remap the evaluator's four ordinary C library calls to Windows ABI.
        for index, (got, name, args) in enumerate((
            (0x7de6f08, 'strlen', '48 89 f9'),
            (0x7de8558, 'memcpy', '49 89 d0 48 89 f2 48 89 f9'),
            (0x7de6f10, 'acosf', ''), (0x7de8580, 'sinf', ''),
        )):
            stub = 0x75b3e00 + 32*index
            host = C.cast(getattr(self.runtime, name), C.c_void_p).value
            code = bytes.fromhex(args + ' 48 83 ec 28 48 b8') + struct.pack('<Q', host)
            self.put(stub, code + bytes.fromhex('ff d0 48 83 c4 28 c3'))
            self.put(got, struct.pack('<Q', self.addr(stub)))
        wrapper = 0x75b3e80
        self.put(wrapper, to_guest(self.addr(ENTRY)))
        for i, (begin, end) in enumerate(regions):
            self.protect(begin, end, 0x20 if i < 3 else 0x02)
        if not self.win.FlushInstructionCache(self.win.GetCurrentProcess(), self.start, 0):
            raise C.WinError(C.get_last_error())
        self.eval = C.CFUNCTYPE(None, C.c_void_p)(self.addr(wrapper))

    def close(self):
        if self.start:
            self.win.VirtualFree(self.start, 0, 0x8000)
            self.start = None

    def sample(self, clip, frame, *, looping=False, wrapped=False):
        keys = C.create_string_buffer(struct.pack(f'<{len(clip["words"])}I', *clip['words']))
        track_data = b''.join(struct.pack('<4H', *t) for t in clip['descriptors'])
        tracks = C.create_string_buffer(track_data)
        record = C.create_string_buffer(0x70)
        struct.pack_into('<QQQ', record, 0, C.addressof(tracks), len(track_data)//8,
                         len(track_data)//8)
        struct.pack_into('<QQQ', record, 0x18, C.addressof(keys), len(clip['words']),
                         len(clip['words']))
        struct.pack_into('<BBHHHB', record, 0x5a, *clip['header'])
        pose = C.create_string_buffer(0x4300)
        struct.pack_into('<Q', pose, 0x4290, C.addressof(record))
        struct.pack_into('<f', pose, 0x429c, frame/30)
        if looping:
            struct.pack_into('<i', pose, 0x42a4, 1)
            struct.pack_into('<BB', pose, 0x42ac, 1, int(not wrapped))
        self.eval(C.addressof(pose))
        return pose.raw


def main():
    parse = runpy.run_path(str(ROOT / 'read-imp-animation.py'))['parse_bank']
    clips = parse(verified_bytes(ASSET, EXPECTED_BANK))
    evaluator = NativeEvaluator(verified_bytes(GUEST, EXPECTED_TEXT))
    try:
        blink = next(c for c in clips if c['name'] == 'default_blink2')
        for frame, expected in ((0, 0), (3, 1), (7, 0)):
            p = evaluator.sample(blink, frame)
            lids = struct.unpack_from('<2f', p, 0x38)
            if not all(math.isclose(x, expected, abs_tol=2e-6) for x in lids):
                raise ValueError(f'Unexpected native blink at frame {frame}: {lids}')
        samples = 0
        for clip in clips:
            for half_frame in range(clip['header'][2] * 2 + 1):
                pose = evaluator.sample(clip, half_frame * 0.5)
                fields = (0x38, 0x3c, 0x20c0, 0x20c4, 0x20c8, 0x20cc, 0x20d0, 0x20d4)
                if not all(math.isfinite(struct.unpack_from('<f', pose, offset)[0])
                           for offset in fields):
                    raise ValueError(f'Invalid pose in {clip["name"]!r} at frame {half_frame / 2}')
                samples += 1
        print(f'Original evaluator sampled {len(clips)} clips at {samples:,} times. '
              'Both native blink tracks matched at their authored keys.')
    finally:
        evaluator.close()


if __name__ == '__main__':
    main()
