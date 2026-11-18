// Render one scene spec (JSON) to PNG. usage: node still.js scene.json out.png
const fs = require("fs");
const { chromium } = require("playwright");
const { scene } = require("./chibi");

(async () => {
  const [inp, out] = process.argv.slice(2);
  const sc = JSON.parse(fs.readFileSync(inp, "utf8"));
  const svg = scene(sc);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: sc.width || 1080, height: sc.height || 1920 } });
  await p.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  await p.screenshot({ path: out });
  await b.close();
  console.log(out);
})();
