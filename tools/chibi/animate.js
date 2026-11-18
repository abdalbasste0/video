// Animate a chibi-map story into a silent video.
// usage: node animate.js --chibi story.chibi.json --voiced voiced_story.json --out raw.mp4 [--aspect 16x9|9x16] [--short] [--fps 24] [--preview N]
// Scene durations come from voiced_story.json (the voiceover), visuals from story.chibi.json (same scene order).
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const { chromium } = require("playwright");
const d3 = require("d3-geo");
const { character, DEFS, mapLayer, shade, INK } = require("./chibi");

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith("--") ? a.concat([[v.slice(2), arr[i + 1] && !arr[i + 1].startsWith("--") ? arr[i + 1] : true]]) : a), []));
const FPS = Number(args.fps || 24);
const ASPECT = args.aspect || "16x9";
const [W, H] = ASPECT === "9x16" ? [1080, 1920] : [1920, 1080];
const V = ASPECT === "9x16";
const FONT = "Inter Display, Inter, sans-serif";

const chibi = JSON.parse(fs.readFileSync(args.chibi, "utf8"));
const voiced = JSON.parse(fs.readFileSync(args.voiced, "utf8"));
const baseDir = path.dirname(path.resolve(args.chibi));
const castDir = path.join(__dirname, "characters");

function castSpec(id) {
  const c = (chibi.cast || {})[id];
  if (c && typeof c === "object") return c;
  const f = path.join(castDir, (c || id) + ".json");
  if (fs.existsSync(f)) return JSON.parse(fs.readFileSync(f, "utf8"));
  return GENERIC[id] || GENERIC.person;
}
const GENERIC = {
  investor: { skin: "#f0cba8", hair: { style: "receding", color: "#8a8a8a" }, face: { mouth: "smirk", glasses: "rect" }, outfit: { type: "blazer", color: "#2b2f3a", tie: "#9c2b2b" } },
  engineer: { skin: "#d9a77d", hair: { style: "short-side", color: "#1b1410" }, face: { mouth: "smile" }, outfit: { type: "hoodie", color: "#5a6b52" } },
  user: { skin: "#e9c39b", hair: { style: "bob", color: "#6b3b20" }, face: { mouth: "smile" }, outfit: { type: "tshirt", color: "#c7678f" } },
  person: { skin: "#f1cfb0", hair: { style: "short-side", color: "#3b2a20" }, face: { mouth: "smile" }, outfit: { type: "tshirt", color: "#4f86c6" } },
};

// ---------------------------------------------------------------- props (drawn at local origin = bottom centre)
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
function wrap(text, n) {
  const words = String(text).split(/\s+/), lines = [""];
  for (const w of words) { if ((lines[lines.length - 1] + " " + w).trim().length > n) lines.push(w); else lines[lines.length - 1] = (lines[lines.length - 1] + " " + w).trim(); }
  return lines;
}
function chart(type, x, y, w, h) {
  if (type === "bars") return [0.25, 0.45, 0.7, 1].map((v, i) => `<rect x="${x + i * w / 4 + 6}" y="${y + h - h * v}" width="${w / 4 - 12}" height="${h * v}" fill="${["#4f86c6", "#5aa36b", "#e0a03f", "#c4544d"][i]}" stroke="${INK}" stroke-width="2"/>`).join("");
  const up = type !== "down";
  const pts = Array.from({ length: 8 }, (_, i) => { const f = i / 7; const v = up ? f : 1 - f; return [x + f * w, y + h - (0.1 + 0.8 * v + Math.sin(i * 2.1) * 0.06) * h]; });
  return `<polyline points="${pts.map(p => p.join(",")).join(" ")}" fill="none" stroke="${up ? "#2f8a4a" : "#c4302b"}" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>`;
}
const PROPS = {
  board(e) { // easel with a paper board
    const t = e.title ? `<text x="0" y="-232" text-anchor="middle" font-family="${FONT}" font-weight="900" font-size="26" fill="${INK}">${esc(e.title)}</text>` : "";
    const lines = (e.lines || []).map((l, i) => `<text x="0" y="${-196 + i * 30}" text-anchor="middle" font-family="${FONT}" font-weight="700" font-size="24" fill="#3a3027">${esc(l)}</text>`).join("");
    return `<path d="M-90,0 L-60,-150 M90,0 L60,-150 M0,-20 L0,-150" stroke="#6b4a2c" stroke-width="10" stroke-linecap="round"/>
      <rect x="-130" y="-262" width="260" height="170" rx="6" fill="#f6efdc" stroke="#6b4a2c" stroke-width="8"/>
      ${t}${e.chart ? chart(e.chart, -110, -215, 220, 108) : ""}${lines}`;
  },
  money(e) {
    return `<path d="M-48,0 C-80,-10 -78,-80 -36,-104 L-24,-120 C-30,-132 30,-132 24,-120 L36,-104 C78,-80 80,-10 48,0 Z" fill="#c9a45a" stroke="${INK}" stroke-width="4"/>
      <path d="M-26,-121 Q0,-110 26,-121" fill="none" stroke="${INK}" stroke-width="4"/>
      <text x="0" y="-36" text-anchor="middle" font-family="${FONT}" font-weight="900" font-size="58" fill="#2f6b3a">$</text>
      ${e.text ? `<text x="0" y="46" text-anchor="middle" font-family="${FONT}" font-weight="900" font-size="44" fill="#fff" stroke="${INK}" stroke-width="8" paint-order="stroke">${esc(e.text)}</text>` : ""}`;
  },
  card(e) {
    const big = e.size || 78, w = Math.max(220, String(e.text).length * big * 0.62 + 60), sub = e.sub ? 66 : 0;
    return `<g transform="rotate(${e.tilt ?? -2})"><rect x="${-w / 2}" y="${-(big + 50 + sub)}" width="${w}" height="${big + 50 + sub}" rx="14" fill="#f8f2e2" stroke="${INK}" stroke-width="5"/>
      <text data-count="${e.count ? esc(e.text) : ""}" x="0" y="${-(sub + 30)}" text-anchor="middle" font-family="${FONT}" font-weight="900" font-size="${big}" fill="${e.color || "#2f6b3a"}">${esc(e.text)}</text>
      ${e.sub ? `<text x="0" y="-24" text-anchor="middle" font-family="${FONT}" font-weight="800" font-size="34" fill="${e.subColor || "#c4302b"}">${esc(e.sub)}</text>` : ""}</g>`;
  },
  stamp(e) {
    const t = esc(e.text || "REJECTED"), w = t.length * 44 + 60;
    return `<g transform="rotate(-12)" opacity=".92"><rect x="${-w / 2}" y="-110" width="${w}" height="100" rx="12" fill="none" stroke="#c4302b" stroke-width="10"/>
      <text x="0" y="-38" text-anchor="middle" font-family="${FONT}" font-weight="900" font-size="66" fill="#c4302b" letter-spacing="4">${t}</text></g>`;
  },
  bubble(e) {
    const lines = wrap(e.text, 20), w = Math.max(...lines.map(l => l.length)) * 19 + 50, h = lines.length * 38 + 34;
    return `<path d="M${-w / 2},${-h - 30} h${w} a16,16 0 0 1 16,16 v${h - 32} a16,16 0 0 1 -16,16 h${-w / 2 + 40} l-34,30 l6,-30 h${-w / 2 + 6} a16,16 0 0 1 -16,-16 v${-(h - 32)} a16,16 0 0 1 16,-16 z" fill="#fff" stroke="${INK}" stroke-width="4" transform="translate(16,0)"/>
      ${lines.map((l, i) => `<text x="16" y="${-h - 30 + 44 + i * 38}" text-anchor="middle" font-family="${FONT}" font-weight="800" font-size="31" fill="${INK}">${esc(l)}</text>`).join("")}`;
  },
  laptop() {
    return `<path d="M-62,0 L62,0 L52,-12 L-52,-12 Z" fill="#9aa3b2" stroke="${INK}" stroke-width="4"/><rect x="-48" y="-84" width="96" height="70" rx="6" fill="#2b3140" stroke="${INK}" stroke-width="4"/><rect x="-40" y="-76" width="80" height="54" fill="#6fb3ff"/><path d="M-30,-62 h44 M-30,-50 h60 M-30,-38 h34" stroke="#e6f2ff" stroke-width="5" stroke-linecap="round"/>`;
  },
  building(e) {
    let win = "";
    for (let r = 0; r < 6; r++) for (let c = 0; c < 4; c++) win += `<rect x="${-62 + c * 32}" y="${-300 + r * 44}" width="20" height="26" fill="${(r + c) % 3 ? "#f3e2a2" : "#8fb2c0"}" stroke="${INK}" stroke-width="2"/>`;
    return `<rect x="-80" y="-330" width="160" height="330" fill="#c9c2b2" stroke="${INK}" stroke-width="5"/>${win}<rect x="-22" y="-56" width="44" height="56" fill="#6b4a2c" stroke="${INK}" stroke-width="4"/>
      ${e.label ? `<rect x="-96" y="-376" width="192" height="50" rx="8" fill="${e.color || "#2f63c6"}" stroke="${INK}" stroke-width="4"/><text x="0" y="-340" text-anchor="middle" font-family="${FONT}" font-weight="900" font-size="30" fill="#fff">${esc(e.label)}</text>` : ""}`;
  },
  sign(e) {
    return `<rect x="-6" y="-120" width="12" height="120" fill="#6b4a2c" stroke="${INK}" stroke-width="3"/><rect x="${-(String(e.text).length * 13 + 30)}" y="-170" width="${String(e.text).length * 26 + 60}" height="62" rx="8" fill="${e.color || "#f6efdc"}" stroke="${INK}" stroke-width="5"/><text x="0" y="-127" text-anchor="middle" font-family="${FONT}" font-weight="900" font-size="34" fill="${e.textColor || INK}">${esc(e.text)}</text>`;
  },
  title(e) {
    const lines = e.lines || [e.text];
    return lines.map((l, i) => `<text x="0" y="${i * (i ? 70 : 110)}" text-anchor="middle" font-family="${FONT}" font-weight="900" font-size="${i ? 54 : 100}" fill="${i ? "#f6efdc" : "#ffd36a"}" stroke="${INK}" stroke-width="${i ? 9 : 14}" paint-order="stroke" stroke-linejoin="round">${esc(l)}</text>`).join("");
  },
  date(e) {
    const t = esc(e.text), w = t.length * 34 + 60;
    return `<rect x="${-w / 2}" y="0" width="${w}" height="76" rx="10" fill="#2e211a" opacity=".88"/><text x="0" y="56" text-anchor="middle" font-family="${FONT}" font-weight="900" font-size="54" fill="#ffd36a">${t}</text>`;
  },
};

// ---------------------------------------------------------------- scene assembly
const ease = k => (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2);

function sceneMarkup(vis, idx) {
  const m = Object.assign({ center: [0, 30], scale: 300 }, vis.map || {});
  const sc = (m.scale || 300) * (V ? 0.95 : 1) * (H / 1080) * (V ? 0.56 : 1);
  const proj = d3.geoMercator().center(m.center).scale(sc).translate([W / 2, H / 2]);
  const P = (ll) => proj(ll);
  const els = [];
  const chars = (vis.characters || []);
  const charScale = V ? 1.45 : 1.5;
  const slotY = V ? H * 0.64 : H * 0.8;
  const BUBBLE = V ? 1.5 : 1.45;
  const spread = V ? 260 : 330;
  chars.forEach((c, i) => {
    const n = chars.length;
    let x, y;
    if (c.at) [x, y] = P(c.at); else if (c.pos) [x, y] = [c.pos[0] * W, c.pos[1] * H];
    else { x = W / 2 + (i - (n - 1) / 2) * spread; y = slotY; }
    const spec = JSON.parse(JSON.stringify(castSpec(c.id)));
    spec.face = Object.assign({}, spec.face, c.face || {}, c.mouth ? { mouth: c.mouth } : {}, c.brows ? { brows: c.brows } : {});
    let to = null; if (c.to) to = Array.isArray(c.to) && c.to.length === 2 && Math.abs(c.to[0]) > 1.5 ? P(c.to) : [c.to[0] * W, c.to[1] * H];
    els.push({ kind: "char", world: !!c.at, x, y, to, s: (c.scale || 1) * charScale, flip: !!c.flip, enter: c.enter || "pop", at: c.enterAt ?? 0.15 + i * 0.35,
      moveAt: c.moveAt || [0.3, 0.75], svg: character(spec, {}) });
  });
  (vis.props || []).forEach((p, i) => {
    const kind = p.type;
    if (kind === "arrow") {
      const [x1, y1] = P(p.from), [x2, y2] = P(p.to);
      const mx = (x1 + x2) / 2, my = Math.min(y1, y2) - Math.hypot(x2 - x1, y2 - y1) * 0.25;
      const ang = Math.atan2(y2 - my, x2 - mx) * 180 / Math.PI;
      els.push({ kind: "arrow", world: true, x: 0, y: 0, s: 1, at: p.enterAt ?? 0.4, enter: "draw",
        svg: `<path data-draw="1" d="M${x1},${y1} Q${mx},${my} ${x2},${y2}" fill="none" stroke="#c4302b" stroke-width="8" stroke-dasharray="22 14" stroke-linecap="round"/><path data-head="1" d="M0,0 L-26,-14 L-26,14 Z" fill="#c4302b" transform="translate(${x2},${y2}) rotate(${ang})" opacity="0"/>` });
      return;
    }
    if (kind === "crowd") {
      const n = Math.min(p.count || 12, 40), cols = Math.ceil(Math.sqrt(n * (V ? 1 : 2)));
      let x0, y0; if (p.at) [x0, y0] = P(p.at); else [x0, y0] = [(p.pos || [0.5, 0.8])[0] * W, (p.pos || [0.5, 0.8])[1] * H];
      const looks = ["user", "engineer", "person", "investor"];
      for (let j = 0; j < n; j++) {
        const r = Math.floor(j / cols), cc = j % cols;
        const spec = JSON.parse(JSON.stringify(GENERIC[looks[j % 3]]));
        spec.outfit.color = ["#4f86c6", "#c7678f", "#5aa36b", "#e07b3f", "#9b6fd1", "#3fa7a3"][j % 6];
        spec.skin = ["#f1cfb0", "#d9a77d", "#a8724c", "#e9c39b", "#8d5a3b"][(j * 7) % 5];
        els.push({ kind: "mini", world: !!p.at, x: x0 + (cc - (cols - 1) / 2) * 62, y: y0 + r * 46 - 20 * Math.floor(n / cols) / 2, s: 0.34, at: (p.enterAt ?? 0.3) + j * 0.06, enter: "pop", svg: character(spec) });
      }
      return;
    }
    let x, y;
    if (p.at) [x, y] = P(p.at);
    else if (p.pos) [x, y] = [p.pos[0] * W, p.pos[1] * H];
    else if (p.near !== undefined && els.filter(e => e.kind === "char")[p.near]) { const c = els.filter(e => e.kind === "char")[p.near]; x = c.x + (p.side === "left" ? -1 : 1) * (kind === "bubble" ? 70 : 200) * c.s; y = kind === "bubble" ? c.y - 290 * c.s : c.y; }
    else { const def = { board: [0.5, 0.62], money: [0.78, 0.78], card: [0.5, 0.36], stamp: [0.5, 0.42], laptop: [0.62, 0.8], building: [0.25, 0.85], sign: [0.75, 0.8], title: [0.5, 0.42], date: [0.5, 0.04], bubble: [0.5, 0.35] }[kind] || [0.5, 0.5]; [x, y] = [def[0] * W, def[1] * H]; }
    const s = (p.scale || 1) * ({ board: V ? 1.25 : 1.15, money: 1, card: 1, stamp: V ? 1.1 : 1.3, laptop: 1, building: V ? 0.9 : 1, sign: 1, title: V ? 0.9 : 1, date: 1, bubble: BUBBLE }[kind] || 1);
    els.push({ kind, world: !!p.at, x, y, s, at: p.enterAt ?? (kind === "date" ? 0 : 0.6 + i * 0.4), enter: kind === "stamp" ? "slam" : kind === "date" ? "drop" : "pop", svg: (PROPS[kind] || PROPS.sign)(p) });
  });
  if (vis.date) els.push({ kind: "date", world: false, x: W / 2, y: V ? 150 : 30, s: 1, at: 0, enter: "drop", svg: PROPS.date({ text: vis.date }) });
  return { map: m, mapSpec: Object.assign({}, m, { scale: sc }), els, camera: vis.camera || { zoom: 1.06 } };
}

// ---------------------------------------------------------------- page runtime (runs inside the browser)
const RUNTIME = `
const ease = k => k < 0.5 ? 2*k*k : 1 - Math.pow(-2*k+2,2)/2;
const backOut = k => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3*Math.pow(k-1,3) + c1*Math.pow(k-1,2); };
window.update = function(t, dur) {
  const S = window.SCENE, k = Math.min(1, t / dur);
  const z = 1 + ((S.camera.zoom || 1) - 1) * ease(k);
  const fx = S.camera.fx ?? S.W/2, fy = S.camera.fy ?? S.H/2;
  document.getElementById("world").setAttribute("transform", "translate(" + (fx - fx*z) + "," + (fy - fy*z) + ") scale(" + z + ")");
  S.els.forEach((e, i) => {
    const g = document.getElementById("e" + i), lt = t - e.at;
    if (lt < 0) { g.setAttribute("opacity", 0); return; }
    let x = e.x, y = e.y, s = e.s, rot = 0, op = 1;
    if (e.enter === "pop") s *= lt < .45 ? Math.max(0, backOut(lt/.45)) : 1;
    if (e.enter === "slam") { const q = Math.min(1, lt/.25); s *= 2.2 - 1.2*q; op = q; }
    if (e.enter === "drop") { const q = Math.min(1, lt/.4); y -= (1-ease(q))*120; op = q; }
    if (e.enter === "draw") {
      const p = g.querySelector("[data-draw]"), L = p.getTotalLength(), q = Math.min(1, lt/1.3);
      p.style.strokeDasharray = L; p.style.strokeDashoffset = L*(1-ease(q));
      g.querySelector("[data-head]").setAttribute("opacity", q >= 1 ? 1 : 0);
    }
    if (e.to) { const q = ease(Math.min(1, Math.max(0, (k - e.moveAt[0]) / (e.moveAt[1]-e.moveAt[0])))); x += (e.to[0]-e.x)*q; y += (e.to[1]-e.y)*q - Math.abs(Math.sin(q*Math.PI*6))*14*(q>0&&q<1); }
    if (e.kind === "char" || e.kind === "mini") {
      y -= Math.abs(Math.sin(t*2.3 + i*1.3)) * 4 * (e.kind === "char" ? 1 : .6);
      rot = Math.sin(t*1.7 + i) * 1.6;
      const eyes = g.querySelector("[data-eyes]");
      if (eyes) { const ph = (t + i*1.37) % 3.6; const b = ph < .12 ? .12 : 1; eyes.setAttribute("transform", "translate(0,-186) scale(1," + b + ") translate(0,186)"); }
    }
    g.querySelectorAll("[data-count]").forEach(n => { const src = n.getAttribute("data-count"); if (!src) return; const m = src.match(/^([^0-9]*)([0-9][0-9,.]*)(.*)$/); if (!m) return; const num = parseFloat(m[2].replace(/,/g,"")), dec = (m[2].split(".")[1]||"").length, q = ease(Math.min(1, lt/1.4)); let v = (num*q).toFixed(dec); if (m[2].includes(",")) v = Number(v).toLocaleString("en-US",{minimumFractionDigits:dec,maximumFractionDigits:dec}); n.textContent = m[1] + v + m[3]; });
    g.setAttribute("opacity", op);
    g.setAttribute("transform", "translate(" + x + "," + y + ") rotate(" + rot + ") scale(" + (e.flip ? -s : s) + "," + s + ")");
  });
  const f = Math.min(1, t/.3, (dur - t)/.3); document.getElementById("fade").setAttribute("opacity", 1 - Math.max(0, f));
};`;

async function main() {
  let idx = voiced.scenes.map((_, i) => i);
  if (args.short) idx = idx.filter(i => voiced.scenes[i].short);
  if (args.preview) { let t = 0; idx = idx.filter(i => (t += voiced.scenes[i].dur) - voiced.scenes[i].dur < Number(args.preview)); }
  const browser = await chromium.launch();
  const mapPage = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1.4 });
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  const ff = spawn("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", args.out], { stdio: ["pipe", "inherit", "inherit"] });
  const mapCache = {};
  let frameNo = 0;
  for (const i of idx) {
    const vs = (chibi.scenes || [])[i] || {};
    const dur = voiced.scenes[i].dur;
    const sc = sceneMarkup(vs, i);
    const key = JSON.stringify(sc.mapSpec);
    if (!mapCache[key]) {
      const m = mapLayer(sc.mapSpec, W, H);
      await mapPage.setContent(`<html><body style="margin:0"><svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}<g filter="url(#paper)">${m.svg}</g></svg></body></html>`);
      mapCache[key] = "data:image/png;base64," + (await mapPage.screenshot({ type: "png" })).toString("base64");
    }
    const world = sc.els.map((e, j) => e.world ? `<g id="e${j}">${e.svg}</g>` : "").join("");
    const screen = sc.els.map((e, j) => !e.world ? `<g id="e${j}">${e.svg}</g>` : "").join("");
    const overlay = vs.dim ? `<rect width="${W}" height="${H}" fill="#1d1612" opacity="${vs.dim}"/>` : "";
    await page.setContent(`<html><body style="margin:0;background:#000"><svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${DEFS}
      <g id="world"><image href="${mapCache[key]}" width="${W}" height="${H}"/>${world}</g>${overlay}${screen}<rect id="fade" width="${W}" height="${H}" fill="#000" opacity="0"/></svg>
      <script>${RUNTIME}</script></body></html>`);
    const cam = sc.camera; const proj = d3.geoMercator().center(sc.map.center).scale(sc.mapSpec.scale).translate([W / 2, H / 2]);
    const [fx, fy] = cam.focus ? proj(cam.focus) : [W / 2, H / 2];
    await page.evaluate(S => { window.SCENE = S; }, { W, H, camera: { zoom: cam.zoom ?? 1.06, fx, fy }, els: sc.els.map(e => ({ kind: e.kind, x: e.x, y: e.y, s: e.s, at: e.at, enter: e.enter, to: e.to, moveAt: e.moveAt, flip: e.flip })) });
    const n = Math.round(dur * FPS);
    for (let f = 0; f < n; f++, frameNo++) {
      await page.evaluate(([t, d]) => window.update(t, d), [f / FPS, dur]);
      const buf = await page.screenshot({ type: "jpeg", quality: 90 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    }
    process.stderr.write(`  scene ${i + 1}: ${dur.toFixed(1)}s, ${sc.els.length} elements\n`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  await browser.close();
  console.log(JSON.stringify({ frames: frameNo, seconds: frameNo / FPS }));
}
main();
