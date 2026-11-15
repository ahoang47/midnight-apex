// planner-v1: win-chance swings along the ladder under "grind until my profile is at target" (50 %) with auto mods, per profile.
// Run: node unapproved/barry/planner-v1/swings.mjs [target]   -> swings_<target>.json + table on stdout
import fs from "fs"; import path from "path"; import { execFileSync } from "child_process";
const here = path.dirname(new URL(import.meta.url).pathname); const target = Number(process.argv[2] || 50);
const core = fs.readFileSync(path.join(here, "constants.ts"), "utf8").replace(/^export /gm, "") + "\n" + fs.readFileSync(path.join(here, "engine.ts"), "utf8");
const src = core + `
const P = { "60/60": [60, 60], "60/80": [60, 80], "80/60": [80, 60], "80/80": [80, 80] }; const out = {};
for (const [k, [rd, tm]] of Object.entries(P)) out[k] = simulate({ read: rd, time: tm, policy: "mine", target: ${target}, autoBuy: true, buildMode: "auto", targets: {}, extra: {}, buys: [] })
  .map((r) => ({ id: r.id, show: r.show, natural: r.natural, g: r.grindsAuto, L: r.L }));
console.log(JSON.stringify(out));`;
fs.writeFileSync(path.join(here, "_sw.ts"), src);
const res = JSON.parse(execFileSync("node", [path.join(here, "_sw.ts")], { encoding: "utf8" })); fs.unlinkSync(path.join(here, "_sw.ts"));
fs.writeFileSync(path.join(here, `swings_${target}.json`), JSON.stringify(res, null, 1));
for (const [k, rows] of Object.entries(res)) {
  const d = rows.slice(1).map((r, i) => ({ from: rows[i].id, to: r.id, a: rows[i].show, b: r.show, dd: +(r.show - rows[i].show).toFixed(1) }));
  const sp = [...d].sort((x, y) => y.dd - x.dd).slice(0, 4), dp = [...d].sort((x, y) => x.dd - y.dd).slice(0, 4);
  const held = rows.filter((r) => r.g > 0 && r.natural < target).map((r) => `${r.id} ${r.natural}->${r.show} (${r.g}g)`);
  console.log(`== ${k}: min ${Math.min(...rows.map((r) => r.show))} max ${Math.max(...rows.map((r) => r.show))}, grinds ${rows.reduce((s, r) => s + r.g, 0)}`);
  console.log("  spikes:", sp.map((x) => `${x.from}->${x.to} ${x.a}->${x.b} (+${x.dd})`).join("; "));
  console.log("  dips:  ", dp.map((x) => `${x.from}->${x.to} ${x.a}->${x.b} (${x.dd})`).join("; "));
  console.log("  held up by grinding:", held.join("; "));
  console.log("  row:", rows.map((r) => `${r.id}:${r.show}${r.g ? "*" + r.g : ""}`).join(" "));
}
