"""Bounded latest-frame mailbox for the live Imp picker."""
import multiprocessing as mp
from multiprocessing.connection import wait
import threading
import os,secrets
from gallery_shared_frames import SharedFrames
from PIL import Image
from gallery_worker import run
from gallery_converter import run as convert_frames,SOURCE_SLOTS,HERO_SIDE


class GalleryClient:
    def __init__(self, log_path, *, premultiplied=False):
        context = mp.get_context('spawn')
        self.connection, child = context.Pipe()
        shared_name='Local\\ImpGalleryFrames-'+str(os.getpid())+'-'+secrets.token_hex(12)
        self.shared=SharedFrames(shared_name)
        source_name='Local\\ImpGallerySources-'+str(os.getpid())+'-'+secrets.token_hex(12)
        self.source=SharedFrames(source_name,slots=SOURCE_SLOTS,bytes_per_pixel=8)
        hero_name='Local\\ImpGalleryHero-'+str(os.getpid())+'-'+secrets.token_hex(12)
        self.hero=SharedFrames(hero_name,slots=1,max_side=HERO_SIDE)
        source_read,source_write=context.Pipe(duplex=False)
        self.frame_connection,frame_write=context.Pipe(duplex=False)
        self.lock = threading.Lock()
        self.frames = {}
        self.visible = set()
        self.size = None
        self.error = None
        self.closed = False
        self.premultiplied=premultiplied
        self.shared_versions={}
        self.converter=context.Process(target=convert_frames,args=(source_read,frame_write,source_name,shared_name,hero_name),daemon=True)
        self.process = context.Process(target=run,args=(child,str(log_path),None,source_name,source_write),daemon=True)
        try:
            self.converter.start()
            self.process.start()
        except BaseException:
            for process in (self.process,self.converter):
                if process.pid is not None:
                    if process.is_alive():process.terminate()
                    process.join(timeout=4)
            for channel in (self.connection,self.frame_connection):channel.close()
            self.shared.close();self.source.close();self.hero.close()
            raise
        finally:
            for channel in (source_read,frame_write,child,source_write):channel.close()
        self.reader = threading.Thread(target=self._read,daemon=True)
        self.reader.start()

    def _read(self):
        try:
            inputs=[self.connection,self.frame_connection]
            while inputs:
                ready=wait(inputs)
                channel=ready[0]
                try:message=channel.recv()
                except (OSError,EOFError):
                    inputs.remove(channel)
                    if channel is self.frame_connection and not self.closed:
                        with self.lock:self.error='Gallery conversion worker stopped unexpectedly'
                        break
                    continue
                if message[0] in ('shared-frame-premultiplied','shared-frame-ready-premultiplied','shared-hero-ready-premultiplied'):
                    ready=message[0]!='shared-frame-premultiplied'
                    hero=message[0]=='shared-hero-ready-premultiplied'
                    _,ident,slot,sequence,width,height=message
                    with self.lock:
                        if ident not in self.visible:continue
                    snapshot=(self.hero if hero else self.shared).read(slot,sequence,width,height,ident)
                    if snapshot is None:continue
                    pixels,version=snapshot
                    with self.lock:
                        if ident not in self.visible or self.shared_versions.get(ident)==(hero,slot,version):continue
                        self.shared_versions[ident]=(hero,slot,version)
                    message=('frame-premultiplied',ident,width,height,pixels)
                    if ready:
                        with self.lock:
                            size=self.size.get(ident) if isinstance(self.size,dict) else self.size
                            if size and size!=(width,height):continue
                        if not self.premultiplied:
                            pixels=Image.frombytes('RGBa',(width,height),pixels).convert('RGBA').tobytes()
                        with self.lock:
                            if ident in self.visible:self.frames[ident]=(width,height,pixels)
                        continue
                if message[0] in ('frame','frame-premultiplied'):
                    _,ident,width,height,pixels = message
                    with self.lock:
                        if ident not in self.visible:continue
                        size=self.size.get(ident) if isinstance(self.size,dict) else self.size
                    # Keep the native premultiplied display pixels through
                    # resizing; RGBA resize otherwise adds two alpha conversions.
                    native=message[0]=='frame-premultiplied'
                    image=Image.frombytes('RGBa' if native else 'RGBA',(width,height),pixels,'raw','BGRa' if native else 'RGBA')
                    if size and size!=(width,height):image=image.resize(size,Image.Resampling.BILINEAR)
                    if self.premultiplied and not native:image=image.convert('RGBa')
                    if not self.premultiplied and native:image=image.convert('RGBA')
                    width,height=image.size;pixels=image.tobytes()
                with self.lock:
                    if message[0] in ('frame','frame-premultiplied'):
                        if ident in self.visible:self.frames[ident]=(width,height,pixels)
                    elif message[0]=='error':self.error=message[1]
        except (OSError,EOFError):pass
        except Exception as exc:
            with self.lock:self.error=str(exc)
        finally:
            self.shared.close();self.source.close();self.hero.close()

    def request(self, ids, aim=None, size=None, interaction=None, movement=None, transforms=None,hovered=None):
        if self.closed or not self.process.is_alive():return
        with self.lock:
            self.size=size
            self.visible=set(ids)
            self.shared_versions={key:value for key,value in self.shared_versions.items() if key in self.visible}
            self.frames={key:value for key,value in self.frames.items() if key in self.visible}
        try:self.connection.send({'ids':list(ids),'aim':aim or {},'interaction':interaction or {},'movement':movement or {},'transforms':transforms or {},'hovered':hovered,'size':size})
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
        self.converter.join(timeout=4)
        if self.converter.is_alive():self.converter.terminate();self.converter.join(timeout=4)
        self.connection.close();self.frame_connection.close();self.reader.join(timeout=1)
