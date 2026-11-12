"""Original Dreams simulation and shaders for the visible picker appearances.

One GPU context, independent native simulation/TAA per visible Imp. The pipe
only carries current viewport requests and newly rendered pixels, never video.
"""
import ctypes as C
from collections import OrderedDict
import json
from pathlib import Path
import runpy
import threading
import time
from carousel_native import crop_projection,HERO_FRAME,CAMERA


def run(connection, log_path, shared_name=None, source_name=None, source_connection=None):
    import os
    import traceback
    root = Path(__file__).resolve().parent
    log = open(log_path, 'w', encoding='utf-8', buffering=1)
    # Vulkan diagnostics must not open a console or disturb the cursor process.
    os.dup2(log.fileno(), 1); os.dup2(log.fileno(), 2)
    condition = threading.Condition()
    request = {'ids': [], 'aim': {}, 'stop': False}

    def receive():
        try:
            while True:
                update = connection.recv()
                with condition:
                    request.update(update)
                    condition.notify_all()
                if update.get('stop'):return
        except (EOFError, OSError):
            with condition:
                request['stop'] = True
                condition.notify_all()

    threading.Thread(target=receive, daemon=True).start()
    imps = OrderedDict()
    output_condition=threading.Condition()
    pending_output=OrderedDict()
    output_done=False
    sender=None
    send_lock=threading.Lock()
    sender_error=None
    shared=None
    source=None
    source_slot=0
    try:
        api = runpy.run_path(str(root/'desktop-imp.py'))
        if source_name:
            from gallery_shared_frames import SharedFrames
            from gallery_converter import SOURCE_SLOTS
            source=SharedFrames(source_name,slots=SOURCE_SLOTS,bytes_per_pixel=8)
        elif shared_name:
            from gallery_shared_frames import SharedFrames
            shared=SharedFrames(shared_name)
        def send_frames():
            nonlocal sender_error
            try:
                while True:
                    with output_condition:
                        while not pending_output and not output_done:output_condition.wait()
                        if not pending_output:return
                        ident,(raw,width,height,frame_slot,size)=pending_output.popitem(last=False)
                    if shared is not None:
                        if size and size!=(width,height) and size[0]*size[1]*4<=512*512*4:
                            from PIL import Image
                            pixels=api['decode'](raw).raw[:width*height*4]
                            image=Image.frombytes('RGBa',(width,height),pixels,'raw','BGRa').resize(size,Image.Resampling.BILINEAR)
                            width,height=size
                            sequence=shared.write_pixels(frame_slot,image.tobytes(),width,height,ident)
                            kind='shared-frame-ready-premultiplied'
                        else:
                            sequence=shared.write(frame_slot,raw,width,height,api['_cursor_decoder'](False),ident)
                            kind='shared-frame-premultiplied'
                        with send_lock:connection.send((kind,ident,frame_slot,sequence,width,height))
                    else:
                        pixels=api['decode'](raw).raw[:width*height*4]
                        with send_lock:connection.send(('frame-premultiplied',ident,width,height,pixels))
            except (BrokenPipeError,EOFError,OSError):
                with condition:request['stop']=True;condition.notify_all()
            except BaseException:
                sender_error=traceback.format_exc()
                with condition:request['stop']=True;condition.notify_all()
        if source is None:
            sender=threading.Thread(target=send_frames,daemon=True)
            sender.start()
        from character_store import catalog as appearance_catalog
        known = {item['id'] for item in appearance_catalog()}
        # Slots describe concurrently retained render histories, not the number
        # of selectable Imps. New Surprise appearances reuse evicted slots.
        active = (C.c_uint8*32)()
        indexes = {}
        order = []; next_index = 0; current = None; slot = 0
        next_cycle = 0.0
        current_projection = [0.] * 32

        def particles():
            nonlocal order, next_index, current, slot, next_cycle
            while True:
                with condition:
                    while not request['ids'] and not request['stop']:
                        # No simulation work while the picker is minimized.
                        condition.wait()
                    if request['stop']:return None
                    requested = tuple(request['ids'])
                    if any(i.removeprefix('hero:') not in known for i in requested):
                        known.update(item['id'] for item in appearance_catalog())
                    wanted = tuple(i for i in requested if i.removeprefix('hero:') in known)
                    aim = dict(request['aim'])
                    interaction = dict(request.get('interaction',{}))
                    movement = dict(request.get('movement',{}))
                    transforms = dict(request.get('transforms',{}))
                    hovered=request.get('hovered')
                if tuple(order) != wanted:
                    following=order[next_index] if order else None
                    order = list(wanted)
                    next_index=order.index(following) if following in order else min(next_index,max(0,len(order)-1))
                    next_cycle = 0.0
                    # Keep recently visible simulations alive while scrolling;
                    # recreating them at every edge causes a visible hitch.
                    while len(imps)>8:
                        oldest=next((key for key in imps if key not in wanted),None)
                        if oldest is None:break
                        imps.pop(oldest)[0].close()
                        active[indexes.pop(oldest)] = 0
                if not order:return None
                if next_index == 0:
                    delay = next_cycle-time.perf_counter()
                    if delay > 0:
                        with condition:condition.wait(timeout=delay)
                        continue
                    next_cycle = time.perf_counter()+1/60
                ident = order[next_index]
                next_index = (next_index+1)%len(order)
                now = time.perf_counter()
                if ident not in imps:
                    available=next((i for i in range(len(active)) if i not in indexes.values()),None)
                    if available is None:raise RuntimeError('Too many simultaneously visible Imp previews')
                    indexes[ident]=available
                    imp = api['Imp'](ident.removeprefix('hero:'))
                    reaction = api['Reactions'](imp,now,None,viewport=(0,0,1000,1000)) if ident.startswith('hero:') else None
                    if reaction is not None:reaction.poll_after = float('inf')
                    imps[ident] = [imp, now, now-1/30, reaction,'idle',now]
                    active[indexes[ident]] = 2
                imps.move_to_end(ident)
                state = imps[ident];current = state[0];slot = indexes[ident]
                frame=transforms.get(ident,HERO_FRAME)
                current_projection[:]=(*crop_projection(frame,1080*(.757 if ident.startswith('hero:') else .334))[0],*frame,*CAMERA['camera_frame'])
                dt = max(1/240, min(.1, now-state[2]));state[2] = now
                x,y = aim.get(ident,(0.0,0.0))
                if state[3] is not None:
                    # This is a stationary preview character, not another mouse
                    # cursor. Its own reaction clock chooses blinks and emotes.
                    mouse = api['MouseState'](500,500,True,32512)
                    state[3].menu_transform=frame
                    return state[3].update(mouse,now)
                clip='custom hover' if ident==hovered else 'idle'
                if clip!=state[4]:state[4]=clip;state[5]=now
                return current.frame(clip, now-state[5], x, y, dt, looping=True,
                                     menu_translation=movement.get(ident),menu_transform=transforms.get(ident))

        def present(raw, width, height):
            nonlocal source_slot
            ident=next(key for key,value in indexes.items() if value==slot)
            with condition:
                wanted=set(request['ids']);sizes=request.get('size');size=sizes.get(ident) if isinstance(sizes,dict) else sizes
            if source is not None:
                version=source.write_pointer(slot,raw,width,height,ident)
                source_connection.send(('source-frame',ident,slot,version,slot,width,height,size))
                active[slot]=1
                return True
            with output_condition:
                for stale in tuple(pending_output):
                    if stale not in wanted:del pending_output[stale]
                pending_output[ident]=(raw,width,height,slot,size)
                while len(pending_output)>32:pending_output.popitem(last=False)
                output_condition.notify()
            active[slot]=1
            return True

        api['GPU']['render'](particles,present,lambda:(current.stick,current.antenna_path),
                             lambda:current.eye_count,appearance=lambda:current.motion.body_color,
                             gallery=(active,lambda:slot),projection=lambda:current_projection,
                             pointer_present=source is not None)
        if sender_error:raise RuntimeError(sender_error)
    except (BrokenPipeError, EOFError):pass
    except BaseException:
        detail = traceback.format_exc()
        log.write(detail)
        try:
            with send_lock:connection.send(('error',detail))
        except (BrokenPipeError, EOFError, OSError):pass
    finally:
        with output_condition:output_done=True;output_condition.notify_all()
        if sender:sender.join(timeout=2)
        for imp, *_ in imps.values():imp.close()
        if shared and (sender is None or not sender.is_alive()):shared.close()
        if source_connection is not None:
            try:source_connection.send(('stop',))
            except (BrokenPipeError,EOFError,OSError):pass
            source_connection.close()
        if source:source.close()
        connection.close();log.close()
