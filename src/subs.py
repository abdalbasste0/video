import json, sys
sys.path.insert(0, '/home/user/video/src')
from beats import BEATS
tim = json.load(open('/home/user/video/build/timings.json'))
def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Inter ExtraBold,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4.5,1.5,2,160,160,64,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
lines = []
srt = []
for k, (text, (a, b)) in enumerate(zip(BEATS, tim)):
    a = max(0, a - 0.05); b = min(b + 0.35, (k + 1) * 5.0 - 0.05)
    lines.append(f"Dialogue: 0,{ts(a)},{ts(b)},Default,,0,0,0,,{text}")
    f = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(round((x%1)*1000)) % 1000:03d}"
    srt.append(f"{k+1}\n{f(a)} --> {f(b)}\n{text}\n")
open('/home/user/video/build/subs.ass', 'w').write(hdr + "\n".join(lines) + "\n")
open('/home/user/video/out/subtitles_en.srt', 'w').write("\n".join(srt))
print("ok")
