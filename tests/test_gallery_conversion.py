"""Conversion across the actual spawned process, including hero and slot reuse."""
import ctypes as C,multiprocessing as mp,os,secrets,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
from gallery_shared_frames import SharedFrames
from gallery_converter import run,SOURCE_SLOTS,HERO_SIDE
from frame_helpers import library
from PIL import Image

def main():
    ctx=mp.get_context('spawn');names=['Local\\ImpConvertTest-'+secrets.token_hex(12) for _ in range(3)]
    source=SharedFrames(names[0],slots=SOURCE_SLOTS,bytes_per_pixel=8)
    display=SharedFrames(names[1]);hero=SharedFrames(names[2],slots=1,max_side=HERO_SIDE)
    receive,send=ctx.Pipe(False);reader,writer=ctx.Pipe(False)
    process=ctx.Process(target=run,args=(receive,writer,*names));process.start();receive.close();writer.close()
    try:
        import random
        raw=random.Random(77).randbytes(512*512*8);pointer=C.create_string_buffer(raw)
        bgra=C.create_string_buffer(512*512*4);library().imp_decode_bgra(raw,bgra,512*512)
        for i,(ident,size) in enumerate([('00_default',(361,361)),('hero:000_alpha',(818,818)),('00_default',(512,512)),('hero:00_default',(113,119)),('33_clown',(600,600))]):
            version=source.write_pointer(0,pointer,512,512,ident)
            send.send(('source-frame',ident,0,version,0,512,512,size))
            assert reader.poll(15),'Converter did not produce a frame'
            kind,returned,slot,version,w,h=reader.recv();assert returned==ident
            ready='ready' in kind;mapping=hero if 'hero' in kind else display
            snapshot=mapping.read(slot,version,w,h,ident);assert snapshot is not None
            expected=Image.frombytes('RGBa',(512,512),bgra.raw,'raw','BGRa')
            if ready:
                assert (w,h)==size
                assert snapshot[0]==expected.resize(size,Image.Resampling.BILINEAR).tobytes()
            else:assert snapshot[0]==bgra.raw
        send.send(('stop',));process.join(4);assert process.exitcode==0
    finally:
        if process.is_alive():process.terminate();process.join(4)
        send.close();reader.close();source.close();display.close();hero.close()
    print('Five cross-process frame comparisons exact; hero resize, slot identity reuse and clean EOF passed')
if __name__=='__main__':main()
