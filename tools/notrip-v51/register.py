"""Put each picked photo-real hero exactly where its CAD frame has the part.

The image model keeps the part's shape but drifts its position and scale a little per
picture, so switching colour on the page would make the part jump. Here the part is cut out
(rembg, isnet, offline), scaled and moved onto the CAD silhouette's bounding box, and laid on
one shared studio sweep with a soft contact shadow. Every colour then lines up, and Standard
and Large keep the shared scale render_all.py gave them.

    py -3 tools/notrip-v51/register.py      (reads build/real/hero-picks.json)
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove

HERE = pathlib.Path(__file__).resolve().parent
B = HERE / 'build'
sys.path.insert(0, str(HERE.parent / 'notrip-amazon'))
import compose as C  # noqa: E402

OUT_SITE = HERE.parents[1] / 'src' / 'assets' / 'img' / 'notrip-leash'
TOP, BOTTOM = np.array([238, 239, 242]), np.array([214, 216, 221])   # the photos' own sweep, averaged


def sweep(W, H):
    t = np.linspace(0, 1, H)[:, None, None]
    return np.repeat(TOP * (1 - t) + BOTTOM * t, W, axis=1)


def main():
    picks = json.loads((B / 'real' / 'hero-picks.json').read_text())
    sess = new_session('isnet-general-use')
    (B / 'registered').mkdir(exist_ok=True)
    for key, n in sorted(picks.items()):
        size, col = key.split('-')
        cad = Image.open(B / 'heroes-cad' / f'hero-{size}-{col}.png').convert('RGB')
        W, H = cad.size
        cb = (np.asarray(C.cutout(cad)) > 128)
        ys, xs = np.nonzero(cb)
        cx0, cx1, cy0, cy1 = xs.min(), xs.max(), ys.min(), ys.max()

        ph = Image.open(B / 'real' / f'hero-{size}-{col}-{n}.png').convert('RGB')
        rgba = remove(ph, session=sess)
        a = np.asarray(rgba)[..., 3]
        a = np.where(a > 24, a, 0).astype(np.uint8)          # drop the faint shadow halo
        py, px = np.nonzero(a > 128)
        box = (px.min(), py.min(), px.max() + 1, py.max() + 1)
        part = rgba.crop(box)
        part.putalpha(Image.fromarray(a).crop(box))
        # fit the photo's part to the CAD box (keep its aspect; the diagonal part fills both)
        s = min((cx1 - cx0 + 1) / part.width, (cy1 - cy0 + 1) / part.height)
        part = part.resize((max(1, round(part.width * s)), max(1, round(part.height * s))), Image.LANCZOS)
        x = round((cx0 + cx1) / 2 - part.width / 2)
        y = round((cy0 + cy1) / 2 - part.height / 2)

        canvas = Image.fromarray(sweep(W, H).astype(np.uint8))
        alpha = part.split()[3]
        shadow = Image.new('L', (W, H), 0)
        shadow.paste(alpha, (x + round(W * 0.012), y + round(H * 0.03)))
        shadow = shadow.filter(ImageFilter.GaussianBlur(W * 0.012)).point(lambda v: v * 0.30)
        canvas.paste(Image.new('RGB', (W, H), (90, 92, 98)), (0, 0), shadow)
        canvas.paste(part, (x, y), part)
        canvas.save(B / 'registered' / f'hero-{size}-{col}.png')
        canvas.save(OUT_SITE / f'hero-{size}-{col}.jpg', quality=80, optimize=True, progressive=True)
        print(key, f'#{n}', 'scale %.2f' % s)


if __name__ == '__main__':
    main()
