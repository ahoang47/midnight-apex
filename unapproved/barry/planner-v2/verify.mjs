// planner-v2 engine check. Concatenates constants.ts + engine.ts (or a saved Page source), runs script.json and
// script_errors.json in node and compares every row with py_reference.json. Run: node verify.mjs [page_source.tsx]
import fs from "fs"; import path from "path"; import { execFileSync } from "child_process";
const here = path.dirname(new URL(import.meta.url).pathname);
const pageSrc = process.argv[2] ? fs.readFileSync(process.argv[2], "utf8") : null;
const core = pageSrc ? pageSrc.slice(pageSrc.indexOf("const C: any"), pageSrc.indexOf("// ENGINE-END")) :
  fs.readFileSync(path.join(here, "constants.ts"), "utf8").replace(/^export /gm, "") + "\n" + fs.readFileSync(path.join(here, "engine.ts"), "utf8");
if (pageSrc) { // the Page must carry constants.ts and engine.ts verbatim
  const ref = fs.readFileSync(path.join(here, "constants.ts"), "utf8").replace(/^export /gm, "").split("\n").slice(1).join("\n").trim();
  const eng = fs.readFileSync(path.join(here, "engine.ts"), "utf8").trim();
  console.log("constants block: " + (pageSrc.includes(ref) ? "identical" : "DIFFERENT")); console.log("engine block: " + (pageSrc.includes(eng) ? "identical" : "DIFFERENT"));
  if (!pageSrc.includes(ref) || !pageSrc.includes(eng)) process.exitCode = 1;
}
const plans = { main: JSON.parse(fs.readFileSync(path.join(here, "script.json"))), errors: JSON.parse(fs.readFileSync(path.join(here, "script_errors.json"))) };
fs.writeFileSync(path.join(here, "_check.ts"), core + `\nconst P: any = ${JSON.stringify(plans)};\nconsole.log(JSON.stringify({ main: simulate(P.main), errors: simulate(P.errors) }));\n`);
const js = JSON.parse(execFileSync("node", ["--experimental-strip-types", "--no-warnings", path.join(here, "_check.ts")], { encoding: "utf8", maxBuffer: 1 << 26 }));
fs.unlinkSync(path.join(here, "_check.ts"));
const py = JSON.parse(fs.readFileSync(path.join(here, "py_reference.json"), "utf8"));
let n = 0, exact = 0, worstWin = 0, worstNum = 0; const bad = [];
const num = (tag, a, b, tol) => { n++; const d = Math.abs(a - b); if (d < 1e-6) exact++; if (!(d <= tol)) bad.push(`${tag}: js ${a} py ${b}`); return d; };
for (const k of ["main", "errors"]) {
  py[k].forEach((p, i) => {
    const j = js[k][i]; const t = `${k} ${p.id}`;
    for (const [f, tol] of [["skill", 1e-5], ["points", 1e-3], ["ledger", 1e-3], ["cash", 0.01], ["debt", 0.01], ["lostX", 1e-3], ["lostW", 1e-3], ["nmw", 0]])
      worstNum = Math.max(worstNum, num(`${t} ${f}`, j[f], p[f], tol));
    if ((p.win === null) !== (j.win === null)) bad.push(`${t} win validity: js ${j.win} py ${p.win}`); else if (p.win !== null) worstWin = Math.max(worstWin, num(t + " win", j.win, p.win, 1e-9));
    p.slots.forEach((s, q) => {
      const o = j.slots[q];
      if ((s === null) !== (o === null)) { bad.push(`${t} slot ${q + 1} owned`); return; }
      if (s) { num(`${t} slot ${q + 1} group`, o[0], s[0], 0); num(`${t} slot ${q + 1} mk`, o[1], s[1], 0); worstNum = Math.max(worstNum, num(`${t} slot ${q + 1} pts`, o[2], s[2], 1e-3)); }
    });
    if (JSON.stringify(j.errors) !== JSON.stringify(p.errors)) bad.push(`${t} errors: js ${JSON.stringify(j.errors)} py ${JSON.stringify(p.errors)}`);
  });
}
const out = `checked ${pageSrc ? process.argv[2] : "constants.ts + engine.ts"}: ${n} numbers over ${py.main.length + py.errors.length} rows (scripted playthrough + error plan), ${exact} exact, worst win diff ${worstWin.toFixed(3)} pp, worst other diff ${worstNum.toExponential(2)}, ${bad.length} mismatches`;
console.log(out); bad.slice(0, 20).forEach((b) => console.log("  " + b));
fs.writeFileSync(path.join(here, "verify_log.txt"), out + "\n" + bad.join("\n") + "\n");
process.exit(bad.length ? 1 : 0);
