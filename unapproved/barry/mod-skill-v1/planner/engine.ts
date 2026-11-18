// ENGINE-START (mod_skill planner engine; mirrors py_reference.py; verified by verify.mjs)
type Pack = { d: number; h: number | null };
type Buy = { at: string; phase: "pre" | "post"; key: string };
type Plan = {
  base: Record<string, number[] | null>; splits: Record<string, Record<string, number[]>>;
  grinds: Record<string, number>; buys: Buy[]; pickG: Record<string, string>; pickW: Record<string, string>;
};
type Mods = Record<string, [number, number]>;
type Move = { label: string; purse: number; toDebt: number; net: number; cash: number; debt: number };
type Row = {
  id: string; rnd: number; j: number; d: string; T: number; B: number; boss: boolean; grinds: number; skill: number;
  skillAfter: number; N: number; points: number; power: number; r: number; stats: number[] | null; ps: number | null;
  win: Pack | null; show: number | null; cashArrive: number; debtArrive: number; cash: number; debt: number;
  xpG: number; xpW: number; lostG: number; lostW: number; modsRace: Mods; mods: Mods; errors: string[];
  moves: Move[]; bought: string[]; tierPrice: number;
};
const SI: Record<string, number> = { P: 0, H: 1, E: 2 };
const clampN = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));
const r1 = (x: number) => Math.round(x * 10 + 1e-9) / 10;
function curve(kn: number[], v: number[], r: number): number {
  const n = kn.length;
  if (r <= kn[0]) return v[0] / 100;
  if (r >= kn[n - 1]) return v[n - 1] / 100;
  let i = 1; while (kn[i] < r && Math.abs(kn[i] - r) >= 1e-9) i++;
  if (Math.abs(kn[i] - r) < 1e-9) return v[i] / 100;
  return (v[i - 1] + (v[i] - v[i - 1]) * (r - kn[i - 1]) / (kn[i] - kn[i - 1])) / 100;
}
function span(xs: number[], x: number): [number, number, number] {
  const n = xs.length;
  if (x <= xs[0]) return [0, 0, 0];
  if (x >= xs[n - 1]) return [n - 1, n - 1, 0];
  let i = 1; while (xs[i] < x && Math.abs(xs[i] - x) >= 1e-12) i++;
  if (Math.abs(xs[i] - x) < 1e-12) return [i, i, 0];
  return [i - 1, i, (x - xs[i - 1]) / (xs[i] - xs[i - 1])];
}
function delta(g: number[], r: number, p: number): number {
  const np = C.OFF_PS.length; const [i0, i1, fr] = span(C.OFF_RS, r); const [j0, j1, fp] = span(C.OFF_PS, p);
  const v = (i: number, j: number) => g[i * np + j] / 100;
  const lo = v(i0, j0) * (1 - fp) + v(i0, j1) * fp, hi = v(i1, j0) * (1 - fp) + v(i1, j1) * fp;
  return lo * (1 - fr) + hi * fr;
}
function profPack(pr: string, r: number, T: number, d: string, ps: number): { d: number; h: number | null } {
  const c = WIN[pr][String(T)][d]; const kn = KNOTS[String(T)];
  const off = Math.abs(ps - C.TUNE[d][0]) >= 1e-12;
  let dm = curve(kn, c.m, r); if (off) dm = clampN(dm + delta(c.dm, r, ps), 0, 100);
  let h: number | null = null;
  if (c.h) { h = curve(kn, c.h, r); if (off) h = clampN(h + delta(c.dh, r, ps), 0, 100); }
  return { d: dm, h };
}
// standard reading curve (placeholder): read and QTE timing are the same skill s, 0.6 at a district's first race to
// 0.8 at its boss; win % blends the 60/60, 60/80, 80/60, 80/80 tables bilinearly (a = (s - 0.6) / 0.2 on both axes)
function skillWeights(s: number): [string, number][] {
  const a = clampN((s - 0.6) / 0.2, 0, 1);
  return [["c6060", (1 - a) * (1 - a)], ["c6080", (1 - a) * a], ["c8060", a * (1 - a)], ["c8080", a * a]];
}
function winPack(s: number, r: number, T: number, d: string, ps: number): Pack {
  let dm = 0, h = 0, hasH = false;
  for (const [pr, k] of skillWeights(s)) { const p = profPack(pr, r, T, d, ps); dm += k * p.d; if (p.h !== null) { h += k * p.h; hasH = true; } }
  return { d: r1(dm), h: hasH ? r1(h) : null };
}
const hardWin = (p: Pack) => (p.h === null ? p.d : p.h);
const raceIds: string[] = [];
for (let n = 0; n < 3; n++) for (const g of C.RUNGS) raceIds.push("R" + (n + 1) + " " + g);
const purseOf = (rnd: number, kind: string, grind: boolean) => C.PAY[kind] * C.PAY_MULT[rnd] * (grind ? C.GRIND_PAY_FRAC : 1);
const tierPrice = (rnd: number) => C.PRICE[rnd] * (rnd === 1 || rnd === 2 ? 1 - C.WHOLESALE : 1);
const copyMods = (m: Mods): Mods => { const o: Mods = {}; for (const k of Object.keys(m)) o[k] = [m[k][0], m[k][1]]; return o; };
const usd0 = (x: number) => "$" + Math.round(x).toLocaleString("en-US");

function simulate(plan: Plan): Row[] {
  let cash = 0, debt = C.DEBT; const mods: Mods = {}; const rows: Row[] = [];
  const take = (pay: number) => { let toDebt = 0; if (debt > 0) { toDebt = Math.min(debt, C.DEBT_SHARE * pay); debt -= toDebt; } cash += pay - toDebt; return toDebt; };
  for (let rnd = 0; rnd < 3; rnd++) {
    const d: string = C.ROUNDS[rnd]; const kit: string[] = C.KITS[d];
    const pts = () => C.STOCK_TOTAL + kit.reduce((s, k) => s + (mods[k] ? mods[k][1] : 0), 0);
    const short = rnd ? Math.max(0, 10 * C.CAP_POWER[rnd - 1] - pts()) : 0;
    const g = C.RUNGS.map((x: string) => Math.max(0, Math.floor(plan.grinds["R" + (rnd + 1) + " " + x] || 0)));
    const N = 6 + g.reduce((a: number, b: number) => a + b, 0); let ran = 0;
    for (let j = 0; j < 7; j++) {
      const id = "R" + (rnd + 1) + " " + C.RUNGS[j]; const err: string[] = []; const T = C.TURNS[j];
      const moves: Move[] = []; const bought: string[] = [];
      const cashArrive = cash, debtArrive = debt;
      moves.push({ label: "On arrival", purse: 0, toDebt: 0, net: 0, cash, debt });
      const buy = (phase: "pre" | "post") => {
        for (const b of plan.buys) {
          if (b.at !== id || b.phase !== phase) continue;
          const k = b.key;
          if (kit.indexOf(k) < 0) { err.push("buy " + k + ": not a slot in this district"); continue; }
          if (mods[k] && mods[k][0] >= rnd + 1) { err.push("buy " + k + ": already at the R" + (rnd + 1) + " tier"); continue; }
          const price = tierPrice(rnd);
          if (price > cash + 1e-9) { err.push("buy " + k + ": needs " + usd0(price) + ", have " + usd0(cash)); continue; }
          cash -= price;
          const lab = (mods[k] ? "Upgrade " + k + " to R" + (rnd + 1) : "Buy " + k + " (R" + (rnd + 1) + " tier)") + (phase === "pre" ? " · before grinds" : " · after the win");
          if (mods[k]) mods[k][0] = rnd + 1; else mods[k] = [rnd + 1, 0];
          bought.push(lab); moves.push({ label: lab, purse: 0, toDebt: 0, net: -price, cash, debt });
        }
      };
      // overflow spills: the picked mod first, then the rest of this district's kit in slot order; what is left is lost
      const assign = (pick: string | undefined, xp: number, what: string): number => {
        if (xp <= 0) return 0;
        if (!pick) { err.push(what + " XP not assigned (" + xp.toFixed(1) + " lost)"); return xp; }
        if (kit.indexOf(pick) < 0 || !mods[pick]) { err.push(what + " XP to " + pick + ": not an owned mod in this kit (" + xp.toFixed(1) + " lost)"); return xp; }
        let left = xp;
        for (const k of [pick, ...kit.filter((x) => x !== pick)]) {
          if (mods[k] && left > 0) {
            const room = C.CEIL[mods[k][0] - 1] - mods[k][1];
            if (room > 0) { const add = Math.min(room, left); mods[k][1] += add; left -= add; }
          }
        }
        return left;
      };
      buy("pre");
      let lostG = 0; const gp = purseOf(rnd, "kid", true);
      for (let i = 0; i < g[j]; i++) {
        const td = take(gp);
        lostG += assign(plan.pickG[id], C.GRIND_XP[rnd], "Grind");
        const last = moves[moves.length - 1];
        if (last.label.indexOf("Grind") === 0 && Math.abs(last.toDebt / last.purse - td / gp) < 1e-9 && Math.abs(last.purse / Number(last.label.split("×")[1] || 1) - gp) < 1e-9) {
          const n = Number(last.label.split("×")[1]) + 1;
          moves[moves.length - 1] = { label: "Grinds × " + n, purse: gp * n, toDebt: last.toDebt + td, net: last.net + gp - td, cash, debt };
        } else moves.push({ label: "Grinds × 1", purse: gp, toDebt: td, net: gp - td, cash, debt });
      }
      ran += g[j];
      const skill = C.SKILL[0] + (C.SKILL[1] - C.SKILL[0]) * ran / N;
      const p = pts(); const power = Math.min(C.CAP_POWER[rnd], p / 10); const B = C.C_ROUND[rnd] / C.TARGET_R[d][j]; const r = power / B;
      const modsRace = copyMods(mods);
      const base = plan.base[d]; let stats: number[] | null = null; let ok = true;
      if (!base || base.length !== 3 || base.some((x) => !isFinite(x)) || Math.abs(base[0] + base[1] + base[2] - C.STOCK_TOTAL) > 1e-9 || base.some((x) => x < C.BASE_MIN || x > C.BASE_MAX)) {
        err.push("base setup invalid"); ok = false;
      } else {
        stats = [base[0], base[1], base[2]];
        for (const k of kit) {
          if (mods[k] && mods[k][1] > 0) {
            const sp = (plan.splits[d] || {})[k];
            if (!sp || sp.length !== 3 || sp.some((x) => !isFinite(x)) || Math.abs(sp[0] + sp[1] + sp[2] - 100) > 1e-9 || Math.min(sp[0], sp[1], sp[2]) < 0 || sp[SI[k[0]]] < 100 * C.OWN_MIN - 1e-9) {
              err.push("split " + k + " invalid"); ok = false; continue;
            }
            for (let i = 0; i < 3; i++) stats[i] += mods[k][1] * sp[i] / 100;
          }
        }
        if (ok) {
          const tot = stats[0] + stats[1] + stats[2];
          if (stats.some((x) => x / tot < C.BAND[0] - 1e-9 || x / tot > C.BAND[1] + 1e-9)) { err.push("build outside the 25-50% band"); ok = false; }
        }
      }
      const ps = ok && stats ? stats[0] / (stats[0] + stats[1] + stats[2]) : null;
      const win = ok && ps !== null ? winPack(skill, r, T, d, ps) : null;
      const sPay = purseOf(rnd, C.KIND[j], false); const sTd = take(sPay);
      moves.push({ label: "Story purse (on a win)", purse: sPay, toDebt: sTd, net: sPay - sTd, cash, debt });
      buy("post");
      const xpW = C.STORY_XP[rnd][j] + C.CATCHUP.k * C.CATCHUP.share[j] * short;
      const lostW = assign(plan.pickW[id], xpW, "Win");
      ran += 1;
      rows.push({
        id, rnd, j, d, T, B, boss: j === 6, grinds: g[j], skill, skillAfter: C.SKILL[0] + (C.SKILL[1] - C.SKILL[0]) * Math.min(ran, N) / N, N,
        points: p, power, r, stats: ok ? stats : null, ps, win, show: win ? hardWin(win) : null, cashArrive, debtArrive, cash, debt,
        xpG: g[j] * C.GRIND_XP[rnd], xpW, lostG, lostW, modsRace, mods: copyMods(mods), errors: err, moves, bought, tierPrice: tierPrice(rnd),
      });
    }
  }
  return rows;
}
// ENGINE-END
