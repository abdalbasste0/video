"""
Text drawing that works for Arabic (right-to-left) and Latin languages.

Why: Pillow draws characters one by one, left to right. Arabic letters must be
(1) joined into their connected shapes  -> arabic_reshaper
(2) put in visual right-to-left order   -> python-bidi
before drawing, otherwise you see separated, reversed letters.
"""
from __future__ import annotations

from functools import lru_cache

from PIL import ImageDraw, ImageFont

from .config import ROOT, StudioError


def shape(text: str, direction: str = "ltr") -> str:
    """Return text ready for Pillow. For RTL: reshape + bidi reorder."""
    if direction != "rtl":
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError as e:
        raise StudioError(
            "Arabic text needs two small packages. Run:  pip install arabic-reshaper python-bidi"
        ) from e
    return get_display(arabic_reshaper.reshape(text))


def is_shaped_arabic(text: str) -> bool:
    """True if text contains Arabic 'presentation forms' (proof that reshaping happened)."""
    return any(0xFE70 <= ord(c) <= 0xFEFF or 0xFB50 <= ord(c) <= 0xFDFF for c in text)


@lru_cache(64)
def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    p = ROOT / path
    if not p.exists():
        raise StudioError(f"Font not found: {path}. Check config/languages.yaml or run `python make.py doctor`.")
    # BASIC layout = draw characters exactly in the order we give them.
    # (Some Pillow builds have their own RTL engine "raqm" which would reverse
    #  our already-reordered Arabic a second time. BASIC behaves the same on every PC.)
    return ImageFont.truetype(str(p), size, layout_engine=ImageFont.Layout.BASIC)


def wrap(text: str, max_chars: int) -> list[str]:
    """Simple word wrap on logical (unshaped) text."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def draw_text(img, xy, text, lang: dict, size: int, fill=(255, 255, 255), anchor="mm",
              stroke=0, stroke_fill=(0, 0, 0), body=False, max_chars=None, line_gap=1.15):
    """
    Draw (possibly multi-line) text at xy.
    anchor: "mm" centre, "rm" right-middle, "lm" left-middle (Pillow anchors).
    For RTL languages, use align right automatically when anchor is left/right based.
    """
    direction = lang.get("direction", "ltr")
    f = font(lang["font_body"] if body else lang["font"], size)
    lines = wrap(text, max_chars) if max_chars else [text]
    d = ImageDraw.Draw(img)
    x, y = xy
    total = len(lines) * size * line_gap
    y0 = y - total / 2 + size * line_gap / 2
    for i, line in enumerate(lines):
        d.text((x, y0 + i * size * line_gap), shape(line, direction), font=f, fill=fill,
               anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)
    return img


def missing_glyphs(font_path: str, text: str) -> list[str]:
    """Characters in `text` the font cannot draw (they would show as empty boxes)."""
    f = font(font_path, 40)
    notdef = f.getmask("￿").getbbox()
    return sorted({c for c in text if not c.isspace() and f.getmask(c).getbbox() == notdef})
