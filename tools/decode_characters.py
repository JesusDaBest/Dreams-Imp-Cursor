"""Decode original character files with Dreams' character reader, offline."""
import ctypes as C
import json
from pathlib import Path
import runpy
import struct
import hashlib
import os

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'runtime'
SRC = Path(os.environ.get('DREAMS_IMP_CHARACTERS', 'data/imp/chars'))

def unpack(data):
    if int.from_bytes(data[:4], 'little') != len(data)-4:
        raise ValueError('Bad LZ4 size')
    data = data[4:]; p=0; out=bytearray()
    def length(n):
        nonlocal p
        if n==15:
            while True:
                b=data[p];p+=1;n+=b
                if b!=255:break
        return n
    while p<len(data):
        token=data[p];p+=1;n=length(token>>4)
        out.extend(data[p:p+n]);p+=n
        if p==len(data):break
        offset=int.from_bytes(data[p:p+2],'little');p+=2;n=length(token&15)+4
        if not 0<offset<=len(out) or len(out)+n>1024*1024:raise ValueError('Invalid match')
        pat=out[-offset:];out.extend((pat*((n+offset-1)//offset))[:n])
    return bytes(out)

def main():
    engine = runpy.run_path(str(RUNTIME/'native-imp-motion.py'))
    body = engine['BODY']; native=engine['NATIVE']
    text=native['verified_bytes'](native['GUEST'], native['EXPECTED_TEXT'])
    _, faces=body['default_mesh']()
    motion=engine['Motion'](text, faces)
    @C.WINFUNCTYPE(C.c_long, C.c_void_p)
    def crash(info):
        er,ctx=struct.unpack('<QQ',C.string_at(info,16))
        code=struct.unpack('<I',C.string_at(er,4))[0]
        if code not in (0xc0000005,0xc000001d): return 0
        regs=struct.unpack_from('<17Q',C.string_at(ctx,256),120)
        print('NATIVE FAULT',hex(code),'guest pc',hex(regs[-1]-motion.start+native['BASE']),
              'regs',*[hex(x) for x in regs],flush=True)
        C.windll.kernel32.TerminateProcess(C.c_void_p(-1),2)
        return 0
    C.windll.kernel32.AddVectoredExceptionHandler(1,crash)
    output_dir=RUNTIME/'characters';output_dir.mkdir(exist_ok=True)
    try:
        motion.pages(0x651b000,0x651c000)
        motion.put(0x651b000,text[0x651b000-native['BASE']:0x651c000-native['BASE']])
        motion.protect(0x651b000,0x651c000,0x20)
        motion.protect(0x75b6000,0x75b7000,0x04)
        motion.put(0x75b6400,text[0x75b6400-native['BASE']:0x75b6800-native['BASE']])
        host=C.cast(motion.runtime.memset,C.c_void_p).value
        stub=0x75b6800
        motion.put(stub,bytes.fromhex('49 89 d0 48 89 f2 48 89 f9 48 83 ec 28 48 b8')+
                   struct.pack('<Q',host)+bytes.fromhex('ff d0 48 83 c4 28 c3'))
        plt=0x7788440
        got=plt+6+struct.unpack_from('<i',text,plt-native['BASE']+2)[0]
        motion.protect(got&~4095,(got&~4095)+4096,0x04)
        motion.put(got,struct.pack('<Q',motion.addr(stub)))
        motion.protect(got&~4095,(got&~4095)+4096,0x02)
        motion.protect(0x75b6000,0x75b7000,0x20)
        motion.protect(0x75c6000,0x75ca000,0x04)
        # Restore the full character reader, including both native decoration arrays.
        off=0x75c7ce5-native['BASE']
        motion.put(0x75c7ce5,text[off:off+18])
        motion.protect(0x75c6000,0x75ca000,0x20)
        motion.win.FlushInstructionCache(motion.win.GetCurrentProcess(),motion.start,0)
        decode=C.CFUNCTYPE(None,C.c_void_p)(motion.addr(0x75b6250))
        entries=[]
        for path in sorted(SRC.glob('*.dat')):
            raw=unpack(path.read_bytes());version=int.from_bytes(raw[4:8],'little')
            print(path.stem, version, len(raw), flush=True)
            inp=C.create_string_buffer(raw+b'\0'*16)
            reader=C.create_string_buffer(0x108)
            struct.pack_into('<I',reader,0x14,version)
            struct.pack_into('<QQ',reader,0x88,C.addressof(inp)+8,C.addressof(inp)+len(raw)+16)
            out=C.create_string_buffer(0x4500+64)
            out[-64:]=b'\xa5'*64
            C.memmove(out, motion.eye_character[0],0x210)
            args=(C.c_void_p*2)(C.addressof(reader),C.addressof(out))
            decode(C.addressof(args))
            used=struct.unpack_from('<Q',reader,0x88)[0]-C.addressof(inp)
            error=struct.unpack_from('<H',reader,0x10)[0]
            if error or used!=len(raw) or out[-64:]!=b'\xa5'*64:
                raise ValueError((path.name,error,used,len(raw),'decode guard'))
            dest=output_dir/(path.stem+'.bin');dest.write_bytes(out[:0x4500])
            entries.append({'id':path.stem,'name':bytes(out[0x10:0x30]).split(b'\0')[0].decode('utf8'),
                'file':dest.name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'version':version,
                'decorations':[struct.unpack_from('<I',out,p)[0] for p in (0x21c0,0x41d0)]})
        (output_dir/'catalog.json').write_text(json.dumps(entries,indent=2))
        print('Decoded',len(entries),'characters')
    finally:motion.close()

if __name__=='__main__':main()
