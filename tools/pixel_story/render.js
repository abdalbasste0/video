// Render a timed story JSON to a silent 480x270 PNG stream piped into ffmpeg.
// usage: node render.js <timed_story.json> <out_raw.mp4> [fps]
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

(async () => {
  const [storyPath, out, fpsArg] = process.argv.slice(2);
  const fps = Number(fpsArg || 24);
  const story = JSON.parse(fs.readFileSync(storyPath, "utf8"));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 980, height: 560 } });
  await page.goto("file://" + path.join(__dirname, "engine.html"));
  const total = await page.evaluate(s => window.engine.load(s), story);
  const frames = Math.ceil(total * fps);
  const ff = spawn("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", out], { stdio: ["pipe", "inherit", "inherit"] });
  const BATCH = 24;
  for (let f = 0; f < frames; f += BATCH) {
    const urls = await page.evaluate(([a, b, fps]) => {
      const r = []; for (let i = a; i < b; i++) r.push(window.engine.frame(i / fps)); return r;
    }, [f, Math.min(frames, f + BATCH), fps]);
    for (const u of urls) {
      const ok = ff.stdin.write(Buffer.from(u.slice(22), "base64"));
      if (!ok) await new Promise(r => ff.stdin.once("drain", r));
    }
    if (f % (fps * 30) === 0) process.stderr.write(`  frame ${f}/${frames}\n`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  await browser.close();
  console.log(JSON.stringify({ frames, seconds: total }));
})();
