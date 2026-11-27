"""Render all 25 scenes to a 1080p silent video with 0.3s crossfades."""
import sys, subprocess, math
from multiprocessing import Pool
import cairo
sys.path.insert(0, '/home/user/video/src')
from gfx import W, H
from scenes import SCENES

FPS = 25
SCENE = 5.0
N = len(SCENES)
TOTAL = N * SCENE + 1.0
XF = 0.3
OUT = "/home/user/video/build"

def draw(i, t):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s)
    SCENES[i](c, t)
    return s

def frame(T):
    i = min(N - 1, int(T // SCENE))
    lt = T - i * SCENE
    if i < N - 1 and lt >= SCENE - XF / 2:
        a, b, k = (i, lt), (i + 1, lt - SCENE), (lt - (SCENE - XF / 2)) / XF
    elif i > 0 and lt < XF / 2:
        a, b, k = (i - 1, lt + SCENE), (i, lt), (lt + XF / 2) / XF
    else:
        a, b, k = (i, lt), None, 0
    s = draw(*a)
    c = cairo.Context(s)
    if b:
        s2 = draw(*b)
        c.set_source_surface(s2); c.paint_with_alpha(k)
    # fade in / out
    fade = min(1.0, T / 0.6, max(0.0, (TOTAL - T) / 1.6))
    if fade < 1:
        c.set_source_rgba(0, 0, 0, 1 - fade); c.paint()
    s.flush()
    return bytes(s.get_data())

def segment(args):
    idx, f0, f1 = args
    path = f"{OUT}/seg_{idx:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(frame(f / FPS))
    p.stdin.close(); p.wait()
    return path

if __name__ == "__main__":
    nf = int(round(TOTAL * FPS))
    chunks = 16
    step = math.ceil(nf / chunks)
    jobs = [(k, k * step, min(nf, (k + 1) * step)) for k in range(chunks)]
    with Pool(4) as pool:
        paths = pool.map(segment, jobs)
    with open(f"{OUT}/segs.txt", "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{OUT}/segs.txt",
                    "-c", "copy", f"{OUT}/video_silent.mp4"], check=True)
    print("done", nf)
