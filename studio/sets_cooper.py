"""Sets for the D.B. Cooper series (also reusable: plane, sky, forest, river, office, map, props)."""
import math
import random

import skia

from .character import paint, OUTLINE
from .scenes import (BACKGROUNDS, GROUND, vgrad, glow, outlined_rect, font, rain, col)


# ------------------------------------------------------------------ cabin
SEAT = 0xFF3B4A6B


def seat(c, x, front=False):
    """Airline seat facing right; hip of a seated passenger goes at (x, 745)."""
    if not front:
        outlined_rect(c, x - 118, 470, x - 58, 790, SEAT, 18, 7)
        outlined_rect(c, x - 112, 470, x - 64, 520, 0xFFE8E2D4, 10, 4)  # headrest cover
    outlined_rect(c, x - 118, 752, x + 46, 800, SEAT, 14, 7)
    outlined_rect(c, x - 30, 800, x - 6, GROUND, 0xFF2A2A30, 4, 5)


def bg_cabin(c, t, W, H, o):
    night = o.get("night", True)
    vgrad(c, 0xFFCFC8B8 if not night else 0xFF8E8A80, 0xFF6E6A62 if night else 0xFFA8A296, skia.Rect.MakeWH(W, H))
    # ceiling curve + overhead bins
    p = skia.Path()
    p.moveTo(0, 0)
    p.lineTo(W, 0)
    p.lineTo(W, 120)
    p.quadTo(W / 2, 170, 0, 120)
    p.close()
    c.drawPath(p, paint(0xFF5E5A52))
    for x in range(-60, W, 420):
        outlined_rect(c, x, 150, x + 400, 260, 0xFFD9D3C4 if not night else 0xFFA29C90, 16, 6)
        c.drawLine(x + 30, 240, x + 370, 240, paint(0x33000000, 4))
    # windows
    for i, x in enumerate(range(140, W, 300)):
        r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x, 320, x + 110, 450), 46, 46)
        c.drawRRect(r, paint(0xFF55524A))
        inner = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x + 12, 332, x + 98, 438), 38, 38)
        sky = skia.Paint(AntiAlias=True)
        sky.setShader(skia.GradientShader.MakeLinear([(0, 332), (0, 438)],
                                                     [0xFF0A1024, 0xFF1C2A4A] if night else [0xFF9CC8F0, 0xFFE6F2FF]))
        c.drawRRect(inner, sky)
        if o.get("rain"):
            rnd = random.Random(i)
            for k in range(6):
                yy = 332 + ((rnd.random() * 106 + t * 60) % 106)
                xx = x + 20 + rnd.random() * 70
                c.drawLine(xx, yy, xx - 8, yy + 10, paint(0x88B8C8E8, 2))
        c.drawRRect(r, paint(OUTLINE, 6))
    c.drawRect(skia.Rect.MakeLTRB(0, 470, W, 480), paint(0x22000000))
    vgrad(c, 0xFF3A3A48, 0xFF22222C, skia.Rect.MakeLTRB(0, GROUND, W, H))
    c.drawLine(0, GROUND, W, GROUND, paint(OUTLINE, 6))
    for x in o.get("seats", [380, 980, 1580]):
        seat(c, x)
    lights = [(x + 200, 270, 420, 0xFFFFE9C0, 0.35 if night else 0.5) for x in range(-60, W, 420)]
    return GROUND, lights


# ------------------------------------------------------------------ the jet
def jet(c, x, y, s=1.0, stairs=0.0, night=True, flip=False):
    """Side view of a three-engine trijet with a rear airstair. (x, y) = nose bottom."""
    c.save()
    c.translate(x, y)
    if flip:
        c.scale(-s, s)
    else:
        c.scale(s, s)
    body = 0xFFE9E9EC if not night else 0xFFB8BCC6
    # rear airstair (under the tail)
    if stairs > 0:
        c.save()
        c.translate(1180, 40)
        c.rotate(20 + 30 * stairs)
        outlined_rect(c, -10, 0, 30, 260 * stairs, 0xFF8A8E98, 6, 6)
        for k in range(1, int(10 * stairs)):
            c.drawLine(-6, k * 26, 26, k * 26, paint(OUTLINE, 4))
        c.restore()
    # wing (far)
    w = skia.Path()
    w.moveTo(520, 10)
    w.lineTo(820, 10)
    w.lineTo(980, 80)
    w.lineTo(900, 90)
    w.close()
    c.drawPath(w, paint(0xFF8A8E98))
    c.drawPath(w, paint(OUTLINE, 6))
    # fuselage
    f = skia.Path()
    f.moveTo(0, 0)
    f.cubicTo(-30, -40, 20, -120, 140, -130)
    f.lineTo(1150, -130)
    f.lineTo(1330, -90)
    f.lineTo(1330, -50)
    f.lineTo(1180, 40)
    f.lineTo(60, 40)
    f.close()
    c.drawPath(f, paint(body))
    c.drawPath(f, paint(OUTLINE, 9))
    c.drawRect(skia.Rect.MakeLTRB(100, -60, 1200, -44), paint(0xFFB0302A))  # cheat line
    # windows
    for wx in range(220, 1100, 46):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(wx, -100, wx + 20, -78), 8, 8),
                    paint(0xFFFFE7A8 if night else 0xFF33404F))
    # cockpit windows
    cp = skia.Path()
    cp.moveTo(40, -70)
    cp.lineTo(80, -110)
    cp.lineTo(150, -110)
    cp.lineTo(150, -72)
    cp.close()
    c.drawPath(cp, paint(0xFF1C2433))
    c.drawPath(cp, paint(OUTLINE, 5))
    # tail fin (T-tail) + 3 engines
    fin = skia.Path()
    fin.moveTo(1120, -130)
    fin.lineTo(1250, -400)
    fin.lineTo(1340, -400)
    fin.lineTo(1320, -90)
    fin.close()
    c.drawPath(fin, paint(0xFFB0302A))
    c.drawPath(fin, paint(OUTLINE, 8))
    outlined_rect(c, 1200, -420, 1420, -394, body, 10, 6)
    outlined_rect(c, 1060, -200, 1260, -140, 0xFF9AA0AA, 30, 7)
    outlined_rect(c, 1230, -320, 1360, -270, 0xFF9AA0AA, 24, 6)
    # gear
    for gx in (160, 700, 760):
        c.drawLine(gx, 40, gx, 90, paint(OUTLINE, 10))
        c.drawCircle(gx, 100, 22, paint(OUTLINE))
        c.drawCircle(gx, 100, 10, paint(0xFF55585E))
    c.restore()


def bg_tarmac(c, t, W, H, o):
    vgrad(c, 0xFF070B18, 0xFF1A2236, skia.Rect.MakeWH(W, H))
    rnd = random.Random(2)
    for _ in range(40):
        c.drawCircle(rnd.random() * W, rnd.random() * 380, 1.5, paint(0x88FFFFFF))
    # terminal silhouette + runway lights
    c.drawRect(skia.Rect.MakeLTRB(0, 560, 700, 760), paint(0xFF141A28))
    for x in range(20, 700, 40):
        c.drawRect(skia.Rect.MakeLTRB(x, 600, x + 18, 620), paint(0xFFE8C46A))
    vgrad(c, 0xFF2A2D36, 0xFF15161B, skia.Rect.MakeLTRB(0, 760, W, H))
    for x in range(0, W, 90):
        c.drawCircle(x + (t * 4) % 90, 790, 4, paint(0xFF6FA8FF))
    jet(c, o.get("jet_x", 260), o.get("jet_y", 760), o.get("jet_s", 1.0), o.get("stairs", 0.0))
    if o.get("truck"):
        tx = o.get("truck_x", 1500)
        outlined_rect(c, tx, 680, tx + 300, 800, 0xFFD9A23A, 14, 7)
        outlined_rect(c, tx + 300, 700, tx + 380, 800, 0xFFB98418, 10, 7)
        for wx in (tx + 60, tx + 240, tx + 340):
            c.drawCircle(wx, 810, 26, paint(OUTLINE))
            c.drawCircle(wx, 810, 12, paint(0xFF55585E))
    lights = [(1500, 300, 900, 0xFFFFE6B0, 0.5)]
    if o.get("police"):
        on = int(t * 4) % 2
        lights.append((1700, 760, 420, 0xFFFF3030 if on else 0xFF3060FF, 0.8))
    return GROUND, lights


# ------------------------------------------------------------------ sky / storm
def cloud(c, x, y, s, color):
    for dx, dy, r in ((0, 0, 90), (90, -30, 110), (200, 0, 90), (110, 30, 100)):
        c.drawCircle(x + dx * s, y + dy * s, r * s, paint(color))


def parachute(c, x, y, s=1.0, color=0xFFD9C29A):
    """Canopy above (x, y) = the jumper's shoulders."""
    top = y - 420 * s
    p = skia.Path()
    p.moveTo(x - 260 * s, top + 120 * s)
    p.cubicTo(x - 240 * s, top - 40 * s, x + 240 * s, top - 40 * s, x + 260 * s, top + 120 * s)
    for k in range(4, -1, -1):
        px = x - 260 * s + k * 130 * s
        p.quadTo(px + 65 * s, top + 90 * s, px, top + 120 * s) if k < 4 else None
    p.close()
    c.drawPath(p, paint(color))
    c.drawPath(p, paint(OUTLINE, 8))
    for k in range(1, 4):
        px = x - 260 * s + k * 130 * s
        c.drawLine(px, top + 112 * s, x + (k - 2) * 60 * s, top + 10 * s, paint(0x55000000, 4))
    for k in range(5):
        px = x - 260 * s + k * 130 * s
        c.drawLine(px, top + 120 * s, x + (k - 2) * 8, y - 30 * s, paint(0xAA222222, 3))


def bg_sky(c, t, W, H, o):
    vgrad(c, 0xFF05070F, 0xFF161C2C, skia.Rect.MakeWH(W, H))
    rnd = random.Random(4)
    speed = o.get("wind", 220)
    for layer, (alpha_col, n, sc) in enumerate(((0xFF1A2030, 7, 1.6), (0xFF232A3C, 6, 1.1), (0xFF2E3548, 5, 0.8))):
        for i in range(n):
            x = (rnd.random() * (W + 800) - t * speed * (0.5 + layer * 0.4)) % (W + 800) - 400
            y = rnd.random() * H
            cloud(c, x, y, sc, alpha_col)
    if o.get("jet"):
        jx = o.get("jet_x", 200) + o.get("_lt", 0) * o.get("jet_speed", 0)
        jet(c, jx, o.get("jet_y", 400), o.get("jet_s", 0.5), o.get("stairs", 0.0))
    if o.get("lightning"):
        ph = (t * 0.37) % 1.0
        if ph < 0.04 or 0.08 < ph < 0.1:
            c.drawRect(skia.Rect.MakeWH(W, H), paint(0x88DDE6FF))
    if o.get("parachute"):
        px, py = o["parachute"]
        parachute(c, px, py + math.sin(t * 1.5) * 8, 1.0)
    return 2000, []


# ------------------------------------------------------------------ forest / river
def pine(c, x, base, h, color):
    p = skia.Path()
    p.moveTo(x, base - h)
    for k in range(4):
        yy = base - h + (k + 1) * h / 4.3
        ww = (k + 1) * h / 9
        p.lineTo(x + ww, yy)
        p.lineTo(x + ww * 0.45, yy)
    p.lineTo(x + h / 12, base)
    p.lineTo(x - h / 12, base)
    for k in range(3, -1, -1):
        yy = base - h + (k + 1) * h / 4.3
        ww = (k + 1) * h / 9
        p.lineTo(x - ww * 0.45, yy)
        p.lineTo(x - ww, yy)
    p.close()
    c.drawPath(p, paint(color))


def bg_forest(c, t, W, H, o):
    night = o.get("night", True)
    vgrad(c, 0xFF070A12 if night else 0xFF8FB0C8, 0xFF1A2230 if night else 0xFFD6E2E6, skia.Rect.MakeWH(W, H))
    for layer, (colr, hmin, base) in enumerate(((0xFF141C26, 380, 760), (0xFF0F151D, 480, 830), (0xFF0A0E14, 620, 920))):
        if not night:
            colr = (0xFF6E8A82, 0xFF4E6C60, 0xFF2E4A3E)[layer]
        rnd = random.Random(layer + 9)
        x = -60
        while x < W + 80:
            pine(c, x, base, hmin + rnd.random() * 160, colr)
            x += 70 + rnd.random() * 90
        if layer == 0:  # mist between layers
            m = skia.Paint(AntiAlias=True)
            m.setShader(skia.GradientShader.MakeLinear([(0, 620), (0, 800)], [0x00AAB4C8, 0x33AAB4C8]))
            c.drawRect(skia.Rect.MakeLTRB(0, 600, W, 800), m)
    vgrad(c, 0xFF141A14 if night else 0xFF3E5236, 0xFF080A08, skia.Rect.MakeLTRB(0, GROUND, W, H))
    return GROUND, []


def bg_riverbank(c, t, W, H, o):
    vgrad(c, 0xFFA9C9E6, 0xFFE9F0F2, skia.Rect.MakeWH(W, H))
    # far shore + trees
    c.drawRect(skia.Rect.MakeLTRB(0, 470, W, 520), paint(0xFF5E7A5A))
    rnd = random.Random(1)
    for i in range(30):
        x = i * 70 + rnd.random() * 30
        c.drawCircle(x, 470, 30 + rnd.random() * 30, paint(0xFF4E6A48))
    # river
    rp = skia.Paint(AntiAlias=True)
    rp.setShader(skia.GradientShader.MakeLinear([(0, 520), (0, 760)], [0xFF4D7C9A, 0xFF6E9AB4]))
    c.drawRect(skia.Rect.MakeLTRB(0, 520, W, 760), rp)
    for i in range(14):
        y = 540 + i * 16
        x = (i * 173 + t * 40) % (W + 200) - 100
        c.drawLine(x, y, x + 90, y, paint(0x55FFFFFF, 3))
    # sandbank
    sp = skia.Path()
    sp.moveTo(0, 760)
    sp.quadTo(W / 2, 700, W, 770)
    sp.lineTo(W, H)
    sp.lineTo(0, H)
    sp.close()
    c.drawPath(sp, paint(0xFFD9C08E))
    c.drawPath(sp, paint(OUTLINE, 6))
    rnd = random.Random(5)
    for _ in range(120):
        x, y = rnd.random() * W, 790 + rnd.random() * 280
        c.drawCircle(x, y, 1.5 + rnd.random() * 2, paint(0x33000000))
    if o.get("money"):
        mx, my = o.get("money_at", [1180, 935])
        for k in range(5):
            c.save()
            c.translate(mx + k * 26 - 40, my + (k % 2) * 8)
            c.rotate(-12 + k * 9)
            outlined_rect(c, -40, -16, 40, 16, 0xFF9DB58A, 3, 3)
            c.drawString("20", -12, 8, font(20, "Black"), paint(0xFF3E5A34))
            c.restore()
    return GROUND, [(1500, 120, 900, 0xFFFFF1C8, 0.35)]


# ------------------------------------------------------------------ FBI office
def bg_fbi(c, t, W, H, o):
    vgrad(c, 0xFF3A3328, 0xFF241F18, skia.Rect.MakeWH(W, H))
    # window with blinds
    outlined_rect(c, 1420, 160, 1800, 560, 0xFF1A2236, 6, 10)
    for y in range(170, 560, 22):
        c.drawRect(skia.Rect.MakeLTRB(1426, y, 1794, y + 12), paint(0xFF8A7E66))
    # cork board
    outlined_rect(c, 260, 170, 1160, 640, 0xFFA87B4E, 8, 12)
    pins = [(340, 220, "PHOTO"), (600, 240, "NOTE"), (880, 220, "TIE"), (420, 430, "MAP"), (760, 430, "$20"),
            (1020, 420, "?")]
    for (x, y, kind) in pins:
        outlined_rect(c, x, y, x + 140, y + 170, 0xFFF4EFE2, 3, 5)
        if kind == "PHOTO":  # sketch of the suspect: round head + dark glasses
            c.drawCircle(x + 70, y + 80, 46, paint(0xFFFFFFFF))
            c.drawCircle(x + 70, y + 80, 46, paint(OUTLINE, 4))
            c.drawPath(_arc_hair(x + 70, y + 80), paint(0xFF241C17))
            for ex in (x + 52, x + 88):
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(ex - 14, y + 70, ex + 14, y + 90), 6, 6),
                            paint(0xFF0B0B0D))
        else:
            c.drawString(kind, x + 70 - font(40, "Black").measureText(kind) / 2, y + 100,
                         font(40, "Black"), paint(0xFF333333))
        c.drawCircle(x + 70, y + 12, 8, paint(0xFFD32F2F))
    red = paint(0xFFD32F2F, 4)
    for a, b in ((0, 1), (1, 2), (0, 3), (3, 4), (4, 5), (2, 5), (1, 4)):
        c.drawLine(pins[a][0] + 70, pins[a][1] + 12, pins[b][0] + 70, pins[b][1] + 12, red)
    vgrad(c, 0xFF2E261E, 0xFF120E0A, skia.Rect.MakeLTRB(0, GROUND, W, H))
    c.drawLine(0, GROUND, W, GROUND, paint(OUTLINE, 6))
    # desk + lamp
    outlined_rect(c, 1200, 700, 1820, 740, 0xFF5A4030, 6)
    outlined_rect(c, 1240, 740, 1270, GROUND, 0xFF5A4030, 4)
    outlined_rect(c, 1750, 740, 1780, GROUND, 0xFF5A4030, 4)
    c.drawLine(1650, 700, 1620, 600, paint(OUTLINE, 10))
    lamp = skia.Path()
    lamp.moveTo(1570, 610)
    lamp.lineTo(1680, 590)
    lamp.lineTo(1650, 540)
    lamp.lineTo(1590, 550)
    lamp.close()
    c.drawPath(lamp, paint(0xFF2E5E3A))
    c.drawPath(lamp, paint(OUTLINE, 6))
    outlined_rect(c, 1300, 670, 1460, 700, 0xFFE9E3D2, 3, 4)  # files
    return GROUND, [(1620, 640, 520, 0xFFFFD890, 0.8), (700, 380, 700, 0xFFFFE6B0, 0.3)]


def _arc_hair(x, y):
    p = skia.Path()
    p.moveTo(x - 46, y - 4)
    p.cubicTo(x - 50, y - 60, x + 30, y - 66, x + 46, y - 16)
    p.cubicTo(x + 20, y - 34, x - 10, y - 36, x - 34, y - 2)
    p.close()
    return p


# ------------------------------------------------------------------ map
CITIES = {"PORTLAND": (980, 760), "SEATTLE": (960, 250), "RENO": (1180, 1040)}


def bg_map(c, t, W, H, o):
    c.clear(0xFF161A22)
    # land and sea
    sea = skia.Path()
    sea.moveTo(0, 0)
    sea.lineTo(560, 0)
    sea.cubicTo(600, 200, 520, 380, 620, 520)
    sea.cubicTo(660, 700, 560, 900, 600, H)
    sea.lineTo(0, H)
    sea.close()
    c.drawRect(skia.Rect.MakeWH(W, H), paint(0xFF2B3528))
    c.drawPath(sea, paint(0xFF1A2A3A))
    c.drawPath(sea, paint(0xFF0E141C, 6))
    # Puget Sound
    ps = skia.Path()
    ps.moveTo(700, 120)
    ps.cubicTo(760, 220, 880, 260, 900, 380)
    ps.cubicTo(860, 330, 760, 300, 720, 240)
    ps.close()
    c.drawPath(ps, paint(0xFF1A2A3A))
    # Columbia River
    cr = skia.Path()
    cr.moveTo(600, 660)
    cr.cubicTo(760, 700, 900, 720, 1000, 740)
    cr.cubicTo(1200, 770, 1500, 720, W, 760)
    c.drawPath(cr, paint(0xFF3E6A8A, 14))
    # grid
    for x in range(0, W, 120):
        c.drawLine(x, 0, x, H, paint(0x11FFFFFF, 1))
    for y in range(0, H, 120):
        c.drawLine(0, y, W, y, paint(0x11FFFFFF, 1))
    f = font(30, "Black")
    for name, (x, y) in CITIES.items():
        if y > H:
            continue
        c.drawCircle(x, y, 12, paint(0xFFFFFFFF))
        c.drawString(name, x + 22, y + 10, f, paint(0xFFFFFFFF))
    c.drawString("WASHINGTON", 1250, 420, font(44, "Black"), paint(0x33FFFFFF))
    c.drawString("OREGON", 1300, 900, font(44, "Black"), paint(0x33FFFFFF))
    c.drawString("PACIFIC OCEAN", 120, 500, font(36, "Black"), paint(0x33FFFFFF))
    # routes: list of [from, to, progress_start, progress_end] animated across the shot
    k = min(1.0, o.get("_lt", t) / max(0.1, o.get("route_time", 4.0)))
    for leg in o.get("routes", []):
        a = CITIES.get(leg[0], leg[0]) if isinstance(leg[0], str) else leg[0]
        b = CITIES.get(leg[1], leg[1]) if isinstance(leg[1], str) else leg[1]
        prog = leg[2] if len(leg) > 2 and leg[2] == 1 else k
        if isinstance(b, (list, tuple)) and b[1] > H:
            b = (b[0], H + 40)
        x = a[0] + (b[0] - a[0]) * prog
        y = a[1] + (b[1] - a[1]) * prog
        dash = paint(0xFFFF4040, 8)
        dash.setPathEffect(skia.DashPathEffect.Make([24, 16], -t * 60))
        c.drawLine(a[0], a[1], x, y, dash)
        c.drawCircle(x, y, 10, paint(0xFFFF4040))
    if o.get("circle"):  # holding pattern over Puget Sound
        cx, cy = o["circle"]
        a = t * 1.6
        c.drawCircle(cx, cy, 110, paint(0x88FF4040, 5))
        c.drawCircle(cx + math.cos(a) * 110, cy + math.sin(a) * 110, 12, paint(0xFFFF4040))
    if o.get("zone"):
        zx, zy = o["zone"]
        pulse = 1 + 0.08 * math.sin(t * 4)
        c.drawCircle(zx, zy, 150 * pulse, paint(0x44FFC020))
        c.drawCircle(zx, zy, 150 * pulse, paint(0xFFFFC020, 5))
        c.drawString(o.get("zone_label", "JUMP ZONE?"), zx + 160, zy, font(34, "Black"), paint(0xFFFFC020))
    if o.get("pin"):
        px, py = o["pin"]
        c.drawCircle(px, py, 18, paint(0xFF4CAF50))
        c.drawString(o.get("pin_label", ""), px + 26, py + 10, font(30, "Black"), paint(0xFF9CE29E))
    return GROUND, []


# ------------------------------------------------------------------ close-up props
def bg_note(c, t, W, H, o):
    c.clear(0xFF151310)
    glow(c, W / 2, H / 2, 900, 0xFFFFE6B0, 0.35)
    c.save()
    c.translate(W / 2, H / 2)
    c.rotate(-4 + math.sin(t * 0.8) * 0.6)
    outlined_rect(c, -460, -260, 460, 260, 0xFFF3EEDF, 6, 6)
    for y in range(-200, 260, 56):
        c.drawLine(-430, y, 430, y, paint(0x332E6BB0, 2))
    lines = o.get("lines", ["I HAVE A BOMB", "IN MY BRIEFCASE."])
    f = font(78, "Bold")
    shown = int(min(len("".join(lines)), o.get("_lt", t) * 18))
    n = 0
    for i, line in enumerate(lines):
        part = line[: max(0, shown - n)]
        n += len(line)
        c.drawString(part, -400, -110 + i * 120, f, paint(0xFF1A1A1A))
    c.restore()
    return GROUND, []


def bg_briefcase(c, t, W, H, o):
    c.clear(0xFF0F0F12)
    glow(c, W / 2, 460, 900, 0xFFFFD890, 0.4)
    # open briefcase
    outlined_rect(c, 460, 300, 1460, 360, 0xFF3A2416, 14, 8)  # lid edge
    outlined_rect(c, 460, 360, 1460, 860, 0xFF4A2E1C, 20, 10)
    outlined_rect(c, 500, 400, 1420, 820, 0xFF2A1A10, 12, 6)
    for i in range(8):  # red sticks
        outlined_rect(c, 560 + i * 60, 470, 600 + i * 60, 760, 0xFFC0302A, 14, 6)
    outlined_rect(c, 1080, 520, 1360, 700, 0xFF2E2E34, 10, 6)  # battery
    wire_cols = [0xFFE53935, 0xFFFDD835, 0xFF1E88E5]
    for k, colr in enumerate(wire_cols):
        p = skia.Path()
        p.moveTo(600 + k * 120, 500)
        p.cubicTo(800 + k * 60, 380 + math.sin(t + k) * 6, 1000, 820, 1100 + k * 60, 560)
        c.drawPath(p, paint(OUTLINE, 12))
        c.drawPath(p, paint(colr, 7))
    return GROUND, []


def bg_money(c, t, W, H, o):
    c.clear(0xFF1A1612)
    glow(c, W / 2, 400, 900, 0xFFFFD890, 0.45)
    outlined_rect(c, 0, 760, W, H, 0xFF4A3424, 0, 6)
    # canvas bag
    bag = skia.Path()
    bag.moveTo(1180, 760)
    bag.cubicTo(1120, 520, 1240, 420, 1380, 430)
    bag.cubicTo(1520, 420, 1640, 520, 1580, 760)
    bag.close()
    c.drawPath(bag, paint(0xFFB8A27A))
    c.drawPath(bag, paint(OUTLINE, 9))
    c.drawString("$", 1340, 640, font(120, "Black"), paint(0xFF6E5A3A))
    for row in range(3):
        for k in range(4):
            x, y = 360 + k * 170, 700 - row * 46
            outlined_rect(c, x, y, x + 150, y + 44, 0xFF9DB58A, 4, 5)
            c.drawString("20", x + 56, y + 32, font(26, "Black"), paint(0xFF3E5A34))
    if o.get("serials"):
        c.drawString("SERIAL NUMBERS RECORDED", 360, 300, font(52, "Black"), paint(0xFFFFFFFF))
    return GROUND, []


def bg_newspaper(c, t, W, H, o):
    c.clear(0xFF0E0E10)
    c.save()
    c.translate(W / 2, H / 2)
    spin = max(0.0, 1 - o.get("_lt", t) / 0.6)
    c.rotate(-3 - spin * 380)
    c.scale(1 - spin * 0.8, 1 - spin * 0.8)
    outlined_rect(c, -620, -420, 620, 420, 0xFFEDE6D3, 4, 6)
    c.drawString(o.get("paper", "THE DAILY RECORD"), -560, -330, font(48, "Black"), paint(0xFF222222))
    c.drawLine(-580, -300, 580, -300, paint(0xFF222222, 4))
    lines = o.get("headline", ["HIJACKER JUMPS", "WITH $200,000"])
    for i, line in enumerate(lines):
        f = font(110, "Black")
        c.drawString(line, -f.measureText(line) / 2, -170 + i * 125, f, paint(0xFF111111))
    for y in range(110, 400, 30):
        c.drawLine(-560, y, -40, y, paint(0x55222222, 10))
        c.drawLine(40, y, 560, y, paint(0x55222222, 10))
    c.restore()
    return GROUND, []


BACKGROUNDS.update({"cabin": bg_cabin, "tarmac": bg_tarmac, "sky": bg_sky, "forest": bg_forest,
                    "riverbank": bg_riverbank, "fbi": bg_fbi, "map": bg_map, "note": bg_note,
                    "briefcase": bg_briefcase, "money": bg_money, "newspaper": bg_newspaper})


# ------------------------------------------------------------------ props
def drink_prop(c, hand, angle):
    c.save()
    c.translate(hand[0], hand[1] - 14)
    p = skia.Path()
    p.moveTo(-18, -40)
    p.lineTo(18, -40)
    p.lineTo(14, 10)
    p.lineTo(-14, 10)
    p.close()
    c.drawPath(p, paint(0x66D8EEFF))
    c.drawRect(skia.Rect.MakeLTRB(-15, -16, 15, 9), paint(0xCCC27A2A))
    c.drawPath(p, paint(OUTLINE, 4))
    c.restore()


def cigarette_prop(c, hand, angle):
    c.save()
    c.translate(hand[0] + 10, hand[1] - 10)
    c.drawLine(0, 0, 40, -8, paint(OUTLINE, 9))
    c.drawLine(0, 0, 40, -8, paint(0xFFF4F4F4, 6))
    c.drawCircle(42, -8, 5, paint(0xFFFF6A2A))
    c.restore()
    glow(c, hand[0] + 52, hand[1] - 18, 60, 0xFFFF7A3A, 0.7)


def briefcase_prop(c, hand, angle):
    c.save()
    c.translate(hand[0], hand[1])
    outlined_rect(c, -70, 10, 70, 110, 0xFF4A2E1C, 10, 7)
    c.drawLine(-20, 10, -20, -4, paint(OUTLINE, 7))
    c.drawLine(20, 10, 20, -4, paint(OUTLINE, 7))
    c.drawLine(-20, -4, 20, -4, paint(OUTLINE, 7))
    c.restore()


def bag_prop(c, hand, angle):
    c.save()
    c.translate(hand[0], hand[1])
    bag = skia.Path()
    bag.moveTo(-50, 110)
    bag.cubicTo(-70, 30, -30, 0, 0, 0)
    bag.cubicTo(30, 0, 70, 30, 50, 110)
    bag.close()
    c.drawPath(bag, paint(0xFFB8A27A))
    c.drawPath(bag, paint(OUTLINE, 6))
    c.restore()


PROPS = {"drink": drink_prop, "cigarette": cigarette_prop, "briefcase": briefcase_prop, "bag": bag_prop}
