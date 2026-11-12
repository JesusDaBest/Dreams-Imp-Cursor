"""Present premultiplied Imp frames in a click-through Windows desktop window."""
import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import NamedTuple

STOP_EVENT = 'Local\\DreamsStandaloneImp.Stop'
ACTIVE_MUTEX = 'Local\\DreamsStandaloneImp.Active'
ARROW = 32512
CURSOR_SHOWING = 1
MENU_START = 4
MENU_POPUP_END = 7
SYSTEM_ROLES = (ARROW, 32513, 32514, 32515, 32516, 32642, 32643, 32644, 32645,
                32646, 32648, 32649, 32650, 32651, 32671, 32672)

class MouseState(NamedTuple):
    x: int
    y: int
    visible: bool
    role: int
    primary: bool = False
    primary_down: bool = False
    secondary: bool = False
    secondary_down: bool = False
    middle: bool = False
    middle_down: bool = False
    back: bool = False
    forward: bool = False
    wheel: int = 0
    wheel_horizontal: int = 0
    shift: bool = False
    ctrl: bool = False
    menu_event: int = 0
    alt: bool = False


class RawInputDevice(C.Structure):
    _fields_ = [('page', W.USHORT), ('usage', W.USHORT), ('flags', W.DWORD),
                ('window', W.HWND)]


class RawInputHeader(C.Structure):
    _fields_ = [('kind', W.DWORD), ('size', W.DWORD), ('device', W.HANDLE),
                ('parameter', W.WPARAM)]


class RawMouse(C.Structure):
    _fields_ = [('flags', W.USHORT), ('padding', W.USHORT), ('buttons', W.USHORT),
                ('delta', C.c_short), ('raw_buttons', W.ULONG), ('x', W.LONG),
                ('y', W.LONG), ('extra', W.ULONG)]


class RawInput(C.Structure):
    _fields_ = [('header', RawInputHeader), ('mouse', RawMouse)]


class CursorInfo(C.Structure):
    _fields_ = [('size', W.DWORD), ('flags', W.DWORD), ('cursor', W.HANDLE), ('point', W.POINT)]


class BitmapHeader(C.Structure):
    _fields_ = [('size', W.DWORD), ('width', W.LONG), ('height', W.LONG),
                ('planes', W.WORD), ('bits', W.WORD), ('compression', W.DWORD),
                ('bytes', W.DWORD), ('x', W.LONG), ('y', W.LONG),
                ('colors', W.DWORD), ('important', W.DWORD)]


class Blend(C.Structure):
    _fields_ = [('operation', W.BYTE), ('flags', W.BYTE), ('alpha', W.BYTE), ('format', W.BYTE)]


class IconInfo(C.Structure):
    _fields_ = [('icon', W.BOOL), ('x', W.DWORD), ('y', W.DWORD),
                ('mask', W.HANDLE), ('color', W.HANDLE)]


class BitmapInfo(C.Structure):
    _fields_ = [('kind', W.LONG), ('width', W.LONG), ('height', W.LONG),
                ('stride', W.LONG), ('planes', W.WORD), ('bits_per_pixel', W.WORD),
                ('pixels', C.c_void_p)]


def bind(dll, name, result, *arguments):
    method = getattr(dll, name)
    method.restype = result
    method.argtypes = arguments
    return method


class Overlay:
    def __init__(self, replace_arrow, width, height):
        self.win = C.WinDLL('user32', use_last_error=True)
        self.gdi = C.WinDLL('gdi32', use_last_error=True)
        self.kernel = C.WinDLL('kernel32', use_last_error=True)
        self.stop_event = self.mutex = self.window = self.dc = self.bitmap = self.previous = None
        self.arrow_hidden = False
        self.check_cursor_at = 0.0
        self.watch_done = None
        self.menu_hook = None
        self.menu_event = 0
        self.replace_arrow = replace_arrow
        self.size = W.SIZE(width, height)
        self.pixel_bytes = width * height * 4
        self.pos = W.POINT()
        self.visible = False
        self.input_available = True
        self.next_z_check = 0.0
        self.win.SetProcessDpiAwarenessContext(C.c_void_p(-4))
        try:
            self._initialize()
        except BaseException:
            self.close()
            raise

    def _initialize(self):
        u, k, g = self.win, self.kernel, self.gdi
        create_mutex = bind(k, 'CreateMutexW', W.HANDLE, C.c_void_p, W.BOOL, W.LPCWSTR)
        self.mutex = create_mutex(None, False, ACTIVE_MUTEX)
        if not self.mutex or C.get_last_error() == 183:
            raise RuntimeError('The standalone Imp is already running')
        create_event = bind(k, 'CreateEventW', W.HANDLE, C.c_void_p, W.BOOL, W.BOOL, W.LPCWSTR)
        self.stop_event = create_event(None, True, False, STOP_EVENT)
        bind(k, 'WaitForSingleObject', W.DWORD, W.HANDLE, W.DWORD)
        create_window = bind(u, 'CreateWindowExW', W.HWND, W.DWORD, W.LPCWSTR,
            W.LPCWSTR, W.DWORD, C.c_int, C.c_int, C.c_int, C.c_int,
            W.HWND, W.HANDLE, W.HINSTANCE, C.c_void_p)
        styles = 0x80000 | 0x20 | 0x8000000 | 0x80 | 8
        self.window = create_window(styles, 'Static', 'Dreams Standalone Imp',
                                    0x80000000, 0, 0, self.size.cx, self.size.cy, None, None, None, None)
        if not self.window:
            raise C.WinError(C.get_last_error())
        create_dc = bind(g, 'CreateCompatibleDC', W.HDC, W.HDC)
        self.dc = create_dc(None)
        header = BitmapHeader(C.sizeof(BitmapHeader), self.size.cx, -self.size.cy, 1, 32)
        self.pixels = C.c_void_p()
        create_bitmap = bind(g, 'CreateDIBSection', W.HANDLE, W.HDC, C.POINTER(BitmapHeader),
                             W.UINT, C.POINTER(C.c_void_p), W.HANDLE, W.DWORD)
        self.bitmap = create_bitmap(self.dc, C.byref(header), 0, C.byref(self.pixels), None, 0)
        self.previous = bind(g, 'SelectObject', W.HANDLE, W.HDC, W.HANDLE)(self.dc, self.bitmap)
        if not (self.stop_event and self.dc and self.bitmap and self.previous):
            raise C.WinError(C.get_last_error())
        bind(u, 'UpdateLayeredWindow', W.BOOL, W.HWND, W.HDC, C.POINTER(W.POINT),
             C.POINTER(W.SIZE), W.HDC, C.POINTER(W.POINT), W.DWORD, C.POINTER(Blend), W.DWORD)
        bind(u, 'GetCursorInfo', W.BOOL, C.POINTER(CursorInfo))
        bind(u, 'GetCursorPos', W.BOOL, C.POINTER(W.POINT))
        bind(u, 'LoadCursorW', W.HANDLE, W.HINSTANCE, C.c_void_p)
        bind(u, 'GetIconInfo', W.BOOL, W.HANDLE, C.POINTER(IconInfo))
        bind(g, 'GetObjectW', C.c_int, W.HANDLE, C.c_int, C.c_void_p)
        bind(g, 'GetBitmapBits', W.LONG, W.HANDLE, W.LONG, C.c_void_p)
        bind(g, 'DeleteObject', W.BOOL, W.HANDLE)
        self._refresh_roles()
        bind(u, 'ShowWindow', W.BOOL, W.HWND, C.c_int)
        bind(u, 'GetWindow', W.HWND, W.HWND, W.UINT)
        bind(u, 'SetWindowPos', W.BOOL, W.HWND, W.HWND, C.c_int, C.c_int,
             C.c_int, C.c_int, W.UINT)
        bind(u, 'GetAsyncKeyState', C.c_short, C.c_int)
        bind(u, 'PeekMessageW', W.BOOL, C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT, W.UINT)
        self.raw_input = RawInput()
        bind(u, 'GetRawInputData', W.UINT, W.HANDLE, W.UINT, C.c_void_p,
             C.POINTER(W.UINT), W.UINT)
        register_raw = bind(u, 'RegisterRawInputDevices', W.BOOL,
                            C.POINTER(RawInputDevice), W.UINT, W.UINT)
        # Listen in the background while preserving normal mouse delivery to apps.
        device = RawInputDevice(1, 2, 0x100, self.window)
        if not register_raw(C.byref(device), 1, C.sizeof(device)):
            raise C.WinError(C.get_last_error())
        event_proc = C.WINFUNCTYPE(None, W.HANDLE, W.DWORD, W.HWND, W.LONG,
                                    W.LONG, W.DWORD, W.DWORD)
        self.menu_callback = event_proc(self._menu_changed)
        hook = bind(u, 'SetWinEventHook', W.HANDLE, W.DWORD, W.DWORD, W.HANDLE,
                    event_proc, W.DWORD, W.DWORD, W.DWORD)
        self.menu_hook = hook(MENU_START, MENU_POPUP_END, None, self.menu_callback, 0, 0, 2)
        self.double_click = (u.GetDoubleClickTime() / 1000,
                             max(1, u.GetSystemMetrics(36) // 2),
                             max(1, u.GetSystemMetrics(37) // 2))
        self.swapped_buttons = bool(u.GetSystemMetrics(23))
        bind(u, 'TranslateMessage', W.BOOL, C.POINTER(W.MSG))
        bind(u, 'DispatchMessageW', W.LPARAM, C.POINTER(W.MSG))
        self.blend = Blend(0, 0, 255, 1)
        self.zero = W.POINT(0, 0)

    def _menu_changed(self, hook, event, window, obj, child, thread, timestamp):
        self.menu_event = 1 if event in (4, 6) else -1

    def state(self):
        message = W.MSG()
        buttons = wheel = horizontal = 0
        while self.win.PeekMessageW(C.byref(message), None, 0, 0, 1):
            if message.message == 0x12:
                return None
            if message.message == 0xff:
                size = W.UINT(C.sizeof(self.raw_input))
                count = self.win.GetRawInputData(message.lParam, 0x10000003,
                    C.byref(self.raw_input), C.byref(size), C.sizeof(RawInputHeader))
                if count == C.sizeof(self.raw_input) and self.raw_input.header.kind == 0:
                    mouse = self.raw_input.mouse
                    buttons |= mouse.buttons
                    if mouse.buttons & 0x0400:
                        wheel += mouse.delta
                    if mouse.buttons & 0x0800:
                        horizontal += mouse.delta
            self.win.TranslateMessage(C.byref(message))
            self.win.DispatchMessageW(C.byref(message))
        if self.kernel.WaitForSingleObject(self.stop_event, 0) == 0:
            return None
        info = CursorInfo(C.sizeof(CursorInfo))
        if not self.win.GetCursorInfo(C.byref(info)):
            error = C.get_last_error()
            if error == 5:
                return self._suspend_input()
            raise C.WinError(error)
        visible = self.win.GetCursorPos(C.byref(self.pos))
        if not visible:
            error = C.get_last_error()
            if error == 5:
                return self._suspend_input()
            raise C.WinError(error)
        self.input_available = True
        if self.arrow_hidden:
            now = time.monotonic()
            if now >= self.check_cursor_at:
                self._hide_system_roles()
                self.check_cursor_at = now + .25
                if not self.input_available:
                    return MouseState(self.pos.x, self.pos.y, False, 0)
        role = self.roles.get(info.cursor, 0)
        # Replacing a cursor's pixels with transparency does not hide it in
        # Windows. Honour the application's actual cursor visibility state.
        visible = bool(info.flags & CURSOR_SHOWING) and bool(info.cursor)
        if self.replace_arrow:
            # Yield to custom cursors that this overlay did not replace.
            visible = visible and role in self.hidden_roles
        left = self.win.GetAsyncKeyState(1)
        right = self.win.GetAsyncKeyState(2)
        middle = self.win.GetAsyncKeyState(4)
        left_down, right_down = bool(buttons & 0x01 or left & 1), bool(buttons & 0x04 or right & 1)
        if self.swapped_buttons:
            left, right = right, left
            left_down, right_down = right_down, left_down
        menu_event, self.menu_event = self.menu_event, 0
        return MouseState(self.pos.x, self.pos.y, bool(visible), role,
                          left < 0, left_down, right < 0, right_down,
                          middle < 0, bool(buttons & 0x10 or middle & 1),
                          bool(buttons & 0x40 or self.win.GetAsyncKeyState(5) & 1),
                          bool(buttons & 0x100 or self.win.GetAsyncKeyState(6) & 1),
                          wheel, horizontal, self.win.GetAsyncKeyState(0x10) < 0,
                          self.win.GetAsyncKeyState(0x11) < 0, menu_event,
                          self.win.GetAsyncKeyState(0x12) < 0)

    def _suspend_input(self):
        # Windows denies these reads on unavailable/protected input desktops.
        # Do not switch desktops or elevate. Yield and retry the same API later.
        self.input_available = False
        self.menu_event = 0
        if self.visible:
            self.win.ShowWindow(self.window, 0)
            self.visible = False
        if self.arrow_hidden and restore_cursor():
            self.arrow_hidden = False
            self.hidden_roles.clear()
        return MouseState(self.pos.x, self.pos.y, False, 0)

    def _refresh_roles(self):
        self.roles = {}
        self.hidden_roles = set()
        for mode in SYSTEM_ROLES:
            cursor = self.win.LoadCursorW(None, mode)
            if cursor:
                self.roles[cursor] = mode

    def _hide_system_roles(self):
        self._refresh_roles()
        for role in self.roles.values():
            if self._ensure_hidden(role):
                self.hidden_roles.add(role)
            if not self.input_available:
                break

    def resize(self, width, height):
        if (width,height)==(self.size.cx,self.size.cy):return
        header=BitmapHeader(C.sizeof(BitmapHeader),width,-height,1,32)
        pixels=C.c_void_p()
        bitmap=self.gdi.CreateDIBSection(self.dc,C.byref(header),0,C.byref(pixels),None,0)
        if not bitmap:raise C.WinError(C.get_last_error())
        old=self.gdi.SelectObject(self.dc,bitmap)
        self.gdi.DeleteObject(old)
        self.bitmap=bitmap;self.pixels=pixels
        self.size=W.SIZE(width,height);self.pixel_bytes=width*height*4

    def present(self, bgra, pointer, hotspot, visible):
        if not self.input_available:
            return
        if self.replace_arrow and not self.arrow_hidden:
            if not self.watch_done:
                self._start_cursor_guard()
            self.arrow_hidden = True
            self._hide_system_roles()
            self.check_cursor_at = time.monotonic() + .25
            if not self.input_available:
                return
        if not visible:
            if self.visible:
                self.win.ShowWindow(self.window, 0)
                self.visible = False
            return
        C.memmove(self.pixels, bgra, self.pixel_bytes)
        dst = W.POINT(pointer[0]-hotspot[0], pointer[1]-hotspot[1])
        if not self.win.UpdateLayeredWindow(self.window, None, C.byref(dst), C.byref(self.size),
                                            self.dc, C.byref(self.zero), 0, C.byref(self.blend), 2):
            error = C.get_last_error()
            if error == 5:
                self._suspend_input()
                return
            raise C.WinError(error)
        if not self.visible:
            self.win.ShowWindow(self.window, 8)
            self.visible = True
            self.next_z_check = 0.0
        now = time.monotonic()
        if now >= self.next_z_check:
            self.next_z_check = now + .1
            if self.win.GetWindow(self.window, 3):  # GW_HWNDPREV
                flags = 0x0001 | 0x0002 | 0x0010 | 0x0200
                self.win.SetWindowPos(self.window, W.HWND(-1), 0, 0, 0, 0, flags)

    def _start_cursor_guard(self):
        k, u = self.kernel, self.win
        name = f'Local\\DreamsStandaloneImp.CursorGuard.{os.getpid()}'
        create_event = bind(k, 'CreateEventW', W.HANDLE, C.c_void_p, W.BOOL, W.BOOL, W.LPCWSTR)
        ready = create_event(None, True, False, name+'.Ready')
        self.watch_done = create_event(None, True, False, name+'.Done')
        try:
            subprocess.Popen([sys.executable, str(Path(__file__).with_name('desktop-imp.py')),
                              '--watch', str(os.getpid()), name],
                             creationflags=subprocess.CREATE_NO_WINDOW)
            if not ready or not self.watch_done or k.WaitForSingleObject(ready, 4000) != 0:
                raise RuntimeError('Windows cursor recovery guard did not start')
        finally:
            if ready:
                bind(k, 'CloseHandle', W.BOOL, W.HANDLE)(ready)

    def _is_transparent(self, cursor):
        info = IconInfo()
        if not cursor or not self.win.GetIconInfo(cursor, C.byref(info)):
            return False
        try:
            bitmap = BitmapInfo()
            if info.color or not info.mask or not self.gdi.GetObjectW(info.mask, C.sizeof(bitmap), C.byref(bitmap)):
                return False
            size = bitmap.stride * bitmap.height
            if not 0 < size <= 65536 or size % 2:
                return False
            pixels = C.create_string_buffer(size)
            if self.gdi.GetBitmapBits(info.mask, size, pixels) != size:
                return False
            half = size // 2
            return pixels.raw[:half] == b'\xff' * half and pixels.raw[half:] == bytes(half)
        finally:
            for handle in (info.mask, info.color):
                if handle:
                    self.gdi.DeleteObject(handle)

    def _ensure_hidden(self, role):
        u = self.win
        cursor = u.LoadCursorW(None, role)
        if not cursor:
            return False
        if self._is_transparent(cursor):
            return True
        width, height = u.GetSystemMetrics(13), u.GetSystemMetrics(14)
        mask_bytes = ((width+15)//16)*2*height
        and_mask = C.create_string_buffer(b'\xff'*mask_bytes)
        xor_mask = C.create_string_buffer(mask_bytes)
        make_cursor = bind(u, 'CreateCursor', W.HANDLE, W.HINSTANCE, C.c_int, C.c_int,
                           C.c_int, C.c_int, C.c_void_p, C.c_void_p)
        cursor = make_cursor(None, 0, 0, width, height, and_mask, xor_mask)
        if not cursor:
            raise C.WinError(C.get_last_error())
        if not bind(u, 'SetSystemCursor', W.BOOL, W.HANDLE, W.DWORD)(cursor, role):
            error = C.get_last_error()
            bind(u, 'DestroyCursor', W.BOOL, W.HANDLE)(cursor)
            if error == 5:
                self._suspend_input()
                return False
            if error in (0, 87, 1402):
                return False
            raise C.WinError(error)
        return True

    def close(self):
        if self.menu_hook:
            bind(self.win, 'UnhookWinEvent', W.BOOL, W.HANDLE)(self.menu_hook)
        if self.arrow_hidden:
            restore_cursor()
        if self.watch_done:
            bind(self.kernel, 'SetEvent', W.BOOL, W.HANDLE)(self.watch_done)
        if self.window:
            bind(self.win, 'DestroyWindow', W.BOOL, W.HWND)(self.window)
        if self.dc:
            if self.previous:
                self.gdi.SelectObject(self.dc, self.previous)
            if self.bitmap:
                bind(self.gdi, 'DeleteObject', W.BOOL, W.HANDLE)(self.bitmap)
            bind(self.gdi, 'DeleteDC', W.BOOL, W.HDC)(self.dc)
        close = bind(self.kernel, 'CloseHandle', W.BOOL, W.HANDLE)
        for handle in (self.stop_event, self.mutex, self.watch_done):
            if handle:
                close(handle)


def stop():
    kernel = C.WinDLL('kernel32', use_last_error=True)
    handle = bind(kernel, 'OpenEventW', W.HANDLE, W.DWORD, W.BOOL, W.LPCWSTR)(2, False, STOP_EVENT)
    if not handle:
        return False
    try:
        return bool(bind(kernel, 'SetEvent', W.BOOL, W.HANDLE)(handle))
    finally:
        bind(kernel, 'CloseHandle', W.BOOL, W.HANDLE)(handle)


def restore_cursor():
    user = C.WinDLL('user32', use_last_error=True)
    return bool(bind(user, 'SystemParametersInfoW', W.BOOL, W.UINT, W.UINT, C.c_void_p,
                     W.UINT)(0x57, 0, None, 0))


def watch(parent, name):
    kernel = C.WinDLL('kernel32', use_last_error=True)
    open_event = bind(kernel, 'OpenEventW', W.HANDLE, W.DWORD, W.BOOL, W.LPCWSTR)
    open_process = bind(kernel, 'OpenProcess', W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
    close = bind(kernel, 'CloseHandle', W.BOOL, W.HANDLE)
    process = open_process(0x100000, False, parent)
    ready = open_event(2, False, name+'.Ready')
    done = open_event(0x100000, False, name+'.Done')
    try:
        if not (process and ready and done):
            return
        bind(kernel, 'SetEvent', W.BOOL, W.HANDLE)(ready)
        wait = bind(kernel, 'WaitForMultipleObjects', W.DWORD, W.DWORD,
                    C.POINTER(W.HANDLE), W.BOOL, W.DWORD)
        handles = (W.HANDLE*2)(done, process)
        if wait(2, handles, False, 0xffffffff) == 1:
            restore_cursor()
    finally:
        for handle in (done, ready, process):
            if handle:
                close(handle)
