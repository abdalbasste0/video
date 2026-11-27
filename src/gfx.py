"""Drawing toolkit: environments, props, and the Karim character rig (pycairo)."""
import math, random
import cairo

W, H = 1920, 1080
TAU = math.tau


# ---------------------------------------------------------------- utilities
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)

def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3

def lerp(a, b, k):
    return a + (b - a) * k

def ramp(t, t0, t1):
    """Eased 0..1 between t0 and t1."""
    return ease((t - t0) / (t1 - t0)) if t1 != t0 else float(t >= t0)

def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)

def mix(c1, c2, k):
    return tuple(lerp(a, b, k) for a, b in zip(c1, c2))

def rgba(ctx, c, a=None):
    if len(c) == 3:
        c = (*c, 1.0)
    ctx.set_source_rgba(c[0], c[1], c[2], c[3] if a is None else a)

def noise1(x, seed=0):
    """Cheap smooth 1D value noise in [-1,1]."""
    i = math.floor(x); f = x - i
    def h(n):
        n = (n * 374761393 + seed * 668265263) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFF) / 32767.5 - 1
    u = f * f * (3 - 2 * f)
    return lerp(h(i), h(i + 1), u)


# ---------------------------------------------------------------- sky & light
def sky(ctx, stops, y0=0, y1=H):
    g = cairo.LinearGradient(0, y0, 0, y1)
    for off, col in stops:
        g.add_color_stop_rgba(off, *hexc(col) if isinstance(col, str) else col)
    ctx.set_source(g)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

def glow(ctx, x, y, r, col, a=0.6):
    c = hexc(col) if isinstance(col, str) else col
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, c[0], c[1], c[2], a)
    g.add_color_stop_rgba(0.35, c[0], c[1], c[2], a * 0.35)
    g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, TAU)
    ctx.fill()

def sun(ctx, x, y, r, core="#FFF4D6", halo="#FFB347", ha=0.55):
    glow(ctx, x, y, r * 9, halo, ha * 0.5)
    glow(ctx, x, y, r * 3.2, halo, ha)
    rgba(ctx, hexc(core))
    ctx.arc(x, y, r, 0, TAU)
    ctx.fill()

def moon(ctx, x, y, r, t=0):
    glow(ctx, x, y, r * 7, "#9FB8FF", 0.25)
    rgba(ctx, hexc("#EEF2FF"))
    ctx.arc(x, y, r, 0, TAU)
    ctx.fill()
    rgba(ctx, hexc("#C9D3EE", 0.7))
    for dx, dy, rr in [(-0.3, -0.2, 0.18), (0.25, 0.3, 0.12), (0.1, -0.4, 0.08)]:
        ctx.arc(x + dx * r, y + dy * r, rr * r, 0, TAU)
        ctx.fill()

def stars(ctx, t, n=220, seed=3, ymax=H * 0.6, a=1.0):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, ymax) ** 1.0
        s = rnd.uniform(0.6, 2.4)
        tw = 0.55 + 0.45 * math.sin(t * rnd.uniform(1.5, 4.5) + rnd.uniform(0, TAU))
        rgba(ctx, (1, 1, 0.95), a * tw * (1 - y / ymax) ** 0.5)
        ctx.arc(x, y, s, 0, TAU)
        ctx.fill()

def god_rays(ctx, x, y, t, col="#FFD9A0", n=9, a=0.07, spread=1.4, length=1600, base=-math.pi / 2):
    c = hexc(col)
    for i in range(n):
        ang = base + (i - n / 2) / n * spread + 0.03 * math.sin(t * 0.4 + i)
        w = 0.035 + 0.025 * math.sin(i * 1.7)
        g = cairo.RadialGradient(x, y, 0, x, y, length)
        aa = a * (0.6 + 0.4 * math.sin(t * 0.7 + i * 2.1))
        g.add_color_stop_rgba(0, c[0], c[1], c[2], aa)
        g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
        ctx.set_source(g)
        ctx.move_to(x, y)
        ctx.line_to(x + math.cos(ang - w) * length, y + math.sin(ang - w) * length)
        ctx.line_to(x + math.cos(ang + w) * length, y + math.sin(ang + w) * length)
        ctx.close_path()
        ctx.fill()

def cloud(ctx, x, y, s, col, a):
    c = hexc(col) if isinstance(col, str) else col
    for dx, dy, r in [(-1.1, 0.15, 0.55), (-0.5, -0.2, 0.75), (0.2, -0.35, 0.85), (0.9, -0.05, 0.65),
                      (1.5, 0.2, 0.45), (0.1, 0.2, 0.7), (-0.2, 0.25, 0.6)]:
        cx, cy, rr = x + dx * s, y + dy * s, r * s
        g = cairo.RadialGradient(cx, cy - rr * 0.3, 0, cx, cy, rr)
        g.add_color_stop_rgba(0, c[0], c[1], c[2], a)
        g.add_color_stop_rgba(0.7, c[0], c[1], c[2], a * 0.6)
        g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
        ctx.set_source(g)
        ctx.arc(cx, cy, rr, 0, TAU)
        ctx.fill()

def clouds(ctx, t, col, a=0.5, seed=1, n=6, ymin=60, ymax=420, speed=8, smin=70, smax=160):
    rnd = random.Random(seed)
    for _ in range(n):
        x0, y, s = rnd.uniform(-300, W + 300), rnd.uniform(ymin, ymax), rnd.uniform(smin, smax)
        sp = speed * rnd.uniform(0.5, 1.5)
        x = (x0 + t * sp + 400) % (W + 800) - 400
        cloud(ctx, x, y, s, col, a * rnd.uniform(0.6, 1))

def fog(ctx, t, y, h, col="#C8D4E0", a=0.25, speed=20, seed=0):
    c = hexc(col)
    for k in range(5):
        yy = y + (k - 2) * h * 0.22 + 10 * math.sin(t * 0.3 + k)
        x = ((t * speed * (0.6 + 0.2 * k) + k * 500) % (W + 1200)) - 600
        for off in (-W - 1200, 0):
            xx = x + off
            g = cairo.RadialGradient(xx + 600, yy, 0, xx + 600, yy, 900)
            g.add_color_stop_rgba(0, c[0], c[1], c[2], a)
            g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
            ctx.save()
            ctx.translate(xx + 600, yy)
            ctx.scale(1, h / 900 * 0.6)
            ctx.translate(-(xx + 600), -yy)
            ctx.set_source(g)
            ctx.arc(xx + 600, yy, 900, 0, TAU)
            ctx.fill()
            ctx.restore()

def vignette(ctx, a=0.55):
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, a)
    ctx.set_source(g)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

def grade(ctx, col, a):
    rgba(ctx, hexc(col) if isinstance(col, str) else col, a)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()


# ---------------------------------------------------------------- sea
def wave_y(x, t, base, amp, k=1.0, seed=0):
    return (base
            + amp * math.sin(x * 0.006 * k + t * 1.1 + seed)
            + amp * 0.5 * math.sin(x * 0.017 * k - t * 1.7 + seed * 2)
            + amp * 0.25 * math.sin(x * 0.041 * k + t * 2.3 + seed * 3))

def sea(ctx, t, horizon, top="#2B5C7A", bottom="#0B2233", layers=7, amp=10, spec="#FFD9A0",
        spec_x=None, spec_a=0.6, foam_a=0.35, calm=1.0):
    g = cairo.LinearGradient(0, horizon, 0, H)
    g.add_color_stop_rgba(0, *hexc(top))
    g.add_color_stop_rgba(1, *hexc(bottom))
    ctx.set_source(g)
    ctx.rectangle(0, horizon, W, H - horizon)
    ctx.fill()
    # sun reflection column
    if spec_x is not None:
        c = hexc(spec)
        rnd = random.Random(11)
        for i in range(90):
            yy = horizon + (rnd.random() ** 1.6) * (H - horizon)
            d = (yy - horizon) / (H - horizon)
            w = 30 + 260 * d
            xx = spec_x + rnd.uniform(-1, 1) * w * 0.5 + 18 * math.sin(t * 2 + i)
            ln = rnd.uniform(20, 90) * (0.4 + d)
            fl = 0.5 + 0.5 * math.sin(t * rnd.uniform(2, 5) + i)
            rgba(ctx, c, spec_a * fl * (1 - d * 0.6))
            ctx.set_line_width(2 + 4 * d)
            ctx.move_to(xx - ln / 2, yy)
            ctx.line_to(xx + ln / 2, yy)
            ctx.stroke()
    # wave layers, back to front
    for L in range(layers):
        d = (L + 1) / layers
        base = horizon + (H - horizon) * (d ** 1.7) * 0.98
        a_amp = amp * (0.25 + 1.6 * d) * calm
        col = mix(hexc(top), hexc(bottom), d * 0.9)
        col = mix(col, (1, 1, 1, 1), 0.04)
        ctx.move_to(0, H)
        for x in range(0, W + 41, 40):
            ctx.line_to(x, wave_y(x, t * (0.8 + d * 0.5), base, a_amp, 1.4 - d * 0.7, L))
        ctx.line_to(W, H)
        ctx.close_path()
        rgba(ctx, col, 0.55)
        ctx.fill()
        # crest highlight
        ctx.set_line_width(1.5 + 2 * d)
        rgba(ctx, (0.85, 0.93, 1.0), foam_a * (0.3 + 0.7 * d))
        first = True
        for x in range(0, W + 41, 40):
            y = wave_y(x, t * (0.8 + d * 0.5), base, a_amp, 1.4 - d * 0.7, L)
            if first:
                ctx.move_to(x, y); first = False
            else:
                ctx.line_to(x, y)
        ctx.stroke()
    # sparkles
    rnd = random.Random(5)
    for i in range(60):
        x = rnd.uniform(0, W)
        y = horizon + rnd.random() ** 1.3 * (H - horizon)
        fl = max(0, math.sin(t * rnd.uniform(1.5, 4) + i * 3.3)) ** 6
        rgba(ctx, (1, 1, 1), 0.7 * fl)
        ctx.arc(x, y, 1.5 + 2 * (y - horizon) / (H - horizon), 0, TAU)
        ctx.fill()

def ripples(ctx, x, y, t, col=(1, 1, 1), n=3, period=2.0, rmax=180, a=0.5, sy=0.25):
    for k in range(n):
        p = ((t / period) + k / n) % 1
        rgba(ctx, col, a * (1 - p))
        ctx.set_line_width(3 * (1 - p) + 1)
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(1, sy)
        ctx.arc(0, 0, 10 + rmax * p, 0, TAU)
        ctx.restore()
        ctx.stroke()


# ---------------------------------------------------------------- props
def outline(ctx, w=4, col=(0.05, 0.05, 0.07)):
    rgba(ctx, col)
    ctx.set_line_width(w)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)

def poly(ctx, pts, fill, stroke=True, w=4, a=1.0):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    rgba(ctx, hexc(fill) if isinstance(fill, str) else fill, a)
    if stroke:
        ctx.fill_preserve()
        outline(ctx, w)
        ctx.stroke()
    else:
        ctx.fill()

def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()

def smoke(ctx, x, y, t, col=(0.75, 0.75, 0.78), n=10, rise=160, spread=40, size=30, a=0.35, seed=0, wind=30):
    rnd = random.Random(seed)
    for i in range(n):
        p = ((t * 0.35) + i / n + rnd.random() * 0.05) % 1
        xx = x + wind * p * 3 + spread * math.sin(i * 2.1 + t * 0.8) * p
        yy = y - rise * p * 2.2
        r = size * (0.4 + p * 1.8)
        g = cairo.RadialGradient(xx, yy, 0, xx, yy, r)
        g.add_color_stop_rgba(0, col[0], col[1], col[2], a * (1 - p))
        g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
        ctx.set_source(g)
        ctx.arc(xx, yy, r, 0, TAU)
        ctx.fill()

def steam(ctx, x, y, t, a=0.45, h=70, seed=0):
    for k in range(3):
        ph = t * 1.3 + k * 2.1 + seed
        rgba(ctx, (1, 1, 1), a * (0.6 + 0.4 * math.sin(ph)))
        ctx.set_line_width(3)
        ctx.move_to(x + (k - 1) * 10, y)
        for s in range(1, 9):
            yy = y - s * h / 8
            xx = x + (k - 1) * 10 + 8 * math.sin(ph + s * 0.9) * s / 8
            ctx.line_to(xx, yy)
        ctx.stroke()

def cargo_ship(ctx, x, y, s, t, alpha=1.0, lights=0.0, bob=1.0, hull="#7A1F1F", deck="#1B2A3A", dir=1):
    """Large modern cargo vessel. (x,y)=waterline center."""
    ctx.save()
    ctx.translate(x, y + 4 * s * math.sin(t * 1.1) * bob)
    ctx.rotate(0.012 * math.sin(t * 0.9) * bob)
    ctx.scale(s * dir, s)
    ctx.push_group()
    # hull
    poly(ctx, [(-300, -40), (290, -40), (340, -70), (330, -40), (300, 18), (-280, 18), (-310, -10)], hull, w=4)
    poly(ctx, [(-300, -40), (290, -40), (300, -22), (-302, -22)], "#E8E2D6", w=3)
    # containers
    cols = ["#2E6DA4", "#C8553D", "#E0A458", "#3F7D5B", "#8E4F8F", "#D9D2C5"]
    rnd = random.Random(4)
    for row in range(3):
        for cx in range(-200, 190, 42):
            if row == 2 and rnd.random() < 0.35:
                continue
            poly(ctx, [(cx, -40 - row * 24), (cx + 40, -40 - row * 24), (cx + 40, -64 - row * 24), (cx, -64 - row * 24)],
                 rnd.choice(cols), w=2)
    # bridge
    poly(ctx, [(-290, -40), (-210, -40), (-210, -150), (-290, -150)], "#E8E2D6", w=3)
    poly(ctx, [(-300, -150), (-200, -150), (-200, -165), (-300, -165)], "#E8E2D6", w=3)
    for wy in (-140, -110, -80):
        for wx in range(-282, -215, 18):
            rgba(ctx, mix(hexc("#2A3B4C"), hexc("#FFE6A8"), lights))
            ctx.rectangle(wx, wy, 12, 10)
            ctx.fill()
    # mast + radar
    outline(ctx, 4)
    ctx.move_to(-250, -165); ctx.line_to(-250, -230); ctx.stroke()
    ang = t * 3
    ctx.move_to(-250 - 24 * math.cos(ang), -228); ctx.line_to(-250 + 24 * math.cos(ang), -228)
    ctx.set_line_width(6); ctx.stroke()
    poly(ctx, [(-262, -165), (-238, -165), (-240, -195), (-260, -195)], "#C8553D", w=3)
    # mast lights
    if lights > 0:
        glow(ctx, -250, -232, 30, "#FF5A4E", 0.7 * lights * (0.5 + 0.5 * math.sin(t * 4)))
        glow(ctx, 330, -72, 24, "#7CFF9E", 0.6 * lights)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()

def trawler(ctx, x, y, s, t, alpha=1.0, lights=0.0, bob=1.0, smoke_on=True, dir=1):
    ctx.save()
    ctx.translate(x, y + 5 * s * math.sin(t * 1.4) * bob)
    ctx.rotate(0.02 * math.sin(t * 1.2) * bob)
    ctx.scale(s * dir, s)
    ctx.push_group()
    if smoke_on:
        smoke(ctx, -20, -175, t, col=(0.6, 0.6, 0.62), n=8, size=22, a=0.3, wind=40)
    poly(ctx, [(-200, -30), (170, -30), (230, -70), (200, 20), (-180, 20)], "#1F4E79", w=4)
    poly(ctx, [(-200, -30), (170, -30), (190, -15), (-195, -15)], "#E8E2D6", w=3)
    poly(ctx, [(-120, -30), (40, -30), (40, -110), (-110, -110)], "#E8E2D6", w=3)
    poly(ctx, [(-40, -110), (0, -110), (0, -165), (-40, -165)], "#C8553D", w=3)
    rgba(ctx, (0.05, 0.05, 0.07)); ctx.rectangle(-40, -165, 40, 10); ctx.fill()
    for wx in (-100, -65, -30, 5):
        rgba(ctx, mix(hexc("#2A3B4C"), hexc("#FFE6A8"), lights))
        ctx.rectangle(wx, -95, 26, 22); ctx.fill()
    outline(ctx, 4)
    ctx.move_to(110, -30); ctx.line_to(110, -200); ctx.stroke()
    ctx.set_line_width(2)
    ctx.move_to(110, -200); ctx.line_to(220, -60); ctx.stroke()
    ctx.move_to(110, -200); ctx.line_to(-110, -110); ctx.stroke()
    if lights > 0:
        glow(ctx, 110, -205, 26, "#FFE6A8", 0.8 * lights)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()

def sail_ship(ctx, x, y, s, t, alpha=1.0, bob=1.0, dir=1, sail="#E9DFC6"):
    ctx.save()
    ctx.translate(x, y + 5 * s * math.sin(t * 1.0) * bob)
    ctx.rotate(0.025 * math.sin(t * 0.8) * bob)
    ctx.scale(s * dir, s)
    ctx.push_group()
    poly(ctx, [(-220, -40), (200, -40), (250, -80), (210, 15), (-190, 15), (-240, -70)], "#5A3A22", w=4)
    rgba(ctx, hexc("#3B2615")); ctx.set_line_width(3)
    for yy in (-25, -8):
        ctx.move_to(-205, yy); ctx.line_to(215, yy); ctx.stroke()
    for mx, hh in [(-100, 260), (40, 300), (160, 200)]:
        outline(ctx, 5); ctx.move_to(mx, -40); ctx.line_to(mx, -40 - hh); ctx.stroke()
        for k in range(2):
            top = -40 - hh + 20 + k * hh * 0.45
            bil = 8 * math.sin(t * 1.5 + mx + k)
            ctx.move_to(mx - 70, top)
            ctx.curve_to(mx - 60 + bil, top + hh * 0.2, mx + 60 + bil, top + hh * 0.2, mx + 70, top)
            ctx.line_to(mx + 65, top + hh * 0.38)
            ctx.curve_to(mx + 30 + bil, top + hh * 0.43, mx - 30 + bil, top + hh * 0.43, mx - 65, top + hh * 0.38)
            ctx.close_path()
            rgba(ctx, hexc(sail)); ctx.fill_preserve(); outline(ctx, 3); ctx.stroke()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()

def raft(ctx, x, y, s, t, bob=1.0):
    ctx.save()
    ctx.translate(x, y + 5 * math.sin(t * 1.6) * bob)
    ctx.rotate(0.03 * math.sin(t * 1.3) * bob)
    ctx.scale(s, s)
    rrect(ctx, -160, -26, 320, 46, 23)
    rgba(ctx, hexc("#D9702E")); ctx.fill_preserve(); outline(ctx, 4); ctx.stroke()
    rgba(ctx, hexc("#F2E8D5")); ctx.set_line_width(5)
    for xx in (-110, -40, 40, 110):
        ctx.move_to(xx, -24); ctx.line_to(xx, 18); ctx.stroke()
    ctx.restore()
    return y + 5 * math.sin(t * 1.6) * bob - 26 * s, 0.03 * math.sin(t * 1.3) * bob

def pier(ctx, x0, x1, y, t, col="#5B3E2B"):
    for px in range(int(x0) + 20, int(x1), 140):
        poly(ctx, [(px, y), (px + 22, y), (px + 22, H), (px, H)], "#3B2718", w=3)
    poly(ctx, [(x0, y - 26), (x1, y - 26), (x1, y + 6), (x0, y + 6)], col, w=4)
    rgba(ctx, hexc("#3B2718")); ctx.set_line_width(2)
    for px in range(int(x0), int(x1), 46):
        ctx.move_to(px, y - 26); ctx.line_to(px, y + 6); ctx.stroke()

def bollard(ctx, x, y):
    poly(ctx, [(x - 16, y), (x + 16, y), (x + 12, y - 36), (x - 12, y - 36)], "#2B2B30", w=3)
    rrect(ctx, x - 22, y - 46, 44, 14, 6)
    rgba(ctx, hexc("#2B2B30")); ctx.fill_preserve(); outline(ctx, 3); ctx.stroke()

def lighthouse(ctx, x, y, s, t, beam=True):
    ang = t * 1.1
    if beam:
        bx, by = x, y - 330 * s
        for side in (0, math.pi):
            a0 = ang + side
            c = math.cos(a0)
            g = cairo.RadialGradient(bx, by, 0, bx, by, 1500)
            g.add_color_stop_rgba(0, 1, 0.95, 0.75, 0.35 * abs(c))
            g.add_color_stop_rgba(1, 1, 0.95, 0.75, 0)
            ctx.set_source(g)
            ctx.move_to(bx, by)
            dx = 1500 * c
            ctx.line_to(bx + dx, by - 120 * (0.3 + abs(c)))
            ctx.line_to(bx + dx, by + 120 * (0.3 + abs(c)))
            ctx.close_path(); ctx.fill()
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    poly(ctx, [(-70, 0), (70, 0), (40, -300), (-40, -300)], "#ECE6DA", w=4)
    for k, yy in enumerate((-60, -160, -250)):
        w0 = 70 - (yy / -300) * 30 * -1
        ctx.save(); ctx.rectangle(-80, yy - 30, 160, 30); ctx.clip()
        poly(ctx, [(-70, 0), (70, 0), (40, -300), (-40, -300)], "#B3342C", w=4)
        ctx.restore()
    poly(ctx, [(-55, -300), (55, -300), (55, -312), (-55, -312)], "#2B2B30", w=3)
    poly(ctx, [(-32, -312), (32, -312), (32, -350), (-32, -350)], "#FFF2C2", w=3)
    poly(ctx, [(-42, -350), (42, -350), (0, -390)], "#2B2B30", w=3)
    ctx.restore()
    glow(ctx, x, y - 330 * s, 90 * s, "#FFE9A8", 0.8)

def crane(ctx, x, y, s, col=(0.08, 0.1, 0.14, 0.85)):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rgba(ctx, col); ctx.set_line_width(6)
    ctx.move_to(-30, 0); ctx.line_to(-10, -300); ctx.line_to(10, -300); ctx.line_to(30, 0); ctx.stroke()
    ctx.move_to(-120, -300); ctx.line_to(260, -300); ctx.stroke()
    ctx.set_line_width(2)
    for k in range(-110, 260, 30):
        ctx.move_to(k, -300); ctx.line_to(k + 15, -280); ctx.line_to(k + 30, -300); ctx.stroke()
    ctx.move_to(200, -300); ctx.line_to(200, -170); ctx.stroke()
    ctx.rectangle(185, -170, 30, 20); ctx.fill()
    ctx.restore()

def thought_bubble(ctx, x, y, r, t, text="?", a=1.0):
    wob = 1 + 0.03 * math.sin(t * 3)
    for dx, dy, rr in [(-r * 0.9, r * 1.4, r * 0.12), (-r * 0.6, r * 1.05, r * 0.2)]:
        rgba(ctx, (1, 1, 1), a); ctx.arc(x + dx, y + dy, rr, 0, TAU); ctx.fill_preserve()
        outline(ctx, 3); ctx.stroke()
    ctx.save(); ctx.translate(x, y); ctx.scale(wob, wob)
    for k in range(9):
        an = k / 9 * TAU
        ctx.arc(math.cos(an) * r * 0.75, math.sin(an) * r * 0.5, r * 0.38, 0, TAU)
        ctx.close_path()
    rgba(ctx, (1, 1, 1), a); ctx.fill()
    ctx.restore()
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(r * 1.1)
    ext = ctx.text_extents(text)
    ctx.move_to(x - ext.width / 2 - ext.x_bearing, y + ext.height / 2)
    rgba(ctx, hexc("#1A1A22"), a); ctx.show_text(text)


# ---------------------------------------------------------------- Karim rig
# Fixed design (identical in every scene):
#   faded orange life vest, slightly torn gray t-shirt, messy black hair,
#   coiled nautical rope on his left shoulder, tense fragile look with old fear.
SKIN_HEAD = (1, 1, 1)
INK = (0.06, 0.06, 0.08)
VEST = hexc("#E07B39")
VEST_DARK = hexc("#B95E26")
SHIRT = hexc("#8E9399")
SHIRT_DARK = hexc("#6C7177")
PANTS = hexc("#2F3A4A")
ROPE = hexc("#C9A15E")
ROPE_DARK = hexc("#8B6A35")

DEFAULT_POSE = dict(lean=0.0, head=0.0, ls=0.22, le=0.12, rs=-0.22, re=-0.12,
                    lh=0.06, lk=0.0, rh=-0.06, rk=0.0)

def pose_mix(a, b, k):
    return {key: lerp(a.get(key, DEFAULT_POSE[key]), b.get(key, DEFAULT_POSE[key]), k) for key in DEFAULT_POSE}

def P(**kw):
    p = dict(DEFAULT_POSE); p.update(kw); return p

def keyframes(t, frames):
    """frames: list of (time, pose). Eased interpolation."""
    if t <= frames[0][0]:
        return P(**frames[0][1]) if isinstance(frames[0][1], dict) else frames[0][1]
    for (t0, p0), (t1, p1) in zip(frames, frames[1:]):
        if t <= t1:
            return pose_mix(P(**p0), P(**p1), ease((t - t0) / (t1 - t0)))
    return P(**frames[-1][1])

def _vec(ang, length):
    # angle measured from straight down, positive = towards +x
    return math.sin(ang) * length, math.cos(ang) * length

def karim(ctx, x, ground, size, t, pose=None, dir=1, expr="fear", look=(0.0, 0.0), blink_seed=0.0,
          wind=0.4, breath=1.0, alpha=1.0, flashlight=False, shiver=0.0, mouth=None, seat=None):
    """Draw Karim with feet on `ground`. size = total height in px (approx)."""
    p = P(**(pose or {}))
    Hs = size
    hr = 0.15 * Hs           # head radius (large round head)
    torso = 0.31 * Hs
    ul, ll = 0.185 * Hs, 0.185 * Hs
    ua, la = 0.15 * Hs, 0.14 * Hs
    sh = shiver * math.sin(t * 40) * 0.01
    br = 1 + 0.015 * math.sin(t * 2.2) * breath

    # legs (relative to hip at 0,0), lean frame applied to body above hip
    def leg(h, k):
        kx, ky = _vec(h, ul)
        fx, fy = _vec(h + k, ll)
        return (kx, ky), (kx + fx, ky + fy)
    lknee, lfoot = leg(p["lh"], p["lk"])
    rknee, rfoot = leg(p["rh"], p["rk"])
    drop = max(lfoot[1], rfoot[1])
    hip = (x, ground - drop) if seat is None else (x, seat)

    ctx.save()
    ctx.translate(*hip)
    ctx.scale(dir, 1)
    ctx.push_group()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    lw = max(3.0, Hs * 0.014)

    def limb(pts, col, w):
        rgba(ctx, col); ctx.set_line_width(w)
        ctx.move_to(*pts[0])
        for q in pts[1:]:
            ctx.line_to(*q)
        ctx.stroke()

    # pants (colored) over thin legs, back leg first
    for knee, foot, back in ((rknee, rfoot, True), (lknee, lfoot, False)):
        limb([(0, 0), knee, foot], INK, lw * 2.9 + 3)
        limb([(0, 0), knee, foot], mix(PANTS, (0, 0, 0, 1), 0.25 if back else 0), lw * 2.9)
        # shoe
        rgba(ctx, INK)
        ctx.save(); ctx.translate(*foot)
        ctx.scale(1.7, 1); ctx.arc(0.012 * Hs, -0.004 * Hs, 0.022 * Hs, 0, TAU); ctx.restore(); ctx.fill()

    # torso frame
    ctx.save()
    ctx.rotate(p["lean"] + sh)
    neck = (0, -torso * br)
    tw = 0.085 * Hs
    # arms helpers
    def arm(s_ang, e_ang, side):
        sx, sy = side * tw * 0.8, -torso * 0.88 * br
        ex, ey = sx + math.sin(s_ang) * ua, sy + math.cos(s_ang) * ua
        hx, hy = ex + math.sin(s_ang + e_ang) * la, ey + math.cos(s_ang + e_ang) * la
        return (sx, sy), (ex, ey), (hx, hy)
    rsh, rel, rha = arm(p["rs"], p["re"], -1)
    lsh, lel, lha = arm(p["ls"], p["le"], 1)

    # back arm (right arm drawn behind body)
    rsl = (rsh[0] + (rel[0] - rsh[0]) * 0.45, rsh[1] + (rel[1] - rsh[1]) * 0.45)
    limb([rsh, rsl], INK, lw * 3.4 + 3)
    limb([rsh, rsl], SHIRT_DARK, lw * 3.4)
    limb([rsh, rel, rha], INK, lw)
    rgba(ctx, INK); ctx.arc(rha[0], rha[1], lw * 1.3, 0, TAU); ctx.fill()
    if flashlight:
        _flashlight(ctx, rha, p["rs"] + p["re"], t, Hs)

    # shirt (gray, slightly torn)
    ctx.move_to(-tw, -torso * 0.92 * br)
    ctx.curve_to(-tw * 0.4, -torso * 1.02 * br, tw * 0.4, -torso * 1.02 * br, tw, -torso * 0.92 * br)
    ctx.line_to(tw * 0.95, 0.02 * Hs)
    ctx.line_to(tw * 0.35, 0.02 * Hs)
    ctx.line_to(tw * 0.22, -0.02 * Hs)   # tear notch at hem
    ctx.line_to(tw * 0.08, 0.02 * Hs)
    ctx.line_to(-tw * 0.95, 0.02 * Hs)
    ctx.close_path()
    rgba(ctx, SHIRT); ctx.fill_preserve(); rgba(ctx, INK); ctx.set_line_width(lw * 0.9); ctx.stroke()

    # life vest (faded orange) with V opening and reflective strips
    vw = tw * 0.98
    ctx.move_to(-vw, -torso * 0.86 * br)
    ctx.line_to(-tw * 0.25, -torso * 0.92 * br)
    ctx.line_to(0, -torso * 0.55 * br)
    ctx.line_to(tw * 0.25, -torso * 0.92 * br)
    ctx.line_to(vw, -torso * 0.86 * br)
    ctx.line_to(vw * 1.02, -torso * 0.12)
    ctx.line_to(-vw * 1.02, -torso * 0.12)
    ctx.close_path()
    g = cairo.LinearGradient(-vw, 0, vw, 0)
    g.add_color_stop_rgba(0, *mix(VEST, (0.85, 0.8, 0.72, 1), 0.18))
    g.add_color_stop_rgba(1, *VEST_DARK)
    ctx.set_source(g); ctx.fill_preserve(); rgba(ctx, INK); ctx.set_line_width(lw * 0.9); ctx.stroke()
    rgba(ctx, (0.86, 0.87, 0.85, 0.9)); ctx.set_line_width(Hs * 0.012)
    for yy in (-torso * 0.42, -torso * 0.26):
        ctx.move_to(-vw * 0.9, yy); ctx.line_to(-vw * 0.12, yy); ctx.stroke()
        ctx.move_to(vw * 0.12, yy); ctx.line_to(vw * 0.9, yy); ctx.stroke()
    rgba(ctx, INK); ctx.set_line_width(lw * 0.6)
    ctx.move_to(0, -torso * 0.55 * br); ctx.line_to(0, -torso * 0.12); ctx.stroke()
    # faded patches
    rgba(ctx, (1, 0.95, 0.85, 0.18))
    ctx.arc(-vw * 0.45, -torso * 0.65, Hs * 0.018, 0, TAU); ctx.fill()
    ctx.arc(vw * 0.5, -torso * 0.2, Hs * 0.014, 0, TAU); ctx.fill()

    # coiled rope on left (front) shoulder, hanging diagonally
    rx, ry = tw * 0.55, -torso * 0.78 * br
    sway = 0.06 * math.sin(t * 1.7) + 0.04 * wind * noise1(t * 0.8, 9)
    ctx.save(); ctx.translate(rx, ry); ctx.rotate(0.35 + sway)
    for k in range(4):
        ctx.save(); ctx.translate(k * Hs * 0.006, k * Hs * 0.012)
        ctx.scale(1, 1.55)
        ctx.arc(0, Hs * 0.03, Hs * (0.055 - k * 0.004), 0, TAU)
        ctx.restore()
        rgba(ctx, ROPE_DARK); ctx.set_line_width(Hs * 0.017); ctx.stroke_preserve()
        rgba(ctx, ROPE); ctx.set_line_width(Hs * 0.011); ctx.stroke()
    # rope twist ticks
    rgba(ctx, ROPE_DARK); ctx.set_line_width(1.5)
    for k in range(10):
        an = k / 10 * TAU
        cx, cy = math.cos(an) * Hs * 0.055, Hs * 0.03 + math.sin(an) * Hs * 0.055 * 1.55
        ctx.move_to(cx - 3, cy - 3); ctx.line_to(cx + 3, cy + 3); ctx.stroke()
    ctx.restore()

    # sleeves (shirt) + front arm
    for shp, elb in ((lsh,lel),):
        pass
    sl = (lsh[0] + (lel[0] - lsh[0]) * 0.45, lsh[1] + (lel[1] - lsh[1]) * 0.45)
    limb([lsh, sl], INK, lw * 3.4 + 3)
    limb([lsh, sl], SHIRT, lw * 3.4)
    # torn sleeve edge
    rgba(ctx, SHIRT_DARK); ctx.set_line_width(2)
    ctx.move_to(sl[0] - lw, sl[1]); ctx.line_to(sl[0] + lw * 0.3, sl[1] + lw * 1.4); ctx.line_to(sl[0] + lw * 1.5, sl[1]); ctx.stroke()
    limb([lsh, lel, lha], INK, lw)
    rgba(ctx, INK); ctx.arc(lha[0], lha[1], lw * 1.3, 0, TAU); ctx.fill()

    # head
    ctx.save()
    ctx.translate(neck[0], neck[1])
    ctx.rotate(p["head"])
    limb([(0, 0), (0, -hr * 0.25)], INK, lw)
    hc = (0, -hr * 1.15)
    _hair(ctx, hc, hr, t, wind, back=True)
    rgba(ctx, SKIN_HEAD)
    ctx.arc(hc[0], hc[1], hr, 0, TAU)
    ctx.fill_preserve()
    rgba(ctx, INK); ctx.set_line_width(max(3, Hs * 0.01)); ctx.stroke()
    _face(ctx, hc, hr, t, expr, look, blink_seed, mouth)
    _hair(ctx, hc, hr, t, wind, back=False)
    ctx.restore()

    ctx.restore()  # torso frame
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    return hip

def _flashlight(ctx, hand, ang, t, Hs):
    hx, hy = hand
    dx, dy = math.sin(ang), math.cos(ang)
    L = Hs * 3.5
    g = cairo.RadialGradient(hx, hy, 0, hx, hy, L)
    fl = 0.85 + 0.15 * math.sin(t * 23) * math.sin(t * 7)
    g.add_color_stop_rgba(0, 1, 0.97, 0.8, 0.55 * fl)
    g.add_color_stop_rgba(1, 1, 0.97, 0.8, 0)
    ctx.set_source(g)
    nx, ny = -dy, dx
    ctx.move_to(hx, hy)
    ctx.line_to(hx + dx * L + nx * L * 0.28, hy + dy * L + ny * L * 0.28)
    ctx.line_to(hx + dx * L - nx * L * 0.28, hy + dy * L - ny * L * 0.28)
    ctx.close_path(); ctx.fill()
    rgba(ctx, hexc("#30343A")); ctx.set_line_width(Hs * 0.03)
    ctx.move_to(hx - dx * Hs * 0.02, hy - dy * Hs * 0.02); ctx.line_to(hx + dx * Hs * 0.05, hy + dy * Hs * 0.05); ctx.stroke()

def _hair(ctx, hc, hr, t, wind, back):
    cx, cy = hc
    rnd = random.Random(42)
    spikes = []
    n = 11
    for i in range(n):
        an = math.pi + (i / (n - 1)) * math.pi  # left to right over the top
        an += rnd.uniform(-0.06, 0.06)
        ln = hr * rnd.uniform(0.28, 0.5)
        w = 0.5 * noise1(t * 2.2 + i * 0.7, 3) * wind + 0.25 * wind
        spikes.append((an, ln, w))
    if back:
        # dark mass behind head top
        rgba(ctx, INK)
        ctx.save(); ctx.translate(cx, cy - hr * 0.12); ctx.scale(1.05, 0.95)
        ctx.arc(0, 0, hr * 1.02, math.pi * 0.95, math.pi * 2.05)
        ctx.restore(); ctx.close_path(); ctx.fill()
        return
    rgba(ctx, INK)
    # cap of hair over top of head
    ctx.move_to(cx + math.cos(math.pi * 1.02) * hr, cy + math.sin(math.pi * 1.02) * hr)
    for an, ln, w in spikes:
        bx, by = cx + math.cos(an) * hr * 0.98, cy + math.sin(an) * hr * 0.98
        tx = cx + math.cos(an + w * 0.35) * (hr + ln)
        ty = cy + math.sin(an + w * 0.35) * (hr + ln)
        ctx.line_to(bx, by)
        ctx.line_to(tx, ty)
    ctx.line_to(cx + math.cos(math.pi * 1.98) * hr, cy + math.sin(math.pi * 1.98) * hr)
    # fringe line across forehead (messy)
    for k in range(7, -1, -1):
        fx = cx + hr * (-0.95 + k * 0.27)
        fy = cy - hr * 0.42 + (hr * 0.13 if k % 2 else 0) + hr * 0.05 * math.sin(t * 2 + k)
        ctx.line_to(fx, fy)
    ctx.close_path()
    ctx.fill()

def _face(ctx, hc, hr, t, expr, look, blink_seed, mouth):
    cx, cy = hc
    fx = 0.22 * hr  # three-quarter offset toward facing direction
    lx, ly = look
    # blink
    bp = (t + blink_seed * 3.1) % 3.7
    blink = 1.0 - (1.0 if bp < 0.12 else 0.0) * 0.9
    wide = {"fear": 1.15, "shock": 1.35, "sad": 0.85, "calm": 0.95, "think": 0.9, "tense": 1.05}.get(expr, 1.0)
    pup = {"fear": 0.38, "shock": 0.3, "sad": 0.5, "calm": 0.55, "think": 0.5, "tense": 0.45}.get(expr, 0.5)
    for side in (-1, 1):
        ex = cx + fx + side * hr * 0.36
        ey = cy - hr * 0.02
        ew, eh = hr * 0.2, hr * 0.27 * wide * blink
        # under-eye shadows: old fear / sleeplessness
        rgba(ctx, (0.55, 0.55, 0.65, 0.45)); ctx.set_line_width(max(1.5, hr * 0.03))
        ctx.arc(ex, ey + hr * 0.08, ew * 1.05, 0.25 * math.pi, 0.75 * math.pi); ctx.stroke()
        ctx.save(); ctx.translate(ex, ey); ctx.scale(ew, max(eh, 0.01)); ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
        rgba(ctx, (1, 1, 1)); ctx.fill_preserve(); rgba(ctx, INK); ctx.set_line_width(max(2, hr * 0.045)); ctx.stroke()
        if blink > 0.5:
            px = ex + lx * ew * 0.45 + 0.012 * hr * math.sin(t * 9 + side)  # trembling gaze
            py = ey + ly * eh * 0.4
            rgba(ctx, INK); ctx.arc(px, py, ew * pup, 0, TAU); ctx.fill()
            rgba(ctx, (1, 1, 1)); ctx.arc(px - ew * pup * 0.35, py - ew * pup * 0.35, ew * pup * 0.3, 0, TAU); ctx.fill()
        # brows: raised and pinched (worry)
        rgba(ctx, INK); ctx.set_line_width(max(3, hr * 0.07))
        inner_up = {"fear": 0.16, "shock": 0.22, "sad": 0.18, "calm": 0.02, "think": -0.06, "tense": 0.08}.get(expr, 0.1)
        bx0 = ex - side * ew * 1.1
        bx1 = ex + side * ew * 1.1
        by_outer = ey - eh - hr * 0.12
        by_inner = by_outer - hr * inner_up
        if expr == "think" and side == 1:
            by_inner += hr * 0.08
        ctx.move_to(bx1, by_outer); ctx.line_to(bx0, by_inner); ctx.stroke()
    # mouth
    m = mouth or {"fear": "wobble", "shock": "o", "sad": "frown", "calm": "flat", "think": "side", "tense": "wobble"}.get(expr, "flat")
    mx, my = cx + fx, cy + hr * 0.5
    rgba(ctx, INK); ctx.set_line_width(max(3, hr * 0.06))
    if m == "o":
        ctx.save(); ctx.translate(mx, my); ctx.scale(hr * 0.12, hr * 0.17); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    elif m == "frown":
        ctx.arc(mx, my + hr * 0.18, hr * 0.2, 1.2 * math.pi, 1.8 * math.pi); ctx.stroke()
    elif m == "wobble":
        ctx.move_to(mx - hr * 0.2, my)
        for k in range(1, 9):
            ctx.line_to(mx - hr * 0.2 + k * hr * 0.05, my + hr * 0.035 * math.sin(k * 1.7 + t * 6))
        ctx.stroke()
    elif m == "side":
        ctx.move_to(mx - hr * 0.12, my + hr * 0.02); ctx.line_to(mx + hr * 0.16, my - hr * 0.04); ctx.stroke()
    elif m == "cough":
        ctx.save(); ctx.translate(mx, my); ctx.scale(hr * 0.16, hr * 0.1); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    else:
        ctx.move_to(mx - hr * 0.15, my); ctx.line_to(mx + hr * 0.15, my); ctx.stroke()
    # sweat drop when tense
    if expr in ("fear", "shock", "tense"):
        sp = (t * 0.5) % 1
        sx, sy = cx - hr * 0.75 + fx, cy - hr * 0.3 + sp * hr * 0.6
        rgba(ctx, (0.7, 0.85, 1.0, 0.85 * (1 - sp)))
        ctx.move_to(sx, sy - hr * 0.12)
        ctx.curve_to(sx + hr * 0.08, sy, sx + hr * 0.06, sy + hr * 0.08, sx, sy + hr * 0.08)
        ctx.curve_to(sx - hr * 0.06, sy + hr * 0.08, sx - hr * 0.08, sy, sx, sy - hr * 0.12)
        ctx.fill()

def walk_pose(t, speed=1.0, amp=0.45):
    ph = t * TAU * speed
    s = math.sin(ph)
    return dict(lh=amp * s, lk=-max(0, -s) * 0.8 * amp * 2, rh=-amp * s, rk=-max(0, s) * 0.8 * amp * 2,
                ls=-0.5 * s * amp, le=0.25, rs=0.5 * s * amp, re=-0.25, lean=0.05)

def walk_bob(t, speed=1.0, size=300):
    return -abs(math.sin(t * TAU * speed)) * size * 0.015
