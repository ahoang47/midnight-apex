// ENGINE-START (planner-v2 engine: live mod_skill rules; mirrors py_reference.py; verified by verify.mjs)
type Buy = { at: string; phase: "pre" | "post"; slot: number };
type Plan = { wilds: Record<string, number>; nm: Record<string, number>; buys: Buy[] };
type Slot = [number, number, number] | null; // [group round index, Mk, earned points]
type Move = { label: string; purse: number; toDebt: number; net: number; cash: number; debt: number };
type Row = {
  id: string; rnd: number; j: number; d: string; T: number; crew: number; boss: boolean; req: number; nm: number; nmw: number;
  skill: number; N: number; points: number; ledger: number; floor: number; win: number | null; cashArrive: number; debtArrive: number;
  cash: number; debt: number; xpX: number; xpW: number; lostX: number; lostW: number; slotsRace: Slot[]; slots: Slot[];
  errors: string[]; moves: Move[]; ws: boolean;
};
const r1 = (x: number) => Math.floor(x * 10 + 0.5 + 1e-9) / 10;
function span(xs: number[], x: number): [number, number, number] {
  const n = xs.length;
  if (x <= xs[0]) return [0, 0, 0];
  if (x >= xs[n - 1]) return [n - 1, n - 1, 0];
  let i = 1; while (xs[i] < x && Math.abs(xs[i] - x) >= 1e-12) i++;
  if (Math.abs(xs[i] - x) < 1e-12) return [i, i, 0];
  return [i - 1, i, (x - xs[i - 1]) / (xs[i] - xs[i - 1])];
}
// win % from the Monte Carlo table: bilinear in reading s (WT.Q) and car points (WT.PTS[d]), clamped to the grid
function winAt(d: string, j: number, s: number, pts: number): number {
  const t = WT.WIN[d][j]; const [q0, q1, fq] = span(WT.Q, s); const [p0, p1, fp] = span(WT.PTS[d], pts);
  const lo = t[q0][p0] * (1 - fp) + t[q0][p1] * fp, hi = t[q1][p0] * (1 - fp) + t[q1][p1] * fp;
  return r1(lo * (1 - fq) + hi * fq);
}
const usd0 = (x: number) => "$" + Math.round(x).toLocaleString("en-US");
const tierOf = (s: [number, number, number]) => C.TIER[s[0]][s[1] - 1];
const copySlots = (a: Slot[]): Slot[] => a.map((s) => (s ? [s[0], s[1], s[2]] : null));
const nextStep = (s: Slot, rnd: number): [number, number] => (!s || s[0] < rnd ? [rnd, 1] : [s[0], s[1] + 1]);

function simulate(plan: Plan): Row[] {
  let cash = 0, debt = C.DEBT, ledger = C.STOCK; const slots: Slot[] = []; for (let i = 0; i < C.SLOTS; i++) slots.push(null);
  const rows: Row[] = [];
  const pts = () => C.STOCK + slots.reduce((a, s) => a + (s ? s[2] : 0), 0);
  const credit = (pay: number) => { let t = 0; if (debt > 0) { t = Math.min(debt, C.DEBT_SHARE * pay); debt -= t; } cash += pay - t; return t; };
  // Garage.assign: the slot with the most room first (stable on ties), spilling; the rest is lost but stays in the ledger
  const assign = (xp: number) => {
    ledger += xp;
    const own = slots.filter((s) => s) as [number, number, number][];
    own.sort((a, b) => (a[2] - tierOf(a)) - (b[2] - tierOf(b)));
    for (const s of own) { const room = tierOf(s) - s[2]; if (room > 0 && xp > 0) { const t = Math.min(room, xp); s[2] += t; xp -= t; } }
    return xp;
  };
  for (let rnd = 0; rnd < 3; rnd++) {
    const d: string = C.ROUNDS[rnd]; const ws: boolean = C.WHOLESALE_ON[rnd]; let nmw = 0;
    const ex: [number, number][] = [];
    for (let j = 0; j < 7; j++) {
      const id = "R" + (rnd + 1) + " " + C.RUNGS[j];
      const w = Math.max(0, Math.floor(plan.wilds[id] || 0)), n = Math.max(0, Math.floor(plan.nm[id] || 0));
      ex.push([Math.min(w, C.REQ_WILDS[j]), n + Math.max(0, w - C.REQ_WILDS[j])]);
    }
    const N = 6 + ex.reduce((a, e) => a + e[0] + e[1], 0); let ran = 0;
    for (let j = 0; j < 7; j++) {
      const id = "R" + (rnd + 1) + " " + C.RUNGS[j]; const err: string[] = []; const [req, nm] = ex[j];
      const moves: Move[] = []; const cashArrive = cash, debtArrive = debt;
      moves.push({ label: "On arrival", purse: 0, toDebt: 0, net: 0, cash, debt });
      const buy = (phase: "pre" | "post") => {
        const top = (phase === "pre" ? C.MK_PRE : C.MK_POST)[j];
        for (const b of plan.buys) {
          if (b.at !== id || b.phase !== phase) continue;
          const i = b.slot; const s = slots[i]; const [g, mk] = nextStep(s, rnd);
          if (mk > 3) { err.push("buy slot " + (i + 1) + ": already Mk3"); continue; }
          if (mk > top) { err.push("buy slot " + (i + 1) + ": Mk" + mk + " not on sale yet"); continue; }
          const price = (ws ? C.PRICE_WS : C.PRICE)[g][mk - 1];
          if (price > cash + 1e-9) { err.push("buy slot " + (i + 1) + ": needs " + usd0(price) + ", have " + usd0(cash)); continue; }
          cash -= price;
          slots[i] = [g, mk, s ? s[2] : 0];
          moves.push({ label: "Slot " + (i + 1) + ": R" + (g + 1) + " Mk" + mk + (phase === "pre" ? " · before the extra races" : " · after the win"), purse: 0, toDebt: 0, net: -price, cash, debt });
        }
      };
      buy("pre");
      let lostX = 0, xpX = 0; const wp = C.WILD_PURSE[rnd];
      const addMove = (lab: string, k: number, td: number) => { if (k) moves.push({ label: lab + " × " + k, purse: wp * k, toDebt: td, net: wp * k - td, cash, debt }); };
      let td = 0;
      for (let k = 0; k < req; k++) { td += credit(wp); xpX += C.WILD_XP[rnd]; lostX += assign(C.WILD_XP[rnd]); }
      addMove("Required wild encounters", req, td); td = 0;
      for (let k = 0; k < nm; k++) { const x = nmw < C.NM_CAP ? C.WILD_XP[rnd] : 0; td += credit(wp); xpX += x; lostX += assign(x); nmw++; }
      addMove("Non-mandatory wins", nm, td);
      ran += req + nm;
      const skill = C.SKILL[0] + (C.SKILL[1] - C.SKILL[0]) * ran / N;
      const p = pts(); const fl = C.FLOOR[d][j];
      if (req < C.REQ_WILDS[j]) err.push("needs " + C.REQ_WILDS[j] + " required wild win(s) first, has " + req);
      if (ledger < fl - 1e-9) err.push("locked: earned " + ledger.toFixed(1) + " < floor " + fl);
      const ok = req >= C.REQ_WILDS[j] && ledger >= fl - 1e-9;
      const win = ok ? winAt(d, j, skill, p) : null;
      const ledgerRace = ledger; const slotsRace = copySlots(slots);
      const sPay = C.PURSE[rnd][C.KIND[j]]; const sTd = credit(sPay);
      moves.push({ label: "Story purse (on a win)", purse: sPay, toDebt: sTd, net: sPay - sTd, cash, debt });
      buy("post");
      const xpW = C.STORY_XP[rnd][j]; const lostW = assign(xpW);
      ran += 1;
      rows.push({
        id, rnd, j, d, T: C.TURNS[j], crew: C.CREW[d][j], boss: j === 6, req, nm, nmw, skill, N, points: p, ledger: ledgerRace, floor: fl, win,
        cashArrive, debtArrive, cash, debt, xpX, xpW, lostX, lostW, slotsRace, slots: copySlots(slots), errors: err, moves, ws,
      });
    }
  }
  return rows;
}
// ENGINE-END
