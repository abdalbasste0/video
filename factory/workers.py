"""The 15 workers. Each takes the job and returns a JSON-serialisable result that is
saved in job.json, so a stopped job can resume from where it stopped."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import image_providers, media, scene_art
from .llm import I, S, arr, ask, obj


def _o(job, wid):
    step = job["steps"].get(wid) or {}
    return step.get("output")


def _story(s):
    return s["channel"].get("format") == "story"


def _words(s):
    return int(s["channel"].get("video_minutes", 5.5) * 135)


def _history(job_root):
    f = Path(job_root) / "topics_done.txt"
    return f.read_text(encoding="utf-8").splitlines()[-60:] if f.exists() else []


# 1 ------------------------------------------------------------------ ideas
def trend_scout(job, s):
    if job.get("topic"):
        return {"skipped_reason": "الموضوع محدد من المستخدم", "ideas": [{"title": job["topic"]}]}
    done = "\n".join(_history(s["output_dir"])) or "لا يوجد"
    schema = obj({"ideas": arr(obj({"title": S, "everyday_mystery": S, "hidden_lesson": S, "why_viral": S}))})
    if _story(s):
        intro = ("اقترح 8 أفكار فيديوهات قصة جديدة. كل فكرة سؤال «ليش ما…؟» عن شيء مشهور (مكان/حدث/مشروع) إجابته كومة "
                 "مشاكل حقيقية تكبر واحدة ورا الثانية ونهايتها إنسانية، وفيها حدث درامي حقيقي.\n")
    else:
        intro = "اقترح 8 أفكار فيديوهات جديدة في مجال القناة. كل فكرة لازم تبدأ بلغز يومي ملموس وتنتهي بدرس اقتصادي/تاريخي.\n"
    return ask(s, "trend_scout", "كشّاف أفكار فيروسية",
               intro + f"ابحث عن مواضيع رائجة الآن لو تقدر.\nمواضيع اتعملت قبل كده (ما تكررهاش):\n{done}",
               schema=schema, web=True)


# 2 ------------------------------------------------------------------ judge
def idea_judge(job, s):
    ideas = _o(job, "trend_scout") or {"ideas": [{"title": job.get("topic")}]}
    schema = obj({"topic": S, "angle": S, "everyday_mystery": S, "lesson": S, "reason": S})
    return ask(s, "idea_judge", "حَكَم يختار أقوى فكرة ويحدد زاويتها",
               "قيّم الأفكار دي من 10 على: قوة اللغز، سهولة الرسم، وجود أرقام وتواريخ حقيقية، الدرس المخفي، قابلية الانتشار.\n"
               "اختار واحدة بس وحدد زاوية الحكاية واللغز اليومي اللي هنبدأ بيه والدرس.\n\n"
               + json.dumps(ideas, ensure_ascii=False), schema=schema)


def _topic(job):
    j = _o(job, "idea_judge") or {}
    return j.get("topic") or job.get("topic"), j


# 3 ------------------------------------------------------------------ research
def researcher(job, s):
    topic, j = _topic(job)
    schema = obj({
        "facts": arr(obj({"claim": S, "detail": S, "year": S, "source": S})),
        "timeline": arr(obj({"year": S, "event": S})),
        "conflict": S, "economic_concept": S, "simple_equation_or_logic": S,
        "surprise": S, "global_parallel": S, "real_event_proof": S,
    })
    return ask(s, "researcher", "باحث تاريخي واقتصادي دقيق",
               f"الموضوع: {topic}\nالزاوية: {j.get('angle', '')}\nاللغز: {j.get('everyday_mystery', '')}\n\n"
               "اجمع 12–18 حقيقة موثقة بأرقام وتواريخ وأسماء وأماكن، مع مصدر لكل واحدة (اسم موقع/كتاب/رابط).\n"
               "حدد: الصراع بين طرفين، المفهوم الاقتصادي الأساسي ومنطقه البسيط، معلومة مفاجئة تقلب الصورة، "
               "ومثال من بلد تاني أغرب + حدث حقيقي أثبته.",
               schema=schema, web=True)


# 4 ------------------------------------------------------------------ fact check
def fact_checker(job, s):
    schema = obj({
        "verified_facts": arr(obj({"claim": S, "detail": S, "year": S, "source": S})),
        "removed": arr(obj({"claim": S, "reason": S})),
        "cautions": arr(S),
    })
    return ask(s, "fact_checker", "مدقق حقائق متشدد",
               "راجع البحث ده. احتفظ بالمعلومات المؤكدة فقط، صحّح أي رقم أو تاريخ غلط، واحذف أي شيء مشكوك فيه مع السبب. "
               "اكتب تحذيرات للكاتب (مثلاً: قول 'تقريباً' هنا).\n\n" + json.dumps(_o(job, "researcher"), ensure_ascii=False),
               schema=schema, web=True)


def _facts(job):
    fc = _o(job, "fact_checker")
    r = dict(_o(job, "researcher") or {})
    if fc:
        r["facts"] = fc["verified_facts"]
        r["cautions"] = fc["cautions"]
    return json.dumps(r, ensure_ascii=False)


# 5 ------------------------------------------------------------------ hook
def hook_writer(job, s):
    topic, j = _topic(job)
    schema = obj({"hooks": arr(obj({"text": S, "technique": S})), "best": I})
    return ask(s, "hook_writer", "صانع افتتاحيات تمسك المشاهد",
               f"الموضوع: {topic}\nاللغز: {j.get('everyday_mystery', '')}\n\nاكتب 3 افتتاحيات مختلفة (40–60 كلمة لكل واحدة) "
               "تبدأ بموقف يومي، ثم مقارنة أرقام، ثم سؤال 'طب إزاي…؟'، ثم وعد بالحكاية. "
               "اختار الأفضل (best = رقمها من 0).\nالحقائق المتاحة:\n" + _facts(job), schema=schema)


# 6 ------------------------------------------------------------------ script
CHAPTERS = obj({"title_working": S, "chapters": arr(obj({"title": S, "text": S}))})


def scriptwriter(job, s):
    topic, j = _topic(job)
    h = _o(job, "hook_writer")
    hook = h["hooks"][min(h["best"], len(h["hooks"]) - 1)]["text"] if h and h.get("hooks") else "(اكتب أنت الافتتاحية)"
    if _story(s):
        return ask(s, "scriptwriter", "كاتب قصص فيديو",
                   f"اكتب سكريبت تعليق صوتي كامل لفيديو قصة عن: {topic}\nالزاوية: {j.get('angle', '')}\n"
                   f"ابدأ بالافتتاحية دي (ممكن تعدّلها بسيط):\n{hook}\n\n"
                   f"الطول: حوالي {_words(s)} كلمة. امشِ على هيكل دليل أسلوب القصة: هوك، ثم مشاكل متتالية كل واحدة أكبر "
                   "(«طيب خلّنا نفترض حليت هذي…»)، حلول مجنونة تسقط، قصة حقيقية داخل القصة بتواريخ، مشكلة الطبيعة/الوقت، "
                   "ثم المشكلة الإنسانية، وخاتمة هادية بجمل قصيرة جداً ثم طلب الدعم والاشتراك.\n"
                   "كل فصل = مشكلة أو مرحلة، بعنوان قصير (2–4 كلمات). استخدم تشبيهات من حياة المشاهد اليومية.\n"
                   "استخدم الحقائق دي بس:\n" + _facts(job), schema=CHAPTERS)
    return ask(s, "scriptwriter", "كاتب سيناريو فيديوهات شرح",
               f"اكتب سكريبت تعليق صوتي كامل عن: {topic}\nالزاوية: {j.get('angle', '')}\nالدرس: {j.get('lesson', '')}\n"
               f"ابدأ بالافتتاحية دي (ممكن تعدّلها بسيط):\n{hook}\n\n"
               f"الطول: حوالي {_words(s)} كلمة. 6 فصول بالضبط على قالب دليل الأسلوب، عنوان قصير لكل فصل (2–4 كلمات).\n"
               f"آخر فصل ينتهي بطلب اللايك والاشتراك وسؤال الكومنتات (مثال لسؤال: {s['channel'].get('cta_question', '')}).\n"
               "استخدم الحقائق دي بس:\n" + _facts(job), schema=CHAPTERS)


# 7 ------------------------------------------------------------------ edit
def script_editor(job, s):
    draft = _o(job, "scriptwriter")
    if _story(s):
        return ask(s, "script_editor", "محرر إيقاع قصص",
                   f"حسّن السكريبت ده للتعليق باللهجة {s['channel']['dialect']}: جمل قصيرة جداً ومتصلة، كرر الرقم الصادم مرة، "
                   "«ليش؟» قبل كل كشف، خلي آخر دقيقتين أبطأ بجمل من كلمتين أو ثلاث. نفس الفصول والحقائق وطول قريب من "
                   f"{_words(s)} كلمة.\n\n" + json.dumps(draft, ensure_ascii=False), schema=CHAPTERS)
    out = ask(s, "script_editor", "محرر إيقاع ولهجة",
              f"حسّن السكريبت ده للتعليق الصوتي باللهجة {s['channel']['dialect']}: جمل أقصر، وقفات (…) قبل المعلومة المهمة، "
              "سؤال أو معلومة جديدة كل 30 ثانية، انتقالات تفتح فضول للفصل الجاي، شيل أي حشو. "
              f"حافظ على نفس الفصول ونفس الحقائق وطول قريب من {_words(s)} كلمة. اكتب الأرقام بالكلمات لو هتتقري أوضح.\n\n"
              + json.dumps(draft, ensure_ascii=False), schema=CHAPTERS)
    return out


def _script(job):
    return _o(job, "script_editor") or _o(job, "scriptwriter")


# 8 ------------------------------------------------------------------ storyboard
BLOCKS = ["none", "big_number", "compare", "equation", "labels", "cta"]


POSES = ["thinking", "pointing", "shocked", "happy", "standing"]
BGS = ["cream", "white", "navy", "blue", "sand", "dark"]


def story_storyboard(job, s):
    """Story format: one shot per 6–14 spoken words (~3–4 s), each an illustration or a big-word card."""
    schema = obj({"series_tag": S, "scenes": arr(obj({
        "chapter": I, "narration": S,
        "kind": {"type": "string", "enum": ["illustration", "text"]},
        "text": S, "pose": {"type": "string", "enum": POSES}, "bg": {"type": "string", "enum": BGS},
        "visual_prompt": S,
    }))})
    out = ask(s, "storyboarder", "مخرج لقطات لفيديو قصة بالرسوم",
              "قسّم السكريبت للقطات قصيرة: كل لقطة 6–14 كلمة من التعليق (3–4 ثواني). narration = النص حرفياً بالترتيب "
              "ومجموع اللقطات يغطي السكريبت كله. chapter = رقم الفصل من 0.\n"
              "kind: illustration (رسمة كرتون للمشهد) أو text (كارت كلمة كبيرة لرقم صادم أو عنوان مشكلة، حوالي لقطة من كل 4–5).\n"
              "text: للكارت = الكلمة/الرقم (1–5 كلمات). للرسمة = تسمية قصيرة اختيارية تظهر تحت الصورة أو فاضي.\n"
              "visual_prompt: وصف إنجليزي دقيق للرسمة بأسلوب ستيك مان (الشخصيات، الفعل، المكان، الأشياء)، بدون أي كتابة داخل الصورة.\n"
              "pose: وضعية شخصية الستيك مان لو مفيش مولّد صور. bg: cream/white للشرح، navy/dark للأعماق واللحظات المظلمة، blue للبحر/السماء.\n"
              "series_tag: فاضي.\n\n" + json.dumps(_script(job), ensure_ascii=False), schema=schema)
    if not out.get("scenes"):
        raise ValueError("مخرج اللقطات ما طلّعش لقطات")
    return out


def storyboarder(job, s):
    if _story(s):
        return story_storyboard(job, s)
    schema = obj({"series_tag": S, "scenes": arr(obj({
        "chapter": I, "narration": S, "title": S, "highlight": S,
        "block": {"type": "string", "enum": BLOCKS},
        "main": S, "left_label": S, "left_value": S, "right_label": S, "right_value": S,
        "labels": arr(S), "stamp": S, "date_tag": S,
        "accent": {"type": "string", "enum": ["red", "green", "blue", "dark"]},
        "visual_prompt": S,
    }))})
    out = ask(s, "storyboarder", "مخرج مشاهد لفيديو شرح 2D على طريقة الفيديو المرجعي",
              "قسّم السكريبت لمشاهد. كل مشهد 20–40 كلمة من التعليق (8–15 ثانية).\n"
              "narration = نص التعليق حرفياً بالترتيب، ومجموع المشاهد يغطي السكريبت كله بدون حذف أو إضافة.\n"
              "chapter = رقم الفصل من 0 (أول مشهد في كل فصل جديد بيظهر قبله كارت الفصل تلقائياً).\n"
              "series_tag = اسم السلسلة القصير اللي هيفضل في الركن طول الفيديو (2–3 كلمات زي «لغز 120 فولت»).\n"
              "لكل مشهد اختار عناصر الشاشة (بتظهر واحد ورا التاني مع الكلام):\n"
              "- title: سطر قصير فوق (3–6 كلمات) غالباً سؤال، و highlight = الكلمة/الجزء اللي يتلوّن أحمر (لازم يكون جزء حرفي من title).\n"
              "- block: big_number (main = رقم كبير زي 120V أو 1882) | compare (عمودين: right = الحالة الغريبة/الأضعف بالأحمر، "
              "left = المقارنة بالأخضر، والقيم أرقام لو أمكن) | equation (main زي «القدرة = الفولت × التيار») | "
              "labels (2–3 بطاقات قصيرة في labels) | none | cta (آخر مشهد فقط: لايك واشتراك وكومنتات).\n"
              "- labels: 0–3 بطاقات من 1–3 كلمات. stamp: ختم مائل قصير (2–3 كلمات) لمفاجأة أو حكم، أو فاضي. "
              "date_tag: «مدينة · سنة» لو المشهد فيه تاريخ، أو فاضي.\n"
              "- الحقول اللي مش مستخدمة تبقى نص فاضي. accent: لون التمييز. visual_prompt: وصف إنجليزي لرسمة 2D مسطحة للمشهد.\n"
              "نوّع العناصر: ما تكررش نفس الـ block أكتر من مرتين ورا بعض.\n\n"
              + json.dumps(_script(job), ensure_ascii=False), schema=schema)
    if not out.get("scenes"):
        raise ValueError("مخرج المشاهد ما طلّعش مشاهد")
    return out


def _scenes(job):
    return _o(job, "storyboarder")["scenes"]


def _chapter_titles(job):
    return [c["title"] for c in _script(job)["chapters"]]


# 9 ------------------------------------------------------------------ images
def _series(job):
    sb = _o(job, "storyboarder") or {}
    return sb.get("series_tag") or scene_art.series_from(_topic(job)[0])


def illustrator(job, s):
    """Draws every scene as build states (elements pop in one by one) + navy chapter cards."""
    d = Path(job["dir"]) / "images"
    d.mkdir(parents=True, exist_ok=True)
    scenes, titles = _scenes(job), _chapter_titles(job)
    w, h = s["video"]["width"], s["video"]["height"]
    series = _series(job)
    use_api = image_providers.enabled(s["images"])

    if _story(s):
        def shot(i):
            sc = scenes[i]
            ill = None
            err = None
            if use_api and sc.get("kind") != "text":
                for attempt in range(2):
                    try:
                        ill = media.fetch_illustration(sc, s, w, h, seed=1000 + i + attempt)
                        break
                    except Exception as e:  # falls back to the offline stick figure
                        err = str(e)[:200]
            p = d / f"shot_{i:03d}.png"
            scene_art.story_frame(sc, w, h, ill).save(p)
            return {"states": [str(p)], "card": None, "ai": ill is not None, "error": err}

        workers = min(s.get("parallel_scene_jobs", 6), int(s["images"].get("parallel", 3))) if use_api else 6
        with ThreadPoolExecutor(max(1, workers)) as ex:
            shots = list(ex.map(shot, range(len(scenes))))
        wanted = sum(1 for sc in scenes if sc.get("kind") != "text") if use_api else 0
        made = sum(1 for x in shots if x["ai"])
        errors = [x["error"] for x in shots if x.get("error")]
        return {"scenes": shots, "ai_images": f"{made}/{wanted}", "first_error": errors[0] if errors else None}

    def one(i):
        sc = scenes[i]
        ch = min(sc.get("chapter", 0), len(titles) - 1)
        ill = None
        if use_api and sc.get("block", "none") == "none":
            try:
                ill = media.fetch_illustration(sc, s, w, h)
            except Exception:
                ill = None  # a failed picture must not stop the video
        paths = []
        for k, img in enumerate(scene_art.build_states(sc, w, h, series, titles[ch], ill)):
            p = d / f"scene_{i:03d}_{k}.png"
            img.save(p)
            paths.append(str(p))
        card = None
        if i > 0 and sc.get("chapter") != scenes[i - 1].get("chapter"):
            card = str(d / f"card_{i:03d}.png")
            scene_art.chapter_card(w, h, ch + 1, titles[ch]).save(card)
        return {"states": paths, "card": card}

    with ThreadPoolExecutor(s.get("parallel_scene_jobs", 6)) as ex:
        return {"scenes": list(ex.map(one, range(len(scenes))))}


# 10 ----------------------------------------------------------------- voice
def narrator(job, s):
    d = Path(job["dir"]) / "audio"
    d.mkdir(parents=True, exist_ok=True)
    scenes = _scenes(job)

    def one(i):
        path = d / f"voice_{i:03d}.mp3"
        return {"audio": str(path), "duration": media.tts(path, scenes[i]["narration"], s)}

    with ThreadPoolExecutor(min(4, s.get("parallel_scene_jobs", 6))) as ex:
        return {"clips": list(ex.map(one, range(len(scenes))))}


def _timed_scenes(job):
    """Scenes + voice length + chapter-card lead time (2s silence under each chapter card)."""
    story = _story(_job_settings(job))
    out = []
    for i, (sc, c) in enumerate(zip(_scenes(job), _o(job, "narrator")["clips"])):
        new_chapter = i > 0 and sc.get("chapter") != out[-1].get("chapter")
        if story:  # story: continuous narration, no chapter cards, tiny breath between shots
            out.append(dict(sc, **c, lead=0.0, gap=0.12))
        else:
            out.append(dict(sc, **c, lead=media.CARD if new_chapter else 0.0))
    return out


def _job_settings(job):
    from . import settings as cfg
    return cfg._merge(cfg.load(), job.get("overrides") or {})


# 11 ----------------------------------------------------------------- sound
def sound_engineer(job, s):
    mix, track = media.build_audio(Path(job["dir"]), _timed_scenes(job), s)
    return {"audio": str(mix), "music": track or "بدون موسيقى (حط ملفات mp3 في assets/music)"}


# 12 ----------------------------------------------------------------- edit video
def editor(job, s):
    jd = Path(job["dir"])
    (jd / "clips").mkdir(exist_ok=True)
    v = s["video"]
    scenes, art = _timed_scenes(job), _o(job, "illustrator")["scenes"]
    story = _story(s)
    audio = (_o(job, "sound_engineer") or {}).get("audio")
    if not audio:  # sound engineer switched off: narration only, no music
        audio = str(media.build_audio(jd, scenes, s, music=False)[0])

    def one(i):
        outs = []
        if scenes[i]["lead"] and art[i].get("card"):
            c = jd / "clips" / f"card_{i:03d}.mp4"
            media.card_clip(art[i]["card"], c, scenes[i]["lead"], v["fps"])
            outs.append(str(c))
        out = jd / "clips" / f"clip_{i:03d}.mp4"
        secs = scenes[i]["duration"] + scenes[i].get("gap", media.GAP)
        if story:
            media.zoom_clip(art[i]["states"][0], out, secs, v["fps"], i)
        else:
            media.build_clip(art[i]["states"], out, secs, v["fps"])
        return outs + [str(out)]

    with ThreadPoolExecutor(min(3, s.get("parallel_scene_jobs", 6))) as ex:
        clips = [c for group in ex.map(one, range(len(scenes))) for c in group]
    srt, ass = jd / "captions.srt", jd / "captions.ass"
    media.write_srt(srt, scenes)
    media.write_ass(ass, scenes, v["width"], v["height"])
    final = jd / "video.mp4"
    burn = v.get("story_captions", False) if story else v.get("burn_captions", True)  # the story reference has no captions
    media.assemble(jd, clips, audio, ass, final, burn, v["fps"])
    return {"video": str(final), "srt": str(srt), "audio": str(audio), "seconds": round(media.duration(final), 1)}


# 13 ----------------------------------------------------------------- shorts
def shorts_maker(job, s):
    if not s["video"].get("make_short", True):
        return {"skipped_reason": "معطّل من الإعدادات"}
    scenes, secs = _timed_scenes(job), 0.0
    for sc, (start, _) in zip(scenes, media.segments(scenes)):
        end = start + sc["lead"] + sc["duration"] + sc.get("gap", media.GAP)
        if end > 58:
            break
        secs = end
    secs = secs or min(58, _o(job, "editor")["seconds"])
    jd = Path(job["dir"])
    ass = jd / "captions_short.ass"
    media.write_ass(ass, scenes, 1080, 1920, words_per_line=3, center_y=0.76, size=0.034)
    out = jd / "short.mp4"
    media.make_short(jd / "clips" / "joined.mp4", _o(job, "editor")["audio"], ass, out, secs)
    return {"short": str(out), "seconds": round(secs, 1)}


# 14 ----------------------------------------------------------------- thumbnail
def thumbnail_designer(job, s):
    topic, _ = _topic(job)
    schema = obj({"text": S, "sub": S, "accent": {"type": "string", "enum": ["red", "green", "blue"]}})
    t = (job.get("answers") or {}).get("thumbnail_designer") or ask(s, "thumbnail_designer", "مصمم ثامبنيل",
            f"الموضوع: {topic}\nاكتب نص ثامبنيل من 2–4 كلمات بالعربي يصدم ويثير الفضول (رقم أو تناقض)، "
            "ونص فرعي قصير جداً (1–3 كلمات)، واختار لون التمييز.\nالمشاهد:\n"
            + json.dumps([sc.get("title") or sc.get("main") for sc in _scenes(job)], ensure_ascii=False), schema=schema)
    art = (_o(job, "illustrator") or {}).get("scenes") or []
    out = Path(job["dir"]) / "thumbnail.jpg"
    media.thumbnail(out, t["text"], t["sub"], t["accent"], art[0]["states"][-1] if art else None)
    return dict(t, thumbnail=str(out))


# 15 ----------------------------------------------------------------- SEO (publishing runs right after)
def seo_publisher(job, s):
    topic, _ = _topic(job)
    scenes, titles = _timed_scenes(job), _chapter_titles(job)
    stamps, seen = [], set()
    for sc, (t, _) in zip(scenes, media.segments(scenes)):
        ch = sc.get("chapter", 0)
        if ch not in seen and ch < len(titles):
            seen.add(ch)
            stamps.append(f"{int(t // 60)}:{int(t % 60):02d} {titles[ch]}")
    chapters = "\n".join(stamps)
    schema = obj({"title": S, "description": S, "tags": arr(S), "hashtags": arr(S), "pinned_comment": S, "short_title": S})
    meta = dict((job.get("answers") or {}).get("seo_publisher") or {}) or ask(s, "seo_publisher", "خبير SEO يوتيوب عربي",
               f"الموضوع: {topic}\nالسكريبت:\n{json.dumps(_script(job), ensure_ascii=False)}\n\n"
               "اكتب: عنوان (أقل من 70 حرف) سؤال صادم يجمع قوة + ضعف غريب؛ وصف: سطرين يعيدوا اللغز ثم السطر "
               "'في الفيديو ده:' ثم مكان الفصول اكتب حرفياً {CHAPTERS} ثم جملة الدرس ثم سؤال الكومنتات؛ "
               "15–20 تاج بالكلمات اللي الناس بتكتبها؛ 5–7 هاشتاجات؛ تعليق مثبّت؛ عنوان للشورتس.",
               schema=schema)
    meta["description"] = meta["description"].replace("{CHAPTERS}", chapters)
    if "{CHAPTERS}" not in meta["description"] and chapters not in meta["description"]:
        meta["description"] += "\n\n" + chapters
    meta["description"] += "\n\n" + " ".join(h if h.startswith("#") else "#" + h for h in meta["hashtags"])
    meta["chapters"] = chapters
    return meta


FUNCS = {f.__name__: f for f in [
    trend_scout, idea_judge, researcher, fact_checker, hook_writer, scriptwriter, script_editor, storyboarder,
    illustrator, narrator, sound_engineer, editor, shorts_maker, thumbnail_designer, seo_publisher,
]}
