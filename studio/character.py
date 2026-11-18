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

STICK = False
BAND = 0xFFD8352A  # red wristband: the hero's small signature

# round-head stickman family (default hero). Bigger bald head, painted shading.
_STICK = dict(STICK=True, HEAD_RX=94, HEAD_RY=98, HEADSET=None, SKIN=0xFFEFE9DC, SKIN_SHADE=0xFFCFC6B4,
              HOODIE=0xFF2E3036, HOODIE_FAR=0xFF212227, NEON=0xFF2E3036, NEON2=0xFF2E3036,
              PANTS=0xFF1C1D22, PANTS_FAR=0xFF141518)
COAT = False
HAT = None
HAIRSTYLE = None   # None | "slick" | "bun" | "kid"
GLASSES = False
NOTEBOOK = False
BEARD = None
GLOVE = 0xFF151515
HATSTYLE = "fedora"  # "fedora" | "pilot"
COAT_LEN = "long"  # "long" trench coat | "short" suit jacket | "dress"
SHIRT = 0xFFF1EBDD
TIE = 0xFF5A3A26
_DETECTIVE = dict(_STICK, COAT=True, HAT=0xFF6B5444, SKIN=0xFFFAFAF8, SKIN_SHADE=0xFF1A1A1A,
                  HOODIE=0xFFD8BF94, HOODIE_FAR=0xFFB89E74, PANTS=0xFF56565C, PANTS_FAR=0xFF46464B,
                  BAND=None, HEAD_RX=88, HEAD_RY=92, THIGH=118, SHIN=118, NOTEBOOK=True)
LOOKS = {
    "captain": dict(_DETECTIVE, HAT=0xFF1A2236, HATSTYLE="pilot", HOODIE=0xFF1E2A44, HOODIE_FAR=0xFF162036,
                    PANTS=0xFF2A2E38, PANTS_FAR=0xFF22252E, COAT_LEN="long", TIE=0xFF0E0E10, BEARD=0xFF4A3426,
                    HAIRSTYLE=None, NOTEBOOK=False),
    "sailor": dict(_DETECTIVE, GLOVE=0xFFFAFAF8, HAT=0xFF8A2A2A, HATSTYLE="beanie", HOODIE=0xFFE8E4DA, HOODIE_FAR=0xFFC9C3B6,
                   PANTS=0xFF2E3A52, PANTS_FAR=0xFF252F44, COAT_LEN="short", TIE=0xFF2E3A52, SHIRT=0xFF2E3A52,
                   NOTEBOOK=False),
    "sailor2": dict(_DETECTIVE, GLOVE=0xFFFAFAF8, HAT=0xFF2E4A3A, HATSTYLE="beanie", HOODIE=0xFF6E5A44, HOODIE_FAR=0xFF5A4836,
                    PANTS=0xFF3A3A40, PANTS_FAR=0xFF2E2E34, COAT_LEN="short", BEARD=0xFF2A211C, NOTEBOOK=False),
    "wife": dict(_DETECTIVE, GLOVE=0xFFFAFAF8, HAT=None, HAIRSTYLE="bun", HAIR=0xFF3A2A1E, HOODIE=0xFF6A2E3A, HOODIE_FAR=0xFF52222C,
                 PANTS=0xFF6A2E3A, PANTS_FAR=0xFF52222C, COAT_LEN="dress", TIE=0xFFE8E0D0, SHIRT=0xFFE8E0D0,
                 THIGH=104, SHIN=104, NOTEBOOK=False),
    "child": dict(_DETECTIVE, GLOVE=0xFFFAFAF8, HAT=None, HAIRSTYLE="kid", HAIR=0xFF8A5A30, HOODIE=0xFFE8D7A0, HOODIE_FAR=0xFFCDBB86,
                  PANTS=0xFFE8D7A0, PANTS_FAR=0xFFCDBB86, COAT_LEN="dress", TIE=0xFFE8D7A0, SHIRT=0xFFE8D7A0,
                  THIGH=60, SHIN=60, NOTEBOOK=False),
    "judge": dict(_DETECTIVE, HAT=None, HAIRSTYLE="slick", HAIR=0xFFDADADA, HOODIE=0xFF1A1A1E, HOODIE_FAR=0xFF111114,
                  PANTS=0xFF1A1A1E, PANTS_FAR=0xFF111114, COAT_LEN="long", TIE=0xFFF4F4F4,
                  NOTEBOOK=False),
    "writer": dict(_DETECTIVE, HAT=None, HAIRSTYLE="slick", HAIR=0xFF5A3A22, HOODIE=0xFF4A4038, HOODIE_FAR=0xFF3A322C,
                   PANTS=0xFF3A3A40, PANTS_FAR=0xFF2E2E34, COAT_LEN="short", NOTEBOOK=False),
    "detective": dict(_DETECTIVE),
    "cooper": dict(_DETECTIVE, HAT=None, HAIRSTYLE="slick", HAIR=0xFF241C17, GLASSES=True,
                   HOODIE=0xFF33343A, HOODIE_FAR=0xFF26272C, PANTS=0xFF2B2C31, PANTS_FAR=0xFF222327,
                   COAT_LEN="short", TIE=0xFF0E0E10),
    "attendant": dict(_DETECTIVE, GLOVE=0xFFFAFAF8, HAT=None, HAIRSTYLE="bun", HAIR=0xFF6B4A2E, HOODIE=0xFF3A6EA5,
                      HOODIE_FAR=0xFF2C5684, PANTS=0xFF2A3A55, PANTS_FAR=0xFF22304A, COAT_LEN="dress",
                      TIE=0xFFE0B040, THIGH=104, SHIN=104),
    "pilot": dict(_DETECTIVE, HAT=0xFF1C2438, HATSTYLE="pilot", HOODIE=0xFF1E2A44, HOODIE_FAR=0xFF162036,
                  PANTS=0xFF1A2336, PANTS_FAR=0xFF141B2A, COAT_LEN="short", TIE=0xFF0E0E10),
    "agent": dict(_DETECTIVE, HAT=0xFF5A5E66, HOODIE=0xFF4A4E58, HOODIE_FAR=0xFF3A3E46,
                  PANTS=0xFF3A3E46, PANTS_FAR=0xFF30333A, COAT_LEN="short", TIE=0xFF1E2A44),
    "boy": dict(_DETECTIVE, GLOVE=0xFFFAFAF8, HAT=None, HAIRSTYLE="kid", HAIR=0xFF8A5A30, HOODIE=0xFFC0392B,
                HOODIE_FAR=0xFF962D22, PANTS=0xFF3B5A86, PANTS_FAR=0xFF2F4A70, COAT_LEN="short",
                TIE=0xFFC0392B, SHIRT=0xFFC0392B, THIGH=80, SHIN=80),
    "detective_leo": dict(_DETECTIVE, HAT=None, HOODIE=0xFF7A2A26, HOODIE_FAR=0xFF5A1D1A),
    "detective_officer": dict(_DETECTIVE, HAT=0xFF1E2A44, HOODIE=0xFF2A3C62, HOODIE_FAR=0xFF1E2C4A),
    "detective_shadow": dict(_DETECTIVE, HAT=0xFF060608, SKIN=0xFF0A0A0E, HOODIE=0xFF0A0A0E,
                             HOODIE_FAR=0xFF060608, PANTS=0xFF08080B, PANTS_FAR=0xFF050507, EYES=0xFFFFFFFF),
    "stick": dict(_STICK),
    "stick_leo": dict(_STICK, SKIN=0xFFFAFAF8, HOODIE=0xFF7A2A26, HOODIE_FAR=0xFF5A1D1A, NEON=0xFF7A2A26, NEON2=0xFF7A2A26,
                      BAND=None),
    "stick_officer": dict(_STICK, HOODIE=0xFF22385E, HOODIE_FAR=0xFF182945, NEON=0xFF22385E,
                          NEON2=0xFFD9B44A, BAND=None),
    "stick_shadow": dict(_STICK, SKIN=0xFF0A0A0E, SKIN_SHADE=0xFF050507, HOODIE=0xFF0A0A0E,
                         HOODIE_FAR=0xFF050507, NEON=0xFF0A0A0E, NEON2=0xFF0A0A0E, PANTS=0xFF08080B,
                         PANTS_FAR=0xFF050507, EYES=0xFFFFFFFF, BAND=None),
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
                                       "NEON2", "HEADSET", "PANTS", "PANTS_FAR", "EYES",
                                       "STICK", "HEAD_RX", "HEAD_RY", "BAND", "COAT", "HAT", "THIGH", "SHIN", "HAIRSTYLE",
                                       "GLASSES", "HATSTYLE", "COAT_LEN", "SHIRT", "TIE", "NOTEBOOK", "BEARD", "GLOVE")}
    g.update(_DEFAULTS)
    g.update(LOOKS.get(name, {}))
    if not g["STICK"]:
        g["BAND"] = None


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
    "happy":      dict(brow=(-6, -6), lid=0.0, mouth=(0.8, 0.0, 34), pupil=8),
    "proud":      dict(brow=(-2, -6), lid=0.2, mouth=(0.6, 0.0, 30), pupil=8),
    "shocked":    dict(brow=(-16, -12), lid=0.0, mouth=(0.0, 0.7, 18), pupil=5),
    "anxious":    dict(brow=(-12, 4), lid=0.0, mouth=(-0.3, 0.1, 24), pupil=5),
    "scared":     dict(brow=(-18, -6), lid=0.0, mouth=(-0.4, 0.45, 22), pupil=4),
    "suspicious": dict(brow=(10, -4), lid=0.4, mouth=(-0.2, 0.0, 20), pupil=7),
    "terrified":  dict(brow=(-20, -2), lid=0.0, mouth=(-0.5, 0.75, 30), pupil=3),
    "surprised":  dict(brow=(-18, -14), lid=0.0, mouth=(0.0, 0.55, 16), pupil=5),
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


def _stick_head_shading(c, oval):
    """Soft painted look: key light from the upper left, core shadow lower right, rim light."""
    hi = skia.Paint(AntiAlias=True)
    hi.setShader(skia.GradientShader.MakeRadial((-34, -44), HEAD_RX * 1.1, [0x40FFFFFF, 0x00FFFFFF]))
    c.drawOval(oval, hi)
    sh = skia.Paint(AntiAlias=True)
    sh.setShader(skia.GradientShader.MakeRadial((-30, -40), HEAD_RX * 1.55,
                                                [0x00000000, 0x00000000, 0x55000000], [0, 0.55, 1]))
    c.drawOval(oval, sh)
    rim = skia.Paint(AntiAlias=True)
    rim.setStyle(skia.Paint.kStroke_Style)
    rim.setStrokeWidth(5)
    rim.setColor(0x55FFFFFF)
    c.drawArc(oval.makeInset(6, 6), 200, 60, False, rim)


def _hair(c):
    rx, ry = HEAD_RX, HEAD_RY
    if HAIRSTYLE == "bun":
        c.drawCircle(-rx * 0.62, -ry * 0.78, 34, paint(OUTLINE))
        c.drawCircle(-rx * 0.62, -ry * 0.78, 28, paint(HAIR))
    hp = skia.Path()
    hp.moveTo(-rx * 1.02, ry * 0.15)
    hp.cubicTo(-rx * 1.15, -ry * 1.05, rx * 0.55, -ry * 1.25, rx * 0.98, -ry * 0.35)
    if HAIRSTYLE == "kid":
        hp.lineTo(rx * 0.7, -ry * 0.5)
        hp.lineTo(rx * 0.62, -ry * 0.3)
        hp.lineTo(rx * 0.35, -ry * 0.55)
        hp.lineTo(rx * 0.1, -ry * 0.4)
    else:  # side part
        hp.cubicTo(rx * 0.5, -ry * 0.62, rx * 0.05, -ry * 0.6, -rx * 0.2, -ry * 0.72)
    hp.cubicTo(-rx * 0.6, -ry * 0.5, -rx * 0.8, -ry * 0.2, -rx * 0.75, ry * 0.15)
    hp.close()
    c.drawPath(hp, paint(OUTLINE, 9))
    c.drawPath(hp, paint(HAIR))
    c.drawLine(-rx * 0.3, -ry * 0.88, rx * 0.4, -ry * 0.8, paint(0x33FFFFFF, 4))


def _glasses(c):
    for ex in (-16, 44):
        r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(ex - 27, -20, ex + 27, 20), 12, 12)
        c.drawRRect(r, paint(0xFF0B0B0D))
        c.drawRRect(r, paint(OUTLINE, 5))
        c.drawLine(ex - 14, -10, ex - 2, -10, paint(0x66FFFFFF, 4))
    c.drawLine(11, -6, 17, -6, paint(OUTLINE, 6))
    c.drawLine(-43, -6, -HEAD_RX + 4, -12, paint(OUTLINE, 6))


def _pilot_cap(c):
    ry = HEAD_RY
    crown = skia.Path()
    crown.moveTo(-HEAD_RX * 0.95, -ry * 0.62)
    crown.lineTo(-HEAD_RX * 1.05, -ry * 1.12)
    crown.quadTo(0, -ry * 1.32, HEAD_RX * 1.05, -ry * 1.1)
    crown.lineTo(HEAD_RX * 0.95, -ry * 0.62)
    crown.close()
    c.drawPath(crown, paint(OUTLINE, 12))
    c.drawPath(crown, paint(HAT))
    c.drawRect(skia.Rect.MakeLTRB(-HEAD_RX * 0.95, -ry * 0.8, HEAD_RX * 0.95, -ry * 0.64), paint(0xFF0E0E10))
    c.drawCircle(HEAD_RX * 0.35, -ry * 0.95, 13, paint(0xFFE0B040))
    visor = skia.Path()
    visor.moveTo(HEAD_RX * 0.1, -ry * 0.64)
    visor.quadTo(HEAD_RX * 1.0, -ry * 0.66, HEAD_RX * 1.35, -ry * 0.48)
    visor.quadTo(HEAD_RX * 0.9, -ry * 0.5, HEAD_RX * 0.1, -ry * 0.56)
    visor.close()
    c.drawPath(visor, paint(OUTLINE, 8))
    c.drawPath(visor, paint(0xFF0E0E10))


def _beanie(c):
    ry = HEAD_RY
    p = skia.Path()
    p.moveTo(-HEAD_RX * 0.98, -ry * 0.35)
    p.cubicTo(-HEAD_RX * 1.0, -ry * 1.2, HEAD_RX * 1.0, -ry * 1.2, HEAD_RX * 0.98, -ry * 0.35)
    p.close()
    c.drawPath(p, paint(OUTLINE, 12))
    c.drawPath(p, paint(HAT))
    r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-HEAD_RX * 1.02, -ry * 0.5, HEAD_RX * 1.02, -ry * 0.28), 14, 14)
    c.drawRRect(r, paint(OUTLINE))
    c.drawRRect(skia.RRect.MakeRectXY(r.rect().makeInset(5, 5), 10, 10), paint(HAT))
    for k in range(-3, 4):
        c.drawLine(k * HEAD_RX * 0.28, -ry * 0.46, k * HEAD_RX * 0.28, -ry * 0.32, paint(0x33000000, 4))


def _beard(c):
    p = skia.Path()
    p.moveTo(-HEAD_RX * 0.88, HEAD_RY * 0.25)
    p.cubicTo(-HEAD_RX * 0.7, HEAD_RY * 1.2, HEAD_RX * 0.95, HEAD_RY * 1.2, HEAD_RX * 0.96, HEAD_RY * 0.3)
    p.cubicTo(HEAD_RX * 0.6, HEAD_RY * 0.75, HEAD_RX * 0.2, HEAD_RY * 0.75, 0, HEAD_RY * 0.72)
    p.cubicTo(-HEAD_RX * 0.3, HEAD_RY * 0.75, -HEAD_RX * 0.6, HEAD_RY * 0.6, -HEAD_RX * 0.88, HEAD_RY * 0.25)
    p.close()
    c.drawPath(p, paint(OUTLINE, 8))
    c.drawPath(p, paint(BEARD))


def _fedora(c):
    if HATSTYLE == "pilot":
        return _pilot_cap(c)
    if HATSTYLE == "beanie":
        return _beanie(c)
    """Fedora: wide brim, pinched crown, dark band."""
    ry = HEAD_RY
    c.save()
    c.translate(0, -ry * 0.3)
    crown = skia.Path()
    crown.moveTo(-HEAD_RX * 0.86, -ry * 0.55)
    crown.cubicTo(-HEAD_RX * 0.9, -ry * 1.25, -HEAD_RX * 0.3, -ry * 1.35, 0, -ry * 1.18)
    crown.cubicTo(HEAD_RX * 0.3, -ry * 1.35, HEAD_RX * 0.95, -ry * 1.25, HEAD_RX * 0.9, -ry * 0.55)
    crown.close()
    c.drawPath(crown, paint(OUTLINE, 12))
    c.drawPath(crown, paint(HAT))
    sh = skia.Paint(AntiAlias=True)
    sh.setShader(skia.GradientShader.MakeLinear([(-HEAD_RX, 0), (HEAD_RX, 0)], [0x00000000, 0x44000000]))
    c.drawPath(crown, sh)
    c.drawLine(-HEAD_RX * 0.15, -ry * 1.2, 0, -ry * 0.95, paint(0x55000000, 6))  # crease
    band = skia.Path()
    band.moveTo(-HEAD_RX * 0.88, -ry * 0.78)
    band.quadTo(0, -ry * 0.68, HEAD_RX * 0.92, -ry * 0.78)
    band.lineTo(HEAD_RX * 0.9, -ry * 0.58)
    band.quadTo(0, -ry * 0.48, -HEAD_RX * 0.86, -ry * 0.58)
    band.close()
    c.drawPath(band, paint(0xFF2A2420))
    brim = skia.Rect.MakeLTRB(-HEAD_RX * 1.45, -ry * 0.66, HEAD_RX * 1.5, -ry * 0.42)
    c.drawOval(brim.makeOutset(6, 6), paint(OUTLINE))
    c.drawOval(brim, paint(HAT))
    c.drawOval(skia.Rect.MakeLTRB(brim.left() + 10, brim.top() + 2, brim.right() - 10, brim.top() + 12),
               paint(0x22FFFFFF))
    c.restore()


def draw_head(c, cx, cy, tilt, expr, t, look=(0, 0), blink_seed=0.0, talk=0.0):
    e = EXPR.get(expr, EXPR["neutral"])
    c.save()
    c.translate(cx, cy)
    c.rotate(tilt)
    # head
    oval = skia.Rect.MakeLTRB(-HEAD_RX, -HEAD_RY, HEAD_RX, HEAD_RY)
    c.drawOval(oval.makeOutset(7 if STICK else 5, 7 if STICK else 5), paint(OUTLINE))
    c.drawOval(oval, paint(SKIN))
    if COAT:
        sh = skia.Paint(AntiAlias=True)
        sh.setShader(skia.GradientShader.MakeRadial((-26, -36), HEAD_RX * 1.6,
                                                    [0x00000000, 0x00000000, 0x2A000000], [0, 0.6, 1]))
        c.drawOval(oval, sh)
        if HAIRSTYLE:
            _hair(c)
    elif STICK:
        _stick_head_shading(c, oval)
    else:
        shade = skia.Paint(AntiAlias=True)
        shade.setShader(skia.GradientShader.MakeRadial((-20, -30), 130, [0x00000000, 0x33000000]))
        c.drawOval(oval, shade)
        # hair tuft
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
    fx = 14 if STICK else 16  # face shift toward facing direction (3/4 view)
    eyes = ((-1, -30 + fx), (1, 30 + fx)) if STICK else ((-1, -28 + fx), (1, 32 + fx))
    for side, ex in eyes:
        ey = 0 if STICK else -2
        rx, ry = (21, 25) if STICK else (17, 21)
        c.drawOval(skia.Rect.MakeLTRB(ex - rx - 4, ey - ry - 4, ex + rx + 4, ey + ry + 4), paint(OUTLINE))
        if EYES is not None:  # silhouette: two glowing slits, nothing else
            c.drawOval(skia.Rect.MakeLTRB(ex - 12, ey - 5, ex + 12, ey + 5), paint(EYES))
            continue
        c.drawOval(skia.Rect.MakeLTRB(ex - rx, ey - ry, ex + rx, ey + ry), paint(0xFFFFFFFF))
        pr = e["pupil"]
        pr = pr * (0.95 if COAT else (1.35 if STICK else 1))
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
            p0 = (ex - 22, ey - ry - 12 + outer)
            p1 = (ex + 16, ey - ry - 12 + inner)
        else:
            p0 = (ex - 16, ey - ry - 12 + inner)
            p1 = (ex + 22, ey - ry - 12 + outer)
        c.drawLine(p0[0], p0[1], p1[0], p1[1], paint(OUTLINE, 13 if STICK else 9))
        if STICK and expr in ("tired", "sad", "empty", "scared", "anxious"):
            bag = skia.Path()
            bag.moveTo(ex - rx + 4, ey + ry + 6)
            bag.quadTo(ex, ey + ry + 16, ex + rx - 4, ey + ry + 6)
            c.drawPath(bag, paint(0x99000000, 4))
    if EYES is not None:
        if HAT is not None:
            _fedora(c)
        c.restore()
        return
    if BEARD is not None:
        _beard(c)
    # mouth
    curve, mopen, w = e["mouth"]
    mopen = max(mopen, talk)
    mx, my = (fx + 2, 58) if STICK else (fx + 6, 48)
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
    if GLASSES:
        _glasses(c)
    if HAT is not None:
        _fedora(c)
    c.restore()


def draw(c, p, X, Y, scale=1.0, facing=1, expr="neutral", t=0.0, look=(0, 0),
         blink_seed=0.0, prop_hand=None, talk=0.0, hide_legs=False):
    """Draw character with hips at world (X,Y). prop_hand(c, hand_xy, angle) optional."""
    if COAT:
        return draw_coat(c, p, X, Y, scale, facing, expr, t, look, blink_seed, prop_hand, talk)
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
    joint_chain(c, sh, p["torso"] + p["shR"], UPPER_ARM, p["torso"] + p["shR"] - p["elR"],
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
    # neon chest stripe + drawstrings (streamer only)
    if not STICK:
        c.drawLine(hip[0] - 26 + tdx * 70, hip[1] - tdy * 70, hip[0] + 28 + tdx * 70, hip[1] - tdy * 70,
                   paint(NEON2, 7))
    for dx in ((-10, 12) if not STICK else (-9, 11)):
        c.drawLine(neck[0] + dx, neck[1] + 20, neck[0] + dx - tdx * 40, neck[1] + 20 + tdy * 40,
                   paint(NEON if not STICK else 0xFFBFBFBF, 4))
    if not hide_legs:
        joint_chain(c, hip, p["hipL"], THIGH, p["hipL"] - p["knL"], SHIN, PANTS, 36, SHOE, 0)
        _foot(c, hip, p["hipL"], p["hipL"] - p["knL"], PANTS)
    if STICK:  # hood resting behind the head
        hood = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(neck[0] - 62, neck[1] - 40, neck[0] + 40, neck[1] + 22), 30, 30)
        c.drawRRect(hood, paint(OUTLINE))
        c.drawRRect(skia.RRect.MakeRectXY(hood.rect().makeInset(6, 6), 24, 24), paint(HOODIE_FAR))
    # hood collar
    c.drawCircle(neck[0], neck[1] + 4, 30, paint(OUTLINE))
    c.drawCircle(neck[0], neck[1] + 4, 24, paint(HOODIE_FAR))
    draw_head(c, head_c[0], head_c[1], p["head"], expr, t, look, blink_seed, talk)
    # near arm last
    elbow, hand = joint_chain(c, sh, p["torso"] + p["shL"], UPPER_ARM,
                              p["torso"] + p["shL"] - p["elL"], FOREARM, HOODIE, 32, SKIN, 16)
    if BAND:  # red wristband just above the hand
        bx = hand[0] + (elbow[0] - hand[0]) * 0.22
        by = hand[1] + (elbow[1] - hand[1]) * 0.22
        c.drawCircle(bx, by, 14, paint(OUTLINE))
        c.drawCircle(bx, by, 10, paint(BAND))
    if prop_hand:
        prop_hand(c, hand, p["torso"] + p["shL"] - p["elL"])
    c.restore()


def _shoe(c, ank):
    r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(ank[0] - 20, ank[1] - 14, ank[0] + 40, ank[1] + 14), 14, 14)
    c.drawRRect(r, paint(OUTLINE))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(ank[0] - 15, ank[1] - 9, ank[0] + 35, ank[1] + 9), 10, 10),
                paint(0xFF7A4A2A))
    c.drawLine(ank[0] - 8, ank[1] - 4, ank[0] + 22, ank[1] - 4, paint(0x55FFFFFF, 3))


def _leg_pts(hip, a1, a2):
    d1 = _dir(a1)
    knee = (hip[0] + d1[0] * THIGH, hip[1] + d1[1] * THIGH)
    d2 = _dir(a2)
    return knee, (knee[0] + d2[0] * SHIN, knee[1] + d2[1] * SHIN)


def draw_coat(c, p, X, Y, scale, facing, expr, t, look, blink_seed, prop_hand, talk):
    """Detective: trench coat over shirt and tie, grey trousers, brown shoes, black gloves."""
    c.save()
    c.translate(X + p["x"], Y + p["y"])
    c.scale(scale * facing, scale)
    c.rotate(p["rot"])
    hip = (0, 0)
    tdx, tdy = _dir(p["torso"])
    neck = (tdx * TORSO, -tdy * TORSO)
    sh = (neck[0] - tdx * 22, neck[1] + tdy * 22)
    head_c = (neck[0] + _dir(p["torso"] + p["head"] * 0.5)[0] * NECK * 0.9, neck[1] - NECK)
    kR, aR = _leg_pts(hip, p["hipR"], p["hipR"] - p["knR"])
    kL, aL = _leg_pts(hip, p["hipL"], p["hipL"] - p["knL"])
    # legs
    joint_chain(c, hip, p["hipR"], THIGH, p["hipR"] - p["knR"], SHIN, PANTS_FAR, 32)
    _shoe(c, aR)
    joint_chain(c, sh, p["torso"] + p["shR"], UPPER_ARM, p["torso"] + p["shR"] - p["elR"], FOREARM,
                HOODIE_FAR, 26, GLOVE, 14)
    joint_chain(c, hip, p["hipL"], THIGH, p["hipL"] - p["knL"], SHIN, PANTS, 34)
    _shoe(c, aL)
    # coat: shoulders -> hips -> hem that follows the knees
    pdx, pdy = tdy, tdx  # perpendicular to the torso (pointing forward)
    def P(v, a, b):
        return (v[0] + pdx * a, v[1] + pdy * a + b)
    hem_y = {"long": max(kL[1], kR[1]) + 34, "short": 46, "dress": max(kL[1], kR[1]) + 6}[COAT_LEN]
    if COAT_LEN == "short":
        hem_b, hem_f = -50, 50
    else:
        hem_b = min(kL[0], kR[0], -10) - 34
        hem_f = max(kL[0], kR[0], 10) + 34
    coat = skia.Path()
    s0 = P(sh, -46, -4)
    coat.moveTo(*s0)
    coat.quadTo(neck[0], neck[1] - 20, *P(sh, 46, -4))
    coat.lineTo(*P(hip, 44, 0))
    coat.lineTo(hem_f, hem_y)
    coat.quadTo((hem_f + hem_b) / 2, hem_y + 10, hem_b, hem_y)
    coat.lineTo(*P(hip, -44, 0))
    coat.close()
    c.drawPath(coat, paint(OUTLINE, 12))
    c.drawPath(coat, paint(HOODIE))
    g = skia.Paint(AntiAlias=True)
    g.setShader(skia.GradientShader.MakeLinear([(-50, 0), (50, 0)], [0x50000000, 0x00000000]))
    c.drawPath(coat, g)
    # shirt V, tie, lapels
    v = skia.Path()
    v.moveTo(*P(neck, -16, 8))
    v.lineTo(*P(neck, 22, 8))
    v.lineTo(*P(neck, 10, 80 * tdy))
    v.close()
    c.drawPath(v, paint(SHIRT))
    tie = skia.Path()
    tie.moveTo(*P(neck, 4, 12))
    tie.lineTo(*P(neck, 14, 12))
    tie.lineTo(*P(neck, 16, 70))
    tie.lineTo(*P(neck, 9, 82))
    tie.lineTo(*P(neck, 2, 70))
    tie.close()
    c.drawPath(tie, paint(TIE))
    for side in (-1, 1):
        lap = skia.Path()
        lap.moveTo(*P(neck, 6 + side * 26, 2))
        lap.lineTo(*P(neck, 6 + side * 8, 92))
        lap.lineTo(*P(neck, 6 + side * 36, 40))
        lap.close()
        c.drawPath(lap, paint(HOODIE_FAR))
        c.drawPath(lap, paint(OUTLINE, 5))
    # front edge, buttons, belt
    fx0 = P(neck, 12, 90)
    c.drawLine(fx0[0], fx0[1], (hem_f + hem_b) / 2 + 20, hem_y + 4, paint(0x88000000, 4))
    for k in (0.25, 0.5):
        bx = ch_lerp(fx0[0], (hem_f + hem_b) / 2 + 20, k) + 10
        by = ch_lerp(fx0[1], hem_y, k)
        c.drawCircle(bx, by, 5, paint(0xFF4A3420))
    b0, b1 = P(hip, -46, -24), P(hip, 46, -24)
    c.drawLine(b0[0], b0[1], b1[0], b1[1], paint(OUTLINE, 14, cap=False))
    c.drawLine(b0[0], b0[1], b1[0], b1[1], paint(HOODIE_FAR, 9, cap=False))
    # pocket with a yellow notebook
    pk = P(hip, 14, 22)
    if NOTEBOOK:
        outlined = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(pk[0] - 18, pk[1] - 22, pk[0] + 10, pk[1] + 6), 3, 3)
        c.drawRRect(outlined, paint(0xFFF2D04A))
        c.drawRRect(outlined, paint(OUTLINE, 4))
    c.drawLine(pk[0] - 24, pk[1] - 2, pk[0] + 26, pk[1] - 2, paint(OUTLINE, 5))
    # popped collar behind the head
    col = skia.Path()
    col.moveTo(*P(neck, -40, 14))
    col.lineTo(*P(neck, -30, -34))
    col.lineTo(*P(neck, 30, -30))
    col.lineTo(*P(neck, 42, 14))
    col.close()
    c.drawPath(col, paint(OUTLINE, 10))
    c.drawPath(col, paint(HOODIE_FAR))
    draw_head(c, head_c[0], head_c[1], p["head"], expr, t, look, blink_seed, talk)
    elbow, hand = joint_chain(c, sh, p["torso"] + p["shL"], UPPER_ARM,
                              p["torso"] + p["shL"] - p["elL"], FOREARM, HOODIE, 28, GLOVE, 15)
    # cuff
    cx_ = hand[0] + (elbow[0] - hand[0]) * 0.25
    cy_ = hand[1] + (elbow[1] - hand[1]) * 0.25
    c.drawCircle(cx_, cy_, 17, paint(OUTLINE))
    c.drawCircle(cx_, cy_, 12, paint(HOODIE_FAR))
    if prop_hand:
        prop_hand(c, hand, p["torso"] + p["shL"] - p["elL"])
    c.restore()


def ch_lerp(a, b, t):
    return a + (b - a) * t


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


# ---- extra actions (series) ------------------------------------------------
def act_sit(t, **_):  # seated, hands resting on the lap
    b = math.sin(t * 1.3)
    return pose(torso=4 + b * 0.8, head=4, hipL=88, knL=92, hipR=84, knR=88,
                shL=40, elL=60, shR=34, elR=56)


def act_sit_drink(t, **_):
    p = act_sit(t)
    p.update(shL=20, elL=120 + math.sin(t * 0.7) * 4)
    return p


def act_sit_turn(t, **_):  # seated, leaning toward the aisle to talk
    p = act_sit(t)
    p.update(torso=10, head=-8, shL=60, elL=40)
    return p


def act_hang(t, **_):  # under a parachute, holding the risers
    s = math.sin(t * 1.4)
    return pose(torso=s * 3, head=-10, shL=168, elL=12, shR=-168, elR=-12,
                hipL=10 + s * 8, knL=14, hipR=-6 - s * 8, knR=10)


def act_fall(t, **_):  # free fall, limbs spread
    s = math.sin(t * 3)
    return pose(rot=s * 6, torso=0, head=-20, shL=120 + s * 10, elL=20, shR=-120 - s * 10, elR=-20,
                hipL=30, knL=30, hipR=-30, knR=30)


def act_point(t, **_):
    b = math.sin(t * 1.5) * 2
    return pose(torso=2, head=-4, shL=92 + b, elL=4, shR=-6, elR=10)


def act_dig(t, **_):  # kneeling, scooping sand
    s = (math.sin(t * 4) + 1) / 2
    return pose(torso=40, head=30, hipL=0, knL=95, hipR=-6, knR=95,
                shL=40 + s * 40, elL=20, shR=30 + (1 - s) * 40, elR=20, y=SHIN - 10)


def act_think(t, **_):  # hand on chin
    b = math.sin(t * 1.2)
    return pose(torso=2, head=8 + b, shL=20, elL=140, shR=-4, elR=8)


ACTIONS.update({k[4:]: v for k, v in list(globals().items()) if k.startswith("act_")})
