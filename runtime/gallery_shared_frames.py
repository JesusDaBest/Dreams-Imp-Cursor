"""Bounded BGRA frame transport; no pixel conversion or persistent files."""
import ctypes as C
import mmap
import struct
import hashlib
from functools import lru_cache

@lru_cache(maxsize=1024)
def identity(ident):return hashlib.blake2b(ident.encode(),digest_size=16).digest()

SLOTS=32
CAPACITY=512*512*4
STRIDE=64+CAPACITY

class SharedFrames:
    def __init__(self,name,*,slots=SLOTS,bytes_per_pixel=4,max_side=512):
        self.slots=slots;self.bytes_per_pixel=bytes_per_pixel
        self.capacity=max_side*max_side*bytes_per_pixel;self.stride=64+self.capacity
        self.mapping=mmap.mmap(-1,self.stride*slots,tagname=name)
        self.buffer=(C.c_ubyte*(self.stride*slots)).from_buffer(self.mapping)
        self.address=C.addressof(self.buffer)
        self.sequences=[0]*self.slots

    def write(self,slot,raw,width,height,decode,ident):
        if not 0<=slot<self.slots or not 0<width*height*4<=self.capacity:raise ValueError('Invalid gallery frame extent')
        at=slot*self.stride
        sequence=self.sequences[slot]+2
        struct.pack_into('<Q',self.mapping,at,sequence-1)
        # The existing native decoder writes its identical premultiplied pixels
        # directly into the shared frame instead of an intermediate allocation.
        self.mapping[at+8:at+24]=identity(ident)
        struct.pack_into('<II',self.mapping,at+24,width,height)
        decode(raw,self.address+at+64,width*height)
        struct.pack_into('<Q',self.mapping,at,sequence)
        self.sequences[slot]=sequence
        return sequence

    def write_pixels(self,slot,pixels,width,height,ident):
        if not 0<=slot<self.slots or len(pixels)!=width*height*4 or not 0<len(pixels)<=self.capacity:
            raise ValueError('Invalid gallery pixel extent')
        at=slot*self.stride;sequence=self.sequences[slot]+2
        struct.pack_into('<Q',self.mapping,at,sequence-1)
        self.mapping[at+8:at+24]=identity(ident)
        struct.pack_into('<II',self.mapping,at+24,width,height)
        self.mapping[at+64:at+64+len(pixels)]=pixels
        struct.pack_into('<Q',self.mapping,at,sequence)
        self.sequences[slot]=sequence
        return sequence

    def write_resized(self,slot,pixels,sw,sh,width,height,resize,ident):
        if not 0<=slot<self.slots or not 0<width*height*4<=self.capacity:
            raise ValueError('Invalid gallery resized extent')
        at=slot*self.stride;sequence=self.sequences[slot]+2
        struct.pack_into('<Q',self.mapping,at,sequence-1)
        self.mapping[at+8:at+24]=identity(ident)
        struct.pack_into('<II',self.mapping,at+24,width,height)
        if not resize(pixels,sw,sh,self.address+at+64,width,height):
            raise RuntimeError('Native gallery resize failed')
        struct.pack_into('<Q',self.mapping,at,sequence)
        self.sequences[slot]=sequence
        return sequence

    def write_pointer(self,slot,pointer,width,height,ident):
        size=width*height*self.bytes_per_pixel
        if not 0<=slot<self.slots or not 0<size<=self.capacity:raise ValueError('Invalid source frame extent')
        at=slot*self.stride;sequence=self.sequences[slot]+2
        struct.pack_into('<Q',self.mapping,at,sequence-1)
        self.mapping[at+8:at+24]=identity(ident)
        struct.pack_into('<II',self.mapping,at+24,width,height)
        C.memmove(self.address+at+64,pointer,size)
        struct.pack_into('<Q',self.mapping,at,sequence)
        self.sequences[slot]=sequence
        return sequence

    def read(self,slot,sequence,width,height,ident):
        if not 0<=slot<self.slots or not 0<width*height*self.bytes_per_pixel<=self.capacity:raise ValueError('Invalid gallery frame extent')
        at=slot*self.stride
        sequence=struct.unpack_from('<Q',self.mapping,at)[0]
        if sequence==0 or sequence&1:return None
        if self.mapping[at+8:at+24]!=identity(ident) or struct.unpack_from('<II',self.mapping,at+24)!=(width,height):return None
        pixels=self.mapping[at+64:at+64+width*height*self.bytes_per_pixel]
        # Aligned 64-bit version stores on this x86-64 runtime detect a frame
        # replaced during the snapshot. Never display a partially written image.
        return (pixels,sequence) if struct.unpack_from('<Q',self.mapping,at)[0]==sequence else None

    def close(self):
        if self.mapping is not None:
            del self.buffer
            self.mapping.close();self.mapping=None
