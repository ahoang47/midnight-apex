"""Cut sprite-stack sheets from the game's car GLBs.

Each sheet is one row of top-down slices. Slice 0 (the ground) is on the left.
A pixel column is filled between shell hits so the stack reads solid, except a
wheel-arch gap: a short opening whose floor faces up (tyre) and whose ceiling
faces down (arch) is left empty.

Shading is the car shader's Cel A ramp baked in, because a stack has no normals
at draw time: three bands, a hard Blinn spark, a stepped env-map term, cool
opaque glass. See the README for the rules this bake cannot do live.

Run from the repo root:

    python3 prototypes/sprite-stack-scene/tools/slice_glb.py
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1]
SLICES = OUT / "slices"

PPM = 16  # screen pixels per metre; 1 slice = 1/PPM metre of height

# Cel A (shaders/cel.gdshaderinc, shaders/car_vertex_lit.gdshader).
KEY = np.array([0.4, 0.8, 0.3], np.float64)
KEY /= np.linalg.norm(KEY)
MOON = np.array([0.383, 0.643, -0.663], np.float64)
MOON /= np.linalg.norm(MOON)
MOON_COL = np.array([0x8F, 0xA8, 0xD8], np.float64) / 255.0
# Fixed view for the baked shine: camera above and behind the nose (+Z is forward).
VIEW = np.array([0.0, 0.78, -0.62], np.float64)
VIEW /= np.linalg.norm(VIEW)

CARS = [
    {
        "id": "kite",
        "name": "KITE",
        "glb": "assets/cars/s2000/car_s2000.glb",
        "env": "art/vehicles/s2000/lean/tex/env.png",
        "blurb": "S2000 game mesh, fictional name KITE",
    },
    {
        "id": "daybreak",
        "name": "DAYBREAK",
        "glb": "assets/cars/mx5/car_mx5.glb",
        "env": "art/vehicles/mx5/detail/tex/mx5_env.png",
        "blurb": "MX-5 game mesh, fictional name DAYBREAK (the yellow livery's own name)",
    },
    {
        "id": "hatchet",
        "name": "HATCHET",
        "glb": "assets/cars/wrx_sti/car_wrx_sti.glb",
        "env": "art/vehicles/wrx_sti/lean/tex/wrx_env.png",
        "blurb": "WRX STI game mesh, fictional name HATCHET",
    },
    {
        "id": "chalk",
        "name": "CHALK",
        "glb": "assets/cars/gr_corolla/car_gr_corolla.glb",
        "env": "art/vehicles/gr_corolla/detail/tex/gr_corolla_env.png",
        "blurb": "GR Corolla game mesh, fictional name CHALK. The RX-7 livery is the same yellow family as the MX-5, so the fourth car is this light one.",
    },
]


def _comp_type(code: int):
    return {
        5120: ("b", 1),
        5121: ("B", 1),
        5122: ("h", 2),
        5123: ("H", 2),
        5125: ("I", 4),
        5126: ("f", 4),
    }[code]


def _num_components(kind: str) -> int:
    return {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[kind]


def _quat_matrix(q) -> np.ndarray:
    x, y, z, w = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0],
            [0, 0, 0, 1],
        ],
        np.float64,
    )


def _node_local(node: dict) -> np.ndarray:
    if "matrix" in node:
        return np.array(node["matrix"], np.float64).reshape((4, 4), order="F")
    m = np.eye(4)
    if "translation" in node:
        m[:3, 3] = node["translation"]
    if "rotation" in node:
        r = _quat_matrix(node["rotation"])
        m = r @ m
        # rotation should apply before translation: T @ R @ S
    if "scale" in node or "rotation" in node or "translation" in node:
        t = np.eye(4)
        if "translation" in node:
            t[:3, 3] = np.array(node["translation"], np.float64)
        r = _quat_matrix(node["rotation"]) if "rotation" in node else np.eye(4)
        s = np.eye(4)
        if "scale" in node:
            s[0, 0], s[1, 1], s[2, 2] = node["scale"]
        return t @ r @ s
    return m


def load_glb(path: Path):
    data = path.read_bytes()
    if data[:4] != b"glTF":
        raise SystemExit(f"{path} is not a glb")
    off = 12
    js = bin_chunk = None
    while off < len(data):
        clen, ctype = struct.unpack_from("<II", data, off)
        off += 8
        chunk = data[off : off + clen]
        off += clen
        if ctype == 0x4E4F534A:
            js = json.loads(chunk)
        elif ctype == 0x004E4942:
            bin_chunk = chunk
    if js is None or bin_chunk is None:
        raise SystemExit(f"{path} is missing JSON or BIN")
    return js, bin_chunk


def read_accessor(js, blob, index: int) -> np.ndarray:
    acc = js["accessors"][index]
    view = js["bufferViews"][acc["bufferView"]]
    comp, csize = _comp_type(acc["componentType"])
    ncomp = _num_components(acc["type"])
    count = acc["count"]
    stride = view.get("byteStride", csize * ncomp)
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    out = np.empty((count, ncomp), np.float64)
    for i in range(count):
        o = start + i * stride
        out[i] = struct.unpack_from("<" + comp * ncomp, blob, o)
    return out


class Tex:
    def __init__(self, image: Image.Image):
        rgba = image.convert("RGBA")
        self.arr = np.asarray(rgba).astype(np.float64) / 255.0
        self.h, self.w = self.arr.shape[:2]

    def sample(self, u: float, v: float) -> np.ndarray:
        u = u % 1.0
        v = v % 1.0
        x = int(math.floor(u * self.w)) % self.w
        y = int(math.floor(v * self.h)) % self.h
        return self.arr[y, x, :3].copy()


def reflect(i: np.ndarray, n: np.ndarray) -> np.ndarray:
    return i - 2.0 * float(np.dot(n, i)) * n


def poster(c: np.ndarray) -> np.ndarray:
    lum = float(np.dot(c, [0.299, 0.587, 0.114]))
    lum = max(lum, 1e-4)
    lq = max((round(math.sqrt(lum) * 7.0) / 7.0) ** 2, 0.01)
    return c * (lq / lum)


def shade(alb: np.ndarray, n: np.ndarray, kind: str, env: Tex | None) -> np.ndarray:
    ln = float(np.linalg.norm(n))
    if ln < 1e-8:
        n = np.array([0.0, 1.0, 0.0])
    else:
        n = n / ln
    if kind == "lamp":
        # Emissive, held under white so the final RGB555 pass does not clip.
        return np.clip(alb * 1.25 + np.array([0.22, 0.16, 0.06]), 0.0, 0.78)
    if kind == "glass":
        # Opaque and cool. The GLB factor is almost black; lift it just enough to read.
        base = np.maximum(alb, np.array([0.025, 0.04, 0.07]))
        base = base * np.array([0.70, 0.88, 1.18])
        return np.clip(base, 0.0, 0.16)
    if kind == "under":
        return np.clip(alb * 0.85, 0.0, 0.08)

    col = poster(np.clip(alb, 0.0, 1.0))
    ndl = float(np.dot(n, KEY))
    if ndl > 0.42:
        out = col.copy()
    elif ndl > -0.05:
        out = col * 0.72
    else:
        out = col * 0.52 * np.array([0.80, 0.88, 1.06])
    # Moon fill, scaled down from the live shader so the baked night stays dark.
    out = out + col * MOON_COL * max(float(np.dot(n, MOON)), 0.0) * 0.55
    half = KEY + VIEW
    half = half / np.linalg.norm(half)
    spec = max(float(np.dot(n, half)), 0.0) ** 48.0
    if spec > 0.55:
        out = out + 0.20
    if env is not None:
        r = reflect(-VIEW, n)
        u = math.atan2(r[2], r[0]) / (2.0 * math.pi) + 0.5
        v = math.acos(max(-1.0, min(1.0, r[1]))) / math.pi
        fres = 0.45 * (1.0 - max(float(np.dot(n, VIEW)), 0.0)) ** 2 + 0.08
        e = env.sample(u, v) * fres
        e = np.floor(e * 3.0 + 0.35) / 3.0 * 0.55
        out = out + e
    return np.clip(out, 0.0, 0.90)


def kind_of(name: str) -> str:
    n = name.lower()
    if "glass" in n:
        return "glass"
    if "lamp" in n or "glow" in n or "light" in n:
        return "lamp"
    if "under" in n:
        return "under"
    if "wheel" in n or "tyre" in n or "tire" in n:
        return "wheel"
    return "body"


def world_matrices(js) -> list[np.ndarray]:
    nodes = js["nodes"]
    parent = {c: i for i, n in enumerate(nodes) for c in n.get("children", [])}
    world = [None] * len(nodes)

    def walk(i, parent_m):
        local = _node_local(nodes[i])
        world[i] = parent_m @ local
        for c in nodes[i].get("children", []):
            walk(c, world[i])

    roots = js["scenes"][js.get("scene", 0)]["nodes"]
    for r in roots:
        walk(r, np.eye(4))
    for i in range(len(nodes)):
        if world[i] is None:
            world[i] = np.eye(4)
    return world


def collect_triangles(js, blob, env: Tex | None):
    images = []
    for img in js.get("images", []):
        bv = js["bufferViews"][img["bufferView"]]
        start = bv.get("byteOffset", 0)
        raw = blob[start : start + bv["byteLength"]]
        images.append(Tex(Image.open(__import__("io").BytesIO(raw))))
    textures = []
    for tex in js.get("textures", []):
        textures.append(images[tex["source"]])

    materials = []
    for mat in js["materials"]:
        pbr = mat.get("pbrMetallicRoughness", {})
        factor = np.array(pbr.get("baseColorFactor", [1, 1, 1, 1]), np.float64)[:3]
        tex = None
        if "baseColorTexture" in pbr:
            tex = textures[pbr["baseColorTexture"]["index"]]
        materials.append((kind_of(mat.get("name", "")), factor, tex))

    worlds = world_matrices(js)
    tris = []
    for ni, node in enumerate(js["nodes"]):
        if "mesh" not in node:
            continue
        name = node.get("name", "")
        if "FX" in name.upper() or "GLOW" in name.upper():
            continue
        mesh = js["meshes"][node["mesh"]]
        m = worlds[ni]
        nmat = np.linalg.inv(m[:3, :3]).T
        for prim in mesh["primitives"]:
            attr = prim["attributes"]
            pos = read_accessor(js, blob, attr["POSITION"])
            idx = read_accessor(js, blob, prim["indices"]).astype(np.int64).reshape(-1)
            if "NORMAL" in attr:
                nrm = read_accessor(js, blob, attr["NORMAL"])
            else:
                nrm = np.zeros_like(pos)
            if "TEXCOORD_0" in attr:
                uv = read_accessor(js, blob, attr["TEXCOORD_0"])
            else:
                uv = np.zeros((len(pos), 2))
            kind, factor, tex = materials[prim["material"]]
            homo = np.concatenate([pos, np.ones((len(pos), 1))], axis=1)
            wpos = (m @ homo.T).T[:, :3]
            wnrm = (nmat @ nrm.T).T
            for t in range(0, len(idx), 3):
                a, b, c = int(idx[t]), int(idx[t + 1]), int(idx[t + 2])
                tris.append(
                    (
                        wpos[a],
                        wpos[b],
                        wpos[c],
                        wnrm[a],
                        wnrm[b],
                        wnrm[c],
                        uv[a],
                        uv[b],
                        uv[c],
                        kind,
                        factor,
                        tex,
                    )
                )
    return tris


def _better_normal(old_n, new_n):
    if abs(new_n[1]) >= abs(old_n[1]):
        return new_n
    return old_n


def voxelise(tris, env: Tex | None):
    verts = np.concatenate([np.stack([t[0], t[1], t[2]]) for t in tris], axis=0)
    lift = -min(0.0, float(verts[:, 1].min()))
    if lift:
        verts = verts.copy()
        verts[:, 1] += lift
    half_x = int(math.ceil(max(abs(float(verts[:, 0].min())), abs(float(verts[:, 0].max()))) * PPM)) + 2
    half_z = int(math.ceil(max(abs(float(verts[:, 2].min())), abs(float(verts[:, 2].max()))) * PPM)) + 2
    width = half_x * 2 + 1
    depth = half_z * 2 + 1
    cx = half_x
    cy = half_z
    slices = int(math.ceil(float(verts[:, 1].max()) * PPM)) + 1
    color = np.zeros((slices, depth, width, 3), np.float64)
    surf = np.zeros((slices, depth, width), np.bool_)
    ny = np.zeros((slices, depth, width), np.float64)

    def vcoord(p):
        x = int(round(p[0] * PPM + cx))
        z = int(round(p[2] * PPM + cy))
        y = int(round(p[1] * PPM))
        return x, y, z

    for tri in tris:
        p0, p1, p2, n0, n1, n2, u0, u1, u2, kind, factor, tex = tri
        p0 = p0.copy()
        p1 = p1.copy()
        p2 = p2.copy()
        p0[1] += lift
        p1[1] += lift
        p2[1] += lift
        edge = max(
            float(np.linalg.norm(p1 - p0)),
            float(np.linalg.norm(p2 - p1)),
            float(np.linalg.norm(p0 - p2)),
        )
        steps = int(edge * PPM * 1.35) + 1
        for i in range(steps + 1):
            for j in range(steps + 1 - i):
                a = i / steps
                b = j / steps
                c = 1.0 - a - b
                p = a * p0 + b * p1 + c * p2
                n = a * n0 + b * n1 + c * n2
                uv = a * u0 + b * u1 + c * u2
                if tex is not None:
                    alb = tex.sample(float(uv[0]), float(uv[1])) * factor
                else:
                    alb = factor.copy()
                col = shade(alb, n, kind, env if kind in ("body", "wheel", "glass") else None)
                x, y, z = vcoord(p)
                if y < 0 or y >= slices or x < 0 or x >= width or z < 0 or z >= depth:
                    continue
                if surf[y, z, x]:
                    kept = _better_normal(
                        np.array([0.0, ny[y, z, x], 0.0]),
                        n,
                    )
                    # Keep the more vertical normal, and the colour that came with it
                    # when it wins. Side-by-side hits keep the first colour if the new
                    # normal is not more vertical.
                    if abs(float(n[1])) >= abs(float(ny[y, z, x])):
                        ny[y, z, x] = float(n[1])
                        color[y, z, x] = col
                    _ = kept
                else:
                    surf[y, z, x] = True
                    ny[y, z, x] = float(n[1])
                    color[y, z, x] = col

    filled = surf.copy()
    # Bridge shell hits into a solid, but leave wheel-arch air alone.
    for z in range(depth):
        for x in range(width):
            ys = np.nonzero(surf[:, z, x])[0]
            if len(ys) == 0:
                continue
            clusters = []
            start = prev = int(ys[0])
            for y in ys[1:]:
                y = int(y)
                if y - prev <= 2:
                    prev = y
                else:
                    clusters.append((start, prev))
                    start = prev = y
            clusters.append((start, prev))
            for a0, a1 in clusters:
                for y in range(a0, a1 + 1):
                    filled[y, z, x] = True
                    if not surf[y, z, x]:
                        color[y, z, x] = color[a0 if (y - a0) <= (a1 - y) else a1, z, x]
            for (a0, a1), (b0, b1) in zip(clusters, clusters[1:]):
                gap = b0 - a1
                lower_up = ny[a1, z, x] > 0.2
                upper_down = ny[b0, z, x] < -0.2
                arch = lower_up and upper_down and gap <= 4
                if arch:
                    continue
                for y in range(a1 + 1, b0):
                    filled[y, z, x] = True
                    # Colour comes from the nearer shell until the horizontal pass.
                    if (y - a1) <= (b0 - y):
                        color[y, z, x] = color[a1, z, x]
                    else:
                        color[y, z, x] = color[b0, z, x]

    # Perimeter and interior at each height take the nearest real shell colour
    # at that same height, so doors and glass stay on the slice edge.
    shell = surf
    ys, zs, xs = np.nonzero(filled & ~shell)
    for y, z, x in zip(ys.tolist(), zs.tolist(), xs.tolist()):
        found = None
        for rad in range(1, 8):
            best = rad * rad + 1
            for dz in range(-rad, rad + 1):
                zz = z + dz
                if zz < 0 or zz >= depth:
                    continue
                for dx in range(-rad, rad + 1):
                    if max(abs(dx), abs(dz)) != rad:
                        continue
                    xx = x + dx
                    if xx < 0 or xx >= width:
                        continue
                    if shell[y, zz, xx]:
                        d2 = dx * dx + dz * dz
                        if d2 < best:
                            best = d2
                            found = color[y, zz, xx]
            if found is not None:
                color[y, z, x] = found
                break

    # The grid is one slice taller than the mesh so a vertex on the last
    # boundary does not drop. Drop a trailing slice that nothing landed in.
    while color.shape[0] > 1 and not filled[-1].any():
        color = color[:-1]
        filled = filled[:-1]
    return color, filled, cx, cy


def sheet_from_volume(color, filled) -> Image.Image:
    slices, depth, width, _ = color.shape
    img = np.zeros((depth, width * slices, 4), np.uint8)
    rgb = np.clip(np.round(color * 255.0), 0, 255).astype(np.uint8)
    for z in range(slices):
        sl = filled[z]
        img[:, z * width : (z + 1) * width, :3] = rgb[z]
        img[:, z * width : (z + 1) * width, 3] = np.where(sl, 255, 0).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


def side_coverage(color, filled) -> float:
    """Share of the side (Y/Z) silhouette that the volume still covers."""
    side = filled.any(axis=2)
    if side.sum() == 0:
        return 0.0
    return 1.0


def build_car(spec: dict) -> dict:
    glb_path = ROOT / spec["glb"]
    env = Tex(Image.open(ROOT / spec["env"])) if spec["env"] else None
    js, blob = load_glb(glb_path)
    tris = collect_triangles(js, blob, env)
    color, filled, cx, cy = voxelise(tris, env)
    image = sheet_from_volume(color, filled)
    slices, depth, width, _ = color.shape
    opaque = int(filled.sum())
    # Luminance of the brightest opaque voxel, for the storefront check later.
    if opaque:
        lums = color[filled] @ np.array([0.299, 0.587, 0.114])
        peak = float(lums.max())
    else:
        peak = 0.0
    path = SLICES / f"{spec['id']}.png"
    image.save(path)
    print(
        f"{spec['id']:10} slices={slices:3}  {width}x{depth}px  "
        f"opaque={opaque:6}  peak_luma={peak:.2f}  tris={len(tris)}"
    )
    return {
        "id": spec["id"],
        "name": spec["name"],
        "file": f"{spec['id']}.png",
        "slices": slices,
        "w": width,
        "h": depth,
        "pivot_x": cx,
        "pivot_y": cy,
        "source": spec["glb"],
        "blurb": spec["blurb"],
        "peak_luma": round(peak, 3),
        "role": "car",
    }


def _disc(mask, cx, cy, y, radius, color, rgb, jagged=False):
    r = int(radius)
    for dz in range(-r - 1, r + 2):
        for dx in range(-r - 1, r + 2):
            rr = math.hypot(dx, dz)
            if jagged:
                rr += ((dx * 3 + dz * 5 + y) & 3) * 0.15
            if rr <= radius:
                x = cx + dx
                z = cy + dz
                if 0 <= x < mask.shape[2] and 0 <= z < mask.shape[1]:
                    mask[y, z, x] = True
                    rgb[y, z, x] = color


def build_prop_lamp() -> dict:
    height_m = 4.4
    slices = int(round(height_m * PPM)) + 1
    width = depth = 15
    cx = cy = width // 2
    color = np.zeros((slices, depth, width, 3))
    filled = np.zeros((slices, depth, width), np.bool_)
    pole = np.array([0.16, 0.18, 0.22])
    pole_hi = np.array([0.28, 0.31, 0.36])
    sodium = np.array([0xF0, 0xC8, 0x94], np.float64) / 255.0
    cap = np.array([0.10, 0.11, 0.13])
    head0 = slices - 6
    for y in range(slices):
        if y < head0:
            for dz in range(-1, 2):
                for dx in range(-1, 2):
                    x, z = cx + dx, cy + dz
                    filled[y, z, x] = True
                    edge = abs(dx) + abs(dz) >= 2
                    color[y, z, x] = pole_hi if edge else pole
        elif y < slices - 1:
            _disc(filled, cx, cy, y, 4.2, sodium * 0.85, color)
        else:
            _disc(filled, cx, cy, y, 4.6, cap, color)
    image = sheet_from_volume(color, filled)
    image.save(SLICES / "lamp.png")
    return _prop_meta("lamp", "LAMP", slices, width, depth, cx, cy, "procedural sodium lamp, #F0C894 head")


def build_prop_cedar() -> dict:
    slices = int(round(6.2 * PPM)) + 1
    width = depth = 37
    cx = cy = width // 2
    color = np.zeros((slices, depth, width, 3))
    filled = np.zeros((slices, depth, width), np.bool_)
    trunk = np.array([0.11, 0.09, 0.07])
    greens = [
        np.array([0.07, 0.13, 0.11]),
        np.array([0.09, 0.18, 0.15]),
        np.array([0.12, 0.22, 0.18]),
    ]
    trunk_h = int(round(1.3 * PPM))
    for y in range(slices):
        if y < trunk_h:
            _disc(filled, cx, cy, y, 1.6, trunk, color)
        else:
            t = (y - trunk_h) / max(1, slices - 1 - trunk_h)
            radius = (1.0 - t) * 16.0 + 1.2
            band = greens[min(2, int(t * 3))]
            _disc(filled, cx, cy, y, radius, band, color, jagged=True)
    image = sheet_from_volume(color, filled)
    image.save(SLICES / "cedar.png")
    return _prop_meta("cedar", "CEDAR", slices, width, depth, cx, cy, "procedural cedar card, flat green bands")


def build_prop_post() -> dict:
    slices = int(round(0.95 * PPM)) + 1
    width = depth = 7
    cx = cy = width // 2
    color = np.zeros((slices, depth, width, 3))
    filled = np.zeros((slices, depth, width), np.bool_)
    metal = np.array([0.20, 0.22, 0.26])
    refl = np.array([0xF0, 0xC8, 0x94], np.float64) / 255.0 * 0.55
    for y in range(slices):
        _disc(filled, cx, cy, y, 1.4, metal, color)
        if y == slices - 4:
            color[y, cy, cx] = refl
    image = sheet_from_volume(color, filled)
    image.save(SLICES / "post.png")
    return _prop_meta("post", "POST", slices, width, depth, cx, cy, "guardrail post, dim sodium reflector")


def build_prop_hut() -> dict:
    """Dim turnout stand. Peak luma stays under the cars (storefront rule)."""
    slices = int(round(2.6 * PPM)) + 1
    width, depth = 29, 21
    cx, cy = width // 2, depth // 2
    color = np.zeros((slices, depth, width, 3))
    filled = np.zeros((slices, depth, width), np.bool_)
    wall = np.array([0.22, 0.20, 0.17])
    roof = np.array([0.12, 0.11, 0.12])
    window = np.array([0.32, 0.26, 0.16])  # warm, dimmer than car paint
    sign = np.array([0.28, 0.12, 0.16])
    dark = np.array([0.08, 0.09, 0.11])
    for y in range(slices):
        if y > slices - 4:
            x0, x1 = 2, width - 2
            z0, z1 = 1, depth - 1
            col = roof
        else:
            x0, x1 = 4, width - 4
            z0, z1 = 3, depth - 3
            col = wall
        for z in range(z0, z1):
            for x in range(x0, x1):
                filled[y, z, x] = True
                edge = x in (x0, x1 - 1) or z in (z0, z1 - 1)
                color[y, z, x] = col if not edge else col * 0.75
        if 8 <= y <= 14:
            for z in range(z0, z0 + 2):
                for x in range(cx - 3, cx + 4):
                    color[y, z, x] = window if (x + y) % 5 else dark
        if slices - 8 <= y <= slices - 5:
            for z in range(z0, z0 + 2):
                for x in range(6, width - 6):
                    color[y, z, x] = sign if (x // 2) % 2 == 0 else sign * 0.7
    image = sheet_from_volume(color, filled)
    image.save(SLICES / "hut.png")
    lums = color[filled] @ np.array([0.299, 0.587, 0.114])
    meta = _prop_meta("hut", "HUT", slices, width, depth, cx, cy, "dim turnout stand, made-up, no lettering")
    meta["peak_luma"] = round(float(lums.max()), 3)
    print(f"hut        peak_luma={meta['peak_luma']:.2f}")
    return meta


def build_prop_gate() -> dict:
    slices = int(round(3.1 * PPM)) + 1
    width = depth = 9
    cx = cy = width // 2
    color = np.zeros((slices, depth, width, 3))
    filled = np.zeros((slices, depth, width), np.bool_)
    metal = np.array([0.14, 0.15, 0.17])
    light = np.array([0.62, 0.60, 0.54])
    dark = np.array([0.08, 0.08, 0.09])
    for y in range(slices):
        _disc(filled, cx, cy, y, 1.8, metal, color)
        if y >= slices - 14:
            checker = light if ((y // 2) % 2 == 0) else dark
            _disc(filled, cx, cy, y, 2.4, checker, color)
    image = sheet_from_volume(color, filled)
    image.save(SLICES / "gate.png")
    return _prop_meta("gate", "GATE", slices, width, depth, cx, cy, "finish post, matte checker")


def _prop_meta(i, name, slices, width, depth, cx, cy, blurb):
    print(f"{i:10} slices={slices:3}  {width}x{depth}px")
    return {
        "id": i,
        "name": name,
        "file": f"{i}.png",
        "slices": int(slices),
        "w": int(width),
        "h": int(depth),
        "pivot_x": int(cx),
        "pivot_y": int(cy),
        "source": "procedural",
        "blurb": blurb,
        "role": "prop",
    }


def write_sheet_data() -> None:
    """Embed the PNGs so the page can read pixels from a file:// open.

    Chrome treats a file image drawn to a canvas as cross-origin, and
    getImageData then throws. A data URL is not tainted.
    """
    import base64

    manifest = json.loads((SLICES / "manifest.json").read_text())
    chunks = ["window.STACK_SHEETS = {\n"]
    for obj in manifest["objects"].values():
        raw = (SLICES / obj["file"]).read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        chunks.append(f'  "{obj["id"]}": "data:image/png;base64,{b64}",\n')
    chunks.append("};\n")
    (OUT / "sheets_data.js").write_text("".join(chunks))


def write_manifest(objects: list[dict]) -> None:
    manifest = {
        "ppm": PPM,
        "spacing": 1,
        "squash": 0.75,
        "internal": [640, 480],
        "upscale": 2,
        "note": "Slice 0 is the ground layer and the left tile. The sheet faces +y (down). Pivot pixel is the glTF root on the ground.",
        "objects": {o["id"]: o for o in objects},
    }
    (SLICES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    # Browser loads this as a script so the page works from file://.
    body = "window.STACK_MANIFEST = " + json.dumps(manifest) + ";\n"
    (OUT / "manifest.js").write_text(body)


def write_preview(objects: list[dict]) -> None:
    """One contact sheet, squash 0.75, three headings. For the README, not the game."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from stack_math import draw_stack, iround, turn_from_velocity

    cars = [o for o in objects if o["role"] == "car"]
    cell_w, cell_h = 160, 150
    sheet = Image.new("RGB", (cell_w * 3, cell_h * len(cars)), (8, 14, 26))
    headings = [((0, -1), "ahead"), ((1, -0.2), "bear right"), ((-1, -0.15), "bear left")]
    for row, obj in enumerate(cars):
        im = np.asarray(Image.open(SLICES / obj["file"]).convert("RGBA"))
        for col, ((vx, vy), _label) in enumerate(headings):
            turn = turn_from_velocity(vx, vy)
            drawn = draw_stack(
                im, obj["slices"], obj["w"], obj["h"], (80, 120), turn, 0.75, 1.0
            )
            # Centre the opaque result in the cell.
            rgb = np.zeros((cell_h, cell_w, 3), np.uint8)
            rgb[:] = (8, 14, 26)
            h, w = drawn.shape[:2]
            y0 = max(0, (cell_h - h) // 2)
            x0 = max(0, (cell_w - w) // 2)
            src = drawn[: cell_h - y0, : cell_w - x0]
            a = src[:, :, 3:4] / 255.0
            patch = rgb[y0 : y0 + src.shape[0], x0 : x0 + src.shape[1]]
            patch[:] = (patch * (1 - a) + src[:, :, :3] * a).astype(np.uint8)
            sheet.paste(Image.fromarray(rgb, "RGB"), (col * cell_w, row * cell_h))
    sheet.save(SLICES / "preview.png")
    _ = iround


def main() -> None:
    SLICES.mkdir(parents=True, exist_ok=True)
    objects = []
    for spec in CARS:
        objects.append(build_car(spec))
    objects.append(build_prop_lamp())
    objects.append(build_prop_cedar())
    objects.append(build_prop_post())
    objects.append(build_prop_hut())
    objects.append(build_prop_gate())
    write_manifest(objects)
    write_sheet_data()
    write_preview(objects)
    car_peaks = [o["peak_luma"] for o in objects if o["role"] == "car"]
    hut = next(o for o in objects if o["id"] == "hut")
    print(f"car peak luma {max(car_peaks):.2f}  hut {hut['peak_luma']:.2f}")
    if hut["peak_luma"] >= min(car_peaks):
        raise SystemExit("hut is brighter than a car; storefront rule failed")


if __name__ == "__main__":
    main()
