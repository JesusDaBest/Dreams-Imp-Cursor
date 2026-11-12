"""Offline original Dreams UI record packing; captured font lookup, no live hooks."""
from native_ui_style import NativeUIStyle,ROOT,RUNTIME,base
import ctypes as C,struct,json,hashlib,math
class NativeUIPack(NativeUIStyle):
    def __init__(self):
        super().__init__()
        text=base['verified_bytes'](RUNTIME/'native-code/guest-text.bin',base['EXPECTED_TEXT'])
        # Original pack globals, bounded cache and local upload buffer.
        self.pages(0xf6ac000,0xf92e000)
        self.put(0xf929460,(ROOT/'ui-presets.bin').read_bytes())
        data={x['address']:x for x in json.loads((ROOT/'pack-data/index.json').read_text())['pages']}
        pages=set(json.loads((ROOT/'code-data-pages.json').read_text()))|set(data)
        for a in pages:
            if 0xf6ac000<=a<0xf92e000:continue
            self.pages(a,a+4096);self.protect(a,a+4096,0x04)
            if a in data:
                row=data[a];b=(ROOT/'pack-data'/row['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'];self.put(a,b)
            elif a+4096-base['BASE']<=len(text):self.put(a,text[a-base['BASE']:a+4096-base['BASE']])
        # Restore the captured table after mapping the neighboring globals.
        self.put(0xf929460,(ROOT/'ui-presets.bin').read_bytes())
        # Original material-cache interpolation reads this global at 0x76b7f51.
        # The cache allocation above is intentionally empty, but this immutable
        # captured setting must survive: zero freezes every cached material.
        transition_page=data[0xf929000]
        transition=(ROOT/'pack-data'/transition_page['file']).read_bytes()
        assert hashlib.sha256(transition).hexdigest()==transition_page['sha256']
        self.put(0xf92935c,transition[0x35c:0x360])
        self.put(0xf6acd40+0x2741e2,b'\xff'*(0x4000*2))
        self.put(0xf6b0f18,b'\0\0');self.put(0xf920f20,b'\0'*4)
        self.output=C.create_string_buffer(524*4096)
        for off in (8,80):self.put(0xf6acd40+off,struct.pack('<Q',C.addressof(self.output)))
        # Empty external font collection: resolve each known glyph directly to its
        # captured 48-byte metadata record; the original shader math is untouched.
        self.put(0xf9349c0,b'\0'*16)
        self.pages(0x76d1000,0x76d2000)
        self.protect(0x76b7000,0x76ba000,0x04)
        self.protect(0x7788000,0x7789000,0x04);self.protect(0x778a000,0x778b000,0x04)
        self.protect(0x7de6000,0x7de9000,0x04)
        self.put(0x7de6cb8,struct.pack('<Q',self.addr(0x7de6cc0)))
        self.pages(0x7456000,0x7457000);self.put(0x74562b0,b'\xc3');self.protect(0x7456000,0x7457000,0x20)
        self.put(0x76b9f00,base['to_guest'](self.addr(0x76b7b30)))
        self.put(0x76b9e80,bytes.fromhex('0f 2e c0 0f 9a c0 0f b6 c0 c3'))
        # Native libc powf import with the same float ABI arguments.
        host=C.cast(self.runtime.powf,C.c_void_p).value
        self.put(0x76b9ec0,bytes.fromhex('48 83 ec 28 48 b8')+struct.pack('<Q',host)+bytes.fromhex('ff d0 48 83 c4 28 c3'))
        for plt,stub in [(0x7788170,0x76b9e80),(0x778af90,0x76b9ec0)]:
            off=plt-base['BASE'];got=plt+6+struct.unpack_from('<i',text,off+2)[0];self.put(got,struct.pack('<Q',self.addr(stub)))
        # sincosf uses the already-tested native bridge.
        body=__import__('runpy').run_path(str(RUNTIME/'verify-native-imp-body.py'));self.sincos=body['native_sincos']()
        code=bytes.fromhex('48 89 f9 48 89 f2 0f 28 d0 48 83 ec 28 48 b8')+struct.pack('<Q',C.cast(self.sincos,C.c_void_p).value)+bytes.fromhex('ff d0 48 83 c4 28 c3')
        self.put(0x76b9e00,code)
        got=0x778afb0+6+struct.unpack_from('<i',text,0x778afb0-base['BASE']+2)[0];self.put(got,struct.pack('<Q',self.addr(0x76b9e00)))
        self.protect(0x76b7000,0x76ba000,0x20)
        self.protect(0x7788000,0x7789000,0x20);self.protect(0x778a000,0x778b000,0x20)
        self.packfn=C.CFUNCTYPE(C.c_uint64,C.c_void_p)(self.addr(0x76b9f00));self.frame=0;self.cache_slots={}
    def pack(self,raw,hover=0,dt=1/30):
        glyph=struct.unpack_from('<I',raw)[0];self.glyph=C.create_string_buffer((ROOT/f'pack-data/glyph-{glyph:x}.bin').read_bytes())
        if struct.unpack_from('<Q',self.glyph,8)[0]:
            self.link=C.create_string_buffer((ROOT/f'pack-data/glyph-{glyph:x}-linked.bin').read_bytes());struct.pack_into('<Q',self.glyph,8,C.addressof(self.link))
        self.protect(0x76d1000,0x76d2000,0x04);self.put(0x76d1880,b'\x48\xb8'+struct.pack('<Q',C.addressof(self.glyph))+b'\xc3');self.protect(0x76d1000,0x76d2000,0x20)
        src=C.create_string_buffer(raw);struct.pack_into('<f',src,0xbc,hover)
        # Offline caller consumes the upload directly, so omit only queue submission.
        src[0x140]=b'\0'
        self.frame+=1;self.put(0xda2687c,struct.pack('<I',self.frame));self.put(0x8a75c6c,struct.pack('<f',dt))
        self.put(0xf6b0f18,b'\0\0');self.put(0xf6b0e60,b'\0'*4)
        value=self.packfn(C.addressof(src));n=C.c_uint16.from_address(self.addr(0xf6b0f18)).value
        assert n==1,(value,n)
        # The game publishes this cache's hash index outside the pack function.
        # Register its newly allocated entry using the exact native probe math
        # (0x76b7c1d..0x76b7ced), so subsequent frames retain their real phases.
        key=struct.unpack_from('<Q',raw,0xc0)[0];mask=(1<<64)-1
        def mix(x):
            x=(((x<<21)&mask)+(~x&mask))&mask;x^=x>>24;x=x*0x109&mask
            x^=x>>14;x=x*21&mask;x^=x>>28;return x
        x=mix(key)
        slot=self.cache_slots.get(key,C.c_uint16.from_address(self.addr(0xf920f20)).value)
        self.cache_slots[key]=slot
        assert C.c_uint64.from_address(self.addr(0xf6b0f20+slot*0x270)).value==key,(self.frame,slot,hex(key),hex(C.c_uint64.from_address(self.addr(0xf6b0f20+slot*0x270)).value))
        for attempt in range(16):
            product=x*0x80000001&mask;bucket=(product&0xffffffff)&0x3fff
            cell=C.c_uint16.from_address(self.addr(0xf6acd40+0x2741e2+bucket*2))
            if cell.value==0xffff:cell.value=slot;break
            if C.c_uint64.from_address(self.addr(0xf6b0f20+cell.value*0x270)).value==key:break
            x=(x*0x10000000200000+(~product&mask))&mask
            x^=x>>24;x=x*0x109&mask;x^=x>>14;x=x*21&mask;x^=x>>28
        else:raise ValueError('Original UI cache probe budget exhausted')
        return self.output.raw[:524]
if __name__=='__main__':
    vm=NativeUIPack()
    try:
        p=ROOT/'entry-inputs/253603052832557.bin';out=vm.pack(p.read_bytes());(ROOT/'offline-packed-record.bin').write_bytes(out);print('Original UI pack emitted',len(out),'bytes',flush=True)
    finally:vm.close()
