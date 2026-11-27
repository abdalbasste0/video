import sys, cairo
from PIL import Image
sys.path.insert(0, '.')
from gfx import W, H
from scenes import SCENES
t = float(sys.argv[1]) if len(sys.argv) > 1 else 2.8
idx = [int(a) for a in sys.argv[2].split(',')] if len(sys.argv) > 2 else range(len(SCENES))
tiles = []
for i in idx:
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    SCENES[i](c, t)
    im = Image.frombuffer("RGBA", (W, H), bytes(s.get_data()), "raw", "BGRA", 0, 1).convert("RGB")
    tiles.append(im.resize((640, 360)))
cols = 5 if len(tiles) > 4 else len(tiles)
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 640, rows * 360))
for k, im in enumerate(tiles):
    sheet.paste(im, ((k % cols) * 640, (k // cols) * 360))
sheet.save(sys.argv[3] if len(sys.argv) > 3 else '/tmp/claude-0/-home-user-video/b85fdd38-99d3-5374-a8d9-2e27d13c008c/scratchpad/sheet.png')
