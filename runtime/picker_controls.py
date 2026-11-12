"""Soft, rounded picker controls; independent of the original Imp artwork."""
from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

GROUPS = ('All Imps', 'Classic Imps', 'Halloween', 'Art’s Dream',
          'Special editions', 'Internal presets')
SCALE = 3

@lru_cache(maxsize=8)
def font(size):
    return ImageFont.truetype(str(Path(__file__).resolve().parent/'fonts/SourceSansPro-Regular.ttf'), size*SCALE)

def text(draw, position, value, size=16, fill='#563453'):
    draw.text(tuple(round(v*SCALE) for v in position), value,
              font=font(size), fill=fill, anchor='mm')

@lru_cache(maxsize=40)
def pill(width, height, label='', grid=0, expanded=False):
    image=Image.new('RGBA', (width*SCALE,height*SCALE))
    shadow=ImageDraw.Draw(image)
    shadow.rounded_rectangle((5*SCALE,9*SCALE,(width-5)*SCALE,(height-3)*SCALE),
                             radius=(height/2-6)*SCALE,fill=(12,3,26,130))
    image=image.filter(ImageFilter.GaussianBlur(3*SCALE))
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((4*SCALE,4*SCALE,(width-4)*SCALE,(height-8)*SCALE),
                           radius=(height/2-6)*SCALE,fill='#ecd9e9',
                           outline='#f8edf4',width=SCALE)
    if grid:
        for row in range(3):
            for col in range(3):
                x,y=20+col*6,17+row*6
                draw.rounded_rectangle((x*SCALE,y*SCALE,(x+4)*SCALE,(y+4)*SCALE),
                                       radius=SCALE,fill='#6d456d')
        text(draw,(width-24,height/2-2),str(grid),20)
    else:
        text(draw,((width-28)/2,height/2-2),label)
        x,y=width-25,height/2-2
        delta=-3 if expanded else 3
        draw.line(((x-5)*SCALE,(y-delta)*SCALE,x*SCALE,(y+delta)*SCALE,
                   (x+5)*SCALE,(y-delta)*SCALE),fill='#795275',width=2*SCALE)
    return image.resize((width,height),Image.Resampling.LANCZOS)

@lru_cache(maxsize=24)
def category_panel(width, selected):
    height=len(GROUPS)*46+16
    image=Image.new('RGBA',(width*SCALE,height*SCALE))
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((2*SCALE,2*SCALE,(width-2)*SCALE,(height-2)*SCALE),
                           radius=22*SCALE,fill=(103,74,116,250),
                           outline='#d8bddd',width=SCALE)
    for index,label in enumerate(GROUPS):
        top=8+index*46
        if label==selected:
            draw.rounded_rectangle((8*SCALE,top*SCALE,(width-8)*SCALE,(top+42)*SCALE),
                                   radius=21*SCALE,fill='#ecdae9')
        text(draw,(width/2,top+21),label,fill='#563453' if label==selected else '#f7ecf5')
    return image.resize((width,height),Image.Resampling.LANCZOS)

@lru_cache(maxsize=40)
def size_slider(width, value):
    height=56
    image=pill(width,height,'').copy()
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((6,6,width-6,height-10),radius=20,fill='#ecd9e9')
    text_draw=ImageDraw.Draw(image)
    f=ImageFont.truetype(str(Path(__file__).resolve().parent/'fonts/SourceSansPro-Regular.ttf'),16)
    text_draw.text((18,14),'Imp size',font=f,fill='#563453')
    text_draw.text((width-52,14),f'{value:g}×',font=f,fill='#563453')
    start,end=92,width-68
    draw.line((start,27,end,27),fill='#b79ab6',width=4)
    x=start+(end-start)*(value-.5)/1.5
    draw.ellipse((x-9,18,x+9,36),fill='#785477',outline='#fff4fc',width=2)
    return image


@lru_cache(maxsize=16)
def player_slider(width, value):
    image=size_slider(width, 0.5+(value-1)*0.5).copy()
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((8,8,88,40),radius=10,fill='#ecd9e9')
    draw.rounded_rectangle((width-64,8,width-8,40),radius=10,fill='#ecd9e9')
    f=ImageFont.truetype(str(Path(__file__).resolve().parent/'fonts/SourceSansPro-Regular.ttf'),16)
    draw.text((18,14),'Player',font=f,fill='#563453')
    draw.text((width-52,14),f'P{value}',font=f,fill='#563453')
    return image
