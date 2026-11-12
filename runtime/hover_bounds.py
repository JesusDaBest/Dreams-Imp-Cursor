"""Publish the picker's actual hit rectangles without accessibility polling or files."""
import ctypes as C
from ctypes import wintypes as W
import mmap
import struct
import time

FORMAT = struct.Struct('<d4iQ')
class HoverBounds:
    def __init__(self):
        self.memory = mmap.mmap(-1, 64, tagname='Local\\DreamsImp.PickerHover')
        self.user = C.WinDLL('user32', use_last_error=True)
        self.user.ClientToScreen.argtypes = (W.HWND, C.POINTER(W.POINT))
        self.user.WindowFromPoint.argtypes = (W.POINT,)
        self.user.WindowFromPoint.restype = W.HWND

    def publish(self, hwnd, rect):
        if hwnd and rect is not None:
            origin = W.POINT(0, 0)
            if not self.user.ClientToScreen(hwnd, C.byref(origin)):
                return
            left, top, width, height = rect
            record = (time.monotonic(), origin.x+left, origin.y+top,
                      origin.x+left+width, origin.y+top+height, hwnd)
        else:
            record = (0., 0, 0, 0, 0, 0)
        self.memory[:FORMAT.size] = FORMAT.pack(*record)

    def hit(self, x, y):
        sample = FORMAT.unpack(self.memory[:FORMAT.size])
        stamp, left, top, right, bottom, hwnd = sample
        if (time.monotonic()-stamp < .25 and left <= x < right and top <= y < bottom
                and self.user.WindowFromPoint(W.POINT(x,y)) == hwnd):
            return (stamp, left, top, right, bottom)
        return None

    def close(self):
        self.memory.close()
