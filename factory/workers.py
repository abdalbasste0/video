"""The 15 workers. Each takes the job and returns a JSON-serialisable result that is
saved in job.json, so a stopped job can resume from where it stopped."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import media
from .llm import I, S, arr, ask, obj


def _o(job, wid):
    step = job["steps"].get(wid) or {}
    return step.get("output")


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
    return ask(s, "trend_scout", "كشّاف أفكار فيروسية",
               f"اقترح 8 أفكار فيديوهات جديدة في مجال القناة. كل فكرة لازم تبدأ بلغز يومي ملموس وتنتهي بدرس اقتصادي/تاريخي.\n"
               f"ابحث عن مواضيع رائجة الآن لو تقدر.\nمواضيع اتعملت قبل كده (ما تكررهاش):\n{done}",
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
    return ask(s, "scriptwriter", "كاتب سيناريو فيديوهات شرح",
               f"اكتب سكريبت تعليق صوتي كامل عن: {topic}\nالزاوية: {j.get('angle', '')}\nالدرس: {j.get('lesson', '')}\n"
               f"ابدأ بالافتتاحية دي (ممكن تعدّلها بسيط):\n{hook}\n\n"
               f"الطول: حوالي {_words(s)} كلمة. 6 فصول بالضبط على قالب دليل الأسلوب، عنوان قصير لكل فصل (2–4 كلمات).\n"
               f"آخر فصل ينتهي بطلب اللايك والاشتراك وسؤال الكومنتات (مثال لسؤال: {s['channel'].get('cta_question', '')}).\n"
               "استخدم الحقائق دي بس:\n" + _facts(job), schema=CHAPTERS)


# 7 ------------------------------------------------------------------ edit
def script_editor(job, s):
    draft = _o(job, "scriptwriter")
    out = ask(s, "script_editor", "محرر إيقاع ولهجة",
              f"حسّن السكريبت ده للتعليق الصوتي باللهجة {s['channel']['dialect']}: جمل أقصر، وقفات (…) قبل المعلومة المهمة، "
              "سؤال أو معلومة جديدة كل 30 ثانية، انتقالات تفتح فضول للفصل الجاي، شيل أي حشو. "
              f"حافظ على نفس الفصول ونفس الحقائق وطول قريب من {_words(s)} كلمة. اكتب الأرقام بالكلمات لو هتتقري أوضح.\n\n"
              + json.dumps(draft, ensure_ascii=False), schema=CHAPTERS)
    return out


def _script(job):
    return _o(job, "script_editor") or _o(job, "scriptwriter")


# 8 ------------------------------------------------------------------ storyboard
def storyboarder(job, s):
    schema = obj({"scenes": arr(obj({
        "chapter": I, "narration": S, "on_screen_text": S, "visual_prompt": S,
        "accent": {"type": "string", "enum": ["red", "green", "blue", "dark"]},
    }))})
    out = ask(s, "storyboarder", "مخرج مشاهد لفيديو رسوم 2D",
              "قسّم السكريبت لمشاهد. كل مشهد 25–45 كلمة من التعليق (10–20 ثانية). "
              "narration = نص التعليق حرفياً بالترتيب، ولازم مجموع المشاهد يغطي السكريبت كله بدون حذف أو إضافة. "
              "chapter = رقم الفصل من 0. on_screen_text = 2–6 كلمات قوية (رقم، تاريخ، اسم مفهوم). "
              "visual_prompt = وصف إنجليزي لرسمة 2D فيكتور (خريطة، شخصية تاريخية، أعمدة مقارنة، سهم…). "
              "accent: أحمر لأمريكا/الخطر، أخضر لأوروبا/الحل، أزرق للمعلومة، dark للفصول.\n\n"
              + json.dumps(_script(job), ensure_ascii=False), schema=schema)
    if not out.get("scenes"):
        raise ValueError("مخرج المشاهد ما طلّعش مشاهد")
    return out


def _scenes(job):
    return _o(job, "storyboarder")["scenes"]


def _chapter_titles(job):
    return [c["title"] for c in _script(job)["chapters"]]


# 9 ------------------------------------------------------------------ images
def illustrator(job, s):
    d = Path(job["dir"]) / "images"
    d.mkdir(parents=True, exist_ok=True)
    scenes, titles = _scenes(job), _chapter_titles(job)
    w, h = s["video"]["width"], s["video"]["height"]

    def one(i):
        sc = scenes[i]
        path = d / f"scene_{i:03d}.png"
        ch = min(sc.get("chapter", 0), len(titles) - 1)
        start = i == 0 or scenes[i - 1].get("chapter") != sc.get("chapter")
        if s["images"]["provider"] == "http" and s["images"].get("http_url") and not start:
            media.scene_from_api(path, sc, s, w, h)
        else:
            media.scene_card(path, sc, i, len(scenes), titles[ch], start and i != 0, w, h)
        return str(path)

    with ThreadPoolExecutor(s.get("parallel_scene_jobs", 6)) as ex:
        return {"images": list(ex.map(one, range(len(scenes))))}


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
    return [dict(sc, **c) for sc, c in zip(_scenes(job), _o(job, "narrator")["clips"])]


# 11 ----------------------------------------------------------------- sound
def sound_engineer(job, s):
    mix, track = media.build_audio(Path(job["dir"]), _timed_scenes(job), s)
    return {"audio": str(mix), "music": track or "بدون موسيقى (حط ملفات mp3 في assets/music)"}


# 12 ----------------------------------------------------------------- edit video
def editor(job, s):
    jd = Path(job["dir"])
    (jd / "clips").mkdir(exist_ok=True)
    v = s["video"]
    scenes, images = _timed_scenes(job), _o(job, "illustrator")["images"]
    audio = (_o(job, "sound_engineer") or {}).get("audio")
    if not audio:  # sound engineer switched off: narration only, no music
        audio = str(media.build_audio(jd, scenes, s, music=False)[0])

    def one(i):
        out = jd / "clips" / f"clip_{i:03d}.mp4"
        media.scene_clip(images[i], out, scenes[i]["duration"] + 0.35, i, v["width"], v["height"], v["fps"])
        return str(out)

    with ThreadPoolExecutor(min(3, s.get("parallel_scene_jobs", 6))) as ex:
        clips = list(ex.map(one, range(len(scenes))))
    srt, ass = jd / "captions.srt", jd / "captions.ass"
    media.write_srt(srt, scenes)
    media.write_ass(ass, scenes, v["width"], v["height"])
    final = jd / "video.mp4"
    media.assemble(jd, clips, audio, ass, final, v.get("burn_captions", True), v["fps"])
    return {"video": str(final), "srt": str(srt), "audio": str(audio), "seconds": round(media.duration(final), 1)}


# 13 ----------------------------------------------------------------- shorts
def shorts_maker(job, s):
    if not s["video"].get("make_short", True):
        return {"skipped_reason": "معطّل من الإعدادات"}
    t, secs = 0.0, 0.0
    for sc in _timed_scenes(job):
        if t + sc["duration"] + 0.35 > 58:
            break
        t += sc["duration"] + 0.35
        secs = t
    secs = secs or min(58, _o(job, "editor")["seconds"])
    jd = Path(job["dir"])
    ass = jd / "captions_short.ass"
    media.write_ass(ass, _timed_scenes(job), 1080, 1920, words_per_line=4, margin_v=0.2, size=0.04)
    out = jd / "short.mp4"
    media.make_short(jd / "clips" / "joined.mp4", _o(job, "editor")["audio"], ass, out, secs)
    return {"short": str(out), "seconds": round(secs, 1)}


# 14 ----------------------------------------------------------------- thumbnail
def thumbnail_designer(job, s):
    topic, _ = _topic(job)
    schema = obj({"text": S, "sub": S, "accent": {"type": "string", "enum": ["red", "green", "blue"]}})
    t = ask(s, "thumbnail_designer", "مصمم ثامبنيل",
            f"الموضوع: {topic}\nاكتب نص ثامبنيل من 2–4 كلمات بالعربي يصدم ويثير الفضول (رقم أو تناقض)، "
            "ونص فرعي قصير جداً (1–3 كلمات)، واختار لون التمييز.\nالمشاهد:\n"
            + json.dumps([sc["on_screen_text"] for sc in _scenes(job)], ensure_ascii=False), schema=schema)
    images = (_o(job, "illustrator") or {}).get("images") or []
    out = Path(job["dir"]) / "thumbnail.jpg"
    media.thumbnail(out, t["text"], t["sub"], t["accent"], images[1] if len(images) > 1 else None)
    return dict(t, thumbnail=str(out))


# 15 ----------------------------------------------------------------- SEO (publishing runs right after)
def seo_publisher(job, s):
    topic, _ = _topic(job)
    scenes, titles = _timed_scenes(job), _chapter_titles(job)
    stamps, t, seen = [], 0.0, set()
    for sc in scenes:
        ch = sc.get("chapter", 0)
        if ch not in seen and ch < len(titles):
            seen.add(ch)
            stamps.append(f"{int(t // 60)}:{int(t % 60):02d} {titles[ch]}")
        t += sc["duration"] + 0.35
    chapters = "\n".join(stamps)
    schema = obj({"title": S, "description": S, "tags": arr(S), "hashtags": arr(S), "pinned_comment": S, "short_title": S})
    meta = ask(s, "seo_publisher", "خبير SEO يوتيوب عربي",
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
