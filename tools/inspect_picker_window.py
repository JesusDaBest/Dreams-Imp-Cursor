"""Read-only native window bounds; no focus, mouse, keyboard or screenshots."""
import ctypes as C,json
from ctypes import wintypes as W
u=C.WinDLL('user32',use_last_error=True)
u.GetWindowTextLengthW.argtypes=[W.HWND]
u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
u.GetWindowRect.argtypes=[W.HWND,C.POINTER(W.RECT)]
u.MonitorFromWindow.argtypes=[W.HWND,W.DWORD]
u.MonitorFromWindow.restype=W.HANDLE
class Monitor(C.Structure):
    _fields_=[('size',W.DWORD),('monitor',W.RECT),('work',W.RECT),('flags',W.DWORD)]
u.GetMonitorInfoW.argtypes=[W.HANDLE,C.POINTER(Monitor)]
rows=[]
@C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
def visit(hwnd,_):
    n=u.GetWindowTextLengthW(hwnd);name=C.create_unicode_buffer(n+1)
    u.GetWindowTextW(hwnd,name,n+1)
    if name.value=='Dreams Imp':
        bounds=W.RECT();assert u.GetWindowRect(hwnd,C.byref(bounds))
        m=Monitor();m.size=C.sizeof(m)
        assert u.GetMonitorInfoW(u.MonitorFromWindow(hwnd,2),C.byref(m))
        rect=lambda r:[r.left,r.top,r.right,r.bottom]
        rows.append(dict(title=name.value,window=rect(bounds),monitor=rect(m.monitor),
                         fullscreen=rect(bounds)==rect(m.monitor)))
    return True
u.EnumWindows(visit,0)
print(json.dumps(rows))
