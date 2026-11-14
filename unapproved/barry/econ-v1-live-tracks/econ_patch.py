"""Apply a live-track constant set to the econ-v1 draft modules (in memory). Draft only."""
from __future__ import annotations
import importlib, os, sys
import oracle


def apply(ladder_r=None, finale_r=None, finale_B=None, story_fill=None):
    """ladder_r: {district: 7 r}; finale_r: 4 r*; finale_B: 4 budgets (default the fixed econ-v1 budgets).
    Finale ceilings C = B x r and caps L follow (model.finale_ceilings / FINALE_L logic). Returns modules."""
    oracle.install()
    import model as M
    if ladder_r:
        for d, v in ladder_r.items():
            M.LADDER_R_C[d] = tuple(v)
        M.BOSS_R_C.update({d: v[6] for d, v in ladder_r.items()})
    if finale_B is not None:
        M.FINALE_B = tuple(finale_B)
    if finale_r is not None:
        M.FINALE_R_C = tuple(finale_r)
    M.FINALE_C = tuple(b * r for b, r in zip(M.FINALE_B, M.FINALE_R_C))
    M.FINALE_L = tuple(int(round(M.level_for_sp(c * 0.8 / M.K_CAP))) for c in M.FINALE_C)
    mods = {}
    for name in ("evaluate", "run_betting_levers", "run_finale_arc"):
        if name in sys.modules:
            mod = importlib.reload(sys.modules[name])
        else:
            mod = importlib.import_module(name)
        mods[name] = mod
    hw = os.environ.get("HARD_WANGAN")
    if hw:   # Austin 2026-11-13: bosses on the hardest track per district -> Wangan 30-turn hard cell
        E = mods["evaluate"]; base = E.wr_cell
        def wr_cell(pr, r, T, district, allow_interp=True, _b=base):
            out = _b(pr, r, T, district, allow_interp)
            if district == "wangan" and T == 30:
                w = oracle.track_wr(pr, r, T, hw)
                cell = dict(win=round(w, 1), r_used=float(r), exact=False, src="live-tracks")
                out["S1_CW"] = dict(cell); out["S1_CCW"] = dict(cell)   # reuse econ-v1 hard-cell slots
            return out
        for m in mods.values():
            if hasattr(m, "wr_cell"):
                m.wr_cell = wr_cell
    A = mods["run_finale_arc"]
    A.CAPS = (M.CAP_L[2],) + tuple(M.FINALE_L)
    for i, st in enumerate(A.STEPS):
        st["enter"], st["cap"] = A.CAPS[i], A.CAPS[i + 1]
    A.GAP_XP = [A.xp_range(A.CAPS[i], A.CAPS[i + 1]) for i in range(4)]
    if story_fill is not None:
        mods["run_betting_levers"].XP = mods["run_betting_levers"].XP.__class__(**{**mods["run_betting_levers"].XP.__dict__, "story_fill": tuple(story_fill)})
    return M, mods
