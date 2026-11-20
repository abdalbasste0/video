"""Scene renderer that follows the layout grammar measured frame-by-frame from the
reference video (see docs/video-analysis.md):

  ┌──────────────────────────────────────────────┐
  │ [chapter pill]                  series tag ‾‾ │  top bar
  │          Serif title with a RED keyword       │  ~17% height
  │     tag boxes · big number · bars · stamp     │  build-up area
  │ 🧍 narrator                                    │
  ├──────────────────────────────────────────────┤  ground line at 80.5%
  │          [ karaoke caption box ]              │  sand band
  └──────────────────────────────────────────────┘

Every scene is rendered as a few *build states* (elements appear one after another,
like in the reference) instead of one static picture. All drawings are original.
"""
import random
import re
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from .media import FONTS, _RAQM, _shape, _text_kwargs, draw_block

C = {
    "paper": (234, 225, 212),
    "ground": (112, 106, 94),
    "band": (218, 204, 176),
    "ink": (38, 36, 34),
    "muted": (120, 114, 104),
    "red": (178, 52, 46),
    "green": (63, 127, 85),
    "blue": (52, 98, 160),
    "gold": (212, 167, 44),
    "navy": (21, 34, 63),
    "white": (255, 255, 255),
    "tag": (252, 250, 245),
    "skin": (196, 140, 98),
}
ACCENT = {"red": C["red"], "green": C["green"], "blue": C["blue"], "dark": C["navy"], "gold": C["gold"]}

GROUND = 0.805  # ground line, as a fraction of height


def _f(name, px):
    path = FONTS / name
    return ImageFont.truetype(str(path), max(8, int(px)),
                              layout_engine=ImageFont.Layout.RAQM if _RAQM else ImageFont.Layout.BASIC)


def serif(px):
    return _f("Amiri-Bold.ttf", px)


def sans(px, black=False):
    return _f("Cairo-Black.ttf" if black else "Cairo-Bold.ttf", px)


def tw(d, text, font):
    return d.textlength(_shape(text), font=font, **_text_kwargs())


def text_c(d, xy, text, font, fill):
    """Draw text centred on xy."""
    w = tw(d, text, font)
    asc, desc = font.getmetrics()
    d.text((xy[0] - w / 2, xy[1] - (asc + desc) / 2), _shape(text), font=font, fill=fill, **_text_kwargs())


# ------------------------------------------------------------------ background
@lru_cache(maxsize=4)
def paper(w, h):
    base = Image.new("RGB", (w, h), C["paper"])
    noise = Image.effect_noise((w // 3, h // 3), 22).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))
    tint = Image.merge("RGB", [noise.point(lambda v: min(255, int(252 + (v - 128) * 0.06)))] * 3)
    img = ImageChops.multiply(base, tint)
    vig = Image.radial_gradient("L").resize((w, h)).point(lambda v: int(max(0, v - 90) * 0.30))
    img = Image.composite(Image.new("RGB", (w, h), (196, 186, 170)), img, vig)
    return img


def base_frame(w, h, series, chapter_label, pill_color="red"):
    img = paper(w, h).copy()
    d = ImageDraw.Draw(img)
    gy = int(h * GROUND)
    d.rectangle((0, gy, w, h), fill=C["band"])
    d.line((0, gy, w, gy), fill=C["ground"], width=max(2, h // 300))
    k = h / 720
    # series tag (top-right) with gold underline
    if series:
        f = serif(30 * k)
        sw = tw(d, series, f)
        x1 = w - 40 * k
        d.text((x1 - sw, 14 * k), _shape(series), font=f, fill=C["ink"], **_text_kwargs())
        d.line((x1 - sw, 62 * k, x1, 62 * k), fill=C["gold"], width=max(2, int(3 * k)))
    # chapter pill (top-left)
    if chapter_label:
        f = sans(20 * k)
        pw = tw(d, chapter_label, f) + 44 * k
        box = (36 * k, 28 * k, 36 * k + pw, 70 * k)
        d.rounded_rectangle((box[0] + 2 * k, box[1] + 3 * k, box[2] + 2 * k, box[3] + 3 * k), radius=21 * k, fill=(150, 140, 126))
        d.rounded_rectangle(box, radius=21 * k, fill=ACCENT.get(pill_color, C["red"]))
        text_c(d, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2 - 2 * k), chapter_label, f, C["white"])
    return img


# ------------------------------------------------------------------ elements
def title(img, text, highlight):
    """Serif title at the top; the highlighted part is red (like «ضعف الوقت؟»)."""
    if not text:
        return
    w, h = img.size
    k = h / 720
    d = ImageDraw.Draw(img)
    size = 50 * k
    while True:
        f = serif(size)
        if tw(d, text, f) < w * 0.78 or size < 26 * k:
            break
        size -= 2 * k
    parts = [(text, C["ink"])]
    if highlight and highlight in text:
        a = text.index(highlight)
        parts = [(text[:a], C["ink"]), (highlight, C["red"]), (text[a + len(highlight):], C["ink"])]
    parts = [p for p in parts if p[0]]
    total = sum(tw(d, p, f) for p, _ in parts)
    x_right = w / 2 + total / 2
    y = 92 * k
    for seg, col in parts:  # RTL: first logical segment sits on the right
        sw = tw(d, seg, f)
        x_right -= sw
        d.text((x_right, y), _shape(seg), font=f, fill=col, **_text_kwargs())


def tag(img, text, cx, cy, size=22, border=C["ink"], color=C["ink"], fill=C["tag"]):
    w, h = img.size
    k = h / 720
    d = ImageDraw.Draw(img)
    f = sans(size * k)
    tw_ = tw(d, text, f)
    bw, bh = tw_ + 46 * k, 52 * k * size / 22
    x0, y0 = cx - bw / 2, cy - bh / 2
    d.rectangle((x0 + 4 * k, y0 + 5 * k, x0 + bw + 4 * k, y0 + bh + 5 * k), fill=(190, 180, 164))
    d.rectangle((x0, y0, x0 + bw, y0 + bh), fill=fill, outline=border, width=max(1, int(1.6 * k)))
    text_c(d, (cx, cy - 2 * k), text, f, color)
    return bw, bh


def date_tag(img, text):
    w, h = img.size
    k = h / 720
    d = ImageDraw.Draw(img)
    f = sans(19 * k)
    bw = tw(d, text, f) + 40 * k
    box = (w / 2 - bw / 2, 172 * k, w / 2 + bw / 2, 210 * k)
    d.rectangle(box, fill=C["navy"])
    text_c(d, (w / 2, (box[1] + box[3]) / 2 - 2 * k), text, f, C["white"])


def stamp(img, text, cx, cy, color=C["red"], angle=8):
    w, h = img.size
    k = h / 720
    f = sans(30 * k, black=True)
    tmp = Image.new("RGBA", (int(w * 0.6), int(h * 0.3)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    sw = tw(d, text, f) + 50 * k
    bx = ((tmp.width - sw) / 2, tmp.height / 2 - 40 * k, (tmp.width + sw) / 2, tmp.height / 2 + 40 * k)
    d.rectangle(bx, fill=(255, 255, 255, 170), outline=color + (255,), width=int(5 * k))
    d.rectangle((bx[0] + 8 * k, bx[1] + 8 * k, bx[2] - 8 * k, bx[3] - 8 * k), outline=color + (200,), width=max(1, int(2 * k)))
    text_c(d, (tmp.width / 2, tmp.height / 2 - 3 * k), text, f, color + (255,))
    tmp = tmp.rotate(angle, resample=Image.BICUBIC)
    img.paste(tmp, (int(cx - tmp.width / 2), int(cy - tmp.height / 2)), tmp)


def big_number(img, text, color=C["red"]):
    w, h = img.size
    k = h / 720
    d = ImageDraw.Draw(img)
    size = 150 * k
    while tw(d, text, serif(size)) > w * 0.5 and size > 50 * k:
        size -= 8 * k
    text_c(d, (w * 0.47, h * 0.47), text, serif(size), color)


def _num(v):
    m = re.search(r"[\d٠-٩]+(?:[.,][\d٠-٩]+)?", v or "")
    if not m:
        return None
    s = m.group().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")).replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def compare(img, left_label, left_value, right_label, right_value, step=2):
    """Two bars like the socket/power comparison. In RTL the first item sits on the right."""
    w, h = img.size
    k = h / 720
    d = ImageDraw.Draw(img)
    a, b = _num(right_value), _num(left_value)
    if a and b:
        top = max(a, b)
        ha, hb = a / top, b / top
    else:
        ha, hb = 0.55, 1.0
    base = h * 0.70
    maxh = h * 0.30
    d.line((w * 0.30, base, w * 0.70, base), fill=C["ink"], width=max(2, int(2 * k)))
    for cx, frac, label, value, col, shown in (
        (w * 0.60, ha, right_label, right_value, C["red"], step >= 1),
        (w * 0.40, hb, left_label, left_value, C["green"], step >= 2),
    ):
        if not shown:
            continue
        bh = max(12 * k, maxh * frac)
        d.rectangle((cx - 34 * k, base - bh, cx + 34 * k, base), fill=col, outline=C["ink"], width=max(1, int(1.5 * k)))
        if value:
            text_c(d, (cx, base + 22 * k), value, sans(17 * k), C["ink"])
        if label:
            tag(img, label, cx, base - bh - 46 * k, size=19)


def equation(img, text):
    """«القدرة = الفولت × التيار» with operands coloured ink/red/green."""
    w, h = img.size
    k = h / 720
    d = ImageDraw.Draw(img)
    f = serif(58 * k)
    tokens = re.split(r"(\s*[=×x\*\+\-÷/]\s*)", text)
    cols = [C["ink"], C["red"], C["green"], C["blue"]]
    parts, n = [], 0
    for t in tokens:
        if not t:
            continue
        if re.fullmatch(r"\s*[=×x\*\+\-÷/]\s*", t):
            parts.append((t, C["muted"]))
        else:
            parts.append((t, cols[n % len(cols)]))
            n += 1
    total = sum(tw(d, p, f) for p, _ in parts)
    x = w / 2 + total / 2
    for seg, col in parts:
        sw = tw(d, seg, f)
        x -= sw
        d.text((x, h * 0.40), _shape(seg), font=f, fill=col, **_text_kwargs())


def label_column(img, labels, upto, x_frac=0.80):
    w, h = img.size
    k = h / 720
    for i, lab in enumerate(labels[:upto]):
        tag(img, lab, w * x_frac, h * 0.36 + i * 64 * k, size=20)


def narrator(img, pose=0, x_frac=0.12):
    """Original simple mascot standing on the ground line (navy hoodie, orange scarf)."""
    w, h = img.size
    k = h / 720
    d = ImageDraw.Draw(img)
    gx, gy = w * x_frac, h * GROUND
    ink = C["ink"]
    lw = max(2, int(2.2 * k))
    # legs + shoes
    for dx in (-13, 13):
        d.rectangle((gx + dx * k - 9 * k, gy - 82 * k, gx + dx * k + 9 * k, gy - 8 * k), fill=(48, 52, 64), outline=ink, width=lw)
        d.rounded_rectangle((gx + dx * k - 13 * k, gy - 12 * k, gx + dx * k + 13 * k, gy), radius=5 * k, fill=(245, 245, 240), outline=ink, width=lw)
    # body (hoodie)
    d.rounded_rectangle((gx - 34 * k, gy - 178 * k, gx + 34 * k, gy - 76 * k), radius=16 * k, fill=(44, 72, 120), outline=ink, width=lw)
    d.line((gx, gy - 160 * k, gx, gy - 80 * k), fill=(30, 50, 90), width=lw)
    # arms
    if pose == 1:  # pointing to the content
        d.line((gx + 30 * k, gy - 165 * k, gx + 92 * k, gy - 190 * k), fill=ink, width=int(16 * k))
        d.line((gx + 30 * k, gy - 165 * k, gx + 90 * k, gy - 189 * k), fill=(44, 72, 120), width=int(12 * k))
        d.ellipse((gx + 86 * k, gy - 198 * k, gx + 102 * k, gy - 182 * k), fill=C["skin"], outline=ink, width=lw)
    else:
        d.line((gx + 33 * k, gy - 165 * k, gx + 40 * k, gy - 100 * k), fill=ink, width=int(16 * k))
        d.line((gx + 33 * k, gy - 165 * k, gx + 40 * k, gy - 101 * k), fill=(44, 72, 120), width=int(12 * k))
    d.line((gx - 33 * k, gy - 165 * k, gx - 40 * k, gy - 100 * k), fill=ink, width=int(16 * k))
    d.line((gx - 33 * k, gy - 165 * k, gx - 40 * k, gy - 101 * k), fill=(44, 72, 120), width=int(12 * k))
    # scarf + head + hair
    d.rounded_rectangle((gx - 26 * k, gy - 184 * k, gx + 26 * k, gy - 168 * k), radius=7 * k, fill=(222, 128, 52), outline=ink, width=lw)
    d.ellipse((gx - 30 * k, gy - 246 * k, gx + 30 * k, gy - 182 * k), fill=C["skin"], outline=ink, width=lw)
    d.chord((gx - 31 * k, gy - 250 * k, gx + 31 * k, gy - 200 * k), 180, 360, fill=(40, 32, 28), outline=ink, width=lw)
    for ex in (-11, 11):
        d.ellipse((gx + ex * k - 3 * k, gy - 216 * k, gx + ex * k + 3 * k, gy - 210 * k), fill=ink)
    d.arc((gx - 10 * k, gy - 208 * k, gx + 10 * k, gy - 194 * k), 20, 160, fill=ink, width=lw)


def cta(img, step):
    """End screen: subscribe / like / comment, like the reference's closing scene."""
    w, h = img.size
    k = h / 720
    d = ImageDraw.Draw(img)
    f = sans(22 * k)
    y = h * 0.42
    sub_col = C["red"] if step < 2 else (140, 136, 128)
    for cx, label, col in ((w * 0.57, "اشترك" if step < 2 else "مشترك", sub_col), (w * 0.43, "لايك", C["blue"] if step >= 1 else C["tag"])):
        box = (cx - 80 * k, y - 26 * k, cx + 80 * k, y + 26 * k)
        d.rounded_rectangle(box, radius=26 * k, fill=col, outline=C["ink"], width=max(1, int(1.5 * k)))
        text_c(d, (cx, y - 2 * k), label, f, C["white"] if col != C["tag"] else C["ink"])
    # bell
    bx, by = w * 0.66, y
    d.pieslice((bx - 18 * k, by - 22 * k, bx + 18 * k, by + 14 * k), 180, 360, fill=C["gold"], outline=C["ink"])
    d.rectangle((bx - 18 * k, by - 4 * k, bx + 18 * k, by + 10 * k), fill=C["gold"], outline=C["ink"])
    d.ellipse((bx - 5 * k, by + 10 * k, bx + 5 * k, by + 20 * k), fill=C["ink"])
    if step >= 1:
        box = (w * 0.33, y + 50 * k, w * 0.67, y + 100 * k)
        d.rounded_rectangle(box, radius=25 * k, fill=C["tag"], outline=C["ink"], width=max(1, int(1.5 * k)))
        text_c(d, (w / 2, y + 73 * k), "قولنا في الكومنتات …", sans(20 * k), C["green"])


# ------------------------------------------------------------------ composition
def build_states(scene, w, h, series, chapter_label, illustration=None):
    """Return a list of PIL images: the scene building up element by element."""
    blk = scene.get("block") or "none"
    accent = ACCENT.get(scene.get("accent"), C["red"])
    labels = [x for x in (scene.get("labels") or []) if x][:3]
    steps = []

    def frame(step, pose):
        img = base_frame(w, h, series, chapter_label, "red" if scene.get("chapter", 0) == 0 else "dark")
        title(img, scene.get("title", ""), scene.get("highlight", ""))
        if scene.get("date_tag") and step >= 1:
            date_tag(img, scene["date_tag"])
        if illustration is not None and blk == "none":
            ill = illustration.copy()
            ill.thumbnail((int(w * 0.46), int(h * 0.50)))
            m = Image.new("L", ill.size, 0)
            ImageDraw.Draw(m).rounded_rectangle((0, 0, *ill.size), radius=int(18 * h / 720), fill=255)
            img.paste(ill, (int(w / 2 - ill.width / 2), int(h * 0.27)), m)
        if blk == "big_number" and step >= 1:
            big_number(img, scene.get("main", ""), accent)
        elif blk == "compare":
            compare(img, scene.get("left_label", ""), scene.get("left_value", ""),
                    scene.get("right_label", ""), scene.get("right_value", ""), step)
        elif blk == "equation" and step >= 1:
            equation(img, scene.get("main", ""))
        elif blk == "cta":
            cta(img, step)
        if blk != "cta":
            if blk in ("big_number", "equation", "compare"):
                label_column(img, labels, max(0, step - 1))
            else:  # tags in a row, appearing one per step
                row_y = h * (0.70 if illustration is not None else 0.50)
                for i, lab in enumerate(labels[:step]):
                    tag(img, lab, w * (0.5 + (i - (len(labels) - 1) / 2) * 0.22), row_y)
            if scene.get("stamp") and step >= 3:
                stamp(img, scene["stamp"], w * 0.52, h * 0.62, accent)
        narrator(img, pose, 0.12 if blk != "cta" else 0.20)
        return img

    n = 4 if (scene.get("stamp") or len(labels) >= 2 or blk in ("compare", "cta")) else 3
    for s in range(n):
        steps.append(frame(s, 1 if s in (1, 2) else 0))
    return steps


def chapter_card(w, h, number, name):
    img = Image.new("RGB", (w, h), C["navy"])
    noise = Image.effect_noise((w // 4, h // 4), 18).resize((w, h), Image.BICUBIC).point(lambda v: int(v * 0.06))
    img = ImageChops.add(img, Image.merge("RGB", [noise] * 3))
    d = ImageDraw.Draw(img)
    k = h / 720
    text_c(d, (w / 2, h * 0.335), f"الفصل {number}", sans(26 * k), C["gold"])
    size = 64 * k
    while tw(d, name, serif(size)) > w * 0.8 and size > 30 * k:
        size -= 4 * k
    text_c(d, (w / 2, h * 0.47), name, serif(size), (240, 236, 228))
    d.line((w / 2 - 66 * k, h * 0.557, w / 2 + 66 * k, h * 0.557), fill=C["gold"], width=max(2, int(4 * k)))
    return img


def series_from(topic):
    """Short series tag for the corner, e.g. «لغز QWERTY»."""
    t = re.sub(r"[؟?!.]", "", topic or "").strip()
    return t if len(t) <= 18 else " ".join(t.split()[:3])
