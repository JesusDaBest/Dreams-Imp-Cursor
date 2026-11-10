"""Prepare portable app and complete source archives; never publish or change installations."""
import hashlib
import argparse
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'release'/'Dreams Imp'
OUT.mkdir(parents=True,exist_ok=True)

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
    dest=OUT/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,dest)
for relative in ('Dreams Imp.exe','runtime/imp-renderer.dll'):
    shutil.copy2(ROOT/'build-output'/relative,OUT/relative)
for name in ('README.txt','Controls.txt','THIRD_PARTY_NOTICES.txt'):
    shutil.copy2(ROOT/name,OUT/name)
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='MANIFEST.sha256')
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(OUT).as_posix()+'\n' for p in files)
(OUT/'MANIFEST.sha256').write_text(manifest,encoding='utf-8')

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=Path.home()/'Downloads')
downloads=parser.parse_args().output
downloads.mkdir(parents=True,exist_ok=True)
archives=[downloads/'Dreams Imp - Windows.zip',downloads/'Dreams Imp - Source.zip']
for archive in archives:
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,Path('Dreams Imp')/p.relative_to(OUT))
        if 'Source' in archive.name:
            z.write(ROOT/'SOURCE.md','Dreams Imp/README.md')
            for directory in ('native','tools'):
                for p in sorted((ROOT/directory).rglob('*')):
                    if p.is_file() and p.suffix not in ('.obj','.res','.exe','.pyc') and '__pycache__' not in p.parts and p.name!='build-local.cmd':
                        z.write(p,Path('Dreams Imp')/p.relative_to(ROOT))
            for filename in ('test_picker_lifecycle.py','test_desktop_access.py','test_portable_render.py','test_tip_bloom.py','portable-render-log.txt','catalog-render.json','character-counts.json','appearance-sheet.png'):
                z.write(ROOT/'tests'/filename,'Dreams Imp/tests/'+filename)
    with zipfile.ZipFile(archive) as z:
        bad=z.testzip()
        if bad:raise RuntimeError('Corrupt archive member: '+bad)
        names=set(z.namelist())
        assert 'Dreams Imp/Dreams Imp.exe' in names
        assert not any(name.endswith(('Start Imp.exe','Stop Imp.exe','renderer.log','settings.json')) for name in names)
        catalog=json.loads(z.read('Dreams Imp/runtime/characters/catalog.json'))
        assert len(catalog)==149
        for character in catalog:
            data=z.read('Dreams Imp/runtime/characters/'+character['file'])
            assert hashlib.sha256(data).hexdigest()==character['sha256']
            assert len(z.read('Dreams Imp/runtime/characters/'+character['id']+'.bindings'))==0x2040
            assert 'Dreams Imp/runtime/thumbnails/'+character['id']+'.png' in names
    print(archive,archive.stat().st_size,hashlib.sha256(archive.read_bytes()).hexdigest(),flush=True)
