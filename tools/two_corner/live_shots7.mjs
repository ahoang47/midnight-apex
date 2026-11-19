// Legibility check (shots7): same live flow as live_check_godot.mjs at several browser window sizes.
// Usage: node tools/live_shots7.mjs <outdir> [WxH ...]   (default 1280x960 1920x1080 1366x768)
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath, pathToFileURL } from 'url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let chromium;
try { chromium = createRequire(import.meta.url)('playwright-core').chromium; }
catch { chromium = (await import(pathToFileURL(path.join(ROOT, 'threejs/node_modules/playwright-core/index.mjs')).href)).chromium; }
const out = path.resolve(process.argv[2] || 'out/shots7/live');
const sizes = process.argv.slice(3).length ? process.argv.slice(3) : ['1280x960', '1920x1080', '1366x768'];
const url = process.env.URL || 'http://127.0.0.1:5176/';
const b = await chromium.launch({ executablePath: '/opt/google/chrome/chrome', headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const s of sizes) {
  const [w, h] = s.split('x').map(Number); const dir = path.join(out, s); fs.mkdirSync(dir, { recursive: true });
  const p = await b.newPage({ viewport: { width: w, height: h } });
  await p.goto(url + '?v=' + Date.now()); await p.waitForTimeout(Number(process.env.BOOT || 9000));
  const k = async (key, ms = 250) => { await p.keyboard.press(key); await p.waitForTimeout(ms); };
  const shot = async n => p.screenshot({ path: `${dir}/${n}.png` });
  await shot('menu');
  await k('Enter', 1500); await shot('1_plan_entry');
  await k('Enter', 1300); await shot('2_plan_apex');
  await k('Enter', 1300); await shot('3_plan_exit');
  await k('Enter', 500); await shot('4_line_locked'); await p.waitForTimeout(Number(process.env.PLAY_WAIT || 1300)); await shot('5_playback');
  await k(' ', 800); await shot('6_playback_b'); await p.waitForTimeout(4000); await shot('7_result');
  await p.close();
}
await b.close();
