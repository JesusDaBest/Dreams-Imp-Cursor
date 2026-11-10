"""Bounded latest-frame mailbox for the live Imp picker."""
import multiprocessing as mp
import threading
from PIL import Image
from gallery_worker import run


class GalleryClient:
    def __init__(self, log_path):
        context = mp.get_context('spawn')
        self.connection, child = context.Pipe()
        self.lock = threading.Lock()
        self.frames = {}
        self.visible = set()
        self.size = None
        self.error = None
        self.closed = False
        self.process = context.Process(target=run,args=(child,str(log_path)),daemon=True)
        self.process.start();child.close()
        self.reader = threading.Thread(target=self._read,daemon=True)
        self.reader.start()

    def _read(self):
        try:
            while True:
                message = self.connection.recv()
                if message[0]=='frame':
                    _,ident,width,height,pixels = message
                    with self.lock:
                        if ident not in self.visible:continue
                        size=self.size
                    # Resampling must not block Tk's pointer/scroll event loop.
                    if size and size!=(width,height):
                        image=Image.frombytes('RGBA',(width,height),pixels).resize(size,Image.Resampling.LANCZOS)
                        width,height=image.size;pixels=image.tobytes()
                with self.lock:
                    if message[0]=='frame':
                        if ident in self.visible and size==self.size:self.frames[ident]=(width,height,pixels)
                    elif message[0]=='error':self.error=message[1]
        except (OSError,EOFError):pass

    def request(self, ids, aim=None, size=None):
        if self.closed or not self.process.is_alive():return
        with self.lock:
            if size!=self.size:self.frames.clear()
            self.size=size
            self.visible=set(ids)
            self.frames={key:value for key,value in self.frames.items() if key in self.visible}
        try:self.connection.send({'ids':list(ids),'aim':aim or {}})
        except (BrokenPipeError,EOFError,OSError):pass

    def take(self):
        with self.lock:
            frames=self.frames;self.frames={}
            error=self.error;self.error=None
        return frames,error

    def close(self):
        if self.closed:return
        self.closed=True
        try:self.connection.send({'stop':True})
        except (BrokenPipeError,EOFError,OSError):pass
        self.process.join(timeout=4)
        if self.process.is_alive():self.process.terminate();self.process.join(timeout=4)
        self.connection.close();self.reader.join(timeout=1)
