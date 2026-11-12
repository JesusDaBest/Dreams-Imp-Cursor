"""Shared Exit request and explicit normal-picker-close acknowledgement."""
import ctypes as C
from ctypes import wintypes as W
import os

EXIT_EVENT='Local\\DreamsImp.Exit'

def event(name,signal=False):
    if not name:return False
    kernel=C.WinDLL('kernel32',use_last_error=True)
    kernel.OpenEventW.argtypes=(W.DWORD,W.BOOL,W.LPCWSTR)
    kernel.OpenEventW.restype=W.HANDLE
    kernel.CloseHandle.argtypes=(W.HANDLE,)
    kernel.SetEvent.argtypes=(W.HANDLE,)
    kernel.WaitForSingleObject.argtypes=(W.HANDLE,W.DWORD)
    handle=kernel.OpenEventW(2 if signal else 0x100000,False,name)
    if not handle:return False
    try:return bool(kernel.SetEvent(handle)) if signal else kernel.WaitForSingleObject(handle,0)==0
    finally:kernel.CloseHandle(handle)

def exit_requested():return event(EXIT_EVENT)
def request_exit():return event(EXIT_EVENT,True)
def picker_closed():return event(os.environ.get('DREAMS_IMP_PICKER_CLOSED'),True)

def active_character():
    """A saved appearance is not a running, successfully presented cursor."""
    import json
    from app import named_handle
    from app_paths import READY
    if not named_handle('Local\\DreamsStandaloneImp.Active'):return None
    try:
        record=json.loads(READY.read_text(encoding='utf-8'))
        kernel=C.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=(W.DWORD,W.BOOL,W.DWORD);kernel.OpenProcess.restype=W.HANDLE
        kernel.WaitForSingleObject.argtypes=(W.HANDLE,W.DWORD);kernel.CloseHandle.argtypes=(W.HANDLE,)
        handle=kernel.OpenProcess(0x100000,False,int(record['pid']))
        if not handle:return None
        try:return record['character'] if kernel.WaitForSingleObject(handle,0)==0x102 else None
        finally:kernel.CloseHandle(handle)
    except (OSError,ValueError,KeyError):return None
