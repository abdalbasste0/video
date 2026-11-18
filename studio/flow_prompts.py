"""Write a Google Flow worksheet for an episode: one image prompt + one animation prompt per shot.

usage: python -m studio.flow_prompts series/mary-celeste/ep01.json
Writes series/<name>/flow-epNN.md and character reference images series/<name>/refs/*.png
Save each Flow clip as clips/<name>-epNN/shotNN.mp4 (a still image shotNN.png also works).
"""
import json
import os
import sys

import skia

from . import character as ch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def char_refs(cast, folder):
    os.makedirs(folder, exist_ok=True)
    for name, info in cast.items():
        path = os.path.join(folder, f"{name}.png")
        s = skia.Surface(1200, 1200)
        c = s.getCanvas()
        c.clear(0xFFF4F1EA)
        ch.set_look(info["look"])
        sc = info.get("ref_scale", 1.6)
        y = 1120 - (ch.THIGH + ch.SHIN + 14) * sc
        ch.draw(c, ch.ACTIONS["stand"](0.0), 600, y, scale=sc, expr=info.get("expr", "neutral"), t=1.0)
        s.makeImageSnapshot().save(path)


def main(story_path):
    story = json.load(open(story_path))
    sdir = os.path.dirname(os.path.abspath(story_path))
    style = json.load(open(os.path.join(sdir, "flow_style.json")))
    ep = os.path.splitext(os.path.basename(story_path))[0]
    slug = f"{os.path.basename(sdir)}-{ep}"
    char_refs(style["cast"], os.path.join(sdir, "refs"))
    se = story.get("series", {})
    out = [f"# Google Flow: {se.get('name', story['title'])}, part {se.get('part', '')}",
           "",
           "## Settings (the same for every scene)",
           "- **Image:** model Nano Banana, 16:9 ratio, one result.",
           "- **Video:** add the scene image, model Omni Flash (or Veo Fast), 720p, 8 seconds, 16:9.",
           "- **Character consistency:** add the matching reference image from the `refs` folder as an "
           "*ingredient* with every scene that has a character.",
           f"- **Saving:** name each clip after the scene number, e.g. `shot03.mp4`, and put it in the "
           f"`clips/{slug}/` folder (or upload to Google Drive and send me the link).",
           "- You don't have to do every scene: any scene without a clip is animated automatically in code.",
           "", "## Style (already included in every prompt)", "", f"> {style['style']}", ""]
    for s_i, s in enumerate(story["shots"], start=1):
        fl = s.get("flow")
        if not fl:
            continue
        cast = [style["cast"][n] for n in fl.get("cast", [])]
        who = " ".join(f"{c['desc']}" for c in cast)
        img = f"{style['style']} {fl['image']} {who}".strip()
        out += [f"---", f"### Scene {s_i:02d}  →  save as `shot{s_i:02d}.mp4`", "",
                f"*Narration:* {s.get('say', '')}", "",
                "**Image prompt:**", "```", img, "```",
                "**Animation prompt:**", "```", f"{fl['motion']} Keep the same art style and character design, "
                "no text, no subtitles.", "```"]
        if fl.get("cast"):
            out.append("Reference images: " + ", ".join(f"`refs/{n}.png`" for n in fl["cast"]))
        out.append("")
    path = os.path.join(sdir, f"flow-{ep}.md")
    open(path, "w").write("\n".join(out))
    os.makedirs(os.path.join(ROOT, "clips", slug), exist_ok=True)
    print("wrote", path)


if __name__ == "__main__":
    main(sys.argv[1])
