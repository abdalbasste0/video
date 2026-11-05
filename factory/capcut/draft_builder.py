"""Compiles timeline.json → a CapCut Desktop draft folder.

    {drafts_dir}/{draft_name}/
        draft_content.json      tracks, segments, materials, keyframes
        draft_meta_info.json    what CapCut's home screen lists
        materials/              copies of every media file (self-contained draft)

Two modes
---------
* Template mode (recommended): `capcut.template_draft` points at a draft YOU made
  in your CapCut version. Its draft_content.json is the base document and the first
  item of every material list is used as a *prototype*: we deep-copy it and only
  override the fields we know. Unknown/new fields of your version are preserved, so
  the structure matches your CapCut exactly.
* Built-in mode: a skeleton matching the classic (unencrypted, ≤ 5.9-era) schema.

Units: CapCut stores time in microseconds (µs). Position x/y are in "half-canvas"
units (−1 … 1, +y = up). Scale 1.0 = fit.
"""
from __future__ import annotations

import copy
import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from .. import media

US = 1_000_000

MATERIAL_KEYS = [
    "audio_balances", "audio_effects", "audio_fades", "audio_track_indexes", "audios", "beats", "canvases",
    "chromas", "color_curves", "digital_humans", "drafts", "effects", "flowers", "green_screens", "handwrites",
    "hsl", "images", "log_color_wheels", "loudnesses", "manual_deformations", "masks", "material_animations",
    "material_colors", "multi_language_refs", "placeholders", "plugin_effects", "primary_color_wheels",
    "realtime_denoises", "shapes", "smart_crops", "smart_relights", "sound_channel_mappings", "speeds",
    "stickers", "tail_leaders", "text_templates", "texts", "time_marks", "transitions", "video_effects",
    "video_trackings", "videos", "vocal_beautifys", "vocal_separations",
]

# CapCut "Adjust" panel → effect material types (verify with `main.py learn-draft`; the
# learned names in effects_library.json["adjust"] take precedence).
DEFAULT_ADJUST_TYPES = {
    "brightness": "brightness", "contrast": "contrast", "saturation": "saturation",
    "temperature": "temperature", "tint": "tone", "highlights": "highlight", "shadows": "shadow",
}


def uid() -> str:
    return str(uuid.uuid4()).upper()


def us(sec: float) -> int:
    return int(round(sec * US))


def hex_rgb(h: str) -> list[float]:
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


class DraftBuilder:
    def __init__(self, settings, timeline: dict, draft_name: str, drafts_dir: Path,
                 template_dir: Path | None = None, portable: bool = False):
        self.s = settings
        self.tl = timeline
        self.name = draft_name
        self.dir = drafts_dir / draft_name
        self.lib = settings.effects
        self.portable = portable          # phone: relative paths, relinked on the PC later
        self.template = self._load_template(template_dir)
        self.protos: dict[str, dict] = {}
        self.skipped: list[str] = []

    # ------------------------------------------------------------------ template
    @staticmethod
    def _load_template(template_dir: Path | None) -> dict | None:
        if not template_dir:
            return None
        f = Path(template_dir) / "draft_content.json"
        if not f.exists():
            f = Path(template_dir) / "draft_info.json"
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Template draft at {template_dir} is unreadable or ENCRYPTED ({e}). "
                "See README → 'If your CapCut encrypts drafts'.") from e

    def _base_doc(self) -> dict:
        w, h = self.tl["width"], self.tl["height"]
        if self.template:
            doc = copy.deepcopy(self.template)
            for key, items in (doc.get("materials") or {}).items():
                if isinstance(items, list) and items and isinstance(items[0], dict):
                    # keep prototypes per (list, type)
                    for it in items:
                        self.protos.setdefault(f"{key}:{it.get('type', '')}", it)
                        self.protos.setdefault(key, it)
                    doc["materials"][key] = []
            for tr in doc.get("tracks", []):
                if tr.get("segments"):
                    self.protos.setdefault(f"segment:{tr.get('type')}", tr["segments"][0])
                    self.protos.setdefault("track", {k: v for k, v in tr.items() if k != "segments"})
            doc["tracks"] = []
        else:
            doc = {
                "canvas_config": {}, "color_space": 0,
                "config": {"adjust_max_index": 1, "attachment_info": [], "combination_max_index": 1,
                           "export_range": None, "extract_audio_last_index": 1, "lyrics_recognition_id": "",
                           "lyrics_sync": True, "lyrics_taskinfo": [], "maintrack_adsorb": True,
                           "material_save_mode": 0, "original_sound_last_index": 1, "record_audio_last_index": 1,
                           "sticker_max_index": 1, "subtitle_recognition_id": "", "subtitle_sync": True,
                           "subtitle_taskinfo": [], "system_font_list": [], "video_mute": False,
                           "zoom_info_params": None},
                "cover": None, "create_time": 0, "extra_info": None, "free_render_index_mode_on": False,
                "group_container": None, "keyframe_graph_list": [],
                "keyframes": {k: [] for k in ("adjusts", "audios", "effects", "filters", "handwrites",
                                              "stickers", "texts", "videos")},
                "last_modified_platform": {"app_id": 359289, "app_source": "cc", "app_version": "5.9.0",
                                           "os": "windows"},
                "materials": {k: [] for k in MATERIAL_KEYS},
                "mutable_config": None, "name": "", "new_version": "110.0.0",
                "platform": {"app_id": 359289, "app_source": "cc", "app_version": "5.9.0", "os": "windows"},
                "relationships": [], "render_index_track_mode_on": False, "retouch_cover": None,
                "source": "default", "static_cover_image_path": "", "time_marks": None, "tracks": [],
                "update_time": 0, "version": 360000,
            }
        doc["canvas_config"] = {**doc.get("canvas_config", {}), "width": w, "height": h, "ratio": "original"}
        doc["fps"] = float(self.tl["fps"])
        doc["duration"] = us(self.tl["duration"])
        doc["id"] = uid()
        doc["name"] = self.name
        for k in MATERIAL_KEYS:
            doc["materials"].setdefault(k, [])
        return doc

    def _mk(self, list_key: str, fields: dict, mtype: str = "") -> dict:
        """New material: template prototype (if any) overlaid with our fields."""
        proto = self.protos.get(f"{list_key}:{mtype}") or self.protos.get(list_key)
        item = copy.deepcopy(proto) if proto else {}
        item.update(fields)
        item["id"] = fields.get("id") or uid()
        return item

    # ------------------------------------------------------------------ media
    def _media_path(self, src: str) -> str:
        """Copy media into the draft's materials/ folder; return the path CapCut should read."""
        src_p = Path(src)
        dst = self.dir / "materials" / src_p.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.stat().st_size != src_p.stat().st_size:
            shutil.copy2(src_p, dst)
        if self.portable:
            return f"##DRAFT_DIR##/materials/{src_p.name}"   # relinked by `main.py install-draft`
        return str(dst.resolve()).replace("\\", "/")

    # ------------------------------------------------------------------ segments
    def _segment(self, material_id: str, start: float, dur: float, src_start: float = 0.0,
                 track_type: str = "video", render_index: int = 0, extra_refs: list[str] | None = None,
                 volume: float = 1.0, transform: tuple[float, float] = (0.0, 0.0), scale: float = 1.0) -> dict:
        proto = self.protos.get(f"segment:{track_type}")
        seg = copy.deepcopy(proto) if proto else {
            "cartoon": False, "enable_adjust": True, "enable_color_curves": True, "enable_color_wheels": True,
            "enable_lut": True, "enable_smart_color_adjust": False, "group_id": "",
            "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000}, "intensifies_audio": False,
            "is_placeholder": False, "is_tone_modify": False, "keyframe_refs": [], "last_nonzero_volume": 1.0,
            "reverse": False, "speed": 1.0, "template_id": "", "template_scene": "default",
            "uniform_scale": {"on": True, "value": 1.0}, "visible": True,
        }
        seg.update({
            "id": uid(), "material_id": material_id,
            "target_timerange": {"start": us(start), "duration": us(dur)},
            "source_timerange": None if track_type in ("text", "effect", "filter")
            else {"start": us(src_start), "duration": us(dur)},
            "render_index": render_index, "track_render_index": 0, "speed": 1.0, "volume": volume,
            "extra_material_refs": extra_refs or [], "common_keyframes": [],
            "clip": {"alpha": 1.0, "flip": {"horizontal": False, "vertical": False}, "rotation": 0.0,
                     "scale": {"x": scale, "y": scale}, "transform": {"x": transform[0], "y": transform[1]}},
        })
        if track_type == "audio":
            seg["clip"] = None
        return seg

    @staticmethod
    def _keyframes(prop: str, points: list[tuple[float, float]], seg_start: float) -> dict:
        return {
            "id": uid(), "material_id": "", "property_type": prop,
            "keyframe_list": [{
                "id": uid(), "curveType": "Line", "graphID": "",
                "left_control": {"x": 0.0, "y": 0.0}, "right_control": {"x": 0.0, "y": 0.0},
                "time_offset": max(0, us(t - seg_start)), "values": [float(v)],
            } for t, v in points],
        }

    def _support_refs(self, doc: dict) -> list[str]:
        m = doc["materials"]
        speed = self._mk("speeds", {"type": "speed", "mode": 0, "speed": 1.0, "curve_speed": None})
        canvas = self._mk("canvases", {"type": "canvas_color", "color": "", "blur": 0.0, "image": "",
                                       "album_image": "", "image_id": "", "image_name": "", "source_platform": 0,
                                       "team_id": ""})
        scm = self._mk("sound_channel_mappings", {"type": "", "audio_channel_mapping": 0, "is_config_open": False})
        m["speeds"].append(speed)
        m["canvases"].append(canvas)
        m["sound_channel_mappings"].append(scm)
        return [speed["id"], canvas["id"], scm["id"]]

    def _lib(self, section: str, key: str | None) -> dict | None:
        if not key:
            return None
        item = (self.lib.get(section) or {}).get(key)
        if not item or not item.get("resource_id"):
            self.skipped.append(f"{section}.{key}")
            return None
        return item

    def _track(self, ttype: str, segments: list[dict], name: str = "", flag: int = 0) -> dict:
        proto = self.protos.get("track", {})
        tr = {**copy.deepcopy(proto), "id": uid(), "type": ttype, "attribute": 0, "flag": flag,
              "is_default_name": not name, "name": name, "segments": segments}
        return tr

    # ------------------------------------------------------------------ build
    def build(self) -> Path:
        if self.dir.exists():
            shutil.rmtree(self.dir)
        (self.dir / "materials").mkdir(parents=True)
        doc = self._base_doc()
        m = doc["materials"]
        tracks: list[dict] = []
        adjust_types = {**DEFAULT_ADJUST_TYPES, **{k: v.get("type", k) for k, v in (self.lib.get("adjust") or {}).items()}}

        # ---- main video track
        main = []
        for c in self.tl["video"]:
            path = self._media_path(c["path"])
            info = media.video_info(Path(c["path"])) if c["kind"] == "video" else None
            w, h = (info["width"], info["height"]) if info else self._img_size(c["path"])
            src_dur = c.get("source_duration") or 10800.0  # photos: CapCut uses 3 h
            mat = self._mk("videos", {
                "type": "photo" if c["kind"] == "image" else "video", "path": path,
                "material_name": Path(c["path"]).name, "duration": us(src_dur), "width": w, "height": h,
                "category_name": "local", "has_audio": bool(info and info["has_audio"]),
                "crop": {"lower_left_x": 0.0, "lower_left_y": 1.0, "lower_right_x": 1.0, "lower_right_y": 1.0,
                         "upper_left_x": 0.0, "upper_left_y": 0.0, "upper_right_x": 1.0, "upper_right_y": 0.0},
                "crop_ratio": "free", "crop_scale": 1.0, "local_material_id": "",
            }, "photo" if c["kind"] == "image" else "video")
            m["videos"].append(mat)
            refs = self._support_refs(doc)

            tr_item = self._lib("transitions", c.get("transition_out"))
            if tr_item:
                tmat = self._mk("transitions", {
                    "type": "transition", "name": tr_item["name"], "effect_id": tr_item.get("effect_id") or tr_item["resource_id"],
                    "resource_id": tr_item["resource_id"], "duration": tr_item.get("duration_us", 400000),
                    "is_overlap": tr_item.get("is_overlap", True), "path": tr_item.get("path", ""),
                    "platform": "all", "category_id": "", "category_name": "", "request_id": "",
                })
                m["transitions"].append(tmat)
                refs.append(tmat["id"])

            for key, val in (c.get("adjust") or {}).items():
                if not val or key not in adjust_types:
                    continue
                amat = self._mk("effects", {"type": adjust_types[key], "value": round(val / 50.0, 4),
                                            "name": "", "path": "", "platform": "all", "apply_target_type": 0,
                                            "adjust_params": [], "category_id": "", "category_name": ""},
                                adjust_types[key])
                m["effects"].append(amat)
                refs.append(amat["id"])

            seg = self._segment(mat["id"], c["start"], c["duration"], c.get("source_start", 0.0),
                                "video", 0, refs, volume=0.0)   # B-roll muted, voice track carries speech
            kb = c.get("ken_burns")
            if kb:
                a, b = c["start"], c["start"] + c["duration"]
                seg["common_keyframes"] = [
                    self._keyframes("KFTypeScaleX", [(a, kb["scale"][0]), (b, kb["scale"][1])], a),
                    self._keyframes("KFTypeScaleY", [(a, kb["scale"][0]), (b, kb["scale"][1])], a),
                    self._keyframes("KFTypePositionX", [(a, kb["x"][0]), (b, kb["x"][1])], a),
                ]
                seg["clip"]["scale"] = {"x": kb["scale"][0], "y": kb["scale"][0]}
            main.append(seg)
        tracks.append(self._track("video", main))

        # ---- text tracks (captions / titles / lower thirds on separate tracks)
        by_kind: dict[str, list[dict]] = {}
        for t in self.tl.get("texts", []):
            by_kind.setdefault(t["kind"], []).append(self._text_segment(doc, t))
        for i, kind in enumerate(("caption", "lower_third", "title")):
            if by_kind.get(kind):
                for s in by_kind[kind]:
                    s["render_index"] = 14000 + i
                tracks.append(self._track("text", by_kind[kind], name=kind))

        # ---- filter (adjustment layer covering the whole timeline)
        f = self.tl.get("filter")
        fitem = self._lib("filters", f["key"]) if f else None
        if fitem:
            fmat = self._mk("effects", {"type": "filter", "name": fitem["name"],
                                        "effect_id": fitem.get("effect_id") or fitem["resource_id"],
                                        "resource_id": fitem["resource_id"], "value": f["intensity"],
                                        "path": fitem.get("path", ""), "platform": "all",
                                        "apply_target_type": 2, "adjust_params": [],
                                        "category_id": "", "category_name": ""}, "filter")
            m["effects"].append(fmat)
            tracks.append(self._track("filter", [self._segment(fmat["id"], 0, self.tl["duration"],
                                                               track_type="filter", render_index=11000)]))

        # ---- VFX effect tracks
        for i, e in enumerate(self.tl.get("effects", [])):
            item = self._lib("video_effects", e["key"])
            if not item:
                continue
            emat = self._mk("video_effects", {
                "type": "video_effect", "name": item["name"], "effect_id": item.get("effect_id") or item["resource_id"],
                "resource_id": item["resource_id"], "value": e.get("intensity", 1.0), "apply_target_type": 2,
                "adjust_params": [], "path": item.get("path", ""), "platform": "all",
                "category_id": "", "category_name": "", "render_index": 0, "track_render_index": 0,
                "common_keyframes": []})
            m["video_effects"].append(emat)
            tracks.append(self._track("effect", [self._segment(emat["id"], e["start"], e["duration"],
                                                               track_type="effect", render_index=11001 + i)]))

        # ---- audio tracks (voice, music, sfx)
        groups: dict[str, list[dict]] = {}
        for a in self.tl.get("audio", []):
            groups.setdefault(a["kind"], []).extend(self._audio_segments(doc, a))
        for kind in ("voice", "music", "sfx"):
            if groups.get(kind):
                tracks.append(self._track("audio", groups[kind], name=kind))

        doc["tracks"] = tracks
        content = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
        (self.dir / "draft_content.json").write_text(content, encoding="utf-8")
        if self.template is not None and (Path(self.s.get("capcut.template_draft")) / "draft_info.json").exists():
            (self.dir / "draft_info.json").write_text(content, encoding="utf-8")
        self._write_meta(doc)
        return self.dir

    # ------------------------------------------------------------------ text
    def _text_segment(self, doc: dict, t: dict) -> dict:
        st = t["style"]
        text = t["text"]
        size_pt = float(st.get("size", 64)) / 6.4          # px@1080w → CapCut size units
        base_color = hex_rgb(st.get("color", "#FFFFFF"))
        hi_color = hex_rgb(st.get("highlight_color", "#FFD400"))
        stroke = {"content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": hex_rgb(st.get("stroke_color", "#000000"))}},
                  "width": float(st.get("stroke_width", 4)) / 50}
        font = {"id": "", "path": st.get("font_file", "")}

        def style(rng: tuple[int, int], color: list[float]) -> dict:
            return {"fill": {"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": color}}},
                    "font": font, "range": list(rng), "size": size_pt, "bold": t["kind"] == "title",
                    "italic": False, "underline": False, "strokes": [stroke], "useLetterColor": True}

        styles = []
        if t.get("words"):
            pos = 0
            for w in t["words"]:
                i = text.find(w["text"], pos)
                if i < 0:
                    continue
                if i > pos:
                    styles.append(style((pos, i), base_color))
                styles.append(style((i, i + len(w["text"])), hi_color if w.get("highlight") else base_color))
                pos = i + len(w["text"])
            if pos < len(text):
                styles.append(style((pos, len(text)), base_color))
        else:
            styles.append(style((0, len(text)), base_color))

        bg = st.get("background", "#00000000").lstrip("#")
        bg_alpha = int(bg[6:8], 16) / 255 if len(bg) == 8 else 1.0
        mat = self._mk("texts", {
            "type": "text", "content": json.dumps({"styles": styles, "text": text}, ensure_ascii=False),
            "alignment": 1, "typesetting": 0, "letter_spacing": 0.0, "line_spacing": 0.02, "line_max_width": 0.82,
            "check_flag": 7, "global_alpha": 1.0, "background_color": f"#{bg[:6]}", "background_alpha": bg_alpha,
            "background_style": 1 if bg_alpha > 0 else 0, "background_round_radius": 0.3,
            "font_path": font["path"], "font_size": size_pt, "text_color": st.get("color", "#FFFFFF"),
            "border_color": st.get("stroke_color", "#000000"), "border_width": stroke["width"],
            "is_rich_text": False, "name": t["id"],
        }, "text")
        doc["materials"]["texts"].append(mat)

        refs = []
        anims = []
        for slot in ("anim_in", "anim_out", "anim_loop"):
            item = self._lib("text_animations", t.get(slot))
            if not item:
                continue
            d = item.get("duration_us", 300000)
            start = 0 if item["type"] != "out" else max(0, us(t["duration"]) - d)
            if item["type"] == "loop":
                d = us(t["duration"])
            anims.append({"anim_adjust_params": None, "platform": "all", "panel": "", "material_type": "sticker",
                          "name": item["name"], "id": item.get("effect_id") or item["resource_id"],
                          "type": item["type"], "resource_id": item["resource_id"], "start": start,
                          "duration": d, "path": item.get("path", ""), "request_id": "",
                          "category_id": "", "category_name": ""})
        if anims:
            amat = self._mk("material_animations", {"type": "sticker_animation", "multi_language_current": "none",
                                                    "animations": anims})
            doc["materials"]["material_animations"].append(amat)
            refs.append(amat["id"])

        y = 1.0 - 2.0 * float(t.get("y", 0.7))      # 0 top … 1 bottom → CapCut +1 top … −1 bottom
        seg = self._segment(mat["id"], t["start"], t["duration"], track_type="text", extra_refs=refs,
                            transform=(0.0, round(y, 4)))
        kf = []
        for prop, ptype in (("scale", ("KFTypeScaleX", "KFTypeScaleY")), ("x", ("KFTypePositionX",)),
                            ("alpha", ("KFTypeGlobalAlpha",))):
            pts = [(t["start"] + k["t"], k["v"]) for k in t.get("keyframes", []) if k["prop"] == prop]
            if len(pts) >= 2:
                kf += [self._keyframes(p, pts, t["start"]) for p in ptype]
        seg["common_keyframes"] = kf
        return seg

    # ------------------------------------------------------------------ audio
    def _audio_segments(self, doc: dict, a: dict) -> list[dict]:
        src_len = media.duration(Path(a["path"]))
        path = self._media_path(a["path"])
        mat = self._mk("audios", {
            "type": "extract_music" if a["kind"] == "voice" else ("music" if a["kind"] == "music" else "sound"),
            "name": Path(a["path"]).name, "path": path, "duration": us(src_len), "category_name": "local",
            "check_flag": 1, "music_id": "", "source_platform": 0, "wave_points": [], "local_material_id": "",
        }, "extract_music")
        doc["materials"]["audios"].append(mat)

        # loop the music bed if it is shorter than the video
        pieces, t = [], a["start"]
        end = a["start"] + a["duration"]
        while t < end - 0.01:
            d = min(src_len, end - t) if a.get("loop") else min(a["duration"], src_len)
            pieces.append((t, d))
            if not a.get("loop"):
                break
            t += d
        segs = []
        for n, (start, d) in enumerate(pieces):
            refs = self._support_refs(doc)
            fi = a.get("fade_in", 0) if n == 0 else 0
            fo = a.get("fade_out", 0) if n == len(pieces) - 1 else 0
            if fi or fo:
                fmat = self._mk("audio_fades", {"type": "audio_fade", "fade_in_duration": us(fi),
                                                "fade_out_duration": us(fo), "fade_type": 0})
                doc["materials"]["audio_fades"].append(fmat)
                refs.append(fmat["id"])
            seg = self._segment(mat["id"], start, d, a.get("source_start", 0.0), "audio", 0, refs,
                                volume=a.get("volume", 1.0))
            pts = [(k["t"], k["v"]) for k in a.get("volume_keyframes", []) if start <= k["t"] <= start + d]
            if len(pts) >= 2:
                seg["common_keyframes"] = [self._keyframes("KFTypeVolume", pts, start)]
            segs.append(seg)
        return segs

    # ------------------------------------------------------------------ meta
    @staticmethod
    def _img_size(path: str) -> tuple[int, int]:
        try:
            i = media.video_info(Path(path))
            return i["width"], i["height"]
        except Exception:
            return 1080, 1920

    def _write_meta(self, doc: dict) -> None:
        now_us = int(time.time() * US)
        root = str(self.dir.parent.resolve()).replace("\\", "/")
        files = []
        for v in doc["materials"]["videos"]:
            files.append({"create_time": int(time.time()), "duration": v["duration"], "extra_info": v["material_name"],
                          "file_Path": v["path"], "height": v["height"], "width": v["width"], "id": uid(),
                          "import_time": int(time.time()), "item_source": 1, "metetype": v["type"],
                          "type": 0, "md5": "", "roughcut_time_range": {"duration": -1, "start": -1}})
        for a in doc["materials"]["audios"]:
            files.append({"create_time": int(time.time()), "duration": a["duration"], "extra_info": a["name"],
                          "file_Path": a["path"], "id": uid(), "import_time": int(time.time()), "item_source": 1,
                          "metetype": "music", "type": 0, "md5": "",
                          "roughcut_time_range": {"duration": -1, "start": -1}})
        meta = {
            "draft_cloud_last_action_download": False, "draft_cloud_purchase_info": "",
            "draft_cloud_template_id": "", "draft_cloud_tutorial_info": "", "draft_cloud_videocut_purchase_info": "",
            "draft_cover": "draft_cover.jpg", "draft_deeplink_url": "", "draft_enterprise_info": {
                "draft_enterprise_extra": "", "draft_enterprise_id": "", "draft_enterprise_name": "",
                "enterprise_material": []},
            "draft_fold_path": "##DRAFT_DIR##" if self.portable else str(self.dir.resolve()).replace("\\", "/"),
            "draft_id": doc["id"], "draft_is_ai_shorts": False, "draft_is_article_video_draft": False,
            "draft_is_from_deeplink": "false", "draft_materials": [{"type": 0, "value": files}] +
            [{"type": t, "value": []} for t in (1, 2, 3, 6, 7, 8)],
            "draft_materials_copied_info": [], "draft_name": self.name, "draft_new_version": "",
            "draft_removable_storage_device": "", "draft_root_path": "##DRAFTS_ROOT##" if self.portable else root,
            "draft_segment_extra_info": [], "draft_timeline_materials_size_": 0, "draft_type": "",
            "tm_draft_cloud_completed": "", "tm_draft_cloud_modified": 0, "tm_draft_create": now_us,
            "tm_draft_modified": now_us, "tm_draft_removed": 0, "tm_duration": doc["duration"],
        }
        (self.dir / "draft_meta_info.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def install_portable_draft(src_dir: Path, drafts_dir: Path) -> Path:
    """PC side: copy a draft built on the phone into CapCut's drafts folder and relink paths."""
    dest = drafts_dir / src_dir.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src_dir, dest)
    d = str(dest.resolve()).replace("\\", "/")
    r = str(drafts_dir.resolve()).replace("\\", "/")
    for fn in ("draft_content.json", "draft_info.json", "draft_meta_info.json"):
        f = dest / fn
        if f.exists():
            txt = f.read_text(encoding="utf-8").replace("##DRAFT_DIR##", d).replace("##DRAFTS_ROOT##", r)
            f.write_text(txt, encoding="utf-8")
    return dest
