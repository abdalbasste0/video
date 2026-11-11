// The 15 workers of the factory. Each worker owns one station of the production line.
// kind: "input"  -> waits for the producer's decision
//       "ai"     -> calls Claude
//       "local"  -> deterministic code (counting, assembling, QA, packaging)
import {
  LOCKED_CHARACTER_DESIGN,
  LOCKED_IMAGE_STYLE,
  IMAGE_CLOSER,
  THUMB_CLOSER,
  characterSheetPrompt,
  masterAnimationPrompt,
} from "./locked.js";

export const WPS = 2.5; // narration speed: words per second

export function countWords(text) {
  return (text || "")
    .split(/\s+/)
    .filter((w) => w && /[\p{L}\p{N}]/u.test(w)).length;
}

const SCRIPT_RULES = `قواعد السكريبت:
القاعدة 1 - سرد متواصل فقط. كتلة واحدة من النثر مقسمة لفقرات قصيرة. بدون عناوين فصول، بدون توجيهات كاميرا، بدون إشارات بصرية. سرد نقي فقط.
القاعدة 2 - افتتاحية باردة. أول 2-3 جمل ترمي المشاهد مباشرة في أكثر نسخة قريبة أو مفاجئة من الموضوع. ممنوع "أهلاً بيكم" أو "الفيديو ده عن". ابدأ جوه الإحساس أو الموقف فوراً.
القاعدة 3 - نبرة حوارية لكن دقيقة. جمل قصيرة سريعة مع جملة أطول توضيحية كل فترة لتنويع الإيقاع. الراوي صوته زي صاحب ذكي وصريح بيشرح حاجة حقيقية، مش واعظ ولا درامي ولا متحمس زيادة عن اللزوم.
القاعدة 4 - كل جملة تحمل فكرة واحدة واضحة ولازم تكون سهلة التخيل كمشهد بصري بشخصيات ستيك فيجر. أي جملة مش قابلة للتصوير بستيك فيجر في بيئة حقيقية تتعاد كتابتها.
القاعدة 5 - لغة بسيطة وقريبة. بدون مصطلحات معقدة ولا لغة أكاديمية. مستوى يفهمه واحد عنده 14 سنة تماماً.
القاعدة 6 - ابنِ القصة بالسبب والنتيجة. استخدم روابط زي: فـ، وده معناه، وعشان كدا، وده بالظبط السبب إن، بس هنا المفاجأة، وأول ما ده يحصل.
القاعدة 7 - ممنوع أي إعلانات، ممنوع "اشترك في القناة"، ممنوع أي نداء للتفاعل في أي مكان في السكريبت.
القاعدة 8 - اختم بجملة ختامية قوية تفضل في دماغ المشاهد. الجملة الأخيرة لازم تحس إنها استنتاج المشاهد وصله بنفسه، مش حاجة اتقالت له.`;

const DIALECTS = {
  fusha: "فصحى مبسطة قريبة من العامية المفهومة لكل الجمهور العربي",
  masri: "عامية مصرية طبيعية",
};

export const WORKERS = [
  {
    id: 1,
    name: "مستلم الطلبات",
    role: "اختيار النيتش",
    kind: "input",
    ready: (s) => !!s.niche,
  },
  {
    id: 2,
    name: "مولّد الأفكار",
    role: "15 فكرة فيديو",
    kind: "ai",
    needsChoice: (s) => !s.topic,
    async run(s, ai) {
      const out = await ai({
        brief: `Generate exactly 15 video ideas in Arabic for the given niche.
No two ideas can be in the same sub-territory. Every idea must cover a completely different angle, emotion, or situation within the niche so the full list feels like 15 different entry points into the same world.
كل عنوان لازم يتبع واحد من الأشكال دي بصياغة عربية طبيعية وجذابة: "ليه [الناس بتعمل كذا]"، "إيه اللي بيحصل لما [موقف]"، "الحقيقة [الصادمة/المخفية] عن [موضوع]"، "إزاي [موضوع] بيشتغل فعلاً"، "ليه [موضوع] [بيعمل كذا] وتعمل إيه في الموقف ده"، "السبب الحقيقي ورا [موقف]"، "اللي محدش بيقولهولك عن [موضوع]"، "إزاي [موضوع] بيغير كل حاجة"، "[رقم] حاجات [الجمهور] عمره ما لاحظها عن [موضوع]"، "الـ[موضوع] اللي [نتيجة مفاجئة]".
كل عنوان لازم يكون مرتبط بخطاف واقعي قريب من حياة المشاهد المصري والعربي. ممنوع الكليك بيت، ممنوع علامات التعجب، ممنوع الكلام المبالغ فيه زي "صادم" أو "جنوني" أو "هيفجر دماغك".
Return JSON: {"ideas": [15 Arabic titles]}.`,
        input: `النيتش: ${s.niche}`,
        schema: {
          type: "object",
          properties: { ideas: { type: "array", items: { type: "string" } } },
          required: ["ideas"],
          additionalProperties: false,
        },
      });
      s.ideas = (out.ideas || []).slice(0, 15);
      s.topic = null;
    },
  },
  {
    id: 3,
    name: "مدير الجدول",
    role: "مدة الفيديو واللهجة",
    kind: "input",
    ready: (s) => !!s.durationSec,
  },
  {
    id: 4,
    name: "كاتب السكريبت",
    role: "السكريبت الكامل",
    kind: "ai",
    async run(s, ai) {
      s.targetWords = Math.round(s.durationSec * WPS);
      s.script = await ai({
        brief: `Write the full narration script in Arabic (${DIALECTS[s.dialect || "fusha"]}).
Word math at 2.5 words per second. Target: about ${s.targetWords} words. Hit the target within 5 percent.
${SCRIPT_RULES}
Output ONLY the script itself as one flowing block split into short paragraphs. No title, no word count, no notes.`,
        input: `النيتش: ${s.niche}\nالموضوع: ${s.topic}\nالمدة: ${s.durationLabel} (حوالي ${s.targetWords} كلمة)`,
      });
      s.auditNote = null;
    },
  },
  {
    id: 5,
    name: "مدقق الكلمات",
    role: "مراجعة العدد ±5%",
    kind: "local",
    async run(s, ai) {
      const tol = Math.max(3, Math.round(s.targetWords * 0.05));
      let words = countWords(s.script);
      let attempts = 0;
      while (Math.abs(words - s.targetWords) > tol && attempts < 2) {
        attempts++;
        s.script = await ai({
          brief: `You are the word-count auditor. Rewrite the Arabic narration script so it has about ${s.targetWords} words (allowed range ${s.targetWords - tol}–${s.targetWords + tol}). It currently has ${words} words. ${words > s.targetWords ? "Trim" : "Expand"} it while keeping the voice, the cold open, the cause-and-effect flow and the strong closing line.
${SCRIPT_RULES}
Output ONLY the revised script.`,
          input: s.script,
        });
        words = countWords(s.script);
      }
      s.actualWords = words;
      s.auditNote =
        Math.abs(words - s.targetWords) <= tol
          ? `مطابق: ${words} كلمة من هدف ${s.targetWords} (${attempts ? `بعد ${attempts} مراجعة` : "من أول مرة"}).`
          : `قريب: ${words} كلمة من هدف ${s.targetWords} بعد ${attempts} مراجعات.`;
    },
  },
  {
    id: 6,
    name: "ضابط الإيقاع",
    role: "مدة المشهد الواحد",
    kind: "input",
    ready: (s) => !!s.sceneSec,
  },
  {
    id: 7,
    name: "مقطّع المشاهد",
    role: "تقسيم البيتس",
    kind: "ai",
    async run(s, ai) {
      const per = Math.round(s.sceneSec * WPS);
      const out = await ai({
        brief: `Split the Arabic script into visual beats for stick figure animation.
عدد كلمات المشهد الواحد = ${s.sceneSec} × 2.5 = حوالي ${per} كلمة. الجملة القصيرة اللي تدخل في حدود كلمات المشهد = بيت واحد. الجملة الطويلة تتقسم عند الفاصلة أو نهاية العبارة الطبيعية. كل بيت يحمل فكرة بصرية واحدة فقط بدون استثناء، ولازم يكون قابل للتصوير كمشهد ستيك فيجر واحد محدد. لو الفكرة البصرية هتتكسر عشان تكمل عدد الكلمات، قسّم لبيتين أقصر — وحدة الفكرة البصرية أهم من دقة عدد الكلمات.
CRITICAL: copy the script text exactly, word for word, in order. Do not add, drop, or change any word. Every word of the script must appear in exactly one beat.
Return JSON: {"beats": ["beat 1 text", "beat 2 text", ...]}.`,
        input: s.script,
        schema: {
          type: "object",
          properties: { beats: { type: "array", items: { type: "string" } } },
          required: ["beats"],
          additionalProperties: false,
        },
      });
      let cum = 0;
      s.beats = (out.beats || [])
        .map((t) => t.trim())
        .filter(Boolean)
        .map((text, i) => {
          const start = Math.round((cum / WPS) * 10) / 10;
          cum += countWords(text);
          return { n: i + 1, start, text };
        });
      s.beatWords = cum;
    },
  },
  {
    id: 8,
    name: "مصمم الشخصيات",
    role: "شكل البطل",
    kind: "input",
    ready: (s) => s.charMode === "skip" || !!s.characterAr,
    async suggest(s, ai) {
      const out = await ai({
        brief: `Generate exactly 3 fully detailed main-character appearance options, in Arabic, for this stick figure video. Each option must include: اسم أو لقب مميز للشخصية، ستايل لبس محدد بوصف ألوان كامل، الإكسسوارات أو الأدوات اللي شايلها، الشخصية البصرية والفايب العام، وليه الشكل ده مناسب لموضوع الفيديو. Each option must have a clearly different personality, style and visual identity.
Return JSON: {"options":[{"name":"","outfit":"","accessories":"","vibe":"","why":""}, x3]}.`,
        input: `النيتش: ${s.niche}\nالموضوع: ${s.topic}\n\nالسكريبت:\n${s.script}`,
        schema: {
          type: "object",
          properties: {
            options: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  name: { type: "string" },
                  outfit: { type: "string" },
                  accessories: { type: "string" },
                  vibe: { type: "string" },
                  why: { type: "string" },
                },
                required: ["name", "outfit", "accessories", "vibe", "why"],
                additionalProperties: false,
              },
            },
          },
          required: ["options"],
          additionalProperties: false,
        },
      });
      s.charOptions = (out.options || []).slice(0, 3);
    },
  },
  {
    id: 9,
    name: "رسام الكراكتر شيت",
    role: "تثبيت الشخصية",
    kind: "ai",
    skip: (s) => s.charMode === "skip",
    async run(s, ai) {
      const out = await ai({
        brief: `Lock the main character. Return JSON with:
"summary_ar": ملخص شكل الشخصية النهائي في 2-3 جمل بالعربية.
"character_en": a complete English description of the locked character translated literally from the Arabic with every detail: the name, the outfit with every color in detail, the accessories, hair if any, and the overall vibe. One prose paragraph, starting with the character's name. Do not describe the head/face construction (that is locked elsewhere).`,
        input: s.characterAr,
        schema: {
          type: "object",
          properties: { summary_ar: { type: "string" }, character_en: { type: "string" } },
          required: ["summary_ar", "character_en"],
          additionalProperties: false,
        },
      });
      s.characterSummary = out.summary_ar;
      s.characterEn = out.character_en;
      s.charSheet = characterSheetPrompt(out.character_en);
    },
  },
  {
    id: 10,
    name: "مخرج المشاهد",
    role: "تخطيط كل لقطة",
    kind: "ai",
    async run(s, ai, progress) {
      const CHUNK = 10;
      const plans = [];
      for (let i = 0; i < s.beats.length; i += CHUNK) {
        const chunk = s.beats.slice(i, i + CHUNK);
        progress?.(`لقطات ${i + 1}–${i + chunk.length} من ${s.beats.length}`);
        const out = await ai({
          brief: `For each beat, silently find the single most powerful visual moment that represents its core idea. Decide the environment, the character count, the specific action or pose, the emotional reaction, costume details, and key props. Think cinematically about camera angle, body language, background action, and what the environment communicates.
Write in ENGLISH, natural flowing prose, three parts per beat:
"environment": SCENE AND ENVIRONMENT in full detail: exact location, what it looks like, color palette and atmospheric lighting, specific background elements (architecture, nature, furniture, sky, fire, water, crowds), and how the background reinforces the emotion of this beat.
"characters": CHARACTER OR CHARACTERS: how many stick figures, exact position of each in frame, thematic clothing with full color description, body pose and posture, facial emotion through eyebrow and mouth expression, motion lines if any, and scale relative to environment.${s.characterEn ? " Whenever the main character appears, refer to them by name and keep their exact locked outfit." : ""}
"action": KEY ACTION AND FOCAL POINT: the single most important thing happening, what the character is doing right now, where the viewer's eye goes first, any prop and how the character interacts with it, and what makes this frame readable as a complete story moment.
Do NOT include the locked style text, the locked character design, or any closer: those are appended automatically.
Return JSON: {"scenes":[{"n":<beat number>,"environment":"","characters":"","action":""}]} with one entry per beat, same order.`,
          input:
            `الموضوع: ${s.topic}\n` +
            (s.characterEn ? `MAIN CHARACTER: ${s.characterEn}\n` : "") +
            `\nFull script for context:\n${s.script}\n\nBeats to plan now:\n` +
            chunk.map((b) => `${b.n}. ${b.text}`).join("\n"),
          schema: {
            type: "object",
            properties: {
              scenes: {
                type: "array",
                items: {
                  type: "object",
                  properties: {
                    n: { type: "integer" },
                    environment: { type: "string" },
                    characters: { type: "string" },
                    action: { type: "string" },
                  },
                  required: ["n", "environment", "characters", "action"],
                  additionalProperties: false,
                },
              },
            },
            required: ["scenes"],
            additionalProperties: false,
          },
        });
        const byN = new Map((out.scenes || []).map((sc) => [sc.n, sc]));
        chunk.forEach((b, k) => plans.push(byN.get(b.n) || out.scenes?.[k] || null));
      }
      s.plans = plans;
    },
  },
  {
    id: 11,
    name: "مجمّع البرومتات",
    role: "برومتات الصور",
    kind: "local",
    run(s) {
      s.imagePrompts = s.beats.map((b, i) => {
        const p = s.plans[i];
        const parts = p ? [p.environment, p.characters, p.action] : [`[missing plan for beat ${b.n}]`];
        parts.push(LOCKED_CHARACTER_DESIGN);
        if (s.characterEn) parts.push("MAIN CHARACTER: " + s.characterEn);
        parts.push(LOCKED_IMAGE_STYLE, IMAGE_CLOSER);
        return parts.map((x) => x.trim()).join(" ");
      });
    },
  },
  {
    id: 12,
    name: "مراقب الجودة",
    role: "فحص الثبات",
    kind: "local",
    run(s) {
      const issues = [];
      s.imagePrompts.forEach((p, i) => {
        const n = i + 1;
        if (!p.includes(LOCKED_CHARACTER_DESIGN)) issues.push(`مشهد ${n}: التصميم المثبت للشخصيات ناقص`);
        if (!p.includes(LOCKED_IMAGE_STYLE)) issues.push(`مشهد ${n}: الستايل المثبت ناقص`);
        if (!p.endsWith(IMAGE_CLOSER)) issues.push(`مشهد ${n}: جملة الختام ناقصة`);
        if (s.characterEn && !p.includes("MAIN CHARACTER: " + s.characterEn)) issues.push(`مشهد ${n}: وصف البطل ناقص`);
        if (p.includes("[missing plan")) issues.push(`مشهد ${n}: المخرج مكتبلوش خطة`);
      });
      const coverage = s.actualWords ? Math.round((s.beatWords / s.actualWords) * 100) : 100;
      if (Math.abs(coverage - 100) > 3) issues.push(`البيتس بتغطي ${coverage}% من كلمات السكريبت`);
      s.qa = { checked: s.imagePrompts.length, issues, coverage };
    },
  },
  {
    id: 13,
    name: "مخرج الأنيميشن",
    role: "البرومت الماستر",
    kind: "local",
    run(s) {
      s.animPrompt = masterAnimationPrompt(s.sceneSec);
    },
  },
  {
    id: 14,
    name: "مصمم الثمبنيل",
    role: "3 أفكار ثمبنيل",
    kind: "ai",
    async run(s, ai) {
      const out = await ai({
        brief: `Generate exactly 3 complete thumbnail image prompts in English, each with a one-sentence Arabic explanation of the idea.
THUMBNAIL STYLE: the thumbnails live in the same cinematic cartoon stick figure world as the video images but pushed to maximum visual impact. Richer colors, more dramatic lighting, more extreme character poses and expressions, built to stop a viewer scrolling instantly and read perfectly at 200 pixels wide.
Rule 1 - One or two stick figure characters in the most extreme, emotionally powerful, or visually dramatic pose from the entire video story, using the locked character design with large expressive white round heads, vivid facial expressions, and fully colored thematic costumes. At least one character must be in a pose so clear and extreme that the emotion is readable as a thumbnail icon.
Rule 2 - The background must be a fully rendered cinematic cartoon environment matching the video style but pushed harder, darker, more saturated, with stronger dramatic lighting effects such as fire glow, storm lightning, spotlight beams, magical light explosions, or deep atmospheric shadows creating maximum visual drama.
Rule 3 - Maximum 2 text elements, written in Arabic (bold clean Arabic sans serif type such as a heavy Kufi or modern Arabic display font), maximum 4 words each, placed with strong visual separation from the character. Text must be either pure white with a thick black outline on a colored background area, or pure black on a light area. Words must be pulled from the most powerful or most curious line in the video script, translated naturally into punchy Arabic. In the English prompt, specify the exact Arabic words to render in quotes and describe their placement and styling.
Rule 4 - One single high contrast accent element to pull the eye immediately such as a large bold arrow, a glowing highlight circle around a key element, a crack of lightning pointing at the character, or a burst effect behind the character.
Rule 5 - The composition must be instantly readable at 200 pixels wide. No small details that disappear at thumbnail size. The character must dominate at least 40 percent of the frame. The most important element must be in the center or right third of the frame (Arabic readers scan right to left).
Rule 6 - Same cinematic cartoon stick figure style as the video. Full color, dramatic lighting, rich atmosphere, expressive characters.
Each prompt must be a complete self-contained English block describing in full: the exact character pose, facial expression, and costume with full color details; the background environment with specific lighting and color atmosphere; the exact Arabic text wording, placement, and style; the accent element and its exact position; and the complete composition layout from right to left and top to bottom.${s.characterEn ? " The main character must be the locked character described below, with the exact same outfit." : ""}
Do NOT write the closing sentence; it is appended automatically.
Return JSON: {"thumbnails":[{"idea_ar":"","prompt":""} x3]}.`,
        input:
          `الموضوع: ${s.topic}\n` +
          (s.characterEn ? `MAIN CHARACTER: ${s.characterEn}\n` : "") +
          `\nالسكريبت:\n${s.script}`,
        schema: {
          type: "object",
          properties: {
            thumbnails: {
              type: "array",
              items: {
                type: "object",
                properties: { idea_ar: { type: "string" }, prompt: { type: "string" } },
                required: ["idea_ar", "prompt"],
                additionalProperties: false,
              },
            },
          },
          required: ["thumbnails"],
          additionalProperties: false,
        },
      });
      s.thumbs = (out.thumbnails || []).slice(0, 3).map((t) => ({
        ideaAr: t.idea_ar,
        prompt: t.prompt.trim() + " " + THUMB_CLOSER,
      }));
    },
  },
  {
    id: 15,
    name: "مدير التغليف",
    role: "تسليم الباكدج",
    kind: "local",
    run(s) {
      s.packageMd = buildPackage(s);
    },
  },
];

export function buildPackage(s) {
  const L = [];
  L.push(`# ${s.topic}`, "", `- النيتش: ${s.niche}`, `- المدة: ${s.durationLabel} — الهدف ${s.targetWords} كلمة / الفعلي ${s.actualWords} كلمة`, `- مدة المشهد: ${s.sceneSec} ثواني — ${s.beats.length} مشهد`, "");
  L.push("## السكريبت", "", s.script, "");
  L.push("## تقسيم المشاهد", "", `إجمالي المشاهد: ${s.beats.length} مشهد × ${s.sceneSec} ثانية = حوالي ${s.beats.length * s.sceneSec} ثانية`, "", "| رقم المشهد | التوقيت (بداية) | كلمات السرد |", "|---|---|---|");
  s.beats.forEach((b) => L.push(`| ${b.n} | ${b.start.toFixed(1)}ث | ${b.text.replace(/\|/g, "/")} |`));
  L.push("");
  if (s.charSheet) {
    L.push("## الشخصية الرئيسية", "", s.characterSummary || s.characterAr, "", "### Character Sheet Prompt", "", "```", s.charSheet, "```", "");
  }
  L.push("## برومتات الصور", "");
  s.imagePrompts.forEach((p, i) => {
    L.push(`### ${i + 1}`, `مشهد ${i + 1} — ${s.beats[i].text}`, "", "```", p, "```", "");
  });
  L.push(`## برومت الأنيميشن الماستر`, "", `ده البرومت الموحد — استخدمه مع كل صورة لتحويلها لمشهد متحرك مدته ${s.sceneSec} ثواني:`, "", "```", s.animPrompt, "```", "");
  L.push("## أفكار الثمبنيل", "");
  s.thumbs.forEach((t, i) => L.push(`### ${i + 1}`, t.ideaAr, "", "```", t.prompt, "```", ""));
  return L.join("\n");
}
