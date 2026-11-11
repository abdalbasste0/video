// Locked texts copied verbatim from the production spec.
// They are appended by code (not by the model) so they stay word-for-word identical in every prompt.

export const LOCKED_CHARACTER_DESIGN =
  "The stick figure characters have large perfectly round pure white heads with highly expressive cartoon faces featuring thick black eyebrow lines that show emotion clearly, large white eyes with black pupils and visible irises, and wide open mouths with teeth and tongue visible when expressing strong emotions like anger, fear, surprise, or excitement. The character bodies are classic stick figure construction with thin black line arms and legs but the heads are the dominant visual feature at approximately one third of the total character height. Characters wear detailed thematic clothing rendered in the stick figure aesthetic, meaning clothing is drawn as clean cartoon outlines with flat colors and simple details that match the scene and story context, such as robes, suits, armor, casual clothes, or period appropriate costumes. Clothing must be colorful and visually specific to the character role in the scene.";

export const LOCKED_IMAGE_STYLE =
  "The overall image style is cinematic cartoon illustration with fully colored and rendered backgrounds that create dramatic atmospheric depth. Backgrounds are richly detailed cartoon environments with strong dramatic lighting, vivid color palettes, atmospheric effects like fire glow, moonlight, spotlights, storm clouds, or magical light, and multiple layers of depth from foreground elements to distant background details. The art style combines the simplicity of stick figure characters with the visual richness of a professionally illustrated cartoon short film, similar to a high quality web comic or animated series still frame. Line weights are bold and confident throughout. Colors are saturated and contrast-rich. The composition uses cinematic framing with clear foreground, midground, and background layers. Lighting is dramatic and purposeful, creating strong mood and atmosphere appropriate to the scene. 16:9 horizontal composition, ultra-detailed, professional cartoon illustration quality.";

export const IMAGE_CLOSER =
  "The stick figure heads must be large, round, pure white, and highly expressive with cartoon facial features clearly visible. Character clothing must be fully colored and thematically appropriate. The background must be a fully rendered cinematic cartoon environment with rich color, dramatic lighting, and atmospheric depth. NOT minimalist, NOT black and white only, NOT flat or textureless. Full color cinematic cartoon stick figure illustration at professional quality, 16:9, ultra-detailed.";

export const THUMB_CLOSER =
  "Large round pure white stick figure heads with highly expressive cartoon faces and fully colored thematic costumes. Cinematic cartoon illustration style with rich saturated colors, dramatic atmospheric lighting, and full environmental depth. Bold confident line work throughout. Maximum visual impact at thumbnail size. Professional cartoon illustration quality, 16:9, ultra-detailed. Texts must have proper gradient colouring and the main and important word must be in a different and unique colour like gradient blue or gradient yellow or gradient red depending on the vibe of the overall thumbnail, main figure must be wearing some sort of amazing dressing according to the overall theme and topic of the video and must be looking extremely sharp and eye catching.";

export function characterSheetPrompt(characterEn) {
  return (
    "Character reference sheet (model sheet) of a single stick figure character, shown in multiple views on one 16:9 canvas: full body front view, full body side profile view, full body back view, and a three-quarter view, all standing in a neutral A-pose, plus a row of five large head close-ups along the bottom showing five distinct facial expressions: neutral, happy, angry, terrified, and surprised. " +
    characterEn.trim() +
    " The stick figure character has a large perfectly round pure white head with highly expressive cartoon facial features: thick black eyebrow lines, large white eyes with black pupils and visible irises, and a wide expressive mouth showing teeth and tongue in strong emotions. The body is classic stick figure construction with thin black line arms and legs, the head being the dominant visual feature at approximately one third of total character height. Clothing is drawn as clean cartoon outlines with flat saturated colors and simple details, fully colored and visually specific. All views must show the exact same character with identical clothing, colors, accessories, and proportions for perfect consistency. Clean light neutral studio background with a subtle soft gradient, evenly lit, no dramatic scene lighting, no environment, character sheet layout with clear spacing between poses. Bold confident line work, cinematic cartoon illustration quality, professional animation studio model sheet, 16:9, ultra-detailed."
  );
}

export function masterAnimationPrompt(n) {
  const mid = n - 1;
  return `Transform the provided stick figure image into a ${n}-second premium professional cinematic cartoon stick figure animation. Before animating anything, analyze the provided image completely and thoroughly: identify every character in the scene, their exact position in the frame, their costume and clothing details, their facial expression and emotional state, every object and prop present, the full environment including background lighting and atmospheric effects, and most importantly the specific action or situation being depicted in this beat. This complete scene analysis is your director's brief. Every animation decision must serve this specific scene and this specific story moment.

STYLE: cinematic cartoon stick figure animation matching the rich colorful illustrated style of the provided image exactly. The large round white character heads with expressive cartoon faces must remain perfectly consistent throughout the clip. Colored clothing and costumes stay exactly as shown. The fully rendered background environment maintains its atmospheric lighting, color palette, and depth throughout. All motion is fluid, physically believable, and dramatically appropriate to the scene. Movements are confident and snappy, not floaty or slow. This animation must feel like a scene from a professionally produced cartoon series, not a basic gif or simple motion test.

CHARACTER ANIMATION RULES - these are mandatory and must be applied to every character in every clip: Every stick figure must move with complete full body physics that feels natural and weighted. When a character steps forward their weight shifts visibly. When they turn their whole body follows through. When they lift or throw something their legs bend and their torso rotates with the effort. Arms swing naturally during walking. The body leans into every direction of movement. Emotional reactions must happen across the entire body simultaneously, not just the face. A character who is terrified stumbles backward with arms flying up and legs buckling. A character who is furious lunges forward with shoulders raised and fists clenched. A character who is victorious throws their arms wide and their chest expands. A character who is defeated slumps their entire frame with head dropping and shoulders collapsing inward. Facial expressions on the large round heads must be animated with full cartoon expressiveness. Eyebrows shoot up for surprise, slam down for anger, curve sadly for defeat. Eyes go wide for shock, narrow for suspicion, fill with tears for sadness. Mouths stretch open for screaming or laughing, press tight for determination, tremble for fear. If multiple characters are in the scene every single character must be animated with appropriate reactions to what is happening, even background crowd characters must show reactions through body language and head movement appropriate to the scene atmosphere.

SCENE ANIMATION RULES - these are mandatory for every clip: Analyze the specific scene depicted and animate every environmental element that can logically move or react. Fire must flicker and pulse with heat distortion above it. Crowds must ripple with movement and reaction. Flags and capes must flow with air movement. Torches must cast moving light. Storm clouds must churn. Smoke must rise and drift. Water must move. Any object being used by a character must have realistic physical motion when touched, thrown, dropped, or interacted with. The environment lighting must pulse and shift subtly throughout the clip to reinforce the dramatic atmosphere of the scene. Fire glow should flicker warmly across characters. Spotlights should hold steady but cast moving shadows. Moonlight should create subtle atmospheric shifts in color tone. The animation must tell the complete story of this specific beat without any narration. A viewer who has never heard the script must understand immediately from watching this clip exactly what is happening, who the characters are, what emotion they feel, and what action is taking place.

CAMERA RULES: the camera stays completely locked and static for the full clip. No zoom, no pan, no tilt, no shake, no rotation, no reframing of any kind. One clean static shot that holds the full composition of the provided image exactly while the characters and environment animate within it.

TIMING AND PACING: the first 0 to 1 second establishes all characters and environment in their starting positions matching the provided image. The middle section from 1 to ${mid} seconds carries the main action and character performance with natural timing, proper ease-in and ease-out on every movement, and believable physical weight on all motion. The final second (${mid} to ${n}) holds the peak dramatic moment of the scene with subtle continuing motion such as breathing, flickering fire, or swaying movement so the frame feels alive before cutting to the next clip.

QUALITY STANDARD: every frame of this animation must be at the quality level of a professionally produced cartoon short film. The character performances must be fully committed and emotionally readable. The environment must feel alive and inhabited. The colors must be rich and properly lit throughout. This is not a simple animation test, this is a premium production piece that must hook a viewer within the first 2 seconds. Make sure this is no morphing, no glitching, no teleporting, no hallucinations and no objects and elements changing shapes out of nowhere like mobile becoming laptop or suddenly a lamp appears out of no where. Animations must look top notch and make sure animations have no lip sync, no dialogue just amazing reactions, actions and stickmen movements. Some animation examples are but not limited to these: running with proper facial reactions, picking plates, refusing something but with gestures no lip sync or dialogue, excitement, tying shoe laces, running behind the bus to catch it, disappointed, working in the gym etc. most important rule is no lip sync, no dialogue and proper uninterrupted animation without glitches or errors or morphing. Goal is to convey message through stick figures actions not dialogues or lip sync.`;
}

export const NICHES = [
  "المال النفسي والتمويل الشخصي",
  "الجرائم والقصص الجنائية الوثائقية",
  "التاريخ والأحداث المنسية",
  "العلوم والسلوك البشري",
  "العلاقات والديناميكيات الاجتماعية",
  "الصحة وعلم النفس",
  "البيزنس وريادة الأعمال",
  "التكنولوجيا والذكاء الاصطناعي ببساطة",
  "الألغاز والأحداث الغامضة",
  "التحفيز وتطوير الذات",
];

export const DURATIONS = [
  { label: "30 ثانية", seconds: 30 },
  { label: "دقيقة", seconds: 60 },
  { label: "دقيقتين", seconds: 120 },
  { label: "3 دقايق", seconds: 180 },
  { label: "5 دقايق", seconds: 300 },
  { label: "10 دقايق", seconds: 600 },
];

export const SCENE_SECONDS = [
  { s: 3, hint: "تقطيع سريع جداً، إيقاع تيك توك" },
  { s: 4, hint: "إيقاع سريع" },
  { s: 5, hint: "إيقاع متوازن" },
  { s: 6, hint: "الافتراضي الأنسب لمعظم موديلات الأنيميشن" },
  { s: 8, hint: "إيقاع هادي، مشاهد أطول" },
  { s: 10, hint: "مشاهد سردية طويلة" },
];
