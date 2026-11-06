"""Re-letter the clip names the image model garbled in the PT07 "happy" scenes (2026-11-05).

The AI drew the clips well but spelled the name wrong on some ("BUDOY", "SUBOY"). Locally,
no re-roll: inpaint the old letters out of the clip face, then put BUDDY back -
  * copied from a clip in the same picture that came out right (keeps its lighting and
    deboss look), shading re-based onto the target clip, or
  * drawn as a deboss (darker letters, light lower edge) when no clip came out right.
Boxes are (x0, y0, x1, y1) in the 1024 px AI frame, set by eye from zooms.

    py -3 tools/notrip-v51/fix_clip_names.py      -> ai/<name>-fixed.png
"""
import pathlib

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
AI = HERE / 'ai'
FONT = 'C:/Windows/Fonts/arialbd.ttf'


def clear(a, box):
    """Inpaint the letters (pixels clearly darker than the clip face) inside box."""
    x0, y0, x1, y1 = box
    reg = a[y0:y1, x0:x1]
    L = cv2.cvtColor(reg, cv2.COLOR_RGB2LAB)[..., 0].astype(int)
    m = (L < np.median(L) - 12).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=1)
    full = np.zeros(a.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = m
    return cv2.inpaint(a, full, 4, cv2.INPAINT_TELEA)


def copy_letters(a, src, dst):
    """Lift src's letters as a shading offset from its own face colour, add onto dst."""
    sx0, sy0, sx1, sy1 = src
    patch = a[sy0:sy1, sx0:sx1].astype(np.float64)
    base = cv2.medianBlur(a[sy0:sy1, sx0:sx1], 7).astype(np.float64)
    delta = patch - base
    dx0, dy0, dx1, dy1 = dst
    delta = cv2.resize(delta, (dx1 - dx0, dy1 - dy0), interpolation=cv2.INTER_CUBIC)
    out = a.astype(np.float64)
    out[dy0:dy1, dx0:dx1] += delta
    return np.clip(out, 0, 255).astype(np.uint8)


def draw_letters(a, box, rotate):
    """A debossed BUDDY fitted to box; rotate=-90 reads top to bottom."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    tw, th = (h, w) if rotate else (w, h)
    face = a[y0:y1, x0:x1].reshape(-1, 3).mean(0)
    size = th
    while size > 4:
        f = ImageFont.truetype(FONT, size)
        bb = f.getbbox('BUDDY')
        if bb[2] - bb[0] <= tw and bb[3] - bb[1] <= th * 0.8:
            break
        size -= 1
    def layer(dx, dy):
        im = Image.new('L', (tw * 4, th * 4), 0)
        ImageDraw.Draw(im).text((tw * 2 + dx * 4, th * 2 + dy * 4), 'BUDDY',
                                font=ImageFont.truetype(FONT, size * 4), fill=255, anchor='mm')
        im = im.resize((tw, th), Image.LANCZOS)
        if rotate:
            im = im.rotate(rotate, expand=True)
        return np.asarray(im, np.float64)[:h, :w, None] / 255
    dark, lite = layer(0, 0), layer(0.6, 0.6)
    out = a.astype(np.float64)
    reg = out[y0:y1, x0:x1]
    reg[:] = reg * (1 - lite * 0.25) + np.minimum(face * 1.18, 255) * lite * 0.25   # light lip
    reg[:] = reg * (1 - dark * 0.55) + face * 0.62 * dark * 0.55                      # sunk letters
    return np.clip(out, 0, 255).astype(np.uint8)


JOBS = {
    'happy-doodle-1': [('draw', (458, 568, 482, 612), -90), ('draw', (498, 788, 522, 834), -90)],
    'happy-golden-2': [('copy', (430, 585, 470, 603), (443, 881, 483, 899))],
}


def main():
    for name, steps in JOBS.items():
        a = np.asarray(Image.open(AI / f'{name}.png').convert('RGB')).copy()
        for kind, box, arg in steps:
            if kind == 'draw':
                a = draw_letters(clear(a, box), box, arg)
            else:
                a = copy_letters(clear(a, arg), box, arg)
        Image.fromarray(a).save(AI / f'{name}-fixed.png')
        print('wrote', name)


if __name__ == '__main__':
    main()
