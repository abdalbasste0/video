"""Sea sets: open ocean with a sailing ship, deck, captain's cabin, Atlantic map, courtroom, logbook."""
import math
import random

import skia

from .character import paint, OUTLINE
from .scenes import BACKGROUNDS, GROUND, vgrad, glow, outlined_rect, font, col

SKIES = {
    "day": (0xFF8DB8DE, 0xFFE4EEF2, 0xFF2E6A8E, 0xFF1C4A66),
    "dusk": (0xFF2C2F5A, 0xFFF0A070, 0xFF2A4A66, 0xFF16283A),
    "night": (0xFF05070F, 0xFF1A2236, 0xFF0E1C2C, 0xFF060C14),
    "storm": (0xFF1C2028, 0xFF3A4048, 0xFF1E2A30, 0xFF0E1418),
    "fog": (0xFF9AA4AC, 0xFFC8CED2, 0xFF5A6E78, 0xFF3A4C56),
}


def wave_band(c, t, y, amp, length, speed, color, W):
    p = skia.Path()
    p.moveTo(0, y)
    for x in range(0, W + 40, 40):
        p.lineTo(x, y + math.sin(x / length + t * speed) * amp + math.sin(x / (length * 0.37) - t * speed * 1.3) * amp * 0.3)
    p.lineTo(W, 1200)
    p.lineTo(0, 1200)
    p.close()
    c.drawPath(p, paint(color))


def ship(c, x, y, s=1.0, t=0.0, sails="full", yawl=True, rock=1.0, dark=False):
    """Two-masted brigantine, side view, bow to the right. (x, y) = waterline centre."""
    c.save()
    c.translate(x, y)
    c.rotate(math.sin(t * 0.9) * 2.5 * rock)
    c.translate(0, math.sin(t * 1.3) * 6 * rock)
    c.scale(s, s)
    hull_c = 0xFF2A1E16 if dark else 0xFF4A3424
    sail_c = 0xFFB9B2A2 if dark else 0xFFEDE6D3
    # masts
    for mx, h in ((150, 560), (-150, 520)):
        c.drawLine(mx, -60, mx, -60 - h, paint(OUTLINE, 16))
        c.drawLine(mx, -60, mx, -60 - h, paint(0xFF6A4A30, 9))
    # bowsprit
    c.drawLine(380, -80, 560, -150, paint(OUTLINE, 12))
    # rigging
    for a, b in (((150, -620), (560, -150)), ((150, -620), (-380, -70)), ((-150, -580), (-400, -70))):
        c.drawLine(a[0], a[1], b[0], b[1], paint(0x99222222, 3))
    # sails
    if sails != "none":
        rows = 3 if sails == "full" else 1
        for k in range(rows):  # square sails on the foremast
            top = -560 + k * 150
            sp = skia.Path()
            sp.moveTo(150 - 150 + k * 10, top)
            sp.lineTo(150 + 150 - k * 10, top)
            sp.quadTo(150 + 175, top + 70, 150 + 160, top + 130)
            sp.lineTo(150 - 160, top + 130)
            sp.quadTo(150 - 130, top + 70, 150 - 150 + k * 10, top)
            sp.close()
            c.drawPath(sp, paint(sail_c))
            c.drawPath(sp, paint(OUTLINE, 6))
        if sails == "full":  # fore-and-aft mainsail + jib
            m = skia.Path()
            m.moveTo(-140, -560)
            m.lineTo(-140, -110)
            m.lineTo(-420, -110)
            m.quadTo(-300, -330, -140, -560)
            m.close()
            c.drawPath(m, paint(sail_c))
            c.drawPath(m, paint(OUTLINE, 6))
        j = skia.Path()
        j.moveTo(170, -470)
        j.lineTo(520, -150)
        j.lineTo(200, -120)
        j.close()
        c.drawPath(j, paint(sail_c if sails == "full" else 0xFF8A8478))
        c.drawPath(j, paint(OUTLINE, 6))
    # hull
    h = skia.Path()
    h.moveTo(-460, -90)
    h.lineTo(420, -90)
    h.quadTo(470, -95, 500, -120)
    h.quadTo(470, 20, 330, 60)
    h.lineTo(-380, 60)
    h.quadTo(-450, 30, -460, -90)
    h.close()
    c.drawPath(h, paint(hull_c))
    c.drawPath(h, paint(OUTLINE, 9))
    c.drawLine(-450, -60, 440, -60, paint(0xFF1A1410, 8))
    c.drawLine(-440, -20, 430, -20, paint(0x33FFFFFF, 3))
    # rail
    c.drawLine(-460, -110, 430, -110, paint(OUTLINE, 8))
    for rx in range(-440, 430, 50):
        c.drawLine(rx, -110, rx, -90, paint(OUTLINE, 5))
    if yawl:  # lifeboat on the stern davits
        outlined_rect(c, -470, -170, -330, -130, 0xFF8A6A48, 20, 5)
        c.drawLine(-460, -170, -460, -110, paint(OUTLINE, 4))
        c.drawLine(-340, -170, -340, -110, paint(OUTLINE, 4))
    c.restore()


def bg_ocean(c, t, W, H, o):
    sky = o.get("sky", "day")
    top, hor, sea1, sea2 = SKIES[sky]
    vgrad(c, top, hor, skia.Rect.MakeLTRB(0, 0, W, 560))
    if sky == "dusk":
        glow(c, 1500, 540, 600, 0xFFFFB86B, 0.8)
    if sky == "night":
        rnd = random.Random(8)
        for _ in range(60):
            c.drawCircle(rnd.random() * W, rnd.random() * 480, 1.6, paint(0x99FFFFFF))
        c.drawCircle(1500, 160, 50, paint(0xFFE9E6D3))
    if sky == "storm":
        ph = (t * 0.33) % 1.0
        if ph < 0.03 or 0.07 < ph < 0.085:
            c.drawRect(skia.Rect.MakeWH(W, H), paint(0x66DDE6FF))
    vgrad(c, sea1, sea2, skia.Rect.MakeLTRB(0, 540, W, H))
    amp = 22 if sky == "storm" else 10
    wave_band(c, t, 560, amp * 0.5, 90, 0.6, sea1, W)
    if o.get("ship2"):
        sx, sy, ss = o["ship2"]
        ship(c, sx, sy, ss, t + 2, "full", True, 0.6)
    lt = o.get("_lt", 0)
    sx = o.get("ship_x", 960) + lt * o.get("ship_speed", 0)
    ship(c, sx, o.get("ship_y", 700), o.get("ship_s", 1.0), t, o.get("sails", "full"), o.get("yawl", True),
         1.8 if sky == "storm" else 1.0, dark=sky in ("night", "storm", "fog"))
    wave_band(c, t, 720, amp, 140, 1.0, sea2, W)
    wave_band(c, t * 1.1, 840, amp * 1.3, 180, 1.2, 0xFF0C1A26 if sky in ("night", "storm") else sea2, W)
    if o.get("fog") or sky == "fog":
        fp = skia.Paint(AntiAlias=True)
        fp.setShader(skia.GradientShader.MakeLinear([(0, 300), (0, 900)], [0x00C8CED2, 0xAAC8CED2, 0x55C8CED2],
                                                    [0, 0.6, 1]))
        c.drawRect(skia.Rect.MakeLTRB(0, 300, W, H), fp)
    return 2000, []


def bg_deck(c, t, W, H, o):
    sky = o.get("sky", "day")
    top, hor, sea1, sea2 = SKIES[sky]
    vgrad(c, top, hor, skia.Rect.MakeLTRB(0, 0, W, 520))
    c.save()  # horizon rocks with the ship
    c.rotate(math.sin(t * 0.9) * 1.5)
    vgrad(c, sea1, sea2, skia.Rect.MakeLTRB(-200, 500, W + 200, 760))
    c.restore()
    # bulwark / railing
    outlined_rect(c, -20, 600, W + 20, 760, 0xFF5A4030, 0, 8)
    c.drawRect(skia.Rect.MakeLTRB(0, 600, W, 620), paint(0xFF3A281C))
    for x in range(40, W, 160):
        c.drawLine(x, 620, x, 760, paint(0x55000000, 6))
    # masts
    for mx in (520, 1500):
        outlined_rect(c, mx - 26, -20, mx + 26, GROUND, 0xFF6A4A30, 6, 8)
    for k in range(6):  # ropes
        c.drawLine(520 + 26, 40 + k * 20, 900 + k * 60, 600, paint(0x77222222, 3))
    # deck planks
    vgrad(c, 0xFF7A5A3E, 0xFF4A3424, skia.Rect.MakeLTRB(0, 760, W, H))
    for y in (800, 850, 920, 1000):
        c.drawLine(0, y, W, y, paint(0x33000000, 3))
    if o.get("hatch"):  # open cargo hatch
        hx = o.get("hatch_x", 1100)
        outlined_rect(c, hx - 150, 820, hx + 150, 880, 0xFF5A4030, 6, 7)
        c.drawRect(skia.Rect.MakeLTRB(hx - 130, 828, hx + 130, 872), paint(0xFF0A0806))
        c.save()
        c.translate(hx + 150, 820)
        c.rotate(-60)
        outlined_rect(c, 0, -10, 280, 10, 0xFF6A4A30, 3, 6)
        c.restore()
    if o.get("wheel"):
        wx = o.get("wheel_x", 1700)
        outlined_rect(c, wx - 14, 640, wx + 14, GROUND, 0xFF4A3424, 4, 6)
        c.drawCircle(wx, 600, 90, paint(OUTLINE, 22))
        c.drawCircle(wx, 600, 90, paint(0xFF8A6A48, 12))
        for k in range(8):
            a = k * math.pi / 4 + math.sin(t) * 0.2
            c.drawLine(wx, 600, wx + math.cos(a) * 120, 600 + math.sin(a) * 120, paint(0xFF8A6A48, 10))
    if o.get("wet"):
        for k in range(12):
            x = (k * 151) % W
            c.drawOval(skia.Rect.MakeLTRB(x, 930 + (k % 3) * 40, x + 120, 950 + (k % 3) * 40), paint(0x334A90C0))
    return GROUND, []


def bg_ship_cabin(c, t, W, H, o):
    vgrad(c, 0xFF5A4030, 0xFF3A281C, skia.Rect.MakeWH(W, H))
    for x in range(0, W, 110):
        c.drawLine(x, 0, x, GROUND, paint(0x22000000, 5))
    # porthole
    c.drawCircle(1420, 340, 110, paint(OUTLINE))
    c.drawCircle(1420, 340, 100, paint(0xFF8A7A50))
    sea = skia.Paint(AntiAlias=True)
    sea.setShader(skia.GradientShader.MakeLinear([(0, 260), (0, 420)], [0xFF8DB8DE, 0xFF2E6A8E]))
    c.drawCircle(1420, 340, 78, sea)
    c.drawCircle(1420, 340, 78, paint(OUTLINE, 6))
    # bunk
    outlined_rect(c, 60, 560, 560, 640, 0xFF4A3424, 6, 7)
    outlined_rect(c, 80, 520, 540, 566, 0xFFD8D0BC, 14, 5)
    # table with logbook + chart
    outlined_rect(c, 820, 700, 1340, 734, 0xFF6A4A30, 6, 7)
    outlined_rect(c, 860, 734, 890, GROUND, 0xFF6A4A30, 4, 5)
    outlined_rect(c, 1270, 734, 1300, GROUND, 0xFF6A4A30, 4, 5)
    outlined_rect(c, 900, 684, 1080, 702, 0xFFE9DFC4, 3, 4)
    outlined_rect(c, 1120, 676, 1240, 702, 0xFF5A1E1E, 4, 5)  # logbook
    if o.get("toys"):
        c.drawCircle(400, 870, 26, paint(OUTLINE))
        c.drawCircle(400, 870, 20, paint(0xFFC0392B))
    vgrad(c, 0xFF4A3424, 0xFF241810, skia.Rect.MakeLTRB(0, GROUND, W, H))
    c.drawLine(0, GROUND, W, GROUND, paint(OUTLINE, 6))
    # swinging lamp
    sw = math.sin(t * 1.2) * 12
    lx = 1080 + sw * 6
    c.drawLine(1080, 0, lx, 300, paint(OUTLINE, 5))
    outlined_rect(c, lx - 34, 300, lx + 34, 380, 0xFFB98418, 10, 6)
    c.drawRect(skia.Rect.MakeLTRB(lx - 22, 312, lx + 22, 368), paint(0xFFFFE6A0 if o.get("lamp", True) else 0xFF3A3020))
    lights = [(lx, 340, 700, 0xFFFFD890, 0.8)] if o.get("lamp", True) else []
    return GROUND, lights


ATLANTIC = {"NEW YORK": (300, 360), "AZORES": (1040, 500), "GIBRALTAR": (1560, 600), "GENOA": (1760, 410),
            "FOUND HERE": (1330, 540)}


def bg_atlantic(c, t, W, H, o):
    c.clear(0xFF1A2A3A)
    land = paint(0xFF2B3528)
    am = skia.Path()  # North America
    am.moveTo(0, 0)
    am.lineTo(420, 0)
    am.cubicTo(380, 200, 330, 300, 300, 360)
    am.cubicTo(260, 460, 300, 600, 200, 760)
    am.cubicTo(160, 860, 260, 980, 220, H)
    am.lineTo(0, H)
    am.close()
    c.drawPath(am, land)
    eu = skia.Path()  # Europe + Africa
    eu.moveTo(W, 0)
    eu.lineTo(1500, 0)
    eu.cubicTo(1460, 200, 1520, 320, 1480, 430)
    eu.cubicTo(1460, 520, 1500, 580, 1540, 600)
    eu.cubicTo(1500, 660, 1440, 760, 1430, 900)
    eu.cubicTo(1420, 980, 1480, 1040, 1500, H)
    eu.lineTo(W, H)
    eu.close()
    c.drawPath(eu, land)
    c.drawCircle(1040, 500, 10, paint(0xFF2B3528))
    c.drawCircle(1010, 490, 7, paint(0xFF2B3528))
    for x in range(0, W, 120):
        c.drawLine(x, 0, x, H, paint(0x11FFFFFF, 1))
    for y in range(0, H, 120):
        c.drawLine(0, y, W, y, paint(0x11FFFFFF, 1))
    c.drawString("ATLANTIC OCEAN", 620, 760, font(48, "Black"), paint(0x33FFFFFF))
    f = font(30, "Black")
    for name in o.get("labels", ["NEW YORK", "AZORES", "GIBRALTAR", "GENOA"]):
        x, y = ATLANTIC[name]
        c.drawCircle(x, y, 11, paint(0xFFFFFFFF))
        c.drawString(name, x + 20, y + 10, f, paint(0xFFFFFFFF))
    k = min(1.0, o.get("_lt", t) / max(0.1, o.get("route_time", 4.0)))
    for leg in o.get("routes", []):
        a, b = ATLANTIC[leg[0]], ATLANTIC[leg[1]]
        prog = 1 if len(leg) > 2 and leg[2] == 1 else k
        x = a[0] + (b[0] - a[0]) * prog
        y = a[1] + (b[1] - a[1]) * prog
        d = paint(0xFFFF4040, 7)
        d.setPathEffect(skia.DashPathEffect.Make([22, 14], -t * 50))
        c.drawLine(a[0], a[1], x, y, d)
        c.drawCircle(x, y, 10, paint(0xFFFF4040))
    if o.get("found"):
        x, y = ATLANTIC["FOUND HERE"]
        pulse = 1 + 0.1 * math.sin(t * 4)
        c.drawCircle(x, y, 60 * pulse, paint(0xFFFFC020, 5))
        c.drawString("FOUND HERE", x - 90, y - 80, f, paint(0xFFFFC020))
    return GROUND, []


def bg_court(c, t, W, H, o):
    vgrad(c, 0xFF4A3424, 0xFF2A1C12, skia.Rect.MakeWH(W, H))
    for x in range(0, W, 240):
        outlined_rect(c, x + 20, 80, x + 220, 520, 0xFF5A4030, 6, 6)
    outlined_rect(c, 660, 30, 1260, 120, 0xFF3A6A3A, 10, 8)  # crest panel
    c.drawString("VICE-ADMIRALTY COURT", 700, 92, font(40, "Black"), paint(0xFFE0C060))
    vgrad(c, 0xFF3A281C, 0xFF140E08, skia.Rect.MakeLTRB(0, GROUND, W, H))
    c.drawLine(0, GROUND, W, GROUND, paint(OUTLINE, 6))
    return GROUND, [(960, 120, 900, 0xFFFFE6B0, 0.35)]


def court_front(c):
    outlined_rect(c, 560, 560, 1360, GROUND, 0xFF3A281C, 6, 9)  # bench, in front of the judge
    outlined_rect(c, 540, 540, 1380, 580, 0xFF5A4030, 6, 8)
    for x in (700, 960, 1220):
        outlined_rect(c, x - 70, 620, x + 70, 840, 0xFF4A3424, 6, 5)


def bg_log(c, t, W, H, o):
    c.clear(0xFF1A140E)
    glow(c, W / 2, H / 2, 900, 0xFFFFD890, 0.4)
    c.save()
    c.translate(W / 2, H / 2)
    c.rotate(-2 + math.sin(t * 0.7) * 0.5)
    outlined_rect(c, -560, -320, 560, 320, 0xFFE6D7AE, 4, 7)
    c.drawLine(0, -320, 0, 320, paint(0x55000000, 5))
    for y in range(-260, 320, 46):
        c.drawLine(-530, y, -20, y, paint(0x332E4A6B, 2))
        c.drawLine(20, y, 530, y, paint(0x332E4A6B, 2))
    lines = o.get("lines", [])
    size = 56
    while lines and max(font(size, "Bold").measureText(l) for l in lines) > 480 and size > 24:
        size -= 2
    f = font(size, "Bold")
    shown = int(o.get("_lt", t) * 16)
    n = 0
    for i, line in enumerate(lines):
        part = line[: max(0, shown - n)]
        n += len(line)
        c.drawString(part, -520 if i < 5 else 40, -200 + (i % 5) * 92, f, paint(0xFF2A1E12))
    c.restore()
    return GROUND, []


def bg_barrels(c, t, W, H, o):
    c.clear(0xFF14100C)
    glow(c, W / 2, 300, 900, 0xFFFFD890, 0.4)
    vgrad(c, 0xFF2A1E14, 0xFF120C08, skia.Rect.MakeLTRB(0, GROUND, W, H))
    empty = o.get("empty", 0)
    for row in range(2):
        for k in range(7):
            x = 200 + k * 230 + row * 115
            y = 520 + row * 200
            idx = row * 7 + k
            colr = 0xFF6A3A22 if idx >= empty else 0xFF3A2A1E
            outlined_rect(c, x, y - 180, x + 170, y + 20, colr, 40, 8)
            for yy in (y - 140, y - 20):
                c.drawLine(x + 6, yy, x + 164, yy, paint(0xFF2A2A2A, 10))
            if idx < empty:
                c.drawString("EMPTY", x + 18, y - 70, font(36, "Black"), paint(0xFFFFC020))
    return GROUND, []


BACKGROUNDS.update({"ocean": bg_ocean, "deck": bg_deck, "ship_cabin": bg_ship_cabin, "atlantic": bg_atlantic,
                    "court": bg_court, "log": bg_log, "barrels": bg_barrels})
