"""Canned results for the thinking workers so the whole factory (images, voice, editing,
shorts, publishing) can be tested without an Anthropic key: `python run_factory.py demo`."""

_CHAPTERS = [
    {"title": "اللغز", "text": "بص على الكيبورد اللي قدامك… أول ست حروف: كيو، دبليو، إي، آر، تي، واي. ليه الترتيب الغريب ده؟ مش أبجدي، ومش أسرع ترتيب. طب إزاي مليارات الناس لسه بيكتبوا عليه لحد النهارده؟"},
    {"title": "آلة كاتبة سنة 1873", "text": "نرجع لأمريكا في السبعينات من القرن التسعتاشر. كريستوفر شولز كان بيطوّر آلة كاتبة… والمشكلة إن الأذرع المعدنية كانت بتشبك في بعض لو كتبت بسرعة. فرتّب الحروف بشكل يفرّق بين الحروف اللي بتيجي ورا بعض كتير."},
    {"title": "الاعتماد على المسار", "text": "الترتيب ده اتباع مع الآلة، والناس اتعلّمت عليه، والمدارس درّسته، والشركات اشترت آلات عليه. ولما الكمبيوتر جه، ما حدّش كان عايز يتعلم من الأول. وده اللي الاقتصاديين بيسمّوه: الاعتماد على المسار."},
    {"title": "الدرس", "text": "أول قرار في أي نظام بيبان صغير… بس كل اللي بيتبني بعده بيتبني عليه. لو الفيديو عجبك، اشترك… وقولنا في الكومنتات: إيه الحاجة اللي شغالة عندنا غلط ومحدش قادر يغيّرها؟"},
]

_SCENES = [
    (0, "بص على الكيبورد اللي قدامك… أول ست حروف: كيو، دبليو، إي، آر، تي، واي.", "QWERTY", "red"),
    (0, "ليه الترتيب الغريب ده؟ مش أبجدي، ومش أسرع ترتيب. طب إزاي مليارات الناس لسه بيكتبوا عليه لحد النهارده؟", "ليه الترتيب ده؟", "blue"),
    (1, "نرجع لأمريكا في السبعينات من القرن التسعتاشر. كريستوفر شولز كان بيطوّر آلة كاتبة…", "1873 · آلة كاتبة", "dark"),
    (1, "والمشكلة إن الأذرع المعدنية كانت بتشبك في بعض لو كتبت بسرعة. فرتّب الحروف بشكل يفرّق بين الحروف اللي بتيجي ورا بعض كتير.", "الأذرع بتشبك", "red"),
    (2, "الترتيب ده اتباع مع الآلة، والناس اتعلّمت عليه، والمدارس درّسته، والشركات اشترت آلات عليه.", "الكل اتعلّم عليه", "green"),
    (2, "ولما الكمبيوتر جه، ما حدّش كان عايز يتعلم من الأول. وده اللي الاقتصاديين بيسمّوه: الاعتماد على المسار.", "الاعتماد على المسار", "blue"),
    (3, "أول قرار في أي نظام بيبان صغير… بس كل اللي بيتبني بعده بيتبني عليه.", "قرار صغير… تمن كبير", "dark"),
    (3, "لو الفيديو عجبك، اشترك… وقولنا في الكومنتات: إيه الحاجة اللي شغالة عندنا غلط ومحدش قادر يغيّرها؟", "قولنا في الكومنتات", "green"),
]

TOPIC = "ليه الكيبورد مترتب QWERTY؟"

DEMO = {
    "trend_scout": {"ideas": [{"title": TOPIC, "everyday_mystery": "ترتيب حروف الكيبورد", "hidden_lesson": "الاعتماد على المسار", "why_viral": "كل الناس بتستخدمه"}]},
    "idea_judge": {"topic": TOPIC, "angle": "قرار قديم لسه بيحكمنا", "everyday_mystery": "ترتيب الحروف", "lesson": "الاعتماد على المسار", "reason": "demo"},
    "researcher": {"facts": [], "timeline": [], "conflict": "", "economic_concept": "path dependence", "simple_equation_or_logic": "", "surprise": "", "global_parallel": "", "real_event_proof": ""},
    "fact_checker": {"verified_facts": [], "removed": [], "cautions": ["نسخة تجريبية"]},
    "hook_writer": {"hooks": [{"text": _CHAPTERS[0]["text"], "technique": "لغز يومي"}], "best": 0},
    "scriptwriter": {"title_working": TOPIC, "chapters": _CHAPTERS},
    "script_editor": {"title_working": TOPIC, "chapters": _CHAPTERS},
    "storyboarder": {"scenes": [{"chapter": c, "narration": n, "on_screen_text": t, "visual_prompt": "typewriter and keyboard, flat vector", "accent": a}
                                for c, n, t, a in _SCENES]},
    "thumbnail_designer": lambda job: _thumb(job),
    "seo_publisher": lambda job: _seo(job),
}


def _thumb(job):
    from pathlib import Path
    from . import media
    imgs = (job["steps"]["illustrator"].get("output") or {}).get("images") or []
    out = Path(job["dir"]) / "thumbnail.jpg"
    media.thumbnail(out, "سر QWERTY", "قرار من 1873", "red", imgs[1] if len(imgs) > 1 else None)
    return {"text": "سر QWERTY", "sub": "قرار من 1873", "accent": "red", "thumbnail": str(out)}


def _seo(job):
    return {"title": "ليه الكيبورد مش مترتب أبجدي؟! قرار من 1873 لسه بيحكمنا",
            "description": "ليه أول حروف الكيبورد QWERTY؟\n\nفي الفيديو ده:\n0:00 اللغز\n\n#اقتصاد #معلومات",
            "tags": ["QWERTY", "الكيبورد", "الاعتماد على المسار"], "hashtags": ["#اقتصاد", "#معلومات"],
            "pinned_comment": "إيه الحاجة اللي شغالة غلط ومحدش قادر يغيّرها؟", "short_title": "سر ترتيب الكيبورد", "chapters": ""}
