"""Dreams-style central preview and native idle/hover bottom carousel."""

import json,math,os,random,subprocess,sys,time

from pathlib import Path

import pygame

from PIL import Image

from app_paths import ROOT,STATE,READY,ERROR,write_json

from gallery_client import GalleryClient

from picker_controls import GROUPS,category_panel

from cloud_background import CloudBackground
from picker_window import PickerWindow,FULLSCREEN_EVENT
from carousel_native import anchor_frame,crop_projection,HERO_FRAME
from native_buttons import NativeButtons,layout as native_button_layout
from hover_bounds import HoverBounds
import menu_music
from picker_layout import content_bounds,content_point

from app import category,display_name,named_handle,TITLE
from character_store import catalog as appearance_catalog,generate_surprises
from surprise_carousel import SurpriseCarousel





def surface(image):

    return pygame.image.frombytes(image.tobytes(),image.size,'RGBA').convert_alpha()





def main():

    pygame.init();pygame.display.set_caption(TITLE)
    # Use the native Imp icon for the SDL window and its taskbar entry.
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Dreams.Imp.Cursor')
    icon=Image.open(ROOT/'app.ico').convert('RGBA')
    pygame.display.set_icon(pygame.image.frombytes(icon.tobytes(),icon.size,'RGBA'))

    window_flags=pygame.NOFRAME|pygame.RESIZABLE|pygame.DOUBLEBUF
    screen=pygame.display.set_mode((1280,720),window_flags,vsync=1)
    window=PickerWindow()
    window.toggle_fullscreen()
    screen=pygame.display.get_surface()

    clock=pygame.time.Clock();settings_path=STATE/'settings.json'

    try:settings=json.loads(settings_path.read_text(encoding='utf-8-sig'))

    except (OSError,ValueError):settings={}

    menu_music.start(settings)

    selected=settings.get('character','00_default')

    items=appearance_catalog()
    surprise_carousel=SurpriseCarousel(generate_surprises)
    surprises=surprise_carousel.items

    favorites=set(settings.get('favorites',[]));group='All Imps';mode='imps';opened=False;selected_button=None

    offset=target=0.;drag=None;preview=None;worker=None;log=None;changing=False;pending=None;deadline=0

    images={};cache={};background=None;bgsize=None;running=True;error=False
    clouds=CloudBackground(ROOT/'picker-assets/cloud-animation.zip');cloud_surface=None
    font=None;fontsize=None
    button_renderer=NativeButtons(STATE/'native-ui.log');button_overlay=None
    hover_bounds=HoverBounds()
    canvas=None

    artwork={name:pygame.image.load(str(ROOT/'picker-assets'/f'{name}.png')).convert_alpha() for name in ('shuffle','imps','favorites','back','settings','previous','title-imp','selected')}

    stop=__import__('runpy').run_path(str(ROOT/'win-imp-overlay.py'))['stop']

    def filtered():
        if mode=='surprise':return surprises
        return sorted((i for i in items if (mode=='favorites' and i['id'] in favorites or mode!='favorites' and not i.get('generated')) and (group=='All Imps' or category(i['id'])==group)),key=lambda i:(i['id']!='00_default',display_name(i).casefold()))

    def select(ident):

        nonlocal selected,changing,pending,deadline

        selected=ident;pending=ident;changing=True;deadline=time.monotonic()+10;stop()

    def save_settings():
        # Cursor hotkeys can change these while this picker remains open.
        try:
            latest=json.loads(settings_path.read_text(encoding='utf-8-sig'))
            for key in ('cursor_size','player'):
                if key in latest:settings[key]=latest[key]
        except (OSError,ValueError):pass
        write_json(settings_path,settings)

    def cached(key,maker):

        if key not in cache:cache[key]=surface(maker())

        return cache[key]

    try:

        while running:

            dt=min(.05,clock.tick(120)/1000)
            viewport=content_bounds(*screen.get_size());_,_,w,h=viewport
            if canvas is None or canvas.get_size()!=(w,h):canvas=pygame.Surface((w,h))
            scale=w/1920;ui_scale=w/1280

            current=filtered();spacing=w/8;thumbh=round(h*.334);thumbw=thumbh

            def rect(x,y,rw,rh):return pygame.Rect(round(x*w),round(y*h),round(rw*w),round(rh*h))

            buttons={name:pygame.Rect(values) for name,values in native_button_layout(mode,w,h).items()}
            if offset<.01 and target<.01:buttons.pop('previous')

            catwidth=max(1,round(284*ui_scale));catleft=(w-catwidth)/2
            catrow=46*ui_scale

            for event in pygame.event.get():
                if event.type in (pygame.MOUSEBUTTONDOWN,pygame.MOUSEBUTTONUP,pygame.MOUSEMOTION):
                    event.pos=content_point(event.pos,viewport)

                if event.type==pygame.QUIT:running=False

                elif event.type==pygame.VIDEORESIZE:
                    screen=pygame.display.get_surface()

                elif event.type==FULLSCREEN_EVENT:
                    window.toggle_fullscreen();screen=pygame.display.get_surface()

                elif event.type==pygame.MOUSEWHEEL:target=max(0,min(max(0,len(current)-1),round(target)-event.y))

                elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:

                    x,y=event.pos;hit=next((name for name,r in buttons.items() if r.collidepoint(x,y)),None)

                    if hit=='back':running=False

                    elif hit=='shuffle':
                        mode='surprise';selected_button='shuffle';opened=False;target=offset=0
                        surprise_carousel.extend()

                    elif hit=='imps':mode='imps';selected_button='imps';opened=not opened

                    elif hit=='favorites':
                        mode='favorites' if mode!='favorites' else 'imps';selected_button='favorites' if mode=='favorites' else None;target=offset=0;opened=False

                    elif hit=='settings':
                        favorites.add(selected);settings['favorites']=sorted(favorites);save_settings()

                    elif hit=='previous':target=0

                    elif window.fullscreen and y<h*.18 and getattr(event,'clicks',1)>=2:
                        window.toggle_fullscreen();screen=pygame.display.get_surface()

                    elif opened and catleft<=x<=catleft+catwidth and h*.18<=y<h*.18+len(GROUPS)*catrow:

                        group=GROUPS[int((y-h*.18)//catrow)];target=offset=0;opened=False

                    else:drag=('carousel',x,y,offset)

                elif event.type==pygame.MOUSEBUTTONDOWN and event.button==3:

                    if rect(.38,.19,.24,.46).collidepoint(event.pos):

                        if selected in favorites:favorites.remove(selected)

                        else:favorites.add(selected)

                        settings['favorites']=sorted(favorites);save_settings()

                elif event.type==pygame.MOUSEMOTION and drag:

                    if drag[0]=='carousel':offset=max(0,min(max(0,len(current)-1),drag[3]-(event.pos[0]-drag[1])/spacing));target=offset

                elif event.type==pygame.MOUSEBUTTONUP and event.button==1 and drag:

                    if drag[0]=='carousel':

                        if math.hypot(event.pos[0]-drag[1],event.pos[1]-drag[2])<8:
                            if drag[2]>h*.65:
                                idx=min(range(len(current)),key=lambda i:abs(crop_projection(anchor_frame(i-offset,item_index=i),1080*.334)[1][0]*w/1920-event.pos[0])) if current else -1
                                if 0<=idx<len(current):select(current[idx]['id'])
                            elif rect(.38,.19,.24,.46).collidepoint(event.pos):select(selected)

                        else:target=round(offset)

                    drag=None

                elif event.type==pygame.KEYDOWN:

                    if event.key==pygame.K_F11 or (event.key==pygame.K_RETURN and event.mod&pygame.KMOD_ALT):
                        window.toggle_fullscreen();screen=pygame.display.get_surface()

                    elif event.key==pygame.K_ESCAPE:
                        if window.fullscreen:window.toggle_fullscreen();screen=pygame.display.get_surface()
                        opened=False

                    elif event.key in (pygame.K_LEFT,pygame.K_RIGHT):target=max(0,min(max(0,len(current)-1),round(target)+(1 if event.key==pygame.K_RIGHT else -1)))

            menu_music.set_focus(pygame.key.get_focused())

            if surprise_carousel.poll():items=appearance_catalog()
            if mode=='surprise':surprise_carousel.ensure_ahead(max(offset,target))

            if changing:

                if not named_handle('Local\\DreamsStandaloneImp.Active') and (worker is None or worker.poll() is not None):

                    if log:log.close()

                    log=(STATE/'renderer.log').open('w',encoding='utf-8');READY.unlink(missing_ok=True);ERROR.unlink(missing_ok=True)

                    worker=subprocess.Popen([sys.executable,str(ROOT/'desktop-imp.py'),'--run','--character',pending],cwd=ROOT,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)

                    settings['character']=pending;save_settings();changing=False

                elif time.monotonic()>deadline:changing=False

            if worker and worker.poll() is not None:worker=None

            if not drag:offset+=(target-offset)*min(1,dt*14)

            resized=bgsize!=(w,h)
            if resized:
                background=pygame.Surface((w,h));background.fill((8,5,23));bgsize=(w,h);cache.clear()

            cloud_frame=clouds.take()
            if cloud_frame:
                _,dimensions,pixels=cloud_frame
                cloud_surface=pygame.image.frombytes(pixels,dimensions,'RGB').convert()
            if clouds.problem:raise RuntimeError('Cloud background: '+clouds.problem)
            if cloud_surface:
                if cloud_frame or resized:
                    background=pygame.transform.smoothscale(cloud_surface,(w,h))
                canvas.blit(background,(0,0))
            else:canvas.blit(background,(0,0))

            desired_fontsize=max(1,round(38*scale))
            if fontsize!=desired_fontsize:
                font=pygame.font.Font(str(ROOT/'fonts/SourceSansPro-Regular.ttf'),desired_fontsize);fontsize=desired_fontsize

            canvas.blit(pygame.transform.smoothscale(artwork['title-imp'],(round(39*scale),round(52*scale))),(round(w*.053),round(h*.083)))
            title={'surprise':'Imp Surprise','favorites':'My Imps'}.get(mode,'Imp Carousel')
            canvas.blit(font.render(title,True,(242,237,233)),(round(w*.08),round(h*.083)))

            visible=[];sizes={};positions={};transforms={}

            for idx,item in enumerate(current):

                frame=anchor_frame(idx-offset,item_index=idx)
                _,native_centre=crop_projection(frame,1080*.334)
                x=native_centre[0]*w/1920

                if -thumbw/2<x<w+thumbw/2:

                    ident=item['id'];visible.append(ident);sizes[ident]=(thumbw,thumbh);positions[ident]=(round(x),round(native_centre[1]*h/1080))
                    # Replay captured carousel layout transforms, including their
                    # scale and rotation, through the original spring solver.
                    transforms[ident]=frame

            hero='hero:'+selected;visible.append(hero);sizes[hero]=(round(h*.757),round(h*.757))
            _,hero_centre=crop_projection(HERO_FRAME,1080*.757)
            positions[hero]=(round(hero_centre[0]*w/1920),round(hero_centre[1]*h/1080));transforms[hero]=HERO_FRAME

            if preview is None and not error:preview=GalleryClient(STATE/'gallery.log',premultiplied=True)

            hovered=None
            if preview:
                mx,my=content_point(pygame.mouse.get_pos(),viewport)
                hovered=next((ident for ident in visible if not ident.startswith('hero:') and
                              abs(mx-positions[ident][0])<spacing*.45 and h*.65<my<h*.91),None)
                preview.request(visible,transforms=transforms,size=sizes,hovered=hovered if not drag else None)

                frames,problem=preview.take()

                if problem or not preview.process.is_alive():

                    pygame.display.set_caption(TITLE+' â€” preview error; see gallery.log');preview.close();preview=None;error=True

                for ident,(fw,fh,pixels) in frames.items():images[ident]=pygame.image.frombytes(pixels,(fw,fh),'RGBA').convert_alpha()

                images={key:value for key,value in images.items() if key in visible}

            for ident in visible:

                if ident in images:
                    image=images[ident]
                    if image.get_size()!=sizes[ident]:image=pygame.transform.smoothscale(image,sizes[ident])
                    canvas.blit(image,image.get_rect(center=positions[ident]),special_flags=pygame.BLEND_PREMULTIPLIED)


            pointer=content_point(pygame.mouse.get_pos(),viewport)
            hit_rect=next((rect for rect in buttons.values() if rect.collidepoint(pointer)),None)
            if hit_rect is None and hovered is not None:
                hit_rect=pygame.Rect(0,0,round(spacing*.9),round(h*.26))
                hit_rect.center=positions[hovered]
            if hit_rect is not None:
                hit_rect=hit_rect.move(viewport[0],viewport[1])
            hover_bounds.publish(window.hwnd,hit_rect if pygame.mouse.get_focused() else None)
            button_hover=next((name for name,r in buttons.items() if r.collidepoint(pointer)),None)
            button_renderer.request(hovered=button_hover,mode=mode,selected_button=selected_button,previous='previous' in buttons,selected_x=positions[selected][0]*1920/w if selected in positions else None)
            native_frame,native_problem=button_renderer.take()
            if native_problem:raise RuntimeError('Native UI renderer: '+native_problem)
            if native_frame:
                fw,fh,pixels=native_frame
                button_overlay=pygame.image.frombytes(pixels,(fw,fh),'RGBA').convert_alpha()
            if button_overlay is not None:
                overlay=button_overlay if button_overlay.get_size()==(w,h) else pygame.transform.smoothscale(button_overlay,(w,h))
                canvas.blit(overlay,(0,0),special_flags=pygame.BLEND_PREMULTIPLIED)

            if opened:
                panel=cached(('category',group),lambda:category_panel(284,group))
                panel_size=(catwidth,max(1,round(panel.get_height()*ui_scale)))
                canvas.blit(pygame.transform.smoothscale(panel,panel_size),(catleft,h*.18))

            screen.fill((8,5,23));screen.blit(canvas,viewport[:2])
            pygame.display.flip()

    finally:
        button_renderer.close()
        hover_bounds.publish(None,None)
        hover_bounds.close()
        menu_music.stop()
        window.close()
        clouds.close()

        if preview:preview.close()

        # The selected cursor owns its tray and crash-recovery guard. Closing
        # the picker releases the gallery/cloud resources, not that cursor.

        if log:log.close()

        pygame.quit()

