"""Independent CPU conversion: latest frames, bounded RAM, original pixels."""
from collections import OrderedDict
import ctypes as C
from pathlib import Path
import traceback
from gallery_shared_frames import SharedFrames
from frame_helpers import library

SOURCE_SLOTS=32
HERO_SIDE=2048

def run(source_connection,output_connection,source_name,display_name,hero_name):
    source=display=hero=None
    try:
        source=SharedFrames(source_name,slots=SOURCE_SLOTS,bytes_per_pixel=8)
        display=SharedFrames(display_name)
        hero=SharedFrames(hero_name,slots=1,max_side=HERO_SIDE)
        helpers=library();decode=helpers.imp_decode_bgra;resize=helpers.imp_resize_rgba
        pixels=C.create_string_buffer(512*512*4)
        pending=OrderedDict();stopping=False;converted=[None]*SOURCE_SLOTS
        while not stopping:
            if not pending:
                message=source_connection.recv()
                if message[0]=='stop':break
                pending[message[1]]=message
            while source_connection.poll():
                message=source_connection.recv()
                if message[0]=='stop':stopping=True;break
                pending[message[1]]=message
                while len(pending)>32:pending.popitem(last=False)
            if stopping:break
            _,message=pending.popitem(last=False)
            _,ident,source_slot,version,display_slot,width,height,size=message
            snapshot=source.read(source_slot,version,width,height,ident)
            if snapshot is None:continue
            raw,actual_version=snapshot
            if converted[source_slot]==(ident,actual_version):continue
            converted[source_slot]=(ident,actual_version)
            target=hero if ident.startswith('hero:') else display
            target_slot=0 if target is hero else display_slot
            if size and size[0]>0 and size[1]>0 and size[0]*size[1]*4<=target.capacity and max(size)<=4096:
                decode(raw,pixels,width*height)
                sw,sh=width,height;width,height=size
                version=target.write_resized(target_slot,pixels,sw,sh,width,height,resize,ident)
                kind='shared-hero-ready-premultiplied' if target is hero else 'shared-frame-ready-premultiplied'
                display_slot=target_slot
            else:
                version=display.write(display_slot,raw,width,height,decode,ident)
                kind='shared-frame-premultiplied'
            output_connection.send((kind,ident,display_slot,version,width,height))
    except (EOFError,BrokenPipeError,OSError):pass
    except BaseException:
        try:output_connection.send(('error',traceback.format_exc()))
        except (EOFError,BrokenPipeError,OSError):pass
    finally:
        if source:source.close()
        if display:display.close()
        if hero:hero.close()
        source_connection.close();output_connection.close()
