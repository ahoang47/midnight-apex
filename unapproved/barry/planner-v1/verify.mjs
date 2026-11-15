// planner-v1: JS-port check. Concatenates constants.ts + engine.ts, runs the walks in node and compares with py_reference.json.
// Run: node unapproved/barry/planner-v1/verify.mjs   (after gen_constants.py and py_reference.py)
import fs from "fs"; import path from "path"; import { execFileSync } from "child_process";
const here = path.dirname(new URL(import.meta.url).pathname);
// optional argv[2]: a saved Page source (.tsx); its data + engine block is checked instead of constants.ts + engine.ts
const pageSrc = process.argv[2] ? fs.readFileSync(process.argv[2], "utf8") : null;
const core = pageSrc ? pageSrc.slice(pageSrc.indexOf("const C: any"), pageSrc.indexOf("// ENGINE-END")) :
  fs.readFileSync(path.join(here, "constants.ts"), "utf8").replace(/^export /gm, "") + "\n" + fs.readFileSync(path.join(here, "engine.ts"), "utf8");
console.log("checking", pageSrc ? process.argv[2] : "constants.ts + engine.ts");
const src = core + `
const base = { target: 50, autoBuy: true, buildMode: "auto", targets: {}, extra: {}, buys: [] };
const P = { c6060: [60, 60], c6080: [60, 80], c8060: [80, 60], c8080: [80, 80] };
const out = { campaign: {}, arc: {}, at_cap: bossAtCap() };
for (const pol of ["story", "mixed", "hard"]) {
  out.campaign[pol] = {};
  for (const [pr, [rd, tm]] of Object.entries(P)) out.campaign[pol][pr] = simulate({ ...base, read: rd, time: tm, policy: pol }).map((r) => ({ id: r.id, L: r.L, r: r.r, win: [r.win.d, r.win.h], g: r.grindsAuto, money: r.cashAfter, show: r.show }));
}
const MODE = { c8080: "story", c6080: "mixed", c8060: "mixed", c6060: "hard" };
for (const [pr, m] of Object.entries(MODE)) out.arc[pr] = out.campaign[m][pr].slice(21);
console.log(JSON.stringify(out));
`;
fs.writeFileSync(path.join(here, "_check.ts"), src);
const js = JSON.parse(execFileSync("node", [path.join(here, "_check.ts")], { encoding: "utf8", maxBuffer: 1 << 26 }));
fs.writeFileSync(path.join(here, "js_walks.json"), JSON.stringify(js));
const py = JSON.parse(fs.readFileSync(path.join(here, "py_reference.json"), "utf8"));
let worst = 0, n = 0, bad = [], off = [];
const cmp = (tag, a, b) => { n++; const d = Math.abs(a - b); worst = Math.max(worst, d); if (d > 1e-9) off.push(`${tag}: js ${a} py ${b}`); if (d > 0.1 + 1e-9) bad.push(`${tag}: js ${a} py ${b}`); };
// campaign rows: every policy walks with its gate; compare all 4 profiles' win on the policy walk (the walk itself is profile-independent
// in the Python sim, so compare the c8080 walk's L/money and each profile's packs from py)
for (const pol of ["story", "mixed", "hard"]) {
  const pyRows = py.campaign[pol], jsRows = js.campaign[pol]["c8080"];
  pyRows.forEach((p, i) => {
    const j = jsRows[i];
    if (p.L !== j.L) bad.push(`${pol} ${p.rung} L js ${j.L} py ${p.L}`);
    if (Math.abs(p.money - j.money) > 0.01) bad.push(`${pol} ${p.rung} money js ${j.money} py ${p.money}`);
    if (p.grind !== j.g) bad.push(`${pol} ${p.rung} grinds js ${j.g} py ${p.grind}`);
    for (const pr of Object.keys(p.wr)) { const jj = js.campaign[pol][pr][i]; cmp(`${pol} ${p.rung} ${pr} dist`, jj.win[0], p.wr[pr][0]); cmp(`${pol} ${p.rung} ${pr} hard`, jj.win[1] ?? jj.win[0], p.wr[pr][1]); }
  });
}
for (const pr of Object.keys(py.arc)) py.arc[pr].log.forEach((p, i) => {
  const j = js.arc[pr][i];
  if (p.L !== j.L) bad.push(`arc ${pr} ${p.id} L js ${j.L} py ${p.L}`);
  if (p.g !== j.g) bad.push(`arc ${pr} ${p.id} grinds js ${j.g} py ${p.g}`);
  cmp(`arc ${pr} ${p.id} dist`, j.win[0], p.wr[0]); cmp(`arc ${pr} ${p.id} hard`, j.win[1] ?? j.win[0], p.wr[1]);
});
py.at_cap.forEach((p, i) => { cmp(`at cap R${i + 1} 60/60`, js.at_cap[i][0], p[0]); cmp(`at cap R${i + 1} 80/80`, js.at_cap[i][1], p[1]); });
console.log("compared", n, "win cells; worst |js-py| =", worst.toFixed(3), "pp"); console.log(bad.length ? bad.join("\n") : "no mismatches"); console.log("cells not exact:", off.length, off.join("; "));
const s = js.campaign.story.c8080; const mins = [0, 1, 2].map((k) => Math.min(...s.slice(7 * k, 7 * k + 7).map((r) => r.show)));
console.log("story 80/80 mins", mins, "bosses", [6, 13, 20].map((i) => s[i].show));
console.log("at cap 60/60", js.at_cap.map((x) => x[0]), "80/80", js.at_cap.map((x) => x[1]));
console.log("finale 80/80", js.arc.c8080.filter((r) => r.id[0] === "F").map((r) => r.win[1] ?? r.win[0]));
