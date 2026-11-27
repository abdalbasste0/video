"""The 25 story beats. Each scene(ctx, t) draws one 5-second shot; camera is locked."""
import math, random
import cairo
from gfx import *


# ------------------------------------------------------------ shared settings
def dawn_sky(ctx):
    sky(ctx, [(0, "#1C2645"), (0.38, "#5C4A78"), (0.58, "#E68A6B"), (0.66, "#FFC98F")])

def sunset_sky(ctx):
    sky(ctx, [(0, "#2A1838"), (0.35, "#7A2E45"), (0.55, "#E0603A"), (0.64, "#FFB25E")])

def night_sky(ctx, t, moon_xy=(1500, 200)):
    sky(ctx, [(0, "#060A18"), (0.5, "#101C3A"), (0.62, "#1E3358")])
    stars(ctx, t)
    if moon_xy:
        moon(ctx, *moon_xy, 46)

def day_sky(ctx):
    sky(ctx, [(0, "#2D6FB7"), (0.45, "#7FB6E6"), (0.6, "#D7ECF7")])

def storm_sky(ctx):
    sky(ctx, [(0, "#0D1218"), (0.45, "#2A3642"), (0.6, "#4A5A66")])

def gulls(ctx, t, n=4, seed=2, col=(0.08, 0.08, 0.1)):
    rnd = random.Random(seed)
    for i in range(n):
        x = (rnd.uniform(0, W) + t * rnd.uniform(40, 90)) % (W + 200) - 100
        y = rnd.uniform(120, 380) + 20 * math.sin(t * 0.8 + i)
        s = rnd.uniform(14, 26)
        f = math.sin(t * 7 + i * 2) * 0.5
        rgba(ctx, col); ctx.set_line_width(3)
        ctx.move_to(x - s, y - s * (0.3 + f * 0.6)); ctx.curve_to(x - s * 0.5, y - s * 0.5, x - s * 0.2, y - s * 0.3, x, y)
        ctx.curve_to(x + s * 0.2, y - s * 0.3, x + s * 0.5, y - s * 0.5, x + s, y - s * (0.3 + f * 0.6))
        ctx.stroke()

def rain(ctx, t, n=260, a=0.25, slant=0.25, seed=4):
    rnd = random.Random(seed)
    rgba(ctx, (0.8, 0.85, 0.95), a); ctx.set_line_width(1.6)
    for i in range(n):
        x0, sp, ln = rnd.uniform(-200, W), rnd.uniform(900, 1400), rnd.uniform(18, 40)
        y = (rnd.uniform(0, H) + t * sp) % (H + 60) - 30
        x = x0 + y * slant
        ctx.move_to(x, y); ctx.line_to(x + ln * slant, y + ln); ctx.stroke()

def ghost(ctx, x, ground, size, t, a, seed=0):
    """Faded crew member silhouette (not Karim)."""
    if a <= 0.01:
        return
    ctx.push_group()
    rnd = random.Random(seed)
    hr, tor, lg = size * 0.14, size * 0.32, size * 0.38
    sway = 0.04 * math.sin(t * 1.5 + seed)
    rgba(ctx, (0.85, 0.9, 1.0)); ctx.set_line_width(size * 0.02); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    hip = (x, ground - lg)
    ctx.move_to(x - size * 0.05, ground); ctx.line_to(*hip); ctx.line_to(x + size * 0.05, ground); ctx.stroke()
    top = (x + math.sin(sway) * tor, hip[1] - tor)
    ctx.move_to(*hip); ctx.line_to(*top); ctx.stroke()
    ctx.move_to(top[0] - size * 0.12, top[1] + size * 0.25); ctx.line_to(top[0], top[1] + size * 0.03)
    ctx.line_to(top[0] + size * 0.12, top[1] + size * 0.25); ctx.stroke()
    ctx.arc(top[0], top[1] - hr * 1.1, hr, 0, TAU); ctx.fill()
    rgba(ctx, hexc(rnd.choice(["#3C6E91", "#8C5A3C", "#5B7F4A"]))); ctx.set_line_width(size * 0.07)
    ctx.move_to(hip[0], hip[1] - tor * 0.1); ctx.line_to(top[0], top[1] + tor * 0.15); ctx.stroke()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    # dissolving particles
    rnd2 = random.Random(seed + 100)
    for i in range(18):
        p = (t * 0.4 + rnd2.random()) % 1
        rgba(ctx, (0.85, 0.9, 1.0), (1 - a) * 0.6 * (1 - p))
        ctx.arc(x + rnd2.uniform(-size * 0.2, size * 0.2) + p * 40, ground - rnd2.uniform(0, size) - p * 120, 3, 0, TAU)
        ctx.fill()

def deck_floor(ctx, y, col="#8A6440", dark="#5E412A"):
    g = cairo.LinearGradient(0, y, 0, H)
    g.add_color_stop_rgba(0, *hexc(col)); g.add_color_stop_rgba(1, *hexc(dark))
    ctx.set_source(g); ctx.rectangle(0, y, W, H - y); ctx.fill()
    rgba(ctx, hexc("#3E2A1A", 0.6)); ctx.set_line_width(2)
    for k in range(-12, 13):
        ctx.move_to(W / 2 + k * 80, y); ctx.line_to(W / 2 + k * 260, H); ctx.stroke()
    for k in range(1, 6):
        yy = y + (H - y) * (k / 6) ** 1.6
        ctx.move_to(0, yy); ctx.line_to(W, yy); ctx.stroke()

def railing(ctx, y, x0=0, x1=W, col="#E8E2D6"):
    rgba(ctx, INK); ctx.set_line_width(10)
    ctx.move_to(x0, y); ctx.line_to(x1, y); ctx.stroke()
    rgba(ctx, hexc(col)); ctx.set_line_width(6)
    ctx.move_to(x0, y); ctx.line_to(x1, y); ctx.stroke()
    for px in range(int(x0) + 30, int(x1), 120):
        rgba(ctx, INK); ctx.set_line_width(8); ctx.move_to(px, y); ctx.line_to(px, y + 110); ctx.stroke()
        rgba(ctx, hexc(col)); ctx.set_line_width(4); ctx.move_to(px, y); ctx.line_to(px, y + 110); ctx.stroke()
    rgba(ctx, hexc(col)); ctx.set_line_width(4)
    ctx.move_to(x0, y + 55); ctx.line_to(x1, y + 55); ctx.stroke()

def cabin_room(ctx, t, lamp_x=960, lamp_y=120, light=1.0, porthole=True):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *hexc("#2A1C14")); g.add_color_stop_rgba(1, *hexc("#4A3222"))
    ctx.set_source(g); ctx.rectangle(0, 0, W, H); ctx.fill()
    rgba(ctx, hexc("#1A110B", 0.7)); ctx.set_line_width(3)
    for x in range(0, W, 95):
        ctx.move_to(x, 0); ctx.line_to(x, 800); ctx.stroke()
    # floor
    g = cairo.LinearGradient(0, 800, 0, H)
    g.add_color_stop_rgba(0, *hexc("#5A3E28")); g.add_color_stop_rgba(1, *hexc("#2E1F14"))
    ctx.set_source(g); ctx.rectangle(0, 800, W, H - 800); ctx.fill()
    rgba(ctx, hexc("#1A110B", 0.6)); ctx.set_line_width(2)
    for k in range(-10, 11):
        ctx.move_to(W / 2 + k * 100, 800); ctx.line_to(W / 2 + k * 220, H); ctx.stroke()
    if porthole:
        px, py = 1560, 360
        ctx.save(); ctx.arc(px, py, 95, 0, TAU); ctx.clip()
        sky(ctx, [(0, "#18284A"), (0.4, "#3A5A86")])
        rgba(ctx, hexc("#0E2238"))
        ctx.move_to(px - 100, py + 200)
        for xx in range(-100, 101, 10):
            ctx.line_to(px + xx, py + 10 + 8 * math.sin(xx * 0.05 + t * 2) + 12 * math.sin(t * 0.9))
        ctx.line_to(px + 100, py + 200); ctx.close_path(); ctx.fill()
        ctx.restore()
        rgba(ctx, hexc("#B08D57")); ctx.set_line_width(18); ctx.arc(px, py, 100, 0, TAU); ctx.stroke()
        outline(ctx, 4); ctx.arc(px, py, 110, 0, TAU); ctx.stroke()
        for k in range(8):
            an = k / 8 * TAU
            rgba(ctx, hexc("#6E5530")); ctx.arc(px + math.cos(an) * 100, py + math.sin(an) * 100, 6, 0, TAU); ctx.fill()
    # swinging lamp
    sw = 0.22 * math.sin(t * 1.6)
    lx, ly = lamp_x + math.sin(sw) * 160, lamp_y + math.cos(sw) * 160
    rgba(ctx, INK); ctx.set_line_width(3); ctx.move_to(lamp_x, 0); ctx.line_to(lx, ly); ctx.stroke()
    flick = light * (0.85 + 0.15 * math.sin(t * 17) * math.sin(t * 5.3))
    # light cone
    g = cairo.RadialGradient(lx, ly, 0, lx, ly, 900)
    g.add_color_stop_rgba(0, 1, 0.85, 0.55, 0.45 * flick)
    g.add_color_stop_rgba(1, 1, 0.85, 0.55, 0)
    ctx.set_source(g)
    ctx.move_to(lx, ly); ctx.line_to(lx + 700 * math.sin(sw) - 650, H); ctx.line_to(lx + 700 * math.sin(sw) + 650, H)
    ctx.close_path(); ctx.fill()
    glow(ctx, lx, ly, 260, "#FFC46B", 0.5 * flick)
    poly(ctx, [(lx - 30, ly), (lx + 30, ly), (lx + 22, ly + 40), (lx - 22, ly + 40)], "#3A3A40", w=3)
    rgba(ctx, (1, 0.9, 0.6, flick)); ctx.arc(lx, ly + 44, 14, 0, TAU); ctx.fill()
    return lx, ly

def table(ctx, x, y, w=520, food=True, t=0.0):
    poly(ctx, [(x - w / 2, y), (x + w / 2, y), (x + w / 2 + 30, y + 30), (x - w / 2 - 30, y + 30)], "#6B4527", w=4)
    for lx in (x - w / 2 + 10, x + w / 2 - 30):
        poly(ctx, [(lx, y + 30), (lx + 20, y + 30), (lx + 20, y + 230), (lx, y + 230)], "#4A2F1A", w=3)
    if food:
        for k, px in enumerate((x - 150, x + 60)):
            rgba(ctx, (0.95, 0.95, 0.92)); ctx.save(); ctx.translate(px, y + 8); ctx.scale(70, 16); ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
            ctx.fill_preserve(); outline(ctx, 3); ctx.stroke()
            rgba(ctx, hexc("#C8783A")); ctx.save(); ctx.translate(px - 10, y); ctx.scale(36, 12); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
            rgba(ctx, hexc("#5E9E4A")); ctx.arc(px + 22, y + 2, 10, 0, TAU); ctx.fill()
            rgba(ctx, hexc("#E8D27A")); ctx.arc(px - 30, y - 4, 8, 0, TAU); ctx.fill()
        # mug with steam
        poly(ctx, [(x + 180, y + 4), (x + 220, y + 4), (x + 216, y - 50), (x + 184, y - 50)], "#E8E2D6", w=3)
        steam(ctx, x + 200, y - 56, t)
        poly(ctx, [(x - 260 + 40, y + 2), (x - 240 + 40, y + 2), (x - 240 + 40, y - 60), (x - 260 + 40, y - 60)], "#3E6B4A", w=3)

def chair(ctx, x, y, tilt=0.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(tilt)
    poly(ctx, [(-60, -120), (60, -120), (60, -100), (-60, -100)], "#6B4527", w=3)
    rgba(ctx, INK); ctx.set_line_width(8)
    for lx in (-50, 50):
        ctx.move_to(lx, -100); ctx.line_to(lx, 0); ctx.stroke()
    ctx.move_to(50, -120); ctx.line_to(55, -300); ctx.stroke()
    ctx.move_to(-50, -120); ctx.line_to(-45, -300); ctx.stroke()
    poly(ctx, [(-52, -300), (58, -300), (58, -260), (-52, -260)], "#6B4527", w=3)
    ctx.restore()

def wall_clock(ctx, x, y, t, r=80):
    rgba(ctx, hexc("#F2EBDC")); ctx.arc(x, y, r, 0, TAU); ctx.fill_preserve()
    rgba(ctx, hexc("#8B5E34")); ctx.set_line_width(12); ctx.stroke_preserve(); outline(ctx, 3); ctx.stroke()
    for k in range(12):
        an = k / 12 * TAU
        rgba(ctx, INK); ctx.set_line_width(4 if k % 3 == 0 else 2)
        ctx.move_to(x + math.cos(an) * r * 0.78, y + math.sin(an) * r * 0.78)
        ctx.line_to(x + math.cos(an) * r * 0.9, y + math.sin(an) * r * 0.9); ctx.stroke()
    sec = math.floor(t * 2) / 2
    for ang, ln, w in [((8.3 / 12) * TAU, 0.45, 6), ((sec / 60 * 6 + 0.1) * TAU / 1, 0.0, 0), (sec * TAU / 30 * 1.0, 0.8, 2)]:
        if ln == 0:
            continue
        a = ang - math.pi / 2
        rgba(ctx, hexc("#B3342C") if w == 2 else INK); ctx.set_line_width(w)
        ctx.move_to(x, y); ctx.line_to(x + math.cos(a) * r * ln, y + math.sin(a) * r * ln); ctx.stroke()
    a = (2.1 / 12) * TAU - math.pi / 2
    rgba(ctx, INK); ctx.set_line_width(5)
    ctx.move_to(x, y); ctx.line_to(x + math.cos(a) * r * 0.65, y + math.sin(a) * r * 0.65); ctx.stroke()
    rgba(ctx, INK); ctx.arc(x, y, 6, 0, TAU); ctx.fill()
    # pendulum
    pa = 0.35 * math.sin(t * math.pi * 2)
    px, py = x + math.sin(pa) * 150, y + r + math.cos(pa) * 150
    rgba(ctx, hexc("#8B5E34")); ctx.set_line_width(4); ctx.move_to(x, y + r); ctx.line_to(px, py); ctx.stroke()
    rgba(ctx, hexc("#D9A441")); ctx.arc(px, py, 18, 0, TAU); ctx.fill_preserve(); outline(ctx, 3); ctx.stroke()

def coat(ctx, x, y, t):
    sw = 0.06 * math.sin(t * 1.6 + 0.5)
    rgba(ctx, INK); ctx.arc(x, y, 8, 0, TAU); ctx.fill()
    ctx.save(); ctx.translate(x, y); ctx.rotate(sw)
    poly(ctx, [(-10, 6), (10, 6), (70, 60), (80, 260), (-80, 260), (-70, 60)], "#3F5872", w=4)
    rgba(ctx, INK); ctx.set_line_width(3); ctx.move_to(0, 20); ctx.line_to(0, 255); ctx.stroke()
    for k in range(4):
        rgba(ctx, hexc("#D9A441")); ctx.arc(10, 70 + k * 45, 6, 0, TAU); ctx.fill()
    ctx.restore()
    ctx.save(); ctx.translate(x + 150, y); ctx.rotate(-sw * 1.2)
    rgba(ctx, INK); ctx.arc(0, 0, 8, 0, TAU); ctx.fill()
    poly(ctx, [(-8, 6), (8, 6), (55, 50), (60, 190), (-60, 190), (-55, 50)], "#B3342C", w=4)
    ctx.restore()

def desk_scene(ctx, t, flicker=0.0):
    sky(ctx, [(0, "#14161E"), (1, "#262A36")])
    # wall map
    poly(ctx, [(240, 120), (900, 120), (900, 500), (240, 500)], "#3A5068", w=4)
    rnd = random.Random(8)
    for i in range(7):
        x, y = rnd.uniform(290, 850), rnd.uniform(160, 460)
        rgba(ctx, hexc("#C8B98A", 0.7)); ctx.save(); ctx.translate(x, y); ctx.scale(rnd.uniform(30, 70), rnd.uniform(20, 45))
        ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    for i in range(6):
        x, y = rnd.uniform(290, 850), rnd.uniform(160, 460)
        rgba(ctx, hexc("#E0443A")); ctx.arc(x, y, 7, 0, TAU); ctx.fill()
    # window with night sea
    ctx.save(); rrect(ctx, 1180, 110, 520, 380, 10); ctx.clip()
    sky(ctx, [(0, "#0A1022"), (0.4, "#1A2A4A")]); stars(ctx, t, n=50, ymax=300)
    moon(ctx, 1560, 190, 28)
    rgba(ctx, hexc("#0D1B2E")); ctx.rectangle(1180, 360, 520, 200); ctx.fill()
    ctx.restore()
    rgba(ctx, INK); ctx.set_line_width(10); rrect(ctx, 1180, 110, 520, 380, 10); ctx.stroke()
    ctx.move_to(1440, 110); ctx.line_to(1440, 490); ctx.stroke()
    on = 1.0 - flicker * (1 if (math.sin(t * 13) * math.sin(t * 3.1) > 0.55) else 0)
    return on

def desk_front(ctx, t, on=1.0, folder_open=1.0, papers_fly=0.0):
    poly(ctx, [(0, 760), (W, 760), (W, H), (0, H)], "#4A2F1A", w=0)
    poly(ctx, [(0, 740), (W, 740), (W, 790), (0, 790)], "#6B4527", w=4)
    # lamp
    poly(ctx, [(1350, 740), (1450, 740), (1430, 720), (1370, 720)], "#2B2B30", w=3)
    rgba(ctx, INK); ctx.set_line_width(8); ctx.move_to(1400, 720); ctx.line_to(1340, 560); ctx.line_to(1250, 520); ctx.stroke()
    poly(ctx, [(1200, 470), (1300, 520), (1250, 590), (1160, 540)], "#2E5E4E", w=3)
    g = cairo.RadialGradient(1170, 600, 0, 1170, 600, 700)
    g.add_color_stop_rgba(0, 1, 0.9, 0.6, 0.55 * on); g.add_color_stop_rgba(1, 1, 0.9, 0.6, 0)
    ctx.set_source(g); ctx.move_to(1210, 560); ctx.line_to(500, 800); ctx.line_to(1400, 800); ctx.close_path(); ctx.fill()
    glow(ctx, 1200, 560, 180, "#FFD27A", 0.6 * on)
    # folder
    poly(ctx, [(640, 745), (980, 745), (1000, 770), (620, 770)], "#C9A15E", w=3)
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    # papers flying
    rnd = random.Random(3)
    for i in range(9):
        p = clamp(papers_fly * 1.4 - i * 0.06)
        x = 700 + i * 30 + p * rnd.uniform(-600, 700)
        y = 735 - p * rnd.uniform(250, 600) + p * p * 300
        ang = p * rnd.uniform(-4, 4)
        ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
        poly(ctx, [(-45, -30), (45, -30), (45, 30), (-45, 30)], "#F2EEE4", w=2)
        rgba(ctx, (0.4, 0.4, 0.45)); ctx.set_line_width(2)
        for k in range(4):
            ctx.move_to(-35, -18 + k * 12); ctx.line_to(30, -18 + k * 12); ctx.stroke()
        ctx.restore()


# ============================================================ the 25 scenes
def s01(ctx, t):  # A ship leaves the harbor at dawn.
    dawn_sky(ctx)
    sun(ctx, 1240, 640 - t * 8, 46, core="#FFF1CF", halo="#FF9E5E")
    god_rays(ctx, 1240, 640 - t * 8, t, n=11, a=0.05, spread=2.6)
    clouds(ctx, t, "#F4B8A0", 0.35, seed=3, n=7, ymin=120, ymax=420)
    for cx in (140, 330):
        crane(ctx, cx, 640, 0.9)
    sea(ctx, t, 640, top="#47607E", bottom="#141F33", spec="#FFC98F", spec_x=1240, spec_a=0.55)
    trawler(ctx, 900 + t * 55, 690, 0.95, t, lights=0.35)
    ripples(ctx, 900 + t * 55 - 220, 705, t, a=0.25, rmax=120)
    gulls(ctx, t, n=4)
    pier(ctx, -20, 620, 900, t)
    bollard(ctx, 520, 880)
    k = ramp(t, 0.6, 1.6) * (1 - ramp(t, 3.8, 4.8))
    wave = 0.25 * math.sin(t * 7)
    karim(ctx, 300, 880, 360, t, dir=1, expr="tense", look=(0.6, -0.2),
          pose=dict(ls=lerp(0.22, 2.7 + wave, k), le=lerp(0.12, 0.3, k)))
    fog(ctx, t, 650, 220, "#F6C9B4", 0.16)
    vignette(ctx)

def s02(ctx, t):  # By sunset, it's gone.
    sunset_sky(ctx)
    sun(ctx, 980, 668, 54, core="#FFE6B0", halo="#FF7A3D", ha=0.7)
    god_rays(ctx, 980, 668, t, col="#FFB070", n=12, a=0.06, spread=2.8)
    clouds(ctx, t, "#C2506A", 0.4, seed=8, n=7, ymin=80, ymax=380, speed=5)
    sea(ctx, t, 668, top="#7A3A4A", bottom="#170E20", spec="#FFB25E", spec_x=980, spec_a=0.7)
    trawler(ctx, 1500, 680, 0.35, t, alpha=0.6 * (1 - ramp(t, 0.0, 1.4)), smoke_on=False)
    pier(ctx, -20, 760, 930, t, col="#4A3020")
    k = ramp(t, 1.2, 1.7)
    karim(ctx, 420 - 30 * k, 904, 380, t, dir=1, expr="shock" if t > 1.2 else "tense", look=(0.7, 0),
          pose=dict(lean=-0.12 * k, ls=lerp(0.22, 1.9, k), le=lerp(0.12, 1.6, k), rs=lerp(-0.22, 1.5, k), re=lerp(-0.12, 1.4, k),
                    lh=lerp(0.06, 0.25, k), rh=lerp(-0.06, -0.3, k)), shiver=k * 0.4)
    vignette(ctx, 0.6)

def s03(ctx, t):  # Not even a drop of fuel on the surface.
    sky(ctx, [(0, "#3A4A6A"), (0.25, "#9A8AA0")])
    clouds(ctx, t, "#C9C3D6", 0.4, seed=12, n=4, ymin=40, ymax=180, smin=60, smax=110)
    sea(ctx, t * 0.6, 260, top="#3E5E7E", bottom="#0E1E30", layers=9, amp=6, calm=0.5, foam_a=0.2,
        spec_x=1300, spec="#E8E0F0", spec_a=0.35)
    # clean surface, ripples from his fingertips
    dip = ramp(t, 0.8, 1.6) * (1 - ramp(t, 3.6, 4.4))
    ty, rot = raft(ctx, 640, 820, 1.4, t)
    if dip > 0.5:
        ripples(ctx, 980, 880, t - 1.6, a=0.6, rmax=260, period=1.6)
    karim(ctx, 600, ty + 4, 400, t, dir=1, expr="fear", look=(0.6, 0.9),
          pose=dict(lean=0.55 * dip + 0.2, head=0.25 * dip, lh=-1.2, lk=2.2, rh=0.6, rk=-0.9,
                    ls=lerp(0.6, 1.25, dip), le=lerp(0.3, 0.1, dip), rs=-0.1, re=0.4))
    # floating "nothing": a flat, empty mirror patch (no oil sheen)
    for i in range(3):
        p = (t * 0.3 + i / 3) % 1
        rgba(ctx, (1, 1, 1), 0.12 * (1 - p))
        ctx.save(); ctx.translate(1350, 600); ctx.scale(1, 0.22); ctx.arc(0, 0, 60 + 300 * p, 0, TAU); ctx.restore()
        ctx.set_line_width(2); ctx.stroke()
    vignette(ctx)

def s04(ctx, t):  # The entire crew... vanished.
    sky(ctx, [(0, "#2C3E5C"), (0.4, "#8DA2B8")])
    sea(ctx, t, 470, top="#4A6A88", bottom="#2A4058", layers=4, amp=5)
    deck_floor(ctx, 600)
    railing(ctx, 470)
    for i, (gx, gs) in enumerate([(380, 330), (620, 350), (860, 320), (1080, 340)]):
        a = 0.8 * (1 - ramp(t, 0.6 + i * 0.6, 1.6 + i * 0.6))
        ghost(ctx, gx, 840 + i * 6, gs, t, a, seed=i)
        # duffel bags vanish too
        rgba(ctx, hexc("#5A6B4A"), a)
        ctx.save(); ctx.translate(gx + 70, 850); ctx.scale(55, 26); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    look = -1 + 2 * ramp(t, 0.5, 4.0) * 0
    karim(ctx, 1520, 900, 420, t, dir=-1, expr="shock", look=(0.8, 0.1),
          pose=dict(lean=0.08, head=0.06 * math.sin(t * 1.3), ls=0.9, le=1.4, rs=0.7, re=1.2), shiver=0.3)
    fog(ctx, t, 560, 200, "#D6E0EA", 0.12, speed=30)
    vignette(ctx)

def s05(ctx, t):  # As if they never boarded at all.
    sky(ctx, [(0, "#5A6E88"), (0.5, "#C6CCD4")])
    sea(ctx, t, 620, top="#5E788E", bottom="#22384A", layers=5, amp=6)
    # ship hull wall at right
    cargo_ship(ctx, 1500, 760, 1.9, t, bob=0.3, hull="#2F3F52")
    # gangway
    poly(ctx, [(560, 880), (1200, 610), (1230, 630), (590, 905)], "#8A8F96", w=4)
    rgba(ctx, INK); ctx.set_line_width(3)
    for k in range(12):
        x = lerp(580, 1210, k / 11); y = lerp(890, 620, k / 11)
        ctx.move_to(x, y); ctx.line_to(x + 18, y + 14); ctx.stroke()
        # footprints that fade away up the gangway
        fa = clamp(1 - ramp(t, 0.5 + k * 0.25, 1.0 + k * 0.25))
        rgba(ctx, hexc("#3A2A20"), 0.7 * fa)
        ctx.save(); ctx.translate(x + 10 + (k % 2) * 8, y + 4); ctx.rotate(-0.4); ctx.scale(9, 5); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    pier(ctx, -20, 760, 920, t)
    karim(ctx, 420, 894, 380, t, dir=1, expr="fear", look=(0.7, -0.6),
          pose=dict(head=-0.1, ls=1.0, le=1.8, lean=-0.04))
    fog(ctx, t, 820, 300, "#E0E6EE", 0.28, speed=40)
    vignette(ctx)

def s06(ctx, t):  # A pattern across every ocean.
    sky(ctx, [(0, "#0B1A2E"), (1, "#123050")])
    # map board
    rgba(ctx, hexc("#173A5E")); rrect(ctx, 160, 80, 1600, 760, 24); ctx.fill_preserve(); outline(ctx, 6); ctx.stroke()
    rgba(ctx, (0.5, 0.75, 1.0, 0.12)); ctx.set_line_width(2)
    for x in range(200, 1760, 80):
        ctx.move_to(x, 100); ctx.line_to(x, 820); ctx.stroke()
    for y in range(120, 840, 80):
        ctx.move_to(180, y); ctx.line_to(1740, y); ctx.stroke()
    land = [(420, 300, 170, 140), (520, 560, 90, 150), (900, 280, 110, 90), (950, 520, 120, 170),
            (1250, 300, 260, 140), (1450, 620, 110, 70), (300, 250, 70, 50), (1150, 640, 50, 40)]
    for x, y, a, b in land:
        rgba(ctx, hexc("#C8B98A")); ctx.save(); ctx.translate(x, y); ctx.scale(a, b)
        ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill_preserve(); outline(ctx, 3); ctx.stroke()
    dots = [(700, 420), (300, 560), (1100, 430), (1600, 450), (780, 680), (1350, 520), (620, 220), (1650, 760), (1150, 230), (260, 720)]
    for i, (x, y) in enumerate(dots):
        on = ramp(t, 0.3 + i * 0.35, 0.5 + i * 0.35)
        if on <= 0:
            continue
        p = (t * 0.9 + i * 0.3) % 1
        rgba(ctx, hexc("#FF4A3A"), 0.6 * (1 - p) * on); ctx.set_line_width(3)
        ctx.arc(x, y, 10 + 40 * p, 0, TAU); ctx.stroke()
        glow(ctx, x, y, 40, "#FF5040", 0.6 * on)
        rgba(ctx, hexc("#FF4A3A"), on); ctx.arc(x, y, 9, 0, TAU); ctx.fill()
    poly(ctx, [(0, 900), (W, 900), (W, H), (0, H)], "#0A121E", stroke=False)
    k = ramp(t, 0.4, 1.0)
    karim(ctx, 1540, 1010, 420, t, dir=-1, expr="tense", look=(0.8, -0.7),
          pose=dict(ls=lerp(0.22, 2.3 + 0.08 * math.sin(t * 2), k), le=lerp(0.1, -0.15, k), head=-0.08))
    vignette(ctx, 0.6)

def s07(ctx, t):  # For hundreds of years.
    night_sky(ctx, t, (420, 170))
    sea(ctx, t, 600, top="#1A2C48", bottom="#060C18", spec="#C9D6FF", spec_x=420, spec_a=0.4)
    for i, (x, s) in enumerate([(900, 0.55), (1350, 0.75), (1700, 0.45)]):
        a = 0.55 * (0.5 + 0.5 * math.sin(t * 0.9 + i * 2.2))
        sail_ship(ctx, x + t * 10, 640 + i * 20, s, t + i, alpha=a, sail="#CFD8E6")
    fog(ctx, t, 640, 360, "#9FB0C8", 0.35, speed=25)
    ty, rot = raft(ctx, 420, 930, 1.2, t)
    lantern_fl = 0.8 + 0.2 * math.sin(t * 13) * math.sin(t * 4.2)
    karim(ctx, 380, ty + 4, 360, t, dir=1, expr="fear", look=(0.8, -0.2),
          pose=dict(ls=1.6, le=-0.3))
    glow(ctx, 520, 640 + 0, 160, "#FFB347", 0.55 * lantern_fl)
    vignette(ctx, 0.65)

def s08(ctx, t):  # Most aren't small or old.
    day_sky(ctx)
    clouds(ctx, t, "#FFFFFF", 0.7, seed=5, n=6)
    sun(ctx, 300, 150, 40, core="#FFFDF0", halo="#FFF2B0", ha=0.4)
    sea(ctx, t, 640, top="#3D7BA8", bottom="#10334F", spec_x=300, spec="#FFFFFF", spec_a=0.4)
    cargo_ship(ctx, 1250, 760, 2.1, t, bob=0.4)
    pier(ctx, -20, 1920, 960, t, col="#6A6E74")
    k = ramp(t, 0.6, 1.3)
    karim(ctx, 420, 934, 430, t, dir=1, expr="tense", look=(0.5, -0.4),
          pose=dict(ls=lerp(0.2, 2.9, k), le=lerp(0.1, 0.25, k), rs=-0.3, re=-0.6 * k, head=-0.06 * k))
    vignette(ctx, 0.4)

def s09(ctx, t):  # Massive vessels, modern equipment, trained crews.
    sky(ctx, [(0, "#3C6E9E"), (0.55, "#BBD6EA")])
    clouds(ctx, t, "#FFFFFF", 0.6, seed=9, n=5, ymin=80, ymax=300)
    sea(ctx, t, 600, top="#3A6F96", bottom="#0F2B44")
    cargo_ship(ctx, 1150 - t * 18, 760, 2.6, t, bob=0.3, lights=0.6)
    for i in range(4):  # crew on deck (tiny silhouettes)
        x = 1150 - t * 18 + (-300 + i * 160) * 2.6 / 2.6
        ghost(ctx, x + 140, 655, 60, t, 0.9, seed=i + 20)
    pier(ctx, -20, 520, 980, t, col="#6A6E74")
    karim(ctx, 260, 954, 240, t, dir=1, expr="fear", look=(0.6, -0.8), pose=dict(head=-0.15, ls=0.4, le=0.5))
    vignette(ctx, 0.4)

def s10(ctx, t):  # Disappeared in calm seas under clear skies.
    sky(ctx, [(0, "#2F7FC8"), (0.6, "#CDE8F8")])
    sun(ctx, 1500, 160, 44, core="#FFFFF4", halo="#FFF5C8", ha=0.45)
    sea(ctx, t * 0.5, 620, top="#4A93C0", bottom="#145076", calm=0.35, spec_x=1500, spec="#FFFFFF", spec_a=0.45)
    fade = 1 - ramp(t, 1.0, 3.6)
    shimmer = 6 * math.sin(t * 25) * (1 - fade) * fade * 4
    cargo_ship(ctx, 1080 + shimmer, 640, 0.6, t, alpha=fade, bob=0.2)
    if 0 < fade < 1:
        for i in range(30):
            rnd = random.Random(i)
            p = (t * 0.6 + rnd.random()) % 1
            rgba(ctx, (1, 1, 1), 0.5 * (1 - fade) * (1 - p) * fade * 3)
            ctx.arc(1080 + rnd.uniform(-200, 200), 600 - p * 120 - rnd.uniform(0, 60), 3, 0, TAU); ctx.fill()
    ty, rot = raft(ctx, 420, 940, 1.25, t)
    k = ramp(t, 2.6, 3.2)
    karim(ctx, 380, ty + 4, 380, t, dir=1, expr="shock" if t > 2.6 else "tense", look=(0.9, -0.2),
          pose=dict(ls=lerp(0.3, 2.2, k), le=lerp(0.1, 2.0, k), lean=-0.06 * k))
    vignette(ctx, 0.35)

def s11(ctx, t):  # Hard to shake.
    night_sky(ctx, t, (1580, 180))
    sea(ctx, t, 640, top="#16294A", bottom="#03070F", spec_x=1580, spec="#C9D6FF", spec_a=0.35)
    glow(ctx, 960, 560, 700, "#6A86C8", 0.18)
    k = ramp(t, 0.2, 1.0)
    karim(ctx, 960, 1180, 1050, t, dir=1, expr="fear", look=(0.1 * math.sin(t * 2.5), 0.1),
          pose=dict(ls=lerp(0.2, 2.75, k), le=lerp(0.1, 0.75, k), rs=lerp(-0.2, -2.75, k), re=lerp(-0.1, -0.75, k),
                    head=0.05 * math.sin(t * 1.4)), shiver=0.5 + 0.5 * k)
    vignette(ctx, 0.7)

def s12(ctx, t):  # The mind wants a big explanation.
    sky(ctx, [(0, "#20163A"), (0.55, "#6A4A88"), (0.66, "#C98AA8")])
    clouds(ctx, t, "#8E6AAE", 0.4, seed=13, n=6)
    sea(ctx, t, 680, top="#4A3A6A", bottom="#100A1E", spec_x=1500, spec="#F0B8D0", spec_a=0.35)
    pier(ctx, -20, 1100, 950, t, col="#4A3020")
    gr = ramp(t, 0.8, 2.2)
    if gr > 0:
        thought_bubble(ctx, 900, 300, 90 + 70 * gr + 8 * math.sin(t * 3), t, "?", a=gr)
    karim(ctx, 560, 924, 420, t, dir=1, expr="think", look=(0.6, -0.6),
          pose=dict(ls=1.0, le=2.25, rs=0.3, re=1.2, head=-0.08 + 0.04 * math.sin(t * 1.2), lean=0.03))
    vignette(ctx)

def s13(ctx, t):  # Simpler and harsher.
    storm_sky(ctx)
    clouds(ctx, t, "#56626E", 0.6, seed=21, n=9, ymin=40, ymax=420, smin=100, smax=200, speed=14)
    sea(ctx, t * 1.3, 640, top="#3A4A58", bottom="#0C1218", amp=16, foam_a=0.45)
    pier(ctx, 300, 1620, 930, t, col="#3E2A1C")
    bollard(ctx, 1200, 904)
    # sits on pier edge, legs dangling, slumped
    karim(ctx, 900, 1020, 400, t, dir=1, expr="sad", seat=900, look=(0.2, 0.7),
          pose=dict(lean=0.32, head=0.3, lh=1.45, lk=-1.45, rh=1.3, rk=-1.35 - 0.1 * math.sin(t * 1.5), ls=0.6, le=0.2, rs=0.3, re=0.3))
    rain(ctx, t)
    grade(ctx, "#1A2430", 0.15)
    vignette(ctx, 0.65)

def s14(ctx, t):  # Found completely empty.
    cabin_room(ctx, t, lamp_x=1100)
    # open door with cold light
    poly(ctx, [(100, 230), (420, 230), (420, 800), (100, 800)], "#0B1018", w=5)
    g = cairo.LinearGradient(100, 0, 700, 0)
    g.add_color_stop_rgba(0, 0.6, 0.75, 0.95, 0.35); g.add_color_stop_rgba(1, 0.6, 0.75, 0.95, 0)
    ctx.set_source(g); ctx.move_to(420, 800); ctx.line_to(100, 800); ctx.line_to(0, H); ctx.line_to(900, H); ctx.close_path(); ctx.fill()
    table(ctx, 1150, 690, food=False, t=t)
    chair(ctx, 1450, 920, tilt=0.0)
    walk = 1 - ramp(t, 2.2, 2.6)
    x = lerp(220, 640, ease(t / 2.4))
    pose = walk_pose(t, 0.9) if t < 2.4 else dict(ls=0.9, le=1.3, rs=0.5, re=1.0, lean=-0.05)
    karim(ctx, x, 960 + (walk_bob(t, 0.9, 400) if t < 2.4 else 0), 400, t, dir=1, expr="fear",
          look=(0.8, 0.1), pose=pose, shiver=0.2)
    vignette(ctx, 0.7)

def s15(ctx, t):  # Stood up and left everything behind.
    lx, ly = cabin_room(ctx, t, lamp_x=820, porthole=True)
    table(ctx, 800, 700, food=True, t=t)
    rock = 0.06 * math.sin(t * 2.4) * math.exp(-t * 0.3)
    chair(ctx, 1150, 930, tilt=0.12 + rock)
    smoke(ctx, 1000, 650, t, col=(1, 1, 1), n=4, size=16, a=0.12, rise=80, wind=10)
    karim(ctx, 1560, 960, 410, t, dir=-1, expr="fear", look=(0.7, 0.2),
          pose=dict(ls=0.3, le=0.4, rs=-0.2, re=0.2, lean=0.02, head=0.05 * math.sin(t)))
    vignette(ctx, 0.7)

def s16(ctx, t):  # Food on the table. Clothes hanging. Clocks ticking.
    lx, ly = cabin_room(ctx, t, lamp_x=700, porthole=False)
    wall_clock(ctx, 1150, 250, t)
    coat(ctx, 1430, 200, t)
    table(ctx, 620, 700, food=True, t=t)
    look_x = lerp(-0.9, 0.9, ramp(t, 0.3, 4.2))
    head = lerp(0.1, -0.15, ramp(t, 2.0, 4.2))
    karim(ctx, 1000, 960, 380, t, dir=-1 if t < 2.0 else 1, expr="fear", look=(abs(look_x), -0.2 - 0.4 * ramp(t, 2, 3)),
          pose=dict(head=head, ls=0.4, le=0.6))
    vignette(ctx, 0.7)

def s17(ctx, t):  # No clean ending.
    on = desk_scene(ctx, t, flicker=0.6)
    karim(ctx, 960, 1080, 600, t, dir=1, expr="sad", look=(-0.2, 0.6),
          pose=dict(ls=2.4, le=1.0 + 0.15 * math.sin(t * 1.5), rs=-0.3, re=1.2, head=0.12, lean=0.05))
    desk_front(ctx, t, on=on, papers_fly=0.0)
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(30); rgba(ctx, hexc("#B3342C"))
    ctx.move_to(720, 765); ctx.show_text("CASE: UNSOLVED")
    vignette(ctx, 0.7)

def s18(ctx, t):  # A rogue wave...
    storm_sky(ctx)
    clouds(ctx, t, "#3A4652", 0.7, seed=30, n=9, ymin=30, ymax=360, smin=120, smax=220, speed=25)
    flash = max(0, math.sin(t * 2.3) ** 30) if t > 2 else 0
    grade(ctx, "#DDE6FF", 0.35 * flash)
    sea(ctx, t * 1.6, 620, top="#2A3A48", bottom="#060A10", amp=26, foam_a=0.6)
    # giant wave rising from the right
    g = ramp(t, 0.2, 3.8)
    crest_x, crest_y = lerp(2300, 1250, g), lerp(700, 120, g)
    ctx.move_to(W + 300, H)
    ctx.line_to(W + 300, crest_y + 40)
    ctx.curve_to(crest_x + 500, crest_y - 60, crest_x + 60, crest_y - 120, crest_x - 140, crest_y + 60)
    ctx.curve_to(crest_x - 60, crest_y + 10, crest_x + 40, crest_y + 140, crest_x - 120, crest_y + 420)
    ctx.curve_to(crest_x - 200, crest_y + 700, crest_x - 300, H - 100, crest_x - 500, H)
    ctx.close_path()
    gg = cairo.LinearGradient(crest_x - 200, crest_y, crest_x + 300, H)
    gg.add_color_stop_rgba(0, *hexc("#3E6A7E")); gg.add_color_stop_rgba(1, *hexc("#0A1A24"))
    ctx.set_source(gg); ctx.fill_preserve(); rgba(ctx, (0.9, 0.95, 1, 0.5)); ctx.set_line_width(5); ctx.stroke()
    rnd = random.Random(1)
    for i in range(80):
        p = (t * 1.2 + rnd.random()) % 1
        fx = crest_x - 140 + rnd.uniform(-80, 260) - p * 220
        fy = crest_y + rnd.uniform(-40, 80) + p * p * 260
        rgba(ctx, (0.95, 0.98, 1), 0.8 * (1 - p))
        ctx.arc(fx, fy, rnd.uniform(3, 9) * (1 - p * 0.5), 0, TAU); ctx.fill()
    railing(ctx, 780, 0, 1100, col="#C8CED6")
    deck_floor(ctx, 900, col="#5E6670", dark="#2A3038")
    k = ramp(t, 1.4, 2.2)
    karim(ctx, 520 - 60 * k, 1000, 400, t, dir=1, expr="shock" if t > 1.4 else "fear", look=(0.8, -0.6),
          pose=dict(lean=-0.18 * k, ls=lerp(0.3, 2.4, k), le=lerp(0.1, 0.9, k), rs=lerp(-0.2, 2.0, k), re=lerp(-0.1, 1.1, k),
                    lh=lerp(0.06, -0.35, k), rh=lerp(-0.06, 0.3, k), rk=-0.3 * k), wind=1.2, shiver=0.5 * k)
    rain(ctx, t, n=320, a=0.3, slant=-0.35)
    vignette(ctx, 0.7)

def s19(ctx, t):  # Mechanical failure, human error.
    sky(ctx, [(0, "#161616"), (1, "#2A2420")])
    alarm = 0.5 + 0.5 * math.sin(t * 6)
    grade(ctx, "#FF2A1A", 0.12 * alarm)
    for y, col in [(180, "#6E6A64"), (300, "#8A5A3A"), (420, "#5E6A70")]:
        rgba(ctx, INK); ctx.set_line_width(56); ctx.move_to(0, y); ctx.line_to(W, y); ctx.stroke()
        rgba(ctx, hexc(col)); ctx.set_line_width(46); ctx.move_to(0, y); ctx.line_to(W, y); ctx.stroke()
        for x in range(120, W, 340):
            poly(ctx, [(x, y - 34), (x + 24, y - 34), (x + 24, y + 34), (x, y + 34)], "#3A3A3A", w=3)
    for gx in (520, 760, 1000):
        rgba(ctx, hexc("#E8E2D6")); ctx.arc(gx, 600, 70, 0, TAU); ctx.fill_preserve(); outline(ctx, 6); ctx.stroke()
        rgba(ctx, hexc("#B3342C")); ctx.set_line_width(10); ctx.arc(gx, 600, 55, -0.6, 0.2); ctx.stroke()
        na = 0.1 + 0.5 * math.sin(t * 9 + gx) + 0.3 * math.sin(t * 23)
        rgba(ctx, INK); ctx.set_line_width(5); ctx.move_to(gx, 600)
        ctx.line_to(gx + math.cos(na - 1.2) * 55, 600 + math.sin(na - 1.2) * 55); ctx.stroke()
    # broken pipe venting smoke + sparks
    smoke(ctx, 1380, 300, t, col=(0.75, 0.75, 0.75), n=14, size=50, a=0.45, rise=200, wind=-60)
    rnd = random.Random(2)
    for i in range(40):
        p = (t * 1.5 + rnd.random()) % 1
        sx, sy = 1380 + rnd.uniform(-80, 80) * p, 330 + p * 420 * rnd.uniform(0.5, 1) + 100 * p * p
        rgba(ctx, (1, 0.85, 0.3), 1 - p); ctx.arc(sx + p * rnd.uniform(-200, 200), sy, 3, 0, TAU); ctx.fill()
    # rotating alarm light
    glow(ctx, 1700, 110, 220, "#FF3A2A", 0.7 * alarm)
    rgba(ctx, hexc("#FF3A2A")); ctx.arc(1700, 110, 30, 0, TAU); ctx.fill()
    poly(ctx, [(0, 860), (W, 860), (W, H), (0, H)], "#2A2A2E", stroke=False)
    rgba(ctx, hexc("#3A3A40")); ctx.set_line_width(3)
    for x in range(0, W, 60):
        ctx.move_to(x, 860); ctx.line_to(x + 30, H); ctx.stroke()
    cough = abs(math.sin(t * 3.2)) ** 3
    karim(ctx, 1100, 990, 400, t, dir=1, expr="fear", look=(0.3, 0.4), mouth="cough" if cough > 0.5 else "wobble",
          pose=dict(lean=0.25 + 0.15 * cough, head=0.2 + 0.1 * cough, ls=2.2, le=1.6, rs=0.6, re=0.6, lh=0.2, rh=-0.2), shiver=0.3)
    smoke(ctx, 700, 900, t, col=(0.5, 0.5, 0.5), n=8, size=90, a=0.2, rise=150, wind=40, seed=3)
    vignette(ctx, 0.7)

def s20(ctx, t):  # Explanations run out.
    sky(ctx, [(0, "#1A1418"), (1, "#2C2228")])
    # cork board with photos and red strings
    poly(ctx, [(260, 120), (1660, 120), (1660, 760), (260, 760)], "#9C7A4E", w=6)
    rnd = random.Random(10)
    pins = []
    for i in range(9):
        x, y = rnd.uniform(340, 1580), rnd.uniform(180, 700)
        pins.append((x, y))
        ctx.save(); ctx.translate(x, y); ctx.rotate(rnd.uniform(-0.15, 0.15) + 0.02 * math.sin(t * 2 + i) * ramp(t, 1.5, 2.0))
        poly(ctx, [(-70, -50), (70, -50), (70, 50), (-70, 50)], "#F2EEE4", w=3)
        if i % 3 == 0:
            ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(70); rgba(ctx, hexc("#B3342C")); ctx.move_to(-20, 25); ctx.show_text("?")
        else:
            rgba(ctx, hexc("#5A7088")); ctx.rectangle(-55, -38, 110, 60); ctx.fill()
            trawler(ctx, 0, 10, 0.18, t, smoke_on=False, bob=0)
        ctx.restore()
        rgba(ctx, hexc("#E0443A")); ctx.arc(x, y - 44, 7, 0, TAU); ctx.fill()
    rgba(ctx, hexc("#C62828")); ctx.set_line_width(3)
    snap = ramp(t, 1.8, 2.4)
    for (a, b) in [(0, 3), (3, 5), (5, 1), (1, 7), (7, 2), (2, 8), (4, 6)]:
        (x0, y0), (x1, y1) = pins[a], pins[b]
        if snap > 0 and a in (3, 7):
            ctx.move_to(x0, y0 - 44); ctx.line_to(lerp(x0, x1, 0.4), lerp(y0, y1, 0.4) + 140 * snap); ctx.stroke()
        else:
            ctx.move_to(x0, y0 - 44); ctx.line_to(x1, y1 - 44); ctx.stroke()
    k = ramp(t, 1.4, 2.0)
    karim(ctx, 960, 960, 560, t, dir=1, expr="shock" if t > 1.4 else "tense", look=(0, -0.3),
          pose=dict(ls=lerp(0.3, 2.2, k), le=lerp(0.1, -0.9, k), rs=lerp(-0.3, -2.2, k), re=lerp(-0.1, 0.9, k), lean=-0.05 * k))
    desk_front(ctx, t, on=0.6 + 0.4 * (math.sin(t * 11) > -0.6), papers_fly=ramp(t, 1.6, 3.6))
    vignette(ctx, 0.7)

def s21(ctx, t):  # No black box, no witness, no body.
    night_sky(ctx, t, None)
    sea(ctx, t, 560, top="#0E1A2E", bottom="#020509", spec_x=None, foam_a=0.2)
    fog(ctx, t, 600, 300, "#5A6A86", 0.3, speed=18)
    sweep = math.sin(t * 0.9) * 0.6
    ty, rot = raft(ctx, 640, 900, 1.3, t)
    karim(ctx, 600, ty + 4, 380, t, dir=1, expr="fear", look=(0.7 + 0.3 * sweep, 0.3), flashlight=True,
          pose=dict(rs=lerp(1.2, 2.0, 0.5 + 0.5 * sweep), re=0.1, ls=0.4, le=0.6, head=-0.05 * sweep))
    vignette(ctx, 0.75)

def s22(ctx, t):  # These stories stay alive.
    night_sky(ctx, t, (380, 160))
    lighthouse(ctx, 1600, 700, 1.0, t)
    sea(ctx, t, 640, top="#13213C", bottom="#03060E", spec_x=380, spec="#C9D6FF", spec_a=0.35)
    rgba(ctx, hexc("#0A0E16")); ctx.move_to(1300, 720); ctx.curve_to(1450, 640, 1800, 640, W, 700); ctx.line_to(W, 760); ctx.line_to(1300, 760); ctx.fill()
    pier(ctx, -20, 900, 930, t, col="#2E2018")
    karim(ctx, 700, 1030, 380, t, dir=1, expr="sad", seat=902, look=(0.7, -0.1),
          pose=dict(lean=0.12, lh=1.45, lk=-1.45, rh=1.35, rk=-1.4 - 0.15 * math.sin(t * 1.2), ls=0.5, le=0.3, rs=0.2, re=0.4, head=0.1))
    vignette(ctx, 0.65)

def s23(ctx, t):  # Satellites and radar.
    sky(ctx, [(0, "#02040C"), (0.6, "#0C1A36"), (0.7, "#1C2E52")])
    stars(ctx, t, n=320, ymax=H * 0.7)
    for i, (y, sp, ph) in enumerate([(160, 60, 0), (300, -45, 900), (90, 35, 1500)]):
        x = (ph + t * sp) % (W + 300) - 150
        ctx.save(); ctx.translate(x, y + 10 * math.sin(t + i)); ctx.rotate(0.3 * i + t * 0.1)
        poly(ctx, [(-14, -10), (14, -10), (14, 10), (-14, 10)], "#C8CED6", w=2)
        for sgn in (-1, 1):
            poly(ctx, [(sgn * 18, -8), (sgn * 70, -8), (sgn * 70, 8), (sgn * 18, 8)], "#2E5EA4", w=2)
        ctx.restore()
        glow(ctx, x, y, 20, "#FF5040", 0.8 * (math.sin(t * 5 + i) > 0.6))
    # radar display (sweep)
    rx, ry, rr = 1520, 380, 230
    rgba(ctx, (0.02, 0.12, 0.06, 0.75)); ctx.arc(rx, ry, rr, 0, TAU); ctx.fill_preserve()
    rgba(ctx, hexc("#4CFF8A", 0.8)); ctx.set_line_width(3); ctx.stroke()
    for k in (0.33, 0.66):
        ctx.arc(rx, ry, rr * k, 0, TAU); rgba(ctx, hexc("#4CFF8A", 0.35)); ctx.set_line_width(1.5); ctx.stroke()
    ang = t * 1.8
    for k in range(30):
        a0 = ang - k * 0.035
        rgba(ctx, (0.3, 1, 0.55, 0.35 * (1 - k / 30)))
        ctx.move_to(rx, ry); ctx.arc(rx, ry, rr, a0 - 0.035, a0); ctx.close_path(); ctx.fill()
    rgba(ctx, (0.3, 1, 0.55, 0.9)); ctx.set_line_width(2)
    ctx.move_to(rx, ry); ctx.line_to(rx + math.cos(ang) * rr, ry + math.sin(ang) * rr); ctx.stroke()
    ctx.select_font_face("DejaVu Sans Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26); rgba(ctx, hexc("#4CFF8A", 0.6 + 0.4 * (math.sin(t * 4) > 0)))
    ctx.move_to(rx - 105, ry + rr + 50); ctx.show_text("NO CONTACT")
    sea(ctx, t, 760, top="#0E1C34", bottom="#02050C", layers=5, foam_a=0.2)
    rgba(ctx, hexc("#0A0E16")); ctx.rectangle(0, 900, 900, 180); ctx.fill()
    turn = ramp(t, 2.2, 2.8)
    karim(ctx, 420, 920, 360, t, dir=1, expr="fear", look=(lerp(0.3, 0.9, turn), lerp(-0.9, -0.2, turn)),
          pose=dict(head=lerp(-0.25, -0.05, turn), ls=0.4, le=0.4))
    vignette(ctx, 0.6)

def s24(ctx, t):  # The ocean is still bigger.
    sky(ctx, [(0, "#0E1430"), (0.4, "#4A3A6A"), (0.62, "#E07A4A"), (0.7, "#FFC27A")])
    sun(ctx, 1300, 740, 70, core="#FFE8B8", halo="#FF8A4A", ha=0.6)
    god_rays(ctx, 1300, 740, t, n=14, a=0.06, spread=3.0, length=2200)
    clouds(ctx, t, "#8A5A7A", 0.45, seed=40, n=8, ymin=60, ymax=520, smin=120, smax=260, speed=4)
    stars(ctx, t, n=90, ymax=300, a=0.6)
    sea(ctx, t * 0.7, 740, top="#5A3A5A", bottom="#0A0A18", spec_x=1300, spec="#FFB86A", spec_a=0.6)
    ty, rot = raft(ctx, 560, 900, 0.32, t)
    karim(ctx, 548, ty + 1, 95, t, dir=1, expr="sad", look=(0.8, 0), pose=dict(ls=0.3))
    vignette(ctx, 0.6)

def s25(ctx, t):  # The sea doesn't always leave a trace.
    sunset_sky(ctx)
    sun(ctx, 1450, 600, 60, core="#FFE0A8", halo="#FF6A3A", ha=0.7)
    clouds(ctx, t, "#A8405A", 0.4, seed=50, n=6, ymin=80, ymax=360, speed=4)
    sea(ctx, t * 0.7, 600, top="#6A3044", bottom="#251425", layers=5, spec_x=1450, spec="#FFB25E", spec_a=0.6)
    # beach
    g = cairo.LinearGradient(0, 760, 0, H)
    g.add_color_stop_rgba(0, *hexc("#C98A62")); g.add_color_stop_rgba(1, *hexc("#6A4030"))
    ctx.set_source(g); ctx.move_to(0, 780)
    for x in range(0, W + 41, 40):
        ctx.line_to(x, 770 + 15 * math.sin(x * 0.004))
    ctx.line_to(W, H); ctx.line_to(0, H); ctx.close_path(); ctx.fill()
    # footprints, erased by the washing wave
    wash = 0.5 - 0.5 * math.cos(t * TAU / 2.5)
    reach = 780 + 160 * wash
    erased = ramp(t, 0.5, 4.5)
    for k in range(10):
        fx, fy = 1500 - k * 95, 960 - k * 14 + (k % 2) * 18
        a = 0.6 * (1 - clamp(erased * 11 - (9 - k)))
        rgba(ctx, hexc("#5A3424"), a)
        ctx.save(); ctx.translate(fx, fy); ctx.scale(16, 8); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    ctx.move_to(0, 760)
    for x in range(0, W + 41, 40):
        ctx.line_to(x, reach + 25 * math.sin(x * 0.01 + t * 2))
    ctx.line_to(W, 760); ctx.close_path()
    rgba(ctx, (0.55, 0.35, 0.45, 0.55)); ctx.fill()
    rgba(ctx, (1, 0.95, 0.9, 0.75)); ctx.set_line_width(5)
    for x in range(0, W + 41, 40):
        y = reach + 25 * math.sin(x * 0.01 + t * 2)
        ctx.line_to(x, y) if x else ctx.move_to(x, y)
    ctx.stroke()
    x = lerp(470, 380, ramp(t, 0, 2.5))
    pose = walk_pose(t, 0.6, 0.3) if t < 2.5 else dict(head=0.05, ls=0.25, le=0.2)
    karim(ctx, x, 990 + (walk_bob(t, 0.6, 380) if t < 2.5 else 0), 380, t, dir=-1 if t < 2.5 else 1,
          expr="sad", look=(0.8, 0), pose=pose)
    vignette(ctx, 0.6)


SCENES = [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12, s13,
          s14, s15, s16, s17, s18, s19, s20, s21, s22, s23, s24, s25]
