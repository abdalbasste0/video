"""Render Agent — final export (H.264/H.265, 1080p, 30 fps) + light preview + thumbnail.

Backends (config: render.backend)
  capcut_ui : Windows only. Opens CapCut, opens the draft, clicks Export (pywinauto/pyautogui).
  manual    : you press Export in CapCut; the factory waits for the file in renders/ or the CapCut export dir.
  ffmpeg    : renders the same timeline with FFmpeg (default on the phone).
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path

from .. import media
from .base import BaseAgent

XFADE = {"fade": "fade", "zoom": "zoomin", "slide": "slideleft", "whip": "wipeleft"}
TRANS_DUR = 0.35


def ass_color(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    a = 255 - int(h[6:8], 16) if len(h) == 8 else 0
    return f"&H{a:02X}{b}{g}{r}".upper()


def ass_time(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


class RenderAgent(BaseAgent):
    name = "render"

    def run(self) -> dict:
        backend = self.ctx.extra.get("render_backend") or self.s.render_backend
        if backend == "capcut_ui":
            self._capcut_ui()
        elif backend == "manual":
            self._manual()
        else:
            self._ffmpeg()
        out = self._finish()
        self.info(f"render ({backend}) → {out['final']} {out['info']}")
        return out

    # ================================================================ FFmpeg
    def _ffmpeg(self) -> None:
        tl = self.p.read_json("draft", "timeline.json")
        W, H, fps = tl["width"], tl["height"], tl["fps"]
        work = self.p.dir("renders") / "_work"
        work.mkdir(exist_ok=True)
        lib = self.s.effects

        # 1) every clip → normalized intermediate (size, fps, Ken Burns, Adjust)
        parts = []
        clips = tl["video"]
        for i, c in enumerate(clips):
            extra = TRANS_DUR if c.get("transition_out") and i + 1 < len(clips) else 0.0
            d = c["duration"] + extra
            out = work / f"{i:03d}_{c['id']}.mp4"
            self._render_clip(c, d, W, H, fps, out)
            parts.append((out, c, d))

        # 2) join with xfade transitions, apply look + vfx + captions
        inputs, chain = [], []
        for out, _, _ in parts:
            inputs += ["-i", str(out)]
        label = "[0:v]"
        for i in range(1, len(parts)):
            prev = parts[i - 1][1]
            nxt = f"[x{i}]"
            if prev.get("transition_out"):
                kind = XFADE.get(prev["transition_out"], "fade")
                chain.append(f"{label}[{i}:v]xfade=transition={kind}:duration={TRANS_DUR}:offset={parts[i][1]['start']:.3f}{nxt}")
            else:
                # hard cut: concat keeps exact timing because clip i ends at clip i+1 start
                chain.append(f"{label}[{i}:v]concat=n=2:v=1:a=0{nxt}")
            label = nxt
        post = []
        f = tl.get("filter") or {}
        if f.get("lut") and Path(f["lut"]).exists():
            post.append(f"lut3d='{self._esc(f['lut'])}'")
        look = (lib.get("filters", {}).get(f.get("key") or "", {}) or {}).get("ffmpeg")
        if look:
            post.append(look)
        for e in tl.get("effects", []):
            fx = (lib.get("video_effects", {}).get(e["key"], {}) or {}).get("ffmpeg")
            if fx and e["duration"] >= tl["duration"] - 0.05:
                post.append(fx)
        ass = self._write_ass(tl, work / "captions.ass")
        fonts = self.s.root / "library" / "fonts"
        post.append(f"subtitles='{self._esc(str(ass))}':fontsdir='{self._esc(str(fonts))}'")
        post.append(f"trim=duration={tl['duration']:.3f},format=yuv420p")
        chain.append(f"{label}{','.join(post)}[vout]")

        # 3) audio mix: voice + ducked music + sfx → loudness-normalised master
        a_inputs, a_chain, mix = [], [], []
        base = len(parts)
        for j, a in enumerate(tl["audio"]):
            idx = base + j
            if a.get("loop"):
                a_inputs += ["-stream_loop", "-1"]
            a_inputs += ["-i", a["path"]]
            fl = [f"atrim=start={a.get('source_start', 0):.3f}:duration={a['duration']:.3f}", "asetpts=PTS-STARTPTS",
                  "aresample=48000", "aformat=channel_layouts=stereo", f"volume={a.get('volume', 1.0)}"]
            if a.get("volume_keyframes"):
                fl.append(f"volume='{self._kf_expr(a['volume_keyframes'], a['start'])}':eval=frame")
            if a.get("fade_in"):
                fl.append(f"afade=t=in:d={a['fade_in']}")
            if a.get("fade_out"):
                fl.append(f"afade=t=out:st={max(0, a['duration'] - a['fade_out']):.3f}:d={a['fade_out']}")
            if a["start"] > 0:
                ms = int(a["start"] * 1000)
                fl.append(f"adelay={ms}|{ms}")
            a_chain.append(f"[{idx}:a]{','.join(fl)}[a{j}]")
            mix.append(f"[a{j}]")
        lufs = tl.get("target_lufs", -14)
        a_chain.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=longest,"
                       f"atrim=duration={tl['duration']:.3f},loudnorm=I={lufs}:TP=-1.5:LRA=11,aresample=48000[aout]")

        graph = ";".join(chain + a_chain)
        (work / "filter_graph.txt").write_text(graph, encoding="utf-8")
        codec = self.s.get("render.codec", "libx264")
        media.ffmpeg(*inputs, *a_inputs, "-filter_complex", graph, "-map", "[vout]", "-map", "[aout]",
                     "-r", str(fps), "-c:v", codec, "-preset", "medium", "-crf", str(self.s.get("render.crf", 20)),
                     "-pix_fmt", "yuv420p", *(["-tag:v", "hvc1"] if codec == "libx265" else []),
                     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(self.p.final_file))
        shutil.rmtree(work, ignore_errors=True) if not self.s.get("render.keep_work", False) else None

    def _render_clip(self, c: dict, d: float, W: int, H: int, fps: int, out: Path) -> None:
        frames = max(1, int(round(d * fps)))
        adj = c.get("adjust") or {}
        eq = (f"eq=brightness={adj.get('brightness', 0) / 250:.3f}:contrast={1 + adj.get('contrast', 0) / 150:.3f}"
              f":saturation={1 + adj.get('saturation', 0) / 100:.3f}")
        temp = adj.get("temperature", 0)
        cb = f",colorbalance=rm={temp / 400:.3f}:bm={-temp / 400:.3f}" if temp else ""
        cover = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
        kb = c.get("ken_burns")
        if c["kind"] == "image":
            src = ["-loop", "1", "-framerate", str(fps), "-t", f"{d:.3f}", "-i", c["path"]]
        else:
            src = ["-stream_loop", "-1", "-ss", f"{c.get('source_start', 0):.3f}", "-t", f"{d:.3f}", "-i", c["path"]]
        if kb:
            s0, s1 = kb["scale"]
            x0, x1 = kb["x"]
            sw, sh = int(W * 1.5) // 2 * 2, int(H * 1.5) // 2 * 2
            z = f"({s0}+({s1}-{s0})*on/{frames})"
            px = f"(iw-iw/zoom)/2+({x0}+({x1}-{x0})*on/{frames})*iw/4"
            vf = (f"scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},"
                  f"zoompan=z='{z}':x='{px}':y='(ih-ih/zoom)/2':d=1:s={W}x{H}:fps={fps}")
            if c["kind"] == "image":
                src = ["-framerate", str(fps), "-loop", "1", "-t", f"{d:.3f}", "-i", c["path"]]
        else:
            vf = cover + f",fps={fps}"
        vf += f",{eq}{cb},setsar=1,format=yuv420p"
        media.ffmpeg(*src, "-vf", vf, "-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "veryfast",
                     "-crf", "16", "-r", str(fps), str(out))

    @staticmethod
    def _esc(p: str) -> str:
        return p.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")

    @staticmethod
    def _kf_expr(kfs: list[dict], offset: float) -> str:
        """Piecewise-linear gain from keyframes (t relative to the delayed segment start)."""
        terms = []
        pts = [(k["t"] - offset, k["v"]) for k in kfs]
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            if t1 <= t0:
                continue
            terms.append(f"gte(t,{t0:.3f})*lt(t,{t1:.3f})*({v0}+({v1 - v0:.5f})*(t-{t0:.3f})/{t1 - t0:.3f})")
        terms.append(f"gte(t,{pts[-1][0]:.3f})*{pts[-1][1]}")
        return "+".join(terms)  # quoted in the graph, so commas need no escaping

    def _write_ass(self, tl: dict, out: Path) -> Path:
        W, H = tl["width"], tl["height"]
        cap = self.s.get("captions", {})
        font = cap.get("font_name", "Arial")
        lines = [
            "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0", "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
            "MarginL, MarginR, MarginV, Encoding",
        ]
        styles = {}
        for t in tl.get("texts", []):
            st = t["style"]
            key = (t["kind"], st.get("size"), st.get("color"), st.get("background"))
            if key in styles:
                continue
            name = f"S{len(styles)}"
            styles[key] = name
            boxed = len(st.get("background", "")) == 9 and not st.get("background", "").endswith("00")
            lines.append(
                f"Style: {name},{font},{st.get('size', 64)},{ass_color(st.get('color', '#FFFFFF'))},&H000000FF,"
                f"{ass_color(st.get('background', '#00000080') if boxed else st.get('stroke_color', '#000000'))},"
                f"&H64000000,{-1 if t['kind'] == 'title' else 0},0,0,0,100,100,0,0,{3 if boxed else 1},"
                f"{12 if boxed else st.get('stroke_width', 4)},0,5,60,60,0,1")
        lines += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
        for t in tl.get("texts", []):
            st = t["style"]
            name = styles[(t["kind"], st.get("size"), st.get("color"), st.get("background"))]
            x, y = W // 2, int(H * float(t.get("y", 0.7)))
            pos = f"\\an5\\pos({x},{y})"
            if t["kind"] == "lower_third":
                pos = f"\\an5\\move({x + (40 if t.get('rtl') else -40)},{y},{x},{y},0,350)"
            fad = "\\fad(150,200)" if t.get("anim_out") else "\\fad(120,0)"
            pop = "\\fscx92\\fscy92\\t(0,250,\\fscx100\\fscy100)" if t.get("anim_in") == "in_pop" else ""
            if t.get("words"):
                hi = ass_color(st.get("highlight_color", "#FFD400"))
                base = ass_color(st.get("color", "#FFFFFF"))
                # karaoke-style: the spoken word lights up, keywords stay highlighted
                for k, w in enumerate(t["words"]):
                    a = w["start"] if k else t["start"]
                    b = t["words"][k + 1]["start"] if k + 1 < len(t["words"]) else t["start"] + t["duration"]
                    parts = []
                    for m, ww in enumerate(t["words"]):
                        col = hi if (m == k or ww.get("highlight")) else base
                        scale = "\\fscx108\\fscy108" if m == k else "\\fscx100\\fscy100"
                        parts.append(f"{{\\c{col}{scale}}}{ww['text']}")
                    lines.append(f"Dialogue: 1,{ass_time(a)},{ass_time(b)},{name},,0,0,0,,{{{pos}}}" + " ".join(parts))
            else:
                text = t["text"].replace("\n", "\\N")
                lines.append(f"Dialogue: 2,{ass_time(t['start'])},{ass_time(t['start'] + t['duration'])},{name},,0,0,0,,"
                             f"{{{pos}{fad}{pop}}}{text}")
        out.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
        return out

    # ================================================================ CapCut
    def _capcut_ui(self) -> None:
        """Windows UI automation. Coordinates differ between CapCut versions; the
        image-based steps use screenshots you place in windows/ui/*.png (README §Export)."""
        import pyautogui  # noqa: F401  (Windows only)
        from pywinauto import Application

        exe = self.s.get("render.capcut_exe", r"%LOCALAPPDATA%\CapCut\Apps\CapCut.exe")
        from ..config import expand
        app = Application(backend="uia").start(str(expand(exe)))
        time.sleep(12)
        win = app.top_window()
        win.set_focus()
        draft = self.ctx.video["meta"].get("draft_name")
        ui = self.s.root / "windows" / "ui"

        def click(img: str, timeout: int = 60) -> None:
            t0 = time.time()
            while time.time() - t0 < timeout:
                try:
                    pt = pyautogui.locateCenterOnScreen(str(ui / img), confidence=0.85)
                except Exception:
                    pt = None
                if pt:
                    pyautogui.click(pt)
                    return
                time.sleep(1)
            raise TimeoutError(f"CapCut UI element '{img}' not found — re-capture windows/ui/{img}")

        win.child_window(title=draft, control_type="Text").click_input()  # open the draft card
        time.sleep(8)
        click("export_button.png")
        time.sleep(2)
        click("export_confirm.png")
        self._wait_for_export(draft, timeout_min=60)

    def _manual(self) -> None:
        draft = self.ctx.video["meta"].get("draft_name")
        self.info(f"MANUAL EXPORT: open draft '{draft}' in CapCut → Export (1080p/30fps). Waiting for the file…")
        self._wait_for_export(draft, timeout_min=float(self.s.get("render.manual_wait_timeout_min", 0)))

    def _wait_for_export(self, draft: str, timeout_min: float) -> None:
        from ..config import expand
        dirs = [self.p.dir("renders"), expand(self.s.get("render.capcut_export_dir", ""))]
        t0 = time.time()
        while True:
            for d in dirs:
                if not d or not Path(d).exists():
                    continue
                cands = [p for p in Path(d).glob("*.mp4") if p.stem.startswith(draft) or p.name == "export.mp4"]
                for c in cands:
                    s1 = c.stat().st_size
                    time.sleep(3)
                    if s1 > 0 and c.stat().st_size == s1:     # finished writing
                        if c != self.p.final_file:
                            shutil.copy2(c, self.p.final_file)
                        return
            if timeout_min and time.time() - t0 > timeout_min * 60:
                raise TimeoutError("manual export not found in time")
            time.sleep(10)

    # ================================================================ outputs
    def _finish(self) -> dict:
        final = self.p.final_file
        info = media.video_info(final)
        ph = int(self.s.get("render.preview_height", 640)) // 2 * 2
        media.ffmpeg("-i", str(final), "-vf", f"scale=-2:{ph}", "-c:v", "libx264", "-preset", "veryfast",
                     "-crf", "30", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(self.p.preview_file))
        t = min(1.5, info["duration"] / 3)
        media.ffmpeg("-ss", f"{t:.2f}", "-i", str(final), "-frames:v", "1", "-q:v", "3", str(self.p.thumb_file))
        return {"final": str(final), "preview": str(self.p.preview_file), "thumbnail": str(self.p.thumb_file),
                "info": info, "sha256": media.sha256(final)}
