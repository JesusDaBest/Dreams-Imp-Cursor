"""Port field construction from Dreams BokehButton::draw (0x743ce14 onward).
Only the ordinary unrotated carousel button path is accepted here.
"""
from pathlib import Path
import struct,math,json
from native_ui_style import ROOT
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def flags(value):
    # Original integer instructions 0x743cc11..0x743cd1b.
    eax=value>>43;ebx=value>>32
    esi=(((value&0xffffffff)<<7)|eax)&0x40000044
    esi|=(value>>21)&0x2000;esi|=((value&0xffffffff)<<16)&0x10000000
    esi|=eax&0x380;esi|=(value>>44)&0x800;esi|=eax&0x400
    esi|=ebx&0xf000000;esi|=(value<<6)&0x80000000
    esi|=(value>>47)&0x8000;esi|=(value>>31)&0x20000000
    esi|=(value>>10)&1;esi|=(value>>14)&0x800000
    typ=value&255
    if 115<=typ<117:esi|=0x20
    if typ==152:esi|=8
    return esi&0xffffffff

COMMON=(ROOT/'entry-inputs/253603052832557.bin').read_bytes()
def build(widget):
    """Native ordinary carousel path, validated against captured GPU records.

    The captured common primitive contains the draw-context defaults. Replace
    only the widget fields used on this path; other widget subclasses are refused.
    """
    assert len(widget)>=0x520
    out=bytearray(COMMON)
    value=struct.unpack_from('<Q',widget,0x228)[0];typ=value&255
    glyph=struct.unpack_from('<I',widget,0x218)[0]
    assert typ in (100,104) and glyph in (0xe241,0xe319,0xe143,0xe149,0xe252,0xe153,0xe697)
    assert struct.unpack_from('<f',widget,0x298)[0]==0,'Rotated widget requires original rotation path'
    for dst,src,n in [(0,0x218,4),(4,0x29c,4),(0x10,0x40,32),(0x30,0x130,16),(0x40,0x160,16),(0x50,0x330,16),(0x60,0x340,4),(0x70,0x1a0,16),(0x80,0x1b0,16),(0x90,0x1c0,16),(0xa0,0x1d0,16),(0xb8,0x194,4),(0xbc,0x1fc,4),(0xc0,0x18,8),(0xc8,0x208,4)]:out[dst:dst+n]=widget[src:src+n]
    scale=struct.unpack_from('<f',widget,0x190)[0]
    struct.pack_into('<f',out,0x3c,f32(struct.unpack_from('<f',out,0x3c)[0]*scale))
    alpha=struct.unpack_from('<f',widget,0x1ac)[0]
    for off in (0x7c,0x8c):struct.pack_into('<f',out,off,f32(struct.unpack_from('<f',out,off)[0]*alpha))
    struct.pack_into('<II',out,0xb0,typ-100,flags(value));struct.pack_into('<I',out,0xcc,(value>>41)&7)
    return bytes(out)
