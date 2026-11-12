"""Oracle shortcut: precomputed clash-count banks, explicit qhat, no knot_window.

Faithful to lines-v1 / flib.wr / lib.wr_counts, except qhat is passed in
directly (raw QTE score x HAN) instead of being q_time * knot_window(r).

Counts (q_read=0.6, N=4000 per bank, seeds 20261113-15, lengths 10/20/30):
  touge  — final-v1/counts_n4000.npz, masked to Touge tracks
  street — lines-v1/counts_S_N90=SSA.npz
  wangan — lines-v1/counts_W_SW=IR=AAD.npz

Balanced builds: HAN modifier = 1, so q_eff = raw score. Opponent QTE = 1.0.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

FINAL = Path("/workspace/barry-drafts/final-v1")
LINES = Path("/workspace/barry-drafts/lines-v1")
sys.path.insert(0, str(FINAL))
import equations_v2 as E2  # noqa: E402

SEEDS = (20261113, 20261114, 20261115)
LENGTHS = (10, 20, 30)
KAPPA = {10: 1.55, 20: 1.35, 30: 1.20}
Q_READ = 0.6
OPPONENT_QTE = 1.0
K0 = E2.K()

_PHI: dict[float, np.ndarray] = {}


def phi(q: float) -> np.ndarray:
    q = float(min(max(q, 0.0), 1.0))
    key = round(q, 8)
    if key not in _PHI:
        _PHI[key] = np.array(
            [float(E2.clash_payoff(np.array(v), np.array(q), K0)) for v in (1, 0, -1)]
        )
    return _PHI[key]


def _load_raw(path: Path) -> dict[str, np.ndarray]:
    return dict(np.load(path))


def touge_counts() -> dict[tuple[int, int], np.ndarray]:
    raw = _load_raw(FINAL / "counts_n4000.npz")
    out = {}
    for sd in SEEDS:
        for L in LENGTHS:
            cnt = raw[f"{sd}_{Q_READ}_{L}"]
            mask = (np.arange(len(cnt)) % 15) // 5 == 0
            out[(sd, L)] = cnt[mask]
    return out


def _district_npz(path: Path) -> dict[tuple[int, int], np.ndarray]:
    raw = _load_raw(path)
    out = {}
    for sd in SEEDS:
        for L in LENGTHS:
            out[(sd, L)] = raw[f"{sd}_{Q_READ}_{L}"]
    return out


def load_banks() -> dict[str, dict[tuple[int, int], np.ndarray]]:
    return {
        "touge": touge_counts(),
        "wangan": _district_npz(LINES / "counts_W_SW=IR=AAD.npz"),
        "street": _district_npz(LINES / "counts_S_N90=SSA.npz"),
    }


def wr_one(cnt: np.ndarray, r: float, qhat: float, L: int) -> float:
    """Win rate in percent, counting ties as 0.5, one (seed, length) bank."""
    gp = (r ** KAPPA[L]) * (cnt @ phi(qhat))
    go = cnt[:, ::-1] @ phi(OPPONENT_QTE)
    return 100.0 * float(np.mean((gp > go) + 0.5 * (gp == go)))


def wr_cell(banks: dict, r: float, qhat: float, districts: list[str] | None = None) -> dict:
    """min/max over seeds x lengths, plus pooled (equal-weight mean of districts).

    Returns unrounded values and official-style 1-decimal bands.
    """
    districts = districts or ["touge", "wangan", "street"]
    per: dict[str, dict[tuple[int, int], float]] = {}
    out_d: dict[str, dict] = {}
    for d in districts:
        vals = {}
        for sd in SEEDS:
            for L in LENGTHS:
                vals[(sd, L)] = wr_one(banks[d][(sd, L)], r, qhat, L)
        series = list(vals.values())
        out_d[d] = {
            "values": series,
            "min": min(series),
            "max": max(series),
            "mid": 0.5 * (min(series) + max(series)),
            "band_1dp": [round(min(series), 1), round(max(series), 1)],
        }
        per[d] = vals
    keys = [(sd, L) for sd in SEEDS for L in LENGTHS]
    pooled = [float(np.mean([per[d][k] for d in districts])) for k in keys]
    out_d["pooled"] = {
        "values": pooled,
        "min": min(pooled),
        "max": max(pooled),
        "mid": 0.5 * (min(pooled) + max(pooled)),
        "band_1dp": [round(min(pooled), 1), round(max(pooled), 1)],
    }
    return {"r": r, "qhat": qhat, "districts": out_d}
