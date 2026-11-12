"""Native dragging and edge resizing for the borderless SDL picker."""
import ctypes as C
from pathlib import Path
import pygame
from picker_layout import content_bounds,content_point
FULLSCREEN_EVENT=pygame.USEREVENT+12

def hit_region(x,y,w,h):
    edge=8
    left,right=x<edge,x>=w-edge
    top,bottom=y<edge,y>=h-edge
    if top:return 2 if left else 4 if right else 3
    if bottom:return 8 if left else 6 if right else 7
    if left:return 9
    if right:return 5
    bounds=content_bounds(w,h);x,y=content_point((x,y),bounds);w,h=bounds[2:]
    # The header moves the window; its buttons retain normal client input.
    controls=(.409*w<=x<=.596*w or .888*w<=x<=.952*w) and .047*h<=y<=.17*h
    music_title=.053*w<=x<=.25*w and .083*h<=y<=.14*h
    return 1 if y<.18*h and not controls and not music_title else 0

class PickerWindow:
    def __init__(self):
        self.dll=None;self.window=None;self.callback=None;self.fullscreen=False
        self.hwnd=None;self.old_proc=None;self.proc=None
        if pygame.display.get_driver()=='dummy':return
        from pygame._sdl2.video import Window
        self.dll=C.CDLL(str(Path(pygame.__file__).parent/'SDL2.dll'))
        self.dll.SDL_GetWindowFromID.argtypes=[C.c_uint32];self.dll.SDL_GetWindowFromID.restype=C.c_void_p
        self.dll.SDL_GetWindowSize.argtypes=[C.c_void_p,C.POINTER(C.c_int),C.POINTER(C.c_int)]
        self.dll.SDL_SetWindowMinimumSize.argtypes=[C.c_void_p,C.c_int,C.c_int]
        self.dll.SDL_SetWindowHitTest.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p]
        self.dll.SDL_SetWindowHitTest.restype=C.c_int
        self.dll.SDL_SetWindowFullscreen.argtypes=[C.c_void_p,C.c_uint32]
        self.dll.SDL_SetWindowFullscreen.restype=C.c_int
        class Point(C.Structure):_fields_=[('x',C.c_int),('y',C.c_int)]
        callback=C.CFUNCTYPE(C.c_int,C.c_void_p,C.POINTER(Point),C.c_void_p)
        @callback
        def hit(window,point,data):
            w=C.c_int();h=C.c_int();self.dll.SDL_GetWindowSize(window,C.byref(w),C.byref(h))
            return 0 if self.fullscreen else hit_region(point.contents.x,point.contents.y,w.value,h.value)
        self.callback=hit
        self.bind()
        # SDL routes caption double-clicks through the Windows non-client path.
        # Queue the toggle for the SDL loop, keeping display changes out of WndProc.
        self.user=C.WinDLL('user32',use_last_error=True)
        self.user.SetWindowLongPtrW.argtypes=[C.c_void_p,C.c_int,C.c_void_p];self.user.SetWindowLongPtrW.restype=C.c_void_p
        self.user.GetWindowLongPtrW.argtypes=[C.c_void_p,C.c_int];self.user.GetWindowLongPtrW.restype=C.c_ssize_t
        self.user.SetWindowPos.argtypes=[C.c_void_p,C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_int,C.c_uint]
        from ctypes import wintypes as W
        class MinMax(C.Structure):
            _fields_=[('reserved',W.POINT),('max_size',W.POINT),('max_position',W.POINT),('min_track',W.POINT),('max_track',W.POINT)]
        class Monitor(C.Structure):
            _fields_=[('size',W.DWORD),('monitor',W.RECT),('work',W.RECT),('flags',W.DWORD)]
        self.user.MonitorFromWindow.argtypes=[C.c_void_p,C.c_uint];self.user.MonitorFromWindow.restype=C.c_void_p
        self.user.GetMonitorInfoW.argtypes=[C.c_void_p,C.POINTER(Monitor)]
        self.user.IsZoomed.argtypes=[C.c_void_p]
        self.user.ScreenToClient.argtypes=[C.c_void_p,C.POINTER(W.POINT)]
        self.user.GetClientRect.argtypes=[C.c_void_p,C.POINTER(W.RECT)]
        self.user.DefWindowProcW.argtypes=[C.c_void_p,C.c_uint,C.c_size_t,C.c_ssize_t];self.user.DefWindowProcW.restype=C.c_ssize_t
        self.user.CallWindowProcW.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_size_t,C.c_ssize_t];self.user.CallWindowProcW.restype=C.c_ssize_t
        proc_type=C.WINFUNCTYPE(C.c_ssize_t,C.c_void_p,C.c_uint,C.c_size_t,C.c_ssize_t)
        @proc_type
        def proc(hwnd,message,wp,lp):
            if message==0x84 and not self.fullscreen: # WM_NCHITTEST
                point=W.POINT(C.c_short(lp&0xffff).value,C.c_short((lp>>16)&0xffff).value)
                bounds=W.RECT()
                if self.user.ScreenToClient(hwnd,C.byref(point)) and self.user.GetClientRect(hwnd,C.byref(bounds)):
                    region=hit_region(point.x,point.y,bounds.right,bounds.bottom)
                    return {0:1,1:2,2:13,3:12,4:14,5:11,6:17,7:15,8:16,9:10}[region]
            if message==0xA1 and wp==2 and not self.fullscreen: # caption down
                # SDL's borderless non-client handler can consume this. Let
                # Windows own the standard move/snap loop for our title area.
                return self.user.DefWindowProcW(hwnd,message,wp,lp)
            if message==0x83: # WM_NCCALCSIZE: keep the native frame invisible.
                if wp and lp and not self.fullscreen and self.user.IsZoomed(hwnd):
                    monitor=Monitor();monitor.size=C.sizeof(monitor)
                    if self.user.GetMonitorInfoW(self.user.MonitorFromWindow(hwnd,2),C.byref(monitor)):
                        # Windows puts the thick frame just outside the monitor
                        # when maximized. Keep the client inside its work area.
                        bounds=C.cast(lp,C.POINTER(W.RECT)).contents
                        bounds.left=monitor.work.left;bounds.top=monitor.work.top
                        bounds.right=monitor.work.right;bounds.bottom=monitor.work.bottom
                return 0
            if message==0x24 and lp and not self.fullscreen: # WM_GETMINMAXINFO
                result=self.user.CallWindowProcW(self.old_proc,hwnd,message,wp,lp)
                monitor=Monitor();monitor.size=C.sizeof(monitor)
                if self.user.GetMonitorInfoW(self.user.MonitorFromWindow(hwnd,2),C.byref(monitor)):
                    bounds=C.cast(lp,C.POINTER(MinMax)).contents
                    bounds.max_position=W.POINT(monitor.work.left-monitor.monitor.left,monitor.work.top-monitor.monitor.top)
                    bounds.max_size=W.POINT(monitor.work.right-monitor.work.left,monitor.work.bottom-monitor.work.top)
                    # SDL's borderless handler otherwise fixes both tracking
                    # limits to the current window size, preventing native snap.
                    bounds.min_track=W.POINT(640,420)
                    bounds.max_track=W.POINT(max(bounds.max_size.x,self.user.GetSystemMetrics(59)),max(bounds.max_size.y,self.user.GetSystemMetrics(60)))
                return result
            if message==0xA3 and wp==2: # WM_NCLBUTTONDBLCLK, HTCAPTION
                pygame.event.post(pygame.event.Event(FULLSCREEN_EVENT));return 0
            return self.user.CallWindowProcW(self.old_proc,hwnd,message,wp,lp)
        self.proc=proc;self.hwnd=pygame.display.get_wm_info()['window']
        self.old_proc=self.user.SetWindowLongPtrW(self.hwnd,-4,C.cast(proc,C.c_void_p))
        if not self.old_proc:raise C.WinError(C.get_last_error())
        # A resizable/maximizable native frame lets Windows perform Aero Snap
        # on title drags, including maximizing when dragged to the top edge.
        self.old_style=self.user.GetWindowLongPtrW(self.hwnd,-16)
        self.enable_native_frame()

    def enable_native_frame(self):
        if not self.hwnd:return
        style=self.user.GetWindowLongPtrW(self.hwnd,-16)
        self.user.SetWindowLongPtrW(self.hwnd,-16,style|0x00c00000|0x00040000|0x00010000|0x00020000|0x00080000)
        self.user.SetWindowPos(self.hwnd,None,0,0,0,0,0x0027) # FRAMECHANGED/NOMOVE/NOSIZE/NOZORDER

    def toggle_fullscreen(self):
        if self.dll is None:
            self.fullscreen=not self.fullscreen;return
        desired=not self.fullscreen
        if self.dll.SDL_SetWindowFullscreen(self.window,0x1001 if desired else 0)!=0:
            raise RuntimeError('Fullscreen could not be changed')
        self.fullscreen=desired
        if not desired:self.enable_native_frame()

    def bind(self):
        if self.dll is None:return
        from pygame._sdl2.video import Window
        self.window=self.dll.SDL_GetWindowFromID(Window.from_display_module().id)
        if not self.window:raise RuntimeError('Picker SDL window is unavailable')
        self.dll.SDL_SetWindowMinimumSize(self.window,640,420)
        if self.dll.SDL_SetWindowHitTest(self.window,C.cast(self.callback,C.c_void_p),None)!=0:
            raise RuntimeError('Native picker drag and resize could not be enabled')

    def close(self):
        if self.old_proc:
            self.user.SetWindowLongPtrW(self.hwnd,-4,self.old_proc);self.old_proc=None
        if self.dll is not None and self.window:
            self.dll.SDL_SetWindowHitTest(self.window,None,None)
            self.window=None
