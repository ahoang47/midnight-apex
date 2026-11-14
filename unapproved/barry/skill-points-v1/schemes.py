"""Whole-number skill-point schemes (draft, Barry 2026-11-14). Each scheme gives grant[L] = whole points earned on
reaching level L (L = 1..115) on top of SP_START = 240 at L0; SP_int(L) = 240 + sum(grant[1..L])."""
import sys, os, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "sim"))
from velocity_shift import equations as E
LMAX = 115
CAPS = (12, 29, 46, 64, 79, 94, 115)
SP = [E.sp_at_level(L) for L in range(LMAX + 1)]

def table(grants, scale=1):
    t = [E.SP_START * scale]
    for L in range(1, LMAX + 1):
        t.append(t[-1] + grants[L])
    return [x / scale for x in t]

def s1_curve():
    """S1: grant = round(SP(L)) - round(SP(L-1)); varies 1-5 per level, follows the live curve to +-0.5 SP."""
    return [0] + [round(SP[L]) - round(SP[L - 1]) for L in range(1, LMAX + 1)]

def s2_band():
    """S2: flat N per level inside each cap band (N = floor of the band's live SP gain / its levels), plus a one-off
    milestone grant on reaching each cap that lands the cap exactly on round(SP(cap))."""
    g = [0] * (LMAX + 1); prev = 0; tgt_prev = round(SP[0]); info = []
    for c in CAPS:
        gap = round(SP[c]) - tgt_prev; n = (c - prev); N = gap // n
        for L in range(prev + 1, c + 1):
            g[L] = N
        g[c] += gap - N * n; info.append((c, N, gap - N * n))
        prev, tgt_prev = c, round(SP[c])
    return g, info

def s2_steps():
    """S2: flat N per level that steps up 2 -> 3 -> 4 -> 5 at fixed levels; breakpoints fitted to the live SP at
    the 7 caps (min of max abs error, then sum abs error)."""
    best = None
    for b3 in range(13, 60):
        for b4 in range(b3 + 1, 100):
            for b5 in range(b4 + 1, 116):
                g = [0] + [2 if L < b3 else 3 if L < b4 else 4 if L < b5 else 5 for L in range(1, LMAX + 1)]
                t = table(g); err = [t[c] - SP[c] for c in CAPS]
                key = (max(abs(e) for e in err), sum(abs(e) for e in err))
                if best is None or key < best[0]:
                    best = (key, (b3, b4, b5), g)
    return best[2], best[1]

def s3_tenths():
    """S3: S1 at x10 resolution: grant = round(10 SP(L)) - round(10 SP(L-1)) points of 0.1 SP each (19-47 per level)."""
    return [0] + [round(10 * SP[L]) - round(10 * SP[L - 1]) for L in range(1, LMAX + 1)]

SCHEMES = {}
g = s1_curve(); SCHEMES["S1_curve"] = dict(grants=g, scale=1, table=table(g))
g, bp = s2_band(); SCHEMES["S2_band"] = dict(grants=g, scale=1, table=table(g), breakpoints=bp)
REJECTED = {}
def rejected():
    g, bp = s2_steps(); return dict(grants=g, scale=1, table=table(g), breakpoints=bp)
g = s3_tenths(); SCHEMES["S3_x10"] = dict(grants=g, scale=10, table=table(g, 10))

if __name__ == "__main__":
    REJECTED["S2alt_steps"] = rejected()
    for k, s in list(SCHEMES.items()) + list(REJECTED.items()):
        g = s["grants"][1:]; t = s["table"]
        print(k, s.get("breakpoints", ""), "grant range", min(g), max(g), "per level;",
              "mix", {v: g.count(v) for v in sorted(set(g))} if s["scale"] == 1 else "")
        print("   cap SP live/int/err%:", [(c, round(SP[c], 2), round(t[c], 1), round(100 * (t[c] - SP[c]) / SP[c], 3)) for c in CAPS])
        print("   max abs err any level", round(max(abs(t[L] - SP[L]) for L in range(LMAX + 1)), 3), "SP")
