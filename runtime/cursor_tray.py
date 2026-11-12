"""Cursor-owned Windows tray; no picker renderer stays alive after closing."""
import ctypes as C
from ctypes import wintypes as W
import subprocess
import sys
import threading


class CursorTray:
    def __init__(self, root, restore):
        self.root, self.restore = root, restore
        self.hwnd = None
        self.error = None
        self.ready = threading.Event()
        self.thread = threading.Thread(target=self._run, name='Imp tray', daemon=True)
        self.thread.start()
        if not self.ready.wait(5):
            raise RuntimeError('Imp tray did not initialize')
        if self.error:
            raise RuntimeError('Imp tray failed') from self.error

    def _run(self):
        user = C.WinDLL('user32', use_last_error=True)
        shell = C.WinDLL('shell32', use_last_error=True)
        kernel = C.WinDLL('kernel32', use_last_error=True)
        PROC = C.WINFUNCTYPE(C.c_ssize_t, W.HWND, W.UINT, W.WPARAM, W.LPARAM)

        class CLASS(C.Structure):
            _fields_ = [('style', W.UINT), ('proc', PROC), ('extra', C.c_int),
                        ('window_extra', C.c_int), ('instance', W.HINSTANCE),
                        ('icon', W.HICON), ('cursor', W.HANDLE), ('brush', W.HBRUSH),
                        ('menu', W.LPCWSTR), ('name', W.LPCWSTR)]

        class NOTICE(C.Structure):
            _fields_ = [('size', W.DWORD), ('hwnd', W.HWND), ('id', W.UINT),
                        ('flags', W.UINT), ('callback', W.UINT), ('icon', W.HICON),
                        ('tip', W.WCHAR * 128), ('state', W.DWORD), ('mask', W.DWORD),
                        ('info', W.WCHAR * 256), ('version', W.UINT),
                        ('title', W.WCHAR * 64), ('info_flags', W.DWORD),
                        ('guid', C.c_byte * 16), ('balloon', W.HICON)]

        user.DefWindowProcW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
        user.DefWindowProcW.restype = C.c_ssize_t
        user.CreateWindowExW.argtypes = [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD,
            C.c_int, C.c_int, C.c_int, C.c_int, W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID]
        user.CreateWindowExW.restype = W.HWND
        user.RegisterClassW.argtypes = [C.POINTER(CLASS)]
        user.CreatePopupMenu.restype = W.HMENU
        user.AppendMenuW.argtypes = [W.HMENU, W.UINT, C.c_size_t, W.LPCWSTR]
        user.TrackPopupMenu.argtypes = [W.HMENU, W.UINT, C.c_int, C.c_int, C.c_int, W.HWND, W.LPVOID]
        user.DestroyMenu.argtypes = [W.HMENU]
        user.DestroyWindow.argtypes = [W.HWND]
        user.IsWindow.argtypes = [W.HWND]
        user.UnregisterClassW.argtypes = [W.LPCWSTR, W.HINSTANCE]
        user.RegisterWindowMessageW.argtypes = [W.LPCWSTR]
        user.GetMessageW.argtypes = [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT]
        user.DispatchMessageW.argtypes = [C.POINTER(W.MSG)]
        user.DispatchMessageW.restype = C.c_ssize_t
        user.SetForegroundWindow.argtypes = [W.HWND]
        user.LoadImageW.argtypes = [W.HINSTANCE, W.LPCWSTR, W.UINT, C.c_int, C.c_int, W.UINT]
        user.LoadImageW.restype = W.HANDLE
        user.DestroyIcon.argtypes = [W.HICON]
        user.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
        shell.Shell_NotifyIconW.argtypes = [W.DWORD, C.POINTER(NOTICE)]
        kernel.GetModuleHandleW.restype = W.HMODULE
        instance = kernel.GetModuleHandleW(None)
        taskbar = user.RegisterWindowMessageW('TaskbarCreated')
        notice = NOTICE()

        def choose():
            exe = self.root.parent / 'Dreams Imp.exe'
            command = [str(exe)] if exe.exists() else [sys.executable, str(self.root / 'app.py')]
            subprocess.Popen(command, cwd=self.root, creationflags=subprocess.CREATE_NO_WINDOW)

        def callback(hwnd, message, wparam, lparam):
            if message == taskbar:
                shell.Shell_NotifyIconW(0, C.byref(notice))
                return 0
            if message == 0x8001:
                if lparam == 0x203:
                    choose()
                elif lparam in (0x205, 0x7b):
                    point = W.POINT()
                    user.GetCursorPos(C.byref(point))
                    menu = user.CreatePopupMenu()
                    try:
                        user.AppendMenuW(menu, 0, 1, 'Choose Imp…')
                        user.AppendMenuW(menu, 0, 2, 'Restore Windows cursor')
                        user.AppendMenuW(menu, 0x800, 0, None)
                        user.AppendMenuW(menu, 0, 3, 'Exit')
                        user.SetForegroundWindow(hwnd)
                        choice = user.TrackPopupMenu(menu, 0x100 | 2, point.x, point.y, 0, hwnd, None)
                        if choice == 1: choose()
                        elif choice == 2: self.restore()
                        elif choice == 3:
                            from app_lifecycle import request_exit
                            request_exit()
                            self.restore()
                        user.PostMessageW(hwnd, 0, 0, 0)
                    finally:
                        user.DestroyMenu(menu)
                return 0
            if message == 0x10:
                user.DestroyWindow(hwnd)
                return 0
            if message == 2:
                user.PostQuitMessage(0)
                return 0
            return user.DefWindowProcW(hwnd, message, wparam, lparam)

        proc = PROC(callback)
        name = 'DreamsImpCursorTray'
        icon = None
        try:
            cls = CLASS(0, proc, 0, 0, instance, None, None, None, None, name)
            if not user.RegisterClassW(C.byref(cls)):
                raise C.WinError(C.get_last_error())
            self.hwnd = user.CreateWindowExW(0, name, '', 0, 0, 0, 0, 0, None, None, instance, None)
            if not self.hwnd: raise C.WinError(C.get_last_error())
            icon = user.LoadImageW(None, str(self.root / 'app.ico'), 1, 0, 0, 0x10)
            notice.size = C.sizeof(NOTICE)
            notice.hwnd, notice.id, notice.flags = self.hwnd, 1, 7
            notice.callback, notice.icon, notice.tip = 0x8001, icon, 'Dreams Imp'
            if not shell.Shell_NotifyIconW(0, C.byref(notice)):
                raise C.WinError(C.get_last_error())
            self.ready.set()
            message = W.MSG()
            while user.GetMessageW(C.byref(message), None, 0, 0) > 0:
                user.TranslateMessage(C.byref(message))
                user.DispatchMessageW(C.byref(message))
        except BaseException as error:
            self.error = error
            self.ready.set()
            self.restore()
        finally:
            shell.Shell_NotifyIconW(2, C.byref(notice))
            if self.hwnd and user.IsWindow(self.hwnd): user.DestroyWindow(self.hwnd)
            self.hwnd = None
            if icon: user.DestroyIcon(icon)
            user.UnregisterClassW(name, instance)

    def close(self):
        if self.hwnd:
            user = C.WinDLL('user32')
            user.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
            user.PostMessageW(self.hwnd, 0x10, 0, 0)
        self.thread.join(timeout=2)
