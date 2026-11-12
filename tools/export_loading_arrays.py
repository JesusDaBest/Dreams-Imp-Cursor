"""Read immutable texture assets through the verified process and original ImageInfo ABI."""
from pathlib import Path
import ctypes as c,hashlib,json,struct,sys,pefile
app=Path(__file__).resolve().parents[1];work=app.parent
root=Path((app/'cloud-capture/latest-compute-launch.txt').read_text().strip())
sys.path[:0]=[str(work/'dreams-debug-control'),str(work/'deferred-readback-waits'),str(work/'lag-investigation')]
from debug_control import Client
from live_reader import Reader
from inspect_private_functions import locate_functions
client=Client(root/'run.json');client.verify()
current=client.run
run={'pid':current['pid'],'exe':current['core'],'sha256':current['core_sha256']}
layout=json.loads((work/'tren-detile-valid-extent/live-image-layout.json').read_text())
types=(work/'menu-lag-investigation/cached-image-uploads-v3/verify_live_image_cache.py').read_text().split('class Meta')[1].split('run = read')[0]
exec('class Meta'+types)
assert c.sizeof(Info)==layout['info_size']
obj=work/'native-emulator/build/CMakeFiles/shadps4.dir/src/core/libraries/gnmdriver/gnmdriver.cpp.obj'
protected=json.loads((work/'texture-single-mip-write-repair-20261102/parent-link-inputs.json').read_text())
protected.update(json.loads((work/'texture-single-mip-write-repair-20261102/live-launch-plan.json').read_text())['protected'])
assert hashlib.sha256(obj.read_bytes()).hexdigest()==protected[str(obj)]
pe=pefile.PE(run['exe'],fast_load=True)
matches=locate_functions(obj,['?sceGnmSubmitDone@'],pe);assert len(matches)==1
submit=matches[0]
refs={i['rip_targets'][0] for i in submit['instructions'] if any(n.startswith('?liverpool@@') for n in i['references'])}
assert len(refs)==1
out=app/'native/loading-screen/native-arrays';out.mkdir(exist_ok=True)
targets={}
for shader,index in [('8c2d4703',1),('f0a05240',8),('f0a05240',7)]:
    j=json.loads((root/'compute-inputs'/shader/'manifest.json').read_text())
    im=next(im for im in j['images'] if im['index']==index)
    targets[im['address']]=im
reports=[]
with Reader(run) as r:
    assert r.read(r.image+submit['rva'],submit['size'])==pe.get_data(submit['rva'],submit['size'])
    liver=r.u64(r.image+next(iter(refs)))
    liver_layout=json.loads((work/'60fps-investigation/layout.json').read_text())
    raster=r.u64(liver+liver_layout['rasterizer'])
    assert r.u64(raster+layout['Vulkan::Rasterizer.liverpool'])==liver
    cache=raster+layout['Vulkan::Rasterizer.buffer_cache']
    texture=r.u64(cache+layout['VideoCore::BufferCache.texture_cache'])
    assert r.u64(texture+layout['VideoCore::TextureCache.liverpool'])==liver
    header_at=texture+layout['VideoCore::TextureCache.slot_images']
    header=r.read(header_at,40);base,cap,bb,be,_=struct.unpack('<5Q',header)
    assert 0<cap<=131072 and 0<be-bb<=cap//8+8
    bits=r.read(bb,be-bb)
    for index in range(cap):
        if not(bits[index//8]>>(index%8))&1:continue
        at=base+index*layout['image_stride']+layout['VideoCore::Image.info']
        raw=r.read(at,layout['info_size']);info=Info.from_buffer_copy(raw)
        if info.guest not in targets:continue
        im=targets[info.guest]
        assert (info.width,info.height,info.layers,info.levels)==(im['width'],im['height'],im['layers'],im['mips'])
        assert info.props&8 and info.guest_size<=128*1024**2
        asset=out/(str(info.width)+'x'+str(info.height)+'x'+str(info.layers));asset.mkdir(exist_ok=True)
        (asset/'image-info.bin').write_bytes(raw)
        digest=hashlib.sha256()
        with (asset/'guest-tiled.bin').open('wb') as f:
            for off in range(0,info.guest_size,8*1024**2):
                data=r.read(info.guest+off,min(8*1024**2,info.guest_size-off));f.write(data);digest.update(data)
        second=hashlib.sha256()
        for off in range(0,info.guest_size,8*1024**2):second.update(r.read(info.guest+off,min(8*1024**2,info.guest_size-off)))
        assert digest.digest()==second.digest() and raw==r.read(at,len(raw)),'Asset changed during read'
        report={'directory':str(asset),'source_address':hex(info.guest),'bytes':info.guest_size,
            'sha256':digest.hexdigest(),'stable_double_read':True,'captured_gpu_reference':im.get('file'),
            'pid':run['pid'],'exe_sha256':run['sha256']}
        (asset/'provenance.json').write_text(json.dumps(report,indent=2));reports.append(report)
    assert header==r.read(header_at,40),'Image table moved during read'
client.verify()
assert len(reports)==len(targets)
(out/'export-result.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports,indent=2))
