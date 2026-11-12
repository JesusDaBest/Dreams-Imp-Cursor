"""Dreams' original Imp Surprise generator, with local native preset resources.

The feature selection, colour selection, proportions and curve fitting execute
guest function 0x75e8930. Only asset lookup and the game's cache refresh are
adapted: decoded presets replace resource IDs, and the app binds the result.
"""
import ctypes as C
import json
from pathlib import Path
import runpy
import struct

ROOT=Path(__file__).resolve().parent
N=runpy.run_path(str(ROOT/'verify-native-imp-animation.py'))
Native=N['NativeEvaluator']

class Surprise(Native):
    def __init__(self):
        text=N['verified_bytes'](N['GUEST'],N['EXPECTED_TEXT'])
        super().__init__(text,last_page=0xec00000)
        try:self._surprise_init(text)
        except BaseException:
            self.close();raise

    def _surprise_init(self,text):
        base=N['BASE']
        for lo,hi in ((0x75e8000,0x75ea000),(0x75c6000,0x75c7000),
                      (0x6294000,0x6295000),(0x760a000,0x760b000),
                      (0x77fe000,0x77ff000),(0x7811000,0x7812000),(0x78b4000,0x78b5000),
                      (0xebf6000,0xebf7000)):
            self.pages(lo,hi)
            if hi-base<=len(text):self.put(lo,text[lo-base:hi-base])
        resource=json.loads((ROOT/'reference-state/surprise-resources.json').read_text(encoding='utf8'))
        self.presets={int(k):(ROOT/'characters'/v).read_bytes() for k,v in resource['presets'].items()}
        eligible=resource['eligible']
        if not eligible or any(k not in self.presets for k in eligible):raise ValueError('Incomplete native Surprise preset resources')
        self.ids=(C.c_uint*len(eligible))(*eligible)
        self.table=C.create_string_buffer(0x38)
        struct.pack_into('<I',self.table,12,len(eligible))
        struct.pack_into('<Q',self.table,16,C.addressof(self.ids))
        self.put(0xebf6570,struct.pack('<Q',C.addressof(self.table)))
        self.resource_error=None
        @C.CFUNCTYPE(C.c_int,C.c_uint,C.c_void_p)
        def resolve(ident,out):
            data=self.presets.get(ident)
            if data is None:
                self.resource_error=ident;return 0
            C.memmove(out,data,0x4220);return 1
        self.resolve=resolve
        stub=bytes.fromhex('48 89 f9 48 89 f2 48 83 ec 28 48 b8')+struct.pack('<Q',C.cast(resolve,C.c_void_p).value)+bytes.fromhex('ff d0 48 83 c4 28 c3')
        self.put(0x760a0c0,stub)
        # The tail refreshes engine resource caches beyond the serialized
        # character. Geometry binding is performed separately by the app.
        self.put(0x75e99a1,b'\xe9'+struct.pack('<i',0x75e9694-0x75e99a1-5))
        # Original memset import: translate its ordinary SysV call to Windows.
        self.protect(0x75b3000,0x75b4000,4)
        stub=bytes.fromhex('49 89 d0 48 89 f2 48 89 f9 48 83 ec 28 48 b8')+struct.pack('<Q',C.cast(self.runtime.memset,C.c_void_p).value)+bytes.fromhex('ff d0 48 83 c4 28 c3')
        self.put(0x75b3b00,stub)
        plt=0x7788440;got=plt+6+struct.unpack_from('<i',text,plt-base+2)[0]
        self.protect(got&~4095,(got&~4095)+4096,4)
        self.put(got,struct.pack('<Q',self.addr(0x75b3b00)))
        code=N['to_guest'](self.addr(0x75e8930))
        at=code.index(bytes.fromhex('48 89 cf 48 b8'))
        code=code[:at]+bytes.fromhex('48 89 c8 48 8b 38 8b 70 08')+code[at+3:]
        # SysV emits no Windows __chkstk call for its 85 KiB stack frame.
        # Touch successive pages before entering the unchanged guest function.
        probe=b''.join(bytes.fromhex('f6 84 24')+struct.pack('<i',-offset)+b'\0'
                       for offset in range(0x1000,0x18001,0x1000))
        code=probe+code
        self.put(0x75b3c00,code)
        for lo,hi in ((0x75e8000,0x75ea000),(0x75c6000,0x75c7000),(0x6294000,0x6295000),
                      (0x760a000,0x760b000),(0x75b3000,0x75b4000)):
            self.protect(lo,hi,0x20)
        self.win.FlushInstructionCache(self.win.GetCurrentProcess(),self.start,0)
        self.generate=C.CFUNCTYPE(C.c_int,C.c_void_p)(self.addr(0x75b3c00))

    def character(self,seed,*,mouth_scale=None):
        if not 0<=seed<=0xffffffff:raise ValueError('Surprise seed is outside the native seed range')
        # The game randomizes an existing character, preserving its four native
        # emote names. Starting from zeros would erase those capabilities.
        out=C.create_string_buffer(self.presets[self.ids[0]],0x4500+64);out[-64:]=b'\xa5'*64
        struct.pack_into('<I',out,8,seed^0xffffffff)
        if mouth_scale is None:mouth_scale=struct.unpack_from('<f',self.presets[self.ids[0]],0xb0)[0]
        struct.pack_into('<f',out,0xb0,mouth_scale)
        args=C.create_string_buffer(struct.pack('<QI',C.addressof(out),seed))
        if not self.generate(C.addressof(args)) or self.resource_error is not None:raise ValueError('Native Surprise could not resolve its preset')
        if out[-64:]!=b'\xa5'*64:raise ValueError('Native Surprise wrote outside its character')
        return bytes(out[:0x4500])
