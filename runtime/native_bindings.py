"""Bind generated appearances with Dreams' original eye-anchor/mouth setup."""
import ctypes as C
from pathlib import Path
import runpy
import struct

ROOT=Path(__file__).resolve().parent

class Bindings:
    def __init__(self):
        engine=runpy.run_path(str(ROOT/'native-imp-motion.py'))
        self.native=engine['NATIVE'];base=self.native['BASE']
        text=self.native['verified_bytes'](self.native['GUEST'],self.native['EXPECTED_TEXT'])
        _,faces=engine['BODY']['default_mesh']()
        self.motion=m=engine['Motion'](text,faces)
        try:
            for lo,hi in ((0x75a4000,0x75a6000),(0x780c000,0x780e000)):
                m.pages(lo,hi);m.put(lo,text[lo-base:hi-base]);m.protect(lo,hi,0x20 if lo<0x7800000 else 2)
            m.protect(0x75b6000,0x75b7000,4)
            start,finish,entry,ret=0x75a4b9e,0x75a549c,0x75b6800,0x75b6880
            code=bytes.fromhex('55 48 89 e5 53 41 54 41 55 41 56 41 57 48 81 ec d8 21 00 00')
            code+=bytes.fromhex('49 89 f5 48 89 b7 f0 03 00 00 48 89 bd a8 df ff ff 48 c7 85 58 df ff ff 00 00 00 00')
            code+=b'\xe9'+struct.pack('<i',start-(entry+len(code)+5));m.put(entry,code)
            m.put(ret,bytes.fromhex('48 81 c4 d8 21 00 00 41 5f 41 5e 41 5d 41 5c 5b 5d c3'))
            m.protect(0x75a5000,0x75a6000,4);m.put(finish,b'\xe9'+struct.pack('<i',ret-finish-5))
            # Only a change-detection hash is replaced; no geometry uses it.
            m.pages(0x629a000,0x629b000);m.put(0x629a4e0,bytes.fromhex('48 c7 01 00 00 00 00 c3'));m.protect(0x629a000,0x629b000,0x20)
            host=C.cast(m.runtime.atan2f,C.c_void_p).value
            m.put(0x75b68c0,bytes.fromhex('48 83 ec 28 48 b8')+struct.pack('<Q',host)+bytes.fromhex('ff d0 48 83 c4 28 c3'))
            plt=0x7788a70;got=plt+6+struct.unpack_from('<i',text,plt-base+2)[0]
            m.protect(got&~4095,(got&~4095)+4096,4);m.put(got,struct.pack('<Q',m.addr(0x75b68c0)))
            bridge=self.native['to_guest'](m.addr(entry));at=bridge.index(bytes.fromhex('48 89 cf 48 b8'))
            bridge[at:at+3]=bytes.fromhex('48 89 c8 48 8b 38 48 8b 70 08');m.put(0x75b6900,bridge)
            m.protect(0x75b6000,0x75b7000,0x20);m.protect(0x75a5000,0x75a6000,0x20)
            m.win.FlushInstructionCache(m.win.GetCurrentProcess(),m.start,0)
            self.setup=C.CFUNCTYPE(None,C.c_void_p)(m.addr(0x75b6900))
        except BaseException:
            m.close();raise

    def bind(self,data):
        if len(data)!=0x4500:raise ValueError('Incomplete native appearance')
        char=C.create_string_buffer(data);obj=C.create_string_buffer(0x3a200+64);obj[-64:]=b'\xa5'*64
        args=(C.c_void_p*2)(C.addressof(obj),C.addressof(char));self.setup(C.addressof(args))
        if obj[-64:]!=b'\xa5'*64:raise ValueError('Native appearance binding exceeded its buffer')
        return bytes(obj[0x2c340:0x2c370])+bytes(obj[0x27ba0:0x29bb0])

    def close(self):self.motion.close()
