"""Backgrounds, props and lighting. Each background is f(canvas, t, W, H, opts)
and returns the ground y and an optional list of light sources drawn after
the character: (x, y, radius, color, intensity)."""
import math
import random
import skia
from .character import paint, OUTLINE

GROUND = 900


def col(v):
    return int(v, 16) if isinstance(v, str) else v


def vgrad(c, top, bottom, rect):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear(
        [(rect.left(), rect.top()), (rect.left(), rect.bottom())], [top, bottom]))
    c.drawRect(rect, p)


def glow(c, x, y, r, color, a=1.0):
    p = skia.Paint(AntiAlias=True)
    col = skia.Color4f.FromColor(color)
    c0 = skia.Color4f(col.fR, col.fG, col.fB, 0.55 * a).toColor()
    c1 = skia.Color4f(col.fR, col.fG, col.fB, 0.18 * a).toColor()
    p.setShader(skia.GradientShader.MakeRadial((x, y), r, [c0, c1, 0x00000000], [0, 0.35, 1]))
    p.setBlendMode(skia.BlendMode.kScreen)
    c.drawCircle(x, y, r, p)


def outlined_rect(c, l, t, r, b, color, radius=8, stroke=8):
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(l, t, r, b), radius, radius)
    c.drawRRect(rr, paint(color))
    c.drawRRect(rr, paint(OUTLINE, stroke))


def font(size, weight="Black"):
    tf = skia.Typeface.MakeFromFile(f"/usr/share/fonts/opentype/inter/Inter-{weight}.otf")
    return skia.Font(tf, size)


# ---------------------------------------------------------------- props
def phone_prop(c, hand, angle, on=True):
    c.save()
    c.translate(hand[0], hand[1])
    c.rotate(-angle + 180)
    outlined_rect(c, -22, -40, 22, 34, 0xFF1C1C22, 8, 6)
    if on:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-16, -33, 16, 26), 4, 4), paint(0xFF9FD3FF))
    c.restore()


def alarm_clock(c, x, y, text="5:00", s=1.0, ring=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    if ring:
        c.rotate(math.sin(ring * 60) * 4)
    outlined_rect(c, -120, -70, 120, 70, 0xFF2B2B30, 26, 10)
    outlined_rect(c, -100, -50, 100, 50, 0xFF0B0B0D, 14, 4)
    f = font(78, "Bold")
    p = paint(0xFFFF3B30)
    w = f.measureText(text)
    c.drawString(text, -w / 2, 28, f, p)
    c.restore()
    glow(c, x, y, 220 * s, 0xFFFF3B30, 0.7)


# ---------------------------------------------------------------- backgrounds
def bg_bedroom(c, t, W, H, o):
    night = o.get("time", "night") == "night"
    wall = (0xFF1D2233, 0xFF141826) if night else (0xFF5A5F7A, 0xFF3D4157)
    vgrad(c, wall[0], wall[1], skia.Rect.MakeWH(W, H))
    # window
    wx, wy = 1300, 200
    sky = (0xFF0B1230, 0xFF1B2A55) if night else (0xFFF6B26B, 0xFFFFE3A3)
    vgrad(c, sky[0], sky[1], skia.Rect.MakeLTRB(wx, wy, wx + 360, wy + 320))
    if night:
        c.drawCircle(wx + 260, wy + 90, 36, paint(0xFFE9E6D3))
        rnd = random.Random(3)
        for _ in range(18):
            sx, sy = wx + rnd.random() * 360, wy + rnd.random() * 320
            c.drawCircle(sx, sy, 2 + (math.sin(t * 2 + sx) + 1), paint(0xAAFFFFFF))
    else:
        c.drawCircle(wx + 180, wy + 300, 70, paint(0xFFFFF4D6))
    c.drawRect(skia.Rect.MakeLTRB(wx, wy, wx + 360, wy + 320), paint(OUTLINE, 14))
    c.drawLine(wx + 180, wy, wx + 180, wy + 320, paint(OUTLINE, 10))
    c.drawLine(wx, wy + 160, wx + 360, wy + 160, paint(OUTLINE, 10))
    # floor
    vgrad(c, 0xFF2A2420 if night else 0xFF6B5444, 0xFF15110E, skia.Rect.MakeLTRB(0, GROUND, W, H))
    c.drawLine(0, GROUND, W, GROUND, paint(OUTLINE, 6))
    # bed
    bx = o.get("bed_x", 260)
    outlined_rect(c, bx, 690, bx + 820, 800, 0xFF3D3150, 18)
    outlined_rect(c, bx - 30, 560, bx + 30, GROUND, 0xFF4A3426, 10)
    outlined_rect(c, bx + 800, 640, bx + 850, GROUND, 0xFF4A3426, 10)
    outlined_rect(c, bx + 40, 640, bx + 230, 705, 0xFFDAD6E8, 30)  # pillow
    # nightstand
    outlined_rect(c, bx + 880, 720, bx + 1080, GROUND, 0xFF4A3426, 8)
    lights = []
    if not night:
        lights.append((wx + 180, wy + 200, 700, 0xFFFFC27A, 0.6))
    return GROUND, lights


def blanket(c, o):
    bx = o.get("bed_x", 260)
    p = skia.Path()
    p.moveTo(bx + 360, 700)
    p.cubicTo(bx + 430, 610, bx + 600, 640, bx + 800, 650)
    p.lineTo(bx + 810, 790)
    p.lineTo(bx + 350, 790)
    p.close()
    c.drawPath(p, paint(0xFF5B4B7A))
    c.drawPath(p, paint(OUTLINE, 10))


def bg_desk(c, t, W, H, o):
    vgrad(c, 0xFF1A1F2C, 0xFF10131C, skia.Rect.MakeWH(W, H))
    # shelf + posters
    outlined_rect(c, 200, 180, 520, 420, 0xFF2A3145, 6)
    outlined_rect(c, 1400, 260, 1700, 300, 0xFF4A3426, 6)
    for i in range(5):
        outlined_rect(c, 1420 + i * 52, 160, 1460 + i * 52, 260, [0xFF8C3B3B, 0xFF3B6E8C, 0xFF8C7A3B, 0xFF4E8C3B, 0xFF6B3B8C][i], 4, 5)
    vgrad(c, 0xFF231D19, 0xFF120F0C, skia.Rect.MakeLTRB(0, GROUND, W, H))
    c.drawLine(0, GROUND, W, GROUND, paint(OUTLINE, 6))
    return GROUND, []


def desk_front(c, t, o):
    """Streaming setup: monitor with game glow, mic arm, RGB strip, LIVE sign."""
    dx = o.get("desk_x", 1020)
    screen_on = o.get("screen", True)
    live = o.get("live", False)
    # gaming chair (behind character)
    outlined_rect(c, 700, 470, 830, 790, 0xFF1C1D24, 40, 8)
    c.drawLine(745, 500, 745, 760, paint(0xFFFF3DAE, 6))
    outlined_rect(c, 760, 760, 990, 795, 0xFF1C1D24, 10)
    outlined_rect(c, 860, 795, 890, GROUND, 0xFF1C1D24, 4)
    # desk + RGB strip
    outlined_rect(c, dx, 700, dx + 620, 735, 0xFF22232B, 6)
    hue = (t * 0.25) % 1.0
    strip = skia.Paint(AntiAlias=True)
    strip.setShader(skia.GradientShader.MakeLinear(
        [(dx + 640 * hue - 640, 0), (dx + 640 * hue + 640, 0)],
        [0xFF2EE6FF, 0xFFFF3DAE, 0xFF7C4DFF, 0xFF2EE6FF], None, skia.TileMode.kRepeat))
    c.drawRect(skia.Rect.MakeLTRB(dx + 6, 733, dx + 614, 742), strip)
    outlined_rect(c, dx + 30, 742, dx + 60, GROUND, 0xFF22232B, 4)
    outlined_rect(c, dx + 560, 742, dx + 590, GROUND, 0xFF22232B, 4)
    # monitor
    outlined_rect(c, dx + 120, 410, dx + 520, 650, 0xFF0E0F14, 12, 10)
    if screen_on:
        sp = skia.Paint(AntiAlias=True)
        g = [col(v) for v in o.get("screen_colors", [0xFF3A7BFF, 0xFFB04DFF])]
        sp.setShader(skia.GradientShader.MakeLinear([(dx + 130, 420), (dx + 510, 640)], g))
        c.drawRect(skia.Rect.MakeLTRB(dx + 134, 424, dx + 506, 636), sp)
        # little game blobs flashing
        if "viewers" in o:
            f = font(34, "Black")
            c.drawRect(skia.Rect.MakeLTRB(dx + 140, 430, dx + 330, 476), paint(0xCC000000))
            c.drawCircle(dx + 160, 453, 9, paint(0xFFFF2D55))
            c.drawString(f"{o['viewers']} watching", dx + 176, 466, font(28, "Bold"), paint(0xFFFFFFFF))
        for i in range(4):
            fx = dx + 170 + ((t * 120 + i * 95) % 320)
            c.drawCircle(fx, 560 - 40 * math.sin(t * 3 + i), 10, paint(0xCCFFFFFF))
    outlined_rect(c, dx + 300, 650, dx + 340, 700, 0xFF0E0F14, 4, 6)
    # keyboard
    outlined_rect(c, dx + 40, 686, dx + 260, 702, 0xFF2EE6FF if screen_on else 0xFF30323C, 6, 5)
    # mic on boom arm
    c.drawLine(dx + 600, 700, dx + 560, 470, paint(OUTLINE, 12))
    c.drawLine(dx + 560, 470, dx + 450, 440, paint(OUTLINE, 12))
    outlined_rect(c, dx + 420, 410, dx + 470, 480, 0xFF2A2B33, 22, 6)
    # LIVE sign on the wall
    if live:
        on = int(t * 1.5) % 2 == 0
        outlined_rect(c, dx + 200, 300, dx + 400, 380, 0xFF2A0D14, 14, 8)
        f = font(56, "Black")
        c.drawString("LIVE", dx + 236, 362, f, paint(0xFFFF2D55 if on else 0xFF6A1A2A))
        if on:
            glow(c, dx + 300, 340, 240, 0xFFFF2D55, 0.6)
    if screen_on:
        return [(dx + 320, 520, 700, g[0], 0.9), (dx + 320, 740, 400, 0xFFFF3DAE, 0.4)]
    return []


def bg_street(c, t, W, H, o):
    vgrad(c, 0xFF0D1020, 0xFF22243A, skia.Rect.MakeWH(W, H))
    rnd = random.Random(7)
    # skyline
    x = -40
    while x < W:
        w = rnd.randint(110, 220)
        h = rnd.randint(220, 520)
        c.drawRect(skia.Rect.MakeLTRB(x, GROUND - h, x + w, GROUND), paint(0xFF161929))
        for wy in range(int(GROUND - h + 30), GROUND - 60, 54):
            for wx in range(x + 18, x + w - 30, 44):
                if rnd.random() < 0.28:
                    c.drawRect(skia.Rect.MakeLTRB(wx, wy, wx + 20, wy + 28), paint(0xFFE8C46A))
        x += w + 10
    vgrad(c, 0xFF2B2D36, 0xFF15161B, skia.Rect.MakeLTRB(0, GROUND, W, H))
    c.drawLine(0, GROUND, W, GROUND, paint(OUTLINE, 6))
    lights = []
    for lx in (300, 1100, 1900):
        lx2 = lx - (o.get("scroll", 0) * t) % 800
        c.drawLine(lx2, GROUND, lx2, 420, paint(OUTLINE, 18))
        c.drawLine(lx2, 420, lx2 + 70, 420, paint(OUTLINE, 14))
        c.drawCircle(lx2 + 70, 432, 16, paint(0xFFFFE2A0))
        lights.append((lx2 + 70, 520, 380, 0xFFFFC870, 0.8))
    return GROUND, lights


def rain(c, t, W, H, density=140):
    rnd = random.Random(11)
    p = paint(0x66B8C8E8, 3)
    for i in range(density):
        x0 = rnd.random() * (W + 300)
        sp = 1400 + rnd.random() * 600
        y = (rnd.random() * H + t * sp) % (H + 100) - 50
        x = x0 - (y * 0.25)
        c.drawLine(x, y, x - 10, y + 38, p)


def bg_gym(c, t, W, H, o):
    vgrad(c, 0xFF2A2F3A, 0xFF1A1D25, skia.Rect.MakeWH(W, H))
    for i in range(4):
        outlined_rect(c, 140 + i * 460, 120, 460 + i * 460, 520, 0xFF3A4150, 6, 6)
    # rack + dumbbells
    outlined_rect(c, 1380, 640, 1800, 670, 0xFF444A55, 6)
    for i in range(5):
        cx = 1420 + i * 80
        c.drawCircle(cx, 620, 26, paint(OUTLINE))
        c.drawCircle(cx, 620, 20, paint(0xFF555A66))
    vgrad(c, 0xFF3A2E26, 0xFF1C1612, skia.Rect.MakeLTRB(0, GROUND, W, H))
    c.drawLine(0, GROUND, W, GROUND, paint(OUTLINE, 6))
    return GROUND, [(960, 80, 900, 0xFFFFF1D6, 0.45)]


def bg_mountain(c, t, W, H, o):
    k = o.get("sun", 0.6)  # 0 = pre-dawn, 1 = sunrise
    top = 0xFF1B2140 if k < 0.5 else 0xFF2E3F7A
    vgrad(c, top, 0xFFF29A5C, skia.Rect.MakeWH(W, H))
    sun_y = 760 - k * 300
    glow(c, 1400, sun_y, 700, 0xFFFFB86B, 0.9)
    c.drawCircle(1400, sun_y, 90, paint(0xFFFFE0A8))
    # far range
    p = skia.Path()
    p.moveTo(0, 700)
    for i, (x, y) in enumerate([(200, 520), (420, 640), (700, 420), (980, 600), (1250, 470), (1550, 620), (1800, 500), (1920, 560)]):
        p.lineTo(x, y)
    p.lineTo(1920, 1080)
    p.lineTo(0, 1080)
    p.close()
    c.drawPath(p, paint(0xFF3B2E4A))
    # near slope (character climbs it): from bottom-left up to summit at right
    q = skia.Path()
    q.moveTo(0, 1000)
    q.lineTo(1250, 730)
    q.lineTo(1500, 710)
    q.lineTo(1920, 760)
    q.lineTo(1920, 1080)
    q.lineTo(0, 1080)
    q.close()
    c.drawPath(q, paint(0xFF1E1826))
    c.drawPath(q, paint(OUTLINE, 8))
    return GROUND, []


def slope_y(x):
    if x < 1250:
        return 1000 + (730 - 1000) * x / 1250
    if x < 1500:
        return 730 + (710 - 730) * (x - 1250) / 250
    return 710 + (760 - 710) * (x - 1500) / 420


def bg_void(c, t, W, H, o):
    c.clear(0xFF0B0B0F)
    glow(c, W / 2, 380, 760, col(o.get("color", 0xFFBFC8FF)), 0.55)
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial((W / 2, GROUND + 10), 420,
                                               [0x55FFFFFF, 0x00FFFFFF]))
    c.drawOval(skia.Rect.MakeLTRB(W / 2 - 420, GROUND - 40, W / 2 + 420, GROUND + 60), p)
    return GROUND, []


def bg_clock(c, t, W, H, o):
    c.clear(0xFF07070A)
    alarm_clock(c, W / 2, H / 2, o.get("clock", "5:00"), 2.4, ring=t if o.get("ring") else 0)
    return GROUND, []


BACKGROUNDS = {
    "bedroom": bg_bedroom, "desk": bg_desk, "street": bg_street, "gym": bg_gym,
    "mountain": bg_mountain, "void": bg_void, "clock": bg_clock,
}
