"""Run real gallery shaders without activating a desktop cursor."""
import hashlib
import json
from pathlib import Path
import sys
import time

RUNTIME=Path(__file__).resolve().parents[1]/'runtime'
sys.path.insert(0,str(RUNTIME))
from gallery_client import GalleryClient
from PIL import Image


def main():
    client=GalleryClient(Path(__file__).with_name('gallery-gpu.log'))
    report=[]
    try:
        catalog=json.loads((RUNTIME/'characters/catalog.json').read_text(encoding='utf-8'))
        sets=[['00_default','33_clown','H21_Pag_Clown']]
        sets += [[i['id'] for i in catalog[start:start+32]] for start in range(0,len(catalog),32)]
        sets += [['MM_dreamqueen','33_clown']]
        for ids in sets:
            client.request(ids)
            counts={ident:0 for ident in ids};hashes={ident:set() for ident in ids}
            began=time.monotonic();deadline=began+90
            first=None;last=None
            while min(counts.values())<4 and time.monotonic()<deadline:
                frames,error=client.take()
                if error:raise RuntimeError(error)
                if not client.process.is_alive():raise RuntimeError('Gallery exited early')
                for ident,(w,h,pixels) in frames.items():
                    if ident not in counts:continue
                    if max(pixels[3::4])<20:raise AssertionError('Empty Imp '+ident)
                    counts[ident]+=1;hashes[ident].add(hashlib.sha256(pixels).hexdigest())
                    now=time.monotonic();first=first or now;last=now
                    if ident=='33_clown':Image.frombytes('RGBA',(w,h),pixels).save(Path(__file__).with_name('gallery-clown.png'))
                time.sleep(.003)
            assert min(counts.values())>=4,(counts,client.process.exitcode)
            assert all(len(values)>1 for values in hashes.values()),'Static previews'
            assert len(client.frames)<=len(ids),'Unbounded mailbox'
            report.append({'visible':len(ids),'frames':sum(counts.values()),'first_frame_seconds':first-began,
                           'elapsed':last-began,'all_images_change':True})
        client.request([])
        time.sleep(.3);client.take();time.sleep(.3)
        assert not client.take()[0],'Minimized gallery still produces frames'
    finally:client.close()
    assert not client.process.is_alive()
    Path(__file__).with_name('live-gallery-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':main()
