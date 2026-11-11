// Live browser check of the served Godot web export (Godot only since 2026-11-11): menu -> START (Enter), Plan the Line with
// arrows (Down, Enter entry, Enter apex, Backspace back, Enter apex, Enter exit = lock), SPACE timing, result. Writes out/shots4/live/*.png
// NOTE: this unapproved copy does not include the web export or threejs/ (Playwright used to load from threejs/node_modules).
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dir = path.join(ROOT, 'out/shots4/live'); fs.mkdirSync(dir, { recursive: true });
const require = createRequire(import.meta.url);
const { chromium } = require('playwright-core');
const url = process.env.URL || 'http://127.0.0.1:5176/';
const b = await chromium.launch({ executablePath: '/opt/google/chrome/chrome', headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: 1280, height: 960 } });
const logs = []; p.on('console', m => logs.push(m.type() + ': ' + m.text())); p.on('pageerror', e => logs.push('pageerror ' + e));
await p.goto(url); await p.waitForTimeout(Number(process.env.BOOT || 9000));
const k = async (key, ms = 250) => { await p.keyboard.press(key); await p.waitForTimeout(ms); };
await p.screenshot({ path: `${dir}/menu.png` });
await k('Enter', 1500); await p.screenshot({ path: `${dir}/select_entry.png` });
await k('ArrowDown'); await p.screenshot({ path: `${dir}/select_entry_down.png` });
await k('Enter'); await p.screenshot({ path: `${dir}/select_apex.png` });
await k('Enter'); await k('Backspace'); await p.screenshot({ path: `${dir}/select_back_to_apex.png` });
await k('Enter'); await p.screenshot({ path: `${dir}/select_exit.png` });
await k('Enter', 1500); await p.screenshot({ path: `${dir}/corner_a.png` });
await k(' ', 800); await p.screenshot({ path: `${dir}/corner_b.png` }); await p.waitForTimeout(4000);
await p.screenshot({ path: `${dir}/result.png` });
console.log(logs.filter(l => !l.startsWith('debug') && !l.includes('GPU stall')).slice(0, 12).join('\n'));
await b.close();
