"""Real gallery: scroll, resize, hide, and close without changing native pixels."""
import json,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'runtime'
sys.path.insert(0,str(ROOT))
from gallery_client import GalleryClient
from carousel_native import anchor_frame,HERO_FRAME

def main():
    catalog=json.loads((ROOT/'characters/catalog.json').read_text())
    first=[x['id'] for x in catalog[:8]]
    second=[x['id'] for x in catalog[8:16]]
    with tempfile.TemporaryDirectory(prefix='imp-transport-test-') as td:
        client=GalleryClient(Path(td)/'gallery.log',premultiplied=True)
        try:
            cases=[(first[:3],(240,240)),(first+['hero:000_alpha'],(361,361)),
                   (second+['hero:000_alpha'],(480,480)),(second,(600,600)),
                   (['hero:000_alpha'],(818,818)),(first[:3],(256,256))]
            for ids,size in cases:
                sizes={i:((818,818) if i.startswith('hero:') else size) for i in ids}
                transforms={i:HERO_FRAME if i.startswith('hero:') else anchor_frame(n,item_index=n) for n,i in enumerate(ids)}
                counts={i:0 for i in ids};end=time.monotonic()+12
                while time.monotonic()<end and min(counts.values())<2:
                    client.request(ids,size=sizes,transforms=transforms)
                    frames,error=client.take();assert error is None,error
                    assert set(frames)<=set(ids)
                    for ident,(w,h,pixels) in frames.items():
                        # A resize can leave one completed previous-size frame
                        # in the mailbox; require two current frames for every ID.
                        if (w,h)==sizes[ident]:
                            assert len(pixels)==w*h*4
                            counts[ident]+=1
                    time.sleep(.01)
                assert min(counts.values())>=2,counts
            client.request([]);time.sleep(.2)
            frames,error=client.take();assert not frames and not error
            assert not client.shared_versions and not client.frames
        finally:client.close()
        assert not client.process.is_alive()
        assert not client.converter.is_alive()
        assert not client.reader.is_alive()
        assert client.shared.mapping is None
        assert client.source.mapping is None
        assert client.hero.mapping is None
    print('Six real-render scroll/resize cases, hidden state, worker exit, reader exit and mapping cleanup passed')

if __name__=='__main__':main()
