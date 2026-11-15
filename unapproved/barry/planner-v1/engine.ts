// ENGINE-START (pasted verbatim into the Page)
type Alloc = [number, number, number];
type Pack = { d: number; h: number | null };
type Owned = { id: string; aero: boolean };
type Weights = [string, number][];
type Policy = "story" | "mixed" | "hard" | "mine";
type BuildMode = "auto" | "custom";
type Buy = { at: string; id: string; aero: boolean };
type Plan = {
  read: number; time: number; policy: Policy; target: number; autoBuy: boolean; buildMode: BuildMode;
  targets: Record<string, Alloc>; extra: Record<string, number>; buys: Buy[];
};
type Row = {
  id: string; label: string; era: string; d: string; T: number; B: number; boss: boolean; billed: boolean;
  grindsAuto: number; grindsExtra: number; grindWin: number; L: number; bag: number; power: number; r: number; fill: number;
  alloc: Alloc; pow: number; win: Pack; show: number; cashBefore: number; cashAfter: number; debtAfter: number; xp: number;
  Lafter: number; equipped: string[]; bought: string[]; failed: string[]; capL: number; stage: number; wholesale: boolean;
  aeroOpen: boolean; done: string[]; owned: Owned[]; ownedAfter: Owned[]; cashAtBuy: number; natural: number;
};
const STATK: Record<string, string> = { P: "POW", H: "HAN", E: "EN" };
const MOD: Record<string, any> = {};
for (const m of C.CATALOG) MOD[m.id] = m;
const FINALE_C: number[] = C.FINALE.map((f: any) => f.B * f.r);
const CAPS: number[] = [C.CAP[2], ...C.FIN_CAP];
const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));
const r1 = (x: number) => Math.round(x * 10 + 1e-9) / 10;

function weightsFor(read: number, time: number): Weights {
  const a = clamp((read - 60) / 20, 0, 1), b = clamp((time - 60) / 20, 0, 1);
  const w: Weights = [["c6060", (1 - a) * (1 - b)], ["c6080", (1 - a) * b], ["c8060", a * (1 - b)], ["c8080", a * b]];
  return w.filter((x) => x[1] > 1e-12);
}
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
function presetPack(pr: string, r: number, T: number, d: string, ps: number | null): Pack {
  const c = WIN[pr][String(T)][d]; const kn = KNOTS[String(T)];
  const off = ps !== null && Math.abs(ps - C.TUNE[d][0]) >= 1e-12;
  let dm = curve(kn, c.m, r); if (off) dm = clamp(dm + delta(c.dm, r, ps as number), 0, 100);
  let h: number | null = null;
  if (c.h) { h = curve(kn, c.h, r); if (off) h = clamp(h + delta(c.dh, r, ps as number), 0, 100); }
  return { d: dm, h };
}
// win % pack (district mean, hardest track or null), rounded to 0.1 like progression.win_pack; blended for custom profiles
function winPack(w: Weights, r: number, T: number, d: string, ps: number | null): Pack {
  let dm = 0, h = 0, hasH = false;
  for (const [pr, k] of w) { const p = presetPack(pr, r, T, d, ps); dm += k * p.d; if (p.h !== null) { h += k * p.h; hasH = true; } }
  return { d: r1(dm), h: hasH ? r1(h) : null };
}
const hardWin = (p: Pack) => (p.h === null ? p.d : p.h);
const shown = (p: Pack) => Math.min(p.d, hardWin(p));

// equations.py
const spPoints = (L: number) => Math.round(C.SP_SCALE * C.SP_START * Math.pow(C.SP_G, L / 12));
const statsAt = (L: number) => spPoints(L) / C.SP_SCALE / C.SP_CAP;
const xpToNext = (L: number) => C.XP_BASE * Math.pow(C.XP_G, Math.max(0, L));
const xpSum = (a: number, b: number) => { let s = 0; for (let L = a; L < b; L++) s += xpToNext(L); return s; };
function grindXp(L: number, cap: number): number {
  const dd = Math.max(0, cap - L);
  return C.GRIND_FRAC * xpToNext(L) * (C.FLOOR + (1 - C.FLOOR) * (1 - Math.exp(-dd / C.TAU)));
}
const wsum: number = C.STORY_W.reduce((a: number, b: number) => a + b, 0);
function liveStoryXp(rnd: number, j: number, enter: number, cap: number): number {
  const mult = C.STORY_XP_MULT[rnd][j];                       // live: R2 boss x1.5 is in STORY_XP_MULT
  return mult * C.STORY_FILL[rnd] * C.STORY_W[j] / wsum * xpSum(enter, cap);
}
// leftover XP carries over (live, equations.story_xp): nominal XP as if entered at the previous cap + CATCHUP.k x shortfall split by CATCHUP.share
function storyXp(rnd: number, j: number, enter: number, cap: number): number {
  const nominal = rnd === 0 ? 0 : C.CAP[rnd - 1];
  const base = liveStoryXp(rnd, j, enter < nominal ? nominal : enter, cap);
  return base + C.CATCHUP.k * C.CATCHUP.share[j] * xpSum(enter, nominal);
}
function applyXp(L: number, xp: number, bag: number, cap: number): [number, number] {
  bag += xp;
  while (L < cap) { const need = xpToNext(L); if (bag + 1e-9 < need) break; bag -= need; L += 1; }
  if (L >= cap) { L = cap; bag = 0; }
  return [L, bag];
}
const budget = (rnd: number, j: number) => C.C_ROUND[rnd] / C.TARGET_R[C.ROUNDS[rnd]][j];
const purse = (rnd: number, kind: string, grind: boolean) => C.PAY[kind] * C.PAY_MULT[rnd] * (grind ? C.GRIND_PAY_FRAC : 1);
function modPrice(id: string, aero: boolean, wholesale: boolean): number {
  const m = MOD[id]; let p = m.price * (aero ? C.AERO_MULT : 1);
  if (wholesale && C.WHOLESALE_TIERS.includes(m.g)) p *= 1 - C.WHOLESALE;
  return p;
}
// skill points (skill-points-v1)
function band(T: number): [number, number] { return [Math.ceil(C.BAND[0] * T - 1e-9), Math.floor(C.BAND[1] * T + 1e-9)]; }
function startBuild(): Alloc { const T = spPoints(0); const a = Math.trunc(T * C.TUNE.street[0]), b = Math.trunc(T * C.TUNE.street[1]); return [a, b, T - a - b]; }
function pyRound(x: number): number { const f = Math.floor(x), d = x - f; return d > 0.5 ? f + 1 : d < 0.5 ? f : (f % 2 === 0 ? f : f + 1); }
function addPoints(alloc: Alloc, n: number, tune: number[]): Alloc {
  const a: Alloc = [alloc[0], alloc[1], alloc[2]]; const T = a[0] + a[1] + a[2] + n; const tgt = tune.map((s) => s * T); const [lo, hi] = band(T);
  for (let i = 0; i < 3; i++) { const g = Math.min(Math.max(0, lo - a[i]), n); a[i] += g; n -= g; }
  while (n > 0) {
    const cand = [0, 1, 2].filter((k) => a[k] < hi);
    let i = cand[0]; for (const k of cand) if (tgt[k] - a[k] > tgt[i] - a[i]) i = k;
    if (tgt[i] - a[i] < 1) {
      for (let k = 0; k < 3; k++) { const g = Math.min(n, k < 2 ? pyRound(tune[k] * n) : n, hi - a[k]); a[k] += g; n -= g; }
      if (n > 0) { let k = 0; for (let q = 1; q < 3; q++) if (a[q] / T < a[k] / T) k = q; a[k] += n; n = 0; }
      break;
    }
    const step = Math.max(1, Math.min(n, Math.trunc(tgt[i] - a[i]), hi - a[i])); a[i] += step; n -= step;
  }
  return a;
}
function retune(alloc: Alloc, tune: number[]): Alloc {
  const a: Alloc = [alloc[0], alloc[1], alloc[2]]; const T = a[0] + a[1] + a[2];
  let bud = Math.floor(C.RETUNE * T + 1e-9); const [lo, hi] = band(T); const tgt = tune.map((s) => s * T);
  while (bud > 0) {
    const sur = [0, 1, 2].filter((k) => a[k] - tgt[k] >= 1 && a[k] > lo), dfc = [0, 1, 2].filter((k) => tgt[k] - a[k] >= 1 && a[k] < hi);
    if (!sur.length || !dfc.length) break;
    let i = sur[0]; for (const k of sur) if (a[k] - tgt[k] > a[i] - tgt[i]) i = k;
    let j = dfc[0]; for (const k of dfc) if (tgt[k] - a[k] > tgt[j] - a[j]) j = k;
    const m = Math.min(bud, Math.trunc(a[i] - tgt[i]), Math.trunc(tgt[j] - a[j]), a[i] - lo, hi - a[j]);
    if (m <= 0) break;
    a[i] -= m; a[j] += m; bud -= m;
  }
  return a;
}
// garage (mods-v1)
const stageCeil = (stage: number) => (stage < 3 ? C.C_ROUND[stage] : FINALE_C[stage - 3]);
const modGap = (L: number, stage: number) => Math.max(0, Math.min(10 * stageCeil(stage), 10 * C.MOD_CAP * statsAt(L)) - spPoints(L));
function equipped(owned: Owned[], d: string): (Owned | null)[] {
  const pat: string = C.PATTERN[d]; const eq: (Owned | null)[] = []; let aero = 0;
  for (const k of "PHE") {
    const n = pat.split("").filter((c) => c === k).length;
    const mine = owned.filter((m) => MOD[m.id].st === STATK[k]).slice().sort((x, y) => MOD[y.id].pts - MOD[x.id].pts);
    const pick: Owned[] = [];
    for (const m of mine) { if (pick.length >= n) break; if (m.aero) { if (aero >= C.AERO_MAX) continue; aero++; } pick.push(m); }
    for (let q = 0; q < n; q++) eq.push(pick[q] || null);
  }
  return eq;
}
const slotPts = (owned: Owned[], d: string) => equipped(owned, d).reduce((s, m) => s + (m ? MOD[m.id].pts : C.STOCK), 0);
const power = (owned: Owned[], L: number, stage: number, d: string) => Math.min(10 * stageCeil(stage), 10 * C.MOD_CAP * statsAt(L), spPoints(L) + slotPts(owned, d)) / 10;
const unlocked = (id: string, done: Set<string>) => done.has(MOD[id].u);
type Wallet = { money: number; owned: Owned[]; spent: number };
function autoShop(w: Wallet, L: number, stage: number, d: string, done: Set<string>, wholesale: boolean, log: string[]): void {
  for (;;) {
    const deficit = modGap(L, stage) - slotPts(w.owned, d);
    if (deficit <= 1e-9) return;
    const eq = equipped(w.owned, d); const pat: string = C.PATTERN[d]; const weakest: Record<string, number> = {}; let i = 0;
    for (const k of "PHE") {
      const n = pat.split("").filter((c) => c === k).length; const vals = eq.slice(i, i + n).map((m) => (m ? MOD[m.id].pts : C.STOCK)); i += n;
      if (vals.length) weakest[STATK[k]] = Math.min(...vals);
    }
    let best: { g: number; p: number; id: string } | null = null;
    for (const m of C.CATALOG) {
      if (!(m.st in weakest) || !unlocked(m.id, done)) continue;
      const price = modPrice(m.id, false, wholesale); if (price > w.money + 1e-9) continue;
      const gain = Math.min(deficit, m.pts - weakest[m.st]); if (gain <= 0) continue;
      const g = Math.round(gain * 1e6) / 1e6;
      if (!best || g > best.g || (g === best.g && -price > -best.p)) best = { g, p: price, id: m.id };
    }
    if (!best) return;
    w.owned.push({ id: best.id, aero: false }); w.money -= best.p; w.spent += best.p; log.push(best.id);
  }
}
const modLabel = (o: Owned) => o.id + (o.aero ? " (aero)" : "");
// full campaign + arc + finale walk
function simulate(plan: Plan): Row[] {
  const W = weightsFor(plan.read, plan.time);
  const tuneOf = (d: string): number[] => (plan.buildMode === "custom" && plan.targets[d] ? plan.targets[d].map((x) => x / 100) : C.TUNE[d]);
  const gate: Record<Policy, Weights[]> = { story: [], mixed: [[["c6080", 1]], [["c8060", 1]]], hard: [[["c6060", 1]]], mine: [W] };
  const thr: number = plan.policy === "mine" ? plan.target : C.CLEAR;   // "mine": grind to the chosen target; sim walks: 50 %
  let L = 0, bag = 0, debt: number = C.DEBT; const wal: Wallet = { money: 0, owned: [], spent: 0 }; const done = new Set<string>(); const rows: Row[] = [];
  let alloc = startBuild();
  const credit = (pay: number) => { if (debt > 0) { const take = Math.min(debt, C.DEBT_SHARE * pay); debt -= take; wal.money += pay - take; } else wal.money += pay; };
  const manual = (id: string, stage: number, wholesale: boolean, aeroOpen: boolean, bought: string[], failed: string[]) => {
    for (const b of plan.buys) {
      if (b.at !== id) continue;
      const price = modPrice(b.id, b.aero, wholesale); const label = modLabel(b);
      if (!unlocked(b.id, done)) { failed.push(label + ": locked"); continue; }
      if (b.aero && !aeroOpen) { failed.push(label + ": aero locked until R1 boss"); continue; }
      if (b.aero && wal.owned.some((o) => o.aero)) { failed.push(label + ": one aero max"); continue; }
      if (price > wal.money + 1e-9) { failed.push(label + ": short $" + Math.ceil(price - wal.money)); continue; }
      wal.owned.push({ id: b.id, aero: b.aero }); wal.money -= price; wal.spent += price; bought.push(label + " $" + Math.round(price));
    }
  };
  for (let rnd = 0; rnd < 3; rnd++) {
    const d = C.ROUNDS[rnd]; const cap = C.CAP[rnd]; const wholesale = rnd >= 1 && rnd < 3; const aeroOpen = rnd >= C.AERO_UNLOCK_AFTER;
    if (rnd > 0) alloc = retune(alloc, tuneOf(d));
    const segA: Alloc = alloc, segL = L; const enter = L; done.add("open:" + rnd);
    const at = (Lx: number): Alloc => (Lx <= segL ? segA : addPoints(segA, spPoints(Lx) - spPoints(segL), tuneOf(d)));
    const ps = (Lx: number) => { const a = at(Lx); return a[0] / (a[0] + a[1] + a[2]); };
    let wallDone = false;
    const shop = (log: string[]) => { if (plan.autoBuy) autoShop(wal, L, rnd, d, done, wholesale, log); };
    for (let j = 0; j < 7; j++) {
      const name: string = C.RUNGS[j]; const B = budget(rnd, j); const T: number = C.TURNS[j]; const id = "R" + (rnd + 1) + " " + name;
      const bought: string[] = []; const failed: string[] = []; const cashBefore = wal.money; const owned0 = wal.owned.slice();
      shop(bought);
      const natural = shown(winPack(W, power(wal.owned, L, rnd, d) / B, T, d, ps(L)));
      const grind1 = () => { [L, bag] = applyXp(L, grindXp(L, cap), bag, cap); credit(purse(rnd, "kid", true)); shop(bought); };
      const ok = (gs: Weights[]) => {
        const r = power(wal.owned, L, rnd, d) / B;
        for (const g of gs) { const pk = winPack(g, r, T, d, ps(L)); if (plan.policy === "mine" ? shown(pk) < thr : pk.d < thr || (T >= 20 && hardWin(pk) < thr)) return false; }
        return true;
      };
      let extra = 0, auto = 0;
      for (let q = 0; q < (plan.extra[id] || 0) && L < cap; q++) { grind1(); extra++; }
      const pol = plan.policy;
      if (name === "boss" && (pol === "mixed" || pol === "hard") && L < cap) { while (L < cap) { grind1(); auto++; } }
      if ((name !== "boss" || pol === "mine") && L < cap && pol !== "story" && !(pol === "mixed" && wallDone)) {
        if (!ok(gate[pol])) { while (auto < 80 && L < cap && !ok(gate[pol])) { grind1(); auto++; } if (pol === "mixed") wallDone = true; }
      }
      const cashAtBuy = wal.money;
      manual(id, rnd, wholesale, aeroOpen, bought, failed);
      const pw = power(wal.owned, L, rnd, d); const r = pw / B; const win = winPack(W, r, T, d, ps(L));
      const gr = winPack(W, pw / budget(rnd, 0), C.GRIND_TURNS, d, ps(L)).d;
      const row: Row = {
        id, label: id, era: "R" + (rnd + 1), d, T, B, boss: name === "boss", billed: false, grindsAuto: auto, grindsExtra: extra, grindWin: gr, L, bag,
        power: pw, r, fill: modGap(L, rnd) ? Math.min(1, slotPts(wal.owned, d) / modGap(L, rnd)) : 1, alloc: at(L), pow: ps(L), win, show: shown(win),
        cashBefore, cashAfter: 0, debtAfter: 0, xp: 0, Lafter: 0, equipped: equipped(wal.owned, d).map((m) => (m ? modLabel(m) : "stock")),
        bought, failed, capL: cap, stage: rnd, wholesale, aeroOpen, done: Array.from(done), owned: owned0, ownedAfter: [], cashAtBuy, natural,
      };
      credit(purse(rnd, C.KIND[j], false)); done.add(rnd + ":" + name);
      const xp = storyXp(rnd, j, enter, cap); [L, bag] = applyXp(L, xp, bag, cap);
      row.xp = xp; row.Lafter = L; row.cashAfter = wal.money; row.debtAfter = Math.max(0, debt); row.ownedAfter = wal.owned.slice();
      rows.push(row);
    }
    if (plan.autoBuy) autoShop(wal, L, rnd, d, done, wholesale, []);
    alloc = at(L);
  }
  // pre-finale arc + finale (econ-v1 arc walk on the live garage; win at the district tune, as the sim)
  const races: any[] = [];
  for (let s = 0; s < 4; s++) {
    const steps = C.ARC.filter((a: any) => (s === 0 ? a.id[0] === "P" : a.id[0] === "M" && a.id[1] === String(s)));
    for (const a of steps) races.push({ id: a.id, d: a.d, T: a.T, B: a.B, step: s, billed: false, share: a.share, purse: a.purse });
    const f = C.FINALE[s]; races.push({ id: "F" + (s + 1), name: f.name, d: f.d, T: 30, B: f.B, step: s, billed: true, share: 0, purse: C.FIN_PURSE });
  }
  const arcGate = plan.policy !== "story";
  let curD = C.ROUNDS[2]; let segA: Alloc = alloc, segL = L;
  for (const rc of races) {
    const s = rc.step, capL = CAPS[s + 1], stage = 3 + s, ad: string = C.STEP_DIST[s], gap = xpSum(CAPS[s], CAPS[s + 1]);
    if (rc.d !== curD) { const cur = segL >= L ? segA : addPoints(segA, spPoints(L) - spPoints(segL), tuneOf(curD)); segA = retune(cur, tuneOf(rc.d)); segL = L; curD = rc.d; }
    const bought: string[] = []; const failed: string[] = []; const cashBefore = wal.money; const owned0 = wal.owned.slice();
    const shop = (log: string[]) => { if (plan.autoBuy) autoShop(wal, L, stage, ad, done, false, log); };
    const grind1 = () => { shop(bought); credit(C.ARC_GRIND_PAY); shop(bought); [L, bag] = applyXp(L, grindXp(L, capL), bag, capL); shop(bought); };
    const stuck = () => { shop(bought); const r = power(wal.owned, L, stage, ad) / rc.B; return hardWin(winPack(W, r, rc.T, rc.d, null)) < thr; };
    shop(bought); const natural = hardWin(winPack(W, power(wal.owned, L, stage, ad) / rc.B, rc.T, rc.d, null));
    let extra = 0, auto = 0;
    for (let q = 0; q < (plan.extra[rc.id] || 0) && L < capL; q++) { grind1(); extra++; }
    const mine = plan.policy === "mine";   // "mine": fewest grinds to the target on every race, finale included
    if (arcGate && (!rc.billed || mine) && L < capL && stuck()) { let g = 0; while (L < capL && g < 80) { if (stuck()) { grind1(); auto++; g++; } else break; } }
    if (rc.billed && arcGate && !mine && L < capL) { let g = 0; while (L < capL && g < 80) { grind1(); auto++; g++; } }
    shop(bought);
    const cashAtBuy = wal.money;
    manual(rc.id, stage, false, true, bought, failed);
    const pw = power(wal.owned, L, stage, ad); const r = pw / rc.B; const win = winPack(W, r, rc.T, rc.d, null);
    const al = L <= segL ? segA : addPoints(segA, spPoints(L) - spPoints(segL), tuneOf(rc.d));
    const row: Row = {
      id: rc.id, label: rc.billed ? rc.id + " " + rc.name : rc.id, era: rc.billed ? "Finale" : "Arc", d: rc.d, T: rc.T, B: rc.B, boss: rc.billed, billed: rc.billed,
      grindsAuto: auto, grindsExtra: extra, grindWin: winPack(W, C.ARC_GRIND_R, C.GRIND_TURNS, ad, null).d, L, bag, power: pw, r,
      fill: modGap(L, stage) ? Math.min(1, slotPts(wal.owned, ad) / modGap(L, stage)) : 1, alloc: al, pow: al[0] / (al[0] + al[1] + al[2]), win, show: hardWin(win),
      cashBefore, cashAfter: 0, debtAfter: 0, xp: 0, Lafter: 0, equipped: equipped(wal.owned, ad).map((m) => (m ? modLabel(m) : "stock")),
      bought, failed, capL, stage, wholesale: false, aeroOpen: true, done: Array.from(done), owned: owned0, ownedAfter: [], cashAtBuy, natural,
    };
    done.add("arc:" + rc.id); credit(rc.purse); shop(bought);
    if (!rc.billed) { const xp = C.ARC_FILL * rc.share * gap; row.xp = xp; [L, bag] = applyXp(L, xp, bag, capL); shop(bought); }
    row.Lafter = L; row.cashAfter = wal.money; row.debtAfter = Math.max(0, debt); row.ownedAfter = wal.owned.slice();
    rows.push(row);
  }
  return rows;
}
// at-cap boss check (progression.boss_check_at_cap): cap build, full mod fill
function bossAtCap(): [number, number][] {
  const out: [number, number][] = []; let L = 0; let alloc = startBuild();
  for (let rnd = 0; rnd < 3; rnd++) {
    const d = C.ROUNDS[rnd];
    if (rnd > 0) { alloc = retune(alloc, C.TUNE[d]); const e = L; L = C.CAP[rnd - 1]; alloc = addPoints(alloc, spPoints(L) - spPoints(e), C.TUNE[d]); }
    const cap = C.CAP[rnd]; const a = addPoints(alloc, spPoints(cap) - spPoints(L), C.TUNE[d]);
    const r = Math.round(Math.min(C.C_ROUND[rnd], C.MOD_CAP * statsAt(cap)) / budget(rnd, 6) * 1e4) / 1e4; const p = a[0] / (a[0] + a[1] + a[2]);
    const one = (pr: string) => { const x = presetPack(pr, r, 30, d, p); return r1(x.h as number); };
    out.push([one("c6060"), one("c8080")]); L = cap; alloc = a;
  }
  return out;
}
// ENGINE-END
