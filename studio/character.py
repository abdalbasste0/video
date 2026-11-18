"""Parametric 2D character ("Sam") drawn with Skia.

Original design ("the Streamer"): round head with messy hair, big over-ear
gaming headset with a mic boom, dark hoodie with neon cyan/magenta accents. Poses are joint-angle dicts; actions are functions of time
that return a pose, so every motion is procedural and smooth.
"""
import math
import skia

# ---- palette -------------------------------------------------------------
SKIN = 0xFFF1E4CF
SKIN_SHADE = 0xFFD9C7AA
OUTLINE = 0xFF141414
HAIR = 0xFF2A211C
HOODIE = 0xFF363A4C
HOODIE_FAR = 0xFF262936
NEON = 0xFF2EE6FF
NEON2 = 0xFFFF3DAE
HEADSET = 0xFF15161C
PANTS = 0xFF1B1E28
PANTS_FAR = 0xFF14161E
SHOE = 0xFF111111

# ---- skeleton lengths (px at scale 1) -------------------------------------
TORSO = 150
UPPER_ARM = 82
FOREARM = 78
THIGH = 96
SHIN = 96
HEAD_RX, HEAD_RY = 80, 88
NECK = 92  # neck point -> head centre

LOOKS = {
    "streamer": {},
    "leo": dict(HOODIE=0xFF8E2B2B, HOODIE_FAR=0xFF6A1E1E, NEON=0xFFFFC23D, NEON2=0xFFFFFFFF,
                HAIR=0xFF6B4226, PANTS=0xFF2A3550, PANTS_FAR=0xFF1E2740),
    "officer": dict(HOODIE=0xFF1F3A66, HOODIE_FAR=0xFF162B4D, NEON=0xFF1F3A66, NEON2=0xFFE0C060,
                    HAIR=0xFF111111, PANTS=0xFF1A2236, PANTS_FAR=0xFF121827, HEADSET=None),
    "shadow": dict(SKIN=0xFF0A0A0E, SKIN_SHADE=0xFF050507, HAIR=0xFF050507, HOODIE=0xFF0A0A0E,
                   HOODIE_FAR=0xFF050507, NEON=0xFF0A0A0E, NEON2=0xFF0A0A0E, PANTS=0xFF08080B,
                   PANTS_FAR=0xFF050507, HEADSET=None, EYES=0xFFFFFFFF),
}
_DEFAULTS = None


def set_look(name):
    """Swap the module palette (each render worker draws one character at a time)."""
    global _DEFAULTS
    g = globals()
    if _DEFAULTS is None:
        _DEFAULTS = {k: g[k] for k in ("SKIN", "SKIN_SHADE", "HAIR", "HOODIE", "HOODIE_FAR", "NEON",
                                       "NEON2", "HEADSET", "PANTS", "PANTS_FAR", "EYES")}
    g.update(_DEFAULTS)
    g.update(LOOKS.get(name, {}))


EYES = None
BASE = dict(torso=0, head=0, shL=8, elL=-12, shR=-6, elR=-10,
            hipL=4, knL=0, hipR=-4, knR=0, x=0, y=0, rot=0)


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def blend(p, q, t):
    return {k: lerp(p.get(k, BASE[k]), q.get(k, BASE[k]), t) for k in BASE}


def pose(**kw):
    d = dict(BASE)
    d.update(kw)
    return d


# ---- expressions ----------------------------------------------------------
# brow: (inner_y, outer_y) offsets (negative = up). lid: 0 open .. 1 closed
# mouth: (curve, open, width) curve>0 smile, <0 frown
EXPR = {
    "neutral":    dict(brow=(0, 0), lid=0.0, mouth=(0.0, 0.0, 30), pupil=8),
    "determined": dict(brow=(14, -8), lid=0.25, mouth=(-0.15, 0.0, 26), pupil=8),
    "angry":      dict(brow=(20, -10), lid=0.15, mouth=(-0.5, 0.25, 30), pupil=7),
    "sad":        dict(brow=(-14, 6), lid=0.2, mouth=(-0.6, 0.0, 26), pupil=8),
    "tired":      dict(brow=(-4, 4), lid=0.55, mouth=(-0.2, 0.0, 22), pupil=7),
    "happy":      dict(brow=(-6, -6), lid=0.0, mouth=(0.8, 0.15, 34), pupil=8),
    "proud":      dict(brow=(-2, -6), lid=0.2, mouth=(0.6, 0.0, 30), pupil=8),
    "shocked":    dict(brow=(-16, -12), lid=0.0, mouth=(0.0, 0.7, 18), pupil=5),
    "anxious":    dict(brow=(-12, 4), lid=0.0, mouth=(-0.3, 0.1, 24), pupil=5),
    "scared":     dict(brow=(-18, -6), lid=0.0, mouth=(-0.4, 0.45, 22), pupil=4),
    "suspicious": dict(brow=(10, -4), lid=0.4, mouth=(-0.2, 0.0, 20), pupil=7),
    "empty":      dict(brow=(0, 2), lid=0.45, mouth=(-0.05, 0.0, 18), pupil=6),
}


def paint(color, stroke=0, cap=True, alpha=None):
    p = skia.Paint(AntiAlias=True, Color=color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap if cap else skia.Paint.kButt_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if alpha is not None:
        p.setAlphaf(alpha)
    return p


def _dir(angle_deg):
    a = math.radians(angle_deg)
    return math.sin(a), math.cos(a)


def limb(c, a, b, color, width):
    # outline then fill gives a cartoon ink line around limbs
    c.drawLine(a[0], a[1], b[0], b[1], paint(OUTLINE, width + 10))
    c.drawLine(a[0], a[1], b[0], b[1], paint(color, width))


def joint_chain(c, start, a1, l1, a2, l2, color, width, end_color=None, end_r=0):
    d1 = _dir(a1)
    mid = (start[0] + d1[0] * l1, start[1] + d1[1] * l1)
    d2 = _dir(a2)
    end = (mid[0] + d2[0] * l2, mid[1] + d2[1] * l2)
    path = skia.Path()
    path.moveTo(*start)
    path.lineTo(*mid)
    path.lineTo(*end)
    c.drawPath(path, paint(OUTLINE, width + 10))
    c.drawPath(path, paint(color, width))
    if end_r:
        c.drawCircle(end[0], end[1], end_r + 5, paint(OUTLINE))
        c.drawCircle(end[0], end[1], end_r, paint(end_color))
    return mid, end


def _headset(c):
    """Gaming headset: band over the head, big ear cup, mic boom to the mouth."""
    band = skia.Path()
    band.moveTo(-HEAD_RX + 4, 4)
    band.cubicTo(-HEAD_RX - 6, -120, 52, -132, 74, -30)
    c.drawPath(band, paint(OUTLINE, 22))
    c.drawPath(band, paint(HEADSET, 12))
    c.drawPath(band, paint(NEON, 3))
    mic = skia.Path()
    mic.moveTo(-HEAD_RX + 10, 30)
    mic.cubicTo(-50, 86, 0, 82, 22, 62)
    c.drawPath(mic, paint(OUTLINE, 11))
    c.drawPath(mic, paint(HEADSET, 6))
    c.drawCircle(24, 61, 11, paint(OUTLINE))
    c.drawCircle(24, 61, 7, paint(0xFF3A3D48))
    cup = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-HEAD_RX - 22, -30, -HEAD_RX + 32, 46), 22, 22)
    c.drawRRect(cup, paint(OUTLINE))
    c.drawRRect(cup, paint(HEADSET))
    inner = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-HEAD_RX - 10, -18, -HEAD_RX + 20, 34), 14, 14)
    c.drawRRect(inner, paint(NEON, 4))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(HEAD_RX - 14, -24, HEAD_RX + 6, 30), 10, 10),
                paint(OUTLINE))


def draw_head(c, cx, cy, tilt, expr, t, look=(0, 0), blink_seed=0.0, talk=0.0):
    e = EXPR.get(expr, EXPR["neutral"])
    c.save()
    c.translate(cx, cy)
    c.rotate(tilt)
    # head
    oval = skia.Rect.MakeLTRB(-HEAD_RX, -HEAD_RY, HEAD_RX, HEAD_RY)
    c.drawOval(oval.makeOutset(5, 5), paint(OUTLINE))
    c.drawOval(oval, paint(SKIN))
    # soft shade on the back-lower side
    shade = skia.Paint(AntiAlias=True)
    shade.setShader(skia.GradientShader.MakeRadial(
        (-20, -30), 130, [0x00000000, 0x33000000]))
    c.drawOval(oval, shade)
    # hair tuft (signature)
    hp = skia.Path()
    hp.moveTo(-70, -40)
    hp.cubicTo(-80, -100, -20, -112, 10, -100)
    hp.lineTo(4, -122)
    hp.lineTo(30, -98)
    hp.lineTo(40, -116)
    hp.lineTo(52, -88)
    hp.cubicTo(70, -78, 78, -60, 76, -42)
    hp.cubicTo(50, -70, 0, -76, -70, -40)
    hp.close()
    c.drawPath(hp, paint(OUTLINE, 10))
    c.drawPath(hp, paint(HAIR))
    if HEADSET is None:
        c.drawCircle(-HEAD_RX + 6, 10, 15, paint(OUTLINE))
        c.drawCircle(-HEAD_RX + 6, 10, 10, paint(SKIN_SHADE))
    else:
        _headset(c)

    # blinking
    bt = (t + blink_seed) % 3.7
    blink = 1.0 if bt < 0.12 else 0.0
    lid = max(e["lid"], blink)
    fx = 16  # face shift toward facing direction (3/4 view)
    for side, ex in ((-1, -28 + fx), (1, 32 + fx)):
        ey = -2
        rx, ry = 17, 21
        c.drawOval(skia.Rect.MakeLTRB(ex - rx - 4, ey - ry - 4, ex + rx + 4, ey + ry + 4), paint(OUTLINE))
        if EYES is not None:  # silhouette: two glowing slits, nothing else
            c.drawOval(skia.Rect.MakeLTRB(ex - 12, ey - 5, ex + 12, ey + 5), paint(EYES))
            continue
        c.drawOval(skia.Rect.MakeLTRB(ex - rx, ey - ry, ex + rx, ey + ry), paint(0xFFFFFFFF))
        pr = e["pupil"]
        c.drawCircle(ex + 4 + look[0] * 7, ey + 2 + look[1] * 7, pr + 1, paint(OUTLINE))
        c.drawCircle(ex + 6 + look[0] * 7, ey - 1 + look[1] * 7, 2.5, paint(0xFFFFFFFF))
        if lid > 0.01:
            c.save()
            c.clipRect(skia.Rect.MakeLTRB(ex - rx - 6, ey - ry - 6, ex + rx + 6, ey - ry + 2 * ry * lid))
            c.drawOval(skia.Rect.MakeLTRB(ex - rx - 1, ey - ry - 1, ex + rx + 1, ey + ry + 1), paint(SKIN))
            c.restore()
            ly = ey - ry + 2 * ry * lid
            c.drawLine(ex - rx, ly, ex + rx, ly, paint(OUTLINE, 5))
        # brows: inner end is toward the nose (between eyes)
        inner, outer = e["brow"]
        bx_in = ex - side * 2 if side < 0 else ex - 14
        if side < 0:
            p0 = (ex - 18, ey - 34 + outer)
            p1 = (ex + 14, ey - 34 + inner)
        else:
            p0 = (ex - 14, ey - 34 + inner)
            p1 = (ex + 18, ey - 34 + outer)
        c.drawLine(p0[0], p0[1], p1[0], p1[1], paint(OUTLINE, 9))
    if EYES is not None:
        c.restore()
        return
    # mouth
    curve, mopen, w = e["mouth"]
    mopen = max(mopen, talk)
    mx, my = fx + 6, 48
    if mopen > 0.05:
        r = skia.Rect.MakeLTRB(mx - w * 0.55, my - 6 - curve * 6, mx + w * 0.55, my + 6 + mopen * 26)
        c.drawOval(r, paint(OUTLINE))
        inner = r.makeInset(5, 5)
        c.drawOval(inner, paint(0xFF6B1F1F))
    else:
        mp = skia.Path()
        mp.moveTo(mx - w / 2, my)
        mp.quadTo(mx, my + curve * 26, mx + w / 2, my)
        c.drawPath(mp, paint(OUTLINE, 7))
    c.restore()


def draw(c, p, X, Y, scale=1.0, facing=1, expr="neutral", t=0.0, look=(0, 0),
         blink_seed=0.0, prop_hand=None, talk=0.0, hide_legs=False):
    """Draw character with hips at world (X,Y). prop_hand(c, hand_xy, angle) optional."""
    c.save()
    c.translate(X + p["x"], Y + p["y"])
    c.scale(scale * facing, scale)
    c.rotate(p["rot"])
    hip = (0, 0)
    tdx, tdy = _dir(p["torso"])
    neck = (tdx * TORSO, -tdy * TORSO)
    sh = (neck[0] - tdx * 22, neck[1] + tdy * 22)
    head_c = (neck[0] + _dir(p["torso"] + p["head"] * 0.5)[0] * NECK * 0.9,
              neck[1] - NECK)

    # far limbs
    if not hide_legs:
        joint_chain(c, hip, p["hipR"], THIGH, p["hipR"] - p["knR"], SHIN, PANTS_FAR, 34,
                    SHOE, 0)
        _foot(c, hip, p["hipR"], p["hipR"] - p["knR"], PANTS_FAR)
    joint_chain(c, sh, p["torso"] + p["shR"], UPPER_ARM, p["torso"] + p["shR"] + p["elR"],
                FOREARM, HOODIE_FAR, 30, SKIN_SHADE, 15)
    # torso (hoodie)
    body = skia.Path()
    body.moveTo(hip[0] - 34, hip[1] + 10)
    body.lineTo(sh[0] - 40, sh[1] - 6)
    body.quadTo(neck[0], neck[1] - 18, sh[0] + 40, sh[1] - 6)
    body.lineTo(hip[0] + 34, hip[1] + 10)
    body.quadTo(hip[0], hip[1] + 22, hip[0] - 34, hip[1] + 10)
    body.close()
    c.drawPath(body, paint(OUTLINE, 12))
    c.drawPath(body, paint(HOODIE))
    sh_p = skia.Paint(AntiAlias=True)
    sh_p.setShader(skia.GradientShader.MakeLinear([(-40, 0), (40, 0)], [0x55000000, 0x00000000]))
    c.drawPath(body, sh_p)
    # neon chest stripe + drawstrings
    c.drawLine(hip[0] - 26 + tdx * 70, hip[1] - tdy * 70, hip[0] + 28 + tdx * 70, hip[1] - tdy * 70,
               paint(NEON2, 7))
    for dx in (-10, 12):
        c.drawLine(neck[0] + dx, neck[1] + 20, neck[0] + dx - tdx * 40, neck[1] + 20 + tdy * 40,
                   paint(NEON, 4))
    if not hide_legs:
        joint_chain(c, hip, p["hipL"], THIGH, p["hipL"] - p["knL"], SHIN, PANTS, 36, SHOE, 0)
        _foot(c, hip, p["hipL"], p["hipL"] - p["knL"], PANTS)
    # hood collar
    c.drawCircle(neck[0], neck[1] + 4, 30, paint(OUTLINE))
    c.drawCircle(neck[0], neck[1] + 4, 24, paint(HOODIE_FAR))
    draw_head(c, head_c[0], head_c[1], p["head"], expr, t, look, blink_seed, talk)
    # near arm last
    _, hand = joint_chain(c, sh, p["torso"] + p["shL"], UPPER_ARM,
                          p["torso"] + p["shL"] + p["elL"], FOREARM, HOODIE, 32, SKIN, 16)
    if prop_hand:
        prop_hand(c, hand, p["torso"] + p["shL"] + p["elL"])
    c.restore()


def _foot(c, hip, a1, a2, color):
    d1 = _dir(a1)
    knee = (hip[0] + d1[0] * THIGH, hip[1] + d1[1] * THIGH)
    d2 = _dir(a2)
    ank = (knee[0] + d2[0] * SHIN, knee[1] + d2[1] * SHIN)
    r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(ank[0] - 16, ank[1] - 12, ank[0] + 34, ank[1] + 12), 12, 12)
    c.drawRRect(r, paint(OUTLINE))
    c.drawRRect(r.makeOffset(0, 0), paint(SHOE))


# ---- actions: time -> pose --------------------------------------------------
def act_stand(t, **_):
    b = math.sin(t * 1.6)
    return pose(torso=b * 1.2, head=math.sin(t * 0.7) * 2, shL=6 + b, shR=-6 - b, y=b * 1.5)


def act_head_down(t, **_):
    b = math.sin(t * 1.2)
    return pose(torso=6, head=18 + b, shL=2, elL=-4, shR=-2, elR=-4, y=b)


def act_walk(t, speed=1.0, **_):
    ph = t * 6.0 * speed
    s = math.sin(ph)
    return pose(torso=4, head=math.sin(ph * 2) * 1.5,
                hipL=26 * s, knL=max(0, -s) * 45 + 6, hipR=-26 * s, knR=max(0, s) * 45 + 6,
                shL=-24 * s, elL=-18, shR=24 * s, elR=-18, y=-abs(math.cos(ph)) * 6)


def act_trudge(t, **_):
    p = act_walk(t, speed=0.6)
    p.update(torso=14, head=16)
    p["shL"] *= 0.4
    p["shR"] *= 0.4
    return p


def act_run(t, **_):
    ph = t * 11.0
    s = math.sin(ph)
    return pose(torso=16, head=-6, hipL=45 * s, knL=max(0, -s) * 80 + 20,
                hipR=-45 * s, knR=max(0, s) * 80 + 20,
                shL=-55 * s, elL=-80, shR=55 * s, elR=-80, y=-abs(math.cos(ph)) * 14)


def act_sit_desk(t, **_):
    ty = math.sin(t * 14) * 3
    return pose(torso=10, head=8, hipL=88, knL=92, hipR=84, knR=88,
                shL=50 + ty, elL=-48, shR=46 - ty, elR=-44, y=0)


def act_sit_desk_slump(t, **_):
    return pose(torso=24, head=26, hipL=88, knL=92, hipR=84, knR=88,
                shL=20, elL=-90, shR=18, elR=-90, y=0)


def act_sit_edge(t, **_):  # elbows on knees, head in hands
    b = math.sin(t * 1.4) * 1.5
    return pose(torso=34 + b, head=22, hipL=86, knL=88, hipR=82, knR=84,
                shL=34, elL=-150, shR=30, elR=-146)


def act_lie(t, **_):  # lying on back (rot -90 -> head to the left when facing 1)
    b = math.sin(t * 1.1) * 1.2
    return pose(rot=-90 + b * 0.3, torso=0, head=-6, hipL=2, hipR=-2, shL=70, elL=-55,
                shR=10, elR=-20)


def act_kneel(t, **_):
    b = math.sin(t * 1.3)
    return pose(torso=32 + b, head=28, hipL=0, knL=95, hipR=-6, knR=95, shL=20, elL=-30,
                shR=10, elR=-20, y=SHIN - 10)


def act_pushup(t, **_):
    s = (math.sin(t * 4.0) + 1) / 2  # 0 down .. 1 up
    rot = lerp(72, 62, s)
    return pose(rot=rot, torso=0, head=-10, hipL=0, hipR=0, knL=0, knR=0,
                shL=rot - 4, elL=lerp(-80, -4, s), shR=rot - 8, elR=lerp(-80, -4, s),
                y=lerp(133, 102, s))


def act_triumph(t, **_):
    b = math.sin(t * 3) * 3
    return pose(torso=-4, head=-14, shL=160 + b, elL=-10, shR=-160 - b, elR=10,
                hipL=8, hipR=-8, y=-math.sin(t * 3) * 2)


def act_reach(t, **_):  # reaching toward something ahead
    b = math.sin(t * 1.5) * 4
    return pose(torso=10, head=-6, shL=100 + b, elL=-6, shR=60, elR=-20, hipL=10, hipR=-14)


def act_phone(t, **_):  # standing looking at phone in hand
    b = math.sin(t * 1.3)
    return pose(torso=10, head=24, shL=30, elL=-110 + b * 2, shR=-4, elR=-6, y=b)


def act_climb(t, **_):
    p = act_walk(t, speed=0.8)
    p.update(torso=18, head=-4)
    p["hipL"] += 14
    p["hipR"] += 14
    return p


ACTIONS = {k[4:]: v for k, v in globals().items() if k.startswith("act_")}
