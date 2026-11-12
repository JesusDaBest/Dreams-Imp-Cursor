"""Original Dreams hover-particle lifetime, integration and draw-record builder.

The emitted particles are 144-byte native records. The update below executes
0x75f8302..0x75f8e86 and returns the game's 136-byte fleck draw records.
"""
import ctypes as C
import json
from pathlib import Path
import struct

class Sparks:
    def __init__(self,motion,text):
        self.m=motion
        base=motion.__class__.__init__.__globals__['NATIVE']['BASE']
        native=motion.__class__.__init__.__globals__['NATIVE']
        for lo,hi in ((0x75f8000,0x75f9000),(0x77a7000,0x77a8000),(0x77fe000,0x77ff000)):
            motion.pages(lo,hi);motion.put(lo,text[lo-base:hi-base])
            motion.protect(lo,hi,0x20 if lo==0x75f8000 else 2)
        motion.pages(0x75b0000,0x75b1000)
        entry,ret,wrapper=0x75b0100,0x75b0200,0x75b0300
        code=bytes.fromhex('55 48 89 e5 53 41 54 41 55 41 56 41 57 48 81 ec c8 01 00 00')
        code+=bytes.fromhex('4c 8b 1f 4c 89 5c 24 08 41 8b 83 50 75 00 00 48 8b 4f 08 31 db 31 f6 31 ff 41 b8 00 02 00 00 c4 41 18 57 e4')
        code+=b'\xe9'+struct.pack('<i',0x75f8302-entry-len(code)-5)
        motion.put(entry,code)
        motion.put(ret,bytes.fromhex('44 89 c8 48 81 c4 c8 01 00 00 41 5f 41 5e 41 5d 41 5c 5b 5d c3'))
        motion.protect(0x75f8000,0x75f9000,4)
        motion.put(0x75f8e86,b'\xe9'+struct.pack('<i',ret-0x75f8e86-5))
        bridge=native['to_guest'](motion.addr(entry));motion.put(wrapper,bridge)
        motion.protect(0x75f8000,0x75f9000,0x20);motion.protect(0x75b0000,0x75b1000,0x20)
        motion.win.FlushInstructionCache(motion.win.GetCurrentProcess(),motion.start,0)
        self.update=C.CFUNCTYPE(C.c_uint,C.c_void_p)(motion.addr(wrapper))
        self.actor=C.create_string_buffer(0x3a1c0+64)
        self.output=C.create_string_buffer(512*136+64)
        settings=json.loads((Path(__file__).parent/'reference-state/spark-configuration.json').read_text())
        for offset,value in settings['fields'].items():
            offset=int(offset,16);value=bytes.fromhex(value)
            self.actor[offset:offset+len(value)]=value
        # The standalone renderer uses the Imp's local coordinates. Camera and
        # actor transforms are therefore identity in this isolated draw job.
        identity=(0.,0.,0.,1.,0.,0.,0.,1.)
        for offset in (0x470,0x490,0x37130):struct.pack_into('<8f',self.actor,offset,*identity)
        struct.pack_into('<4f',self.actor,0x37aa0,0,0,0,1)
        self.phase=0.
        self.last=b''

    def emission_init(self,text):
        m=self.m;native=m.__class__.__init__.__globals__['NATIVE'];base=native['BASE']
        for lo,hi in ((0x75ac000,0x75b0000),(0x76e6000,0x76e7000),(0x629a000,0x629b000),
                      (0x7801000,0x7802000),(0x78b4000,0x78b5000),
                      (0xb79c000,0xb79d000),(0x119ed000,0x119ee000)):
            m.pages(lo,hi)
            if hi-base<=len(text):m.put(lo,text[lo-base:hi-base])
            m.protect(lo,hi,0x20 if lo<0x77a0000 else 4)
        # Native global current, previous and inverse camera frames. They must
        # agree with the local-coordinate camera above, including unit scale.
        for address in (0xb79c990,0xb79c9b0,0xb79c9d0):
            m.put(address,struct.pack('<8f',0,0,0,1,0,0,0,1))
        # These calls only submit already-built antenna/core draw geometry.
        # The independent original particle emitter and its RNG are retained.
        m.pages(0x760b000,0x760c000);m.put(0x760bf60,b'\xc3');m.protect(0x760b000,0x760c000,0x20)
        m.protect(0x75b0000,0x75b1000,4)
        m.put(0x75b0400,native['to_guest'](m.addr(0x75acfe0)))
        m.protect(0x75b0000,0x75b1000,0x20)
        m.win.FlushInstructionCache(m.win.GetCurrentProcess(),m.start,0)
        self.emit=C.CFUNCTYPE(None,C.c_void_p)(m.addr(0x75b0400))
        # 0x75aee76-0x75af1db submits two prebuilt tip flecks through the
        # shared native draw ring. It is separate from the 200 live sparks.
        # Give this submission its own two-record ring, not the mouth ring.
        self.emission_draw=C.create_string_buffer(2*136+64)
        m.protect(0xebfb000,0xebfc000,4)

    def spawn(self):
        struct.pack_into('<Q',self.actor,0x460,C.addressof(self.actor)+0x4d0)
        old=self.m.solver_step.value
        self.m.solver_step.value=1/30
        ring=C.c_uint64.from_address(self.m.addr(0xebfb328))
        prior_ring=ring.value
        self.emission_draw[-64:]=b'\xa5'*64
        # Native owner fields: first, capacity, written, in-flight count.
        struct.pack_into('<4H',self.actor,0x4d0+0x7118,0,2,0,0)
        ring.value=C.addressof(self.emission_draw)
        try:
            self.emit(C.addressof(self.actor))
            if self.emission_draw[-64:]!=b'\xa5'*64:
                raise ValueError('Native tip submission exceeded its two records')
        finally:
            ring.value=prior_ring
            self.m.solver_step.value=old

    def advance(self,point,controls,color,hovered,dt,player=2):
        self.actor[0x38]=bytes((player-1,))
        struct.pack_into('<4f',self.actor,0x37a90,*point,1.)
        struct.pack_into('<4f',self.actor,0x490,*point,1.)
        struct.pack_into('<4f',self.actor,0x400,*color,0.)
        struct.pack_into('<2f',self.actor,0x27af8,*controls)
        self.phase+=dt
        while self.phase>=1/30:
            self.phase-=1/30
            if hovered:self.spawn()
        self.last=self.step(dt)
        return self.last

    def step(self,dt):
        count=struct.unpack_from('<I',self.actor,0x7550)[0]
        if not count:return b''
        if count>200:raise ValueError('Invalid native spark count')
        self.actor[-64:]=self.output[-64:]=b'\xa5'*64
        old=self.m.solver_step.value
        self.m.solver_step.value=dt
        try:
            args=(C.c_void_p*2)(C.addressof(self.actor),C.addressof(self.output))
            n=self.update(C.addressof(args))
        finally:self.m.solver_step.value=old
        if n>512 or self.actor[-64:]!=b'\xa5'*64 or self.output[-64:]!=b'\xa5'*64:
            raise ValueError('Native spark update exceeded its buffers')
        return self.output[:n*136]
