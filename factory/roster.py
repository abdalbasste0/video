"""The 15 workers of the factory, in production order.

kind:
  "llm"   -> the worker thinks with Claude
  "media" -> the worker builds files locally (images, audio, video)
model:  default model slot ("main" or "fast"), editable from the dashboard
required: cannot be switched off (the video can't be made without it)
"""

WORKERS = [
    {"id": "trend_scout", "num": 1, "name": "كشّاف الأفكار", "kind": "llm", "model": "fast", "required": False,
     "desc": "يقترح 8 ألغاز يومية لها جذر اقتصادي/تاريخي (مثل: ليه أمريكا على 120 فولت؟). يشتغل فقط لو ما كتبتش موضوع."},
    {"id": "idea_judge", "num": 2, "name": "حَكَم الأفكار", "kind": "llm", "model": "fast", "required": False,
     "desc": "يقيّم الأفكار (فضول، سهولة الشرح، الدرس المخفي) ويختار الأقوى ويحدد زاوية الحكاية."},
    {"id": "researcher", "num": 3, "name": "الباحث", "kind": "llm", "model": "main", "required": True,
     "desc": "يجمع الحقائق والتواريخ والأرقام والمصادر، والمفهوم الاقتصادي، والمفاجأة، والمثال العالمي الموازي."},
    {"id": "fact_checker", "num": 4, "name": "مدقق الحقائق", "kind": "llm", "model": "main", "required": False,
     "desc": "يراجع كل معلومة، يحذف المشكوك فيه، ويكتب تحذيرات للكاتب."},
    {"id": "hook_writer", "num": 5, "name": "صانع الافتتاحية", "kind": "llm", "model": "main", "required": False,
     "desc": "يكتب 3 افتتاحيات (أول 15 ثانية) على طريقة اللغز اليومي ويختار الأفضل."},
    {"id": "scriptwriter", "num": 6, "name": "كاتب السيناريو", "kind": "llm", "model": "main", "required": True,
     "desc": "يكتب السكريبت كامل باللهجة المختارة على قالب الـ6 فصول (لغز ← تاريخ ← صراع ← اقتصاد ← مفاجأة ← درس)."},
    {"id": "script_editor", "num": 7, "name": "محرر الإيقاع واللهجة", "kind": "llm", "model": "main", "required": False,
     "desc": "يشدّ الإيقاع، يحط وقفات (…) للتعليق، يشيل الحشو، ويضمن إن كل 30 ثانية فيه سؤال أو معلومة جديدة."},
    {"id": "storyboarder", "num": 8, "name": "مخرج المشاهد", "kind": "llm", "model": "main", "required": True,
     "desc": "يقسّم السكريبت لمشاهد 10–20 ثانية، ولكل مشهد: نص على الشاشة، وصف الرسمة، ولون التمييز."},
    {"id": "illustrator", "num": 9, "name": "الرسّام", "kind": "media", "model": "fast", "required": True,
     "desc": "يرسم صورة لكل مشهد (بطاقات 2D جاهزة محلياً، أو أي API صور تربطه من الإعدادات)."},
    {"id": "narrator", "num": 10, "name": "المعلّق الصوتي", "kind": "media", "model": "fast", "required": True,
     "desc": "يقرأ كل مشهد بصوت عربي (Edge مجاني أو ElevenLabs)، ويقيس مدة كل مشهد بالضبط."},
    {"id": "sound_engineer", "num": 11, "name": "مهندس الصوت", "kind": "media", "model": "fast", "required": False,
     "desc": "يجمع التعليق، ويضيف موسيقى خلفية من assets/music مع خفض تلقائي للموسيقى وقت الكلام (ducking)."},
    {"id": "editor", "num": 12, "name": "المونتير", "kind": "media", "model": "fast", "required": True,
     "desc": "يركّب الفيديو بحركة زوم هادئة، يحرق الترجمة العربية، ويطلع MP4 جاهز 1080p."},
    {"id": "shorts_maker", "num": 13, "name": "صانع الشورتس", "kind": "media", "model": "fast", "required": False,
     "desc": "يقص الافتتاحية كفيديو عمودي 9:16 (أقل من 60 ثانية) لتيك توك/ريلز/شورتس."},
    {"id": "thumbnail_designer", "num": 14, "name": "مصمم الصورة المصغرة", "kind": "llm", "model": "fast", "required": False,
     "desc": "يكتب نص الثامبنيل (3–4 كلمات صادمة) ويصمم صورة 1280×720."},
    {"id": "seo_publisher", "num": 15, "name": "خبير SEO والنشر", "kind": "llm", "model": "fast", "required": True,
     "desc": "يكتب العنوان والوصف بالفصول الحقيقية والتاجات وتعليق مثبّت، ثم يسلّم الفيديو لكل المنصات المربوطة."},
]

WORKER_IDS = [w["id"] for w in WORKERS]
BY_ID = {w["id"]: w for w in WORKERS}
