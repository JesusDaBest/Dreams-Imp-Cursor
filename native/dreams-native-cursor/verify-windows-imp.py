"""Verify the installed layer and cursor restoration without launching Dreams."""
import ctypes as C
from ctypes import wintypes as W
import hashlib
from pathlib import Path
import subprocess
import sys
import time

USER = C.WinDLL('user32', use_last_error=True)
GDI = C.WinDLL('gdi32', use_last_error=True)


class Icon(C.Structure):
    _fields_ = [('icon', W.BOOL), ('x', W.DWORD), ('y', W.DWORD),
                ('mask', W.HANDLE), ('color', W.HANDLE)]


class Bitmap(C.Structure):
    _fields_ = [('kind', W.LONG), ('width', W.LONG), ('height', W.LONG),
                ('row', W.LONG), ('planes', W.WORD), ('bpp', W.WORD), ('bits', C.c_void_p)]


def arrow():
    icon = Icon()
    handle = USER.LoadCursorW(None, 32512)
    if not USER.GetIconInfo(handle, C.byref(icon)):
        raise C.WinError(C.get_last_error())
    result = []
    for bitmap_handle in (icon.mask, icon.color):
        if not bitmap_handle:
            continue
        try:
            bitmap = Bitmap()
            if not GDI.GetObjectW(bitmap_handle, C.sizeof(bitmap), C.byref(bitmap)):
                raise C.WinError(C.get_last_error())
            pixels = C.create_string_buffer(bitmap.row*bitmap.height)
            count = GDI.GetBitmapBits(bitmap_handle, len(pixels), pixels)
            result.append(hashlib.sha256(pixels.raw[:count]).hexdigest())
        finally:
            GDI.DeleteObject(bitmap_handle)
    return result


def until(test, description):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        result = test()
        if result:
            return result
        time.sleep(.05)
    raise TimeoutError(description)


def main(runtime):
    USER.LoadCursorW.argtypes = W.HINSTANCE, C.c_void_p
    USER.LoadCursorW.restype = W.HANDLE
    USER.GetIconInfo.argtypes = W.HANDLE, C.POINTER(Icon)
    USER.FindWindowW.argtypes = W.LPCWSTR, W.LPCWSTR
    USER.FindWindowW.restype = W.HWND
    USER.IsWindowVisible.argtypes = W.HWND,
    USER.GetWindowRect.argtypes = W.HWND, C.POINTER(W.RECT)
    GDI.GetObjectW.argtypes = W.HANDLE, C.c_int, C.c_void_p
    GDI.GetBitmapBits.argtypes = W.HANDLE, W.LONG, C.c_void_p
    GDI.DeleteObject.argtypes = W.HANDLE,
    initial = arrow()
    for forced in (False, True):
        with runtime.with_name('guard-test.log').open('w') as log:
            process = subprocess.Popen([sys.executable, '-u', str(runtime), '--run'],
                                       stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                def visible():
                    hwnd = USER.FindWindowW('Static', 'Dreams Standalone Imp')
                    return hwnd if hwnd and USER.IsWindowVisible(hwnd) else None

                hwnd = until(visible, 'Standalone overlay did not appear')
                until(lambda: arrow() != initial, 'The original arrow was not replaced')
                rect = W.RECT()
                assert USER.GetWindowRect(hwnd, C.byref(rect))
                assert (rect.right-rect.left, rect.bottom-rect.top) == (160, 160)
                if not forced:
                    USER.SystemParametersInfoW.argtypes = W.UINT, W.UINT, C.c_void_p, W.UINT
                    assert USER.SystemParametersInfoW(0x57, 0, None, 0)
                    until(lambda: arrow() != initial, 'Arrow became visible after a Windows cursor reload')
                    print('The Imp hid the arrow again after a Windows cursor reload', flush=True)
                if forced:
                    process.kill()
                else:
                    subprocess.run([sys.executable, str(runtime), '--stop'], check=True)
                process.wait(8)
                until(lambda: arrow() == initial, 'The original arrow did not restore')
                print('160×160 layer and arrow restoration passed after',
                      'forced exit' if forced else 'normal Stop', flush=True)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    main(Path(sys.argv[1]))
