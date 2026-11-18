// mod_skill planner: engine check. Concatenates constants.ts + engine.ts (or a saved Page source), runs script.json and
// script_errors.json in node and compares every row with py_reference.json. Run: node verify.mjs [page_source.tsx]
import fs from "fs"; import path from "path"; import { execFileSync } from "child_process";
const here = path.dirname(new URL(import.meta.url).pathname);
const pageSrc = process.argv[2] ? fs.readFileSync(process.argv[2], "utf8") : null;
const core = pageSrc ? pageSrc.slice(pageSrc.indexOf("const C: any"), pageSrc.indexOf("// ENGINE-END")) :
  fs.readFileSync(path.join(here, "constants.ts"), "utf8").replace(/^export /gm, "") + "\n" + fs.readFileSync(path.join(here, "engine.ts"), "utf8");
if (pageSrc) { // the Page must carry constants.ts verbatim: deep-compare C, KNOTS, WIN
  const grab = (src, name) => JSON.parse(src.match(new RegExp("const " + name + ": any = (.*);\\s*$", "m"))[1]);
  const ref = fs.readFileSync(path.join(here, "constants.ts"), "utf8");
  for (const nm of ["C", "KNOTS", "WIN"]) { const ok = JSON.stringify(grab(pageSrc, nm)) === JSON.stringify(grab(ref, nm)); console.log(`constants ${nm}: ${ok ? "identical" : "DIFFERENT"}`); if (!ok) process.exitCode = 1; }
}
const plans = { main: JSON.parse(fs.readFileSync(path.join(here, "script.json"))), errors: JSON.parse(fs.readFileSync(path.join(here, "script_errors.json"))) };
fs.writeFileSync(path.join(here, "_check.ts"), core + `\nconst P: any = ${JSON.stringify(plans)};\nconsole.log(JSON.stringify({ main: simulate(P.main), errors: simulate(P.errors) }));\n`);
const js = JSON.parse(execFileSync("node", [path.join(here, "_check.ts")], { encoding: "utf8", maxBuffer: 1 << 26 }));
fs.unlinkSync(path.join(here, "_check.ts"));
const py = JSON.parse(fs.readFileSync(path.join(here, "py_reference.json"), "utf8"));
let n = 0, exact = 0, worstWin = 0, worstNum = 0; const bad = [];
const num = (tag, a, b, tol) => { n++; const d = Math.abs(a - b); if (d < 1e-6) exact++; if (d > tol) bad.push(`${tag}: js ${a} py ${b}`); return d; };
for (const k of ["main", "errors"]) {
  py[k].forEach((p, i) => {
    const j = js[k][i]; const t = `${k} ${p.id}`;
    worstNum = Math.max(worstNum, num(t + " skill", j.skill, p.skill, 1e-5), num(t + " points", j.points, p.points, 1e-3), num(t + " r", j.r, p.r, 1e-5),
      num(t + " cash", j.cash, p.cash, 0.01), num(t + " debt", j.debt, p.debt, 0.01), num(t + " lostG", j.lostG, p.lostG, 1e-3), num(t + " lostW", j.lostW, p.lostW, 1e-3));
    if ((p.ps === null) !== (j.ps === null)) bad.push(`${t} validity: js ${j.ps} py ${p.ps}`); else if (p.ps !== null) worstNum = Math.max(worstNum, num(t + " ps", j.ps, p.ps, 1e-5));
    if (p.win && j.win) { worstWin = Math.max(worstWin, num(t + " win d", j.win.d, p.win.d, 0.1 + 1e-9)); if (p.win.h !== null) worstWin = Math.max(worstWin, num(t + " win h", j.win.h, p.win.h, 0.1 + 1e-9)); }
    for (const m of Object.keys(p.mods)) { worstNum = Math.max(worstNum, num(`${t} mod ${m} pts`, j.mods[m][1], p.mods[m][1], 1e-3)); if (j.mods[m][0] !== p.mods[m][0]) bad.push(`${t} mod ${m} tier`); }
    if (JSON.stringify(j.errors) !== JSON.stringify(p.errors.map((e) => e.replace(/\$([\d,]+)/g, "$$$1")))) bad.push(`${t} errors: js ${JSON.stringify(j.errors)} py ${JSON.stringify(p.errors)}`);
  });
}
const out = `checked ${pageSrc ? process.argv[2] : "constants.ts + engine.ts"}: ${n} numbers over ${py.main.length + py.errors.length} rows (scripted playthrough + error plan), ${exact} exact, worst win diff ${worstWin.toFixed(3)} pp, worst other diff ${worstNum.toExponential(2)}, ${bad.length} mismatches`;
console.log(out); bad.slice(0, 20).forEach((b) => console.log("  " + b));
fs.writeFileSync(path.join(here, "verify_log.txt"), out + "\n" + bad.join("\n") + "\n");
process.exit(bad.length ? 1 : 0);
