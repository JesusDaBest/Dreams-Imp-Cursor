"""Prepare portable app and complete source archives; never publish or change installations."""
import hashlib
import argparse
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'release'/'Imp Carousel'
OUT.mkdir(parents=True,exist_ok=True)

# Do not ship vendor-only SPIR-V imports in a cross-vendor download.
def audit_portable_shaders(root):
    import struct
    for shader in root.rglob('*.spv'):
        raw=shader.read_bytes()
        assert len(raw)>=20 and len(raw)%4==0, shader
        words=struct.unpack('<%dI'%(len(raw)//4),raw)
        assert words[0]==0x07230203, shader
        i=5
        while i<len(words):
            n=words[i]>>16;op=words[i]&65535
            assert n and i+n<=len(words), shader
            if op in (10,11):
                start=2 if op==11 else 1
                name=struct.pack('<%dI'%(n-start),*words[i+start:i+n]).split(b'\0')[0].decode()
                assert not any(v in name for v in ('AMD','NV_','NVX')), (shader,name)
            i+=n

audit_portable_shaders(ROOT/'runtime')

def copy_changed(source,dest):
    if dest.exists() and source.read_bytes()==dest.read_bytes():return
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,dest)

def include(relative):
    parts=relative.parts
    if '__pycache__' in parts or relative.suffix in ('.pyc','.lib','.exp','.pdb'):return False
    if relative.name=='desktop-lighting.bin':return False
    if 'demos' in parts and 'python' in parts:return False
    if relative.name in ('RECORD','direct_url.json'):return False
    return True

for original in (ROOT/'runtime').rglob('*'):
    if not original.is_file():continue
    relative=original.relative_to(ROOT)
    if not include(relative):continue
    if relative.as_posix()=='runtime/imp-renderer.dll':continue
    copy_changed(original,OUT/relative)
for relative in ('Imp Carousel.exe','runtime/imp-renderer.dll'):
    copy_changed(ROOT/'build-output'/relative,OUT/relative)
for name in ('README.txt','Controls.txt','THIRD_PARTY_NOTICES.txt'):
    shutil.copy2(ROOT/name,OUT/name)
audit_portable_shaders(OUT/'runtime')
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='MANIFEST.sha256' and include(p.relative_to(OUT)))
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(OUT).as_posix()+'\n' for p in files)
(OUT/'MANIFEST.sha256').write_text(manifest,encoding='utf-8')

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=Path.home()/'Downloads')
downloads=parser.parse_args().output
downloads.mkdir(parents=True,exist_ok=True)
archives=[downloads/'Imp Carousel - Windows.zip',downloads/'Imp Carousel - Source.zip']
for archive in archives:
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file() and include(p.relative_to(OUT)):z.write(p,Path('Imp Carousel')/p.relative_to(OUT))
        if 'Source' in archive.name:
            z.write(ROOT/'SOURCE.md','Imp Carousel/README.md')
            for directory in ('native','tools'):
                for p in sorted((ROOT/directory).rglob('*')):
                    if p.is_file() and p.suffix in ('.cpp','.h','.cmd','.rc','.py','.md','.txt','.glsl','.spvasm','.comp','.vert','.frag') and '__pycache__' not in p.parts and 'loading-screen' not in p.relative_to(ROOT).parts and p.name!='build-local.cmd':
                        z.write(p,Path('Imp Carousel')/p.relative_to(ROOT))
            for test in sorted((ROOT/'tests').glob('test_*.py')):
                if test.name not in ('test_persistent_cursor.py', 'test_native_clip_clock.py', 'test_cursor_tray.py', 'test_picker_lifecycle.py', 'test_desktop_access.py', 'test_portable_render.py', 'test_tip_bloom.py', 'test_live_gallery.py', 'test_gallery_history.py'):
                    z.write(test,'Imp Carousel/tests/'+test.name)
            for filename in ('live-body-export-audit.json','live-character-export-audit.json','fleck-atlas-export-audit.json','test_persistent_cursor.py','test_native_clip_clock.py','test_cursor_tray.py','cursor-scale-calibration.json','test_picker_lifecycle.py','test_desktop_access.py','test_portable_render.py','test_tip_bloom.py','test_live_gallery.py','test_gallery_history.py','live-gallery-report.json','gallery-history-report.json','portable-render-log.txt','catalog-render.json','character-counts.json','appearance-sheet.png'):
                z.write(ROOT/'tests'/filename,'Imp Carousel/tests/'+filename)
    with zipfile.ZipFile(archive) as z:
        bad=z.testzip()
        if bad:raise RuntimeError('Corrupt archive member: '+bad)
        names=set(z.namelist())
        assert 'Imp Carousel/Imp Carousel.exe' in names
        assert 'Imp Carousel/runtime/python/DLLs/_multiprocessing.pyd' in names
        assert 'Imp Carousel/runtime/fonts/SourceSansPro-Regular.ttf' in names
        assert not any(name.endswith(('Start Imp.exe','Stop Imp.exe','renderer.log','settings.json')) for name in names)
        catalog=json.loads(z.read('Imp Carousel/runtime/characters/catalog.json'))
        assert len(catalog)==149
        for character in catalog:
            data=z.read('Imp Carousel/runtime/characters/'+character['file'])
            assert hashlib.sha256(data).hexdigest()==character['sha256']
            assert len(z.read('Imp Carousel/runtime/characters/'+character['id']+'.bindings'))==0x2040
            assert 'Imp Carousel/runtime/thumbnails/'+character['id']+'.png' in names
    print(archive,archive.stat().st_size,hashlib.sha256(archive.read_bytes()).hexdigest(),flush=True)
