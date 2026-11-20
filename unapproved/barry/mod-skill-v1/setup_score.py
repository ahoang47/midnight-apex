"""SETUP STUDY scorecard (Barry, 2026-11-19): applies the pre-registered G1-G5 thresholds (SETUP-STUDY.md section 1) to
setup_study.json (engine) and journey_setups.json (G2b). Retuned rows (M7r, M13r) have the M20 floors by construction, so their
stat criteria reuse the M20 cells (same points, same stat-locked crews); only G2b differs. -> setup_score.json"""
import json, os
import setup_study as S
HERE = os.path.dirname(os.path.abspath(__file__))
C = {(i, j, p, pts): w for i, j, p, pts, w in json.load(open(os.path.join(HERE, "setup_study.json")))["cells"]}
G2B = json.load(open(os.path.join(HERE, "journey_setups.json")))["g2b"]


def w(i, j, p, pts): return C[S.key(i, j, p, pts)]


def score(name, c):
    M = int(name[1:].rstrip("r")); Ms = 20 if name.endswith("r") else M
    fl, mx = S.builds(Ms, c); rows = {}
    g1a = [w(i, 6, "80/80", fl[i][6]) for i in range(3)]
    g1b = [round(sum(100 / max(w(i, j, "80/80", fl[i][j]), 0.01) - 1 for j in range(7)), 2) for i in range(3)]
    g2a = min(w(i, j, "60/60", mx[i][j]) for i in range(3) for j in range(7))
    g2a_at = min(((w(i, j, "60/60", mx[i][j]), S.D[i] + " " + S.RUNGS[j]) for i in range(3) for j in range(7)))[1]
    curves = [[w(i, j, "80/80", fl[i][j]) for j in range(7)] for i in range(3)]
    mono = all(curves[i][j + 1] <= curves[i][j] + 1.0 for i in range(3) for j in range(6))
    drop = min(curves[i][0] - curves[i][6] for i in range(3))
    g3b = [round(w(i, 6, "80/80", fl[i][6]) - w(i, 6, "60/60", mx[i][6]), 2) for i in range(3)]
    g4a = min(min(cv) for cv in curves)
    g4b = [w(i, 6, "60/60", fl[i][6]) for i in range(3)]
    g5 = [w(i, 6, "80/80", mx[i][6]) for i in range(3)]
    j2 = G2B[f"{name}|{c}"]
    P = dict(G1a=all(40 <= x <= 65 for x in g1a), G1b=all(1.5 <= x <= 4.0 for x in g1b), G2a=g2a >= 30,
             G2b=j2["attempts"] <= 60 and j2["stuck"] == 0, G3a=mono and drop >= 30, G3b=min(g3b) >= 10,
             G4a=g4a >= 40, G4b=max(g4b) <= 10, G5=(c != "none") and max(g5) <= 95)
    V = dict(G1a=g1a, G1b=g1b, G2a=[g2a, g2a_at], G2b=[j2["attempts"], j2["stuck"], j2["nm_wins"]], G3a=[mono, round(drop, 2)],
             G3b=g3b, G4a=g4a, G4b=g4b, G5=g5)
    return dict(setup=f"S1 {name} cap {c}", passes=sum(P.values()), P=P, V=V, curves=curves,
                floors_boss=[f[6] for f in fl], max_boss=[m[6] for m in mx])


if __name__ == "__main__":
    out = [score(n, c) for n in ("M7", "M10", "M13", "M20", "M7r", "M13r") for c in ("none", "8", "12", "15")]
    json.dump(out, open(os.path.join(HERE, "setup_score.json"), "w"), indent=1)
    for o in out:
        print(o["setup"], o["passes"], " ".join(k + ("+" if v else "-") for k, v in o["P"].items()), json.dumps(o["V"]))
    s2 = json.load(open(os.path.join(HERE, "setup_study.json")))["s2"]
    for x in s2: print(x)
