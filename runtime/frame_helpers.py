"""Exact CPU frame preparation; no shader, animation or quality settings."""
import ctypes as C
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def library():
    lib=C.CDLL(str(Path(__file__).parent/'imp-frame-helpers.dll'))
    lib.imp_decode_bgra.argtypes=(C.c_void_p,C.c_void_p,C.c_uint)
    lib.imp_decode_bgra.restype=None
    lib.imp_interpolate_samples.argtypes=(C.c_void_p,C.c_void_p,C.c_void_p,
        C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_double,C.c_void_p,C.c_void_p)
    lib.imp_interpolate_samples.restype=None
    lib.imp_resize_rgba.argtypes=(C.c_void_p,C.c_int,C.c_int,C.c_void_p,C.c_int,C.c_int)
    lib.imp_resize_rgba.restype=C.c_int
    return lib
