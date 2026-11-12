"""Extract named, unmodified Dreams bokeh shader containers from dd.shaders."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GAME = Path('D:/Emulators/ShadPS4/Games/CUSA04301/CUSA04301')
OUT = ROOT/'native/loading-screen'
MASK = (1 << 64)-1

def rol(x, n):
    return ((x << n) | (x >> (64-n))) & MASK

def fmix(x):
    x ^= x >> 33
    x = x*0xff51afd7ed558ccd & MASK
    x ^= x >> 33
    x = x*0xc4ceb9fe1a85ec53 & MASK
    return x ^ (x >> 33)

def hash128(data):
    # Original function 0x629a4e0: MurmurHash3 x64/128, seed zero.
    h1 = h2 = 0
    c1, c2 = 0x87c37b91114253d5, 0x4cf5ad432745937f
    for i in range(0, len(data)//16*16, 16):
        k1, k2 = struct.unpack_from('<QQ', data, i)
        h1 ^= rol(k1*c1 & MASK, 31)*c2 & MASK
        h1 = (rol(h1, 27)+h2) & MASK
        h1 = (h1*5+0x52dce729) & MASK
        h2 ^= rol(k2*c2 & MASK, 33)*c1 & MASK
        h2 = (rol(h2, 31)+h1) & MASK
        h2 = (h2*5+0x38495ab5) & MASK
    tail = data[len(data)//16*16:]
    k1 = int.from_bytes(tail[:8], 'little')
    k2 = int.from_bytes(tail[8:], 'little')
    if len(tail)>8: h2 ^= rol(k2*c2 & MASK, 33)*c1 & MASK
    if tail: h1 ^= rol(k1*c1 & MASK, 31)*c2 & MASK
    h1 ^= len(data); h2 ^= len(data)
    h1 = (h1+h2) & MASK; h2 = (h2+h1) & MASK
    h1, h2 = fmix(h1), fmix(h2)
    h1 = (h1+h2) & MASK; h2 = (h2+h1) & MASK
    return h1, h2

def main():
    archive = (GAME/'shaders/dd.shaders').read_bytes()
    magic, count = struct.unpack_from('<II', archive)
    assert magic == 0x12345678 and 0<count<4096
    entries = {}
    for i in range(count):
        key, offset, size = struct.unpack_from('<QII', archive, 8+16*i)
        assert offset+size<=len(archive)
        entries[key] = (offset, size)
    reference = 'src/ui/ORBIS_shaders/prim_imp.cpp-PrimImpVS.vs.pssl.sb'
    reference_hash = hash128(reference.encode())[0]
    assert reference_hash == 0xda7c2b6d5aaa52d7, hex(reference_hash)
    assert entries[reference_hash] == (2384044, 3048)
    OUT.mkdir(exist_ok=True)
    modules = []
    names=[]
    for name in ('SimpleBokehQuadDraw', 'BokehMoteDraw',
                 'BokehBackgroundCircleDraw', 'BokehLoadingSpinnerDraw'):
        for suffix in ('_base.vs.pssl.sb', '_neo.vs.pssl.sb', '.ps.pssl.sb'):
            names.append(('src/gfx/draw/ORBIS_shaders/bokeh_render.cpp-', name+suffix))
    for name in ('TransitionMakeCapture', 'TransitionDraw', 'TransitionZeroBitCounters',
                 'TransitionSortKeys', 'TransitionBlurryBG', 'TransitionFlares', 'TransitionParticles'):
        names.append(('src/ui/ORBIS_shaders/transition.cpp-', name+'.cs.pssl.sb'))
    for suffix in ('.vs.pssl.sb', '.ps.pssl.sb'):
        names.append(('src/ui/ORBIS_shaders/transition.cpp-', 'TransitionParticles'+suffix))
    for prefix,filename in names:
            path = prefix+filename
            key = hash128(path.encode())[0]
            assert key in entries, (path, hex(key))
            offset, size = entries[key]
            raw = archive[offset:offset+size]
            (OUT/filename).write_bytes(raw)
            modules.append(dict(name=filename, archive_name=path, key=hex(key),
                                offset=offset, bytes=size,
                                sha256=hashlib.sha256(raw).hexdigest()))
    dumps = Path('C:/Users/Jdura/AppData/Roaming/shadPS4/shader/dumps')
    for module in modules:
        raw = (OUT/module['name']).read_bytes()
        shader_hash = struct.unpack_from('<I', raw, 4)[0]
        module['guest_shader_hash'] = hex(shader_hash)
        stage = 'vs' if '.vs.' in module['name'] else 'cs' if '.cs.' in module['name'] else 'fs'
        captures = []
        for binary in dumps.glob(f'{stage}_0x{shader_hash:016x}_*.bin'):
            code = binary.read_bytes()
            at = raw.find(code)
            assert at >= 0, f'Captured GPU code mismatch: {binary}'
            stem = binary.stem
            (OUT/(stem+'.gcn.bin')).write_bytes(code)
            spv = binary.with_suffix('.spv')
            if not spv.is_file(): continue
            target = OUT/spv.name
            target.write_bytes(spv.read_bytes())
            subprocess.run(['spirv-val', '--target-env', 'vulkan1.3', str(target)], check=True)
            subprocess.run(['spirv-cross', str(target), '--vulkan-semantics', '--output', str(target.with_suffix('.glsl'))], check=True)
            subprocess.run(['spirv-cross', str(target), '--reflect', '--output', str(target.with_suffix('.bindings.json'))], check=True)
            captures.append(dict(gcn_offset=at, gcn_bytes=len(code),
                spirv=target.name, spirv_sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        module['captured_variants'] = captures
    (OUT/'manifest.json').write_text(json.dumps(dict(
        source=str(GAME/'shaders/dd.shaders'),
        source_sha256=hashlib.sha256(archive).hexdigest(),
        original_hash_function='0x629a4e0; validated against existing PrimImpVS export',
        modules=modules), indent=2))
    print(json.dumps(dict(extracted=len(modules), directory=str(OUT))))

if __name__ == '__main__': main()
