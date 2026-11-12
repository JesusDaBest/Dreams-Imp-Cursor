"""Shared transport must retain every decoded byte and reject torn/reused slots."""
from pathlib import Path
import ctypes as C,os,runpy,secrets,sys,threading,time
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]/'runtime'
sys.path.insert(0,str(ROOT))
from gallery_shared_frames import SharedFrames
api=runpy.run_path(str(ROOT/'desktop-imp.py'))
name='Local\\ImpFrameTest-'+str(os.getpid())+'-'+secrets.token_hex(12)
writer=SharedFrames(name);reader=SharedFrames(name)
raws=[]
# Use real rendered Imp frames, including HDR and transparent edge pixels.
imp=api['Imp']('000_alpha');frames=[0]
def particles():
    if frames[0]>=12:return None
    return imp.frame('idle',frames[0]/60,.2,-.1,1/60,looping=True)
def present(raw,w,h):raws.append(raw);frames[0]+=1;return True
try:
    api['GPU']['render'](particles,present,lambda:(imp.stick,imp.antenna_path),lambda:imp.eye_count,appearance=lambda:imp.motion.body_color)
finally:imp.close()
decode=api['_cursor_decoder'](False)
expected=[api['decode'](raw).raw[:512*512*4] for raw in raws]
checked=0
try:
    for slot in (0,15,31):
        for index,raw in enumerate(raws):
            seq=writer.write(slot,raw,512,512,decode,'test-imp')
            pixels,version=reader.read(slot,seq,512,512,'test-imp')
            assert version==seq and pixels==expected[index]
            for size in [(240,240),(361,361),(818,818)]:
                actual=Image.frombytes('RGBa',(512,512),pixels,'raw','BGRa').resize(size,Image.Resampling.BILINEAR).tobytes()
                original=Image.frombytes('RGBa',(512,512),expected[index],'raw','BGRa').resize(size,Image.Resampling.BILINEAR).tobytes()
                assert actual==original
                checked+=1
                if size[0]*size[1]<=512*512:
                    seq=writer.write_pixels(slot,original,*size,'test-imp')
                    transported,version=reader.read(slot,seq,*size,'test-imp')
                    assert transported==original and version==seq
                    # Shared thumbnails retain premultiplied RGBA byte order.
                    assert Image.frombytes('RGBa',size,transported).convert('RGBA').tobytes()==Image.frombytes('RGBa',size,original).convert('RGBA').tobytes()
                    checked+=1
    writer.write(0,raws[0],512,512,decode,'another-imp')
    assert reader.read(0,2,512,512,'test-imp') is None
    stop=threading.Event();seen=[];failures=[]
    def produce():
        try:
            for i in range(180):
                writer.write(1,raws[i%len(raws)],512,512,decode,'moving-imp')
                time.sleep(.0005)
        except BaseException as e:failures.append(e)
        finally:stop.set()
    worker=threading.Thread(target=produce);worker.start()
    valid=set(expected)
    while not stop.is_set():
        snapshot=reader.read(1,0,512,512,'moving-imp')
        if snapshot:
            assert snapshot[0] in valid,'Partially written frame escaped the version check'
            seen.append(snapshot[1])
    worker.join();assert not failures and seen
finally:writer.close();reader.close()
print(checked,'pixel-exact resized-frame comparisons; reused identity rejected; concurrent snapshots intact; both mappings closed')
