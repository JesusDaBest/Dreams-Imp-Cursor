"""Idle schedules and clip groups read from Dreams' Imp update code."""
import random
import struct

PRIMARY = ('idle roll eye', 'idle stretch', 'idle yawn', 'idle happy')
SECONDARY = ('idle sneeze', 'idle bored', 'idle bored look', 'idle roll eye')
def f32(value):
    return struct.unpack('<f',struct.pack('<f',value))[0]
class NativeIdle:
    def __init__(self, seed=None):
        self.seed = random.getrandbits(30) if seed is None else seed & 0x3fffffff
        self.previous = {PRIMARY:None,SECONDARY:None}
    def advance(self):
        self.seed = (self.seed * 0x2e90edd + 0xe908fc1) & 0x3fffffff
        return self.seed
    def delay(self, rare=False):
        # 0x75f3af1–0x75f3b24 and 0x75f5605–0x75f563c.
        unit = f32(f32(self.advance() >> 16) * 6.103888154029846e-05)
        return f32(f32(unit * (120. if rare else 15.)) + (120. if rare else 10.))
    def clip(self, rare=False):
        # Original two-bit rejection selection: never repeat the previous item
        # in the same group (0x75f5440 and 0x75f57c0).
        clips = SECONDARY if rare else PRIMARY
        while True:
            index = self.advance() >> 28
            if index != self.previous[clips]:break
        self.previous[clips] = index
        return clips[index]
    def blink_delay(self):
        # 0x75f75ec–0x75f761f: rand * 2^-30 * 3 + .25.
        # The stream is local to the desktop app; it does not reuse a game's
        # process-global random state.
        return f32(f32(f32(random.getrandbits(31)) * 9.313225746154785e-10) * 3 + .25)
