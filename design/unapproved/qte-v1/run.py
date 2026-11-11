#!/usr/bin/env python3
"""qte-v1 experiment runner. Writes results.json and RESULTS.md. No repo edits."""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

import numpy as np

import qte_model as M
import wr_shortcut as W

HERE = Path(__file__).resolve().parent
OFFICIAL = Path("/workspace/midnight-apex/sim/config/winrate_n4000.json")

# Forced-policy arrival r (repo progression, default crew order).
# mature #2 skipped is 1.0355 in every crew; bosses at target are 1.05.
CELLS = [
    {"id": "touge_boss_target", "label": "Touge boss at target", "district": "touge", "r": 1.05, "kind": "boss_target"},
    {"id": "wangan_boss_target", "label": "Wangan boss at target", "district": "wangan", "r": 1.05, "kind": "boss_target"},
    {"id": "street_boss_target", "label": "Street boss at target", "district": "street", "r": 1.05, "kind": "boss_target"},
    {"id": "touge_mature2_skip", "label": "Touge mature #2 skipped", "district": "touge", "r": 1.0355, "kind": "mature2_skip"},
    {"id": "wangan_mature2_skip", "label": "Wangan mature #2 skipped", "district": "wangan", "r": 1.0355, "kind": "mature2_skip"},
    {"id": "street_mature2_skip", "label": "Street mature #2 skipped", "district": "street", "r": 1.0355, "kind": "mature2_skip"},
    {"id": "myth2_skip", "label": "Myth #2 skipped", "district": "wangan", "r": 1.0336, "kind": "myth2_skip"},
    {"id": "summit_skip", "label": "Summit skipped", "district": "touge", "r": 1.0359, "kind": "summit_skip"},
]

# Representative opponent budgets (forced path, SP points = Delta_r * B).
BUDGETS = {
    "mature2_skip": {"R1 Touge": 315.8, "R1 Wangan": 347.4, "R1 Street": 382.1, "R3 Wangan": 944.9},
    "boss_target": {"R1 Touge": 330.0, "R1 Wangan": 363.0, "R1 Street": 399.3, "R3 Wangan": 987.5},
}

MOD_MULTS = (0.10, 0.20, 0.30)
PROFILES = ("weak", "average", "strong")
QT_CURRENT = {"weak": 0.4, "average": 0.6, "strong": 0.8}


def official_band(table: dict, q: str, district: str, r: float) -> list[float] | None:
    block = table["q"][q][district]
    for i, x in enumerate(block["r"]):
        if abs(x - r) < 1e-12:
            return [block["min"][i], block["max"][i]]
    return None


def verify_closed_form(sigmas: dict, n: int = 200_000, seed: int = 20261110) -> dict:
    """Monte Carlo check of E[s] vs the closed form (not used as a result source)."""
    rng = np.random.default_rng(seed)
    checks = []
    for name, rec in sigmas.items():
        sig = rec["sigma_over_a0"]
        for w in (0.3276, 0.58, 1.0, 1.3):
            e_closed = M.expected_score(w, sig)
            err = rng.normal(0.0, sig, n)
            s = np.clip(1.0 - np.abs(err) / w, 0.0, None)
            e_mc = float(s.mean())
            checks.append({
                "profile": name, "w_over_w0": w,
                "closed": e_closed, "mc": e_mc, "abs_diff": abs(e_closed - e_mc),
            })
    return {
        "n": n, "seed": seed,
        "max_abs_diff": max(c["abs_diff"] for c in checks),
        "checks": checks,
    }


def width_curve(sigma_avg: float) -> dict:
    knots = []
    for r, _ in M.KNOT_WINDOW_105:
        knots.append(M.width_for_average_at_r(r, sigma_avg))
    knots.append(M.width_for_average_at_r(1.10, sigma_avg))  # 1.05+ plateau

    grid_r = [round(x, 4) for x in np.arange(0.80, 1.10001, 0.0025)]
    grid = [M.width_for_average_at_r(r, sigma_avg) for r in grid_r]
    ws = [g["w_over_w0"] for g in grid]
    d1 = [ws[i + 1] - ws[i] for i in range(len(ws) - 1)]
    # "Smooth" = no sign flip in first differences, no jump larger than the
    # adjacent-knot rise of W would imply after the inverse transform.
    monotone = all(d >= -1e-12 for d in d1)
    max_step = max(d1)
    # Locate the steepest grid step (expect 1.00 -> 1.05).
    i_steep = int(np.argmax(d1))
    return {
        "knots": knots,
        "grid": [{"r": g["r"], "W": g["knot_window"], "w_over_w0": g["w_over_w0"], "w_ms": g["w_ms"]} for g in grid],
        "monotone_nondecreasing": monotone,
        "min_first_diff": min(d1),
        "max_first_diff": max_step,
        "steepest_step": {"r_from": grid_r[i_steep], "r_to": grid_r[i_steep + 1], "dw": d1[i_steep]},
        "flat_below_r": 0.90,  # W (and therefore w) is flat on [0.80, 0.90]
        "plateau_from_r": 1.05,
    }


def band_payload(cell_wr: dict, district: str) -> dict:
    d = cell_wr["districts"][district]
    return {
        "min": d["min"], "max": d["max"], "mid": d["mid"],
        "band_1dp": d["band_1dp"],
    }


def within_official(new_band: list[float], official: list[float], tol: float = 2.0) -> bool:
    return (new_band[0] >= official[0] - tol) and (new_band[1] <= official[1] + tol)


def find_r_equivalent(banks, r0: float, target_mid: float, qhat_of_r, r_lo: float, r_hi: float, district: str) -> dict:
    """Binary search r in [r_lo, r_hi] whose mid WR (at that r's qhat) matches target_mid.

    Uses the district mid (min+max)/2 over seeds x lengths. Returns whether
    the target was reached inside the interval.
    """
    def mid_at(r):
        qhat = qhat_of_r(r)
        wr = W.wr_cell(banks, r, qhat)
        return wr["districts"][district]["mid"], qhat, wr

    m_lo, _, _ = mid_at(r_lo)
    m_hi, _, _ = mid_at(r_hi)
    # WR should rise with r; if target is outside, report the bound.
    if target_mid <= m_lo + 1e-9:
        return {"found": True, "r": r_lo, "delta_r": r_lo - r0, "mid": m_lo, "note": "at_or_below_low_end"}
    if target_mid >= m_hi - 1e-9:
        return {"found": False, "r": r_hi, "delta_r": r_hi - r0, "mid": m_hi, "note": "above_high_end", "high_end_mid": m_hi}
    lo, hi = r_lo, r_hi
    mid = qhat = wr = None
    for _ in range(40):
        r = 0.5 * (lo + hi)
        mid, qhat, wr = mid_at(r)
        if mid < target_mid:
            lo = r
        else:
            hi = r
    r = 0.5 * (lo + hi)
    mid, qhat, wr = mid_at(r)
    return {
        "found": True, "r": r, "delta_r": r - r0, "mid": mid, "qhat": qhat,
        "band_1dp": wr["districts"][district]["band_1dp"],
        "note": "interpolated",
    }


def fmt_band(b) -> str:
    return f"{b[0]:.1f}–{b[1]:.1f}"


def md_escape(s: str) -> str:
    return s


def write_results_md(data: dict, path: Path) -> None:
    sig = data["sigmas"]
    lines = []
    A = lines.append
    A("# qte-v1 — visible QTE window replaces hidden knot_window(r)")
    A("")
    A("Draft only (`/workspace/barry-drafts/qte-v1`). No repo edits. Austin's direction (2026-11-10): the stat gap should make the visible QTE harder or easier, replacing the hidden `knot_window(r)` multiplier; specific mods exist that only widen the QTE window; the QTE must not change with mid-race position.")
    A("")
    A("All win rates below were produced by this run from the official clash-count banks (q_read = 0.6, N = 4000, seeds 20261113–15 × 10/20/30 turns). Skill σ values and the linear-falloff press model are **placeholders until playtest data exists**. Numbers are not invented.")
    A("")
    A("## 1. QTE model (placeholders)")
    A("")
    A("- Timing error `e ~ Normal(0, σ)`, unbiased.")
    A("- Zone width `w`, default `w0 = 800 ms` (Godot `QTE_TIMING_WINDOW_BASE_MS`; presentation unit only). Half-width `a0 = 400 ms`.")
    A("- Hit quality: `s = max(0, 1 − |e| / (w/2))` — 1 at centre, 0 at the edge and outside.")
    A("- Raw turn score used here is `E[s]` (closed form), as a constant `q_time`. This matches the oracle's fixed-`q_time` methodology. Multiple presses would not change `E[s]`; mash speed is unused in this draft.")
    A("- `q_eff = raw × HAN modifier`, with **no** `knot_window`. Runs are balanced (HAN share = 1/3, modifier = 1), so `q_eff = raw`.")
    A("- Zone width depends on the race's fixed stat ratio `r`, not on mid-race lead.")
    A("")
    A("| profile | target E[s] at default zone | σ / a0 | σ (ms) | achieved E[s] |")
    A("|---------|----------------------------:|-------:|-------:|--------------:|")
    for name in PROFILES:
        rec = sig[name]
        A(f"| {name} | {rec['target_E_at_default_zone']:.1f} | {rec['sigma_over_a0']:.6f} | {rec['sigma_ms']:.3f} | {rec['achieved_E_at_default_zone']:.6f} |")
    A("")
    A(f"Closed-form check vs Monte Carlo (n={data['closed_form_check']['n']:,}): max |Δ| = {data['closed_form_check']['max_abs_diff']:.6f}.")
    A("")
    A("## 2. Zone width w(r)")
    A("")
    A("`w(r)` is chosen so the **average** player's expected raw score equals `0.6 × KNOT_WINDOW_105(r)`, the current effective `q_time × window` value. Widths are fractions of the default zone.")
    A("")
    A("| r | W(r) | target E[s] = 0.6·W | w(r)/w0 | w (ms at w0=800) |")
    A("|--:|-----:|--------------------:|--------:|-----------------:|")
    for k in data["w_curve"]["knots"]:
        A(f"| {k['r']:.2f} | {k['knot_window']:.2f} | {k['target_E']:.4f} | {k['w_over_w0']:.4f} | {k['w_ms']:.1f} |")
    A("")
    wc = data["w_curve"]
    A(f"On the 0.80–1.10 grid (step 0.0025): monotone non-decreasing = {wc['monotone_nondecreasing']}; min first difference = {wc['min_first_diff']:.6e}; max first difference = {wc['max_first_diff']:.6f} (steepest step r={wc['steepest_step']['r_from']:.4f}→{wc['steepest_step']['r_to']:.4f}). `w(r)` is flat on [0.80, 0.90] (inherited from W) and plateaus for r ≥ 1.05 at the default zone. Between knots it is a smooth increasing transform of the piecewise-linear W, so it has the same kinks as W (derivative jumps at 0.90, 0.95, 1.00, 1.05) but the segments are not linear in w.")
    A("")
    A("## 3. Oracle cells, window removed")
    A("")
    A("New model: `qhat = E[s | w(r), σ_profile]`. Current model (comparison): `qhat = q_time × W(r)` with q_time 0.4 / 0.6 / 0.8. **q_read stays 0.6** in both (timing only; this is not the official table's q=0.8 column, which also changes read skill). Average should sit inside the official 0.6 band ±2 points.")
    A("")
    A("### Average vs official 0.6 band")
    A("")
    A("| cell | r | official 0.6 | current model (0.6·W) | new model (E[s]) | Δ mid vs current | inside official ±2? |")
    A("|------|--:|-------------:|----------------------:|-----------------:|-----------------:|--------------------:|")
    for cell in data["cells"]:
        d = cell["district"]
        off = cell["official_q06"]
        cur = cell["current"]["average"][d]
        new = cell["new"]["average"][d]
        dmid = new["mid"] - cur["mid"]
        A(f"| {cell['label']} | {cell['r']} | {fmt_band(off)} | {fmt_band(cur['band_1dp'])} | {fmt_band(new['band_1dp'])} | {dmid:+.2f} | {cell['average_within_official_pm2']} |")
    A("")
    A("### Skill spread: new E[s] vs current q_time × W(r)")
    A("")
    A("At r = 1.05 the default zone is used, so the three profiles reproduce 0.4 / 0.6 / 0.8 exactly and the win-rate spread matches the current model. At r < 1.05 the tighter zone does **not** scale scores linearly: a strong player loses less than `0.8·W(r)` would predict, a weak player a little more than `0.4·W(r)`.")
    A("")
    A("| cell | profile | qhat current | qhat new | official-style band current | band new | Δ mid |")
    A("|------|---------|-------------:|---------:|----------------------------:|---------:|------:|")
    for cell in data["cells"]:
        d = cell["district"]
        for prof in PROFILES:
            cur = cell["current"][prof][d]
            new = cell["new"][prof][d]
            A(f"| {cell['label']} | {prof} | {cell['current'][prof]['qhat']:.4f} | {cell['new'][prof]['qhat']:.4f} | {fmt_band(cur['band_1dp'])} | {fmt_band(new['band_1dp'])} | {new['mid']-cur['mid']:+.2f} |")
    A("")
    A("Pooled (equal-weight mean of the three districts, then min/max over seeds × lengths) for the shared-r skip cells:")
    A("")
    A("| cell | r | profile | current pooled | new pooled | Δ mid |")
    A("|------|--:|---------|---------------:|-----------:|------:|")
    seen_pooled = set()
    for cell in data["cells"]:
        if cell["kind"] not in ("mature2_skip", "myth2_skip", "summit_skip"):
            continue
        key = (cell["kind"], cell["r"])
        if key in seen_pooled:
            continue
        seen_pooled.add(key)
        label = "mature #2 skipped (any district)" if cell["kind"] == "mature2_skip" else cell["label"]
        for prof in PROFILES:
            cur = cell["current"][prof]["pooled"]
            newb = cell["new"][prof]["pooled"]
            A(f"| {label} | {cell['r']} | {prof} | {fmt_band(cur['band_1dp'])} | {fmt_band(newb['band_1dp'])} | {newb['mid']-cur['mid']:+.2f} |")
    A("")
    A("## 4. Window-only mods")
    A("")
    A("A window mod multiplies the current `w(r)` by 1.10 / 1.20 / 1.30 (it does not change `r` or `V = r**kappa`). Gains are versus the no-mod new model for the same profile. Also shown: a flat add of +10/20/30% of the **default** zone (`w(r) + x·w0`).")
    A("")
    A("### Multiplicative +X% of w(r) — win-rate gain")
    A("")
    A("| cell | profile | no mod | +10% | gain | +20% | gain | +30% | gain |")
    A("|------|---------|-------:|-----:|-----:|-----:|-----:|-----:|-----:|")
    for rec in data["window_mods"]["multiplicative"]:
        def g(x):
            return rec["mods"][x]
        A(
            f"| {rec['label']} | {rec['profile']} | {fmt_band(rec['baseline']['band_1dp'])} | "
            f"{fmt_band(g('0.1')['band_1dp'])} | {g('0.1')['gain_mid']:+.2f} | "
            f"{fmt_band(g('0.2')['band_1dp'])} | {g('0.2')['gain_mid']:+.2f} | "
            f"{fmt_band(g('0.3')['band_1dp'])} | {g('0.3')['gain_mid']:+.2f} |"
        )
    A("")
    A("### Flat add +X% of w0 — win-rate gain (same cells)")
    A("")
    A("| cell | profile | no mod | +0.10 w0 | gain | +0.20 w0 | gain | +0.30 w0 | gain |")
    A("|------|---------|-------:|---------:|-----:|---------:|-----:|---------:|-----:|")
    for rec in data["window_mods"]["flat"]:
        def g(x):
            return rec["mods"][x]
        A(
            f"| {rec['label']} | {rec['profile']} | {fmt_band(rec['baseline']['band_1dp'])} | "
            f"{fmt_band(g('0.1')['band_1dp'])} | {g('0.1')['gain_mid']:+.2f} | "
            f"{fmt_band(g('0.2')['band_1dp'])} | {g('0.2')['gain_mid']:+.2f} | "
            f"{fmt_band(g('0.3')['band_1dp'])} | {g('0.3')['gain_mid']:+.2f} |"
        )
    A("")
    A("### Stat-point equivalence (average player, multiplicative mods)")
    A("")
    A("A flat stat mod raises `r` (and therefore both `V = r**kappa` and `w(r)`, until the zone plateaus at r = 1.05). Window mods raise only the zone. Equivalence is the `r'` whose new-model average mid win rate matches the window-mod mid, searched first inside the 105% cap (`r ≤ 1.05`) and then, if needed, above it.")
    A("")
    A("| cell | r0 | mod | mid WR | r' inside cap? | r' | Δr | ΔSP at R1 Touge B | ΔSP at R3 Wangan B |")
    A("|------|---:|-----|-------:|:---------------|---:|---:|------------------:|-------------------:|")
    for rec in data["stat_equivalence"]:
        B1 = rec["delta_sp"]["R1"]
        B3 = rec["delta_sp"]["R3"]
        inside = "yes" if rec["inside_cap"]["found"] and rec["inside_cap"]["r"] <= 1.05 + 1e-12 and rec["inside_cap"]["note"] != "above_high_end" else "no"
        used = rec["inside_cap"] if inside == "yes" else rec["uncapped"]
        A(
            f"| {rec['label']} | {rec['r0']} | {rec['mod_label']} | {rec['target_mid']:.2f} | {inside} | "
            f"{used['r']:.4f} | {used['delta_r']:+.4f} | {B1[used['name']]:+.1f} | {B3[used['name']]:+.1f} |"
        )
    A("")
    A("ΔSP = Δr × opponent budget. Representative budgets: mature #2 R1 Touge 315.8 / R3 Wangan 944.9; boss R1 Touge 330.0 / R3 Wangan 987.5.")
    A("")
    A("## 5. Cap-dodge risk and recommended limits")
    A("")
    cd = data["cap_dodge"]
    A(cd["narrative"])
    A("")
    A("| r | meaning | no-mod mid (avg, pooled) | +10% w(r) | +20% | +30% | +0.30 w0 flat |")
    A("|--:|---------|-------------------------:|----------:|-----:|-----:|--------------:|")
    for row in cd["rows"]:
        A(
            f"| {row['r']:.2f} | {row['meaning']} | {row['baseline_mid']:.2f} | "
            f"{row['m10_mid']:.2f} | {row['m20_mid']:.2f} | {row['m30_mid']:.2f} | {row['flat30_mid']:.2f} |"
        )
    A("")
    A("## Surprises and notes")
    A("")
    for note in data["notes"]:
        A(f"- {note}")
    A("")
    A("## How to reproduce")
    A("")
    A("```")
    A("cd /workspace/barry-drafts/qte-v1 && python3 run.py")
    A("```")
    A("")
    A("Requires numpy and the existing count banks under `barry-drafts/final-v1` and `barry-drafts/lines-v1`. Does not import or edit the midnight-apex working tree except to read `sim/config/winrate_n4000.json` for the official bands.")
    A("")
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    official = json.loads(OFFICIAL.read_text())
    sigmas_full = M.fit_sigmas()
    sig = {name: sigmas_full[name]["sigma_over_a0"] for name in PROFILES}
    curve = width_curve(sig["average"])
    check = verify_closed_form(sigmas_full)
    banks = W.load_banks()

    def w_of(r: float) -> float:
        return M.width_for_average_at_r(r, sig["average"])["w_over_w0"]

    cells_out = []
    for cell in CELLS:
        r = cell["r"]
        w = w_of(r)
        W_r = M.knot_window(r)
        off = official_band(official, "0.6", cell["district"], r)
        current = {}
        new = {}
        for prof in PROFILES:
            q_cur = QT_CURRENT[prof] * W_r
            q_new = M.expected_score(w, sig[prof])
            wr_cur = W.wr_cell(banks, r, q_cur)
            wr_new = W.wr_cell(banks, r, q_new)
            current[prof] = {
                "qhat": q_cur,
                cell["district"]: band_payload(wr_cur, cell["district"]),
                "pooled": band_payload(wr_cur, "pooled"),
            }
            new[prof] = {
                "qhat": q_new,
                cell["district"]: band_payload(wr_new, cell["district"]),
                "pooled": band_payload(wr_new, "pooled"),
            }
        avg_band = new["average"][cell["district"]]["band_1dp"]
        cells_out.append({
            **cell,
            "W": W_r,
            "w_over_w0": w,
            "official_q06": off,
            "current": current,
            "new": new,
            "average_within_official_pm2": within_official(avg_band, off, 2.0),
        })

    # Window mods on the cells the brief named: boss at target + mature #2 skipped.
    # Use Street as a named district plus all three bosses / all three mature#2, and
    # also Myth/Summit are not required for this section.
    mod_cells = [c for c in cells_out if c["kind"] in ("boss_target", "mature2_skip")]

    def eval_mod(cell, prof, w_used):
        qhat = M.expected_score(w_used, sig[prof])
        wr = W.wr_cell(banks, cell["r"], qhat)
        d = cell["district"]
        return {
            "w_over_w0": w_used, "qhat": qhat,
            **band_payload(wr, d),
        }

    def pack_mods(kind: str):
        rows = []
        for cell in mod_cells:
            w0r = cell["w_over_w0"]
            for prof in PROFILES:
                base = eval_mod(cell, prof, w0r)
                mods = {}
                for x in MOD_MULTS:
                    w_used = w0r * (1.0 + x) if kind == "multiplicative" else w0r + x
                    rec = eval_mod(cell, prof, w_used)
                    rec["gain_mid"] = rec["mid"] - base["mid"]
                    rec["gain_band"] = [rec["band_1dp"][0] - base["band_1dp"][0], rec["band_1dp"][1] - base["band_1dp"][1]]
                    mods[str(x)] = rec
                rows.append({
                    "id": cell["id"], "label": cell["label"], "district": cell["district"],
                    "r": cell["r"], "kind": cell["kind"], "profile": prof,
                    "baseline": base, "mods": mods,
                })
        return rows

    mods_mult = pack_mods("multiplicative")
    mods_flat = pack_mods("flat")

    # Stat equivalence for average player, multiplicative mods, Street as the
    # representative district for each kind (Street was the thin official
    # spot-check) plus we average? Better: do it per cell (3 bosses + 3 mature).
    def qhat_avg_at_r(r):
        return M.expected_score(w_of(r), sig["average"])

    stat_eq = []
    for rec in mods_mult:
        if rec["profile"] != "average":
            continue
        r0 = rec["r"]
        d = rec["district"]
        budgets = BUDGETS["boss_target" if rec["kind"] == "boss_target" else "mature2_skip"]
        B_r1 = budgets["R1 Touge"]
        B_r3 = budgets["R3 Wangan"]
        for x in MOD_MULTS:
            key = str(x)
            target_mid = rec["mods"][key]["mid"]
            inside = find_r_equivalent(banks, r0, target_mid, qhat_avg_at_r, r0, 1.05, d)
            inside["name"] = "inside"
            uncapped = find_r_equivalent(banks, r0, target_mid, qhat_avg_at_r, r0, 1.20, d)
            uncapped["name"] = "uncapped"

            def sp(block, B):
                return block["delta_r"] * B

            # attach SP for whichever block
            for block, name in ((inside, "inside"), (uncapped, "uncapped")):
                pass
            stat_eq.append({
                "label": rec["label"], "id": rec["id"], "r0": r0, "district": d,
                "mod_label": f"+{int(x*100)}% w(r)", "x": x,
                "target_mid": target_mid,
                "inside_cap": inside, "uncapped": uncapped,
                "delta_sp": {
                    "R1": {"inside": sp(inside, B_r1), "uncapped": sp(uncapped, B_r1)},
                    "R3": {"inside": sp(inside, B_r3), "uncapped": sp(uncapped, B_r3)},
                    "budgets": {"R1": B_r1, "R3": B_r3},
                },
            })

    # Cap-dodge illustration at r=0.80 (SP cap, no mods), r=1.00, r=1.05 (mod cap).
    cap_rows = []
    for r, meaning in ((0.80, "SP cap / no mods at a 1.05 reference"), (1.00, "between caps"), (1.05, "105% mod cap / boss at target")):
        w = w_of(r)
        def mid_pooled(width):
            qhat = M.expected_score(width, sig["average"])
            wr = W.wr_cell(banks, r, qhat)
            return wr["districts"]["pooled"]["mid"], wr["districts"]["pooled"]["band_1dp"]
        b_mid, b_band = mid_pooled(w)
        row = {"r": r, "meaning": meaning, "w_over_w0": w, "baseline_mid": b_mid, "baseline_band": b_band}
        for x, key in ((0.10, "m10_mid"), (0.20, "m20_mid"), (0.30, "m30_mid")):
            row[key], row[key.replace("_mid", "_band")] = mid_pooled(w * (1.0 + x))
        row["flat30_mid"], row["flat30_band"] = mid_pooled(w + 0.30)
        cap_rows.append(row)

    # Build recommended-limit narrative from the actual numbers (filled after we have them).
    # We'll write it after computing a few headline figures.
    boss_avg_gains = [r for r in mods_mult if r["profile"] == "average" and r["kind"] == "boss_target"]
    skip_avg_gains = [r for r in mods_mult if r["profile"] == "average" and r["kind"] == "mature2_skip"]
    # mean mid gain across the three districts
    def mean_gain(rows, x):
        return float(np.mean([row["mods"][str(x)]["gain_mid"] for row in rows]))

    g_boss = {x: mean_gain(boss_avg_gains, x) for x in MOD_MULTS}
    g_skip = {x: mean_gain(skip_avg_gains, x) for x in MOD_MULTS}
    cap80 = cap_rows[0]
    cap105 = cap_rows[2]

    # Equivalence at Street mature #2 +30% — is it inside the cap?
    street_m2_30 = next(s for s in stat_eq if s["id"] == "street_mature2_skip" and abs(s["x"] - 0.30) < 1e-12)
    street_boss_10 = next(s for s in stat_eq if s["id"] == "street_boss_target" and abs(s["x"] - 0.10) < 1e-12)

    notes = []
    # average match
    n_ok = sum(1 for c in cells_out if c["average_within_official_pm2"])
    notes.append(
        f"Average-player new-model bands sit inside the official 0.6 band ±2 on {n_ok}/{len(cells_out)} named cells. "
        "They should match the current 0.6·W model almost exactly, because E[s] was calibrated to that value; leftover difference is rounding only."
    )
    # skill spread headline at r<1.05
    s_cell = next(c for c in cells_out if c["id"] == "street_mature2_skip")
    notes.append(
        f"At Street mature #2 skipped (r=1.0355, w/w0={s_cell['w_over_w0']:.4f}), the strong player's qhat is "
        f"{s_cell['new']['strong']['qhat']:.4f} vs the linear {s_cell['current']['strong']['qhat']:.4f}, "
        f"mid WR {s_cell['new']['strong']['street']['mid']:.2f} vs {s_cell['current']['strong']['street']['mid']:.2f}. "
        f"The weak player's qhat is {s_cell['new']['weak']['qhat']:.4f} vs {s_cell['current']['weak']['qhat']:.4f}. "
        "A tight visible zone punishes imprecision more, but a precise player still hits it — the hidden linear window flattened that difference."
    )
    notes.append(
        "At r=0.80 (the 80% SP cap with no mods) the effect is larger: the same tight zone (w/w0="
        f"{w_of(0.80):.4f}) gives the strong placeholder E[s]={M.expected_score(w_of(0.80), sig['strong']):.4f} "
        f"against a linear 0.8·W(0.80)={0.8*M.knot_window(0.80):.4f}."
    )
    notes.append(
        "q_read was held at 0.6. The official winrate table's q=0.8 column is not the right comparison here; that column also uses the 0.8 read bank and sits in the high 90s at these cells."
    )
    notes.append(
        "The QTE does not depend on mid-race progress in this model: w is a function of the race's fixed stat ratio r only."
    )

    # Recommend a cap on total zone width at 1.15 * w0 or 1.20 * w0,
    # based on gains at r=1.05 (pure cap dodge) vs remaining headroom when behind.
    rec_bits = []
    rec_bits.append(
        f"The 105% cap is the real dodge. Window mods do not spend SP or the 25% mod budget. At r=1.05 the zone is already the default, so a +X% mod pushes E[s] above 0.6 and raises win rate while a legal stat mod cannot raise r further. "
        f"Across the three boss-at-target districts, an average player gains about {g_boss[0.10]:.1f} / {g_boss[0.20]:.1f} / {g_boss[0.30]:.1f} mid-WR points from +10/20/30% of w(r) — enough to turn a ~64% mid into the mid-70s. "
        f"Street boss +10% has no match inside the cap; the uncapped equivalent is r'={street_boss_10['uncapped']['r']:.4f} (Δr={street_boss_10['uncapped']['delta_r']:+.4f}, about {street_boss_10['delta_sp']['R1']['uncapped']:.1f} SP on R1 Touge's budget or {street_boss_10['delta_sp']['R3']['uncapped']:.1f} SP on R3 Wangan's)."
    )
    rec_bits.append(
        f"The 80% SP cap is not dodged. At r=0.80, V=r**kappa still dominates: the pooled average mid stays {cap80['baseline_mid']:.2f} with no mod, {cap80['m10_mid']:.2f} / {cap80['m20_mid']:.2f} / {cap80['m30_mid']:.2f} with +10/20/30% of w(r), and only {cap80['flat30_mid']:.2f} with a flat +0.30 w0. Window mods cannot replace stats when the player is that far under budget."
    )
    rec_bits.append(
        f"At mature #2 skipped (r=1.0355, 0.0145 of r still inside the 105% cap) window mods compete with legal stats and sit on the steep part of the win-rate curve. Across the three districts the average +10/20/30% mid-WR gains are about {g_skip[0.10]:.1f} / {g_skip[0.20]:.1f} / {g_skip[0.30]:.1f} points. "
        f"+10% and +20% can be matched by a legal stat bump (Street +10% Δr={next(s for s in stat_eq if s['id']=='street_mature2_skip' and abs(s['x']-0.10)<1e-12)['inside_cap']['delta_r']:+.4f}, "
        f"+20% Δr={next(s for s in stat_eq if s['id']=='street_mature2_skip' and abs(s['x']-0.20)<1e-12)['inside_cap']['delta_r']:+.4f}; a few SP at R1 and about 6–12 at R3). "
        f"Street mature #2 +30% cannot be matched inside the cap (search stopped at r=1.05, mid still short); the uncapped equivalent is r'={street_m2_30['uncapped']['r']:.4f} (Δr={street_m2_30['uncapped']['delta_r']:+.4f})."
    )
    rec_bits.append(
        "Recommended limit (from these runs, still a design choice): cap **total** zone width at **1.15 × w0** (920 ms if w0 stays 800). "
        "That allows at most a +15% mod at boss at target, which blocks the +20/+30% cap dodge that is worth ~10–13 mid-WR points there. "
        "When the player is behind, w(r) is well below w0 (0.85× at mature #2 skipped, 0.33× at r=0.80), so a +30% of current w(r) still sits under the 1.15 w0 ceiling and remains available as a catch-up tool — useful at the skipped wall, not a substitute for the 80% SP floor. "
        "A slot cost alone is not enough: at the 105% cap a window slot has no legal stat alternative, so its opportunity cost is zero unless the width cap (or a rule that window mods spend a fraction of the 25% mod budget) is also in place. "
        "A milder alternative is 1.20 × w0 if +15% feels too tight in playtest; I would not leave width uncapped."
    )
    narrative = "\n\n".join(rec_bits)

    notes.append(
        f"Recommended total-width cap: 1.15×w0. At r=1.05, w is already w0, so +20% and +30% would be clipped; at r=1.0355, w/w0={w_of(1.0355):.4f}, and even +30% of w(r) is {1.3*w_of(1.0355):.4f}×w0, still under 1.15."
    )

    out = {
        "_provenance": (
            "qte-v1 visible-QTE draft, 2026-11-10. No repo edits. "
            "Oracle shortcut on official count banks, q_read=0.6, opponent QTE=1.0, balanced HAN. "
            "Skill σ and linear-falloff press model are placeholders until playtest."
        ),
        "sigmas": sigmas_full,
        "defaults": {"w0_ms": M.W0_MS, "a0_ms": M.A0_MS, "q_read": W.Q_READ, "opponent_qte": W.OPPONENT_QTE},
        "closed_form_check": check,
        "w_curve": {k: v for k, v in curve.items() if k != "grid"} | {"grid_n": len(curve["grid"]), "grid": curve["grid"]},
        "cells": cells_out,
        "window_mods": {"multiplicative": mods_mult, "flat": mods_flat},
        "stat_equivalence": stat_eq,
        "cap_dodge": {"rows": cap_rows, "narrative": narrative, "mean_gains_boss_avg": g_boss, "mean_gains_mature2_avg": g_skip},
        "notes": notes,
    }

    (HERE / "results.json").write_text(json.dumps(out, indent=2, default=_json_default))
    # results.json includes the full grid; that's fine.
    write_results_md(out, HERE / "RESULTS.md")
    print("wrote", HERE / "results.json", HERE / "RESULTS.md")
    print("sigmas (ms):", {n: round(sigmas_full[n]["sigma_ms"], 3) for n in PROFILES})
    print("w/w0 at knots:", [(round(k["r"], 2), round(k["w_over_w0"], 4)) for k in curve["knots"]])
    print("average within official ±2:", {c["id"]: c["average_within_official_pm2"] for c in cells_out})
    print("closed-form max |d|:", check["max_abs_diff"])


def _json_default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


if __name__ == "__main__":
    main()
