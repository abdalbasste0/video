// The studio: draws and animates the stick figure scenes on a canvas, adds Arabic captions,
// mixes the voice-over and background music, and records the final video file.

export const W = 1280;
export const H = 720;
const GROUND = 580;

// ---------- vocabularies the motion designer may use ----------
export const BACKGROUNDS = ["street", "home", "office", "bank", "shop", "park", "city_night", "classroom", "hospital", "desert", "stage", "bedroom", "kitchen", "abstract"];
export const LIGHTS = ["day", "night", "sunset", "spotlight", "storm"];
export const EMOTIONS = ["neutral", "happy", "sad", "angry", "scared", "surprised", "thinking", "tired", "excited", "worried"];
export const ACTIONS = ["idle", "walk", "run", "talk", "point", "jump", "sit", "fall", "cry", "celebrate", "think", "shrug", "wave", "work", "carry", "count_money", "look_phone", "sleep", "fight", "hide", "shocked_back", "give", "facepalm", "nod"];
export const PROPS = {
  coin: "🪙", money: "💵", money_bag: "💰", card: "💳", phone: "📱", laptop: "💻", house: "🏠", car: "🚗", bus: "🚌",
  lightbulb: "💡", question: "❓", exclaim: "❗", heart: "❤️", broken_heart: "💔", chart_up: "📈", chart_down: "📉",
  clock: "⏰", calendar: "📅", gift: "🎁", box: "📦", book: "📚", food: "🍔", coffee: "☕", shopping_cart: "🛒",
  bag: "🛍️", trophy: "🏆", warning: "⚠️", lock: "🔒", key: "🔑", brain: "🧠", fire: "🔥", tree: "🌳", bed: "🛏️",
  pill: "💊", rocket: "🚀", target: "🎯", scale: "⚖️", door: "🚪", tv: "📺", chat: "💬", zzz: "💤", sweat: "💦", star: "⭐",
};
export const EFFECTS = ["none", "rain", "sparkles", "money_rain", "shake", "zoom_in", "fire", "stars", "hearts"];

export const SCENE_SCHEMA = {
  type: "object",
  properties: {
    mainOutfit: {
      type: "object",
      properties: {
        shirt: { type: "string" }, pants: { type: "string" },
        hat: { type: "string", enum: ["none", "cap", "tophat", "beanie", "hair"] },
        tie: { type: "boolean" }, accent: { type: "string" },
      },
      required: ["shirt", "pants", "hat", "tie", "accent"],
      additionalProperties: false,
    },
    scenes: {
      type: "array",
      items: {
        type: "object",
        properties: {
          n: { type: "integer" },
          bg: { type: "string", enum: BACKGROUNDS },
          light: { type: "string", enum: LIGHTS },
          sky: { type: "string" }, ground: { type: "string" },
          effect: { type: "string", enum: EFFECTS },
          props: {
            type: "array",
            items: {
              type: "object",
              properties: {
                type: { type: "string", enum: Object.keys(PROPS) },
                x: { type: "number" }, y: { type: "number" }, size: { type: "number" },
                motion: { type: "string", enum: ["none", "float", "pulse", "spin", "fall", "fly_in"] },
              },
              required: ["type", "x", "y", "size", "motion"],
              additionalProperties: false,
            },
          },
          characters: {
            type: "array",
            items: {
              type: "object",
              properties: {
                main: { type: "boolean" },
                x: { type: "number" }, toX: { type: "number" },
                facing: { type: "string", enum: ["left", "right"] },
                scale: { type: "number" },
                shirt: { type: "string" }, pants: { type: "string" },
                emotion: { type: "string", enum: EMOTIONS },
                action: { type: "string", enum: ACTIONS },
              },
              required: ["main", "x", "toX", "facing", "scale", "shirt", "pants", "emotion", "action"],
              additionalProperties: false,
            },
          },
        },
        required: ["n", "bg", "light", "sky", "ground", "effect", "props", "characters"],
        additionalProperties: false,
      },
    },
  },
  required: ["mainOutfit", "scenes"],
  additionalProperties: false,
};

export const MOTION_BRIEF = `You are the motion designer. Our in-browser animation engine draws every beat as a 2D cartoon stick figure scene (large round white heads with expressive faces, colored clothes, colored backgrounds). Turn each beat into a scene spec using ONLY the allowed values in the JSON schema.
Rules:
- Pick the bg, light, sky and ground colors (hex like "#ffcc00") that best tell the beat's emotion. Night/storm for fear or loss, sunset for reflection, spotlight for a reveal, day for normal life.
- 1 to 3 characters per scene. Use the main character (main: true) whenever the story is about "you"/the viewer or the hero. x and toX are 0..1 across the frame (0.15 to 0.85 is safe). toX differs from x only for walk/run. scale 0.8..1.2. Non-main characters get their own shirt/pants hex colors.
- The action and emotion must show the beat's meaning with body language alone — no text, no lip sync.
- 0 to 3 props that make the idea instantly readable (money for money, phone for phones, chart_down for losses, question for confusion...). Prop x is 0..1, y is 0..1 (0 = top, 0.75 = on the ground), size 0.5..2.
- effect adds energy only when it fits.
- mainOutfit: the locked main character's clothing as hex colors (if no main character is given, invent a simple consistent look).
Return one scene per beat, same order, with n = beat number.`;

// ---------- helpers ----------
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const hex = (c, fb) => (/^#[0-9a-f]{3,8}$/i.test(c || "") ? c : fb);
function rand(seed) { let s = seed * 9301 + 49297; return () => ((s = (s * 9301 + 49297) % 233280) / 233280); }
function shade(c, amt) {
  let h = hex(c, "#888888").slice(1); if (h.length === 3) h = h.split("").map((x) => x + x).join("");
  const n = parseInt(h.slice(0, 6), 16);
  const f = (v) => clamp(Math.round(v + amt * 255), 0, 255);
  return `rgb(${f(n >> 16)},${f((n >> 8) & 255)},${f(n & 255)})`;
}

// ---------- backgrounds ----------
function drawBackground(ctx, sc, t, seed) {
  const sky = hex(sc.sky, "#8ecae6"), ground = hex(sc.ground, "#6a994e");
  const g = ctx.createLinearGradient(0, 0, 0, GROUND);
  g.addColorStop(0, shade(sky, -0.15)); g.addColorStop(1, shade(sky, 0.12));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, GROUND);
  const r = rand(seed);
  const indoor = ["home", "office", "bank", "shop", "classroom", "hospital", "bedroom", "kitchen", "stage"].includes(sc.bg);

  if (sc.bg === "abstract") {
    for (let i = 0; i < 14; i++) {
      ctx.fillStyle = `rgba(255,255,255,${0.05 + r() * 0.08})`;
      ctx.beginPath(); ctx.arc(r() * W, r() * GROUND, 40 + r() * 160 + Math.sin(t + i) * 8, 0, 7); ctx.fill();
    }
  } else if (indoor) {
    // back wall panels + window/door
    ctx.fillStyle = shade(sky, -0.05);
    for (let x = 0; x < W; x += 160) ctx.fillRect(x, 0, 4, GROUND);
    ctx.fillStyle = shade(sky, -0.22); ctx.fillRect(0, GROUND - 26, W, 26);
    const wx = 120 + r() * 300;
    ctx.fillStyle = sc.light === "night" || sc.light === "storm" ? "#1d2b53" : "#cdeffd";
    roundRect(ctx, wx, 110, 230, 170, 10); ctx.fill();
    ctx.strokeStyle = "#3b2f2f"; ctx.lineWidth = 8; ctx.stroke();
    ctx.beginPath(); ctx.moveTo(wx + 115, 110); ctx.lineTo(wx + 115, 280); ctx.moveTo(wx, 195); ctx.lineTo(wx + 230, 195); ctx.stroke();
    if (sc.bg === "office" || sc.bg === "classroom") {
      ctx.fillStyle = sc.bg === "classroom" ? "#2d6a4f" : "#f1f1f1";
      roundRect(ctx, 700, 120, 380, 200, 8); ctx.fill(); ctx.strokeStyle = "#333"; ctx.lineWidth = 6; ctx.stroke();
      ctx.strokeStyle = sc.bg === "classroom" ? "#e9f5db" : "#457b9d"; ctx.lineWidth = 5; ctx.beginPath();
      ctx.moveTo(740, 280); ctx.lineTo(820, 230); ctx.lineTo(900, 250); ctx.lineTo(1040, 160); ctx.stroke();
    }
    if (sc.bg === "bank" || sc.bg === "shop") {
      ctx.fillStyle = sc.bg === "bank" ? "#e0c068" : "#e76f51";
      ctx.fillRect(0, 40, W, 50); ctx.fillStyle = "#fff"; ctx.font = "800 34px Cairo, sans-serif"; ctx.textAlign = "center";
      ctx.fillText(sc.bg === "bank" ? "🏦  BANK  🏦" : "🛒  SHOP  🛒", W / 2, 78);
      ctx.fillStyle = "#8d5524"; roundRect(ctx, 760, 390, 420, 190, 6); ctx.fill();
      ctx.fillStyle = shade("#8d5524", 0.15); ctx.fillRect(760, 390, 420, 22);
    }
    if (sc.bg === "bedroom") { ctx.font = "160px serif"; ctx.textAlign = "center"; ctx.fillText("🛏️", 980, GROUND - 10); }
    if (sc.bg === "kitchen") { ctx.fillStyle = "#adb5bd"; ctx.fillRect(700, 400, 520, 180); ctx.fillStyle = "#495057"; ctx.fillRect(700, 400, 520, 16); }
    if (sc.bg === "hospital") { ctx.fillStyle = "#e63946"; ctx.fillRect(1040, 140, 40, 120); ctx.fillRect(1000, 180, 120, 40); }
    if (sc.bg === "stage") {
      ctx.fillStyle = "#9d0208"; ctx.fillRect(0, 0, 120, GROUND); ctx.fillRect(W - 120, 0, 120, GROUND);
      for (let x = 0; x < 120; x += 30) { ctx.fillStyle = "rgba(0,0,0,.18)"; ctx.fillRect(x, 0, 12, GROUND); ctx.fillRect(W - 120 + x, 0, 12, GROUND); }
    }
  } else {
    // outdoor: sun/moon, clouds, skyline or nature
    const night = sc.light === "night" || sc.light === "storm" || sc.bg === "city_night";
    ctx.fillStyle = night ? "#fefae0" : sc.light === "sunset" ? "#ffb703" : "#ffd60a";
    ctx.beginPath(); ctx.arc(1080, 110, 55, 0, 7); ctx.fill();
    if (night) { ctx.fillStyle = shade(sky, -0.15); ctx.beginPath(); ctx.arc(1100, 98, 50, 0, 7); ctx.fill(); }
    if (night) for (let i = 0; i < 40; i++) { ctx.fillStyle = `rgba(255,255,255,${0.4 + 0.5 * Math.abs(Math.sin(t * 2 + i))})`; ctx.fillRect(r() * W, r() * 300, 3, 3); }
    else for (let i = 0; i < 4; i++) cloud(ctx, ((r() * W + t * 18 * (i + 1)) % (W + 300)) - 150, 60 + r() * 140, 0.7 + r() * 0.6);
    if (sc.bg === "street" || sc.bg === "city_night") {
      for (let i = 0; i < 9; i++) {
        const bw = 110 + r() * 80, bh = 150 + r() * 260, bx = i * 150 - 30 + r() * 30;
        ctx.fillStyle = night ? shade("#22223b", r() * 0.1) : shade(sky, -0.28 - r() * 0.1);
        ctx.fillRect(bx, GROUND - bh, bw, bh);
        for (let wy = GROUND - bh + 20; wy < GROUND - 30; wy += 34) for (let wx = bx + 14; wx < bx + bw - 20; wx += 30) {
          ctx.fillStyle = night ? (r() > 0.45 ? "#ffd166" : "#2b2d42") : "rgba(255,255,255,.55)"; ctx.fillRect(wx, wy, 14, 18);
        }
      }
    } else if (sc.bg === "park") {
      for (let i = 0; i < 5; i++) { ctx.font = `${120 + r() * 60}px serif`; ctx.textAlign = "center"; ctx.fillText("🌳", 80 + i * 280 + r() * 60, GROUND + 10); }
    } else if (sc.bg === "desert") {
      ctx.fillStyle = shade(ground, 0.08); ctx.beginPath(); ctx.moveTo(0, GROUND);
      for (let x = 0; x <= W; x += 40) ctx.lineTo(x, GROUND - 70 - 50 * Math.sin(x / 210 + seed));
      ctx.lineTo(W, GROUND); ctx.fill();
    }
  }
  // floor
  const fg = ctx.createLinearGradient(0, GROUND, 0, H);
  fg.addColorStop(0, ground); fg.addColorStop(1, shade(ground, -0.2));
  ctx.fillStyle = fg; ctx.fillRect(0, GROUND, W, H - GROUND);
  if (sc.bg === "street" || sc.bg === "city_night") {
    ctx.fillStyle = "rgba(255,255,255,.7)";
    for (let x = ((-t * 60) % 120); x < W; x += 120) ctx.fillRect(x, GROUND + 70, 60, 8);
  }
}

function cloud(ctx, x, y, s) {
  ctx.fillStyle = "rgba(255,255,255,.9)"; ctx.beginPath();
  ctx.arc(x, y, 30 * s, 0, 7); ctx.arc(x + 35 * s, y - 15 * s, 38 * s, 0, 7); ctx.arc(x + 75 * s, y, 30 * s, 0, 7); ctx.fill();
}
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

function drawLight(ctx, sc, t, seed) {
  if (sc.light === "night") { ctx.fillStyle = "rgba(10,20,60,.32)"; ctx.fillRect(0, 0, W, H); }
  if (sc.light === "sunset") { const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, "rgba(255,120,60,.22)"); g.addColorStop(1, "rgba(120,0,80,.12)"); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  if (sc.light === "spotlight") {
    const g = ctx.createRadialGradient(W / 2, GROUND - 120, 60, W / 2, GROUND - 120, 520);
    g.addColorStop(0, "rgba(255,250,220,0)"); g.addColorStop(1, "rgba(0,0,0,.7)"); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  if (sc.light === "storm") {
    ctx.fillStyle = "rgba(20,20,40,.38)"; ctx.fillRect(0, 0, W, H);
    const flash = (Math.sin(t * 1.7 + seed) > 0.985) || (t % 3.1 < 0.08);
    if (flash) { ctx.fillStyle = "rgba(255,255,255,.55)"; ctx.fillRect(0, 0, W, H); }
  }
}

// ---------- characters ----------
const EMO_FACE = {
  neutral: { brow: 0, mouth: "flat", eye: 1 },
  happy: { brow: -0.1, mouth: "smile", eye: 1 },
  sad: { brow: 0.45, mouth: "frown", eye: 0.9 },
  angry: { brow: -0.5, mouth: "grit", eye: 0.8 },
  scared: { brow: 0.5, mouth: "o", eye: 1.35 },
  surprised: { brow: 0.35, mouth: "O", eye: 1.4 },
  thinking: { brow: 0.2, mouth: "side", eye: 1 },
  tired: { brow: 0.2, mouth: "flat", eye: 0.45 },
  excited: { brow: -0.2, mouth: "grin", eye: 1.25 },
  worried: { brow: 0.4, mouth: "wobble", eye: 1.1 },
};

function pose(action, t, dur) {
  const s = Math.sin, w = t * Math.PI * 2;
  const P = { dy: 0, lean: 0, rot: 0, la: [0.25, -0.1], ra: [-0.25, -0.1], ll: [0.12, 0], rl: [-0.12, 0], head: 0, move: 0, talk: false, hold: null };
  const breathe = s(w * 0.4) * 2;
  P.dy = breathe;
  switch (action) {
    case "walk": { const p = w * 1.6; P.ll = [0.45 * s(p), -0.4 * Math.max(0, -s(p))]; P.rl = [-0.45 * s(p), -0.4 * Math.max(0, s(p))]; P.la = [-0.4 * s(p), -0.3]; P.ra = [0.4 * s(p), -0.3]; P.dy = Math.abs(s(p)) * -6; P.move = 1; break; }
    case "run": { const p = w * 2.6; P.lean = 0.3; P.ll = [0.8 * s(p), -0.9 * Math.max(0, -s(p)) - 0.2]; P.rl = [-0.8 * s(p), -0.9 * Math.max(0, s(p)) - 0.2]; P.la = [-0.9 * s(p), -1.2]; P.ra = [0.9 * s(p), -1.2]; P.dy = Math.abs(s(p)) * -14; P.move = 1; break; }
    case "talk": P.ra = [1.1 + 0.3 * s(w * 1.2), -0.9 + 0.3 * s(w * 1.5)]; P.talk = true; P.head = 0.05 * s(w); break;
    case "point": P.ra = [Math.PI / 2 + 0.05 * s(w * 2), 0]; P.lean = 0.05; break;
    case "jump": { const j = Math.abs(s(w * 0.9)); P.dy = -j * 90; P.la = [Math.PI - 0.4, 0]; P.ra = [-(Math.PI - 0.4), 0]; P.ll = [0.3 * (1 - j) + 0.2, -0.6 * (1 - j)]; P.rl = [0.3 * (1 - j) + 0.2, -0.6 * (1 - j)]; break; }
    case "sit": P.dy = 70; P.ll = [1.5, -1.5]; P.rl = [1.4, -1.45]; P.la = [0.6, -0.6]; P.ra = [0.5, -0.5]; break;
    case "fall": { const k = ease(clamp(t / Math.min(1.2, dur * 0.5), 0, 1)); P.rot = -k * 1.45; P.dy = k * 20; P.la = [lerp(0.2, 2.6, k), 0]; P.ra = [lerp(-0.2, 2.2, k), 0]; P.ll = [lerp(0.1, 0.5, k), 0]; P.rl = [lerp(-0.1, -0.3, k), 0]; break; }
    case "cry": P.head = 0.25; P.la = [2.2, 1.5 + 0.1 * s(w * 6)]; P.ra = [2.1, 1.6 + 0.1 * s(w * 6)]; P.lean = 0.12 + 0.02 * s(w * 6); break;
    case "celebrate": { const j = Math.abs(s(w * 1.2)); P.dy = -j * 35; P.la = [Math.PI - 0.5 + 0.3 * s(w * 2), 0.2]; P.ra = [-(Math.PI - 0.5) - 0.3 * s(w * 2), -0.2]; break; }
    case "think": P.ra = [1.9, 2.0]; P.la = [0.5, -1.6]; P.head = -0.1 + 0.05 * s(w * 0.5); break;
    case "shrug": { const k = 0.6 + 0.4 * Math.abs(s(w * 0.6)); P.la = [0.9 * k, -1.6 * k]; P.ra = [-0.9 * k, 1.6 * k]; P.head = 0.12 * s(w * 0.6); break; }
    case "wave": P.ra = [2.6, 0.5 * s(w * 2.4)]; break;
    case "work": P.ra = [1.2, -0.5 + 0.15 * s(w * 5)]; P.la = [1.1, -0.5 - 0.15 * s(w * 5)]; P.lean = 0.12; P.head = 0.08; break;
    case "carry": P.ra = [1.3, -0.6]; P.la = [1.25, -0.55]; P.hold = "box"; P.lean = -0.05; { const p = w * 1.2; P.ll = [0.3 * s(p), -0.2]; P.rl = [-0.3 * s(p), -0.2]; P.move = 1; } break;
    case "count_money": P.ra = [1.2, -0.7 + 0.25 * Math.max(0, s(w * 3))]; P.la = [1.1, -0.8]; P.hold = "money"; P.head = 0.15; break;
    case "look_phone": P.ra = [1.0, -1.4]; P.la = [0.2, -0.1]; P.hold = "phone"; P.head = 0.2 + 0.03 * s(w); break;
    case "sleep": P.rot = -1.5; P.dy = 25; P.la = [0.3, 0]; P.ra = [0.1, 0]; P.hold = "zzz"; break;
    case "fight": { const p = s(w * 2.5) > 0; P.ra = p ? [Math.PI / 2, 0] : [1.0, -1.6]; P.la = p ? [1.0, -1.6] : [Math.PI / 2, 0]; P.lean = 0.15; P.ll = [0.4, -0.2]; P.rl = [-0.4, 0]; break; }
    case "hide": P.dy = 60; P.ll = [1.4, -1.9]; P.rl = [1.3, -1.9]; P.la = [2.7, 1.6]; P.ra = [2.6, 1.7]; P.lean = 0.4 + 0.03 * s(w * 8); break;
    case "shocked_back": { const k = ease(clamp(t / 0.5, 0, 1)); P.lean = -0.35 * k; P.la = [lerp(0.2, 2.7, k), 0.3]; P.ra = [lerp(-0.2, -2.7, k), -0.3]; P.ll = [0.25, 0]; P.rl = [-0.35, 0]; P.move = -0.25 * k; break; }
    case "give": P.ra = [Math.PI / 2 - 0.2, -0.1]; P.hold = "money"; P.lean = 0.08; break;
    case "facepalm": P.ra = [2.6, 2.4]; P.head = 0.3; P.lean = 0.1; break;
    case "nod": P.head = 0.18 * Math.abs(s(w * 1.4)); break;
    default: break;
  }
  return P;
}

function drawFigure(ctx, ch, t, dur, outfit) {
  const sc = clamp(ch.scale || 1, 0.6, 1.4);
  const f = ch.facing === "left" ? -1 : 1;
  const P = pose(ch.action, t, dur);
  const Hh = 300 * sc;
  const headR = Hh * 0.165, torso = Hh * 0.29, upL = Hh * 0.19, loL = Hh * 0.19, upA = Hh * 0.15, loA = Hh * 0.15;
  const shirt = hex(ch.main ? outfit.shirt : ch.shirt, "#e63946");
  const pants = hex(ch.main ? outfit.pants : ch.pants, "#264653");

  let x0 = lerp(0.1, 0.9, clamp(ch.x, 0, 1)) * W;
  if (P.move > 0) {
    const tx = lerp(0.1, 0.9, clamp(ch.toX ?? ch.x, 0, 1)) * W;
    x0 = lerp(x0, tx, clamp(t / Math.max(dur, 0.1), 0, 1));
  } else if (P.move < 0) x0 += P.move * 80 * f;
  const hipY = GROUND - (upL + loL) + P.dy;

  ctx.save();
  // shadow
  ctx.fillStyle = "rgba(0,0,0,.22)"; ctx.beginPath(); ctx.ellipse(x0, GROUND + 6, 55 * sc, 10 * sc, 0, 0, 7); ctx.fill();
  ctx.translate(x0, hipY);
  if (P.rot) { ctx.translate(0, upL + loL - P.dy); ctx.rotate(P.rot * f); ctx.translate(0, -(upL + loL - P.dy)); }

  const ang = (a) => [Math.sin(a) * f, Math.cos(a)];
  const limb = (sx, sy, a, b, l1, l2) => {
    const [ux, uy] = ang(a); const ex = sx + ux * l1, ey = sy + uy * l1;
    const [vx, vy] = ang(a + b); return [ex, ey, ex + vx * l2, ey + vy * l2];
  };
  const [tx, ty] = [Math.sin(P.lean) * f, -Math.cos(P.lean)];
  const sx = tx * torso, sy = ty * torso;
  const black = "#111";
  const line = (pts, wdt, col) => { ctx.strokeStyle = col; ctx.lineWidth = wdt; ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.beginPath(); ctx.moveTo(pts[0], pts[1]); for (let i = 2; i < pts.length; i += 2) ctx.lineTo(pts[i], pts[i + 1]); ctx.stroke(); };

  // legs (back first)
  const L1 = limb(0, 0, P.ll[0], P.ll[1], upL, loL), L2 = limb(0, 0, P.rl[0], P.rl[1], upL, loL);
  for (const L of [L1, L2]) {
    line([0, 0, L[0], L[1]], 22 * sc, black); line([0, 0, L[0], L[1]], 16 * sc, pants);
    line([L[0], L[1], L[2], L[3]], 7 * sc, black);
    ctx.fillStyle = black; ctx.beginPath(); ctx.ellipse(L[2] + 9 * f * sc, L[3], 13 * sc, 7 * sc, 0, 0, 7); ctx.fill();
  }
  // arm behind
  const A1 = limb(sx, sy, P.la[0], P.la[1], upA, loA);
  line([sx, sy, A1[0], A1[1]], 7 * sc, black); line([A1[0], A1[1], A1[2], A1[3]], 7 * sc, black);
  ctx.fillStyle = black; ctx.beginPath(); ctx.arc(A1[2], A1[3], 6 * sc, 0, 7); ctx.fill();
  // torso shirt
  ctx.save(); ctx.rotate(P.lean * f);
  ctx.fillStyle = black; roundRect(ctx, -25 * sc, -torso - 6 * sc, 50 * sc, torso + 18 * sc, 18 * sc); ctx.fill();
  ctx.fillStyle = shirt; roundRect(ctx, -21 * sc, -torso - 2 * sc, 42 * sc, torso + 10 * sc, 15 * sc); ctx.fill();
  ctx.fillStyle = "rgba(255,255,255,.18)"; roundRect(ctx, -17 * sc, -torso + 2 * sc, 12 * sc, torso * 0.8, 8 * sc); ctx.fill();
  if (ch.main && outfit.tie) { ctx.fillStyle = hex(outfit.accent, "#ffd166"); ctx.beginPath(); ctx.moveTo(0, -torso); ctx.lineTo(7 * sc, -torso + 35 * sc); ctx.lineTo(0, -torso + 50 * sc); ctx.lineTo(-7 * sc, -torso + 35 * sc); ctx.fill(); }
  ctx.fillStyle = pants; ctx.fillRect(-21 * sc, -4 * sc, 42 * sc, 12 * sc);
  ctx.restore();
  // arm in front
  const A2 = limb(sx, sy, P.ra[0], P.ra[1], upA, loA);
  line([sx, sy, A2[0], A2[1]], 18 * sc, black); line([sx, sy, A2[0], A2[1]], 12 * sc, shirt);
  line([A2[0], A2[1], A2[2], A2[3]], 7 * sc, black);
  ctx.fillStyle = black; ctx.beginPath(); ctx.arc(A2[2], A2[3], 6 * sc, 0, 7); ctx.fill();
  if (P.hold) drawHeld(ctx, P.hold, A2[2], A2[3], sc, t, f);

  // head
  const hx = sx + tx * (headR + 6 * sc), hy = sy + ty * (headR + 6 * sc);
  ctx.save(); ctx.translate(hx, hy); ctx.rotate((P.head + P.lean * 0.3) * f);
  ctx.fillStyle = "#fff"; ctx.strokeStyle = black; ctx.lineWidth = 6 * sc;
  ctx.beginPath(); ctx.arc(0, 0, headR, 0, 7); ctx.fill(); ctx.stroke();
  drawFace(ctx, ch.emotion, headR, t, f, P.talk);
  drawHat(ctx, ch.main ? outfit.hat : "none", headR, ch.main ? hex(outfit.accent, "#222") : "#222");
  ctx.restore();
  ctx.restore();
}

function drawFace(ctx, emotion, r, t, f, talk) {
  const E = EMO_FACE[emotion] || EMO_FACE.neutral;
  const k = r / 50;
  const ox = 8 * k * f;
  const blink = (t % 3.3) > 3.18 ? 0.12 : 1;
  for (const side of [-1, 1]) {
    const ex = ox + side * 17 * k, ey = -6 * k;
    const ew = 11 * k * E.eye, eh = 13 * k * E.eye * blink;
    ctx.fillStyle = "#fff"; ctx.strokeStyle = "#111"; ctx.lineWidth = 3 * k;
    ctx.beginPath(); ctx.ellipse(ex, ey, ew, eh, 0, 0, 7); ctx.fill(); ctx.stroke();
    if (blink > 0.5) {
      ctx.fillStyle = "#3d2b1f"; ctx.beginPath(); ctx.arc(ex + 3 * k * f, ey + 1 * k, 6 * k * Math.min(E.eye, 1.1), 0, 7); ctx.fill();
      ctx.fillStyle = "#111"; ctx.beginPath(); ctx.arc(ex + 3 * k * f, ey + 1 * k, 3.4 * k, 0, 7); ctx.fill();
      ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(ex + 5 * k * f, ey - 2 * k, 1.6 * k, 0, 7); ctx.fill();
    }
    // eyebrow: positive brow = inner end up (sad/worried), negative = inner end down (angry)
    const inner = -side * f;
    ctx.strokeStyle = "#111"; ctx.lineWidth = 5 * k; ctx.lineCap = "round";
    const by = ey - eh - 7 * k;
    ctx.beginPath();
    ctx.moveTo(ex + inner * 11 * k, by - E.brow * 10 * k);
    ctx.lineTo(ex - inner * 11 * k, by + E.brow * 6 * k);
    ctx.stroke();
  }
  // mouth
  const mx = ox, my = 22 * k;
  const open = talk ? Math.abs(Math.sin(t * 11)) : 0;
  ctx.lineWidth = 4 * k; ctx.strokeStyle = "#111";
  const filled = (h, w) => { ctx.fillStyle = "#5a0f0f"; ctx.beginPath(); ctx.ellipse(mx, my, w, h, 0, 0, 7); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#fff"; ctx.fillRect(mx - w * 0.6, my - h + 1 * k, w * 1.2, Math.min(5 * k, h * 0.5));
    ctx.fillStyle = "#e5989b"; ctx.beginPath(); ctx.ellipse(mx, my + h * 0.55, w * 0.5, h * 0.3, 0, 0, 7); ctx.fill(); };
  switch (E.mouth) {
    case "smile": if (open > 0.3) filled(8 * k * open + 4 * k, 13 * k); else { ctx.beginPath(); ctx.arc(mx, my - 6 * k, 14 * k, 0.2, Math.PI - 0.2); ctx.stroke(); } break;
    case "grin": filled(12 * k + 3 * k * open, 17 * k); break;
    case "frown": ctx.beginPath(); ctx.arc(mx, my + 12 * k, 13 * k, Math.PI + 0.35, -0.35); ctx.stroke(); break;
    case "grit": ctx.fillStyle = "#fff"; ctx.beginPath(); roundRect(ctx, mx - 15 * k, my - 6 * k, 30 * k, 12 * k, 4 * k); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(mx - 15 * k, my); ctx.lineTo(mx + 15 * k, my); for (let i = -10; i <= 10; i += 7) { ctx.moveTo(mx + i * k, my - 6 * k); ctx.lineTo(mx + i * k, my + 6 * k); } ctx.stroke(); break;
    case "o": filled(8 * k, 7 * k); break;
    case "O": filled(14 * k, 11 * k); break;
    case "side": ctx.beginPath(); ctx.moveTo(mx - 8 * k, my + 2 * k); ctx.lineTo(mx + 10 * k * f, my - 3 * k); ctx.stroke(); break;
    case "wobble": ctx.beginPath(); for (let i = 0; i <= 6; i++) { const x = mx - 12 * k + i * 4 * k, y = my + Math.sin(i * 1.6 + t * 9) * 2.5 * k; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); break;
    default: if (open > 0.3) filled(7 * k * open + 3 * k, 10 * k); else { ctx.beginPath(); ctx.moveTo(mx - 10 * k, my); ctx.lineTo(mx + 10 * k, my); ctx.stroke(); }
  }
  if (emotion === "sad" && Math.sin(t * 2) > 0) { ctx.fillStyle = "#4cc9f0"; ctx.beginPath(); ctx.ellipse(ox - 17 * k, 14 * k + (t * 30 % 20) * k, 3 * k, 5 * k, 0, 0, 7); ctx.fill(); }
  if (emotion === "scared" || emotion === "worried") { ctx.font = `${22 * k}px serif`; ctx.textAlign = "center"; ctx.fillText("💦", -f * 42 * k, -30 * k); }
  if (emotion === "angry") { ctx.font = `${24 * k}px serif`; ctx.textAlign = "center"; ctx.fillText("💢", f * 40 * k, -40 * k); }
}

function drawHat(ctx, hat, r, color) {
  ctx.fillStyle = color; ctx.strokeStyle = "#111"; ctx.lineWidth = 4;
  if (hat === "cap") { ctx.beginPath(); ctx.arc(0, -r * 0.35, r * 0.95, Math.PI, 0); ctx.fill(); ctx.stroke(); ctx.fillRect(-r * 1.1, -r * 0.4, r * 2.3, r * 0.15); }
  if (hat === "tophat") { ctx.fillRect(-r * 0.6, -r * 1.75, r * 1.2, r * 1.0); ctx.strokeRect(-r * 0.6, -r * 1.75, r * 1.2, r * 1.0); ctx.fillRect(-r * 0.95, -r * 0.82, r * 1.9, r * 0.14); }
  if (hat === "beanie") { ctx.beginPath(); ctx.arc(0, -r * 0.3, r * 0.98, Math.PI, 0); ctx.fill(); ctx.stroke(); ctx.beginPath(); ctx.arc(0, -r * 1.3, r * 0.2, 0, 7); ctx.fill(); }
  if (hat === "hair") { ctx.fillStyle = "#2b2b2b"; ctx.beginPath(); ctx.arc(0, -r * 0.25, r * 1.0, Math.PI * 1.05, -0.05 * Math.PI); ctx.quadraticCurveTo(0, -r * 0.55, -r * 0.98, -r * 0.35); ctx.fill(); }
}

function drawHeld(ctx, what, x, y, sc, t, f) {
  ctx.save(); ctx.textAlign = "center"; ctx.textBaseline = "middle";
  if (what === "phone") { ctx.fillStyle = "#222"; roundRect(ctx, x - 12 * sc, y - 34 * sc, 24 * sc, 42 * sc, 5 * sc); ctx.fill(); ctx.fillStyle = "#7dd3fc"; ctx.fillRect(x - 9 * sc, y - 30 * sc, 18 * sc, 32 * sc); }
  if (what === "money") { ctx.font = `${44 * sc}px serif`; ctx.fillText("💵", x + 8 * f * sc, y - 10 * sc); }
  if (what === "box") { ctx.fillStyle = "#c68b59"; ctx.strokeStyle = "#5b3a1a"; ctx.lineWidth = 4; ctx.fillRect(x - 10 * sc, y - 60 * sc, 70 * sc * f, 60 * sc); ctx.strokeRect(x - 10 * sc, y - 60 * sc, 70 * sc * f, 60 * sc); }
  if (what === "zzz") { ctx.font = `${40 * sc}px serif`; ctx.globalAlpha = 0.5 + 0.5 * Math.sin(t * 3); ctx.fillText("💤", x + 40 * sc, y - 120 * sc - (t * 20 % 30)); }
  ctx.restore();
}

// ---------- props & effects ----------
function drawProps(ctx, sc, t) {
  ctx.save(); ctx.textAlign = "center"; ctx.textBaseline = "middle";
  for (const p of sc.props || []) {
    const glyph = PROPS[p.type]; if (!glyph) continue;
    let x = clamp(p.x, 0, 1) * W, y = clamp(p.y, 0, 1) * H, s = clamp(p.size || 1, 0.3, 2.5) * 80, rot = 0, a = 1;
    if (p.motion === "float") y += Math.sin(t * 2 + x) * 12;
    if (p.motion === "pulse") s *= 1 + 0.12 * Math.sin(t * 5);
    if (p.motion === "spin") rot = t * 2;
    if (p.motion === "fall") y = ((y + t * 160) % (GROUND + 40));
    if (p.motion === "fly_in") { const k = ease(clamp(t / 0.7, 0, 1)); x = lerp(x > W / 2 ? W + 120 : -120, x, k); a = k; }
    ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.rotate(rot);
    ctx.shadowColor = "rgba(0,0,0,.35)"; ctx.shadowBlur = 12; ctx.shadowOffsetY = 6;
    ctx.font = `${s}px serif`; ctx.fillText(glyph, 0, 0);
    ctx.restore();
  }
  ctx.restore();
}

function drawEffect(ctx, sc, t, seed) {
  const r = rand(seed + 7);
  ctx.save(); ctx.textAlign = "center";
  if (sc.effect === "rain" || sc.light === "storm") {
    ctx.strokeStyle = "rgba(200,220,255,.6)"; ctx.lineWidth = 2; ctx.beginPath();
    for (let i = 0; i < 140; i++) { const x = (r() * W + t * 120) % W, y = (r() * H + t * 900) % H; ctx.moveTo(x, y); ctx.lineTo(x - 6, y + 22); }
    ctx.stroke();
  }
  const fallers = { money_rain: "💸", hearts: "💖", stars: "⭐", sparkles: "✨" }[sc.effect];
  if (fallers) for (let i = 0; i < 18; i++) {
    const x = r() * W, sp = 80 + r() * 120, y = ((r() * H + t * sp) % (H + 80)) - 40;
    ctx.globalAlpha = sc.effect === "sparkles" ? 0.5 + 0.5 * Math.sin(t * 4 + i) : 0.95;
    ctx.font = `${26 + r() * 26}px serif`; ctx.fillText(fallers, x + Math.sin(t * 2 + i) * 20, sc.effect === "sparkles" ? r() * GROUND : y);
  }
  if (sc.effect === "fire") for (let i = 0; i < 26; i++) {
    const x = (i / 26) * W + Math.sin(t * 7 + i) * 10, h = 60 + 50 * Math.abs(Math.sin(t * 6 + i * 1.7));
    const g = ctx.createLinearGradient(0, H, 0, H - h); g.addColorStop(0, "rgba(255,80,0,.85)"); g.addColorStop(1, "rgba(255,220,0,0)");
    ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(x, H - h / 2, 30, h / 2, 0, 0, 7); ctx.fill();
  }
  ctx.restore();
}

// ---------- captions ----------
export function captionChunks(text, maxWords = 7) {
  const words = text.split(/\s+/).filter(Boolean);
  const out = [];
  for (let i = 0; i < words.length; i += maxWords) out.push(words.slice(i, i + maxWords).join(" "));
  return out.length ? out : [""];
}

function drawCaption(ctx, text) {
  if (!text) return;
  ctx.save();
  ctx.direction = "rtl"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.font = "800 44px Cairo, sans-serif";
  const w = Math.min(W - 80, ctx.measureText(text).width + 60);
  ctx.fillStyle = "rgba(0,0,0,.62)"; roundRect(ctx, W / 2 - w / 2, H - 112, w, 74, 18); ctx.fill();
  ctx.lineWidth = 6; ctx.strokeStyle = "#000"; ctx.strokeText(text, W / 2, H - 74, W - 120);
  ctx.fillStyle = "#fff"; ctx.fillText(text, W / 2, H - 74, W - 120);
  ctx.restore();
}

// ---------- timeline ----------
export function buildTimeline(beats, specs, wps, audioDuration) {
  const base = beats.map((b) => Math.max(1.6, b.text.split(/\s+/).filter(Boolean).length / wps));
  const sum = base.reduce((a, b) => a + b, 0);
  const k = audioDuration ? audioDuration / sum : 1;
  let at = 0;
  const items = beats.map((b, i) => {
    const dur = base[i] * k;
    const it = { start: at, dur, beat: b, spec: normalizeSpec(specs[i]), chunks: captionChunks(b.text) };
    at += dur; return it;
  });
  return { items, total: at };
}

const num = (v, d) => (typeof v === "number" && isFinite(v) ? v : d);
const pick = (v, list, d) => (list.includes(v) ? v : d);
/** Fill in anything missing or invalid so a bad spec never breaks the render. */
export function normalizeSpec(sc) {
  sc = sc && typeof sc === "object" ? sc : {};
  const chars = (Array.isArray(sc.characters) ? sc.characters : []).slice(0, 4).map((c) => ({
    main: !!c.main,
    x: clamp(num(c.x, 0.5), 0, 1), toX: clamp(num(c.toX, num(c.x, 0.5)), 0, 1),
    facing: c.facing === "left" ? "left" : "right",
    scale: clamp(num(c.scale, 1), 0.6, 1.4),
    shirt: hex(c.shirt, "#e76f51"), pants: hex(c.pants, "#264653"),
    emotion: pick(c.emotion, EMOTIONS, "neutral"), action: pick(c.action, ACTIONS, "idle"),
  }));
  if (!chars.length) chars.push({ main: true, x: 0.5, toX: 0.5, facing: "right", scale: 1, shirt: "#e76f51", pants: "#264653", emotion: "neutral", action: "idle" });
  return {
    bg: pick(sc.bg, BACKGROUNDS, "abstract"), light: pick(sc.light, LIGHTS, "day"),
    sky: hex(sc.sky, "#8ecae6"), ground: hex(sc.ground, "#6a994e"), effect: pick(sc.effect, EFFECTS, "none"),
    props: (Array.isArray(sc.props) ? sc.props : []).filter((p) => PROPS[p?.type]).slice(0, 5).map((p) => ({
      type: p.type, x: clamp(num(p.x, 0.5), 0, 1), y: clamp(num(p.y, 0.5), 0, 1), size: clamp(num(p.size, 1), 0.3, 2.5), motion: p.motion || "none",
    })),
    characters: chars,
  };
}

/** Draw the frame at global time T. */
export function renderFrame(ctx, tl, T, outfit, { captions = true } = {}) {
  const items = tl.items;
  let i = items.findIndex((it) => T < it.start + it.dur);
  if (i < 0) i = items.length - 1;
  const it = items[i];
  const t = clamp(T - it.start, 0, it.dur);
  const sc = it.spec;
  const seed = i * 13 + 5;

  ctx.save();
  if (sc.effect === "shake") ctx.translate(Math.sin(T * 40) * 6, Math.cos(T * 37) * 4);
  if (sc.effect === "zoom_in") { const z = 1 + 0.08 * (t / it.dur); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2); }
  drawBackground(ctx, sc, T, seed);
  drawProps(ctx, sc, t);
  const chars = [...(sc.characters || [])].sort((a, b) => (a.scale || 1) - (b.scale || 1));
  for (const ch of chars) drawFigure(ctx, ch, t, it.dur, outfit);
  drawEffect(ctx, sc, T, seed);
  drawLight(ctx, sc, T, seed);
  ctx.restore();

  if (captions) {
    const n = it.chunks.length;
    const ci = Math.min(n - 1, Math.floor((t / it.dur) * n));
    drawCaption(ctx, it.chunks[ci]);
  }
  // quick dip at beat boundaries
  const edge = Math.min(t, it.dur - t);
  if (edge < 0.12 && T > 0.05) { ctx.fillStyle = `rgba(0,0,0,${(1 - edge / 0.12) * 0.55})`; ctx.fillRect(0, 0, W, H); }
}

// ---------- music ----------
const MOODS = {
  calm: { chords: [[261.6, 329.6, 392], [220, 261.6, 329.6], [174.6, 220, 261.6], [196, 246.9, 293.7]], type: "sine", bpm: 60 },
  tense: { chords: [[220, 261.6, 311.1], [207.7, 246.9, 293.7], [196, 233.1, 293.7], [207.7, 246.9, 311.1]], type: "triangle", bpm: 72 },
  upbeat: { chords: [[261.6, 329.6, 392], [392, 493.9, 587.3], [220, 261.6, 329.6], [349.2, 440, 523.3]], type: "triangle", bpm: 100 },
  mystery: { chords: [[146.8, 174.6, 220], [155.6, 185, 233.1], [130.8, 155.6, 196], [138.6, 164.8, 207.7]], type: "sine", bpm: 54 },
};
export const MOOD_LABELS = { none: "بدون موسيقى", calm: "هادية", tense: "مشدودة", upbeat: "حماسية", mystery: "غامضة" };

/** Schedules a simple generated music bed on `dest` from `when` for `seconds`. */
export function scheduleMusic(actx, dest, mood, when, seconds, volume = 0.12) {
  const m = MOODS[mood]; if (!m) return () => {};
  const master = actx.createGain(); master.gain.value = volume;
  const lp = actx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 1400;
  master.connect(lp); lp.connect(dest);
  const barLen = (60 / m.bpm) * 4;
  const nodes = [];
  for (let b = 0, t = when; t < when + seconds; b++, t += barLen) {
    const chord = m.chords[b % m.chords.length];
    for (const fq of chord) {
      const o = actx.createOscillator(); o.type = m.type; o.frequency.value = fq;
      const g = actx.createGain(); g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(0.28, t + barLen * 0.25); g.gain.linearRampToValueAtTime(0.0, t + barLen * 1.05);
      o.connect(g); g.connect(master); o.start(t); o.stop(t + barLen * 1.1); nodes.push(o);
    }
    // soft pulse on each beat
    for (let k = 0; k < 4; k++) {
      const bt = t + (barLen / 4) * k; if (bt > when + seconds) break;
      const o = actx.createOscillator(); o.type = "sine"; o.frequency.value = chord[0] / 2;
      const g = actx.createGain(); g.gain.setValueAtTime(0.35, bt); g.gain.exponentialRampToValueAtTime(0.001, bt + 0.4);
      o.connect(g); g.connect(master); o.start(bt); o.stop(bt + 0.45); nodes.push(o);
    }
  }
  const end = when + seconds;
  master.gain.setValueAtTime(volume, Math.max(when, end - 1.5)); master.gain.linearRampToValueAtTime(0, end);
  return () => nodes.forEach((n) => { try { n.stop(); } catch { /* already stopped */ } });
}

export function pickMime() {
  const list = ["video/mp4;codecs=avc1.42E01E,mp4a.40.2", "video/mp4", "video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm"];
  if (typeof MediaRecorder === "undefined") return null;
  return list.find((m) => MediaRecorder.isTypeSupported(m)) || "";
}
