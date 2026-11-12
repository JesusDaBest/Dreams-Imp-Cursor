"""Play recorded Dreams GPU frames at their captured timestamps, with bounded memory."""
import bisect,io,json,threading,time,zipfile
from PIL import Image

class CloudBackground:
    def __init__(self,path):
        self.path=path;self.lock=threading.Lock();self.stop=threading.Event()
        self.latest=None;self.problem=None
        self.thread=threading.Thread(target=self._run,name='Dreams cloud playback',daemon=True)
        self.thread.start()

    def _run(self):
        try:
            with zipfile.ZipFile(self.path) as archive:
                info=json.loads(archive.read('animation.json'));frames=info['frames']
                times=[f['milliseconds']-frames[0]['milliseconds'] for f in frames]
                assert len(times)>1 and all(b>a for a,b in zip(times,times[1:]))
                duration=info.get('duration_ms',times[-1]+(times[-1]-times[-2]));start=time.monotonic();last=-1
                while not self.stop.is_set():
                    elapsed=((time.monotonic()-start)*1000)%duration
                    index=max(0,bisect.bisect_right(times,elapsed)-1)
                    if index!=last:
                        with Image.open(io.BytesIO(archive.read(frames[index]['file']))) as im:
                            im=im.convert('RGB');item=(index,im.size,im.tobytes())
                        with self.lock:self.latest=item
                        last=index
                    self.stop.wait(.006)
        except Exception as exc:
            self.problem=str(exc)

    def take(self):
        with self.lock:
            item=self.latest;self.latest=None
        return item

    def close(self):
        self.stop.set();self.thread.join(timeout=2)
