// بنك أفكار وقصص جاهزة: يجعل المصنع يعمل فورًا حتى بدون أي مفاتيح API (الوضع التجريبي)
export const NICHES = {
  horror: { label: 'قصص رعب', icon: '👻' },
  crime: { label: 'عالم الجريمة', icon: '🕵️' },
  riddle: { label: 'ألغاز', icon: '🧩' },
};

export const IDEA_BANK = {
  horror: [
    'صوت يناديك باسمك من الغيط في منتصف الليل',
    'المرآة التي تتأخر عن حركتك بثانية',
    'البيت الذي يضيف غرفة جديدة كل ليلة',
    'رسائل صوتية من رقم أمك المتوفاة',
    'حارس المقابر الذي يعدّ القبور فيجدها تزيد',
  ],
  crime: [
    'الجريمة التي حلّها فنجان قهوة بارد',
    'شاهد العيان الوحيد كان ببغاء',
    'اللص الذي يعيد ما يسرقه بعد أسبوع',
    'الغرفة المغلقة من الداخل في الطابق العاشر',
    'البصمة التي ظهرت بعد موت صاحبها بسنة',
  ],
  riddle: [
    'لغز البيت الذي كل نوافذه تطل على الجنوب',
    'لغز الرجل الذي مات في الصحراء ومعه عود ثقاب',
    'لغز الأبواب الثلاثة والحارس الكاذب',
    'لغز الساعة التي توقفت عند وقت الجريمة',
    'لغز المصعد والرجل الذي يصعد للطابق السابع فقط',
  ],
};

const T = (narration, visualAr, visualEn, opts = {}) => ({
  narration,
  onScreenText: opts.text || '',
  visual: visualAr,
  imagePrompt: visualEn,
  camera: opts.camera || 'medium shot',
  characters: opts.chars || [],
  sfx: opts.sfx || 'wind',
  motion: opts.motion || 'zoomIn',
});

export const DEMO_SCRIPTS = {
  horror: {
    title: 'لا تردّ على النداء',
    logline: 'أب وابنته على طريق زراعي ليلًا، وصوت امرأة يناديهما من حقول القصب.',
    hook: 'في تلك الليلة ظن حسن أن أخطر ما في الطريق هو الظلام…',
    mood: 'horror',
    characters: [
      { id: 'hassan', name: 'حسن', role: 'الأب', look: 'رجل خمسيني بجلباب رمادي يحمل فانوسًا' },
      { id: 'fatma', name: 'فاطمة', role: 'الابنة', look: 'طفلة في العاشرة بضفيرتين وفستان أزرق' },
      { id: 'naddaha', name: 'النداهة', role: 'الكيان', look: 'امرأة طويلة بفستان أبيض ووجه غير واضح' },
    ],
    scenes: [
      T('[whispers] في تلك الليلة… ظن حسن أن أخطر ما في الطريق هو ظلامه.', 'رجل وابنته يمشيان على طريق زراعي مظلم بين حقول القصب، فانوس، قمر', 'stick figure man with lantern and little girl walking on dark rural road between sugarcane fields at night, full moon, fog', { chars: ['hassan', 'fatma'], sfx: 'crickets', motion: 'zoomIn', camera: 'wide shot' }),
      T('وبينما يمشي مع ابنته فاطمة… سمعا صوت امرأة ينادي من وسط الحقل.', 'حقول قصب كثيفة في الظلام وضباب، رجل وطفلة يلتفتان', 'dark dense sugarcane field at night, fog, stick figure man and girl turning their heads, eerie', { chars: ['hassan', 'fatma'], sfx: 'whisper', motion: 'panLeft' }),
      T('[nervous] توقفت فاطمة فجأة وقالت: بابا… هل تعرفني هذه المرأة؟', 'طفلة تنظر إلى أبيها بخوف، فانوس', 'close up stick figure little girl looking up at her father with lantern light, fear', { chars: ['fatma', 'hassan'], sfx: 'heartbeat', motion: 'zoomIn', camera: 'close-up', text: 'هل تعرفني؟' }),
      T('شدّ حسن يدها وقال: لا تردّي مهما سمعتِ… ولا تنظري خلفك.', 'رجل يمسك يد ابنته ويمشي بسرعة، طريق مظلم', 'stick figure father grabbing daughter hand walking fast on dark road, lantern, tension', { chars: ['hassan', 'fatma'], sfx: 'footsteps', motion: 'shake' }),
      T('[whispers] لكن الصوت تغيّر… صار يشبه صوت أمها التي ماتت منذ سنين.', 'امرأة بفستان أبيض بعيدة بين القصب، ضباب', 'ghostly woman in white dress standing far between sugarcane in fog at night, faceless', { chars: ['naddaha'], sfx: 'whisper', motion: 'zoomIn', camera: 'long shot' }),
      T('رفع حسن الفانوس… فرأى امرأة بفستان أبيض واقفة بين عيدان القصب.', 'رجل يرفع فانوسًا ويرى امرأة شبحية بفستان أبيض', 'stick figure man raising lantern revealing ghost woman in white dress among sugarcane', { chars: ['hassan', 'naddaha'], sfx: 'stinger', motion: 'shake', camera: 'over the shoulder' }),
      T('جرى بابنته نحو أنوار البيوت… لكن النداء صار يأتي من كل اتجاه.', 'رجل يركض مع طفلة نحو بيوت قرية مضيئة بعيدة', 'stick figure man running with girl toward distant lit village houses at night, fog', { chars: ['hassan', 'fatma'], sfx: 'footsteps', motion: 'panRight', camera: 'wide shot' }),
      T('[nervous] وفجأة… سمع صوت فاطمة يناديه من داخل الحقل، رغم أن يدها كانت في يده.', 'رجل يتجمد في مكانه، طفلة بجانبه، ظل في الحقل', 'stick figure man frozen, girl beside him, dark silhouette calling from sugarcane field', { chars: ['hassan', 'fatma'], sfx: 'heartbeat', motion: 'zoomIn', camera: 'close-up' }),
      T('[whispers] نظر بجانبه… فوجدها تبتسم، وقالت بصوت ليس صوتها: بابا… هي تناديك أنت أيضًا.', 'طفلة تبتسم ابتسامة مخيفة بعيون متوهجة', 'creepy smiling stick figure little girl with glowing eyes at night, horror', { chars: ['fatma'], sfx: 'stinger', motion: 'zoomIn', camera: 'extreme close-up', text: 'هي تناديك أنت أيضًا' }),
    ],
    riddle: null,
    cta: 'لو سمعت النداء… هل كنت سترد؟ اكتب في التعليقات.',
  },
  crime: {
    title: 'الفنجان البارد',
    logline: 'رجل أعمال يُعثر عليه ميتًا في مكتبه المغلق، وفنجان قهوة بارد يكشف الكذبة.',
    hook: 'الباب كان مغلقًا من الداخل… والقهوة كانت تقول شيئًا آخر.',
    mood: 'crime',
    characters: [
      { id: 'samir', name: 'المحقق سمير', role: 'المحقق', look: 'رجل أربعيني بمعطف داكن وقبعة' },
      { id: 'secretary', name: 'السكرتيرة نادية', role: 'المشتبه بها', look: 'امرأة شابة بنظارات وملف في يدها' },
    ],
    scenes: [
      T('في الثامنة صباحًا… وُجد رجل الأعمال كمال ميتًا في مكتبه، والباب مغلق من الداخل.', 'مكتب فخم مظلم، باب مغلق، شرطة', 'dark luxury office interior with locked door, police tape, cinematic, crime scene', { sfx: 'rain', motion: 'zoomIn', camera: 'wide shot', text: 'غرفة مغلقة من الداخل' }),
      T('السكرتيرة نادية قالت إنها غادرت في السادسة مساءً… وتركته حيًا يشرب قهوته.', 'امرأة بنظارات تتحدث إلى محقق في ممر مكتب', 'stick figure woman with glasses talking to detective in office corridor, noir lighting', { chars: ['secretary', 'samir'], sfx: 'clock', motion: 'panLeft' }),
      T('اقترب المحقق سمير من المكتب… ولمس فنجان القهوة.', 'يد محقق تقترب من فنجان قهوة على مكتب', 'detective hand touching coffee cup on desk, noir, close up, crime', { chars: ['samir'], sfx: 'clock', motion: 'zoomIn', camera: 'extreme close-up' }),
      T('[nervous] كان الفنجان باردًا… لكن طبقة الحليب فوقه لم تتجمد بعد.', 'فنجان قهوة عليه طبقة حليب، ضوء مصباح مكتب', 'coffee cup with fresh milk foam under desk lamp light, detective noir', { sfx: 'heartbeat', motion: 'zoomIn', camera: 'macro shot', text: 'الحليب لم يتجمد' }),
      T('القهوة بالحليب تكوّن قشرة خلال ساعات… وهذه بلا قشرة. أي أنها صُبت قبل أقل من ساعة.', 'محقق يفكر وخلفه لوحة أدلة', 'stick figure detective thinking in front of evidence board with red strings', { chars: ['samir'], sfx: 'clock', motion: 'panRight', camera: 'medium shot' }),
      T('إذن كمال لم يكن وحيدًا الليلة الماضية… أحدهم صنع له قهوة هذا الصباح.', 'ممر مكتب مظلم وظل شخص يحمل فنجانًا', 'dark office corridor, shadow of a person carrying coffee cup, noir', { sfx: 'footsteps', motion: 'zoomOut' }),
      T('سأل سمير: من يملك نسخة من مفتاح المكتب؟ تجمّدت نادية… ثم سقط الملف من يدها.', 'امرأة مصدومة يسقط ملف من يدها', 'stick figure woman shocked dropping file folder, papers flying, detective watching', { chars: ['secretary', 'samir'], sfx: 'stinger', motion: 'shake', camera: 'close-up', text: 'من يملك المفتاح؟' }),
      T('الكذبة لم يكشفها مفتاح ولا كاميرا… كشفها فنجان قهوة بارد.', 'فنجان قهوة وحيد على مكتب مع ضوء خافت', 'single coffee cup on desk dim light, cinematic noir ending', { sfx: 'rain', motion: 'zoomOut', camera: 'wide shot' }),
    ],
    riddle: null,
    cta: 'هل لاحظت الدليل قبل المحقق؟ أخبرنا في التعليقات.',
  },
  riddle: {
    title: 'لغز المصعد',
    logline: 'رجل يسكن في الطابق العاشر لكنه يصعد بالمصعد إلى السابع فقط ثم يكمل على الدرج… لماذا؟',
    hook: 'لغز حيّر 90% من الناس… هل أنت من الـ 10%؟',
    mood: 'riddle',
    characters: [{ id: 'man', name: 'الرجل', role: 'صاحب اللغز', look: 'رجل قصير القامة بمعطف ومظلة' }],
    scenes: [
      T('لغز حيّر تسعين بالمئة من الناس… هل أنت من العشرة بالمئة؟', 'علامة استفهام عملاقة متوهجة في الظلام', 'giant glowing question mark in darkness, mysterious purple light, riddle', { sfx: 'stinger', motion: 'zoomIn', camera: 'wide shot', text: '90% فشلوا' }),
      T('رجل يسكن في الطابق العاشر من عمارة قديمة.', 'عمارة قديمة ليلًا ونوافذ مضيئة', 'old apartment building at night with lit windows, mysterious', { sfx: 'wind', motion: 'panLeft', camera: 'wide shot' }),
      T('كل صباح… يركب المصعد من الطابق العاشر وينزل إلى الأرضي مباشرة.', 'رجل يدخل مصعدًا قديمًا', 'stick figure man entering an old elevator, dim light', { chars: ['man'], sfx: 'clock', motion: 'zoomIn' }),
      T('لكن في المساء… يركب المصعد إلى الطابق السابع فقط، ثم يصعد بقية الطريق على الدرج.', 'رجل يصعد درجًا مظلمًا', 'stick figure man climbing dark staircase, mysterious', { chars: ['man'], sfx: 'footsteps', motion: 'panRight' }),
      T('إلا في الأيام الممطرة… أو عندما يكون معه أحد، فإنه يصعد مباشرة إلى العاشر.', 'رجل يحمل مظلة في المطر', 'stick figure man holding umbrella in rain at night', { chars: ['man'], sfx: 'rain', motion: 'zoomIn', text: 'لماذا؟' }),
      T('[whispers] فكّر جيدًا… لماذا يفعل ذلك؟ لديك خمس ثوانٍ.', 'ساعة رملية وعلامة استفهام', 'hourglass and question mark, countdown, purple glow', { sfx: 'clock', motion: 'still', camera: 'close-up', text: '⏳ 5 ثوانٍ' }),
      T('الحل: الرجل قصير القامة! لا يصل إلا إلى زر الطابق السابع.', 'رجل قصير يمد يده نحو أزرار المصعد', 'short stick figure man reaching up to elevator buttons, cannot reach top button', { chars: ['man'], sfx: 'stinger', motion: 'zoomIn', camera: 'close-up', text: 'الحل!' }),
      T('وفي الأيام الممطرة يضغط الزر بمظلته… ومع أي شخص آخر يطلب منه المساعدة.', 'رجل يضغط زر المصعد بمظلته', 'stick figure man pressing elevator button with umbrella tip, clever', { chars: ['man'], sfx: 'wind', motion: 'zoomOut' }),
    ],
    riddle: { question: 'لماذا يصعد الرجل إلى الطابق السابع فقط؟', answer: 'لأنه قصير ولا يصل إلا إلى زر السابع', explanation: 'المظلة تساعده في الأيام الممطرة، والآخرون يضغطون له الزر.' },
    cta: 'هل حللته قبل الإجابة؟ اكتب "حليته" في التعليقات!',
  },
};

export const DEMO_SEO = {
  horror: {
    titles: ['لا تردّ على هذا النداء أبدًا… قصة رعب من الريف 😱', 'سمع صوت زوجته المتوفاة في الغيط… والنهاية صادمة', 'النداهة: لماذا لا يجب أن تلتفت خلفك ليلًا؟'],
    description: 'قصة رعب قصيرة مستوحاة من الفلكلور الشعبي عن أب وابنته وصوت غامض في حقول القصب.\n\nاشترك لتصلك قصص رعب جديدة كل يوم.',
    tags: ['قصص رعب', 'النداهة', 'رعب', 'قصص مرعبة', 'فلكلور', 'horror story', 'رعب مصري'],
    hashtags: ['#قصص_رعب', '#رعب', '#shorts'],
    thumbnailText: 'لا تردّ!',
  },
  crime: {
    titles: ['فنجان قهوة كشف جريمة الغرفة المغلقة ☕🔍', 'الجريمة التي حلّها المحقق بلمسة واحدة', 'هل تلاحظ الدليل قبل المحقق؟'],
    description: 'لغز جريمة في غرفة مغلقة من الداخل… والدليل الحاسم كان أبسط مما تتخيل.\n\nاشترك لمزيد من قصص الجريمة والتحقيق.',
    tags: ['جريمة', 'قصص جريمة', 'تحقيق', 'غرفة مغلقة', 'لغز جريمة', 'true crime عربي'],
    hashtags: ['#جريمة', '#تحقيق', '#shorts'],
    thumbnailText: 'القهوة فضحته',
  },
  riddle: {
    titles: ['لغز المصعد الذي حيّر 90% من الناس 🧠', 'لماذا يتوقف عند الطابق السابع؟ لغز ذكاء', 'لو حليت هذا اللغز فأنت عبقري'],
    description: 'لغز ذكاء ممتع: رجل يسكن في الطابق العاشر لكنه يصعد للسابع فقط… هل تعرف السبب؟\n\nاكتب إجابتك قبل مشاهدة الحل!',
    tags: ['ألغاز', 'لغز', 'ألغاز ذكاء', 'ألغاز صعبة', 'ألغاز مع الحل', 'riddle'],
    hashtags: ['#ألغاز', '#لغز', '#shorts'],
    thumbnailText: 'لماذا السابع؟',
  },
};
