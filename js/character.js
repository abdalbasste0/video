// The permanent main character. Every new project uses it automatically until the user
// replaces it (worker 8 → "بدّل الشخصية الثابتة") or turns it off.

export const KARIM = {
  name: "كريم",
  summaryAr:
    "كريم، شاب في العشرينات، بحّار ناجي وحيد لسه الخوف القديم باين في عينيه. لابس سترة نجاة برتقالي باهت بأبازيم وأحزمة واضحة فوق تيشيرت رمادي مقطوع شوية، شعره أسود منكوش، وشايل حبل بحري بني ملفوف على كتف واحد من آخر رحلة. الفايب متوتر وهش، كأنه لسه فاكر حاجة مرعبة حصلتله.",
  characterEn:
    "Karim, a young man in his twenties, a lone survivor sailor with old fear still visible in his eyes. He wears a faded orange life vest with its buckles and straps clearly visible over a slightly torn gray t-shirt, has messy tousled black hair, and carries a coiled brown nautical rope slung over one shoulder, left over from his last voyage. His overall vibe is tense and fragile, as if he is still remembering something terrifying that happened to him.",
  sheet:
    "Character reference sheet (model sheet) of a single stick figure character, shown in multiple views on one 16:9 canvas: full body front view, full body side profile view, full body back view, and a three-quarter view, all standing in a neutral A-pose, plus a row of five large head close-ups along the bottom showing five distinct facial expressions: neutral, happy, angry, terrified, and surprised. The character is Karim, a young man in his twenties, a lone survivor sailor with old fear still visible in his eyes. He wears a faded orange life vest over a slightly torn gray t-shirt, has messy tousled black hair, and carries a coiled nautical rope slung over one shoulder, left over from his last voyage. His overall vibe is tense and fragile, as if he is still remembering something terrifying that happened to him. The stick figure character has a large perfectly round pure white head with highly expressive cartoon facial features: thick black eyebrow lines, large white eyes with black pupils and visible irises, and a wide expressive mouth showing teeth and tongue in strong emotions. The body is classic stick figure construction with thin black line arms and legs, the head being the dominant visual feature at approximately one third of total character height. Clothing is drawn as clean cartoon outlines with flat saturated colors and simple details, fully colored and visually specific: the faded orange life vest with its buckles and straps clearly visible, the torn gray t-shirt underneath, and the coiled brown nautical rope over the shoulder. All views must show the exact same character with identical clothing, colors, accessories, and proportions for perfect consistency. Clean light neutral studio background with a subtle soft gradient, evenly lit, no dramatic scene lighting, no environment, character sheet layout with clear spacing between poses. Bold confident line work, cinematic cartoon illustration quality, professional animation studio model sheet, 16:9, ultra-detailed.",
  // colours for the drawn (no-image) stick figure scenes
  outfit: { shirt: "#e8833a", pants: "#6c727a", hat: "hair", tie: false, accent: "#8b5a2b" },
};

const KEY = "stickfactory.fixedCharacter.v1";

/** The fixed character, or null when the user turned it off. */
export function getFixedCharacter() {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw === null) return KARIM;          // default: Karim
    const v = JSON.parse(raw);
    return v && v.off ? null : v;
  } catch { return KARIM; }
}

export function setFixedCharacter(c) {
  try { localStorage.setItem(KEY, JSON.stringify(c ?? { off: true })); } catch { /* storage unavailable */ }
}

/**
 * Build a fixed character from what the user pasted: a full character-sheet prompt (English),
 * or a plain description (any language; worker 9 translates it then).
 */
export function characterFromText(text) {
  const t = text.trim();
  const m = t.match(/surprised\.\s*([\s\S]+?)\s*The stick figure character has/i);
  const isSheet = /^Character reference sheet/i.test(t) && m;
  const nameMatch = (m ? m[1] : t).match(/The character is ([^,]+),/i) || (m ? m[1] : t).match(/^([^,،.]+)[,،]/);
  return {
    name: nameMatch ? nameMatch[1].trim() : "البطل",
    summaryAr: isSheet ? "" : t,
    characterEn: isSheet ? m[1].replace(/^The character is\s+/i, "").trim() : "",
    sheet: isSheet ? t : "",
    outfit: null,
  };
}
