from pathlib import Path
import ctypes as C,subprocess,time
root=Path(__file__).resolve().parents[1]
u=C.WinDLL('user32',use_last_error=True)
u.GetWindowThreadProcessId.argtypes=[C.c_void_p,C.POINTER(C.c_ulong)]
u.PostMessageW.argtypes=[C.c_void_p,C.c_uint,C.c_size_t,C.c_ssize_t]
callback=C.WINFUNCTYPE(C.c_bool,C.c_void_p,C.c_ssize_t)
matches=[]
@callback
def visit(hwnd,param):
    n=u.GetWindowTextLengthW(hwnd);buf=C.create_unicode_buffer(n+1)
    u.GetWindowTextW(hwnd,buf,n+1)
    if buf.value in ('Dreams Imp','Imp Carousel'):matches.append(hwnd)
    return True
u.EnumWindows(visit,0)
for hwnd in matches:u.PostMessageW(hwnd,0x10,0,0)
time.sleep(3)
print('Requested normal picker close:',len(matches))
