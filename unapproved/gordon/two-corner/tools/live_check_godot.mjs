// Live browser check of the served Godot web export (Godot only since 2026-11-11): menu -> START (Enter), B.5b camera stops + Plan the Line with
// arrows (Down, Enter entry, Enter apex, Backspace back, Enter apex, Enter exit = lock), SPACE timing, result. Writes out/shots5/live/*.png
// Paths are relative to the two-corner root. Playwright: a normal `playwright-core` install, else ../threejs/node_modules (box prototype only;
// the unapproved/gordon copy has neither threejs/ nor the web export, so there this script is noted only).
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath, pathToFileURL } from 'url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let chromium;
try { chromium = createRequire(import.meta.url)('playwright-core').chromium; }
catch { chromium = (await import(pathToFileURL(path.join(ROOT, 'threejs/node_modules/playwright-core/index.mjs')).href)).chromium; }
const dir = path.join(ROOT, 'out/shots5/live'); fs.mkdirSync(dir, { recursive: true });
const url = process.env.URL || 'http://127.0.0.1:5176/';
const b = await chromium.launch({ executablePath: '/opt/google/chrome/chrome', headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: 1280, height: 960 } });
const logs = []; p.on('console', m => logs.push(m.type() + ': ' + m.text())); p.on('pageerror', e => logs.push('pageerror ' + e));
await p.goto(url); await p.waitForTimeout(Number(process.env.BOOT || 9000));
const k = async (key, ms = 250) => { await p.keyboard.press(key); await p.waitForTimeout(ms); };
await p.screenshot({ path: `${dir}/menu.png` });
await k('Enter', 1500); await p.screenshot({ path: `${dir}/select_entry.png` });
await k('ArrowDown'); await p.screenshot({ path: `${dir}/select_entry_down.png` });
await k('Enter', 1100); await p.screenshot({ path: `${dir}/select_apex.png` });
await k('Enter'); await k('Backspace'); await p.screenshot({ path: `${dir}/select_back_to_apex.png` });
await k('Enter', 1100); await p.screenshot({ path: `${dir}/select_exit.png` });
await k('Enter', 900); await p.screenshot({ path: `${dir}/line_locked.png` }); await p.waitForTimeout(1200); await p.screenshot({ path: `${dir}/corner_a.png` });
await k(' ', 800); await p.screenshot({ path: `${dir}/corner_b.png` }); await p.waitForTimeout(4000);
await p.screenshot({ path: `${dir}/result.png` });
console.log(logs.filter(l => !l.startsWith('debug') && !l.includes('GPU stall')).slice(0, 12).join('\n'));
await b.close();
