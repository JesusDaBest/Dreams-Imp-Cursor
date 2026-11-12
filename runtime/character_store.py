"""Verified built-in appearances and persistent native Imp Surprise results."""
import hashlib
import json
import re
import secrets
from pathlib import Path
from app_paths import ROOT,STATE,write_json

GENERATED=STATE/'surprise'

def catalog():
    items=json.loads((ROOT/'characters/catalog.json').read_text(encoding='utf8'))
    path=GENERATED/'catalog.json'
    if path.exists():items.extend(json.loads(path.read_text(encoding='utf8')))
    return items

def load(entry):
    ident=entry['id']
    if entry.get('generated'):
        if not re.fullmatch(r'surprise_[0-9a-f]{16}',ident):raise ValueError('Invalid native Surprise identity')
        directory=GENERATED;filename=ident+'.bin'
    else:
        directory=ROOT/'characters';filename=entry['file']
        if Path(filename).name!=filename:raise ValueError('Invalid appearance filename')
    data=(directory/filename).read_bytes();bindings=(directory/(ident+'.bindings')).read_bytes()
    if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Imp appearance failed its integrity check')
    if entry.get('bindings_sha256') and hashlib.sha256(bindings).hexdigest()!=entry['bindings_sha256']:
        raise ValueError('Imp appearance bindings failed their integrity check')
    return data,bindings

def generate_surprises(count=8):
    from native_surprise import Surprise
    from native_bindings import Bindings
    generator=Surprise();binder=None;results=[]
    try:
        binder=Bindings();GENERATED.mkdir(parents=True,exist_ok=True)
        existing=catalog();saved={item['id']:item for item in existing if item.get('generated')}
        for _ in range(count):
            seed=secrets.randbits(32);data=generator.character(seed);bindings=binder.bind(data)
            ident='surprise_'+data[:8][::-1].hex()
            entry={'id':ident,'name':'Imp Surprise','file':ident+'.bin','generated':True,'native_seed':seed,
                   'sha256':hashlib.sha256(data).hexdigest(),'bindings_sha256':hashlib.sha256(bindings).hexdigest(),
                   'source':'Dreams 0x75e8930; original native eligibility, feature mixing and curve fitting'}
            (GENERATED/entry['file']).write_bytes(data);(GENERATED/(ident+'.bindings')).write_bytes(bindings)
            saved[ident]=entry;results.append(entry)
        write_json(GENERATED/'catalog.json',list(saved.values()))
        return results
    finally:
        if binder is not None:binder.close()
        generator.close()
