"""
Rig demo: a ~20 second test clip with two stickmen walking and talking.

    python make.py demo --lang ar
    python make.py demo --lang en
    python make.py demo            (renders every language listed in --langs default: ar en)

It exercises the whole chain end-to-end: language font + RTL text, TTS chain,
lip flap, walk cycles without foot sliding, 3 parallax layers, camera
pan/zoom/shake, flashlight in darkness, alarm light, music ducking, -14 LUFS,
.srt captions. The story text here is a tiny ORIGINAL test scene.
"""
from __future__ import annotations

import time
from pathlib import Path

from . import audio, captions, render, tts
from .config import OUTPUT, characters_cfg, language, settings, write_json

# Short original test lines, written separately for each language (not translated word-for-word).
LINES = {
    "ar": {
        "title": "اختبار الشخصيات", "subtitle": "استوديو ستيكمان للغموض",
        "n1": "في غابةٍ لا تظهر على أيّ خريطة... بدأ كلّ شيء بصوتٍ واحد.",
        "h1": "هل تسمع ذلك؟ إنه يأتي من بين الأشجار.",
        "a1": "إنه قادمٌ من المحطة القديمة... لا يجب أن نذهب.",
        "h2": "ابقَ خلفي، ولا تُطفئ الضوء مهما حدث.",
        "a2": "ما هذا الصوت؟!",
        "end": "يتبع...",
    },
    "en": {
        "title": "Rig Test", "subtitle": "Stickman Mystery Studio",
        "n1": "In a forest no map remembers... it all started with one sound.",
        "h1": "Do you hear that? It's coming through the trees.",
        "a1": "It's the old station... we really shouldn't go in there.",
        "h2": "Stay behind me. And whatever happens, keep the light on.",
        "a2": "What was that?!",
        "end": "To be continued...",
    },
    "fr": {
        "title": "Test des personnages", "subtitle": "Stickman Mystery Studio",
        "n1": "Dans une forêt qu'aucune carte ne connaît... tout a commencé par un bruit.",
        "h1": "Tu entends ça ? Ça vient d'entre les arbres.",
        "a1": "C'est la vieille station... on ne devrait pas y aller.",
        "h2": "Reste derrière moi. Et quoi qu'il arrive, garde la lumière allumée.",
        "a2": "C'était quoi, ça ?!",
        "end": "À suivre...",
    },
    "es": {
        "title": "Prueba de personajes", "subtitle": "Stickman Mystery Studio",
        "n1": "En un bosque que ningún mapa recuerda... todo empezó con un sonido.",
        "h1": "¿Oyes eso? Viene de entre los árboles.",
        "a1": "Es la vieja estación... no deberíamos entrar.",
        "h2": "Quédate detrás de mí. Y pase lo que pase, no apagues la luz.",
        "a2": "¿¡Qué fue eso!?",
        "end": "Continuará...",
    },
}


def build(lang_code: str, log=print) -> Path:
    t_start = time.time()
    lang = language(lang_code)
    L = LINES.get(lang_code)
    if not L:
        raise SystemExit(f"No demo lines for '{lang_code}'. Add them to LINES in studio/demo.py.")
    fps = settings()["video"]["fps"]
    out = OUTPUT / "_demo" / lang_code
    (out / "shots").mkdir(parents=True, exist_ok=True)
    rtl = lang["direction"] == "rtl"

    # 1) cast
    dc = characters_cfg()["demo_cast"]
    cast = {k: {"color": v["color"], "accessory": v["accessory"], "name": v["names"][lang_code]} for k, v in dc.items()}

    # 2) voices (+ mouth envelopes)
    log(f"[{lang_code}] 1/4 voices")
    plan = [("n1", "narrator", None), ("h1", "hero", "hero"), ("a1", "ally", "ally"), ("h2", "hero", "hero"), ("a2", "ally", "ally")]
    if "elevenlabs" in lang["tts"]["chain"] and tts.available("elevenlabs")[0]:
        tts.elevenlabs_budget_check([L[k] for k, _, _ in plan], log)
    V = {}
    for key, role, speaker in plan:
        wav, provider = tts.synthesize(L[key], lang_code, role, log)
        V[key] = {"wav": wav, "dur": audio.duration(wav), "env": audio.envelope(wav, fps), "speaker": speaker,
                  "provider": provider}
        log(f"    {key:3s} {role:9s} {V[key]['dur']:.1f}s via {provider}")

    def speech(key, t0):
        v = V[key]
        return [{"speaker": v["speaker"], "t0": t0, "env": v["env"]}] if v["speaker"] else []

    # 3) shots (durations fit the voice lines)
    sfx = audio.ensure_demo_sounds()
    hero_label = {"text": cast["hero"]["name"], "t0": 0.6, "t1": 3.6}
    ally_label = {"text": cast["ally"]["name"], "t0": 0.9, "t1": 3.9}
    d1 = max(4.0, V["n1"]["dur"] + 0.9)
    d2 = max(4.5, V["h1"]["dur"] + 1.6)
    d3 = max(3.5, V["a1"]["dur"] + 0.9)
    d4 = max(4.0, V["h2"]["dur"] + 1.0)
    d5 = max(3.2, V["a2"]["dur"] + 2.2)
    x_dir = -1 if rtl else 1         # RTL viewers read right->left: characters travel that way too
    def X(v):                         # mirror positions for RTL so the "forward" direction matches reading
        return 1 - v if rtl else v

    shots = [
        {"id": "S01", "duration": d1, "bg": {"preset": "forest", "mood": "night", "seed": 11},
         "camera": {"from": {"x": 0.5, "y": 0.42, "zoom": 1.25}, "to": {"x": 0.5, "y": 0.5, "zoom": 1.0}},
         "fade_in": 0.6,
         "text": [{"t0": 0.3, "t1": d1 - 0.2, "text": L["title"], "x": 0.5, "y": 0.36, "size": 120, "stroke": 6},
                  {"t0": 0.8, "t1": d1 - 0.2, "text": L["subtitle"], "x": 0.5, "y": 0.50, "size": 50, "stroke": 4,
                   "body": True, "color": [255, 214, 120]}],
         "fx": {"vignette": 0.55, "fog": 0.35}},
        {"id": "S02", "duration": d2, "bg": {"preset": "forest", "mood": "dusk", "seed": 3},
         "camera": {"from": {"x": X(0.38), "zoom": 1.05}, "to": {"x": X(0.55), "zoom": 1.15}},
         "actors": [
             {"char": "hero", "height": 0.30, "x": X(0.30), "label": hero_label, "depth": 1,
              "actions": [{"t0": 0, "t1": d2 - 1.6, "do": "walk", "to": X(0.58)},
                          {"t0": d2 - 1.6, "t1": d2, "do": "pose", "pose": "listen", "facing": x_dir}],
              "emotions": [{"t": 0, "e": "neutral"}, {"t": d2 - 1.8, "e": "surprised"}]},
             {"char": "ally", "height": 0.29, "x": X(0.22), "label": ally_label,
              "actions": [{"t0": 0, "t1": d2 - 1.4, "do": "walk", "to": X(0.47)},
                          {"t0": d2 - 1.4, "t1": d2, "do": "pose", "pose": "idle", "facing": x_dir}],
              "emotions": [{"t": 0, "e": "happy"}, {"t": d2 - 1.2, "e": "neutral"}]}],
         "speech": speech("h1", 0.8), "fx": {"vignette": 0.4}},
        {"id": "S03", "duration": d3, "bg": {"preset": "forest", "mood": "dusk", "seed": 3},
         "camera": {"from": {"x": X(0.52), "y": 0.56, "zoom": 1.45}, "to": {"x": X(0.53), "y": 0.56, "zoom": 1.55}},
         "actors": [
             {"char": "hero", "height": 0.30, "x": X(0.58), "facing": -x_dir, "depth": 1,
              "actions": [{"t0": 0, "t1": d3, "do": "pose", "pose": "arms_crossed"}],
              "emotions": [{"t": 0, "e": "neutral"}]},
             {"char": "ally", "height": 0.29, "x": X(0.47), "facing": x_dir,
              "actions": [{"t0": 0, "t1": d3, "do": "pose", "pose": "talk"}],
              "emotions": [{"t": 0, "e": "scared"}]}],
         "speech": speech("a1", 0.35), "fx": {"vignette": 0.45}},
        {"id": "S04", "duration": d4, "bg": {"preset": "corridor", "mood": "night", "seed": 5},
         "camera": {"from": {"x": X(0.40), "zoom": 1.1}, "to": {"x": X(0.52), "zoom": 1.2}},
         "actors": [
             {"char": "hero", "height": 0.30, "x": X(0.36), "prop": "flashlight", "depth": 1,
              "actions": [{"t0": 0, "t1": d4 - 0.8, "do": "sneak", "to": X(0.56)},
                          {"t0": d4 - 0.8, "t1": d4, "do": "pose", "pose": "flashlight", "facing": x_dir}],
              "emotions": [{"t": 0, "e": "angry"}]},
             {"char": "ally", "height": 0.29, "x": X(0.26),
              "actions": [{"t0": 0, "t1": d4 - 0.5, "do": "sneak", "to": X(0.45)},
                          {"t0": d4 - 0.5, "t1": d4, "do": "pose", "pose": "cower", "facing": x_dir}],
              "emotions": [{"t": 0, "e": "scared"}]}],
         "speech": speech("h2", 0.4), "fx": {"darkness": 0.88, "vignette": 0.5, "flicker": True}},
        {"id": "S05", "duration": d5, "bg": {"preset": "corridor", "mood": "night", "seed": 5},
         "camera": {"from": {"x": X(0.50), "zoom": 1.25}, "to": {"x": X(0.50), "zoom": 1.4},
                    "shake": [{"t": 0.15, "dur": 0.9, "amp": 22}]},
         "fade_out": 0.9,
         "actors": [
             {"char": "hero", "height": 0.30, "x": X(0.56), "facing": x_dir, "prop": "flashlight", "depth": 1,
              "actions": [{"t0": 0, "t1": 0.6, "do": "pose", "pose": "surprised"},
                          {"t0": 0.6, "t1": d5, "do": "pose", "pose": "brace"}],
              "emotions": [{"t": 0, "e": "surprised"}]},
             {"char": "ally", "height": 0.29, "x": X(0.45), "facing": x_dir,
              "actions": [{"t0": 0, "t1": 0.5, "do": "pose", "pose": "surprised"},
                          {"t0": 0.5, "t1": d5, "do": "pose", "pose": "scared"}],
              "emotions": [{"t": 0, "e": "scared"}]}],
         "speech": speech("a2", 0.3),
         "text": [{"t0": d5 - 1.5, "t1": d5, "text": L["end"], "x": 0.5, "y": 0.2, "size": 80, "stroke": 5}],
         "fx": {"darkness": 0.6, "alarm": True, "vignette": 0.5}},
    ]

    # 4) render video (parallel)
    log(f"[{lang_code}] 2/4 rendering {len(shots)} shots in parallel")
    paths = render.render_shots(shots, cast, lang, out / "shots", log)
    video = render.concat(paths, out / "video_only.mp4")

    # 5) sound: voices + ducked music + sfx -> -14 LUFS
    log(f"[{lang_code}] 3/4 mixing sound")
    starts, t = [], 0.0
    for s in shots:
        starts.append(t)
        t += round(s["duration"] * fps) / fps   # exact frame-rounded shot starts
    total = t
    offs = {"n1": (0, 0.5), "h1": (1, 0.8), "a1": (2, 0.35), "h2": (3, 0.4), "a2": (4, 0.3)}
    voices = [(V[k]["wav"], starts[i] + o) for k, (i, o) in offs.items()]
    steps = []
    for i, step_t in ((1, 0.0), (3, 0.0)):
        n_steps = int((shots[i]["duration"] - 1.4) / (0.5 if i == 1 else 0.8))
        steps += [(sfx["demo_footstep"], starts[i] + 0.25 + k * (0.5 if i == 1 else 0.8), -6 if i == 1 else -10)
                  for k in range(n_steps)]
    mix = audio.mix(total, voices,
                    music=[(sfx["demo_tension_drone"], 0, total)],
                    sfx=[(sfx["demo_impact"], starts[4], 2), (sfx["demo_alarm"], starts[4] + 0.2, -4)] + steps)
    raw = out / "mix.wav"
    audio.write_wav(raw, mix)
    final_audio = out / "final.wav"
    audio.loudnorm(raw, final_audio)
    lufs = audio.measure_lufs(final_audio)

    # 6) final mp4 + captions
    log(f"[{lang_code}] 4/4 final video + captions")
    final = render.mux(video, final_audio, OUTPUT / "_demo" / f"demo_{lang_code}.mp4")
    lines = [{"text": L[k], "start": starts[i] + o, "end": starts[i] + o + V[k]["dur"]} for k, (i, o) in offs.items()]
    captions.write_srt(lang_code, OUTPUT / "_demo" / f"demo_{lang_code}.srt", lines=lines, log=log)
    render.still(shots[1], cast, lang, shots[1]["duration"] * 0.4, OUTPUT / "_demo" / f"demo_{lang_code}_frame.png")
    write_json(out / "shots.json", shots)
    log(f"[{lang_code}] done: {final}  ({total:.1f}s, {lufs:.1f} LUFS, {time.time() - t_start:.0f}s to make)")
    return final
