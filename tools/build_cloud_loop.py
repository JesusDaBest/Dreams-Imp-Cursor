"""Overlap the recorded Dreams clouds' tail and head to remove the loop cut."""
from pathlib import Path
import bisect,io,json,statistics,zipfile
from PIL import Image,ImageChops,ImageStat
root=Path(__file__).resolve().parents[1]
source=root/'cloud-capture/record-session'
info=json.loads((source/'animation.json').read_text(encoding='utf-8'))
frames=info['frames'][1:] # first read was the previous capture's retained frame
times=[x['milliseconds']-frames[0]['milliseconds'] for x in frames]
step=statistics.median(b-a for a,b in zip(times,times[1:]));duration=times[-1]+step
begin=bisect.bisect_left(times,2000);fade=times[begin]
duration=times[-1]+times[begin]-times[begin-1]
def image(index):return Image.open(source/'frames'/frames[index]['file']).convert('RGB')
def sample(t):
    j=max(0,min(len(times)-2,bisect.bisect_right(times,t)-1))
    amount=max(0,min(1,(t-times[j])/(times[j+1]-times[j])))
    return Image.blend(image(j),image(j+1),amount)
def difference(a,b):return sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
original_seam=difference(image(0),image(len(frames)-1))
out=root/'runtime/picker-assets/cloud-animation.zip';new=[];first=last=None
with zipfile.ZipFile(out,'w',zipfile.ZIP_STORED) as archive:
    for i in range(begin,len(frames)):
        im=image(i);t=times[i]
        if t>=duration-fade:
            head=t-(duration-fade)
            alpha=max(0,min(1,head/fade));alpha=alpha*alpha*(3-2*alpha)
            im=Image.blend(im,sample(head),alpha)
        name=f'{len(new):04}.jpg';data=io.BytesIO();im.save(data,format='JPEG',quality=94,subsampling=0)
        archive.writestr(name,data.getvalue());new.append({'file':name,'milliseconds':t-fade})
        if first is None:first=im
        last=im
    info.update(frames=new,loop_processing={'method':'overlap recorded tail and head','overlap_ms':fade},duration_ms=duration-fade)
    archive.writestr('animation.json',json.dumps(info))
seam=difference(first,last)
adjacent=[difference(image(i),image(i+1)) for i in range(len(frames)-1)]
normal=statistics.median(adjacent)
assert seam<=max(adjacent) and seam<original_seam,(seam,original_seam,normal)
report={'frames':len(new),'duration_ms':duration-fade,'original_cut_mean_rgb_difference':original_seam,'loop_cut_mean_rgb_difference':seam,'normal_frame_step_mean_rgb_difference':normal,'recorded_clouds_only':True}
(root/'tests/cloud-loop-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
