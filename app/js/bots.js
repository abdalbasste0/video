// فريق العمل: 10 روبوتات، لكل واحد مهمة محددة، يديرهم "المدير التنفيذي" في خط إنتاج واحد
import { Store, Settings } from './store.js';
import { claudeJSON, hasClaude, obj, str, num, arr, en, generateImage, synthesizeSpeech, hasVoice } from './ai.js';
import { DEMO_SCRIPTS, DEMO_SEO, IDEA_BANK, NICHES } from './demo.js';
import { decodeBlob, estimateDuration, buildMix, SFX } from './audio.js';
import { prepareState, renderVideo, renderThumbnail } from './render.js';
import { notifyReview } from './publish.js';

export const BOTS = [
  { id: 'director', icon: '🎬', name: 'المدير التنفيذي', job: 'يخطط الإنتاج، يوزع المهام، ويجري فحص الجودة النهائي قبل إرسال العمل لك' },
  { id: 'scout', icon: '📡', name: 'باحث الترندات', job: 'يقترح 5 أفكار في النيش، يقيّم قوة كل فكرة، ويختار الأقوى بدون تكرار' },
  { id: 'writer', icon: '✍️', name: 'كاتب السيناريو', job: 'يكتب سيناريو بخطّاف قوي ونقاط احتفاظ ونهاية صادمة مع وسوم نبرة للمعلق' },
  { id: 'critic', icon: '🧐', name: 'الناقد', job: 'يقيّم السيناريو على 8 معايير ويعيده للكاتب حتى يتجاوز حد الجودة' },
  { id: 'art', icon: '🎨', name: 'المخرج الفني', job: 'يبني دليل الأسلوب وبطاقات الشخصيات ووصف كل لقطة وزاوية الكاميرا' },
  { id: 'painter', icon: '🖼️', name: 'الرسام', job: 'يولّد صور المشاهد بشخصيات ثابتة الملامح ويعيد المحاولة عند الفشل' },
  { id: 'voice', icon: '🎙️', name: 'المعلق الصوتي', job: 'يسجل التعليق مشهدًا بمشهد بنبرة مناسبة (همس، توتر، صدمة)' },
  { id: 'sound', icon: '🎧', name: 'مهندس الصوت', job: 'يؤلف موسيقى تصويرية ومؤثرات لكل مشهد ويخفض الموسيقى تلقائيًا تحت الصوت' },
  { id: 'editor', icon: '🎞️', name: 'المونتير', job: 'يركّب الفيديو: حركة كاميرا، انتقالات، ترجمة كلمة بكلمة، عدّاد الألغاز، خاتمة' },
  { id: 'publisher', icon: '🚀', name: 'خبير النشر', job: 'يكتب العناوين والوصف والوسوم ويصمم الصورة المصغرة وينشر بعد موافقتك' },
];

export const DIALECTS = {
  msa: 'العربية الفصحى المبسطة',
  eg: 'اللهجة المصرية العامية',
  gulf: 'اللهجة الخليجية',
  levant: 'اللهجة الشامية',
  maghreb: 'اللهجة المغربية/الدارجة',
  en: 'English',
};

export const STAGES = ['research', 'script', 'art', 'images', 'voice', 'sound', 'edit', 'seo', 'qa'];
const STAGE_BOT = { research: 'scout', script: 'writer', art: 'art', images: 'painter', voice: 'voice', sound: 'sound', edit: 'editor', seo: 'publisher', qa: 'director' };

// ---------- shared prompt material ----------
const NICHE_GUIDE = {
  horror: 'قصص رعب نفسي وفلكلوري: توتر متصاعد، تفاصيل حسية (أصوات، ظلال، روائح)، كيان غامض لا يُكشف بالكامل، ونهاية بتحوّل صادم (twist) يترك المشاهد قلقًا. تجنب الدم المفرط؛ الرعب في الإيحاء.',
  crime: 'عالم الجريمة والتحقيق: قضية بغرفة مغلقة أو دليل صغير حاسم، مشتبهون، تسلسل منطقي يمكن للمشاهد تتبعه، وكشف ذكي في النهاية. إذا كانت القضية حقيقية فالتزم بالوقائع الموثقة ولا تخترع أسماء أو تفاصيل عن أشخاص حقيقيين؛ والأفضل قصص خيالية مستوحاة من أنماط جرائم شهيرة مع الإشارة لذلك.',
  riddle: 'ألغاز ذكاء وغموض: اعرض اللغز بقصة قصيرة مشوقة، أعطِ كل المعلومات اللازمة للحل بعدل، ثم مشهد "فكّر" مع عدّاد تنازلي (countdown 5 ثوانٍ)، ثم الحل وشرحه، ثم دعوة للتعليق. الحل يجب أن يكون منطقيًا ومفاجئًا ومتسقًا مع المعطيات.',
};

function formatSpec(brief) {
  if (brief.format === 'short') return { scenes: '8 إلى 10', words: '130 إلى 170', seconds: 60, label: 'Short عمودي 9:16 مدته ~60 ثانية' };
  const m = Math.max(2, Math.min(15, Number(brief.minutes) || 5));
  return { scenes: `${m * 7} إلى ${m * 9}`, words: `${m * 125} إلى ${m * 145}`, seconds: m * 60, label: `فيديو طويل أفقي 16:9 مدته ~${m} دقائق` };
}

const SCRIPT_SCHEMA = obj({
  title: str('عنوان داخلي قصير'),
  logline: str('ملخص القصة في جملة'),
  hook: str('أول جملة تُقال — يجب أن تشد في أول 3 ثوانٍ'),
  mood: en(['horror', 'crime', 'riddle']),
  characters: arr(obj({ id: str('معرّف لاتيني قصير'), name: str(), role: str(), look: str('وصف بصري ثابت للشخصية') })),
  scenes: arr(obj({
    narration: str('نص التعليق لهذا المشهد مع وسوم نبرة إنجليزية بين أقواس مربعة مثل [whispers] [nervous] [scared] [dramatic pause] [excited]'),
    onScreenText: str('نص قصير جدًا يظهر على الشاشة أو فارغ'),
    visual: str('وصف بصري عربي للمشهد'),
    camera: str('زاوية/حجم اللقطة'),
    characters: arr(str(), 'معرّفات الشخصيات الظاهرة'),
    sfx: en(SFX),
    motion: en(['zoomIn', 'zoomOut', 'panLeft', 'panRight', 'shake', 'still']),
    countdown: num('عدد ثواني العدّاد بعد التعليق (0 إن لم يوجد؛ 5 لمشهد التفكير في الألغاز)'),
  })),
  riddle: obj({ question: str(), answer: str(), explanation: str() }),
  cta: str('دعوة ختامية للتفاعل'),
});

// ---------- pipeline ----------
const running = new Map();

export function isRunning(id) { return running.has(id); }
export function stopProject(id) { running.get(id)?.abort(); }

function log(p, bot, msg, level = 'info') {
  p.log.push({ t: Date.now(), bot, msg, level });
}
function setBot(p, bot, state) { p.bots[bot] = state; }

export function newProject(brief) {
  return {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    createdAt: Date.now(),
    status: 'queued',
    brief,
    seed: Math.floor(Math.random() * 1e6),
    log: [],
    bots: Object.fromEntries(BOTS.map((b) => [b.id, 'idle'])),
    stage: 'research',
    progress: 0,
    feedback: [],
  };
}

export async function runPipeline(project, { from } = {}) {
  const p = project;
  const ctrl = new AbortController();
  running.set(p.id, ctrl);
  const signal = ctrl.signal;
  const demo = !hasClaude();
  const startIdx = Math.max(0, STAGES.indexOf(from || p.stage || 'research'));
  delete p.resumeFrom;
  p.status = 'working';
  p.error = null;
  STAGES.slice(startIdx).forEach((s) => setBot(p, STAGE_BOT[s], 'idle'));
  setBot(p, 'director', 'working');
  if (startIdx === 0) {
    log(p, 'director', `بدأ الإنتاج: ${NICHES[p.brief.niche].label} — ${formatSpec(p.brief).label} — ${DIALECTS[p.brief.dialect]}`);
    if (demo) log(p, 'director', 'لا يوجد مفتاح Claude: الفريق يعمل بالوضع التجريبي (قصص جاهزة). أضف المفتاح من الإعدادات لإنتاج قصص جديدة كليًا.', 'warn');
  } else {
    log(p, 'director', `إعادة الإنتاج من مرحلة: ${from}`);
  }
  await Store.saveProject(p);

  try {
    for (let i = startIdx; i < STAGES.length; i++) {
      if (signal.aborted) throw new DOMException('aborted', 'AbortError');
      const stage = STAGES[i];
      const bot = STAGE_BOT[stage];
      p.stage = stage;
      p.progress = i / STAGES.length;
      setBot(p, bot, 'working');
      await Store.saveProject(p);
      await STAGE_FN[stage](p, { demo, signal, save: () => Store.saveProject(p) });
      setBot(p, bot, 'done');
      await Store.saveProject(p);
    }
    p.progress = 1;
    p.stage = 'review';
    p.status = 'review';
    setBot(p, 'director', 'done');
    log(p, 'director', 'اكتمل الإنتاج وأُرسل العمل إليك للمراجعة. لن يُنشر شيء قبل موافقتك ✅');
    await Store.saveProject(p);
    notifyReview(p).then((r) => r && log(p, 'publisher', r)).then(() => Store.saveProject(p)).catch((e) => {
      log(p, 'publisher', 'تعذر إرسال الإشعار: ' + e.message, 'warn'); Store.saveProject(p);
    });
  } catch (e) {
    const aborted = e?.name === 'AbortError';
    p.status = aborted ? 'stopped' : 'error';
    p.error = aborted ? 'أوقفته أنت' : String(e?.message || e);
    setBot(p, STAGE_BOT[p.stage] || 'director', aborted ? 'idle' : 'error');
    log(p, 'director', aborted ? 'تم إيقاف الإنتاج.' : 'توقف الإنتاج بسبب خطأ: ' + p.error, aborted ? 'warn' : 'error');
    await Store.saveProject(p);
  } finally {
    running.delete(p.id);
  }
  return p;
}

// ---------- stages ----------
const STAGE_FN = {
  async research(p, { demo }) {
    const niche = p.brief.niche;
    if (p.brief.topic?.trim()) {
      p.idea = { title: p.brief.topic.trim(), angle: p.brief.notes || '', hook: '', why: 'فكرة من صاحب القناة', score: 10 };
      log(p, 'scout', `اعتمدت فكرتك: «${p.idea.title}»`);
      return;
    }
    if (demo) {
      const s = DEMO_SCRIPTS[niche];
      p.idea = { title: s.title, angle: s.logline, hook: s.hook, why: 'قصة جاهزة من بنك الوضع التجريبي', score: 8.5 };
      p.ideas = IDEA_BANK[niche].map((t) => ({ title: t, score: 0 }));
      log(p, 'scout', `اخترت: «${p.idea.title}»`);
      return;
    }
    const history = (await Store.listProjects()).filter((x) => x.id !== p.id && x.idea).map((x) => x.idea.title).slice(0, 40);
    const res = await claudeJSON({
      effort: 'medium',
      maxTokens: 16000,
      system: 'أنت باحث ترندات محترف لقنوات يوتيوب وتيك توك العربية. تعرف ما يحقق ملايين المشاهدات في نيش الرعب والجريمة والألغاز: الخطّاف، الفضول، الفلكلور المحلي، الحالات الغامضة.',
      prompt: `النيش: ${NICHES[niche].label}\n${NICHE_GUIDE[niche]}\nالصيغة: ${formatSpec(p.brief).label}\nاللغة: ${DIALECTS[p.brief.dialect]}\nملاحظات صاحب القناة: ${p.brief.notes || 'لا يوجد'}\n\nعناوين أنتجناها سابقًا (لا تكررها ولا تقترب منها):\n${history.join('\n') || 'لا يوجد'}\n\nاقترح 5 أفكار أصلية عالية الانتشار، قيّم كل واحدة من 10 (فضول + قابلية المشاركة + ملاءمة الصيغة)، واختر الأفضل في pick (رقم الفهرس من 0).`,
      schema: obj({ ideas: arr(obj({ title: str(), angle: str(), hook: str(), why: str(), score: num() })), pick: num() }),
    });
    p.ideas = res.ideas;
    p.idea = res.ideas[Math.max(0, Math.min(res.ideas.length - 1, Math.round(res.pick) || 0))];
    log(p, 'scout', `درست 5 أفكار واخترت «${p.idea.title}» (${p.idea.score}/10): ${p.idea.why}`);
  },

  async script(p, { demo, save }) {
    const s = Settings.get();
    const threshold = Number(s.qualityThreshold) || 8.5;
    const maxRounds = Math.max(0, Number(s.maxRevisions) || 0);
    if (demo) {
      p.script = structuredClone(DEMO_SCRIPTS[p.brief.niche]);
      p.script.scenes.forEach((sc) => { sc.countdown = sc.onScreenText?.includes('⏳') ? 5 : 0; });
      log(p, 'writer', `كتبت السيناريو: ${p.script.scenes.length} مشاهد.`);
      setBot(p, 'critic', 'working'); await save();
      p.critique = heuristicCritique(p.script);
      log(p, 'critic', `التقييم ${p.critique.average.toFixed(1)}/10 — ${p.critique.notes[0]}`);
      setBot(p, 'critic', 'done');
      return;
    }
    const spec = formatSpec(p.brief);
    const feedback = p.feedback.filter((f) => !f.used).map((f) => f.text);
    const system = `أنت كاتب سيناريو محترف لقنوات ${NICHES[p.brief.niche].label} تحقق ملايين المشاهدات. تكتب للأذن قبل العين: جمل قصيرة، إيقاع متوتر، صور حسية، ونقاط احتفاظ (open loops) كل 15-20 ثانية.\n${NICHE_GUIDE[p.brief.niche]}\nقواعد صارمة:\n- اكتب السرد بـ${DIALECTS[p.brief.dialect]} بدقة وطبيعية.\n- أول جملة هي الخطّاف ويجب أن تثير سؤالًا لا يُجاب إلا في النهاية.\n- كل مشهد = لقطة بصرية واحدة واضحة يمكن رسمها، مع جملة أو جملتين سرد فقط.\n- استخدم وسوم النبرة الإنجليزية بين أقواس مربعة في narration حيث تفيد ([whispers], [nervous], [scared], [dramatic pause], [shouting]) دون مبالغة.\n- اجعل الشخصيات قليلة وثابتة، ولكل شخصية وصف بصري واحد ثابت.\n- اختر sfx وmotion مناسبة لكل مشهد (shake للحظات الصدمة، zoomIn للتوتر).\n- إن لم يكن لغزًا: املأ riddle بنصوص فارغة.`;
    let prompt = `الفكرة: ${p.idea.title}\nالزاوية: ${p.idea.angle}\nالخطّاف المقترح: ${p.idea.hook}\nالصيغة: ${spec.label}\nعدد المشاهد: ${spec.scenes}\nإجمالي كلمات السرد: ${spec.words} كلمة.\n${p.brief.notes ? 'ملاحظات صاحب القناة: ' + p.brief.notes + '\n' : ''}${feedback.length ? '\nملاحظات صاحب القناة على النسخة السابقة (أولوية قصوى):\n- ' + feedback.join('\n- ') + '\n' : ''}${p.script ? '\nالنسخة السابقة للمراجعة:\n' + JSON.stringify(p.script) : ''}`;

    let round = 0;
    for (;;) {
      log(p, 'writer', round === 0 ? 'أكتب السيناريو…' : `أعيد الكتابة (الجولة ${round + 1}) بناءً على ملاحظات الناقد…`);
      await save();
      p.script = await claudeJSON({ system, prompt, schema: SCRIPT_SCHEMA, effort: 'high', maxTokens: 64000 });
      p.script.mood = p.brief.niche;
      log(p, 'writer', `سيناريو «${p.script.title}»: ${p.script.scenes.length} مشهد.`);
      setBot(p, 'critic', 'working'); await save();
      p.critique = await critique(p);
      p.critique.rounds = round + 1;
      log(p, 'critic', `التقييم ${p.critique.average.toFixed(1)}/10 (الحد المطلوب ${threshold}). ${p.critique.verdict === 'pass' ? 'مقبول ✅' : 'يحتاج تحسين'}`);
      setBot(p, 'critic', 'done');
      if (p.critique.average >= threshold || round >= maxRounds) break;
      prompt = `حسّن هذا السيناريو بناءً على ملاحظات الناقد مع الحفاظ على نقاط قوته.\nالملاحظات:\n- ${p.critique.notes.join('\n- ')}\nنقاط القوة:\n- ${p.critique.strengths.join('\n- ')}\nالسيناريو الحالي:\n${JSON.stringify(p.script)}\nالصيغة: ${spec.label}، عدد المشاهد ${spec.scenes}، الكلمات ${spec.words}.`;
      round++;
      setBot(p, 'writer', 'working');
    }
    p.feedback.forEach((f) => (f.used = true));
    if (p.critique.average < threshold) log(p, 'critic', 'لم يصل للحد بعد كل الجولات؛ سأُعلِم صاحب القناة في تقرير الجودة.', 'warn');
  },

  async art(p, { demo }) {
    const sc = p.script;
    if (demo || !hasClaude()) {
      p.art = {
        styleBible: 'dark cinematic 2D illustration, simple stick-figure characters, moody volumetric lighting, film grain, high contrast',
        characterSheets: sc.characters.map((c) => ({ id: c.id, prompt: c.look })),
        scenes: sc.scenes.map((s) => ({ imagePrompt: s.imagePrompt || s.visual })),
        thumbnail: { imagePrompt: (sc.scenes.find((s) => s.sfx === 'stinger') || sc.scenes[0]).imagePrompt || sc.scenes[0].visual, text: DEMO_SEO[p.brief.niche]?.thumbnailText || sc.title, badge: '' },
      };
      log(p, 'art', 'جهزت دليل الأسلوب ووصف اللقطات.');
      return;
    }
    const res = await claudeJSON({
      effort: 'medium',
      maxTokens: 32000,
      system: 'You are an art director for viral faceless YouTube story channels (horror, true-crime, riddles). You write image-generation prompts in English that keep characters visually consistent across scenes, use strong cinematic composition, varied camera angles, dramatic lighting and a coherent colour palette. Never include text/letters in images.',
      prompt: `Niche: ${p.brief.niche}. Aspect: ${p.brief.format === 'short' ? '9:16 vertical' : '16:9 horizontal'}.
Write: (1) a one-paragraph style bible (art style, palette, lighting, texture) suited to the niche — default to "dark cinematic 2D illustration with simple stick-figure characters" unless the owner notes request otherwise; (2) a compact, reusable visual description for each character (same id); (3) one image prompt per scene, in the SAME ORDER and SAME COUNT (${sc.scenes.length}) as the scenes, each describing subject, action, setting, camera angle/shot size, lighting and mood — mention characters by their visual description, not by name; (4) a thumbnail concept: image prompt with one striking focal subject + 2-4 word Arabic overlay text + optional short badge.
Owner notes: ${p.brief.notes || 'none'}
Script JSON:
${JSON.stringify({ characters: sc.characters, scenes: sc.scenes.map((s) => ({ visual: s.visual, camera: s.camera, characters: s.characters })) })}`,
      schema: obj({
        styleBible: str(),
        characterSheets: arr(obj({ id: str(), prompt: str() })),
        scenes: arr(obj({ imagePrompt: str() })),
        thumbnail: obj({ imagePrompt: str(), text: str(), badge: str() }),
      }),
    });
    while (res.scenes.length < sc.scenes.length) res.scenes.push({ imagePrompt: sc.scenes[res.scenes.length].visual });
    p.art = res;
    log(p, 'art', `دليل الأسلوب جاهز + ${res.characterSheets.length} بطاقات شخصيات + ${res.scenes.length} لقطة.`);
  },

  async images(p, { signal, save }) {
    const { W, H } = dims(p);
    const sc = p.script.scenes;
    const sheets = Object.fromEntries((p.art.characterSheets || []).map((c) => [c.id, c.prompt]));
    p.images = p.images && p.images.length === sc.length ? p.images : sc.map(() => null);
    const jobs = sc.map((s, i) => async () => {
      if (signal.aborted) return;
      const chars = (s.characters || []).map((id) => sheets[id]).filter(Boolean).join('; ');
      const prompt = `${p.art.scenes[i].imagePrompt}. ${chars ? 'Characters: ' + chars + '. ' : ''}Style: ${p.art.styleBible}. No text, no watermark.`;
      let blob;
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          blob = await generateImage({ prompt, width: W, height: H, seed: p.seed + attempt * 101, hint: `${s.visual} ${p.art.scenes[i].imagePrompt}` });
          break;
        } catch (e) {
          if (attempt === 2) throw e;
        }
      }
      const key = `${p.id}/img/${i}`;
      await Store.putBlob(key, blob);
      p.images[i] = { imgKey: key, fallback: blob.fallback || null };
      log(p, 'painter', `رسمت المشهد ${i + 1}/${sc.length}${blob.fallback ? ' (بالرسام الاحتياطي)' : ''}`);
      await save();
    });
    // thumbnail base image in parallel
    jobs.push(async () => {
      const prompt = `${p.art.thumbnail.imagePrompt}. Style: ${p.art.styleBible}. Dramatic, high contrast, single focal subject, no text.`;
      const tw = p.brief.format === 'short' ? 1080 : 1280, th = p.brief.format === 'short' ? 1920 : 720;
      const blob = await generateImage({ prompt, width: tw, height: th, seed: p.seed + 7, hint: p.art.thumbnail.imagePrompt });
      await Store.putBlob(`${p.id}/thumbbase`, blob);
      p.thumbBaseKey = `${p.id}/thumbbase`;
    });
    await pool(jobs, 3);
    if (signal.aborted) throw new DOMException('aborted', 'AbortError');
    const fb = p.images.filter((x) => x?.fallback).length;
    if (fb) log(p, 'painter', `${fb} صورة رُسمت بالرسام الاحتياطي لتعذر مزود الصور. يمكنك إعادة توليد الصور من المراجعة.`, 'warn');
  },

  async voice(p, { signal, save }) {
    const sc = p.script.scenes;
    p.voice = sc.map(() => null);
    if (!hasVoice()) {
      log(p, 'voice', 'لا يوجد مفتاح ElevenLabs: الفيديو سيعتمد على الترجمة النصية والموسيقى بدون تعليق صوتي. أضف المفتاح لتعليق بشري الجودة.', 'warn');
      return;
    }
    const jobs = sc.map((s, i) => async () => {
      if (signal.aborted) return;
      let blob;
      for (let attempt = 0; ; attempt++) {
        try { blob = await synthesizeSpeech(s.narration); break; } catch (e) { if (attempt >= 2) throw e; await sleep(1500 * (attempt + 1)); }
      }
      const key = `${p.id}/voice/${i}`;
      await Store.putBlob(key, blob);
      const buf = await decodeBlob(blob);
      p.voice[i] = { audioKey: key, duration: buf.duration };
      log(p, 'voice', `سجلت المشهد ${i + 1}/${sc.length} (${buf.duration.toFixed(1)} ث)`);
      await save();
    });
    await pool(jobs, 2);
  },

  async sound(p) {
    const timeline = await buildTimeline(p);
    const mix = await buildMix({ timeline, mood: p.script.mood || p.brief.niche, total: p.total, seed: p.seed % 1000 });
    mem(p).mix = mix; // in-memory only (AudioBuffer can't be stored)
    log(p, 'sound', `ألفت موسيقى ${NICHES[p.brief.niche].label} (${p.total.toFixed(0)} ث) + ${timeline.filter((t) => t.sfx !== 'none').length} مؤثر، مع خفض تلقائي تحت التعليق.`);
  },

  async edit(p, { signal, save }) {
    const { W, H } = dims(p);
    const timeline = mem(p).timeline || (await buildTimeline(p));
    const mix = mem(p).mix || (await buildMix({ timeline, mood: p.script.mood || p.brief.niche, total: p.total, seed: p.seed % 1000 }));
    const images = await Promise.all(p.images.map(async (im) => (im ? createImageBitmap(await Store.getBlob(im.imgKey)) : null)));
    const st = await prepareState({
      W, H, timeline, images, mood: p.script.mood || p.brief.niche, total: p.total,
      outro: { start: p.total - OUTRO }, channel: Settings.get().channelName, cta: p.script.cta,
    });
    log(p, 'editor', `أركّب الفيديو ${W}×${H}… (يستغرق مثل مدة الفيديو تقريبًا؛ أبقِ التطبيق مفتوحًا)`);
    await save();
    let lastSave = 0;
    const blob = await renderVideo({
      st, mix, signal,
      onProgress: (x) => {
        p.renderProgress = x;
        if (Date.now() - lastSave > 1500) { lastSave = Date.now(); save(); }
      },
    });
    if (!blob) throw new DOMException('aborted', 'AbortError');
    await Store.putBlob(`${p.id}/video`, blob);
    p.videoKey = `${p.id}/video`;
    p.videoType = blob.type;
    p.videoSize = blob.size;
    MEM.delete(p.id);
    log(p, 'editor', `الفيديو جاهز: ${(blob.size / 1048576).toFixed(1)} ميجابايت (${blob.type}).`);
  },

  async seo(p, { demo }) {
    if (demo) {
      p.seo = { ...structuredClone(DEMO_SEO[p.brief.niche]), pinnedComment: p.script.cta, bestPostTime: '8–10 مساءً بتوقيت جمهورك' };
    } else {
      p.seo = await claudeJSON({
        effort: 'medium',
        maxTokens: 16000,
        system: 'أنت خبير نمو قنوات يوتيوب وتيك توك العربية (SEO، نسبة النقر CTR، العناوين، الصور المصغرة). تكتب عناوين فضولية صادقة غير مضللة، بحد أقصى 70 حرفًا، وتضع الكلمة المفتاحية في البداية.',
        prompt: `اكتب حزمة النشر لهذا الفيديو (${formatSpec(p.brief).label}، ${DIALECTS[p.brief.dialect]}).\nالقصة: ${p.script.logline}\nالخطّاف: ${p.script.hook}\nالنيش: ${NICHES[p.brief.niche].label}\nالمطلوب: 3 عناوين مرتبة من الأقوى، وصف (3-5 أسطر + دعوة للاشتراك)، 10-15 وسمًا، 3-5 هاشتاج${p.brief.format === 'short' ? ' منها #shorts' : ''}، نص صورة مصغرة 2-4 كلمات، تعليق مثبت يحفز النقاش، وأفضل وقت للنشر.`,
        schema: obj({ titles: arr(str()), description: str(), tags: arr(str()), hashtags: arr(str()), thumbnailText: str(), pinnedComment: str(), bestPostTime: str() }),
      });
    }
    // thumbnail
    const base = p.thumbBaseKey ? await Store.getBlob(p.thumbBaseKey) : null;
    const img = base ? await createImageBitmap(base) : null;
    const short = p.brief.format === 'short';
    const thumb = await renderThumbnail({
      image: img, text: p.seo.thumbnailText || p.art?.thumbnail?.text, mood: p.brief.niche,
      W: short ? 1080 : 1280, H: short ? 1920 : 720, badge: p.art?.thumbnail?.badge || '',
    });
    await Store.putBlob(`${p.id}/thumb`, thumb);
    p.thumbKey = `${p.id}/thumb`;
    p.publish = { title: p.seo.titles[0], description: [p.seo.description, '', p.seo.hashtags.join(' ')].join('\n'), tags: p.seo.tags };
    log(p, 'publisher', `جهزت 3 عناوين ووصفًا و${p.seo.tags.length} وسمًا وصورة مصغرة. العنوان المقترح: «${p.seo.titles[0]}»`);
  },

  async qa(p) {
    const checks = [];
    const add = (ok, label) => checks.push({ ok, label });
    const s = Settings.get();
    add(p.images?.every(Boolean), 'كل المشاهد لها صور');
    add(!p.images?.some((x) => x?.fallback), 'كل الصور من مزود الصور الأساسي');
    add(p.voice?.some(Boolean), 'التعليق الصوتي موجود');
    add((p.critique?.average || 0) >= (Number(s.qualityThreshold) || 8.5), `جودة السيناريو ≥ ${s.qualityThreshold}`);
    const target = formatSpec(p.brief).seconds;
    add(Math.abs(p.total - target) / target <= 0.35, `المدة ${p.total.toFixed(0)} ث قريبة من الهدف ${target} ث`);
    add((p.publish?.title || '').length <= 70, 'العنوان ≤ 70 حرفًا');
    add(p.videoSize > 100000, 'ملف الفيديو سليم');
    add(p.brief.format !== 'short' || p.total <= 180, 'مدة Short ضمن حد يوتيوب (3 دقائق)');
    const score = Math.round((checks.filter((c) => c.ok).length / checks.length) * 100);
    p.qa = { checks, score };
    log(p, 'director', `فحص الجودة: ${score}% (${checks.filter((c) => !c.ok).map((c) => '✗ ' + c.label).join('، ') || 'كل البنود ناجحة'})`, score >= 75 ? 'info' : 'warn');
  },
};

const OUTRO = 3;
const MEM = new Map();
const mem = (p) => { if (!MEM.has(p.id)) MEM.set(p.id, {}); return MEM.get(p.id); };

async function buildTimeline(p) {
  const sc = p.script.scenes;
  let t = 0.2;
  const tl = [];
  for (let i = 0; i < sc.length; i++) {
    const s = sc[i];
    let voiceBuffer = null;
    if (p.voice?.[i]) voiceBuffer = await decodeBlob(await Store.getBlob(p.voice[i].audioKey));
    const voiceDuration = voiceBuffer ? voiceBuffer.duration : estimateDuration(s.narration);
    const voiceOffset = 0.25;
    const countdown = Number(s.countdown) > 0 ? Math.min(10, Number(s.countdown)) : 0;
    const duration = Math.max(2.5, voiceOffset + voiceDuration + 0.35 + (countdown ? countdown + 0.3 : 0));
    tl.push({
      start: t, duration, voiceBuffer, voiceOffset, voiceDuration, narration: s.narration,
      sfx: countdown ? 'clock' : s.sfx, motion: s.motion, onScreenText: s.onScreenText, countdown,
      cdStart: t + voiceOffset + voiceDuration + 0.2,
    });
    t += duration;
  }
  p.total = t + OUTRO;
  mem(p).timeline = tl;
  return tl;
}

function dims(p) {
  const hq = Settings.get().renderQuality !== '720';
  if (p.brief.format === 'short') return hq ? { W: 1080, H: 1920 } : { W: 720, H: 1280 };
  return hq ? { W: 1920, H: 1080 } : { W: 1280, H: 720 };
}

function heuristicCritique(script) {
  const n = script.scenes.length;
  const scores = { hook: 9, tension: 8.5, clarity: 9, twist: 8.5, pacing: n >= 7 && n <= 12 ? 9 : 7.5, language: 9, originality: 8, retention: 8.5 };
  const vals = Object.values(scores);
  return { scores, average: vals.reduce((a, b) => a + b, 0) / vals.length, verdict: 'pass', notes: ['خطّاف قوي وإيقاع متصاعد ونهاية صادمة.'], strengths: ['مشاهد بصرية واضحة'] };
}

async function critique(p) {
  const res = await claudeJSON({
    effort: 'high',
    maxTokens: 16000,
    system: `أنت ناقد صارم ومحرر سيناريوهات لقنوات ${NICHES[p.brief.niche].label} واسعة الانتشار. معاييرك قاسية: 10 تعني "سيحقق ملايين المشاهدات". لا تجامل.`,
    prompt: `قيّم السيناريو من 10 على: hook (قوة أول 3 ثوانٍ)، tension (التوتر/الفضول)، clarity (وضوح القصة للأذن)، twist (قوة النهاية/الحل)، pacing (الإيقاع وعدد الكلمات لكل مشهد)، language (سلامة ${DIALECTS[p.brief.dialect]} وطبيعيتها)، originality، retention (نقاط الاحتفاظ). ${p.brief.niche === 'riddle' ? 'تأكد أن اللغز عادل وأن الحل منطقي ومتسق مع المعطيات.' : ''}${p.brief.niche === 'crime' ? 'تأكد ألا توجد ادعاءات مختلقة عن أشخاص حقيقيين.' : ''}\nأعطِ ملاحظات عملية محددة قابلة للتنفيذ (ماذا تغيّر وأين) ونقاط القوة.\n\nالسيناريو:\n${JSON.stringify(p.script)}`,
    schema: obj({
      scores: obj({ hook: num(), tension: num(), clarity: num(), twist: num(), pacing: num(), language: num(), originality: num(), retention: num() }),
      verdict: en(['pass', 'revise']),
      notes: arr(str()),
      strengths: arr(str()),
    }),
  });
  const vals = Object.values(res.scores).map(Number);
  res.average = vals.reduce((a, b) => a + b, 0) / vals.length;
  return res;
}

async function pool(jobs, n) {
  const queue = [...jobs];
  const workers = Array.from({ length: n }, async () => { while (queue.length) await queue.shift()(); });
  await Promise.all(workers);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
