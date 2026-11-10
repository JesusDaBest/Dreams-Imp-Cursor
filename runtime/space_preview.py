"""Purple-space presentation for the picker; the Imp artwork stays unchanged."""
from functools import lru_cache
import math
import random
import time
import tkinter as tk
from PIL import Image, ImageDraw, ImageFilter, ImageTk


@lru_cache(maxsize=8)
def space_image(width, height, seed=29):
    # Render the soft background once, not on every animation frame.
    small = Image.new('RGB', (max(1, width//3), max(1, height//3)))
    pixels = small.load()
    for y in range(small.height):
        for x in range(small.width):
            u, v = x/small.width, y/small.height
            cloud = math.exp(-((u-.24)**2/.28 + (v-.38)**2/.16))
            rose = math.exp(-((u-.92)**2/.25 + (v-.84)**2/.15))
            haze = math.exp(-((u-.65)**2/.38 + (v-.08)**2/.12))
            pixels[x,y] = (round(24+31*cloud+35*rose),
                           round(12+12*cloud+6*rose+10*haze),
                           round(46+47*cloud+17*rose+24*haze))
    result = small.resize((width,height),Image.Resampling.BICUBIC).convert('RGBA')
    randomizer = random.Random(seed)
    bokeh = Image.new('RGBA',result.size)
    draw = ImageDraw.Draw(bokeh)
    for _ in range(15):
        x,y = randomizer.uniform(-.1,1.1)*width,randomizer.random()*height
        radius = randomizer.uniform(.015,.07)*min(width,height)
        draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=(188,153,235,randomizer.randrange(5,17)))
    result = Image.alpha_composite(result,bokeh.filter(ImageFilter.GaussianBlur(max(.5,width/180))))
    stars = Image.new('RGBA',result.size)
    draw = ImageDraw.Draw(stars)
    for _ in range(max(18,round(width*height/2400))):
        x,y = randomizer.randrange(width),randomizer.randrange(height)
        alpha = randomizer.randrange(40,140)
        radius = .5 if randomizer.random()<.8 else 1
        draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=(229,214,255,alpha))
    return Image.alpha_composite(result,stars)


def card_image(imp):
    result = space_image(124,176).copy()
    artwork = imp.convert('RGBA').resize((110,160),Image.Resampling.LANCZOS)
    result.alpha_composite(artwork,(7,8))
    return result


class SpacePreview(tk.Canvas):
    """Gently float the original thumbnail without deforming or recolouring it."""
    def __init__(self,parent):
        super().__init__(parent,width=340,height=350,bg='#221238',highlightthickness=0)
        self.artwork=None
        self.background_id=self.create_image(0,0,anchor='nw')
        self.imp_id=self.create_image(170,175)
        self.started=time.monotonic()
        self.resize_job=None
        self.frame_job=None
        self.bind('<Configure>',self.resize)
        self.bind('<Map>',self.animate)
        self.bind('<Unmap>',self.suspend)
        self.bind('<Destroy>',self.suspend)

    def set_imp(self,image):
        self.artwork=image.convert('RGBA').copy()
        self.redraw()

    def resize(self,event):
        if self.resize_job:self.after_cancel(self.resize_job)
        self.resize_job=self.after(80,self.redraw)

    def redraw(self):
        self.resize_job=None
        w,h=max(2,self.winfo_width()),max(2,self.winfo_height())
        if w<10 or h<10:return
        self.background=ImageTk.PhotoImage(space_image(w,h))
        self.itemconfigure(self.background_id,image=self.background)
        if self.artwork is not None:
            scale=min((w-36)/self.artwork.width,(h-24)/self.artwork.height)
            artwork=self.artwork.resize((max(1,round(self.artwork.width*scale)),
                                        max(1,round(self.artwork.height*scale))),Image.Resampling.LANCZOS)
            self.imp_image=ImageTk.PhotoImage(artwork)
            self.itemconfigure(self.imp_id,image=self.imp_image)
        self.position()

    def position(self):
        t=time.monotonic()-self.started
        self.coords(self.imp_id,self.winfo_width()/2+2*math.sin(t*.55),
                    self.winfo_height()/2+5*math.sin(t*.9))

    def animate(self,event=None):
        if self.frame_job:return
        if not self.winfo_viewable():return
        self.position()
        self.frame_job=self.after(50,self.tick)

    def tick(self):
        self.frame_job=None
        self.animate()

    def suspend(self,event=None):
        for job in (self.frame_job,self.resize_job):
            if job:
                try:self.after_cancel(job)
                except tk.TclError:pass
        self.frame_job=self.resize_job=None
