import sys, math, cairo
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, '/home/user/video/src')
from gfx import *

def base():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s); t = 1.7
    sky(c, [(0, "#0B0F1A"), (0.35, "#3A1E3A"), (0.55, "#B8402E"), (0.62, "#FF9A3C")])
    sun(c, 1380, 610, 70, core="#FFE3A0", halo="#FF5A2A", ha=0.8)
    god_rays(c, 1380, 610, t, col="#FF9A5A", n=16, a=0.09, spread=3.0, length=2200)
    clouds(c, t, "#4A2438", 0.75, seed=77, n=9, ymin=40, ymax=420, smin=140, smax=260)
    sea(c, t, 620, top="#5A2A36", bottom="#05070D", amp=22, spec_x=1380, spec="#FFB060", spec_a=0.8, foam_a=0.5)
    # ship fading into the sea at the horizon
    cargo_ship(c, 1380, 650, 0.95, t, alpha=0.55, lights=0.8, bob=0)
    for i in range(60):
        rnd = random.Random(i); p = rnd.random()
        rgba(c, (1, 0.9, 0.8), 0.6 * (1 - p)); c.arc(1380 + rnd.uniform(-330, 330), 560 - p * 260, rnd.uniform(2, 6), 0, TAU); c.fill()
    fog(c, t, 700, 260, "#E8A080", 0.18)
    karim(c, 470, 1640, 1500, 0.9, dir=1, expr="shock", look=(0.85, -0.1), wind=1.0,
          pose=dict(ls=1.9, le=1.6, rs=1.5, re=1.4, head=0.08))
    vignette(c, 0.75)
    return Image.frombuffer("RGBA", (W, H), bytes(s.get_data()), "raw", "BGRA", 0, 1).convert("RGB")

def text(im, lines, font, sizes, x, y, fills, rtl=False):
    d = ImageDraw.Draw(im)
    for line, size, fill in zip(lines, sizes, fills):
        f = ImageFont.truetype(font, size)
        kw = dict(direction="rtl", language="ar") if rtl else {}
        bb = d.textbbox((0, 0), line, font=f, stroke_width=14, **kw)
        w = bb[2] - bb[0]
        # drop shadow
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        sd.text((x - w / 2 + 12, y + 14), line, font=f, fill=(0, 0, 0, 200), stroke_width=14, stroke_fill=(0, 0, 0, 200), **kw)
        im.paste(sh.filter(ImageFilter.GaussianBlur(10)), (0, 0), sh.filter(ImageFilter.GaussianBlur(10)))
        d.text((x - w / 2, y), line, font=f, fill=fill, stroke_width=14, stroke_fill=(8, 8, 12), **kw)
        y += int(size * 1.08)

img = base()
en = img.copy()
text(en, ["VANISHED", "AT SEA"], "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", [200, 170], 1330, 120,
     [(255, 214, 64), (255, 255, 255)])
en.save("/home/user/video/out/thumbnail_en.png")
ar = img.copy()
text(ar, ["اختفت", "في البحر"], "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", [250, 190], 1390, 60,
     [(255, 214, 64), (255, 255, 255)], rtl=True)
ar.save("/home/user/video/out/thumbnail_ar.png")
print("ok")
