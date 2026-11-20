"""Sprite-stack blit used by the tests and the slice preview.

Mirrors the draw in ``main.js``. Canvas space is +x right, +y down.
``ctx.rotate`` is clockwise in that space:

    x' = x cos(t) - y sin(t)
    y' = x sin(t) + y cos(t)

Turn for a velocity is ``atan2(vy, vx) - pi/2`` (the sheet faces +y).
Slices are lifted by ``-round(z * spacing)`` after the squash, ground slice first.
"""

from __future__ import annotations

import math

import numpy as np


def iround(v: float) -> int:
    return int(math.floor(v + 0.5))


def turn_from_velocity(vx: float, vy: float) -> float:
    return math.atan2(vy, vx) - math.pi / 2.0


def draw_stack(
    sheet: np.ndarray,
    count: int,
    sw: int,
    sh: int,
    pos: tuple[int, int],
    turn: float,
    squash: float = 0.75,
    spacing: float = 1.0,
    dest: np.ndarray | None = None,
) -> np.ndarray:
    """Paste ``count`` slices of ``sw`` x ``sh`` from ``sheet`` (H, count*sw, 4).

    Later slices overwrite earlier ones. Transparent source pixels are skipped,
    so a slice never punches a hole in the one below it.
    """
    if sheet.ndim != 3 or sheet.shape[2] != 4:
        raise ValueError("sheet must be HxWx4")
    if sheet.shape[1] != count * sw or sheet.shape[0] != sh:
        raise ValueError("sheet size does not match count, sw, sh")
    if squash <= 0:
        raise ValueError("squash must be positive")

    cos = math.cos(turn)
    sin = math.sin(turn)
    cx = sw // 2
    cy = sh // 2
    # Corners of the unrotated slice, then canvas rotate, then squash.
    corners = []
    for sx, sy in ((-cx, -cy), (sw - 1 - cx, -cy), (sw - 1 - cx, sh - 1 - cy), (-cx, sh - 1 - cy)):
        rx = sx * cos - sy * sin
        ry = (sx * sin + sy * cos) * squash
        corners.append((rx, ry))
    min_dx = int(math.floor(min(p[0] for p in corners))) - 1
    max_dx = int(math.ceil(max(p[0] for p in corners))) + 1
    min_dy = int(math.floor(min(p[1] for p in corners))) - 1
    max_dy = int(math.ceil(max(p[1] for p in corners))) + 1

    posx, posy = int(pos[0]), int(pos[1])
    top = posy - iround((count - 1) * spacing) + min_dy
    bot = posy + max_dy
    left = posx + min_dx
    right = posx + max_dx
    if dest is None:
        pad = 2
        width = right - left + 1 + pad * 2
        height = bot - top + 1 + pad * 2
        dest = np.zeros((height, width, 4), np.uint8)
        origin = (pad - left, pad - top)
    else:
        origin = (0, 0)

    ox, oy = origin
    for z in range(count):
        lift = iround(z * spacing)
        src = sheet[:, z * sw : (z + 1) * sw]
        for dy in range(min_dy, max_dy + 1):
            ry = dy / squash
            sy_base = oy + (posy - lift + dy)
            if sy_base < 0 or sy_base >= dest.shape[0]:
                continue
            for dx in range(min_dx, max_dx + 1):
                sx = ox + posx + dx
                if sx < 0 or sx >= dest.shape[1]:
                    continue
                # Inverse of canvas rotate, applied to the un-squashed point.
                u = dx * cos + ry * sin
                v = -dx * sin + ry * cos
                ix = iround(u + cx)
                iy = iround(v + cy)
                if ix < 0 or iy < 0 or ix >= sw or iy >= sh:
                    continue
                pixel = src[iy, ix]
                if pixel[3] < 128:
                    continue
                dest[sy_base, sx] = pixel
    return dest


def opaque_bbox(img: np.ndarray) -> tuple[int, int, int, int] | None:
    """Return (x0, y0, x1, y1) inclusive, or None if nothing is opaque."""
    alpha = img[:, :, 3] >= 128
    ys, xs = np.nonzero(alpha)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
