"""Original Dreams simulation and shaders for the visible picker appearances.

One GPU context, independent native simulation/TAA per visible Imp. The pipe
only carries current viewport requests and newly rendered pixels, never video.
"""
import ctypes as C
import json
from pathlib import Path
import runpy
import threading
import time


def run(connection, log_path):
    import os
    import traceback
    from PIL import Image
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
    imps = {}
    try:
        api = runpy.run_path(str(root/'desktop-imp.py'))
        catalog = json.loads((root/'characters/catalog.json').read_text(encoding='utf-8'))
        indexes = {item['id']: i for i, item in enumerate(catalog)}
        active = (C.c_uint8*len(catalog))()
        order = []; next_index = 0; current = None; slot = 0
        next_cycle = 0.0

        def particles():
            nonlocal order, next_index, current, slot, next_cycle
            while True:
                with condition:
                    while not request['ids'] and not request['stop']:
                        # No simulation work while the picker is minimized.
                        condition.wait()
                    if request['stop']:return None
                    wanted = tuple(i for i in request['ids'] if i in indexes)
                    aim = dict(request['aim'])
                if tuple(order) != wanted:
                    order = list(wanted);next_index = 0;next_cycle = 0.0
                    for ident in list(imps):
                        if ident not in wanted:
                            imps.pop(ident)[0].close()
                    active[:] = bytes(len(active))
                    for ident in wanted:active[indexes[ident]] = 1
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
                    imp = api['Imp'](ident)
                    imps[ident] = [imp, now, now-1/30]
                state = imps[ident];current = state[0];slot = indexes[ident]
                dt = max(1/240, min(.1, now-state[2]));state[2] = now
                x,y = aim.get(ident,(0.0,0.0))
                return current.frame('idle', now-state[1], x, y, dt, looping=True)

        def present(raw, width, height):
            premultiplied = api['decode'](raw).raw[:width*height*4]
            image = Image.frombytes('RGBa',(width,height),premultiplied,'raw','BGRa').convert('RGBA')
            connection.send(('frame',catalog[slot]['id'],width,height,image.tobytes()))
            return True

        api['GPU']['render'](particles,present,lambda:(current.stick,current.antenna_path),
                             lambda:current.eye_count,appearance=lambda:current.motion.body_color,
                             gallery=(active,lambda:slot))
    except (BrokenPipeError, EOFError):pass
    except BaseException:
        detail = traceback.format_exc()
        log.write(detail)
        try:connection.send(('error',detail))
        except (BrokenPipeError, EOFError, OSError):pass
    finally:
        for imp, *_ in imps.values():imp.close()
        connection.close();log.close()
