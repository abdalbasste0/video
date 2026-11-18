// Chibi characters + vintage map backgrounds as SVG strings (no browser needed to build them).
// A character is a big-headed "peg doll" figure: round head, rounded trunk with no legs, short arms.
// Every look is driven by a plain JSON spec so each real person gets their own recognisable version.

const d3 = require("d3-geo");
const topo = require("topojson-client");
const world = require("world-atlas/countries-50m.json");
const usStates = require("us-atlas/states-10m.json");

const INK = "#2e211a";

function shade(hex, amt) {
  const n = parseInt(hex.slice(1), 16);
  const c = v => Math.max(0, Math.min(255, Math.round(v + amt)));
  return "#" + ((c(n >> 16) << 16) | (c((n >> 8) & 255) << 8) | c(n & 255)).toString(16).padStart(6, "0");
}

let uid = 0;

// ---------------------------------------------------------------- hair
function hairBack(h) {
  if (!h || h.style === "bald") return "";
  if (h.style === "long") return `<path d="M-80,-200 C-92,-140 -84,-96 -60,-80 L60,-80 C84,-96 92,-140 80,-200 Z" fill="${h.color}" stroke="${INK}" stroke-width="3.5"/>`;
  if (h.style === "bob") return `<path d="M-82,-205 C-90,-160 -84,-128 -66,-118 L66,-118 C84,-128 90,-160 82,-205 Z" fill="${h.color}" stroke="${INK}" stroke-width="3.5"/>`;
  return "";
}
function hairFront(h) {
  if (!h || h.style === "bald") return "";
  const c = h.color, hi = shade(c, 30);
  const styles = {
    // short, slightly messy, side part: common tech-founder cut
    "short-side": `<path d="M-74,-196 C-80,-246 -40,-272 4,-268 C52,-266 82,-238 76,-192 C70,-206 60,-222 40,-228 C30,-214 6,-208 -18,-214 C-36,-218 -50,-222 -56,-226 C-64,-216 -70,-206 -74,-196 Z" fill="${c}" stroke="${INK}" stroke-width="3.5" stroke-linejoin="round"/>
      <path d="M-30,-252 C-6,-262 26,-260 48,-246" fill="none" stroke="${hi}" stroke-width="5" stroke-linecap="round" opacity=".55"/>`,
    "buzz": `<path d="M-72,-198 C-76,-250 -36,-266 2,-266 C44,-266 78,-246 72,-198 C60,-224 30,-234 0,-234 C-30,-234 -60,-224 -72,-198 Z" fill="${c}" stroke="${INK}" stroke-width="3.5"/>`,
    "receding": `<path d="M-74,-196 C-80,-232 -64,-252 -46,-258 C-40,-236 -50,-214 -60,-204 Z M74,-196 C80,-232 64,-252 46,-258 C40,-236 50,-214 60,-204 Z" fill="${c}" stroke="${INK}" stroke-width="3.5"/>`,
    "curly": Array.from({ length: 11 }, (_, i) => { const a = Math.PI * (1.05 + i * 0.09); return `<circle cx="${(Math.cos(a) * 66).toFixed(1)}" cy="${(-196 + Math.sin(a) * 62).toFixed(1)}" r="22" fill="${c}" stroke="${INK}" stroke-width="3"/>`; }).join(""),
    "long": `<path d="M-76,-194 C-82,-250 -38,-272 4,-268 C50,-266 84,-240 76,-194 C64,-226 30,-240 -6,-232 C-36,-226 -62,-214 -76,-194 Z" fill="${c}" stroke="${INK}" stroke-width="3.5"/>`,
    "bob": `<path d="M-78,-190 C-84,-250 -38,-272 4,-268 C50,-266 86,-240 78,-190 C66,-222 34,-236 -2,-230 C-34,-226 -64,-212 -78,-190 Z" fill="${c}" stroke="${INK}" stroke-width="3.5"/>`,
  };
  return styles[h.style] || styles["short-side"];
}

// ---------------------------------------------------------------- face
function face(f, skin) {
  const blush = `<ellipse cx="-40" cy="-168" rx="13" ry="7" fill="#e8907a" opacity=".35"/><ellipse cx="40" cy="-168" rx="13" ry="7" fill="#e8907a" opacity=".35"/>`;
  const eye = (x) => `<ellipse cx="${x}" cy="-186" rx="6" ry="8" fill="#1d1612"/><circle cx="${x + 2}" cy="-189" r="2.2" fill="#fff"/>`;
  const browY = f.brows === "raised" ? -210 : f.brows === "angry" ? -202 : -205;
  const tilt = f.brows === "angry" ? 5 : f.brows === "worried" ? -5 : 0;
  const brows = `<path d="M-36,${browY + tilt} L-14,${browY - tilt}" stroke="${f.browColor || INK}" stroke-width="5" stroke-linecap="round"/><path d="M14,${browY - tilt} L36,${browY + tilt}" stroke="${f.browColor || INK}" stroke-width="5" stroke-linecap="round"/>`;
  const nose = `<path d="M-3,-176 Q2,-170 -4,-166" fill="none" stroke="${shade(skin, -60)}" stroke-width="2.6" stroke-linecap="round"/>`;
  const mouths = {
    smile: `<path d="M-15,-152 Q0,-140 15,-152" fill="none" stroke="${INK}" stroke-width="3.4" stroke-linecap="round"/>`,
    grin: `<path d="M-17,-154 Q0,-134 17,-154 Z" fill="#7a2e26" stroke="${INK}" stroke-width="3" stroke-linejoin="round"/><path d="M-12,-153 L12,-153" stroke="#fff" stroke-width="3"/>`,
    neutral: `<path d="M-11,-150 L11,-150" stroke="${INK}" stroke-width="3.4" stroke-linecap="round"/>`,
    sad: `<path d="M-13,-146 Q0,-156 13,-146" fill="none" stroke="${INK}" stroke-width="3.4" stroke-linecap="round"/>`,
    smirk: `<path d="M-10,-150 Q6,-146 16,-156" fill="none" stroke="${INK}" stroke-width="3.4" stroke-linecap="round"/>`,
    open: `<ellipse cx="0" cy="-150" rx="9" ry="8" fill="#7a2e26" stroke="${INK}" stroke-width="3"/>`,
  };
  let out = blush + eye(-25) + eye(25) + brows + nose + (mouths[f.mouth || "smile"]);
  if (f.glasses) {
    const g = f.glasses === "round"
      ? `<circle cx="-25" cy="-186" r="16"/><circle cx="25" cy="-186" r="16"/>`
      : `<rect x="-43" y="-199" width="34" height="25" rx="7"/><rect x="9" y="-199" width="34" height="25" rx="7"/>`;
    out += `<g fill="rgba(255,255,255,.18)" stroke="${f.glassesColor || "#222"}" stroke-width="3.6">${g}</g><path d="M-9,-188 Q0,-193 9,-188" fill="none" stroke="${f.glassesColor || "#222"}" stroke-width="3.6"/>`;
  }
  return out;
}

function facialHair(fh, color) {
  if (!fh || fh === "none") return "";
  const c = color, o = fh === "stubble" ? 0.38 : 1;
  const beard = `<path d="M-66,-182 C-66,-150 -40,-118 0,-116 C40,-118 66,-150 66,-182 C58,-162 44,-146 30,-142 C18,-158 -18,-158 -30,-142 C-44,-146 -58,-162 -66,-182 Z" fill="${c}" opacity="${o}" ${fh === "stubble" ? "" : `stroke="${INK}" stroke-width="3"`}/>`;
  const moustache = `<path d="M-24,-158 Q-12,-166 0,-160 Q12,-166 24,-158 Q12,-154 0,-156 Q-12,-154 -24,-158 Z" fill="${c}" opacity="${o}"/>`;
  if (fh === "moustache") return moustache;
  if (fh === "trimmed") {
    const tb = `<path d="M-64,-176 C-62,-146 -36,-124 0,-122 C36,-124 62,-146 64,-176 C56,-160 44,-150 30,-148 C18,-156 -18,-156 -30,-148 C-44,-150 -56,-160 -64,-176 Z" fill="${c}" opacity=".88"/>`;
    return tb + `<path d="M-20,-157 Q-10,-163 0,-158 Q10,-163 20,-157 Q10,-154 0,-155 Q-10,-154 -20,-157 Z" fill="${c}" opacity=".9"/>`;
  }
  return beard + moustache;
}

// ---------------------------------------------------------------- outfits
function outfit(o, skin) {
  const c = o.color || "#3a4a6b", dk = shade(c, -28), lt = shade(c, 22);
  const trunk = `M-40,-126 C-62,-110 -68,-62 -64,-22 Q-60,6 0,6 Q60,6 64,-22 C68,-62 62,-110 40,-126 Z`;
  const neck = `<rect x="-16" y="-132" width="32" height="14" rx="5" fill="${shade(skin, -18)}"/>`;
  const arms = (col) => `<path d="M-52,-112 C-74,-100 -80,-72 -74,-52" fill="none" stroke="${INK}" stroke-width="27" stroke-linecap="round"/><path d="M-52,-112 C-74,-100 -80,-72 -74,-52" fill="none" stroke="${col}" stroke-width="20" stroke-linecap="round"/>
    <path d="M52,-112 C74,-100 80,-72 74,-52" fill="none" stroke="${INK}" stroke-width="27" stroke-linecap="round"/><path d="M52,-112 C74,-100 80,-72 74,-52" fill="none" stroke="${col}" stroke-width="20" stroke-linecap="round"/>
    <circle cx="-74" cy="-48" r="11" fill="${skin}" stroke="${INK}" stroke-width="3"/><circle cx="74" cy="-48" r="11" fill="${skin}" stroke="${INK}" stroke-width="3"/>`;
  const body = (fill) => `<path d="${trunk}" fill="${fill}" stroke="${INK}" stroke-width="3.5" stroke-linejoin="round"/>`;
  const sheen = `<path d="${trunk}" fill="url(#bodyShade)"/>`;
  let detail = "";
  if (o.type === "hoodie") {
    detail = `<path d="M-40,-126 C-30,-104 30,-104 40,-126" fill="${dk}" stroke="${INK}" stroke-width="3"/>
      <path d="M-12,-108 L-14,-74 M12,-108 L14,-74" stroke="${o.accent || "#e8e2d4"}" stroke-width="3.4" stroke-linecap="round"/>
      <path d="M-34,-44 Q0,-36 34,-44 L30,-20 Q0,-14 -30,-20 Z" fill="${dk}" stroke="${INK}" stroke-width="2.6"/>`;
  } else if (o.type === "tshirt") {
    detail = `<path d="M-20,-126 Q0,-112 20,-126" fill="none" stroke="${dk}" stroke-width="4"/>`;
  } else if (o.type === "blazer") {
    const shirt = o.accent || "#f2f0ea";
    detail = `<path d="M-26,-126 L0,-70 L26,-126 Z" fill="${shirt}" stroke="${INK}" stroke-width="2.6"/>
      <path d="M-40,-126 L-8,-62 L-30,-6 M40,-126 L8,-62 L30,-6" fill="none" stroke="${INK}" stroke-width="3"/>
      ${o.tie ? `<path d="M-6,-120 L6,-120 L9,-84 L0,-72 L-9,-84 Z" fill="${o.tie}" stroke="${INK}" stroke-width="2.4"/>` : ""}
      <circle cx="-12" cy="-40" r="3.4" fill="${INK}"/><circle cx="-12" cy="-22" r="3.4" fill="${INK}"/>`;
  } else if (o.type === "turtleneck") {
    detail = `<rect x="-26" y="-138" width="52" height="20" rx="8" fill="${c}" stroke="${INK}" stroke-width="3"/>`;
  } else if (o.type === "vest") {
    detail = `<path d="M-46,-118 L-20,-122 L-6,-30 L-40,-10 Z M46,-118 L20,-122 L6,-30 L40,-10 Z" fill="${o.accent || "#2b2f38"}" stroke="${INK}" stroke-width="3"/>`;
  }
  return neck + arms(o.type === "vest" ? (o.sleeves || lt) : lt) + body(c) + sheen + detail;
}

// ---------------------------------------------------------------- character
function character(spec, opts = {}) {
  uid++;
  const skin = spec.skin || "#f1cfb0";
  const hairColor = (spec.hair && spec.hair.color) || "#3b2a20";
  const head = `<ellipse cx="0" cy="-190" rx="74" ry="68" fill="${skin}" stroke="${INK}" stroke-width="3.5"/>`;
  const ears = `<ellipse cx="-73" cy="-184" rx="10" ry="14" fill="${skin}" stroke="${INK}" stroke-width="3.2"/><ellipse cx="73" cy="-184" rx="10" ry="14" fill="${skin}" stroke="${INK}" stroke-width="3.2"/>`;
  const headShade = `<ellipse cx="0" cy="-190" rx="74" ry="68" fill="url(#headShade)"/>`;
  const sc = opts.scale || 1;
  return `<g transform="translate(${opts.x || 0},${opts.y || 0}) scale(${(opts.flip ? -1 : 1) * sc},${sc})">
    <ellipse cx="0" cy="8" rx="66" ry="12" fill="rgba(40,30,20,.28)"/>
    ${hairBack(spec.hair)}
    ${outfit(spec.outfit || { type: "tshirt" }, skin)}
    ${ears}${head}${headShade}
    ${facialHair(spec.facialHair, spec.facialHairColor || hairColor)}
    ${face(spec.face || {}, skin)}
    ${hairFront(spec.hair)}
    ${spec.hat ? hat(spec.hat) : ""}
  </g>`;
}
function hat(h) {
  if (h.type === "cap") return `<path d="M-70,-212 C-66,-262 66,-262 70,-212 Z" fill="${h.color}" stroke="${INK}" stroke-width="3.5"/><path d="M40,-214 Q96,-214 104,-200 L56,-202 Z" fill="${shade(h.color, -25)}" stroke="${INK}" stroke-width="3"/>`;
  return "";
}

const DEFS = `<defs>
  <radialGradient id="headShade" cx="38%" cy="32%" r="75%"><stop offset="0" stop-color="#fff" stop-opacity=".22"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#5a3a28" stop-opacity=".18"/></radialGradient>
  <linearGradient id="bodyShade" x1="0" x2="1"><stop offset="0" stop-color="#000" stop-opacity=".16"/><stop offset=".45" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-color="#000" stop-opacity=".2"/></linearGradient>
  <filter id="paper" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4" result="n"/><feColorMatrix type="saturate" values="0" in="n" result="g"/><feComponentTransfer in="g" result="t"><feFuncA type="table" tableValues="0 .07"/></feComponentTransfer><feComposite in="t" in2="SourceGraphic" operator="over"/></filter>
  <radialGradient id="vignette" cx="50%" cy="50%" r="75%"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#2a1c10" stop-opacity=".45"/></radialGradient>
  <filter id="soft"><feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#2a1c10" flood-opacity=".35"/></filter>
</defs>`;

// ---------------------------------------------------------------- map
const COUNTRIES = topo.feature(world, world.objects.countries);
const STATES = topo.feature(usStates, usStates.objects.states);

function mapLayer(m, W, H) {
  const proj = d3.geoMercator().center(m.center || [0, 30]).scale(m.scale || 400).translate([W / 2, H / 2]);
  const path = d3.geoPath(proj);
  const sea = m.sea || "#8fb2c0", land = m.land || "#e8dbbd", border = "#9b8a6e";
  let s = `<rect width="${W}" height="${H}" fill="${sea}"/>`;
  for (let y = 40; y < H; y += 46) s += `<path d="M0,${y} ${Array.from({ length: Math.ceil(W / 60) + 1 }, (_, i) => `Q${i * 60 + 15},${y - 4} ${i * 60 + 30},${y} T${i * 60 + 60},${y}`).join(" ")}" fill="none" stroke="#fff" stroke-opacity=".08" stroke-width="2"/>`;
  s += `<g filter="url(#soft)"><path d="${path(COUNTRIES)}" fill="${land}" stroke="${border}" stroke-width="1.6" stroke-linejoin="round"/></g>`;
  const hl = m.highlight || [];
  for (const h of hl) {
    const feats = (h.state ? STATES.features.filter(f => f.properties.name === h.state) : COUNTRIES.features.filter(f => f.properties.name === h.country));
    for (const f of feats) s += `<path d="${path(f)}" fill="${h.color || "#2f63c6"}" stroke="#1d3f86" stroke-width="2" opacity=".92"/>`;
  }
  if (m.states) s += `<path d="${path(topo.mesh(usStates, usStates.objects.states, (a, b) => a !== b))}" fill="none" stroke="${border}" stroke-width=".9" stroke-opacity=".7"/>`;
  for (const p of m.pins || []) {
    const [x, y] = proj(p.lonlat);
    s += `<g transform="translate(${x},${y})"><circle r="9" fill="#c4302b" stroke="#fff" stroke-width="3"/>${p.label ? `<text x="16" y="7" font-family="Inter Display, Inter, sans-serif" font-weight="800" font-size="26" fill="#2e211a" stroke="#f4ecd8" stroke-width="5" paint-order="stroke">${p.label}</text>` : ""}</g>`;
  }
  s += `<rect width="${W}" height="${H}" fill="#f3e6c4" opacity=".12"/><rect width="${W}" height="${H}" fill="url(#vignette)"/>`;
  return { svg: s, proj };
}

function caption(text, W, y, size = 64) {
  return `<text x="${W / 2}" y="${y}" text-anchor="middle" font-family="Inter Display, Inter, sans-serif" font-weight="900" font-size="${size}" fill="#fff" stroke="#1d1612" stroke-width="${size / 7}" paint-order="stroke" stroke-linejoin="round">${text}</text>`;
}

function scene(sc) {
  const W = sc.width || 1080, H = sc.height || 1920;
  const m = mapLayer(sc.map || {}, W, H);
  let chars = "";
  for (const c of sc.characters || []) {
    let x = c.x, y = c.y;
    if (c.lonlat) [x, y] = m.proj(c.lonlat);
    chars += character(c.spec, { x, y: y + (c.dy || 0), scale: c.scale || 1.6, flip: c.flip });
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${DEFS}
    <g filter="url(#paper)">${m.svg}</g>${chars}${sc.caption ? caption(sc.caption, W, sc.captionY || H * 0.74, sc.captionSize) : ""}${sc.extra || ""}</svg>`;
}

module.exports = { character, scene, DEFS, mapLayer, caption };
