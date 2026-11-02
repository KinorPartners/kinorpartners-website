"""Software rasteriser for the v5.1 renders: orthographic, z-buffered, 2x supersampled.

The same renderer the v4 heroes, turntables and size-box minis came from (NoTrip
scripts/render.py), with the per-pixel loop vectorised per triangle row so a 40k
triangle assembly renders in seconds, and a colour per triangle so the body and
the name clip can differ.
"""
import math

import numpy as np

TOP, BOTTOM = (250, 251, 252), (222, 227, 233)


def backdrop(W, H, white=False):
    if white:
        return np.full((H, W, 3), 255, np.uint8)
    t = np.linspace(0, 1, H)[:, None]
    bg = np.array(TOP) * (1 - t) + np.array(BOTTOM) * t
    return np.repeat(bg[:, None, :], W, axis=1).astype(np.uint8).reshape(H, W, 3)


def rot(rx, ry, rz):
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


def roll(tris, deg):
    """Turn the part about its own long axis (model Z) before the camera rotations."""
    a = math.radians(deg)
    R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    return tris @ R.T


def render(tris, cols, W, H, rx, ry, rz, margin=0.06, ss=2, bg=None, light=(-0.3, 0.7, 0.8),
           spec=0.42, ambient=0.44, extent=None):
    """extent: (spanx, spany) in mm to fit instead of the part's own, so parts of
    different lengths share one scale."""
    R = rot(rx, ry, rz)
    V = (tris.reshape(-1, 3) @ R.T).reshape(-1, 3, 3)
    lo, hi = V.reshape(-1, 3).min(0), V.reshape(-1, 3).max(0)
    ctr = (lo + hi) / 2
    Wp, Hp = W * ss, H * ss
    sx, sy = (extent if extent else (hi[0] - lo[0], hi[1] - lo[1]))
    scale = min(Wp / (sx * (1 + 2 * margin)), Hp / (sy * (1 + 2 * margin)))
    P2 = (V[:, :, :2] - ctr[:2]) * scale
    P2[:, :, 0] += Wp / 2
    P2[:, :, 1] = Hp / 2 - P2[:, :, 1]
    Z = V[:, :, 2]

    N = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0])
    ln = np.linalg.norm(N, axis=1)
    ln[ln == 0] = 1
    N /= ln[:, None]
    lv = np.array(light, float)
    lv /= np.linalg.norm(lv)
    shade = ambient + (1 - ambient) * np.abs(N @ lv)
    rim = 0.30 * np.clip(1 - np.abs(N[:, 2]), 0, 1) ** 2
    h = lv + np.array([0, 0, 1.0])
    h /= np.linalg.norm(h)
    rgb = cols * shade[:, None] + rim[:, None] * 255 + (spec * 255 * np.abs(N @ h) ** 48)[:, None]
    rgb = np.clip(rgb, 0, 255)

    if bg is None:
        bg = backdrop(W, H)
    fb = np.repeat(np.repeat(bg, ss, 0), ss, 1).astype(np.float32).copy()
    zb = np.full((Hp, Wp), -1e30, np.float32)

    for i in range(len(P2)):
        (x0, y0), (x1, y1), (x2, y2) = P2[i]
        minx, maxx = max(int(min(x0, x1, x2)), 0), min(int(max(x0, x1, x2)) + 1, Wp)
        miny, maxy = max(int(min(y0, y1, y2)), 0), min(int(max(y0, y1, y2)) + 1, Hp)
        if minx >= maxx or miny >= maxy:
            continue
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(d) < 1e-12:
            continue
        xs = np.arange(minx, maxx) + 0.5 - x2
        ys = (np.arange(miny, maxy) + 0.5 - y2)[:, None]
        a = ((y1 - y2) * xs + (x2 - x1) * ys) / d
        b = ((y2 - y0) * xs + (x0 - x2) * ys) / d
        g = 1 - a - b
        m = (a >= -0.002) & (b >= -0.002) & (g >= -0.002)
        if not m.any():
            continue
        z = a * Z[i, 0] + b * Z[i, 1] + g * Z[i, 2]
        sub = zb[miny:maxy, minx:maxx]
        w = m & (z > sub)
        sub[w] = z[w]
        fb[miny:maxy, minx:maxx][w] = rgb[i]

    img = fb.reshape(H, ss, W, ss, 3).mean(axis=(1, 3))
    alpha = (zb > -1e29).reshape(H, ss, W, ss).mean(axis=(1, 3))
    return np.clip(img, 0, 255).astype(np.uint8), alpha


def load(path):
    d = np.load(path)
    body, clip = d['body'] if 'body' in d else np.zeros((0, 3, 3)), d['clip']
    return body.astype(np.float64), clip.astype(np.float64)


def paint(body, clip, body_rgb, clip_rgb):
    tris = np.concatenate([body, clip])
    cols = np.concatenate([np.tile(np.array(body_rgb, float), (len(body), 1)),
                           np.tile(np.array(clip_rgb, float), (len(clip), 1))])
    return tris, cols
